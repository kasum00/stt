class BanditExposureValidator:

    @staticmethod
    def _float(value):

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def validate(self, exposure):

        errors = []
        warnings = []
        candidate_set = exposure.get("candidate_set") or []
        selected_action_id = exposure.get(
            "selected_action_id"
        )
        policy = exposure.get("behavior_policy") or {}

        action_ids = [
            row.get("action_id")
            for row in candidate_set
            if row.get("action_id")
        ]

        if not candidate_set:
            errors.append("candidate_set_empty")

        if not selected_action_id:
            errors.append("selected_action_id_missing")
        elif selected_action_id not in action_ids:
            errors.append(
                "selected_action_not_in_candidate_set"
            )

        if len(action_ids) != len(set(action_ids)):
            errors.append("duplicate_action_ids")

        propensity = self._float(
            policy.get("selected_propensity")
        )
        ips_eligible = bool(
            policy.get("ips_eligible", False)
        )
        probabilities = policy.get(
            "action_probabilities"
        ) or {}
        support_ids = list(
            policy.get("support_action_ids") or []
        )

        if propensity is not None and not (
            0.0 < propensity <= 1.0
        ):
            errors.append("selected_propensity_invalid")

        if ips_eligible:

            if len(support_ids) < 2:
                errors.append("ips_support_too_small")

            if selected_action_id not in support_ids:
                errors.append(
                    "selected_action_outside_support"
                )

            total_probability = 0.0

            for action_id in support_ids:

                value = self._float(
                    probabilities.get(action_id)
                )

                if value is None or value <= 0.0:
                    errors.append(
                        "support_probability_invalid"
                    )
                    continue

                total_probability += value

            if abs(total_probability - 1.0) > 1e-9:
                errors.append("probability_sum_not_one")

            selected_probability = self._float(
                probabilities.get(selected_action_id)
            )

            if (
                selected_probability is None
                or propensity is None
                or abs(selected_probability - propensity)
                > 1e-12
            ):
                errors.append(
                    "selected_propensity_mismatch"
                )

            candidate_lookup = {
                row.get("action_id"): row
                for row in candidate_set
            }

            for action_id in support_ids:

                candidate = candidate_lookup.get(action_id)

                if candidate is None:
                    errors.append(
                        "support_action_not_in_candidate_set"
                    )
                    continue

                if candidate.get("threshold_flag") is False:
                    errors.append(
                        "unsafe_threshold_action_in_support"
                    )

            max_score_drop = self._float(
                policy.get("max_score_drop")
            )

            if max_score_drop is not None:

                support_scores = []

                for action_id in support_ids:

                    candidate = candidate_lookup.get(action_id)

                    if candidate is None:
                        continue

                    score = self._float(
                        candidate.get(
                            "scheduler_adjusted_score"
                        )
                    )

                    if score is not None:
                        support_scores.append(score)

                if support_scores:

                    best = max(support_scores)
                    worst = min(support_scores)

                    if (
                        best - worst
                        > max_score_drop + 1e-12
                    ):
                        errors.append(
                            "support_exceeds_max_score_drop"
                        )

        else:
            warnings.append("not_ips_eligible")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "candidate_count": len(candidate_set),
            "support_count": len(support_ids),
            "selected_propensity": propensity,
            "ips_eligible": ips_eligible,
        }


__all__ = [
    "BanditExposureValidator",
]
