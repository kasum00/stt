from dataclasses import (
    asdict,
    dataclass,
    field,
    is_dataclass,
)

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
)


# =========================================================
# OUTFIT FEEDBACK TARGETS
#
# These are engineering sample strengths, not probabilities
# and not learned parameters.
# =========================================================

OUTFIT_EVENT_TARGETS = {
    "outfit_liked": {
        "label": 1,
        "sample_weight": 1.00,
    },
    "outfit_saved": {
        "label": 1,
        "sample_weight": 0.80,
    },
    "outfit_worn": {
        "label": 1,
        "sample_weight": 1.20,
    },
    "outfit_edited": {
        "label": 1,
        "sample_weight": 0.70,
    },
    "outfit_disliked": {
        "label": 0,
        "sample_weight": 1.00,
    },
    "outfit_skipped": {
        "label": 0,
        "sample_weight": 0.30,
    },
    "outfit_regenerated": {
        "label": 0,
        "sample_weight": 0.20,
    },
}


@dataclass
class PersonalizationTrainingExample:

    user_id: str

    event_type: str

    label: int

    sample_weight: float

    structure: Optional[str] = None

    compatibility_score: Optional[float] = None

    style_score: Optional[float] = None

    fusion_score: Optional[float] = None

    base_score: Optional[float] = None

    preference_score_v1: Optional[float] = None

    base_card_id: Optional[int] = None

    layer_count: Optional[int] = None

    slots: List[str] = field(
        default_factory=list
    )

    item_ids: List[str] = field(
        default_factory=list
    )

    categories: List[str] = field(
        default_factory=list
    )

    subcategories: List[str] = field(
        default_factory=list
    )

    colors: List[str] = field(
        default_factory=list
    )

    patterns: List[str] = field(
        default_factory=list
    )

    style_tags: List[str] = field(
        default_factory=list
    )

    weather: Dict[str, Any] = field(
        default_factory=dict
    )

    request_applied: Optional[bool] = None

    event_id: Optional[str] = None

    timestamp: Optional[str] = None

    created_at: Optional[str] = None

    recommendation_id: Optional[str] = None

    temperature: Optional[float] = None

    rain_risk: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:

        return asdict(
            self
        )


