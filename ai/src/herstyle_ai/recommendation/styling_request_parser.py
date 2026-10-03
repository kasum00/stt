from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Dict,
    List,
    Optional,
)

import re


# =========================================================
# CONSTRAINT MODEL
# =========================================================

@dataclass
class GarmentConstraint:
    category: Optional[str] = None
    subcategory: Optional[str] = None
    preferred_colors: List[str] = field(
        default_factory=list
    )
    excluded_colors: List[str] = field(
        default_factory=list
    )
    preferred_patterns: List[str] = field(
        default_factory=list
    )
    excluded_patterns: List[str] = field(
        default_factory=list
    )
    required: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class StylingRequestConstraints:
    raw_text: str
    target_day_offset: Optional[int] = None
    prefer_dress: Optional[bool] = None
    include_categories: List[str] = field(
        default_factory=list
    )
    exclude_categories: List[str] = field(
        default_factory=list
    )
    include_subcategories: List[str] = field(
        default_factory=list
    )
    exclude_subcategories: List[str] = field(
        default_factory=list
    )
    preferred_colors: List[str] = field(
        default_factory=list
    )
    excluded_colors: List[str] = field(
        default_factory=list
    )
    preferred_patterns: List[str] = field(
        default_factory=list
    )
    excluded_patterns: List[str] = field(
        default_factory=list
    )
    preferred_color_group: Optional[str] = None
    item_constraints: List[GarmentConstraint] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


# =========================================================
# RULE-BASED PARSER
# =========================================================

