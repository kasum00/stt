class OutfitReranker:

    def __init__(
        self,
        compatibility_weight=0.70,
        styling_weight=0.30,
        min_candidates=5,
    ):

        compatibility_weight = float(
            compatibility_weight
        )

        styling_weight = float(
            styling_weight
        )

        if compatibility_weight < 0:
            raise ValueError(
                "compatibility_weight must be >= 0"
            )

        if styling_weight < 0:
            raise ValueError(
                "styling_weight must be >= 0"
            )

        total_weight = (
            compatibility_weight
            + styling_weight
        )

        if total_weight <= 0:
            raise ValueError(
                "reranking weights must sum to > 0"
            )

        # Normalize weights defensively.
        self.compatibility_weight = (
            compatibility_weight
            / total_weight
        )

        self.styling_weight = (
            styling_weight
            / total_weight
        )

        self.min_candidates = int(
            min_candidates
        )

    # =====================================================
    # RANK PERCENTILE
    # =====================================================

    def _rank_percentile(
        self,
        values,
    ):

        n = len(
            values
        )

        if n == 0:
            return []

        if n == 1:
            return [0.5]

        indexed = sorted(
            enumerate(
                values
            ),
            key=lambda x:
                x[1],
            reverse=True,
        )

        normalized = [
            0.0
            for _ in range(
                n
            )
        ]

        position = 0

        while position < n:

            end = (
                position
                + 1
            )

            current_value = (
                indexed[
                    position
                ][1]
            )

            while (
                end < n
                and abs(
                    indexed[
                        end
                    ][1]
                    - current_value
                )
                < 1e-12
            ):
                end += 1

            average_rank = (
                position
                + (
                    end
                    - 1
                )
            ) / 2.0

            percentile = (
                1.0
                - average_rank
                / (
                    n
                    - 1
                )
            )

            for tie_position in range(
                position,
                end,
            ):

                original_index = (
                    indexed[
                        tie_position
                    ][0]
                )

                normalized[
                    original_index
                ] = percentile

            position = end

        return normalized

    # =====================================================
    # COMPATIBILITY FALLBACK
    # =====================================================

    def _compatibility_only(
        self,
        recommendations,
    ):

        for recommendation in recommendations:

            compatibility_score = float(
                recommendation[
                    "compatibility_score"
                ]
            )

            recommendation[
                "score"
            ] = compatibility_score

            recommendation[
                "fusion_score"
            ] = None

            recommendation[
                "compatibility_rank_score"
            ] = None

            recommendation[
                "style_rank_score"
            ] = None

            recommendation[
                "ranking_method"
            ] = "compatibility"

        recommendations.sort(
            key=lambda x:
                x[
                    "compatibility_score"
                ],
            reverse=True,
        )

        return recommendations

    # =====================================================
    # RERANK
    # =====================================================

    def rerank(
        self,
        recommendations,
    ):

        recommendations = [
            dict(
                recommendation
            )
            for recommendation
            in recommendations
        ]

        if len(
            recommendations
        ) < self.min_candidates:

            return (
                self._compatibility_only(
                    recommendations
                )
            )

        # Styling must exist for every candidate.
        if any(
            recommendation.get(
                "style_score"
            )
            is None
            for recommendation
            in recommendations
        ):

            return (
                self._compatibility_only(
                    recommendations
                )
            )

        compatibility_scores = [
            float(
                recommendation[
                    "compatibility_score"
                ]
            )
            for recommendation
            in recommendations
        ]

        style_scores = [
            float(
                recommendation[
                    "style_score"
                ]
            )
            for recommendation
            in recommendations
        ]

        compatibility_rank_scores = (
            self._rank_percentile(
                compatibility_scores
            )
        )

        style_rank_scores = (
            self._rank_percentile(
                style_scores
            )
        )

        for index, recommendation in enumerate(
            recommendations
        ):

            compatibility_rank_score = (
                compatibility_rank_scores[
                    index
                ]
            )

            style_rank_score = (
                style_rank_scores[
                    index
                ]
            )

            fusion_score = (
                self.compatibility_weight
                * compatibility_rank_score
                +
                self.styling_weight
                * style_rank_score
            )

            recommendation[
                "compatibility_rank_score"
            ] = (
                compatibility_rank_score
            )

            recommendation[
                "style_rank_score"
            ] = (
                style_rank_score
            )

            recommendation[
                "fusion_score"
            ] = fusion_score

            # IMPORTANT:
            #
            # Downstream scheduler already reads "score".
            # Therefore score becomes the active ranking
            # score after reranking.
            recommendation[
                "score"
            ] = fusion_score

            recommendation[
                "ranking_method"
            ] = (
                "compatibility_style_fusion"
            )

        recommendations.sort(
            key=lambda x:
                x[
                    "score"
                ],
            reverse=True,
        )

        return recommendations