from dataclasses import (
    dataclass,
    field,
)

from typing import (
    List,
)


from herstyle_ai.styling.pattern_scorer import (
    PatternHarmonyScorer,
)


# =========================================================
# RESULT
# =========================================================

@dataclass
class PatternOutfitResult:

    # Deterministic styling score.
    #
    # NOT:
    # - probability
    # - learned compatibility
    # - calibrated confidence

    score: float

    relation: str

    reasons: List[str] = field(
        default_factory=list
    )


# =========================================================
# PATTERN OUTFIT SCORER
# =========================================================

class PatternOutfitScorer:

    GARMENT_SLOTS = (
        "top",
        "bottom",
        "dress",
        "outerwear",
    )

    # =====================================================
    # OUTFIT-LEVEL CALIBRATION
    # =====================================================

    SCORE_SINGLE_GARMENT = 0.70

    BONUS_POSITION_RULE = 0.02

    BONUS_SOLID_BLAZER = 0.01

    BONUS_PRINTED_DRESS = 0.01

    # =====================================================
    # GLOBAL PATTERN CONFLICT CAPS
    #
    # Prevent extra solid garments from diluting
    # a multiple-pattern conflict.
    # =====================================================

    MAX_SCORE_MULTIPLE_PATTERNS = 0.55

    MAX_SCORE_PRIMARY_PATTERN_CONFLICT = 0.45

    def __init__(
        self,
        pair_scorer: PatternHarmonyScorer,
    ):

        self.pair_scorer = (
            pair_scorer
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _get_items(
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

        return {

            slot: item

            for slot, item in items.items()

            if (
                slot in self.GARMENT_SLOTS
                and isinstance(
                    item,
                    dict,
                )
            )
        }

    def _get_pattern(
        self,
        item,
    ):

        profile = item.get(
            "pattern_profile",
            {},
        )

        if isinstance(
            profile,
            dict,
        ):

            value = profile.get(
                "type"
            )

            if value is not None:

                return value

        return item.get(
            "pattern"
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
    # SCORE
    # =====================================================

    def score_candidate(
        self,
        candidate,
    ):

        items = self._get_items(
            candidate
        )

        # ---------------------------------------------
        # No garment information
        # ---------------------------------------------

        if not items:

            return PatternOutfitResult(
                score=0.50,
                relation="unknown",
                reasons=[
                    "no_garment_pattern_information"
                ],
            )

        slots = list(
            items.keys()
        )

        patterned_slots = [

            slot

            for slot, item in items.items()

            if not self._is_solid(
                item
            )
        ]

        # =============================================
        # GLOBAL PATTERN CONFLICT
        # =============================================

        max_patterned_items = int(
            self.pair_scorer
            .pattern_config
            .general_rules
            .get(
                "max_patterned_items_default",
                1,
            )
        )

        has_multiple_patterns = (
            len(
                patterned_slots
            )
            > max_patterned_items
        )

        has_primary_pattern_conflict = False

        if has_multiple_patterns:

            for slot in patterned_slots:

                item = items[
                    slot
                ]

                profiles = (
                    self.pair_scorer
                    .resolve_item_profiles(
                        item
                    )
                )

                for profile_name in profiles:

                    profile = (
                        self.pair_scorer
                        .pattern_config
                        .get_profile(
                            profile_name
                        )
                    )

                    if profile.get(
                        "primary_visual_accent",
                        False,
                    ):

                        has_primary_pattern_conflict = True

                        break

                if has_primary_pattern_conflict:

                    break

        # ---------------------------------------------
        # Single garment
        #
        # Example:
        # dress + shoes
        #
        # Shoes are intentionally ignored for pattern
        # rules in V1.
        # ---------------------------------------------

        if len(items) == 1:

            slot = slots[0]

            item = items[
                slot
            ]

            if self._is_solid(
                item
            ):

                return PatternOutfitResult(
                    score=self.SCORE_SINGLE_GARMENT,
                    relation="single_solid_garment",
                    reasons=[
                        f"single_solid_slot:{slot}"
                    ],
                )

            return PatternOutfitResult(
                score=self.SCORE_SINGLE_GARMENT,
                relation="single_patterned_garment",
                reasons=[
                    f"single_patterned_slot:{slot}"
                ],
            )

        # ---------------------------------------------
        # Pairwise garment scores
        # ---------------------------------------------

        pair_scores = []

        reasons = []

        # P8.5 layer relations are explanatory metadata only.  The
        # pattern score itself is unchanged, so these reasons do not
        # double-count the existing pattern-with-solid rules.
        structure_analysis = candidate.get(
            "structure_analysis",
            {},
        )

        if not isinstance(
            structure_analysis,
            dict,
        ):

            structure_analysis = {}

        relation_tags = structure_analysis.get(
            "relation_tags",
            [],
        )

        if not isinstance(
            relation_tags,
            (list, tuple, set),
        ):

            relation_tags = []

        if "pattern_inner_solid_outer" in relation_tags:

            reasons.append(
                "layering:"
                "pattern_inner_solid_outer"
            )

        if "solid_inner_pattern_outer" in relation_tags:

            reasons.append(
                "layering:"
                "solid_inner_pattern_outer"
            )

        item_pairs = []

        for i in range(
            len(slots)
        ):

            for j in range(
                i + 1,
                len(slots),
            ):

                slot_a = slots[i]
                slot_b = slots[j]

                item_a = items[
                    slot_a
                ]

                item_b = items[
                    slot_b
                ]

                result = (
                    self.pair_scorer
                    .score_pair(
                        item_a,
                        item_b,
                    )
                )

                pair_scores.append(
                    result.score
                )

                item_pairs.append(
                    (
                        slot_a,
                        slot_b,
                        result,
                    )
                )

                reasons.extend(
                    [
                        f"{slot_a}+{slot_b}:{reason}"

                        for reason
                        in result.reasons
                    ]
                )

        # ---------------------------------------------
        # Base score
        # ---------------------------------------------

        if pair_scores:

            score = (
                sum(
                    pair_scores
                )
                / len(
                    pair_scores
                )
            )

        else:

            score = 0.50

        # =============================================
        # OUTFIT POSITION RULES
        # =============================================

        slot_bonus = 0.0

        # ---------------------------------------------
        # Pattern top + solid bottom
        # ---------------------------------------------

        if (
            "top" in items
            and "bottom" in items
            and not self._is_solid(
                items[
                    "top"
                ]
            )
            and self._is_solid(
                items[
                    "bottom"
                ]
            )
        ):

            slot_bonus += (
                self.BONUS_POSITION_RULE
            )

            reasons.append(
                "outfit_rule:"
                "pattern_top_solid_bottom"
            )

        # ---------------------------------------------
        # Solid top + pattern bottom
        # ---------------------------------------------

        if (
            "top" in items
            and "bottom" in items
            and self._is_solid(
                items[
                    "top"
                ]
            )
            and not self._is_solid(
                items[
                    "bottom"
                ]
            )
        ):

            slot_bonus += (
                self.BONUS_POSITION_RULE
            )

            reasons.append(
                "outfit_rule:"
                "solid_top_pattern_bottom"
            )

        # ---------------------------------------------
        # Pattern + solid outerwear
        # ---------------------------------------------

        if (
            "outerwear" in items
            and self._is_solid(
                items[
                    "outerwear"
                ]
            )
        ):

            patterned_main_slot = None

            if (
                "top" in items
                and not self._is_solid(
                    items[
                        "top"
                    ]
                )
            ):

                patterned_main_slot = (
                    "top"
                )

            elif (
                "dress" in items
                and not self._is_solid(
                    items[
                        "dress"
                    ]
                )
            ):

                patterned_main_slot = (
                    "dress"
                )

            if patterned_main_slot:

                slot_bonus += (
                    self.BONUS_POSITION_RULE
                )

                reasons.append(
                    "outfit_rule:"
                    "pattern_with_solid_outerwear"
                )

                outerwear_subcategory = (
                    items[
                        "outerwear"
                    ].get(
                        "subcategory"
                    )
                )

                if (
                    outerwear_subcategory
                    == "blazer"
                ):

                    slot_bonus += (
                        self.BONUS_SOLID_BLAZER
                    )

                    reasons.append(
                        "solid_blazer_with_pattern"
                    )

        # ---------------------------------------------
        # Printed dress + solid outerwear
        # ---------------------------------------------

        if (
            "dress" in items
            and "outerwear" in items
            and not self._is_solid(
                items[
                    "dress"
                ]
            )
            and self._is_solid(
                items[
                    "outerwear"
                ]
            )
        ):

            slot_bonus += (
                self.BONUS_PRINTED_DRESS
            )

            reasons.append(
                "outfit_rule:"
                "printed_dress_outerwear"
            )

        # =============================================
        # GLOBAL PATTERN COUNT
        # =============================================

        if len(
            patterned_slots
        ) == 0:

            reasons.append(
                "all_garments_solid"
            )

        elif len(
            patterned_slots
        ) == 1:

            reasons.append(
                "single_patterned_garment"
            )

        else:

            reasons.append(
                "multiple_patterned_garments"
            )

        # ---------------------------------------------
        # Apply small slot-rule bonus
        #
        # Pairwise harmony remains the main signal.
        # ---------------------------------------------

        score += slot_bonus

        # =============================================
        # GLOBAL PATTERN CONFLICT CAP
        #
        # Pairwise averaging must NOT allow extra solid
        # garments to hide a multi-pattern conflict.
        # =============================================

        if has_multiple_patterns:

            if has_primary_pattern_conflict:

                score = min(
                    score,
                    self.MAX_SCORE_PRIMARY_PATTERN_CONFLICT,
                )

                reasons.append(
                    "global_pattern_cap:"
                    "primary_pattern_conflict"
                )

            else:

                score = min(
                    score,
                    self.MAX_SCORE_MULTIPLE_PATTERNS,
                )

                reasons.append(
                    "global_pattern_cap:"
                    "multiple_patterns"
                )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        # ---------------------------------------------
        # Relation
        # ---------------------------------------------

        if len(
            patterned_slots
        ) == 0:

            relation = (
                "all_solid"
            )

        elif len(
            patterned_slots
        ) == 1:

            relation = (
                "single_pattern_coordination"
            )

        else:

            relation = (
                "multiple_pattern_coordination"
            )

        return PatternOutfitResult(
            score=round(
                score,
                4,
            ),
            relation=relation,
            reasons=reasons,
        )
