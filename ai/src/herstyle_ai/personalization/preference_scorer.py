from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping


# =========================================================
# RESULT
# =========================================================

@dataclass
class PreferenceScoreResult:
    score: float
    item_scores: Dict[str, float]
    components: Dict[str, float]
    reasons: list[str]


# =========================================================
# USER PREFERENCE SCORER
# =========================================================

class UserPreferenceScorer:
    """Score wardrobe items against a persisted preference profile.

    Each preference dimension is normalized independently by its largest
    absolute signal.  This keeps the result in [-1, 1] even when the profile
    contains more feedback events over time.
    """

    DIMENSIONS = (
        "category",
        "subcategory",
        "color",
        "pattern",
        "style_tags",
        "item_id",
    )

    def __init__(
        self,
        profile: Any,
    ):
        self.profile = profile

    @staticmethod
    def _dimension_values(
        item: Mapping[str, Any],
        dimension: str,
    ) -> list[str]:
        if dimension == "style_tags":
            value = item.get("style_tags")

            if value is None:
                value = item.get("styles")

            if value is None:
                value = item.get("style")

            if value is None:
                value = item.get("tags")

            if value is None:
                return []

            if isinstance(value, str):
                return [
                    part.strip()
                    for part in value.split(",")
                    if part.strip()
                ]

            if isinstance(value, Iterable):
                return [
                    str(part)
                    for part in value
                    if part is not None and str(part)
                ]

            return [str(value)]

        value = item.get(dimension)

        if value is None:
            return []

        if isinstance(value, (list, tuple, set)):
            return [
                str(part)
                for part in value
                if part is not None
            ]

        return [str(value)]

    @staticmethod
    def _profile_values(
        profile: Any,
        dimension: str,
    ) -> Dict[str, float]:
        if isinstance(profile, Mapping):
            values = profile.get(dimension, {})
        else:
            values = getattr(
                profile,
                dimension,
                {},
            )

        if not isinstance(values, Mapping):
            return {}

        return {
            str(key): float(value)
            for key, value in values.items()
            if isinstance(value, (int, float))
        }

    @classmethod
    def _normalised_signal(
        cls,
        profile: Any,
        dimension: str,
        value: str,
    ) -> float:
        values = cls._profile_values(
            profile,
            dimension,
        )

        if not values:
            return 0.0

        maximum = max(
            abs(signal)
            for signal in values.values()
        )

        if maximum == 0.0:
            return 0.0

        return max(
            -1.0,
            min(
                1.0,
                values.get(value, 0.0) / maximum,
            ),
        )

    @staticmethod
    def _mean(
        values: list[float],
    ) -> float:
        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _reason(
        dimension: str,
        values: list[str],
        signal: float,
    ) -> str:
        label = ", ".join(values)

        if signal > 0:
            return (
                f"likes {dimension}={label} "
                f"({signal:+.3f})"
            )

        if signal < 0:
            return (
                f"dislikes {dimension}={label} "
                f"({signal:+.3f})"
            )

        return (
            f"no learned signal for {dimension}={label}"
        )

    def score_item(
        self,
        item: Mapping[str, Any],
    ) -> PreferenceScoreResult:
        if not isinstance(item, Mapping):
            raise TypeError(
                "item must be a mapping"
            )

        components: Dict[str, float] = {}
        reasons: list[str] = []

        for dimension in self.DIMENSIONS:
            values = self._dimension_values(
                item,
                dimension,
            )

            if not values:
                continue

            signals = [
                self._normalised_signal(
                    self.profile,
                    dimension,
                    value,
                )
                for value in values
            ]
            signal = self._mean(signals)

            # Do not let unknown values dilute a score.  A dimension is
            # included when the profile has a non-zero signal for at least
            # one of the item's values.
            profile_values = self._profile_values(
                self.profile,
                dimension,
            )
            known_signals = [
                value
                for value in values
                if value in profile_values
                and profile_values[value] != 0
            ]

            if not known_signals:
                continue

            components[dimension] = round(
                signal,
                6,
            )
            reasons.append(
                self._reason(
                    dimension,
                    known_signals,
                    signal,
                )
            )

        score = self._mean(
            list(
                components.values()
            )
        )
        score = max(
            -1.0,
            min(
                1.0,
                score,
            ),
        )

        item_id = item.get("item_id")
        item_key = (
            str(item_id)
            if item_id is not None
            else "item"
        )

        if not reasons:
            reasons.append(
                "no matching preference signals"
            )

        return PreferenceScoreResult(
            score=round(score, 6),
            item_scores={
                item_key: round(score, 6),
            },
            components=components,
            reasons=reasons,
        )

    def score_candidate(
        self,
        candidate: Mapping[str, Any],
    ) -> PreferenceScoreResult:
        if not isinstance(candidate, Mapping):
            raise TypeError(
                "candidate must be a mapping"
            )

        items = candidate.get("items", {})

        if not isinstance(items, Mapping):
            raise ValueError(
                "candidate.items must be a mapping"
            )

        item_scores: Dict[str, float] = {}
        component_values: Dict[str, list[float]] = {}
        reasons: list[str] = []

        for slot, item in items.items():
            result = self.score_item(item)
            item_scores[str(slot)] = result.score
            reasons.extend(
                f"{slot}: {reason}"
                for reason in result.reasons
            )

            for dimension, value in result.components.items():
                component_values.setdefault(
                    dimension,
                    [],
                ).append(value)

        components = {
            dimension: round(
                self._mean(values),
                6,
            )
            for dimension, values
            in component_values.items()
        }

        score = self._mean(
            list(
                item_scores.values()
            )
        )

        return PreferenceScoreResult(
            score=round(score, 6),
            item_scores=item_scores,
            components=components,
            reasons=reasons or [
                "no matching preference signals"
            ],
        )


__all__ = [
    "PreferenceScoreResult",
    "UserPreferenceScorer",
]
