import json

from collections import (
    defaultdict,
)

from pathlib import Path

from herstyle_ai.personalization.bandit_reward import (
    BanditRewardMapper,
)


MIN_REWARDED_DECISIONS = 200
MIN_POSITIVE_REWARDS = 50
MIN_NEGATIVE_REWARDS = 50
MIN_IPS_ELIGIBLE = 100


class BanditDatasetExporter:

    def __init__(
        self,
        project_root,
        *,
        excluded_user_prefixes=(
            "p9_snapshot_test",
            "p10_",
            "scheduler_smoke",
        ),
    ):

        self.project_root = Path(
            project_root
        )

        self.excluded_user_prefixes = tuple(
            excluded_user_prefixes
        )

        self.output_dir = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "bandit"
            / "training"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.logged_path = (
            self.output_dir
            / "bandit_logged.jsonl"
        )

        self.train_ready_path = (
            self.output_dir
            / "bandit_train_ready.jsonl"
        )

        self.report_path = (
            self.output_dir
            / "quality_report.json"
        )

        self.reward_mapper = (
            BanditRewardMapper()
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _excluded_user(
        self,
        user_id,
    ):

        user_id = str(
            user_id
        )

        return any(
            user_id.startswith(
                prefix
            )
            for prefix in (
                self.excluded_user_prefixes
            )
        )

    @staticmethod
    def _recommendation_id_from_event(
        event,
    ):

        metadata = (
            event.get(
                "metadata"
            )
            or {}
        )

        return (
            metadata.get(
                "recommendation_id"
            )
            or event.get(
                "recommendation_id"
            )
        )

    # =====================================================
    # BUILD
    # =====================================================

    def build(
        self,
        *,
        exposures,
        feedback_events,
    ):

        exposures = list(
            exposures
        )

        feedback_events = list(
            feedback_events
        )

        events_by_recommendation = defaultdict(
            list
        )

        for event in feedback_events:

            recommendation_id = (
                self._recommendation_id_from_event(
                    event
                )
            )

            if not recommendation_id:

                continue

            events_by_recommendation[
                str(
                    recommendation_id
                )
            ].append(
                event
            )

        logged_rows = []

        train_rows = []

        stats = {

            "total_exposures":
                len(
                    exposures
                ),

            "excluded_test_user":
                0,

            "joined_with_feedback":
                0,

            "shown_confirmed":
                0,

            "reward_resolved":
                0,

            "reward_unresolved":
                0,

            "reward_conflicts":
                0,

            "positive_rewards":
                0,

            "negative_rewards":
                0,

            "zero_rewards":
                0,

            "ips_eligible_examples":
                0,

            "train_ready_examples":
                0,
        }

        for exposure in exposures:

            user_id = str(
                exposure.get(
                    "user_id",
                    ""
                )
            )

            if self._excluded_user(
                user_id
            ):

                stats[
                    "excluded_test_user"
                ] += 1

                continue

            recommendation_id = str(
                exposure.get(
                    "recommendation_id",
                    "",
                )
            )

            related_events = (
                events_by_recommendation.get(
                    recommendation_id,
                    [],
                )
            )

            if related_events:

                stats[
                    "joined_with_feedback"
                ] += 1

            event_types = {

                str(
                    event.get(
                        "event_type"
                    )
                )

                for event in related_events
            }

            # Explicit shown event is ideal.
            #
            # Reward-bearing actions also imply the user
            # must have interacted with the recommendation.
            shown_confirmed = (
                "outfit_shown"
                in event_types
                or any(
                    self.reward_mapper
                    .reward_for_event(
                        event_type
                    )
                    is not None
                    for event_type in event_types
                )
            )

            if shown_confirmed:

                stats[
                    "shown_confirmed"
                ] += 1

            reward_result = (
                self.reward_mapper
                .aggregate(
                    related_events
                )
            )

            if reward_result[
                "conflict"
            ]:

                stats[
                    "reward_conflicts"
                ] += 1

            if reward_result[
                "resolved"
            ]:

                stats[
                    "reward_resolved"
                ] += 1

            else:

                stats[
                    "reward_unresolved"
                ] += 1

            behavior_policy = (
                exposure.get(
                    "behavior_policy"
                )
                or {}
            )

            ips_eligible = bool(
                behavior_policy.get(
                    "ips_eligible",
                    False,
                )
            )

            row = {

                "decision_id":
                    exposure.get(
                        "decision_id"
                    ),

                "recommendation_id":
                    recommendation_id,

                "user_id":
                    user_id,

                "timestamp":
                    exposure.get(
                        "timestamp"
                    ),

                "day":
                    exposure.get(
                        "day"
                    ),

                "structure":
                    exposure.get(
                        "structure"
                    ),

                "context":
                    exposure.get(
                        "context",
                        {},
                    ),

                "request_applied":
                    exposure.get(
                        "request_applied",
                        False,
                    ),

                "candidate_count":
                    exposure.get(
                        "candidate_count",
                        0,
                    ),

                "candidate_set":
                    exposure.get(
                        "candidate_set",
                        [],
                    ),

                "selected_action_id":
                    exposure.get(
                        "selected_action_id"
                    ),

                "selected":
                    exposure.get(
                        "selected"
                    ),

                "behavior_policy":
                    behavior_policy,

                "shown_confirmed":
                    shown_confirmed,

                "reward":
                    reward_result[
                        "reward"
                    ],

                "reward_resolved":
                    reward_result[
                        "resolved"
                    ],

                "reward_conflict":
                    reward_result[
                        "conflict"
                    ],

                "reward_events":
                    reward_result[
                        "evidence_event_types"
                    ],
            }

            logged_rows.append(
                row
            )

            # ---------------------------------------------
            # TRAIN READY
            #
            # We require:
            # - actual observed interaction/reward
            # - no contradictory reward
            # - impression effectively observed
            # ---------------------------------------------

            if not shown_confirmed:
                continue

            if not reward_result[
                "resolved"
            ]:
                continue

            if reward_result[
                "conflict"
            ]:
                continue

            reward = float(
                reward_result[
                    "reward"
                ]
            )

            if reward > 0:

                stats[
                    "positive_rewards"
                ] += 1

            elif reward < 0:

                stats[
                    "negative_rewards"
                ] += 1

            else:

                stats[
                    "zero_rewards"
                ] += 1

            train_rows.append(
                row
            )

            # IPS eligibility counts only rewarded,
            # conflict-free, train-ready decisions.
            if ips_eligible:

                stats[
                    "ips_eligible_examples"
                ] += 1

            # Count IPS eligibility only for rows that
            # actually have an observed, resolved reward.
            # Unrewarded impressions must not open the
            # bandit training/evaluation gate.

            # Count IPS eligibility only for rows that
            # actually have an observed, resolved reward.
            # Unrewarded impressions must not open the
            # bandit training/evaluation gate.

        stats[
            "train_ready_examples"
        ] = len(
            train_rows
        )

        blockers = []

        if (
            len(
                train_rows
            )
            < MIN_REWARDED_DECISIONS
        ):

            blockers.append(
                "rewarded_decisions_below_minimum"
            )

        if (
            stats[
                "positive_rewards"
            ]
            < MIN_POSITIVE_REWARDS
        ):

            blockers.append(
                "positive_rewards_below_minimum"
            )

        if (
            stats[
                "negative_rewards"
            ]
            < MIN_NEGATIVE_REWARDS
        ):

            blockers.append(
                "negative_rewards_below_minimum"
            )

        if (
            stats[
                "ips_eligible_examples"
            ]
            < MIN_IPS_ELIGIBLE
        ):

            blockers.append(
                "ips_eligible_examples_below_minimum"
            )

        report = {

            **stats,

            "ready_for_bandit_training":
                len(
                    blockers
                )
                == 0,

            "blockers":
                blockers,

            "thresholds": {

                "min_rewarded_decisions":
                    MIN_REWARDED_DECISIONS,

                "min_positive_rewards":
                    MIN_POSITIVE_REWARDS,

                "min_negative_rewards":
                    MIN_NEGATIVE_REWARDS,

                "min_ips_eligible":
                    MIN_IPS_ELIGIBLE,
            },

            "important_note":
                (
                    "Current deterministic policy uses "
                    "degenerate propensity=1.0 and is not "
                    "IPS-eligible. P10 exploration logging "
                    "must be introduced before unbiased "
                    "off-policy evaluation."
                ),
        }

        return (
            logged_rows,
            train_rows,
            report,
        )

    # =====================================================
    # EXPORT
    # =====================================================

    def export(
        self,
        *,
        exposures,
        feedback_events,
    ):

        (
            logged_rows,
            train_rows,
            report,
        ) = self.build(
            exposures=exposures,
            feedback_events=feedback_events,
        )

        with self.logged_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            for row in logged_rows:

                json.dump(
                    row,
                    f,
                    ensure_ascii=False,
                )

                f.write(
                    "\n"
                )

        with self.train_ready_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            for row in train_rows:

                json.dump(
                    row,
                    f,
                    ensure_ascii=False,
                )

                f.write(
                    "\n"
                )

        with self.report_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return {

            "logged_path":
                str(
                    self.logged_path
                ),

            "train_ready_path":
                str(
                    self.train_ready_path
                ),

            "report_path":
                str(
                    self.report_path
                ),

            "report":
                report,
        }


__all__ = [
    "BanditDatasetExporter",
]
