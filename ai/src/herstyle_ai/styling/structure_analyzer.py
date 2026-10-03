from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
)


@dataclass
class OutfitStructureResult:
    base_card_id: Optional[int] = None
    base_structure: Optional[str] = None
    layer_count: int = 1
    is_layered: bool = False
    relation_card_ids: List[int] = field(default_factory=list)
    relation_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OutfitStructureAnalyzer:
    """Annotate structure and inner/outer relations without changing score."""

    TROUSER_SUBCATEGORIES = {"trouser", "trousers", "pants", "jeans"}
    SKIRT_SUBCATEGORIES = {"skirt"}
    BLAZER_SUBCATEGORIES = {"blazer"}
    CARDIGAN_SUBCATEGORIES = {"cardigan"}

    @staticmethod
    def _items(candidate: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
        items = candidate.get("items", {})
        if not isinstance(items, Mapping):
            return {}
        return {
            str(slot): item
            for slot, item in items.items()
            if isinstance(item, Mapping)
        }

    @staticmethod
    def _subcategory(item: Optional[Mapping[str, Any]]) -> str:
        if not isinstance(item, Mapping):
            return ""
        value = item.get("subcategory")
        return "" if value is None else str(value).strip().casefold()

    @staticmethod
    def _pattern(item: Optional[Mapping[str, Any]]) -> str:
        if not isinstance(item, Mapping):
            return ""
        profile = item.get("pattern_profile", {})
        if isinstance(profile, Mapping) and profile.get("type") is not None:
            value = profile.get("type")
        else:
            value = item.get("pattern")
        return "" if value is None else str(value).strip().casefold()

    @classmethod
    def _layer_relation(cls, items):
        inner = items.get("top") or items.get("dress")
        outer = items.get("outerwear")
        if inner is None or outer is None:
            return [], []

        inner_pattern = cls._pattern(inner)
        outer_pattern = cls._pattern(outer)

        if inner_pattern and inner_pattern != "solid" and outer_pattern == "solid":
            return [31], ["pattern_inner_solid_outer"]

        if inner_pattern == "solid" and outer_pattern and outer_pattern != "solid":
            return [32], ["solid_inner_pattern_outer"]

        return [], []

    @classmethod
    def _base_card(cls, items):
        outer_subcategory = cls._subcategory(items.get("outerwear"))

        if "top" in items and "bottom" in items:
            bottom_subcategory = cls._subcategory(items.get("bottom"))

            if bottom_subcategory in cls.TROUSER_SUBCATEGORIES:
                if outer_subcategory in cls.BLAZER_SUBCATEGORIES:
                    return 28, "top+trousers+blazer"
                if "outerwear" not in items:
                    return 26, "top+trousers"

            if bottom_subcategory in cls.SKIRT_SUBCATEGORIES:
                if outer_subcategory in cls.CARDIGAN_SUBCATEGORIES:
                    return 29, "top+skirt+cardigan"
                if "outerwear" not in items:
                    return 27, "top+skirt"

        if (
            "dress" in items
            and outer_subcategory in (
                cls.BLAZER_SUBCATEGORIES | cls.CARDIGAN_SUBCATEGORIES
            )
        ):
            return 30, "dress+blazer/cardigan"

        return None, None

    @classmethod
    def analyze(cls, candidate: Mapping[str, Any]) -> OutfitStructureResult:
        items = cls._items(candidate)
        base_card_id, base_structure = cls._base_card(items)
        has_inner = "top" in items or "dress" in items
        has_outer = "outerwear" in items
        layer_count = 2 if has_inner and has_outer else 1
        relation_card_ids, relation_tags = cls._layer_relation(items)

        return OutfitStructureResult(
            base_card_id=base_card_id,
            base_structure=base_structure,
            layer_count=layer_count,
            is_layered=layer_count > 1,
            relation_card_ids=relation_card_ids,
            relation_tags=relation_tags,
        )


__all__ = ["OutfitStructureResult", "OutfitStructureAnalyzer"]
