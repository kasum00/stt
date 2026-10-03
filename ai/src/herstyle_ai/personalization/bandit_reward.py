# =========================================================
# BANDIT REWARD MAPPING
#
# Engineering defaults for P10 V1.
# These are NOT learned probabilities.
# =========================================================

BANDIT_REWARD_MAP = {

    "outfit_liked":
        1.0,

    "outfit_saved":
        0.8,

    "outfit_worn":
        1.0,

    "outfit_edited":
        0.6,

    "outfit_disliked":
        -1.0,

    "outfit_skipped":
        -0.3,

    "outfit_regenerated":
        -0.2,

    # Exposure / weak interaction only.
    "outfit_shown":
        None,

    "outfit_opened":
        None,

    # Directional replacement signal.
    # Do not treat as whole-outfit scalar reward.
    "item_replaced":
        None,
}


class BanditRewardMapper:

    def reward_for_event(
        self,
        event_type,
    ):

        return (
            BANDIT_REWARD_MAP.get(
                str(
                    event_type
                )
            )
        )

    def aggregate(
        self,
        events,
    ):

        evidence = []

        rewards = []

        for event in events:

            event_type = (
                event.get(
                    "event_type"
                )
            )

            reward = (
                self.reward_for_event(
                    event_type
                )
            )

            if reward is None:

                continue

            reward = float(
                reward
            )

            evidence.append(
                str(
                    event_type
                )
            )

            rewards.append(
                reward
            )

        if not rewards:

            return {

                "resolved":
                    False,

                "reward":
                    None,

                "conflict":
                    False,

                "evidence_event_types":
                    [],
            }

        has_positive = any(
            reward > 0.0
            for reward in rewards
        )

        has_negative = any(
            reward < 0.0
            for reward in rewards
        )

        # Conflicting explicit/implicit evidence.
        if (
            has_positive
            and has_negative
        ):

            return {

                "resolved":
                    False,

                "reward":
                    None,

                "conflict":
                    True,

                "evidence_event_types":
                    sorted(
                        set(
                            evidence
                        )
                    ),
            }

        if has_positive:

            final_reward = max(
                rewards
            )

        elif has_negative:

            final_reward = min(
                rewards
            )

        else:

            final_reward = 0.0

        return {

            "resolved":
                True,

            "reward":
                float(
                    final_reward
                ),

            "conflict":
                False,

            "evidence_event_types":
                sorted(
                    set(
                        evidence
                    )
                ),
        }


__all__ = [
    "BANDIT_REWARD_MAP",
    "BanditRewardMapper",
]
