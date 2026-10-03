from pathlib import Path

import yaml


# =========================================================
# PATTERN STYLING CONFIG
# =========================================================

class PatternStylingConfig:

    VALID_SCALES = {
        "small",
        "medium",
        "large",
    }

    VALID_ORIENTATIONS = {
        "vertical",
        "horizontal",
    }

    VALID_TONE_RELATIONS = {
        "tonal",
        "contrast",
        "mixed",
    }

    VALID_SLOTS = {
        "top",
        "bottom",
        "dress",
        "outerwear",
        "shoes",
    }

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
            / "styling_patterns.yaml"
        )

        self.taxonomy_path = (
            self.project_root
            / "configs"
            / "taxonomy.yaml"
        )

        # =====================================
        # LOAD
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

        self.general_rules = (
            self.config.get(
                "general_rules",
                {},
            )
        )

        self.profiles = (
            self.config.get(
                "profiles",
                {},
            )
        )

        self.outfit_rules = (
            self.config.get(
                "outfit_rules",
                {},
            )
        )

        # =====================================
        # VALIDATE
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

        self._validate_general_rules()

        self._validate_profiles()

        self._validate_outfit_rules()

    # =====================================================
    # GENERAL RULES
    # =====================================================

    def _validate_general_rules(
        self,
    ):

        if not isinstance(
            self.general_rules,
            dict,
        ):

            raise ValueError(
                "'general_rules' must be a mapping"
            )

        max_patterned = (
            self.general_rules.get(
                "max_patterned_items_default",
                1,
            )
        )

        if (
            not isinstance(
                max_patterned,
                int,
            )
            or max_patterned < 0
        ):

            raise ValueError(
                "max_patterned_items_default "
                "must be a non-negative integer"
            )

    # =====================================================
    # PROFILES
    # =====================================================

    def _validate_profiles(
        self,
    ):

        if not isinstance(
            self.profiles,
            dict,
        ):

            raise ValueError(
                "'profiles' must be a mapping"
            )

        if not self.profiles:

            raise ValueError(
                "'profiles' cannot be empty"
            )

        taxonomy_patterns = set(
            self.taxonomy.get(
                "pattern",
                [],
            )
        )

        if not taxonomy_patterns:

            raise ValueError(
                "taxonomy.yaml has no pattern labels"
            )

        for (
            profile_name,
            profile,
        ) in self.profiles.items():

            if not isinstance(
                profile,
                dict,
            ):

                raise ValueError(
                    "Invalid pattern profile: "
                    f"{profile_name}"
                )

            # ---------------------------------
            # BASE PATTERNS
            # ---------------------------------

            base_patterns = profile.get(
                "base_patterns",
                [],
            )

            if (
                not isinstance(
                    base_patterns,
                    list,
                )
                or not base_patterns
            ):

                raise ValueError(
                    "base_patterns must be a "
                    "non-empty list for "
                    f"{profile_name}"
                )

            invalid_base = [

                pattern

                for pattern in base_patterns

                if pattern
                not in taxonomy_patterns
            ]

            if invalid_base:

                raise ValueError(
                    "Invalid base pattern(s) for "
                    f"{profile_name}: "
                    + ", ".join(
                        invalid_base
                    )
                )

            # ---------------------------------
            # SCALE
            #
            # May be:
            # None
            # "small"
            # ["small", "medium"]
            # ---------------------------------

            self._validate_scale(
                profile_name,
                profile.get(
                    "scale"
                ),
            )

            # ---------------------------------
            # ORIENTATION
            # ---------------------------------

            orientation = profile.get(
                "orientation"
            )

            if (
                orientation is not None
                and orientation
                not in self.VALID_ORIENTATIONS
            ):

                raise ValueError(
                    "Invalid orientation for "
                    f"{profile_name}: "
                    f"{orientation}"
                )

            # ---------------------------------
            # TONE RELATION
            # ---------------------------------

            tone_relation = profile.get(
                "tone_relation"
            )

            if (
                tone_relation is not None
                and tone_relation
                not in self.VALID_TONE_RELATIONS
            ):

                raise ValueError(
                    "Invalid tone_relation for "
                    f"{profile_name}: "
                    f"{tone_relation}"
                )

            # ---------------------------------
            # BOOLEAN RULES
            # ---------------------------------

            boolean_fields = [
                "requires_solid_companion",
                "prefer_repeat_motif_color",
                "avoid_second_pattern",
                "primary_visual_accent",
                "restrict_new_colors",
            ]

            for field_name in boolean_fields:

                if field_name not in profile:

                    continue

                value = profile[
                    field_name
                ]

                if not isinstance(
                    value,
                    bool,
                ):

                    raise ValueError(
                        f"{field_name} must be "
                        "boolean for "
                        f"{profile_name}"
                    )

            # ---------------------------------
            # MULTICOLOR THRESHOLD
            # ---------------------------------

            if (
                "multicolor_threshold"
                in profile
            ):

                threshold = profile[
                    "multicolor_threshold"
                ]

                if (
                    not isinstance(
                        threshold,
                        int,
                    )
                    or threshold < 2
                ):

                    raise ValueError(
                        "multicolor_threshold "
                        "must be an integer >= 2"
                    )

    # =====================================================
    # SCALE VALIDATION
    # =====================================================

    def _validate_scale(
        self,
        profile_name,
        scale,
    ):

        if scale is None:

            return

        if isinstance(
            scale,
            str,
        ):

            values = [
                scale
            ]

        elif isinstance(
            scale,
            list,
        ):

            values = scale

        else:

            raise ValueError(
                "scale must be null, string, "
                "or list for "
                f"{profile_name}"
            )

        invalid = [

            value

            for value in values

            if value
            not in self.VALID_SCALES
        ]

        if invalid:

            raise ValueError(
                "Invalid scale value(s) for "
                f"{profile_name}: "
                + ", ".join(
                    invalid
                )
            )

    # =====================================================
    # OUTFIT RULE VALIDATION
    # =====================================================

    def _validate_outfit_rules(
        self,
    ):

        if not isinstance(
            self.outfit_rules,
            dict,
        ):

            raise ValueError(
                "'outfit_rules' must be a mapping"
            )

        for (
            rule_name,
            rule,
        ) in self.outfit_rules.items():

            if not isinstance(
                rule,
                dict,
            ):

                raise ValueError(
                    "Invalid outfit rule: "
                    f"{rule_name}"
                )

            # ---------------------------------
            # SLOT FIELDS
            # ---------------------------------

            slot_fields = [
                "patterned_slot",
                "solid_slot",
                "required_solid_slot",
            ]

            for field_name in slot_fields:

                if field_name not in rule:

                    continue

                slots = rule[
                    field_name
                ]

                if not isinstance(
                    slots,
                    list,
                ):

                    raise ValueError(
                        f"{field_name} must be "
                        f"a list in {rule_name}"
                    )

                invalid_slots = [

                    slot

                    for slot in slots

                    if slot
                    not in self.VALID_SLOTS
                ]

                if invalid_slots:

                    raise ValueError(
                        "Invalid slot(s) in "
                        f"{rule_name}: "
                        + ", ".join(
                            invalid_slots
                        )
                    )

            # ---------------------------------
            # ENABLED
            # ---------------------------------

            if (
                "enabled"
                in rule
                and not isinstance(
                    rule[
                        "enabled"
                    ],
                    bool,
                )
            ):

                raise ValueError(
                    "'enabled' must be boolean "
                    f"in {rule_name}"
                )

            # ---------------------------------
            # OUTERWEAR SUBCATEGORY
            # ---------------------------------

            if (
                "preferred_outerwear_subcategories"
                in rule
            ):

                values = rule[
                    "preferred_outerwear_subcategories"
                ]

                if not isinstance(
                    values,
                    list,
                ):

                    raise ValueError(
                        "preferred_outerwear_"
                        "subcategories must be a list"
                    )

                allowed_outerwear = set(
                    self.taxonomy.get(
                        "subcategory",
                        {},
                    ).get(
                        "outerwear",
                        [],
                    )
                )

                invalid = [

                    value

                    for value in values

                    if value
                    not in allowed_outerwear
                ]

                if invalid:

                    raise ValueError(
                        "Invalid outerwear "
                        "subcategory(s): "
                        + ", ".join(
                            invalid
                        )
                    )

    # =====================================================
    # PROFILE LOOKUP
    # =====================================================

    def has_profile(
        self,
        profile_name,
    ):

        return (
            profile_name
            in self.profiles
        )

    def get_profile(
        self,
        profile_name,
    ):

        if not self.has_profile(
            profile_name
        ):

            raise ValueError(
                "Unknown styling pattern profile: "
                f"{profile_name}"
            )

        return self.profiles[
            profile_name
        ]

    # =====================================================
    # PROFILES FOR BASE PATTERN
    # =====================================================

    def get_profiles_for_pattern(
        self,
        base_pattern,
    ):

        results = []

        for (
            profile_name,
            profile,
        ) in self.profiles.items():

            if base_pattern in profile.get(
                "base_patterns",
                [],
            ):

                results.append(
                    profile_name
                )

        return results

    # =====================================================
    # PROFILE MATCHING
    # =====================================================

    def matches_profile(
        self,
        profile_name,
        base_pattern,
        scale=None,
        orientation=None,
        tone_relation=None,
    ):

        profile = self.get_profile(
            profile_name
        )

        # ---------------------------------
        # BASE PATTERN
        # ---------------------------------

        if base_pattern not in profile.get(
            "base_patterns",
            [],
        ):

            return False

        # ---------------------------------
        # SCALE
        # ---------------------------------

        expected_scale = profile.get(
            "scale"
        )

        if expected_scale is not None:

            if isinstance(
                expected_scale,
                str,
            ):

                valid_scales = {
                    expected_scale
                }

            else:

                valid_scales = set(
                    expected_scale
                )

            if scale not in valid_scales:

                return False

        # ---------------------------------
        # ORIENTATION
        # ---------------------------------

        expected_orientation = (
            profile.get(
                "orientation"
            )
        )

        if (
            expected_orientation
            is not None
            and orientation
            != expected_orientation
        ):

            return False

        # ---------------------------------
        # TONE RELATION
        # ---------------------------------

        expected_tone = profile.get(
            "tone_relation"
        )

        if (
            expected_tone is not None
            and tone_relation
            != expected_tone
        ):

            return False

        return True
    # =====================================================
    # RESOLVE MATCHING STYLING PROFILES
    # =====================================================

    def resolve_profiles(
        self,
        base_pattern,
        scale=None,
        orientation=None,
        tone_relation=None,
        motif_color_count=0,
    ):

        results = []

        for (
            profile_name,
            profile,
        ) in self.profiles.items():

            # ---------------------------------
            # BASE PATTERN
            # ---------------------------------

            if base_pattern not in profile.get(
                "base_patterns",
                [],
            ):

                continue

            # ---------------------------------
            # MULTICOLOR PRINT
            #
            # Requires enough visible motif
            # colors. Do not match every floral
            # or geometric item automatically.
            # ---------------------------------

            threshold = profile.get(
                "multicolor_threshold"
            )

            if threshold is not None:

                if motif_color_count < threshold:

                    continue

            # ---------------------------------
            # NORMAL PROFILE MATCH
            # ---------------------------------

            if not self.matches_profile(
                profile_name=profile_name,
                base_pattern=base_pattern,
                scale=scale,
                orientation=orientation,
                tone_relation=tone_relation,
            ):

                continue

            results.append(
                profile_name
            )

        return results
    # =====================================================
    # OUTFIT RULE LOOKUP
    # =====================================================

    def get_outfit_rule(
        self,
        rule_name,
    ):

        if rule_name not in self.outfit_rules:

            raise ValueError(
                "Unknown pattern outfit rule: "
                f"{rule_name}"
            )

        return self.outfit_rules[
            rule_name
        ]