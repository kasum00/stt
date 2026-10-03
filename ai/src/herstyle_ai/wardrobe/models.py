# from dataclasses import (
#     dataclass,
#     field,
#     asdict,
# )

# from typing import (
#     Optional,
#     List,
#     Dict,
# )

# from datetime import (
#     datetime,
#     timezone,
# )


# # =========================================================
# # MATERIAL CANDIDATE
# # =========================================================

# @dataclass
# class MaterialCandidate:

#     label: str

#     score: float


# # =========================================================
# # WARDROBE ITEM
# # =========================================================

# @dataclass
# class WardrobeItem:

#     # -----------------------------------------------------
#     # Identity
#     # -----------------------------------------------------

#     item_id: str

#     image_path: str

#     created_at: str = field(
#         default_factory=lambda:
#             datetime.now(
#                 timezone.utc
#             ).isoformat()
#     )

#     # -----------------------------------------------------
#     # Main garment attributes
#     # -----------------------------------------------------

#     category: Optional[str] = None

#     subcategory: Optional[str] = None

#     color: Optional[str] = None

#     material: Optional[str] = None

#     pattern: Optional[str] = None

#     sleeve_length: Optional[str] = None

#     neckline: Optional[str] = None

#     fit: Optional[str] = None

#     # -----------------------------------------------------
#     # Multi-value attributes
#     # -----------------------------------------------------

#     design_details: List[str] = field(
#         default_factory=list
#     )

#     style_tags: List[str] = field(
#         default_factory=list
#     )

#     # -----------------------------------------------------
#     # Material assistance
#     # -----------------------------------------------------

#     material_candidates: List[
#         MaterialCandidate
#     ] = field(
#         default_factory=list
#     )

#     # -----------------------------------------------------
#     # Human confirmation
#     # -----------------------------------------------------

#     needs_confirmation: List[str] = field(
#         default_factory=list
#     )

#     # -----------------------------------------------------
#     # Prediction source
#     # -----------------------------------------------------

#     recognition_sources: Dict[
#         str,
#         str
#     ] = field(
#         default_factory=dict
#     )

#     # -----------------------------------------------------
#     # Office information
#     # Filled later
#     # -----------------------------------------------------

#     office_relevance: Optional[str] = None

#     office_relevance_reasons: List[str] = field(
#     default_factory=list
#     )

#     # -----------------------------------------------------
#     # Serialization
#     # -----------------------------------------------------

#     def to_dict(
#         self,
#     ):

#         return asdict(
#             self
#         )


from dataclasses import (
    dataclass,
    field,
    asdict,
)

from typing import (
    Optional,
    List,
    Dict,
)

from datetime import (
    datetime,
    timezone,
)


# =========================================================
# MATERIAL CANDIDATE
# =========================================================

@dataclass
class MaterialCandidate:

    label: str

    score: float


# =========================================================
# COLOR PROFILE
#
# Rich color information used by the styling /
# recommendation layer.
#
# IMPORTANT:
# This does NOT replace the existing "color" field.
#
# Example:
#
# color = "blue"
#
# color_profile = {
#     "dominant": "navy",
#     "palette": [
#         "navy",
#         "ivory",
#         "powder_blue",
#     ],
# }
# =========================================================

@dataclass
class ColorProfile:

    # Most visually dominant fine-grained color.
    #
    # May be more specific than the main taxonomy color.
    #
    # Example:
    # color = "blue"
    # dominant = "navy"
    dominant: Optional[str] = None

    # Fine-grained colors visible on the garment.
    #
    # Example:
    # [
    #     "ivory",
    #     "navy",
    #     "powder_blue",
    # ]
    palette: List[str] = field(
        default_factory=list
    )


# =========================================================
# PATTERN PROFILE
#
# Detailed pattern representation used by the styling
# engine.
#
# IMPORTANT:
# This does NOT replace the existing "pattern" field.
#
# It allows us to distinguish:
#
# - small floral
# - large floral
# - tonal floral
# - micro check
# - subtle check
# - large plaid
# - vertical stripe
# - horizontal stripe
# - multicolor print
# =========================================================

@dataclass
class PatternProfile:

    # Base pattern family.
    #
    # Usually mirrors the existing taxonomy pattern:
    #
    # floral
    # striped
    # checked
    # plaid
    # polka_dot
    # geometric
    # abstract
    # ...
    type: Optional[str] = None

    # Visual pattern scale.
    #
    # Expected styling values:
    #
    # small
    # medium
    # large
    scale: Optional[str] = None

    # Pattern direction where relevant.
    #
    # Expected values:
    #
    # vertical
    # horizontal
    #
    # None for patterns without meaningful orientation.
    orientation: Optional[str] = None

    # Background/base color of patterned garment.
    #
    # Example:
    # ivory blouse with navy flowers
    #
    # background_color = "ivory"
    background_color: Optional[str] = None

    # Colors appearing in motif / print.
    #
    # Example:
    #
    # [
    #     "navy",
    #     "powder_blue",
    # ]
    motif_colors: List[str] = field(
        default_factory=list
    )

    # Relationship between motif and background.
    #
    # Planned values:
    #
    # tonal
    # contrast
    # mixed
    #
    # Example:
    # Dusty pink background + mauve flower
    # -> tonal
    tone_relation: Optional[str] = None


# =========================================================
# WARDROBE ITEM
# =========================================================

@dataclass
class WardrobeItem:

    # -----------------------------------------------------
    # Identity
    # -----------------------------------------------------

    item_id: str

    image_path: str

    created_at: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )

    # -----------------------------------------------------
    # Main garment attributes
    #
    # DO NOT REMOVE.
    #
    # These are still the canonical classification labels
    # used by the existing AI pipeline.
    # -----------------------------------------------------

    category: Optional[str] = None

    subcategory: Optional[str] = None

    color: Optional[str] = None

    material: Optional[str] = None

    pattern: Optional[str] = None

    sleeve_length: Optional[str] = None

    neckline: Optional[str] = None

    fit: Optional[str] = None

    # -----------------------------------------------------
    # Styling metadata
    #
    # These fields enrich color/pattern information for
    # recommendation.
    #
    # They intentionally coexist with:
    #
    # color
    # pattern
    #
    # so existing training/inference code remains valid.
    # -----------------------------------------------------

    color_profile: ColorProfile = field(
        default_factory=ColorProfile
    )

    pattern_profile: PatternProfile = field(
        default_factory=PatternProfile
    )

    # -----------------------------------------------------
    # Multi-value attributes
    # -----------------------------------------------------

    design_details: List[str] = field(
        default_factory=list
    )

    style_tags: List[str] = field(
        default_factory=list
    )

    # -----------------------------------------------------
    # Material assistance
    # -----------------------------------------------------

    material_candidates: List[
        MaterialCandidate
    ] = field(
        default_factory=list
    )

    # -----------------------------------------------------
    # Human confirmation
    # -----------------------------------------------------

    needs_confirmation: List[str] = field(
        default_factory=list
    )

    # -----------------------------------------------------
    # Prediction source
    # -----------------------------------------------------

    recognition_sources: Dict[
        str,
        str
    ] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # Office information
    # Filled later
    # -----------------------------------------------------

    office_relevance: Optional[str] = None

    office_relevance_reasons: List[str] = field(
        default_factory=list
    )

    # -----------------------------------------------------
    # Serialization
    # -----------------------------------------------------

    def to_dict(
        self,
    ):

        return asdict(
            self
        )