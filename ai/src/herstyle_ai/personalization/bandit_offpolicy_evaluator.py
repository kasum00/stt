class BanditOffPolicyEvaluator:

    def evaluate(
        self,
        rows,
        *,
        target_probability_fn,
    ):

        rows = list(
            rows
        )

        used = []

        skipped_not_ips_eligible = 0
        skipped_missing_reward = 0
        skipped_invalid_propensity = 0

        for row in rows:

            reward = row.get(
                "reward"
            )

            if reward is None:

                skipped_missing_reward += 1

                continue

            behavior_policy = (
                row.get(
                    "behavior_policy"
                )
                or {}
            )

            if not bool(
                behavior_policy.get(
                    "ips_eligible",
                    False,
                )
            ):

                skipped_not_ips_eligible += 1

                continue

            behavior_probability = (
                behavior_policy.get(
                    "selected_propensity"
                )
            )

            try:

                behavior_probability = float(
                    behavior_probability
                )

            except (
                TypeError,
                ValueError,
            ):

                skipped_invalid_propensity += 1

                continue

            if not (
                0.0
                < behavior_probability
                <= 1.0
            ):

                skipped_invalid_propensity += 1

                continue

            target_probability = (
                target_probability_fn(
                    row
                )
            )

            try:

                target_probability = float(
                    target_probability
                )

            except (
                TypeError,
                ValueError,
            ):

                raise ValueError(
                    "target probability "
                    "must be numeric"
                )

            if not (
                0.0
                <= target_probability
                <= 1.0
            ):

                raise ValueError(
                    "target probability "
                    "must be in [0, 1]"
                )

            importance_weight = (
                target_probability
                / behavior_probability
            )

            used.append(
                {
                    "reward":
                        float(
                            reward
                        ),

                    "behavior_probability":
                        behavior_probability,

                    "target_probability":
                        target_probability,

                    "importance_weight":
                        importance_weight,
                }
            )

        if not used:

            return {

                "examples":
                    0,

                "ips":
                    None,

                "snips":
                    None,

                "effective_sample_size":
                    0.0,

                "logged_mean_reward":
                    None,

                "skipped_not_ips_eligible":
                    skipped_not_ips_eligible,

                "skipped_missing_reward":
                    skipped_missing_reward,

                "skipped_invalid_propensity":
                    skipped_invalid_propensity,
            }

        weighted_rewards = [

            row[
                "importance_weight"
            ]
            * row[
                "reward"
            ]

            for row in used
        ]

        weights = [

            row[
                "importance_weight"
            ]

            for row in used
        ]

        rewards = [

            row[
                "reward"
            ]

            for row in used
        ]

        n = len(
            used
        )

        ips = (
            sum(
                weighted_rewards
            )
            / n
        )

        weight_sum = sum(
            weights
        )

        snips = (
            sum(
                weighted_rewards
            )
            / weight_sum

            if weight_sum > 0.0
            else None
        )

        weight_square_sum = sum(
            weight
            * weight
            for weight in weights
        )

        effective_sample_size = (

            (
                weight_sum
                * weight_sum
            )
            / weight_square_sum

            if (
                weight_square_sum
                > 0.0
            )
            else 0.0
        )

        return {

            "examples":
                n,

            "ips":
                float(
                    ips
                ),

            "snips":
                (
                    float(
                        snips
                    )
                    if snips is not None
                    else None
                ),

            "effective_sample_size":
                float(
                    effective_sample_size
                ),

            "logged_mean_reward":
                float(
                    sum(
                        rewards
                    )
                    / n
                ),

            "mean_importance_weight":
                float(
                    weight_sum
                    / n
                ),

            "max_importance_weight":
                float(
                    max(
                        weights
                    )
                ),

            "skipped_not_ips_eligible":
                skipped_not_ips_eligible,

            "skipped_missing_reward":
                skipped_missing_reward,

            "skipped_invalid_propensity":
                skipped_invalid_propensity,

            "warning":
                (
                    "IPS/SNIPS are meaningful only when "
                    "logged behavior propensities are correct "
                    "and the target policy stays inside the "
                    "behavior policy support."
                ),
        }


__all__ = [
    "BanditOffPolicyEvaluator",
]
