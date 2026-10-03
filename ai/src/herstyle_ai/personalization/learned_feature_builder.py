from typing import (
    Any,
    Dict,
    Iterable,
    Mapping,
)


class LearnedPersonalizationFeatureBuilder:

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            if value is None:

                return float(
                    default
                )

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                default
            )

    @staticmethod
    def _safe_bool(
        value,
        default=False,
    ):

        if value is None:

            return bool(
                default
            )

        if isinstance(
            value,
            str,
        ):

            return value.strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
            }

        return bool(
            value
        )

    @staticmethod
    def _add_numeric(
        features: Dict[str, float],
        name: str,
        value: Any,
    ):

        features[
            name
        ] = LearnedPersonalizationFeatureBuilder._safe_float(
            value
        )

    @staticmethod
    def _add_categorical(
        features: Dict[str, float],
        prefix: str,
        value: Any,
    ):

        if value is None:

            return

        value = str(
            value
        ).strip()

        if not value:

            return

        features[
            f"{prefix}={value}"
        ] = 1.0

    @staticmethod
    def _add_many(
        features: Dict[str, float],
        prefix: str,
        values: Any,
    ):

        if isinstance(
            values,
            str,
        ):

            values = [
                values
            ]

        if not isinstance(
            values,
            (list, tuple, set),
        ):

            return

        for value in values:

            LearnedPersonalizationFeatureBuilder._add_categorical(
                features,
                prefix,
                value,
            )

    def build(
        self,
        row: Mapping[str, Any],
    ) -> Dict[str, float]:

        if not isinstance(
            row,
            Mapping,
        ):

            raise TypeError(
                "row must be a mapping"
            )

        features: Dict[str, float] = {}

        # Continuous model inputs.
        for field_name in (
            "compatibility_score",
            "style_score",
            "base_score",
            "preference_score_v1",
            "preference_rank_score",
            "personalization_confidence",
            "personalization_weight",
            "request_score",
            "request_rank_score",
            "temperature",
            "apparent_temperature",
            "decision_temperature",
            "precipitation_probability",
            "layer_count",
        ):

            if field_name in row:

                self._add_numeric(
                    features,
                    field_name,
                    row.get(
                        field_name
                    ),
                )

        # Keep these as explicit numeric indicators.
        for field_name in (
            "is_layered",
            "rain_risk",
            "request_applied",
        ):

            if field_name in row:

                features[
                    field_name
                ] = float(
                    self._safe_bool(
                        row.get(
                            field_name
                        )
                    )
                )

        # Categorical context.
        for field_name in (
            "user_id",
            "structure",
            "base_structure",
            "weather_context",
            "request_context",
        ):

            self._add_categorical(
                features,
                field_name,
                row.get(
                    field_name
                ),
            )

        base_card_id = row.get(
            "base_card_id"
        )

        if base_card_id is not None:

            self._add_categorical(
                features,
                "base_card_id",
                base_card_id,
            )

        # Multi-value garment/style dimensions.
        for field_name in (
            "slots",
            "categories",
            "subcategories",
            "colors",
            "patterns",
            "style_tags",
        ):

            self._add_many(
                features,
                field_name,
                row.get(
                    field_name,
                    [],
                ),
            )

        # V1 intentionally does not include item_ids/item_id.
        return features

    def build_many(
        self,
        rows: Iterable[Mapping[str, Any]],
    ):

        return [
            self.build(
                row
            )
            for row in rows
        ]


__all__ = [
    "LearnedPersonalizationFeatureBuilder",
]
