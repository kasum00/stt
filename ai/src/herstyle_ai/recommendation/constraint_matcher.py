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

from herstyle_ai.recommendation.styling_request_parser import (
    GarmentConstraint,
    StylingRequestConstraints,
    StylingRequestParser,
)


# =========================================================
# RESULT
# =========================================================

@dataclass
class ConstraintMatchResult:
    hard_match: bool
    request_score: Optional[float] = None
    hard_matches: List[str] = field(
        default_factory=list
    )
    violations: List[str] = field(
        default_factory=list
    )
    soft_matches: List[str] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =========================================================
# MATCHER
# =========================================================

class StylingConstraintMatcher:
    """Apply hard request constraints and score soft request preferences."""

    LIGHT_COLORS = {
        "white",
        "beige",
        "pink",
        "yellow",
        "orange",
        "light_blue",
    }

    DARK_COLORS = {
        "black",
        "brown",
        "gray",
        "grey",
        "navy",
        "purple",
        "dark_blue",
    }

    def __init__(
        self,
        parser: Optional[StylingRequestParser] = None,
    ):
        self.parser = parser or StylingRequestParser()

    @staticmethod
    def _values(
        item: Mapping[str, Any],
        field_name: str,
    ) -> List[str]:
        value = item.get(
            field_name
        )

        if value is None:
            return []

        if isinstance(value, (list, tuple, set)):
            return [
                str(entry).casefold()
                for entry in value
                if entry is not None
            ]

        return [
            str(value).casefold()
        ]

    @staticmethod
    def _constraint_values(
        value,
    ) -> List[str]:
        if value is None:
            return []

        if isinstance(value, (list, tuple, set)):
            return [
                str(entry).casefold()
                for entry in value
                if entry is not None
            ]

        return [
            str(value).casefold()
        ]

    @staticmethod
    def _add_unique(
        values: List[str],
        value: str,
    ):
        if value not in values:
            values.append(value)

    @classmethod
    def _items(
        cls,
        candidate: Mapping[str, Any],
    ) -> List[Mapping[str, Any]]:
        items = candidate.get(
            "items",
            {},
        )

        if not isinstance(items, Mapping):
            return []

        return [
            item
            for item in items.values()
            if isinstance(item, Mapping)
        ]

    @staticmethod
    def _coerce_constraints(
        constraints,
    ) -> StylingRequestConstraints:
        if isinstance(
            constraints,
            StylingRequestConstraints,
        ):
            return constraints

        if isinstance(constraints, Mapping):
            payload = dict(constraints)
            item_constraints = []

            for item_constraint in payload.get(
                "item_constraints",
                [],
            ):
                if isinstance(
                    item_constraint,
                    GarmentConstraint,
                ):
                    item_constraints.append(
                        item_constraint
                    )
                elif isinstance(
                    item_constraint,
                    Mapping,
                ):
                    item_constraints.append(
                        GarmentConstraint(
                            **item_constraint
                        )
                    )

            payload[
                "item_constraints"
            ] = item_constraints
            return StylingRequestConstraints(
                **payload
            )

        raise TypeError(
            "constraints must be StylingRequestConstraints "
            "or a mapping"
        )

    @classmethod
    def _has_value(
        cls,
        items: List[Mapping[str, Any]],
        field_name: str,
        expected: str,
    ) -> bool:
        return any(
            expected.casefold()
            in cls._values(
                item,
                field_name,
            )
            for item in items
        )

    @classmethod
    def _matches_garment(
        cls,
        item: Mapping[str, Any],
        constraint: GarmentConstraint,
    ) -> bool:
        if (
            constraint.category is not None
            and constraint.category.casefold()
            not in cls._values(item, "category")
        ):
            return False

        if (
            constraint.subcategory is not None
            and constraint.subcategory.casefold()
            not in cls._values(item, "subcategory")
        ):
            return False

        item_colors = cls._values(
            item,
            "color",
        )
        item_patterns = cls._values(
            item,
            "pattern",
        )

        preferred_colors = cls._constraint_values(
            constraint.preferred_colors
        )
        excluded_colors = cls._constraint_values(
            constraint.excluded_colors
        )
        preferred_patterns = cls._constraint_values(
            constraint.preferred_patterns
        )
        excluded_patterns = cls._constraint_values(
            constraint.excluded_patterns
        )

        if preferred_colors and not any(
            color in item_colors
            for color in preferred_colors
        ):
            return False

        if any(
            color in item_colors
            for color in excluded_colors
        ):
            return False

        if preferred_patterns and not any(
            pattern in item_patterns
            for pattern in preferred_patterns
        ):
            return False

        if any(
            pattern in item_patterns
            for pattern in excluded_patterns
        ):
            return False

        return True

    def _match_hard_constraints(
        self,
        items,
        constraints,
        hard_matches,
        violations,
    ):
        for category in constraints.include_categories:
            if self._has_value(
                items,
                "category",
                category,
            ):
                self._add_unique(
                    hard_matches,
                    f"required_category:{category}",
                )
            else:
                self._add_unique(
                    violations,
                    f"missing_category:{category}",
                )

        for category in constraints.exclude_categories:
            if self._has_value(
                items,
                "category",
                category,
            ):
                self._add_unique(
                    violations,
                    f"excluded_category:{category}",
                )
            else:
                self._add_unique(
                    hard_matches,
                    f"not_excluded_category:{category}",
                )

        for subcategory in constraints.include_subcategories:
            if self._has_value(
                items,
                "subcategory",
                subcategory,
            ):
                self._add_unique(
                    hard_matches,
                    f"required_subcategory:{subcategory}",
                )
            else:
                self._add_unique(
                    violations,
                    f"missing_subcategory:{subcategory}",
                )

        for subcategory in constraints.exclude_subcategories:
            if self._has_value(
                items,
                "subcategory",
                subcategory,
            ):
                self._add_unique(
                    violations,
                    f"excluded_subcategory:{subcategory}",
                )
            else:
                self._add_unique(
                    hard_matches,
                    f"not_excluded_subcategory:{subcategory}",
                )

        for color in constraints.excluded_colors:
            if self._has_value(
                items,
                "color",
                color,
            ):
                self._add_unique(
                    violations,
                    f"excluded_color:{color}",
                )

        for pattern in constraints.excluded_patterns:
            if self._has_value(
                items,
                "pattern",
                pattern,
            ):
                self._add_unique(
                    violations,
                    f"excluded_pattern:{pattern}",
                )

        for garment_constraint in constraints.item_constraints:
            if not garment_constraint.required:
                continue

            if any(
                self._matches_garment(
                    item,
                    garment_constraint,
                )
                for item in items
            ):
                label = (
                    garment_constraint.subcategory
                    or garment_constraint.category
                    or "garment"
                )
                self._add_unique(
                    hard_matches,
                    f"item_constraint:{label}",
                )
            else:
                label = (
                    garment_constraint.subcategory
                    or garment_constraint.category
                    or "garment"
                )
                self._add_unique(
                    violations,
                    f"item_constraint_not_met:{label}",
                )

    @classmethod
    def _color_group_score(
        cls,
        items,
        color_group,
    ):
        if color_group == "light":
            accepted = cls.LIGHT_COLORS
        elif color_group == "dark":
            accepted = cls.DARK_COLORS
        else:
            return None, []

        colors = [
            color
            for item in items
            for color in cls._values(item, "color")
        ]

        if not colors:
            return 0.0, []

        matches = [
            color
            for color in colors
            if color in accepted
        ]
        return (
            len(matches) / len(colors),
            [
                f"color_group:{color_group}"
            ]
            if matches
            else [],
        )

    @classmethod
    def _soft_dimension_score(
        cls,
        items,
        field_name,
        preferred_values,
    ):
        preferred_values = {
            str(value).casefold()
            for value in preferred_values
        }

        if not preferred_values:
            return None, []

        values = [
            value
            for item in items
            for value in cls._values(
                item,
                field_name,
            )
        ]

        if not values:
            return 0.0, []

        matches = [
            value
            for value in values
            if value in preferred_values
        ]

        return (
            len(matches) / len(values),
            [
                f"preferred_{field_name}"
            ]
            if matches
            else [],
        )

    def _score_soft_constraints(
        self,
        items,
        constraints,
        soft_matches,
    ):
        scores = []

        color_group_score, matches = self._color_group_score(
            items,
            constraints.preferred_color_group,
        )

        if color_group_score is not None:
            scores.append(color_group_score)
            soft_matches.extend(matches)

        for field_name, values in (
            (
                "color",
                constraints.preferred_colors,
            ),
            (
                "pattern",
                constraints.preferred_patterns,
            ),
        ):
            score, matches = self._soft_dimension_score(
                items,
                field_name,
                values,
            )

            if score is not None:
                scores.append(score)
                soft_matches.extend(matches)

        if not scores:
            return None

        return round(
            sum(scores) / len(scores),
            6,
        )

    def match(
        self,
        candidate: Mapping[str, Any],
        constraints,
    ) -> ConstraintMatchResult:
        if not isinstance(candidate, Mapping):
            raise TypeError(
                "candidate must be a mapping"
            )

        constraints = self._coerce_constraints(
            constraints
        )
        items = self._items(
            candidate
        )
        hard_matches = []
        violations = []
        soft_matches = []

        self._match_hard_constraints(
            items,
            constraints,
            hard_matches,
            violations,
        )
        request_score = self._score_soft_constraints(
            items,
            constraints,
            soft_matches,
        )

        return ConstraintMatchResult(
            hard_match=not violations,
            request_score=request_score,
            hard_matches=hard_matches,
            violations=violations,
            soft_matches=soft_matches,
        )


__all__ = [
    "ConstraintMatchResult",
    "StylingConstraintMatcher",
]
