from dataclasses import (
    dataclass,
    field,
)

from pathlib import Path

from typing import (
    Dict,
    List,
)

import yaml


from herstyle_ai.styling.color_scorer import (
    ColorHarmonyScorer,
)

from herstyle_ai.styling.pattern_outfit_scorer import (
    PatternOutfitScorer,
)


# =========================================================
# RESULT
# =========================================================

@dataclass
class StylingResult:

    # Final deterministic styling score.
    #
    # NOT:
    # - probability
    # - calibrated confidence
    # - learned compatibility score

    score: float

    color_score: float

    pattern_score: float

    reasons: List[str] = field(
        default_factory=list
    )

    components: Dict[
        str,
        float,
    ] = field(
        default_factory=dict
    )


# =========================================================
# STYLING SCORER
# =========================================================

class StylingScorer:

    COLOR_SLOTS = (
        "top",
        "bottom",
        "dress",
        "outerwear",
        "shoes",
    )

    def __init__(
        self,
        project_root,
        color_scorer: ColorHarmonyScorer,
        pattern_scorer: PatternOutfitScorer,
    ):

        self.project_root = Path(
            project_root
        )

        self.color_scorer = (
            color_scorer
        )

        self.pattern_scorer = (
            pattern_scorer
        )

        config_path = (
            self.project_root
            / "configs"
            / "styling_rules.yaml"
        )

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as f:

            config = (
                yaml.safe_load(
                    f
                )
                or {}
            )

        weights = config.get(
            "weights",
            {},
        )

        self.color_weight = float(
            weights.get(
                "color",
                0.55,
            )
        )

        self.pattern_weight = float(
            weights.get(
                "pattern",
                0.45,
            )
        )

        self._validate_weights()

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_weights(
        self,
    ):

        if self.color_weight < 0:

            raise ValueError(
                "color weight must be >= 0"
            )

        if self.pattern_weight < 0:

            raise ValueError(
                "pattern weight must be >= 0"
            )

        total = (
            self.color_weight
            + self.pattern_weight
        )

        if total <= 0:

            raise ValueError(
                "styling weights total must be > 0"
            )

        # Normalize automatically.
        self.color_weight /= total

        self.pattern_weight /= total

    # =====================================================
    # DOMINANT COLOR
    # =====================================================

    def _get_dominant_color(
        self,
        item,
    ):

        profile = item.get(
            "color_profile",
            {},
        )

        if isinstance(
            profile,
            dict,
        ):

            dominant = profile.get(
                "dominant"
            )

            if dominant is not None:

                return dominant

        return item.get(
            "color"
        )

    # =====================================================
    # OUTFIT COLORS
    # =====================================================

    def _get_outfit_colors(
        self,
        candidate,
    ):

        items = candidate.get(
            "items",
            {},
        )

        if not isinstance(
            items,
            dict,
        ):

            raise ValueError(
                "candidate['items'] must be a dict"
            )

        colors = []

        for slot in self.COLOR_SLOTS:

            item = items.get(
                slot
            )

            if not isinstance(
                item,
                dict,
            ):

                continue

            color = (
                self._get_dominant_color(
                    item
                )
            )

            if color is not None:

                colors.append(
                    color
                )

        return colors

    # =====================================================
    # SCORE CANDIDATE
    # =====================================================

    def score_candidate(
        self,
        candidate,
    ):

        # ---------------------------------------------
        # COLOR
        # ---------------------------------------------

        colors = (
            self._get_outfit_colors(
                candidate
            )
        )

        color_result = (
            self.color_scorer
            .score_palette(
                colors
            )
        )

        # ---------------------------------------------
        # PATTERN
        # ---------------------------------------------

        pattern_result = (
            self.pattern_scorer
            .score_candidate(
                candidate
            )
        )

        # ---------------------------------------------
        # COMBINE
        # ---------------------------------------------

        final_score = (
            self.color_weight
            * color_result.score
            +
            self.pattern_weight
            * pattern_result.score
        )

        final_score = max(
            0.0,
            min(
                1.0,
                final_score,
            ),
        )

        reasons = []

        reasons.extend(
            [
                f"color:{reason}"

                for reason
                in color_result.reasons
            ]
        )

        reasons.extend(
            [
                f"pattern:{reason}"

                for reason
                in pattern_result.reasons
            ]
        )

        return StylingResult(
            score=round(
                final_score,
                4,
            ),
            color_score=round(
                color_result.score,
                4,
            ),
            pattern_score=round(
                pattern_result.score,
                4,
            ),
            reasons=reasons,
            components={
                "color_weight":
                    round(
                        self.color_weight,
                        4,
                    ),

                "pattern_weight":
                    round(
                        self.pattern_weight,
                        4,
                    ),
            },
        )