class PersonalizationTrainingExampleBuilder:
    """Convert eligible outfit feedback into immutable training examples.

    Existing feedback events without a recommendation snapshot retain
    ``None`` for score and structure fields.  The builder deliberately does
    not recompute historical ranking values.
    """

    def __init__(
        self,
        item_lookup: Optional[Any] = None,
    ):

        self.item_lookup = self._normalise_item_lookup(
            item_lookup
        )

    @staticmethod
    def _normalise_item_lookup(
        item_lookup: Optional[Any],
    ) -> Dict[str, Dict[str, Any]]:

        if item_lookup is None:

            return {}

        if isinstance(
            item_lookup,
            Mapping,
        ):

            result = {}

            for item_id, item in item_lookup.items():

                if not isinstance(
                    item,
                    Mapping,
                ):

                    continue

                payload = dict(
                    item
                )

                payload.setdefault(
                    "item_id",
                    str(
                        item_id
                    ),
                )

                result[
                    str(
                        item_id
                    )
                ] = payload

            return result

        result = {}

        if isinstance(
            item_lookup,
            Iterable,
        ) and not isinstance(
            item_lookup,
            (str, bytes),
        ):

            for item in item_lookup:

                if not isinstance(
                    item,
                    Mapping,
                ):

                    continue

                item_id = item.get(
                    "item_id"
                )

                if item_id is not None:

                    result[
                        str(
                            item_id
                        )
                    ] = dict(
                        item
                    )

        return result

    @staticmethod
    def _event_to_dict(
        event: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            event,
            Mapping,
        ):

            return dict(
                event
            )

        if hasattr(
            event,
            "to_dict",
        ):

            payload = event.to_dict()

            if isinstance(
                payload,
                Mapping,
            ):

                return dict(
                    payload
                )

        if is_dataclass(
            event
        ):

            return asdict(
                event
            )

        raise TypeError(
            "events must be mappings or dataclass-like feedback events"
        )

    @staticmethod
    def _first(
        *values,
    ):

        for value in values:

            if value is not None:

                return value

        return None

    @staticmethod
    def _optional_float(
        value,
    ):

        if value is None:

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _unique_strings(
        values,
    ) -> List[str]:

        result = []

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

            return result

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

    def _snapshot(
        self,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:

        metadata = event.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            Mapping,
        ):

            metadata = {}

        snapshot = metadata.get(
            "training_snapshot"
        )

        if not isinstance(
            snapshot,
            Mapping,
        ):

            snapshot = metadata.get(
                "snapshot"
            )

        if not isinstance(
            snapshot,
            Mapping,
        ):

            snapshot = {}

        merged = dict(
            snapshot
        )

        for key, value in metadata.items():

            if key not in merged:

                merged[key] = value

        return merged

    def _lookup_item(
        self,
        item_ref: Any,
        event: Mapping[str, Any],
        snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:

        if isinstance(
            item_ref,
            Mapping,
        ):

            return dict(
                item_ref
            )

        if item_ref is None:

            return {}

        item_id = str(
            item_ref
        )

        item = dict(
            self.item_lookup.get(
                item_id,
                {},
            )
        )

        for container in (
            snapshot,
            event,
        ):

            metadata = container.get(
                "item_metadata",
                {},
            )

            if not isinstance(
                metadata,
                Mapping,
            ):

                continue

            embedded = metadata.get(
                item_id
            )

            if isinstance(
                embedded,
                Mapping,
            ):

                merged = dict(
                    embedded
                )

                merged.update(
                    item
                )

                item = merged

        item.setdefault(
            "item_id",
            item_id,
        )

        return item

    @staticmethod
    def _item_value(
        item: Mapping[str, Any],
        key: str,
    ):

        value = item.get(
            key
        )

        if value is not None:

            return value

        profile_key = {
            "color": "color_profile",
            "pattern": "pattern_profile",
        }.get(
            key
        )

        if profile_key is None:

            return None

        profile = item.get(
            profile_key,
            {},
        )

        if not isinstance(
            profile,
            Mapping,
        ):

            return None

        if key == "color":

            return profile.get(
                "dominant"
            )

        return profile.get(
            "type"
        )

    def _make_example(
        self,
        event: Mapping[str, Any],
    ) -> PersonalizationTrainingExample:

        target = OUTFIT_EVENT_TARGETS[
            event[
                "event_type"
            ]
        ]

        snapshot = self._snapshot(
            event
        )

        snapshot_items = snapshot.get(
            "items",
            {},
        )

        if isinstance(
            snapshot_items,
            Mapping,
        ) and snapshot_items:

            items = snapshot_items

        else:

            items = event.get(
                "items",
                {},
            )

        if not isinstance(
            items,
            Mapping,
        ):

            items = {}

        slots = [
            str(
                slot
            )
            for slot in items.keys()
        ]

        item_payloads = [
            self._lookup_item(
                item_ref,
                event,
                snapshot,
            )
            for item_ref in items.values()
        ]

        structure_analysis = snapshot.get(
            "structure_analysis",
            {},
        )

        if not isinstance(
            structure_analysis,
            Mapping,
        ):

            structure_analysis = {}

        snapshot_weather = snapshot.get(
            "weather",
            {},
        )

        if not isinstance(
            snapshot_weather,
            Mapping,
        ):

            snapshot_weather = {}

        recommendation_id = self._first(
            snapshot.get(
                "recommendation_id"
            ),
            event.get(
                "recommendation_id"
            ),
            (
                event.get(
                    "metadata",
                    {}
                ).get(
                    "recommendation_id"
                )
                if isinstance(
                    event.get(
                        "metadata",
                        {},
                    ),
                    Mapping,
                )
                else None
            ),
        )

        base_card_id = self._first(
            snapshot.get(
                "base_card_id"
            ),
            structure_analysis.get(
                "base_card_id"
            ),
        )

        layer_count = self._first(
            snapshot.get(
                "layer_count"
            ),
            structure_analysis.get(
                "layer_count"
            ),
        )

        return PersonalizationTrainingExample(
            user_id=str(
                event.get(
                    "user_id",
                    "default",
                )
            ),
            event_type=str(
                event[
                    "event_type"
                ]
            ),
            label=int(
                target[
                    "label"
                ]
            ),
            sample_weight=float(
                target[
                    "sample_weight"
                ]
            ),
            structure=self._first(
                snapshot.get(
                    "structure"
                ),
                event.get(
                    "structure"
                ),
            ),
            compatibility_score=self._first(
                snapshot.get(
                    "compatibility_score"
                ),
                event.get(
                    "compatibility_score"
                ),
            ),
            style_score=self._first(
                snapshot.get(
                    "style_score"
                ),
                event.get(
                    "style_score"
                ),
            ),
            fusion_score=self._first(
                snapshot.get(
                    "fusion_score"
                ),
                event.get(
                    "fusion_score"
                ),
            ),
            base_score=self._first(
                snapshot.get(
                    "base_score"
                ),
                event.get(
                    "base_score"
                ),
            ),
            preference_score_v1=self._first(
                snapshot.get(
                    "preference_score_v1"
                ),
                snapshot.get(
                    "preference_score"
                ),
                event.get(
                    "preference_score_v1"
                ),
            ),
            base_card_id=(
                int(
                    base_card_id
                )
                if base_card_id is not None
                else None
            ),
            layer_count=(
                int(
                    layer_count
                )
                if layer_count is not None
                else None
            ),
            slots=slots,
            item_ids=self._unique_strings(
                [
                    item.get(
                        "item_id"
                    )
                    for item in item_payloads
                ]
            ),
            categories=self._unique_strings(
                [
                    item.get(
                        "category"
                    )
                    for item in item_payloads
                ]
            ),
            subcategories=self._unique_strings(
                [
                    item.get(
                        "subcategory"
                    )
                    for item in item_payloads
                ]
            ),
            colors=self._unique_strings(
                [
                    self._item_value(
                        item,
                        "color",
                    )
                    for item in item_payloads
                ]
            ),
            patterns=self._unique_strings(
                [
                    self._item_value(
                        item,
                        "pattern",
                    )
                    for item in item_payloads
                ]
            ),
            style_tags=self._unique_strings(
                [
                    tag
                    for item in item_payloads
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
                ]
            ),
            weather=dict(
                snapshot_weather
            ),
            request_applied=self._first(
                snapshot.get(
                    "request_applied"
                ),
                event.get(
                    "request_applied"
                ),
            ),
            event_id=event.get(
                "event_id"
            ),
            timestamp=event.get(
                "timestamp"
            ) or event.get(
                "created_at"
            ),
            created_at=event.get(
                "timestamp"
            ) or event.get(
                "created_at"
            ),
            recommendation_id=(
                str(
                    recommendation_id
                )
                if recommendation_id is not None
                else None
            ),
            temperature=self._optional_float(
                snapshot_weather.get(
                    "temperature"
                )
            ),
            rain_risk=(
                None
                if snapshot_weather.get(
                    "rain_risk"
                ) is None
                else bool(
                    snapshot_weather.get(
                        "rain_risk"
                    )
                )
            ),
        )

    def build(
        self,
        events: Iterable[Any],
    ) -> List[PersonalizationTrainingExample]:

        examples = []

        for raw_event in events:

            event = self._event_to_dict(
                raw_event
            )

            event_type = event.get(
                "event_type"
            )

            if event_type not in OUTFIT_EVENT_TARGETS:

                continue

            examples.append(
                self._make_example(
                    event
                )
            )

        return examples

    def build_from_repository(
        self,
        repository: Any,
    ) -> List[PersonalizationTrainingExample]:

        return self.build(
            repository.list_all()
        )


__all__ = [
    "OUTFIT_EVENT_TARGETS",
    "PersonalizationTrainingExample",
    "PersonalizationTrainingExampleBuilder",
]
