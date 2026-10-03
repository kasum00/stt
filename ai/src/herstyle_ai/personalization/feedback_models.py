from dataclasses import (
    asdict,
    dataclass,
    field,
)

from datetime import (
    datetime,
    timezone,
)

import math

from typing import (
    Any,
    Dict,
    Optional,
)

from uuid import uuid4


# =========================================================
# SUPPORTED EVENTS
# =========================================================

SUPPORTED_FEEDBACK_EVENTS = {
    "outfit_shown",
    "outfit_opened",
    "outfit_liked",
    "outfit_disliked",
    "outfit_saved",
    "outfit_worn",
    "outfit_skipped",
    "outfit_regenerated",
    "item_replaced",
    "outfit_edited",
}


# =========================================================
# FEEDBACK EVENT
# =========================================================

@dataclass
class FeedbackEvent:

    event_type: str

    user_id: str

    structure: Optional[str] = None

    items: Dict[str, str] = field(
        default_factory=dict
    )

    compatibility_score: Optional[float] = None

    style_score: Optional[float] = None

    fusion_score: Optional[float] = None

    ranking_method: Optional[str] = None

    event_id: str = field(
        default_factory=lambda:
            str(
                uuid4()
            )
    )

    timestamp: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(
        self,
    ):

        if self.event_type not in (
            SUPPORTED_FEEDBACK_EVENTS
        ):

            raise ValueError(
                "Unsupported feedback event: "
                f"{self.event_type}"
            )

        if (
            not isinstance(
                self.user_id,
                str,
            )
            or not self.user_id.strip()
        ):

            raise ValueError(
                "user_id must be a non-empty string"
            )

        if not isinstance(
            self.items,
            dict,
        ):

            raise ValueError(
                "items must be a dictionary"
            )

        if not isinstance(
            self.metadata,
            dict,
        ):

            raise ValueError(
                "metadata must be a dictionary"
            )

        for score_name in (
            "compatibility_score",
            "style_score",
            "fusion_score",
        ):

            score = getattr(
                self,
                score_name,
            )

            if score is None:

                continue

            if not isinstance(
                score,
                (int, float),
            ) or not math.isfinite(
                float(
                    score
                )
            ):

                raise ValueError(
                    f"{score_name} must be a finite number"
                )

    def to_dict(
        self,
    ):

        return asdict(
            self
        )
