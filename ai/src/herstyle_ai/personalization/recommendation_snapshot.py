from typing import (
    Mapping,
)


def _safe_float(
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


def _snapshot_item(
    item,
):

    if not isinstance(
        item,
        Mapping,
    ):

        return {}

    return {
        "item_id": item.get(
            "item_id"
        ),
        "category": item.get(
            "category"
        ),
        "subcategory": item.get(
            "subcategory"
        ),
        "color": item.get(
            "color"
        ),
        "pattern": item.get(
            "pattern"
        ),
        "style_tags": list(
            item.get(
                "style_tags",
                [],
            )
            or []
        ),
    }


def build_recommendation_snapshot(
    recommendation_id,
    user_id,
    outfit,
    weather=None,
    request_applied=None,
):

    if not isinstance(
        outfit,
        Mapping,
    ):

        raise TypeError(
            "outfit must be a mapping"
        )

    if not isinstance(
        weather,
        Mapping,
    ):

        weather = {}

    items = outfit.get(
        "items",
        {},
    )

    if not isinstance(
        items,
        Mapping,
    ):

        items = {}

    item_snapshot = {
        str(slot): _snapshot_item(
            item
        )
        for slot, item in items.items()
    }

    structure_analysis = outfit.get(
        "structure_analysis",
        {},
    )

    if not isinstance(
        structure_analysis,
        Mapping,
    ):

        structure_analysis = {}

    return {
        "recommendation_id": str(
            recommendation_id
        ),
        "user_id": str(
            user_id
        ),
        "structure": outfit.get(
            "structure"
        ),
        "structure_analysis": dict(
            structure_analysis
        ),
        "items": item_snapshot,
        "compatibility_score": _safe_float(
            outfit.get(
                "compatibility_score"
            )
        ),
        "style_score": _safe_float(
            outfit.get(
                "style_score"
            )
        ),
        "base_score": _safe_float(
            outfit.get(
                "base_score"
            )
        ),
        "ranking_method": outfit.get(
            "ranking_method"
        ),
        "preference_score_v1": _safe_float(
            outfit.get(
                "preference_score"
            )
        ),
        "preference_rank_score": _safe_float(
            outfit.get(
                "preference_rank_score"
            )
        ),
        "personalization_confidence": _safe_float(
            outfit.get(
                "personalization_confidence"
            )
        ),
        "personalization_weight": _safe_float(
            outfit.get(
                "personalization_weight"
            )
        ),
        "personalized_score": _safe_float(
            outfit.get(
                "personalized_score"
            )
        ),
        "learned_preference_score": _safe_float(
            outfit.get(
                "learned_preference_score"
            )
        ),
        "learned_preference_rank_score": _safe_float(
            outfit.get(
                "learned_preference_rank_score"
            )
        ),
        "learned_model_version": outfit.get(
            "learned_model_version"
        ),
        "personalization_method": outfit.get(
            "personalization_method"
        ),
        "request_applied": (
            None
            if request_applied is None
            else bool(
                request_applied
            )
        ),
        "request_score": _safe_float(
            outfit.get(
                "request_score"
            )
        ),
        "request_rank_score": _safe_float(
            outfit.get(
                "request_rank_score"
            )
        ),
        "weather": {
            "date": weather.get(
                "date"
            ),
            "temperature": _safe_float(
                weather.get(
                    "temperature"
                )
            ),
            "apparent_temperature": _safe_float(
                weather.get(
                    "apparent_temperature"
                )
            ),
            "decision_temperature": _safe_float(
                weather.get(
                    "decision_temperature"
                )
            ),
            "precipitation_probability": _safe_float(
                weather.get(
                    "precipitation_probability"
                )
            ),
            "rain_risk": (
                None
                if weather.get(
                    "rain_risk"
                ) is None
                else bool(
                    weather.get(
                        "rain_risk"
                    )
                )
            ),
        },
    }


__all__ = [
    "build_recommendation_snapshot",
]
