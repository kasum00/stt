import hashlib
import json

from datetime import (
    datetime,
    timezone,
)

from uuid import uuid4


def utc_now_iso():

    return (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


def stable_action_id(
    candidate,
):

    items = (
        candidate.get(
            "items"
        )
        or {}
    )

    pairs = []

    if isinstance(
        items,
        dict,
    ):

        for slot, item in sorted(
            items.items()
        ):

            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = (
                item.get(
                    "item_id"
                )
            )

            if item_id:

                pairs.append(
                    [
                        str(
                            slot
                        ),
                        str(
                            item_id
                        ),
                    ]
                )

    raw = json.dumps(
        pairs,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()[
        :24
    ]


def candidate_action_snapshot(
    candidate,
):

    items = (
        candidate.get(
            "items"
        )
        or {}
    )

    item_ids = {}

    if isinstance(
        items,
        dict,
    ):

        for slot, item in items.items():

            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = item.get(
                "item_id"
            )

            if item_id:

                item_ids[
                    str(
                        slot
                    )
                ] = str(
                    item_id
                )

    scheduler = (
        candidate.get(
            "scheduler"
        )
        or {}
    )

    return {

        "action_id":
            stable_action_id(
                candidate
            ),

        "structure":
            candidate.get(
                "structure"
            ),

        "threshold_flag":
            candidate.get(
                "threshold_flag"
            ),

        "item_ids":
            item_ids,

        "compatibility_score":
            candidate.get(
                "compatibility_score"
            ),

        "style_score":
            candidate.get(
                "style_score"
            ),

        "fusion_score":
            candidate.get(
                "fusion_score"
            ),

        "base_score":
            candidate.get(
                "base_score"
            ),

        "score":
            candidate.get(
                "score"
            ),

        "preference_score":
            candidate.get(
                "preference_score"
            ),

        "preference_rank_score":
            candidate.get(
                "preference_rank_score"
            ),

        "learned_preference_score":
            candidate.get(
                "learned_preference_score"
            ),

        "learned_preference_rank_score":
            candidate.get(
                "learned_preference_rank_score"
            ),

        "ranking_method":
            candidate.get(
                "ranking_method"
            ),

        "personalization_method":
            candidate.get(
                "personalization_method"
            ),

        "learned_model_version":
            candidate.get(
                "learned_model_version"
            ),

        "request_score":
            candidate.get(
                "request_score"
            ),

        "scheduler_adjusted_score":
            scheduler.get(
                "adjusted_score"
            ),

        "recent_repeat_count":
            scheduler.get(
                "recent_repeat_count"
            ),
    }


def build_bandit_exposure(
    *,
    recommendation_id,
    user_id,
    day,
    structure,
    context,
    request_applied,
    candidates,
    selected,
    behavior_policy=None,
    decision_id=None,
):

    candidates = list(
        candidates
    )

    candidate_set = [

        candidate_action_snapshot(
            candidate
        )

        for candidate in candidates
    ]

    selected_action_id = (
        stable_action_id(
            selected
        )
    )

    selected_rank = None

    for index, action in enumerate(
        candidate_set,
        start=1,
    ):

        if (
            action[
                "action_id"
            ]
            == selected_action_id
        ):

            selected_rank = (
                index
            )

            break

    weather_context = {}

    if isinstance(
        context,
        dict,
    ):

        for key in (
            "date",
            "temperature",
            "apparent_temperature",
            "decision_temperature",
            "precipitation_probability",
            "precipitation_sum",
            "rain_risk",
            "weather_code",
        ):

            if key in context:

                weather_context[
                    key
                ] = context[
                    key
                ]

    effective_behavior_policy = dict(
        behavior_policy
        or {
            "name":
                "herstyle-ranking-scheduler",
            "version":
                "p10-deterministic-v1",
            "deterministic":
                True,
            "exploration_enabled":
                False,
            "selected_propensity":
                1.0,
            "ips_eligible":
                False,
        }
    )

    return {

        "decision_id":
            decision_id
            or uuid4().hex,

        "recommendation_id":
            str(
                recommendation_id
            ),

        "user_id":
            str(
                user_id
            ),

        "timestamp":
            utc_now_iso(),

        "day":
            int(
                day
            ),

        "structure":
            structure,

        "request_applied":
            bool(
                request_applied
            ),

        "context":
            weather_context,

        "candidate_count":
            len(
                candidate_set
            ),

        "candidate_set":
            candidate_set,

        "selected_action_id":
            selected_action_id,

        "selected_rank_before_scheduler":
            selected_rank,

        "selected_propensity": (
            effective_behavior_policy.get(
                "selected_propensity"
            )
        ),

        "selected":
            candidate_action_snapshot(
                selected
            ),

        # =============================================
        # BEHAVIOR POLICY
        #
        # Current system is deterministic.
        #
        # propensity=1.0 here DOES NOT mean we can use
        # IPS to compare arbitrary policies.
        # =============================================

        "behavior_policy":
            effective_behavior_policy,
    }


__all__ = [
    "stable_action_id",
    "candidate_action_snapshot",
    "build_bandit_exposure",
]
