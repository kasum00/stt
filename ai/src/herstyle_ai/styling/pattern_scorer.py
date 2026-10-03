from dataclasses import (
    dataclass,
    field,
)

from typing import (
    List,
)


from herstyle_ai.styling.color_config import (
    ColorStylingConfig,
)

from herstyle_ai.styling.pattern_config import (
    PatternStylingConfig,
)


# =========================================================
# RESULT
# =========================================================

@dataclass
class PatternHarmonyResult:

    # Deterministic rule score.
    #
    # NOT a probability.
    # NOT a learned compatibility score.

    score: float

    relation: str

    reasons: List[str] = field(
        default_factory=list
    )


# =========================================================
# PATTERN HARMONY SCORER
# =========================================================

class PatternHarmonyScorer:

    # =====================================================
    # CALIBRATED V1 SCORE SCALE
    # =====================================================

    SCORE_UNKNOWN = 0.50
    # Safe but not exceptional.
    SCORE_SOLID_PAIR = 0.78
    SCORE_MULTIPLE_PATTERNS = 0.40
    # Especially strong conflict:
    # large / primary accent pattern + another pattern.
    SCORE_PRIMARY_PATTERN_CONFLICT = 0.25
    # Pattern + solid is the preferred baseline.
    SCORE_PATTERN_SOLID_BASE = 0.72
    BONUS_REPEAT_MOTIF = 0.12
    BONUS_REPEAT_BACKGROUND = 0.07
    BONUS_NEUTRAL_COMPANION = 0.05
    PENALTY_NEW_MULTICOLOR = 0.15

    def __init__(
        self,
        pattern_config: PatternStylingConfig,
        color_config: ColorStylingConfig,
    ):

        self.pattern_config = (
            pattern_config
        )

        self.color_config = (
            color_config
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _get_pattern(
        self,
        item,
    ):

        profile = item.get(
            "pattern_profile",
            {},
        )

        if not isinstance(
            profile,
            dict,
        ):

            profile = {}

        return (
            profile.get(
                "type"
            )
            or item.get(
                "pattern"
            )
        )

    def _get_pattern_profile(
        self,
        item,
    ):

        profile = item.get(
            "pattern_profile",
            {},
        )

        if not isinstance(
            profile,
            dict,
        ):

            return {}

        return profile

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

    def _is_solid(
        self,
        item,
    ):

        return (
            self._get_pattern(
                item
            )
            == "solid"
        )

    # =====================================================
    # RESOLVE PROFILES
    # =====================================================

    def resolve_item_profiles(
        self,
        item,
    ):

        profile = (
            self._get_pattern_profile(
                item
            )
        )

        base_pattern = (
            self._get_pattern(
                item
            )
        )

        if base_pattern is None:

            return []

        motif_colors = profile.get(
            "motif_colors",
            [],
        )

        if not isinstance(
            motif_colors,
            list,
        ):

            motif_colors = []

        return (
            self.pattern_config
            .resolve_profiles(
                base_pattern=base_pattern,
                scale=profile.get(
                    "scale"
                ),
                orientation=profile.get(
                    "orientation"
                ),
                tone_relation=profile.get(
                    "tone_relation"
                ),
                motif_color_count=len(
                    set(
                        motif_colors
                    )
                ),
            )
        )

    # =====================================================
    # SCORE PAIR
    # =====================================================

    def score_pair(
        self,
        item_a,
        item_b,
    ):

        pattern_a = (
            self._get_pattern(
                item_a
            )
        )

        pattern_b = (
            self._get_pattern(
                item_b
            )
        )

        # ---------------------------------------------
        # Missing information
        # ---------------------------------------------

        if (
            pattern_a is None
            or pattern_b is None
        ):

            return PatternHarmonyResult(
                score=self.SCORE_UNKNOWN,
                relation="unknown",
                reasons=[
                    "missing_pattern_information"
                ],
            )

        solid_a = self._is_solid(
            item_a
        )

        solid_b = self._is_solid(
            item_b
        )

        # ---------------------------------------------
        # SOLID + SOLID
        # ---------------------------------------------

        if solid_a and solid_b:

            return PatternHarmonyResult(
                score=self.SCORE_SOLID_PAIR,
                relation="solid_pair",
                reasons=[
                    "both_items_solid"
                ],
            )

        # ---------------------------------------------
        # PATTERN + PATTERN
        # ---------------------------------------------

        if (
            not solid_a
            and not solid_b
        ):

            profiles_a = (
                self.resolve_item_profiles(
                    item_a
                )
            )

            profiles_b = (
                self.resolve_item_profiles(
                    item_b
                )
            )

            primary_accent = False

            for profile_name in (
                profiles_a
                + profiles_b
            ):

                profile = (
                    self.pattern_config
                    .get_profile(
                        profile_name
                    )
                )

                if profile.get(
                    "primary_visual_accent",
                    False,
                ):

                    primary_accent = True

            if primary_accent:

                return PatternHarmonyResult(
                    score=self.SCORE_PRIMARY_PATTERN_CONFLICT,
                    relation="pattern_conflict",
                    reasons=[
                        "primary_pattern_with_second_pattern"
                    ],
                )

            return PatternHarmonyResult(
                score=self.SCORE_MULTIPLE_PATTERNS,
                relation="multiple_patterns",
                reasons=[
                    "two_patterned_items"
                ],
            )

        # ---------------------------------------------
        # Identify patterned / solid item
        # ---------------------------------------------

        if solid_a:

            solid_item = item_a
            pattern_item = item_b

        else:

            solid_item = item_b
            pattern_item = item_a

        pattern_profile = (
            self._get_pattern_profile(
                pattern_item
            )
        )

        motif_colors = list(
            pattern_profile.get(
                "motif_colors",
                [],
            )
            or []
        )

        background_color = (
            pattern_profile.get(
                "background_color"
            )
        )

        solid_color = (
            self._get_dominant_color(
                solid_item
            )
        )

        # ---------------------------------------------
        # PATTERN + SOLID baseline
        # ---------------------------------------------

        score = (
            self.SCORE_PATTERN_SOLID_BASE
        )

        reasons = [
            "pattern_with_solid"
        ]

        # ---------------------------------------------
        # Repeat motif color
        # ---------------------------------------------

        if (
            solid_color is not None
            and solid_color
            in motif_colors
        ):

            score += (
                self.BONUS_REPEAT_MOTIF
            )

            reasons.append(
                "solid_repeats_motif_color:"
                + solid_color
            )

        # ---------------------------------------------
        # Repeat background color
        # ---------------------------------------------

        elif (
            solid_color is not None
            and background_color
            is not None
            and solid_color
            == background_color
        ):

            score += (
                self.BONUS_REPEAT_BACKGROUND
            )

            reasons.append(
                "solid_repeats_background_color:"
                + solid_color
            )

        # ---------------------------------------------
        # Neutral companion
        # ---------------------------------------------

        elif (
            solid_color is not None
            and self.color_config.has_color(
                solid_color
            )
            and self.color_config.is_neutral(
                solid_color
            )
        ):

            score += (
                self.BONUS_NEUTRAL_COMPANION
            )

            reasons.append(
                "neutral_solid_companion:"
                + solid_color
            )

        # ---------------------------------------------
        # MULTICOLOR RESTRICTION
        # ---------------------------------------------

        item_profiles = (
            self.resolve_item_profiles(
                pattern_item
            )
        )

        if (
            "multicolor_print"
            in item_profiles
            and solid_color is not None
        ):

            palette = set(
                motif_colors
            )

            if background_color is not None:

                palette.add(
                    background_color
                )

            is_neutral = (
                self.color_config.has_color(
                    solid_color
                )
                and self.color_config.is_neutral(
                    solid_color
                )
            )

            if (
                solid_color not in palette
                and not is_neutral
            ):

                score -= (
                    self.PENALTY_NEW_MULTICOLOR
                )

                reasons.append(
                    "new_color_outside_multicolor_palette:"
                    + solid_color
                )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        return PatternHarmonyResult(
            score=round(
                score,
                4,
            ),
            relation="pattern_solid_coordination",
            reasons=reasons,
        )
