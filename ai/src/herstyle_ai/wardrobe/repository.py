from pathlib import Path

from datetime import (
    datetime,
    timezone,
)

import json


from herstyle_ai.vlm.fashion_prompt import (
    MATERIAL,
)


class WardrobeRepository:

    def __init__(
        self,
        project_root,
        data_root=None,
    ):

        self.project_root = Path(
            project_root
        )
        self.data_root = Path(data_root) if data_root is not None else self.project_root / "data"

        self.items_dir = (
            self.data_root
            / "processed"
            / "wardrobe"
            / "items"
        )

        self.items_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _item_path(
        self,
        item_id,
    ):

        return (
            self.items_dir
            / f"{item_id}.json"
        )

    def _now(
        self,
    ):

        return (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    def _normalize_item_data(
        self,
        data,
    ):
        """
        Normalize wardrobe JSON to the current schema.

        This keeps old wardrobe items backward compatible
        without changing the existing canonical fields:

        color
        pattern

        Rich styling metadata is added conservatively.
        Unknown information is never invented.
        """

        if not isinstance(
            data,
            dict,
        ):

            raise TypeError(
                "wardrobe item data must be a dict"
            )

        result = dict(
            data
        )

        color = result.get(
            "color"
        )

        pattern = result.get(
            "pattern"
        )

        # =================================================
        # COLOR PROFILE
        # =================================================

        raw_color_profile = result.get(
            "color_profile"
        )

        if isinstance(
            raw_color_profile,
            dict,
        ):

            color_profile = dict(
                raw_color_profile
            )

        else:

            color_profile = {}

        # ---------------------------------------------
        # DOMINANT
        # ---------------------------------------------

        if (
            color_profile.get(
                "dominant"
            )
            is None
        ):

            color_profile[
                "dominant"
            ] = color

        # ---------------------------------------------
        # PALETTE
        # ---------------------------------------------

        palette = color_profile.get(
            "palette"
        )

        if not isinstance(
            palette,
            list,
        ):

            palette = []

        # Old items only know the coarse taxonomy color.
        #
        # Use it as a safe baseline.
        if (
            not palette
            and color is not None
        ):

            palette = [
                color
            ]

        color_profile[
            "palette"
        ] = palette

        result[
            "color_profile"
        ] = color_profile

        # =================================================
        # PATTERN PROFILE
        # =================================================

        raw_pattern_profile = result.get(
            "pattern_profile"
        )

        if isinstance(
            raw_pattern_profile,
            dict,
        ):

            pattern_profile = dict(
                raw_pattern_profile
            )

        else:

            pattern_profile = {}

        # ---------------------------------------------
        # TYPE
        # ---------------------------------------------

        if (
            pattern_profile.get(
                "type"
            )
            is None
        ):

            pattern_profile[
                "type"
            ] = pattern

        # ---------------------------------------------
        # SCALE
        # ---------------------------------------------

        pattern_profile.setdefault(
            "scale",
            None,
        )

        # ---------------------------------------------
        # ORIENTATION
        # ---------------------------------------------

        pattern_profile.setdefault(
            "orientation",
            None,
        )

        # ---------------------------------------------
        # BACKGROUND COLOR
        #
        # Safe inference only for solid garments.
        # ---------------------------------------------

        if (
            "background_color"
            not in pattern_profile
        ):

            pattern_profile[
                "background_color"
            ] = None

        if (
            pattern == "solid"
            and
            pattern_profile.get(
                "background_color"
            )
            is None
            and
            color is not None
        ):

            pattern_profile[
                "background_color"
            ] = color

        # ---------------------------------------------
        # MOTIF COLORS
        # ---------------------------------------------

        motif_colors = (
            pattern_profile.get(
                "motif_colors"
            )
        )

        if not isinstance(
            motif_colors,
            list,
        ):

            motif_colors = []

        pattern_profile[
            "motif_colors"
        ] = motif_colors

        # ---------------------------------------------
        # TONE RELATION
        # ---------------------------------------------

        pattern_profile.setdefault(
            "tone_relation",
            None,
        )

        result[
            "pattern_profile"
        ] = pattern_profile

        return result
    # =====================================================
    # ADD
    # =====================================================

    def add(
        self,
        item,
    ):

        if hasattr(
            item,
            "to_dict",
        ):

            data = item.to_dict()

        elif isinstance(
            item,
            dict,
        ):

            data = dict(
                item
            )

        else:

            raise TypeError(
                "item must be WardrobeItem or dict"
            )

        item_id = data.get(
            "item_id"
        )

        data = self._normalize_item_data(
            data
        )        

        if not item_id:

            raise ValueError(
                "item_id is required"
            )

        path = self._item_path(
            item_id
        )

        if path.exists():

            raise FileExistsError(
                f"Wardrobe item already exists: {item_id}"
            )

        data[
            "updated_at"
        ] = self._now()

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return data

    # =====================================================
    # GET
    # =====================================================

    def get(
        self,
        item_id,
    ):

        path = self._item_path(
            item_id
        )

        if not path.exists():

            return None

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(
                f
            )

        return self._normalize_item_data(
            data
        )

    # =====================================================
    # SAVE / UPDATE
    # =====================================================

    def save(
        self,
        item,
    ):

        if not isinstance(
            item,
            dict,
        ):

            raise TypeError(
                "save() expects a dict"
            )
        item = self._normalize_item_data(
            item
        )

        item_id = item.get(
            "item_id"
        )

        if not item_id:

            raise ValueError(
                "item_id is required"
            )

        path = self._item_path(
            item_id
        )

        item[
            "updated_at"
        ] = self._now()

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                item,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return item

    # =====================================================
    # LIST ALL
    # =====================================================

    def list_all(
        self,
    ):

        items = []

        for path in sorted(
            self.items_dir.glob(
                "*.json"
            )
        ):

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as f:

                data = json.load(
                    f
                )

                items.append(
                    self._normalize_item_data(
                        data
                    )
                )

        return items

    # =====================================================
    # FILTER OFFICE POSITIVE
    # =====================================================

    def list_office_positive(
        self,
    ):

        return [

            item

            for item in self.list_all()

            if (
                item.get(
                    "office_relevance"
                )
                == "positive"
            )
        ]

    # =====================================================
    # CONFIRM MATERIAL
    # =====================================================

    def confirm_material(
        self,
        item_id,
        material,
    ):

        if material not in MATERIAL:

            raise ValueError(
                f"Invalid material: {material}"
            )

        item = self.get(
            item_id
        )

        if item is None:

            raise FileNotFoundError(
                f"Item not found: {item_id}"
            )

        # Final confirmed value
        item[
            "material"
        ] = material

        # Remove confirmation requirement
        needs_confirmation = list(
            item.get(
                "needs_confirmation",
                []
            )
        )

        needs_confirmation = [

            field

            for field in needs_confirmation

            if field != "material"
        ]

        item[
            "needs_confirmation"
        ] = needs_confirmation

        # Record source
        sources = dict(
            item.get(
                "recognition_sources",
                {}
            )
        )

        sources[
            "material"
        ] = "user_confirmed"

        item[
            "recognition_sources"
        ] = sources

        return self.save(
            item
        )

    # =====================================================
    # UPDATE ATTRIBUTE
    # =====================================================

    def update_attribute(
        self,
        item_id,
        field,
        value,
    ):

        editable_fields = {
            "category",
            "subcategory",
            "color",
            "material",
            "pattern",
            "sleeve_length",
            "neckline",
            "fit",
            "design_details",
            "style_tags",
        }

        if field not in editable_fields:

            raise ValueError(
                f"Field is not editable: {field}"
            )

        item = self.get(
            item_id
        )

        if item is None:

            raise FileNotFoundError(
                f"Item not found: {item_id}"
            )

        item[
            field
        ] = value

        sources = dict(
            item.get(
                "recognition_sources",
                {}
            )
        )

        sources[
            field
        ] = "user_edited"

        item[
            "recognition_sources"
        ] = sources

        return self.save(
            item
        )

    # =====================================================
    # DELETE
    # =====================================================

    def delete(
        self,
        item_id,
    ):

        path = self._item_path(
            item_id
        )

        if not path.exists():

            return False

        path.unlink()

        return True

    # =====================================================
    # COUNT
    # =====================================================

    def count(
        self,
    ):

        return len(
            list(
                self.items_dir.glob(
                    "*.json"
                )
            )
        )
