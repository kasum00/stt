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
    Mapping,
    Optional,
)


# =========================================================
# EVENT WEIGHTS
#
# Engineering defaults for V1.
# These are preference signals, not probabilities and not
# learned model parameters.
# =========================================================

EVENT_WEIGHTS = {
    "outfit_shown": 0.0,
    "outfit_opened": 0.10,
    "outfit_liked": 1.00,
    "outfit_disliked": -1.00,
    "outfit_saved": 0.80,
    "outfit_worn": 1.20,
    "outfit_skipped": -0.30,
    "outfit_regenerated": -0.20,
    # Replacement is handled directionally below: old item gets
    # a negative signal and new item gets a positive signal.
    "item_replaced": 0.0,
    "outfit_edited": 0.70,
}


PROFILE_DIMENSIONS = (
    "category",
    "subcategory",
    "color",
    "pattern",
    "style_tags",
    "item_id",
)


@dataclass
class UserPreferenceProfile:
    """Aggregated V1 preference signals for one user."""

    user_id: str

    event_count: int = 0

    signal_count: int = 0

    category: Dict[str, float] = field(
        default_factory=dict
    )

    subcategory: Dict[str, float] = field(
        default_factory=dict
    )

    color: Dict[str, float] = field(
        default_factory=dict
    )

    pattern: Dict[str, float] = field(
        default_factory=dict
    )

    style_tags: Dict[str, float] = field(
        default_factory=dict
    )

    item_id: Dict[str, float] = field(
        default_factory=dict
    )

    @property
    def events(self) -> int:
        """Backward-friendly alias for event_count."""

        return self.event_count

    @property
    def signals(self) -> int:
        """Backward-friendly alias for signal_count."""

        return self.signal_count

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def as_dict(self) -> Dict[str, Any]:
        return self.to_dict()


