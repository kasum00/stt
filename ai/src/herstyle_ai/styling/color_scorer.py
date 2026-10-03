from dataclasses import (
    dataclass,
    field,
)

from typing import (
    List,
    Optional,
)


from herstyle_ai.styling.color_config import (
    ColorStylingConfig,
)


# =========================================================
# COLOR SCORE RESULT
# =========================================================

@dataclass
class ColorHarmonyResult:

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # This is a deterministic styling-rule score.
    #
    # It is NOT:
    # - a probability
    # - a calibrated confidence
    # - a learned compatibility score
    # -----------------------------------------------------

    score: float

    relation: str

    reasons: List[str] = field(
        default_factory=list
    )


# =========================================================
# COLOR HARMONY SCORER
# =========================================================

class ColorHarmonyScorer:

    # =====================================================
    # CALIBRATED V1 SCORE SCALE
    #
    # These are deterministic engineering values.
    # NOT probabilities.
    # =====================================================

    SCORE_UNKNOWN = 0.50
    SCORE_SINGLE_COLOR = 0.68
    # Same color is safe, but should NOT automatically
    # be considered an excellent outfit.
    SCORE_SAME_COLOR = 0.84
    # Explicit harmony is slightly stronger than simply
    # repeating exactly the same color.
    SCORE_SAME_HARMONY = 0.88
    SCORE_NEUTRAL_BALANCE = 0.78
    SCORE_SAME_FAMILY = 0.72
    SCORE_UNCLASSIFIED = 0.60
    # Explicit office palette from the styling knowledge
    # base is the strongest color rule in V1.
    SCORE_OFFICE_COMBINATION = 0.95

    def __init__(
        self,
        config: ColorStylingConfig,
    ):

        self.config = config

    # =====================================================
    # VALIDATE COLOR
    # =====================================================

    def _validate_color(
        self,
        color: Optional[str],
    ):

        if color is None:

            return

        if not self.config.has_color(
            color
        ):

            raise ValueError(
                f"Unknown styling color: {color}"
            )

    # =====================================================
    # SCORE TWO COLORS
    # =====================================================

    def score_pair(
        self,
        color_a: Optional[str],
        color_b: Optional[str],
    ):

        # ---------------------------------------------
        # Missing information
        #
        # 0.5 is a neutral engineering baseline.
        # It does NOT mean 50% probability.
        # ---------------------------------------------

        if (
            color_a is None
            or color_b is None
        ):

            return ColorHarmonyResult(
                score=self.SCORE_UNKNOWN,
                relation="unknown",
                reasons=[
                    "missing_color_information"
                ],
            )

        self._validate_color(
            color_a
        )

        self._validate_color(
            color_b
        )

        # ---------------------------------------------
        # SAME COLOR
        # ---------------------------------------------

        if color_a == color_b:

            return ColorHarmonyResult(
                score=self.SCORE_SAME_COLOR,
                relation="same_color",
                reasons=[
                    f"repeated_color:{color_a}"
                ],
            )

        # ---------------------------------------------
        # SAME HARMONY GROUP
        # ---------------------------------------------

        if (
            self.config.same_harmony_group(
                color_a,
                color_b,
            )
        ):

            groups_a = set(
                self.config.get_harmony_groups(
                    color_a
                )
            )

            groups_b = set(
                self.config.get_harmony_groups(
                    color_b
                )
            )

            common_groups = sorted(
                groups_a
                & groups_b
            )

            return ColorHarmonyResult(
                score=self.SCORE_SAME_HARMONY,
                relation="same_harmony_group",
                reasons=[
                    "harmony_group:"
                    + ",".join(
                        common_groups
                    )
                ],
            )

        # ---------------------------------------------
        # NEUTRAL + COLOR
        # ---------------------------------------------

        neutral_a = (
            self.config.is_neutral(
                color_a
            )
        )

        neutral_b = (
            self.config.is_neutral(
                color_b
            )
        )

        if (
            neutral_a
            or neutral_b
        ):

            return ColorHarmonyResult(
                score=self.SCORE_NEUTRAL_BALANCE,
                relation="neutral_balance",
                reasons=[
                    (
                        "neutral_color:"
                        + (
                            color_a
                            if neutral_a
                            else color_b
                        )
                    )
                ],
            )

        # ---------------------------------------------
        # SAME COLOR FAMILY
        # ---------------------------------------------

        family_a = (
            self.config.get_family(
                color_a
            )
        )

        family_b = (
            self.config.get_family(
                color_b
            )
        )

        if family_a == family_b:

            return ColorHarmonyResult(
                score=self.SCORE_SAME_FAMILY,
                relation="same_family",
                reasons=[
                    f"color_family:{family_a}"
                ],
            )

        # ---------------------------------------------
        # NO EXPLICIT RULE
        #
        # Do NOT call this a bad combination.
        #
        # The current knowledge base simply does not
        # contain an explicit positive relation yet.
        # ---------------------------------------------

        return ColorHarmonyResult(
            score=self.SCORE_UNCLASSIFIED,
            relation="unclassified",
            reasons=[
                "no_explicit_color_rule"
            ],
        )

    # =====================================================
    # FIND EXACT OFFICE COMBINATION
    # =====================================================

    def _find_office_combination(
        self,
        colors,
    ):

        clean_colors = [

            color

            for color in colors

            if color is not None
        ]

        if not clean_colors:

            return None

        for color in clean_colors:

            self._validate_color(
                color
            )

        target = frozenset(
            clean_colors
        )

        for (
            anchor,
            combinations,
        ) in (
            self.config
            .office_combinations
            .items()
        ):

            for combination in combinations:

                candidate = frozenset(
                    combination
                )

                if target == candidate:

                    return list(
                        combination
                    )

        return None

    # =====================================================
    # SCORE COLOR PALETTE
    #
    # Useful for:
    #
    # top + bottom + shoes
    # top + bottom + blazer
    # dress + outerwear + shoes
    # =====================================================

    def score_palette(
        self,
        colors,
    ):

        colors = [

            color

            for color in colors

            if color is not None
        ]

        if not colors:

            return ColorHarmonyResult(
                score=self.SCORE_UNKNOWN,
                relation="unknown",
                reasons=[
                    "no_color_information"
                ],
            )

        for color in colors:

            self._validate_color(
                color
            )

        # ---------------------------------------------
        # EXACT OFFICE COMBINATION
        # ---------------------------------------------

        office_match = (
            self._find_office_combination(
                colors
            )
        )

        if office_match is not None:

            return ColorHarmonyResult(
                score=self.SCORE_OFFICE_COMBINATION,
                relation="office_combination",
                reasons=[
                    "office_palette:"
                    + "+".join(
                        office_match
                    )
                ],
            )

        # ---------------------------------------------
        # ONE COLOR
        # ---------------------------------------------

        if len(colors) == 1:

            return ColorHarmonyResult(
                score=self.SCORE_SINGLE_COLOR,
                relation="single_color",
                reasons=[
                    f"single_color:{colors[0]}"
                ],
            )

        # ---------------------------------------------
        # SCORE ALL UNIQUE PAIRS
        # ---------------------------------------------

        pair_scores = []

        pair_reasons = []

        for i in range(
            len(colors)
        ):

            for j in range(
                i + 1,
                len(colors),
            ):

                result = self.score_pair(
                    colors[i],
                    colors[j],
                )

                pair_scores.append(
                    result.score
                )

                pair_reasons.extend(
                    result.reasons
                )

        if not pair_scores:

            return ColorHarmonyResult(
                score=self.SCORE_UNKNOWN,
                relation="unknown",
                reasons=[
                    "insufficient_color_information"
                ],
            )

        average_score = (
            sum(pair_scores)
            / len(pair_scores)
        )

        return ColorHarmonyResult(
            score=round(
                average_score,
                4,
            ),
            relation="pairwise_harmony",
            reasons=pair_reasons,
        )
