from pathlib import Path

import yaml


class WardrobeOfficeFilter:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        config_path = (
            self.project_root
            / "configs"
            / "office_wear.yaml"
        )

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as f:

            self.config = yaml.safe_load(
                f
            )

        self.allowed_categories = set(
            self.config.get(
                "allowed_categories",
                [],
            )
        )

        self.core_subcategories = set(
            self.config.get(
                "core_subcategories",
                [],
            )
        )

        self.extended_subcategories = set(
            self.config.get(
                "extended_subcategories",
                [],
            )
        )

        self.hard_exclude_details = set(
            self.config.get(
                "hard_exclude_design_details",
                [],
            )
        )

    # =====================================================
    # GENERIC GETTER
    # Supports dict or WardrobeItem
    # =====================================================

    def _get(
        self,
        item,
        field,
        default=None,
    ):

        if isinstance(
            item,
            dict,
        ):

            return item.get(
                field,
                default,
            )

        return getattr(
            item,
            field,
            default,
        )

    # =====================================================
    # EVALUATE
    # =====================================================

    def evaluate(
        self,
        item,
    ):

        category = self._get(
            item,
            "category",
        )

        subcategory = self._get(
            item,
            "subcategory",
        )

        design_details = self._get(
            item,
            "design_details",
            [],
        )

        if design_details is None:
            design_details = []

        reasons = []

        # =====================================
        # 1. CATEGORY
        # =====================================

        if category is None:

            return {
                "office_relevance":
                    "review",

                "reasons": [
                    "missing_category"
                ],
            }

        if (
            self.allowed_categories
            and
            category
            not in self.allowed_categories
        ):

            return {
                "office_relevance":
                    "negative",

                "reasons": [
                    f"category_not_allowed:{category}"
                ],
            }

        # =====================================
        # 2. HARD-EXCLUDED DETAILS
        # =====================================

        excluded_details = sorted(

            set(
                design_details
            )
            &
            self.hard_exclude_details

        )

        if excluded_details:

            return {
                "office_relevance":
                    "negative",

                "reasons": [
                    (
                        "hard_excluded_design:"
                        + detail
                    )

                    for detail in excluded_details
                ],
            }

        # =====================================
        # 3. SUBCATEGORY
        # =====================================

        if subcategory is None:

            return {
                "office_relevance":
                    "review",

                "reasons": [
                    "missing_subcategory"
                ],
            }

        # Strong office-wear groups
        if (
            subcategory
            in self.core_subcategories
        ):

            reasons.append(
                f"core_subcategory:{subcategory}"
            )

            return {
                "office_relevance":
                    "positive",

                "reasons":
                    reasons,
            }

        # Allowed, but less certain
        if (
            subcategory
            in self.extended_subcategories
        ):

            reasons.append(
                f"extended_subcategory:{subcategory}"
            )

            return {
                "office_relevance":
                    "review",

                "reasons":
                    reasons,
            }

        # =====================================
        # 4. UNKNOWN / OTHER SUBCATEGORY
        # =====================================

        reasons.append(
            f"subcategory_not_classified:{subcategory}"
        )

        return {
            "office_relevance":
                "review",

            "reasons":
                reasons,
        }

    # =====================================================
    # APPLY TO WARDROBE ITEM
    # =====================================================

    def apply(
        self,
        item,
    ):

        result = self.evaluate(
            item
        )

        if isinstance(
            item,
            dict,
        ):

            item[
                "office_relevance"
            ] = result[
                "office_relevance"
            ]

            item[
                "office_relevance_reasons"
            ] = result[
                "reasons"
            ]

        else:

            item.office_relevance = (
                result[
                    "office_relevance"
                ]
            )

            item.office_relevance_reasons = (
                result[
                    "reasons"
                ]
            )

        return item