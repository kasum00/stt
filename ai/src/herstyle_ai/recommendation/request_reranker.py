from copy import deepcopy


class RequestAwareReranker:
    """Apply explicit natural-language constraints after base ranking.

    Hard constraints remove candidates.  Soft request preferences rerank only
    the surviving candidates and never overwrite the original base score.
    """

    def __init__(
        self,
        max_request_weight=0.15,
    ):
        self.max_request_weight = float(
            max_request_weight
        )

        if not (
            0.0
            <= self.max_request_weight
            <= 1.0
        ):
            raise ValueError(
                "max_request_weight must be in [0, 1]"
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
                normalized[
                    indexed[tie_position][0]
                ] = percentile

            position = end

        return normalized

    @staticmethod
    def _base_score(
        candidate,
    ):
        if candidate.get("score") is not None:
            return float(
                candidate["score"]
            )

        if candidate.get("personalized_score") is not None:
            return float(
                candidate["personalized_score"]
            )

        if candidate.get("fusion_score") is not None:
            return float(
                candidate["fusion_score"]
            )

        return float(
            candidate.get(
                "compatibility_score",
                0.0,
            )
        )

    @staticmethod
    def _method_with_request(
        candidate,
    ):
        method = candidate.get(
            "ranking_method",
            "compatibility",
        )

        if method.endswith(
            "_request_aware"
        ):
            return method

        return f"{method}_request_aware"

    def rerank(
        self,
        candidates,
        constraints,
        matcher,
    ):
        candidates = [
            deepcopy(candidate)
            for candidate in candidates
        ]

        surviving = []

        for candidate in candidates:
            match_result = matcher.match(
                candidate,
                constraints,
            )

            if not match_result.hard_match:
                continue

            pre_request_score = self._base_score(
                candidate
            )
            candidate[
                "pre_request_score"
            ] = pre_request_score
            candidate[
                "request_score"
            ] = match_result.request_score
            candidate[
                "request_hard_match"
            ] = True
            candidate[
                "request_hard_matches"
            ] = list(
                match_result.hard_matches
            )
            candidate[
                "request_soft_matches"
            ] = list(
                match_result.soft_matches
            )
            surviving.append(candidate)

        if not surviving:
            return []

        request_scores = [
            candidate["request_score"]
            for candidate in surviving
        ]
        has_soft_request = any(
            score is not None
            for score in request_scores
        )

        if has_soft_request:
            numeric_scores = [
                float(score or 0.0)
                for score in request_scores
            ]
            request_rank_scores = self._rank_percentile(
                numeric_scores
            )
            request_weight = self.max_request_weight
        else:
            request_rank_scores = [
                None
                for _ in surviving
            ]
            request_weight = 0.0

        for index, candidate in enumerate(
            surviving
        ):
            pre_request_score = candidate[
                "pre_request_score"
            ]
            request_rank_score = request_rank_scores[
                index
            ]

            candidate[
                "request_rank_score"
            ] = request_rank_score
            candidate[
                "request_weight"
            ] = request_weight

            if has_soft_request:
                request_aware_score = (
                    (1.0 - request_weight)
                    * pre_request_score
                    + request_weight
                    * request_rank_score
                )
                candidate[
                    "ranking_method"
                ] = self._method_with_request(
                    candidate
                )
            else:
                request_aware_score = pre_request_score

            candidate[
                "request_aware_score"
            ] = request_aware_score
            candidate[
                "score"
            ] = request_aware_score

        if has_soft_request:
            surviving.sort(
                key=lambda candidate: candidate[
                    "request_aware_score"
                ],
                reverse=True,
            )
        else:
            surviving.sort(
                key=lambda candidate: candidate[
                    "pre_request_score"
                ],
                reverse=True,
            )

        return surviving


__all__ = [
    "RequestAwareReranker",
]