class StylingRequestParser:
    """Parse a small, deterministic V1 styling language.

    The parser produces constraints only.  It never chooses wardrobe items
    and it does not call an LLM.
    """

    _DAY_RULES = (
        (1, (
            "ngày mai",
            "mai",
            "tomorrow",
        )),
        (2, (
            "ngày kia",
            "ngày mốt",
            "mốt",
            "day after tomorrow",
        )),
        (0, (
            "hôm nay",
            "today",
        )),
    )

    # Specific subcategories come before broad category rules so phrases such
    # as "chân váy" are not mistaken for the dress category.
    _SUBCATEGORY_RULES = (
        ("shirt", (
            "sơ mi",
            "so mi",
            "shirt",
            "dress shirt",
        )),
        ("skirt", (
            "chân váy",
            "chan vay",
            "skirt",
        )),
        ("sneakers", (
            "sneaker",
            "sneakers",
            "giày thể thao",
            "giay the thao",
        )),
        ("flats", (
            "giày bệt",
            "giay bet",
            "flats",
        )),
        ("boots", (
            "boots",
            "boot",
            "giày bốt",
            "giay bot",
        )),
        ("sandals", (
            "sandals",
            "sandals",
            "dép sandal",
            "dep sandal",
        )),
        ("heels", (
            "heels",
            "high heels",
            "giày cao gót",
            "giay cao got",
        )),
        ("trousers", (
            "trousers",
            "pants",
            "quần dài",
            "quan dai",
        )),
    )

    _CATEGORY_RULES = (
        ("dress", (
            "váy",
            "vay",
            "đầm",
            "dam",
            "dress",
        )),
        ("top", (
            "áo",
            "ao",
            "top",
        )),
        ("bottom", (
            "quần",
            "quan",
            "bottom",
        )),
        ("shoes", (
            "giày",
            "giay",
            "dép",
            "dep",
            "shoes",
        )),
        ("outerwear", (
            "áo khoác",
            "ao khoac",
            "outerwear",
            "jacket",
            "coat",
        )),
    )

    _COLOR_RULES = (
        ("white", ("trắng", "trang", "white")),
        ("black", ("đen", "den", "black")),
        ("beige", ("be", "beige", "kem")),
        ("brown", ("nâu", "nau", "brown")),
        ("gray", ("xám", "xam", "ghi", "gray", "grey")),
        ("blue", ("xanh dương", "xanh biển", "blue")),
        ("green", ("xanh lá", "xanh la", "green")),
        ("red", ("đỏ", "do", "red")),
        ("pink", ("hồng", "hong", "pink")),
        ("yellow", ("vàng", "vang", "yellow")),
        ("purple", ("tím", "tim", "purple")),
        ("orange", ("cam", "orange")),
    )

    _PATTERN_RULES = (
        ("polka_dot", (
            "chấm bi",
            "cham bi",
            "polka dot",
            "polka_dot",
        )),
        ("striped", (
            "sọc",
            "soc",
            "kẻ sọc",
            "ke soc",
            "striped",
            "stripe",
        )),
        ("plaid", (
            "caro",
            "ca rô",
            "kẻ caro",
            "ke caro",
            "plaid",
        )),
        ("floral", (
            "hoa",
            "floral",
        )),
        ("solid", (
            "trơn",
            "tron",
            "solid",
        )),
    )

    # Canonical lookup tables used when binding nearby attributes to one
    # garment.  Keys are normalized user-facing keywords.
    SUBCATEGORIES = {
        alias: canonical
        for canonical, aliases in _SUBCATEGORY_RULES
        for alias in aliases
    }

    COLORS = {
        alias: canonical
        for canonical, aliases in _COLOR_RULES
        for alias in aliases
    }

    SUBCATEGORY_CATEGORY = {
        "blouse": "top",
        "shirt": "top",
        "t_shirt": "top",
        "sweater": "top",
        "cardigan": "top",
        "trousers": "bottom",
        "jeans": "bottom",
        "skirt": "bottom",
        "blazer": "outerwear",
        "jacket": "outerwear",
        "coat": "outerwear",
        "trench_coat": "outerwear",
        "heels": "shoes",
        "flats": "shoes",
        "loafers": "shoes",
        "sneakers": "shoes",
        "boots": "shoes",
        "sandals": "shoes",
    }

    CATEGORY_KEYWORDS = {
        alias: canonical
        for canonical, aliases in _CATEGORY_RULES
        for alias in aliases
    }

    _NEGATION_RE = re.compile(
        r"(?:không|ko|chẳng|chang|tránh|tranh|đừng|dung)"
        r"(?:\s+\S+){0,3}\s*$",
        re.IGNORECASE,
    )

    _WORD_BOUNDARY = r"(?<!\w){alias}(?!\w)"

    @staticmethod
    def _normalise_text(
        text: str,
    ) -> str:
        return " ".join(
            text.casefold().strip().split()
        )

    @classmethod
    def _matches(
        cls,
        text: str,
        aliases,
    ):
        patterns = sorted(
            aliases,
            key=len,
            reverse=True,
        )

        for alias in patterns:
            pattern = cls._WORD_BOUNDARY.format(
                alias=re.escape(alias)
            )

            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                yield match

    @classmethod
    def _is_negated(
        cls,
        text: str,
        start: int,
    ) -> bool:
        prefix = text[
            max(0, start - 32):start
        ]
        return bool(
            cls._NEGATION_RE.search(
                prefix
            )
        )

    @staticmethod
    def _add_unique(
        values: List[str],
        value: str,
    ):
        if value not in values:
            values.append(value)

    @classmethod
    def _extract_rules(
        cls,
        text: str,
        rules,
        included: List[str],
        excluded: List[str],
        occupied=None,
    ):
        if occupied is None:
            occupied = []

        found = []

        for canonical, aliases in rules:
            for match in cls._matches(
                text,
                aliases,
            ):
                span = match.span()

                if any(
                    span[0] < end
                    and start < span[1]
                    for start, end in occupied
                ):
                    continue

                occupied.append(span)
                found.append(
                    (
                        canonical,
                        cls._is_negated(
                            text,
                            span[0],
                        ),
                        span,
                    )
                )

        found.sort(
            key=lambda value: value[2][0]
        )

        for canonical, negated, _ in found:
            if negated:
                cls._add_unique(
                    excluded,
                    canonical,
                )
            else:
                cls._add_unique(
                    included,
                    canonical,
                )

        return occupied

    @staticmethod
    def _find_item_constraint(
        result,
        subcategory,
    ):
        for constraint in result.item_constraints:
            if constraint.subcategory == subcategory:
                return constraint

        return None

    def _ensure_item_constraint(
        self,
        result,
        subcategory,
    ):
        existing = self._find_item_constraint(
            result,
            subcategory,
        )

        if existing is not None:
            return existing

        constraint = GarmentConstraint(
            category=self.SUBCATEGORY_CATEGORY.get(
                subcategory
            ),
            subcategory=subcategory,
            required=True,
        )
        result.item_constraints.append(
            constraint
        )
        return constraint

    @staticmethod
    def _find_category_constraint(
        result,
        category,
    ):
        for constraint in result.item_constraints:
            if (
                constraint.category == category
                and constraint.subcategory is None
            ):
                return constraint

        return None

    def _ensure_category_constraint(
        self,
        result,
        category,
    ):
        existing = self._find_category_constraint(
            result,
            category,
        )

        if existing is not None:
            return existing

        # A specific subcategory already covers this broad category.
        if any(
            constraint.category == category
            for constraint in result.item_constraints
        ):
            return None

        constraint = GarmentConstraint(
            category=category,
            required=True,
        )
        result.item_constraints.append(
            constraint
        )
        return constraint

    @staticmethod
    def _between_has_boundary(
        text,
        first_end,
        second_start,
    ):
        if first_end > second_start:
            first_end, second_start = (
                second_start,
                first_end,
            )

        return bool(
            re.search(
                r"[,.;!?]",
                text[first_end:second_start],
            )
        )

    def _extract_bound_item_constraints(
        self,
        normalized,
        result,
    ):
        """Bind nearby colors to the garment they describe."""

        garment_matches = []

        for keyword, subcategory in sorted(
            self.SUBCATEGORIES.items(),
            key=lambda value: len(value[0]),
            reverse=True,
        ):
            for match in self._matches(
                normalized,
                (keyword,),
            ):
                span = match.span()

                if any(
                    span[0] < existing_end
                    and existing_start < span[1]
                    for existing_start, existing_end, _, _
                    in garment_matches
                ):
                    continue

                garment_matches.append(
                    (
                        span[0],
                        span[1],
                        subcategory,
                        False,
                    )
                )

        for keyword, category in sorted(
            self.CATEGORY_KEYWORDS.items(),
            key=lambda value: len(value[0]),
            reverse=True,
        ):
            for match in self._matches(
                normalized,
                (keyword,),
            ):
                span = match.span()

                if any(
                    span[0] < existing_end
                    and existing_start < span[1]
                    for existing_start, existing_end, _, _
                    in garment_matches
                ):
                    continue

                garment_matches.append(
                    (
                        span[0],
                        span[1],
                        category,
                        True,
                    )
                )

        positive_garments = []

        for start, end, value, is_category in sorted(
            garment_matches,
            key=lambda item: item[0],
        ):
            if self._is_negated(
                normalized,
                start,
            ):
                continue

            if is_category:
                constraint = self._ensure_category_constraint(
                    result,
                    value,
                )
            else:
                constraint = self._ensure_item_constraint(
                    result,
                    value,
                )

            if constraint is not None:
                positive_garments.append(
                    (
                        start,
                        end,
                        constraint,
                    )
                )

        color_matches = []

        for keyword, color in sorted(
            self.COLORS.items(),
            key=lambda value: len(value[0]),
            reverse=True,
        ):
            for match in self._matches(
                normalized,
                (keyword,),
            ):
                span = match.span()

                if any(
                    span[0] < existing_end
                    and existing_start < span[1]
                    for existing_start, existing_end, _ in color_matches
                ):
                    continue

                color_matches.append(
                    (
                        span[0],
                        span[1],
                        color,
                    )
                )

        for color_start, color_end, color in color_matches:
            candidates = []

            for garment_start, garment_end, constraint in positive_garments:
                if self._between_has_boundary(
                    normalized,
                    garment_end,
                    color_start,
                ):
                    continue

                if color_start >= garment_end:
                    distance = color_start - garment_end
                else:
                    distance = garment_start - color_end

                if distance < 0:
                    distance = 0

                if distance <= 24:
                    candidates.append(
                        (
                            distance,
                            constraint,
                        )
                    )

            if not candidates:
                continue

            _, constraint = min(
                candidates,
                key=lambda value: value[0],
            )

            if self._is_negated(
                normalized,
                color_start,
            ):
                self._add_unique(
                    constraint.excluded_colors,
                    color,
                )
            else:
                self._add_unique(
                    constraint.preferred_colors,
                    color,
                )

    @staticmethod
    def _remove_bound_colors(
        result,
    ):
        bound_preferred_colors = {
            color
            for constraint in result.item_constraints
            for color in constraint.preferred_colors
        }
        bound_excluded_colors = {
            color
            for constraint in result.item_constraints
            for color in constraint.excluded_colors
        }

        result.preferred_colors = [
            color
            for color in result.preferred_colors
            if color not in bound_preferred_colors
        ]
        result.excluded_colors = [
            color
            for color in result.excluded_colors
            if color not in bound_excluded_colors
        ]

    @classmethod
    def _extract_day_offset(
        cls,
        text: str,
    ) -> Optional[int]:
        for offset, aliases in cls._DAY_RULES:
            for match in cls._matches(
                text,
                aliases,
            ):
                if not cls._is_negated(
                    text,
                    match.start(),
                ):
                    return offset

        return None

    @classmethod
    def _extract_color_group(
        cls,
        text: str,
    ) -> Optional[str]:
        light_aliases = (
            "tone sáng",
            "tông sáng",
            "màu sáng",
            "mau sang",
            "light tone",
            "light colors",
        )
        dark_aliases = (
            "tone tối",
            "tông tối",
            "màu tối",
            "mau toi",
            "dark tone",
            "dark colors",
        )

        for alias in light_aliases:
            if re.search(
                cls._WORD_BOUNDARY.format(
                    alias=re.escape(alias)
                ),
                text,
                flags=re.IGNORECASE,
            ) and not cls._is_negated(
                text,
                text.find(alias),
            ):
                return "light"

        for alias in dark_aliases:
            if re.search(
                cls._WORD_BOUNDARY.format(
                    alias=re.escape(alias)
                ),
                text,
                flags=re.IGNORECASE,
            ) and not cls._is_negated(
                text,
                text.find(alias),
            ):
                return "dark"

        return None

    def parse(
        self,
        text: str,
    ) -> StylingRequestConstraints:
        if not isinstance(text, str):
            raise TypeError(
                "styling request text must be a string"
            )

        raw_text = text
        normalised = self._normalise_text(
            text
        )

        constraints = StylingRequestConstraints(
            raw_text=raw_text
        )

        constraints.target_day_offset = (
            self._extract_day_offset(
                normalised
            )
        )
        occupied = []

        self._extract_rules(
            normalised,
            self._SUBCATEGORY_RULES,
            constraints.include_subcategories,
            constraints.exclude_subcategories,
            occupied,
        )
        self._extract_rules(
            normalised,
            self._CATEGORY_RULES,
            constraints.include_categories,
            constraints.exclude_categories,
            occupied,
        )

        # Infer the broad category from a specific subcategory without
        # reinterpreting "chân váy" as the dress category.
        for subcategory in constraints.include_subcategories:
            inferred_category = {
                "shirt": "top",
                "skirt": "bottom",
                "trousers": "bottom",
                "sneakers": "shoes",
                "flats": "shoes",
                "boots": "shoes",
                "sandals": "shoes",
                "heels": "shoes",
            }.get(subcategory)

            if inferred_category:
                self._add_unique(
                    constraints.include_categories,
                    inferred_category,
                )

        self._extract_rules(
            normalised,
            self._COLOR_RULES,
            constraints.preferred_colors,
            constraints.excluded_colors,
        )

        self._extract_bound_item_constraints(
            normalised,
            constraints,
        )
        self._remove_bound_colors(
            constraints,
        )

        self._extract_rules(
            normalised,
            self._PATTERN_RULES,
            constraints.preferred_patterns,
            constraints.excluded_patterns,
        )

        constraints.preferred_color_group = (
            self._extract_color_group(
                normalised
            )
        )

        if "dress" in constraints.include_categories:
            constraints.prefer_dress = True
        elif "dress" in constraints.exclude_categories:
            constraints.prefer_dress = False

        return constraints


__all__ = [
    "GarmentConstraint",
    "StylingRequestConstraints",
    "StylingRequestParser",
]