class UserPreferenceProfileBuilder:
    """Build a preference profile from stored feedback events.

    ``item_lookup`` can be either a mapping of ``item_id`` to item
    dictionaries or a list of item dictionaries.  The lookup is optional:
    item-level signals are still recorded when an event contains only IDs.
    """

    def __init__(
        self,
        user_id: str = "default",
        item_lookup: Optional[Any] = None,
        *,
        items: Optional[Any] = None,
    ):

        # Accept ``UserPreferenceProfileBuilder(items)`` as a convenient
        # shorthand while keeping the explicit user_id API.
        if (
            item_lookup is None
            and items is None
            and isinstance(user_id, (dict, list, tuple))
        ):
            item_lookup = user_id
            user_id = "default"

        if items is not None:
            item_lookup = items

        self.user_id = str(user_id)
        self.item_lookup = self._normalise_item_lookup(
            item_lookup
        )

    @staticmethod
    def _normalise_item_lookup(
        item_lookup: Optional[Any],
    ) -> Dict[str, Dict[str, Any]]:

        if item_lookup is None:
            return {}

        if isinstance(item_lookup, Mapping):
            result = {}

            for item_id, item in item_lookup.items():
                if isinstance(item, Mapping):
                    payload = dict(item)
                    payload.setdefault(
                        "item_id",
                        str(item_id),
                    )
                    result[str(item_id)] = payload

            return result

        result = {}

        if isinstance(item_lookup, Iterable) and not isinstance(
            item_lookup,
            (str, bytes),
        ):
            for item in item_lookup:
                if not isinstance(item, Mapping):
                    continue

                item_id = item.get("item_id")

                if item_id is not None:
                    result[str(item_id)] = dict(item)

        return result

    @staticmethod
    def _event_to_dict(
        event: Any,
    ) -> Dict[str, Any]:

        if isinstance(event, Mapping):
            return dict(event)

        if hasattr(event, "to_dict"):
            payload = event.to_dict()

            if isinstance(payload, Mapping):
                return dict(payload)

        if is_dataclass(event):
            return asdict(event)

        raise TypeError(
            "events must be mappings or dataclass-like feedback events"
        )

    def _lookup_item(
        self,
        item_ref: Any,
        event: Mapping[str, Any],
    ) -> tuple[Optional[str], Dict[str, Any]]:

        if isinstance(item_ref, Mapping):
            item = dict(item_ref)
            item_id = item.get("item_id")
            return (
                str(item_id) if item_id is not None else None,
                item,
            )

        if item_ref is None:
            return None, {}

        item_id = str(item_ref)
        item = dict(
            self.item_lookup.get(
                item_id,
                {},
            )
        )

        # This allows a caller to attach item metadata directly to an event
        # without changing the JSONL event schema.
        event_items = event.get("item_metadata", {})

        if not item and isinstance(event_items, Mapping):
            event_item = event_items.get(item_id)

            if isinstance(event_item, Mapping):
                item = dict(event_item)

        return item_id, item

    @staticmethod
    def _values_for_dimension(
        item: Mapping[str, Any],
        dimension: str,
    ):

        if dimension == "style_tags":
            raw_value = item.get("style_tags")

            if raw_value is None:
                raw_value = item.get("styles")

            if raw_value is None:
                raw_value = item.get("style")

            if raw_value is None:
                raw_value = item.get("tags")

            if raw_value is None:
                return []

            if isinstance(raw_value, str):
                return [
                    value.strip()
                    for value in raw_value.split(",")
                    if value.strip()
                ]

            if isinstance(raw_value, Iterable):
                return [
                    str(value)
                    for value in raw_value
                    if value is not None and str(value)
                ]

            return [str(raw_value)]

        value = item.get(dimension)

        if value is None:
            return []

        if isinstance(value, (list, tuple, set)):
            return [
                str(entry)
                for entry in value
                if entry is not None
            ]

        return [str(value)]

    @staticmethod
    def _add_signal(
        bucket: Dict[str, float],
        value: str,
        weight: float,
    ):

        bucket[value] = round(
            bucket.get(value, 0.0) + weight,
            6,
        )

    def _apply_item_signal(
        self,
        profile: UserPreferenceProfile,
        item_ref: Any,
        weight: float,
        event: Mapping[str, Any],
    ):

        item_id, item = self._lookup_item(
            item_ref,
            event,
        )

        if item_id is None:
            return

        self._add_signal(
            profile.item_id,
            item_id,
            weight,
        )

        for dimension in PROFILE_DIMENSIONS:

            if dimension == "item_id":
                continue

            bucket = getattr(
                profile,
                dimension,
            )

            for value in self._values_for_dimension(
                item,
                dimension,
            ):
                self._add_signal(
                    bucket,
                    value,
                    weight,
                )

    def build(
        self,
        events: Iterable[Any],
        item_lookup: Optional[Any] = None,
    ) -> UserPreferenceProfile:

        if item_lookup is not None:
            self.item_lookup = self._normalise_item_lookup(
                item_lookup
            )

        profile = UserPreferenceProfile(
            user_id=self.user_id,
        )

        for raw_event in events:
            event = self._event_to_dict(
                raw_event
            )

            if event.get("user_id", self.user_id) != self.user_id:
                continue

            event_type = event.get("event_type")

            if event_type not in EVENT_WEIGHTS:
                continue

            profile.event_count += 1

            if event_type == "item_replaced":
                metadata = event.get("metadata") or {}

                old_item_id = metadata.get(
                    "old_item_id"
                )
                new_item_id = metadata.get(
                    "new_item_id"
                )

                if old_item_id is None:
                    old_item_id = event.get(
                        "old_item_id"
                    )

                if new_item_id is None:
                    new_item_id = event.get(
                        "new_item_id"
                    )

                if old_item_id is not None:
                    self._apply_item_signal(
                        profile,
                        old_item_id,
                        -1.0,
                        event,
                    )

                if new_item_id is not None:
                    self._apply_item_signal(
                        profile,
                        new_item_id,
                        1.0,
                        event,
                    )

                if old_item_id is not None or new_item_id is not None:
                    profile.signal_count += 1

                continue

            weight = float(
                EVENT_WEIGHTS[event_type]
            )

            if weight == 0.0:
                continue

            items = event.get("items") or {}

            if isinstance(items, Mapping):
                for item_ref in items.values():
                    self._apply_item_signal(
                        profile,
                        item_ref,
                        weight,
                        event,
                    )

            profile.signal_count += 1

        return profile

    def build_from_repository(
        self,
        repository: Any,
        item_lookup: Optional[Any] = None,
    ) -> UserPreferenceProfile:

        return self.build(
            repository.list_all(
                user_id=self.user_id
            ),
            item_lookup=item_lookup,
        )


__all__ = [
    "EVENT_WEIGHTS",
    "UserPreferenceProfile",
    "UserPreferenceProfileBuilder",
]
