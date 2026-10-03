from statistics import mean


class RecommendationEvaluator:

    @staticmethod
    def _outfit_signature(
        outfit,
    ):

        items = (
            outfit.get(
                "items"
            )
            or {}
        )

        pairs = []

        for slot, item in sorted(
            items.items()
        ):

            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = item.get(
                "item_id"
            )

            if item_id:

                pairs.append(
                    (
                        str(
                            slot
                        ),
                        str(
                            item_id
                        ),
                    )
                )

        return tuple(
            pairs
        )

    @staticmethod
    def _safe_float(
        value,
    ):

        try:

            if value is None:
                return None

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    def evaluate(
        self,
        result,
    ):

        schedule = list(
            result.get(
                "schedule"
            )
            or []
        )

        total_days = len(
            schedule
        )

        scheduled_days = [

            day

            for day in schedule

            if (
                day.get(
                    "status"
                )
                == "scheduled"
                and isinstance(
                    day.get(
                        "outfit"
                    ),
                    dict,
                )
            )
        ]

        outfits = [

            day[
                "outfit"
            ]

            for day in scheduled_days
        ]

        signatures = [

            self._outfit_signature(
                outfit
            )

            for outfit in outfits
        ]

        unique_signatures = set(
            signatures
        )

        compatibility_scores = []

        style_scores = []

        ranking_scores = []

        threshold_flags = []

        recommendation_id_count = 0

        bandit_decision_id_count = 0

        weather_count = 0

        request_applied_count = 0

        learned_p9_count = 0

        p6_count = 0

        deterministic_bandit_count = 0

        exploration_count = 0

        for day in scheduled_days:

            outfit = day[
                "outfit"
            ]

            compatibility = (
                self._safe_float(
                    outfit.get(
                        "compatibility_score"
                    )
                )
            )

            if compatibility is not None:

                compatibility_scores.append(
                    compatibility
                )

            style = (
                self._safe_float(
                    outfit.get(
                        "style_score"
                    )
                )
            )

            if style is not None:

                style_scores.append(
                    style
                )

            ranking = (
                self._safe_float(
                    outfit.get(
                        "score"
                    )
                )
            )

            if ranking is not None:

                ranking_scores.append(
                    ranking
                )

            if (
                outfit.get(
                    "threshold_flag"
                )
                is not None
            ):

                threshold_flags.append(
                    bool(
                        outfit.get(
                            "threshold_flag"
                        )
                    )
                )

            if outfit.get(
                "recommendation_id"
            ):

                recommendation_id_count += 1

            if outfit.get(
                "bandit_decision_id"
            ):

                bandit_decision_id_count += 1

            if day.get(
                "weather"
            ):

                weather_count += 1

            if day.get(
                "request_applied"
            ):

                request_applied_count += 1

            personalization_method = (
                outfit.get(
                    "personalization_method"
                )
            )

            if (
                personalization_method
                == "learned_p9"
            ):

                learned_p9_count += 1

            elif (
                outfit.get(
                    "ranking_method"
                )
                == "compatibility_style_personalized"
            ):

                p6_count += 1

            policy = (
                outfit.get(
                    "bandit_policy"
                )
                or {}
            )

            if policy.get(
                "exploration_enabled"
            ):

                exploration_count += 1

            else:

                deterministic_bandit_count += 1

        def average(
            values,
        ):

            if not values:
                return None

            return float(
                mean(
                    values
                )
            )

        scheduled_count = len(
            scheduled_days
        )

        return {

            "days": {
                "total":
                    total_days,

                "scheduled":
                    scheduled_count,

                "success_rate":
                    (
                        scheduled_count
                        / total_days

                        if total_days
                        else 0.0
                    ),
            },

            "diversity": {
                "unique_outfits":
                    len(
                        unique_signatures
                    ),

                "duplicate_outfits":
                    (
                        scheduled_count
                        -
                        len(
                            unique_signatures
                        )
                    ),

                "unique_outfit_rate":
                    (
                        len(
                            unique_signatures
                        )
                        / scheduled_count

                        if scheduled_count
                        else 0.0
                    ),
            },

            "scores": {
                "average_compatibility":
                    average(
                        compatibility_scores
                    ),

                "average_style":
                    average(
                        style_scores
                    ),

                "average_ranking_score":
                    average(
                        ranking_scores
                    ),
            },

            "compatibility_threshold": {
                "observed":
                    len(
                        threshold_flags
                    ),

                "passed":
                    sum(
                        threshold_flags
                    ),

                "pass_rate":
                    (
                        sum(
                            threshold_flags
                        )
                        /
                        len(
                            threshold_flags
                        )

                        if threshold_flags
                        else None
                    ),
            },

            "traceability": {
                "recommendation_id_coverage":
                    (
                        recommendation_id_count
                        / scheduled_count

                        if scheduled_count
                        else 0.0
                    ),

                "bandit_decision_id_coverage":
                    (
                        bandit_decision_id_count
                        / scheduled_count

                        if scheduled_count
                        else 0.0
                    ),

                "weather_context_coverage":
                    (
                        weather_count
                        / scheduled_count

                        if scheduled_count
                        else 0.0
                    ),
            },

            "personalization": {
                "p6_days":
                    p6_count,

                "p9_days":
                    learned_p9_count,
            },

            "request": {
                "request_applied_days":
                    request_applied_count,
            },

            "bandit": {
                "deterministic_days":
                    deterministic_bandit_count,

                "exploration_days":
                    exploration_count,
            },
        }


__all__ = [
    "RecommendationEvaluator",
]
