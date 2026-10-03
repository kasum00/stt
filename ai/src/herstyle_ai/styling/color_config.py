from pathlib import Path

import yaml


# =========================================================
# COLOR STYLING CONFIG
# =========================================================

class ColorStylingConfig:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        self.config_path = (
            self.project_root
            / "configs"
            / "styling_colors.yaml"
        )

        self.taxonomy_path = (
            self.project_root
            / "configs"
            / "taxonomy.yaml"
        )

        # =====================================
        # LOAD CONFIG
        # =====================================

        self.config = self._load_yaml(
            self.config_path
        )

        self.taxonomy = self._load_yaml(
            self.taxonomy_path
        )

        # =====================================
        # SECTIONS
        # =====================================

        self.colors = self.config.get(
            "colors",
            {},
        )

        self.neutral_colors = set(
            self.config.get(
                "neutral_colors",
                [],
            )
        )

        self.harmony_groups = (
            self.config.get(
                "harmony_groups",
                {},
            )
        )

        self.office_combinations = (
            self.config.get(
                "office_combinations",
                {},
            )
        )

        # =====================================
        # VALIDATION
        # =====================================

        self._validate()

    # =====================================================
    # LOAD YAML
    # =====================================================

    def _load_yaml(
        self,
        path,
    ):

        if not path.exists():

            raise FileNotFoundError(
                f"Config file not found: {path}"
            )

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            data = yaml.safe_load(
                f
            )

        if data is None:

            data = {}

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                f"Config must be a YAML mapping: {path}"
            )

        return data

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate(
        self,
    ):

        # -------------------------------------
        # COLORS
        # -------------------------------------

        if not isinstance(
            self.colors,
            dict,
        ):

            raise ValueError(
                "'colors' must be a mapping"
            )

        if not self.colors:

            raise ValueError(
                "'colors' cannot be empty"
            )

        taxonomy_colors = set(
            self.taxonomy.get(
                "color",
                [],
            )
        )

        if not taxonomy_colors:

            raise ValueError(
                "taxonomy.yaml has no color labels"
            )

        for (
            color_name,
            color_data,
        ) in self.colors.items():

            if not isinstance(
                color_data,
                dict,
            ):

                raise ValueError(
                    "Invalid styling color entry: "
                    f"{color_name}"
                )

            coarse = color_data.get(
                "coarse"
            )

            family = color_data.get(
                "family"
            )

            if coarse is None:

                raise ValueError(
                    "Missing coarse mapping for "
                    f"styling color: {color_name}"
                )

            if coarse not in taxonomy_colors:

                raise ValueError(
                    "Invalid coarse color mapping: "
                    f"{color_name} -> {coarse}"
                )

            if (
                family is None
                or not isinstance(
                    family,
                    str,
                )
                or not family.strip()
            ):

                raise ValueError(
                    "Missing or invalid family for "
                    f"styling color: {color_name}"
                )

        # -------------------------------------
        # NEUTRAL COLORS
        # -------------------------------------

        unknown_neutrals = (
            self.neutral_colors
            - set(
                self.colors.keys()
            )
        )

        if unknown_neutrals:

            raise ValueError(
                "Unknown neutral colors: "
                + ", ".join(
                    sorted(
                        unknown_neutrals
                    )
                )
            )

        # -------------------------------------
        # HARMONY GROUPS
        # -------------------------------------

        if not isinstance(
            self.harmony_groups,
            dict,
        ):

            raise ValueError(
                "'harmony_groups' must be a mapping"
            )

        for (
            group_name,
            group_colors,
        ) in self.harmony_groups.items():

            if not isinstance(
                group_colors,
                list,
            ):

                raise ValueError(
                    "Harmony group must be a list: "
                    f"{group_name}"
                )

            unknown_colors = set(
                group_colors
            ) - set(
                self.colors.keys()
            )

            if unknown_colors:

                raise ValueError(
                    "Unknown colors in harmony group "
                    f"{group_name}: "
                    + ", ".join(
                        sorted(
                            unknown_colors
                        )
                    )
                )

        # -------------------------------------
        # OFFICE COMBINATIONS
        # -------------------------------------

        if not isinstance(
            self.office_combinations,
            dict,
        ):

            raise ValueError(
                "'office_combinations' "
                "must be a mapping"
            )

        for (
            anchor_color,
            combinations,
        ) in (
            self.office_combinations.items()
        ):

            if anchor_color not in self.colors:

                raise ValueError(
                    "Unknown office-combination "
                    f"anchor color: {anchor_color}"
                )

            if not isinstance(
                combinations,
                list,
            ):

                raise ValueError(
                    "Office combinations must be "
                    f"a list: {anchor_color}"
                )

            for combination in combinations:

                if not isinstance(
                    combination,
                    list,
                ):

                    raise ValueError(
                        "Office color combination "
                        "must be a list"
                    )

                if len(
                    combination
                ) < 2:

                    raise ValueError(
                        "Office color combination "
                        "must contain at least "
                        "two colors"
                    )

                unknown_colors = [

                    color

                    for color in combination

                    if color
                    not in self.colors
                ]

                if unknown_colors:

                    raise ValueError(
                        "Unknown colors in office "
                        "combination: "
                        + ", ".join(
                            unknown_colors
                        )
                    )

    # =====================================================
    # COLOR LOOKUP
    # =====================================================

    def has_color(
        self,
        color,
    ):

        return color in self.colors

    def get_color(
        self,
        color,
    ):

        if color not in self.colors:

            raise ValueError(
                f"Unknown styling color: {color}"
            )

        return self.colors[
            color
        ]

    # =====================================================
    # COARSE TAXONOMY COLOR
    # =====================================================

    def get_coarse(
        self,
        color,
    ):

        return self.get_color(
            color
        )[
            "coarse"
        ]

    # =====================================================
    # COLOR FAMILY
    # =====================================================

    def get_family(
        self,
        color,
    ):

        return self.get_color(
            color
        )[
            "family"
        ]

    # =====================================================
    # NEUTRAL
    # =====================================================

    def is_neutral(
        self,
        color,
    ):

        return (
            color
            in self.neutral_colors
        )

    # =====================================================
    # HARMONY GROUPS
    # =====================================================

    def get_harmony_groups(
        self,
        color,
    ):

        if not self.has_color(
            color
        ):

            raise ValueError(
                f"Unknown styling color: {color}"
            )

        groups = []

        for (
            group_name,
            group_colors,
        ) in self.harmony_groups.items():

            if color in group_colors:

                groups.append(
                    group_name
                )

        return groups

    def same_harmony_group(
        self,
        color_a,
        color_b,
    ):

        groups_a = set(
            self.get_harmony_groups(
                color_a
            )
        )

        groups_b = set(
            self.get_harmony_groups(
                color_b
            )
        )

        return bool(
            groups_a
            & groups_b
        )

    # =====================================================
    # OFFICE COLOR COMBINATIONS
    # =====================================================

    def get_office_combinations(
        self,
        anchor_color,
    ):

        if not self.has_color(
            anchor_color
        ):

            raise ValueError(
                "Unknown styling color: "
                f"{anchor_color}"
            )

        return list(
            self.office_combinations.get(
                anchor_color,
                [],
            )
        )