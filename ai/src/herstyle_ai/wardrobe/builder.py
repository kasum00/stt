from pathlib import Path

from uuid import uuid4

from herstyle_ai.wardrobe.models import (
    WardrobeItem,
    MaterialCandidate,
    ColorProfile,
    PatternProfile,
)

# =========================================================
# BUILDER
# =========================================================

class WardrobeItemBuilder:

    def build(
        self,
        image_path,
        prediction,
    ):

        image_path = Path(
            image_path
        )

        # =====================================
        # MATERIAL
        # =====================================

        material_data = prediction.get(
            "material",
            {},
        )

        material_label = (
            material_data.get(
                "label"
            )
        )

        material_candidates = []

        for candidate in (
            material_data.get(
                "candidates",
                []
            )
        ):

            label = candidate.get(
                "label"
            )

            score = candidate.get(
                "score"
            )

            if (
                label is None
                or
                score is None
            ):
                continue

            material_candidates.append(
                MaterialCandidate(
                    label=str(
                        label
                    ),
                    score=float(
                        score
                    ),
                )
            )

        # =====================================
        # NEEDS CONFIRMATION
        # =====================================

        needs_confirmation = []

        if (
            material_data.get(
                "status"
            )
            == "needs_confirmation"
        ):

            needs_confirmation.append(
                "material"
            )

        # =====================================
        # DESIGN DETAILS
        # =====================================

        design_data = prediction.get(
            "design_details",
            {},
        )

        design_details = (
            design_data.get(
                "labels",
                [],
            )
        )

                # =====================================
        # BASE COLOR / PATTERN PROFILE
        #
        # At this stage we only populate
        # information that is already known
        # from the existing classifier.
        #
        # Fine-grained colors such as:
        #
        # ivory
        # camel
        # powder_blue
        # burgundy
        #
        # will be added by the styling-profile
        # extractor in a later step.
        #
        # Do NOT guess them here.
        # =====================================

        color_label = self._label(
            prediction,
            "color",
        )

        pattern_label = self._label(
            prediction,
            "pattern",
        )

        # -------------------------------------
        # COLOR PROFILE
        # -------------------------------------

        color_palette = []

        if color_label is not None:

            color_palette.append(
                color_label
            )

        color_profile = ColorProfile(
            dominant=color_label,
            palette=color_palette,
        )

        # -------------------------------------
        # PATTERN PROFILE
        # -------------------------------------

        pattern_background = None

        # For a solid garment the garment color
        # is also its background/base color.
        if (
            pattern_label == "solid"
            and color_label is not None
        ):

            pattern_background = (
                color_label
            )

        pattern_profile = PatternProfile(
            type=pattern_label,
            scale=None,
            orientation=None,
            background_color=(
                pattern_background
            ),
            motif_colors=[],
            tone_relation=None,
        )

        # =====================================
        # SOURCES
        # =====================================

        recognition_sources = {}

        fields = [
            "category",
            "subcategory",
            "color",
            "material",
            "pattern",
            "sleeve_length",
            "neckline",
            "fit",
            "design_details",
        ]

        for field_name in fields:

            data = prediction.get(
                field_name
            )

            if not isinstance(
                data,
                dict,
            ):
                continue

            source = data.get(
                "source"
            )

            if source is not None:

                recognition_sources[
                    field_name
                ] = source

        # =====================================
        # BUILD ITEM
        # =====================================

        item = WardrobeItem(

            item_id=uuid4().hex,

            image_path=str(
                image_path
            ),

            category=self._label(
                prediction,
                "category",
            ),

            subcategory=self._label(
                prediction,
                "subcategory",
            ),

            color=color_label,

            material=material_label,

            pattern=pattern_label,

            sleeve_length=self._label(
                prediction,
                "sleeve_length",
            ),

            neckline=self._label(
                prediction,
                "neckline",
            ),

            fit=self._label(
                prediction,
                "fit",
            ),

            color_profile=(
                color_profile
            ),

            pattern_profile=(
                pattern_profile
            ),

            design_details=list(
                design_details
            ),

            style_tags=[],

            material_candidates=(
                material_candidates
            ),

            needs_confirmation=(
                needs_confirmation
            ),

            recognition_sources=(
                recognition_sources
            ),
        )

        return item

    # =====================================================
    # HELPER
    # =====================================================

    def _label(
        self,
        prediction,
        field_name,
    ):

        data = prediction.get(
            field_name
        )

        if not isinstance(
            data,
            dict,
        ):
            return None

        return data.get(
            "label"
        )