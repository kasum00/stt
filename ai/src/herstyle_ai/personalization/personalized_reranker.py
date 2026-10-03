from copy import deepcopy
from typing import Any


class PersonalizedReranker:
    """Apply user preference to an existing base recommendation ranking."""

    def __init__(
        self,
        max_personalization_weight=0.15,
        full_confidence_signals=20,
        min_candidates=5,
    ):
        self.max_personalization_weight = float(
            max_personalization_weight
        )
        self.full_confidence_signals = int(
            full_confidence_signals
        )
        self.min_candidates = int(
            min_candidates
        )

        if not (
            0.0
            <= self.max_personalization_weight
            <= 1.0
        ):
            raise ValueError(
                "max_personalization_weight "
                "must be in [0, 1]"
            )

        if self.full_confidence_signals <= 0:
            raise ValueError(
                "full_confidence_signals must be > 0"
            )

        if self.min_candidates <= 0:
            raise ValueError(
                "min_candidates must be > 0"
            )

    @staticmethod
    def _rank_percentile(
        values,
    ):
        n = len(values)

        if n == 0:
            return []

        if n == 1:
            return [0.5]

        indexed = sorted(
            enumerate(values),
            key=lambda pair: pair[1],
            reverse=True,
        )
        normalized = [
            0.0
            for _ in values
        ]
        position = 0

        while position < n:
            end = position + 1
            current_value = indexed[position][1]

            while (
                end < n
                and abs(
                    indexed[end][1]
                    - current_value
                ) < 1e-12
            ):
                end += 1

            average_rank = (
                position
                + end
                - 1
            ) / 2.0
            percentile = 1.0 - (
                average_rank / (n - 1)
            )

            for tie_position in range(
                position,
                end,
            ):
                original_index = indexed[
                    tie_position
                ][0]
                normalized[original_index] = percentile

            position = end

        return normalized

    def _signal_count(
        self,
        preference_scorer: Any,
    ) -> int:
        profile = getattr(
            preference_scorer,
            "profile",
            None,
        )

        if isinstance(profile, dict):
            value = profile.get(
                "signal_count",
                0,
            )
        else:
            value = getattr(
                profile,
                "signal_count",
                0,
            )

        try:
            return max(
                0,
                int(value),
            )
        except (TypeError, ValueError):
            return 0

    def _personalization_confidence(
        self,
        preference_scorer: Any,
    ) -> float:
        confidence = min(
            1.0,
            self._signal_count(
                preference_scorer
            )
            / self.full_confidence_signals,
        )

        return confidence

    def _personalization_weight(
        self,
        preference_scorer: Any,
    ) -> float:
        return (
            self.max_personalization_weight
            * self._personalization_confidence(
                preference_scorer
            )
        )

    @staticmethod
    def _base_score(
        recommendation,
    ) -> float:
        value = recommendation.get(
            "score"
        )

        if value is None:
            value = recommendation.get(
                "fusion_score"
            )

        if value is None:
            value = recommendation.get(
                "compatibility_score",
                0.0,
            )

        return float(value)

    def rerank(
        self,
        recommendations,
        preference_scorer,
    ):
        """Return a new, preference-aware ranking.

        The incoming recommendation dictionaries are never mutated.  Base
        scores stay on their existing scale; only preference scores are
        converted to structure-local rank percentiles before fusion.
        """

        rows = []
        copied_recommendations = deepcopy(
            list(recommendations)
        )

        for recommendation in copied_recommendations:
            base_score = self._base_score(
                recommendation
            )
            preference_result = (
                preference_scorer
                .score_candidate(
                    recommendation
                )
            )

            rows.append(
                {
                    "recommendation": recommendation,
                    "base_score": base_score,
                    "preference_score": float(
                        preference_result.score
                    ),
                }
            )

        if not rows:
            return []

        preference_rank_scores = self._rank_percentile(
            [
                row["preference_score"]
                for row in rows
            ]
        )
        weight = self._personalization_weight(
            preference_scorer
        )
        confidence = self._personalization_confidence(
            preference_scorer
        )
        should_personalize = (
            len(rows) >= self.min_candidates
        )

        for index, row in enumerate(rows):
            recommendation = row[
                "recommendation"
            ]
            preference_rank_score = (
                preference_rank_scores[index]
            )

            recommendation[
                "base_score"
            ] = row[
                "base_score"
            ]
            recommendation[
                "preference_score"
            ] = row[
                "preference_score"
            ]
            recommendation[
                "preference_rank_score"
            ] = preference_rank_score
            recommendation[
                "personalization_confidence"
            ] = confidence

            if should_personalize:
                personalized_score = (
                    (1.0 - weight)
                    * row["base_score"]
                    + weight
                    * preference_rank_score
                )
                recommendation[
                    "score"
                ] = personalized_score
                recommendation[
                    "personalized_score"
                ] = personalized_score
                recommendation[
                    "personalization_weight"
                ] = weight
                recommendation[
                    "ranking_method"
                ] = (
                    "compatibility_style_personalized"
                )

            else:
                recommendation[
                    "score"
                ] = row[
                    "base_score"
                ]
                recommendation[
                    "personalized_score"
                ] = None
                recommendation[
                    "personalization_weight"
                ] = 0.0
                recommendation[
                    "ranking_method"
                ] = (
                    "compatibility_style"
                )

        rows.sort(
            key=lambda row: row[
                "recommendation"
            ][
                "score"
            ],
            reverse=True,
        )

        return [
            row[
                "recommendation"
            ]
            for row in rows
        ]


__all__ = [
    "PersonalizedReranker",
]
