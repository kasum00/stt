from pathlib import Path
import yaml


# =========================================================
# FIELD GROUPS
# =========================================================

SINGLE_VALUE_FIELDS = {
    "category",
    "subcategory",
    "color",
    "material",
    "pattern",
    "sleeve_length",
    "neckline",
    "fit",
}


MULTI_VALUE_FIELDS = {
    "design_details",
    "style_tags",
}


# =========================================================
# VALIDATOR
# =========================================================

class WardrobeTaxonomyValidator:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        taxonomy_path = (
            self.project_root
            / "configs"
            / "taxonomy.yaml"
        )

        if not taxonomy_path.is_file():

            raise FileNotFoundError(
                f"Taxonomy file not found: {taxonomy_path}"
            )

        with open(
            taxonomy_path,
            "r",
            encoding="utf-8",
        ) as f:

            self.taxonomy = (
                yaml.safe_load(
                    f
                )
                or {}
            )

    # =====================================================
    # SINGLE VALUE
    # =====================================================

    def _validate_single(
        self,
        field,
        value,
    ):

        # Optional attributes may be null.
        if value is None:

            return None

        if not isinstance(
            value,
            str,
        ):

            raise ValueError(
                f"{field} must be a string or null"
            )

        value = (
            value.strip()
        )

        if not value:

            raise ValueError(
                f"{field} cannot be empty"
            )

        allowed = (
            self.taxonomy.get(
                field,
                []
            )
        )

        if value not in allowed:

            raise ValueError(
                f"Invalid {field}: {value}. "
                f"Allowed values: {allowed}"
            )

        return value

    # =====================================================
    # MULTI VALUE
    # =====================================================

    def _validate_multi(
        self,
        field,
        value,
    ):

        if value is None:

            return []

        if not isinstance(
            value,
            list,
        ):

            raise ValueError(
                f"{field} must be a list"
            )

        allowed = set(
            self.taxonomy.get(
                field,
                []
            )
        )

        result = []

        seen = set()

        for item in value:

            if not isinstance(
                item,
                str,
            ):

                raise ValueError(
                    f"{field} values must be strings"
                )

            item = (
                item.strip()
            )

            if item not in allowed:

                raise ValueError(
                    f"Invalid {field} value: {item}. "
                    f"Allowed values: {sorted(allowed)}"
                )

            if item not in seen:

                seen.add(
                    item
                )

                result.append(
                    item
                )

        return result

    # =====================================================
    # SUBCATEGORY
    # =====================================================

    def _validate_subcategory(
        self,
        category,
        subcategory,
    ):

        if subcategory is None:

            return None

        if category is None:

            raise ValueError(
                "category is required when "
                "subcategory is provided"
            )

        if not isinstance(
            subcategory,
            str,
        ):

            raise ValueError(
                "subcategory must be a string or null"
            )

        subcategory = (
            subcategory.strip()
        )

        allowed_by_category = (
            self.taxonomy.get(
                "subcategory",
                {}
            )
        )

        allowed = (
            allowed_by_category.get(
                category,
                []
            )
        )

        if subcategory not in allowed:

            raise ValueError(
                f"Invalid subcategory '{subcategory}' "
                f"for category '{category}'. "
                f"Allowed values: {allowed}"
            )

        return subcategory

    # =====================================================
    # MAIN
    # =====================================================

    def validate_attributes(
        self,
        attributes,
        base_item=None,
    ):

        if not isinstance(
            attributes,
            dict,
        ):

            raise ValueError(
                "attributes must be an object"
            )

        base_item = (
            base_item
            or {}
        )

        normalized = {}

        # =====================================
        # CATEGORY FIRST
        # =====================================

        if "category" in attributes:

            category = (
                self._validate_single(
                    "category",
                    attributes[
                        "category"
                    ],
                )
            )

            if category is None:

                raise ValueError(
                    "category cannot be null"
                )

            normalized[
                "category"
            ] = category

        else:

            category = (
                base_item.get(
                    "category"
                )
            )

        # =====================================
        # NORMAL SINGLE FIELDS
        # =====================================

        for field in [

            "color",

            "material",

            "pattern",

            "sleeve_length",

            "neckline",

            "fit",

        ]:

            if field not in attributes:

                continue

            normalized[
                field
            ] = (
                self._validate_single(
                    field,
                    attributes[
                        field
                    ],
                )
            )

        # =====================================
        # SUBCATEGORY
        # =====================================

        if "subcategory" in attributes:

            normalized[
                "subcategory"
            ] = (
                self._validate_subcategory(
                    category=category,
                    subcategory=(
                        attributes[
                            "subcategory"
                        ]
                    ),
                )
            )

        elif "category" in attributes:

            # Category changed.
            # Keep existing subcategory only if it
            # still belongs to the new category.

            current_subcategory = (
                base_item.get(
                    "subcategory"
                )
            )

            if current_subcategory is not None:

                allowed = (
                    self.taxonomy
                    .get(
                        "subcategory",
                        {}
                    )
                    .get(
                        category,
                        []
                    )
                )

                if (
                    current_subcategory
                    not in allowed
                ):

                    normalized[
                        "subcategory"
                    ] = None

        # =====================================
        # MULTI VALUE FIELDS
        # =====================================

        for field in [

            "design_details",

            "style_tags",

        ]:

            if field not in attributes:

                continue

            normalized[
                field
            ] = (
                self._validate_multi(
                    field,
                    attributes[
                        field
                    ],
                )
            )

        return normalized