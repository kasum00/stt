from copy import deepcopy

from pathlib import Path

from herstyle_ai.personalization.learned_ranker import (
    LearnedPersonalizationRanker,
)

from herstyle_ai.personalization.learned_model_artifact import (
    LearnedPersonalizationModelArtifact,
)

from herstyle_ai.personalization.model_registry import (
    PersonalizationModelRegistry,
)


class LearnedPersonalizationRuntime:

    def __init__(
        self,
        project_root,
        *,
        max_personalization_weight=0.15,
        min_candidates=5,
    ):

        self.project_root = Path(
            project_root
        )

        self.max_personalization_weight = float(
            max_personalization_weight
        )

        self.min_candidates = int(
            min_candidates
        )

        if not 0.0 <= self.max_personalization_weight <= 1.0:

            raise ValueError(
                "max_personalization_weight must be in [0, 1]"
            )

        if self.min_candidates <= 0:

            raise ValueError(
                "min_candidates must be > 0"
            )

        self.registry = (
            PersonalizationModelRegistry(
                project_root=self.project_root
            )
        )

        self.artifact = (
            LearnedPersonalizationModelArtifact(
                project_root=self.project_root
            )
        )

        self._ranker = None
        self._model_version = None
        self._loaded_version = None

    @staticmethod
    def _rank_percentile(
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

            current_value = indexed[
                position
            ][1]

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
                average_rank
                / (n - 1)
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

        for field_name in (
            "score",
            "request_aware_score",
            "personalized_score",
            "fusion_score",
            "compatibility_score",
        ):

            value = candidate.get(
                field_name
            )

            if value is not None:

                return float(
                    value
                )

        return 0.0

    @staticmethod
    def _unique_values(
        values,
    ):

        result = []

        for value in values:

            if value is None:

                continue

            value = str(
                value
            )

            if value and value not in result:

                result.append(
                    value
                )

        return result

    def _load_active_model(
        self,
    ):

        version = self.registry.get_active_version()
        model_path = self.registry.get_active_model_path()

        if not version or not model_path:

            self._ranker = None
            self._model_version = None
            self._loaded_version = None
            return False

        if (
            self._ranker is not None
            and self._model_version == version
        ):

            return True

        try:

            ranker = LearnedPersonalizationRanker.load(
                model_path
            )

        except Exception:

            self._ranker = None
            self._model_version = None
            self._loaded_version = None
            return False

        self._ranker = ranker
        self._model_version = str(
            version
        )

        self._loaded_version = self._model_version

        return True

    def can_use(
        self,
        user_id,
    ):

        if user_id is None or not str(
            user_id
        ).strip():

            return False

        return self._load_active_model()

    def _feature_row(
        self,
        candidate,
        context,
        request_constraints,
        request_applied,
        preference_scorer,
        user_id,
    ):

        row = dict(
            candidate
        )

        structure_analysis = candidate.get(
            "structure_analysis",
            {},
        )

        if not isinstance(
            structure_analysis,
            dict,
        ):

            structure_analysis = {}

        items = candidate.get(
            "items",
            {},
        )

        if not isinstance(
            items,
            dict,
        ):

            items = {}

        row[
            "user_id"
        ] = str(
            user_id
        )

        row[
            "base_score"
        ] = self._base_score(
            candidate
        )

        row[
            "base_structure"
        ] = structure_analysis.get(
            "base_structure"
        )

        row[
            "base_card_id"
        ] = structure_analysis.get(
            "base_card_id"
        )

        row[
            "layer_count"
        ] = structure_analysis.get(
            "layer_count"
        )

        row[
            "is_layered"
        ] = structure_analysis.get(
            "is_layered"
        )

        row[
            "slots"
        ] = list(
            items.keys()
        )

        row[
            "categories"
        ] = self._unique_values(
            item.get(
                "category"
            )
            for item in items.values()
            if isinstance(
                item,
                dict,
            )
        )

        row[
            "subcategories"
        ] = self._unique_values(
            item.get(
                "subcategory"
            )
            for item in items.values()
            if isinstance(
                item,
                dict,
            )
        )

        row[
            "colors"
        ] = self._unique_values(
            item.get(
                "color"
            )
            for item in items.values()
            if isinstance(
                item,
                dict,
            )
        )

        row[
            "patterns"
        ] = self._unique_values(
            item.get(
                "pattern"
            )
            for item in items.values()
            if isinstance(
                item,
                dict,
            )
        )

        row[
            "style_tags"
        ] = self._unique_values(
            tag
            for item in items.values()
            if isinstance(
                item,
                dict,
            )
            for tag in (
                item.get(
                    "style_tags",
                    [],
                )
                if isinstance(
                    item.get(
                        "style_tags",
                        [],
                    ),
                    (list, tuple, set),
                )
                else [
                    item.get(
                        "style_tags"
                    )
                ]
            )
        )

        if isinstance(
            context,
            dict,
        ):

            for field_name in (
                "temperature",
                "apparent_temperature",
                "decision_temperature",
                "precipitation_probability",
                "rain_risk",
            ):

                if field_name in context:

                    row[
                        field_name
                    ] = context.get(
                        field_name
                    )

        row[
            "request_applied"
        ] = (
            bool(
                request_applied
            )
            if request_applied is not None
            else request_constraints is not None
        )

        if request_constraints is not None:

            row[
                "request_context"
            ] = getattr(
                request_constraints,
                "raw_text",
                None,
            )

        if preference_scorer is not None:

            try:

                preference_result = (
                    preference_scorer
                    .score_candidate(
                        candidate
                    )
                )

                row[
                    "preference_score_v1"
                ] = float(
                    preference_result.score
                )

            except Exception:

                row[
                    "preference_score_v1"
                ] = 0.0

        return row

    def rerank(
        self,
        candidates,
        *,
        user_id,
        context,
        request_applied,
        preference_scorer,
        request_constraints=None,
    ):

        if not self.can_use(
            user_id
        ):

            return deepcopy(
                list(
                    candidates
                )
            )

        copied = deepcopy(
            list(
                candidates
            )
        )

        if not copied:

            return []

        feature_rows = [
            self._feature_row(
                candidate=candidate,
                context=context or {},
                request_constraints=request_constraints,
                request_applied=request_applied,
                preference_scorer=preference_scorer,
                user_id=user_id,
            )
            for candidate in copied
        ]

        learned_scores = self._ranker.score_many(
            feature_rows
        )

        learned_rank_scores = self._rank_percentile(
            learned_scores
        )

        should_personalize = len(
            copied
        ) >= self.min_candidates

        for index, candidate in enumerate(
            copied
        ):

            base_score = self._base_score(
                candidate
            )

            learned_score = float(
                learned_scores[index]
            )

            learned_rank_score = float(
                learned_rank_scores[index]
            )

            candidate[
                "base_score"
            ] = base_score

            candidate[
                "learned_preference_score"
            ] = learned_score

            candidate[
                "learned_preference_rank_score"
            ] = learned_rank_score

            candidate[
                "learned_model_version"
            ] = (
                self._loaded_version
                or self._model_version
            )

            if should_personalize:

                final_score = (
                    (1.0 - self.max_personalization_weight)
                    * base_score
                    + self.max_personalization_weight
                    * learned_rank_score
                )

                candidate[
                    "score"
                ] = final_score

                candidate[
                    "personalized_score"
                ] = final_score

                candidate[
                    "personalization_weight"
                ] = self.max_personalization_weight

                candidate[
                    "personalization_method"
                ] = "learned_p9"

                candidate[
                    "ranking_method"
                ] = "compatibility_style_learned_personalized"

            else:

                candidate[
                    "score"
                ] = base_score

                candidate[
                    "personalized_score"
                ] = None

                candidate[
                    "personalization_weight"
                ] = 0.0

                candidate[
                    "personalization_method"
                ] = "learned_p9"

            candidate[
                "learned_preference_score"
            ] = learned_score

        copied.sort(
            key=lambda candidate: candidate.get(
                "score",
                0.0,
            ),
            reverse=True,
        )

        return copied


__all__ = [
    "LearnedPersonalizationRuntime",
]
