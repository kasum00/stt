from herstyle_ai.data.equifashion_mapping_rules import (
    GARMENT_MAPPING,
    SLEEVE_LENGTH_MAPPING,
    NECKLINE_MAPPING,
    DESIGN_DETAIL_MAPPING,
    STYLE_TAG_MAPPING,
    CONTEXT_TOKENS,
    GARMENT_LENGTH_TOKENS,
    SLEEVE_TYPE_TOKENS,
    HEM_TOKENS,
    WAIST_TOKENS,
)


# =========================================================
# CAPTION
# =========================================================

def split_caption(
    caption
):

    if caption is None:
        return []

    return [
        token.strip()
        for token in str(
            caption
        ).split(",")
        if token.strip()
    ]


# =========================================================
# SINGLE ATTRIBUTE
# =========================================================

def detect_single_mapping(
    tokens,
    mapping
):

    detected = []

    for token in tokens:

        if token in mapping:

            value = mapping[
                token
            ]

            if value not in detected:
                detected.append(
                    value
                )

    if len(detected) == 1:
        return detected[0], False

    if len(detected) > 1:
        return None, True

    return None, False


# =========================================================
# GARMENT
# =========================================================

def detect_garment(
    tokens
):

    detected = [
        token
        for token in tokens
        if token in GARMENT_MAPPING
    ]

    if not detected:

        return {
            "source_garment":
                None,

            "category":
                None,

            "subcategory":
                None,

            "category_conflict":
                False,
        }

    if len(detected) > 1:

        return {
            "source_garment":
                detected,

            "category":
                None,

            "subcategory":
                None,

            "category_conflict":
                True,
        }

    garment = detected[0]

    category, subcategory = (
        GARMENT_MAPPING[
            garment
        ]
    )

    # Special refinement:
    # exact Midi Dress can safely use midi_dress
    if (
        garment == "Dress"
        and
        "Midi Dress" in tokens
    ):

        subcategory = (
            "midi_dress"
        )

    return {
        "source_garment":
            garment,

        "category":
            category,

        "subcategory":
            subcategory,

        "category_conflict":
            False,
    }


# =========================================================
# MULTI LABEL
# =========================================================

def detect_multi_mapping(
    tokens,
    mapping
):

    detected = set()

    for token in tokens:

        if token in mapping:

            detected.add(
                mapping[
                    token
                ]
            )

    return sorted(
        detected
    )


# =========================================================
# SOURCE METADATA
# =========================================================

def detect_source_tokens(
    tokens,
    allowed_tokens
):

    return [
        token
        for token in tokens
        if token in allowed_tokens
    ]


# =========================================================
# MAIN RECORD MAPPER
# =========================================================

def map_equifashion_caption(
    caption
):

    tokens = split_caption(
        caption
    )

    garment = detect_garment(
        tokens
    )

    sleeve_length, sleeve_conflict = (
        detect_single_mapping(
            tokens,
            SLEEVE_LENGTH_MAPPING,
        )
    )

    neckline, neckline_conflict = (
        detect_single_mapping(
            tokens,
            NECKLINE_MAPPING,
        )
    )

    design_details = (
        detect_multi_mapping(
            tokens,
            DESIGN_DETAIL_MAPPING,
        )
    )

    style_tags = (
        detect_multi_mapping(
            tokens,
            STYLE_TAG_MAPPING,
        )
    )

    context_tags = (
        detect_source_tokens(
            tokens,
            CONTEXT_TOKENS,
        )
    )

    garment_length_tokens = (
        detect_source_tokens(
            tokens,
            GARMENT_LENGTH_TOKENS,
        )
    )

    sleeve_type_tokens = (
        detect_source_tokens(
            tokens,
            SLEEVE_TYPE_TOKENS,
        )
    )

    hem_tokens = (
        detect_source_tokens(
            tokens,
            HEM_TOKENS,
        )
    )

    waist_tokens = (
        detect_source_tokens(
            tokens,
            WAIST_TOKENS,
        )
    )

    # -----------------------------------------
    # Track consumed source tokens
    # -----------------------------------------

    consumed = set()

    source_garment = garment[
        "source_garment"
    ]

    if isinstance(
        source_garment,
        str
    ):
        consumed.add(
            source_garment
        )

    elif isinstance(
        source_garment,
        list
    ):
        consumed.update(
            source_garment
        )

    for mapping in [
        SLEEVE_LENGTH_MAPPING,
        NECKLINE_MAPPING,
        DESIGN_DETAIL_MAPPING,
        STYLE_TAG_MAPPING,
    ]:

        for token in tokens:

            if token in mapping:
                consumed.add(
                    token
                )

    consumed.update(
        context_tags
    )

    consumed.update(
        garment_length_tokens
    )

    consumed.update(
        sleeve_type_tokens
    )

    consumed.update(
        hem_tokens
    )

    consumed.update(
        waist_tokens
    )

    unused_tokens = [
        token
        for token in tokens
        if token not in consumed
    ]

    return {

        # =====================================
        # Source
        # =====================================

        "source_caption":
            caption,

        "source_tokens":
            tokens,

        "source_garment":
            garment[
                "source_garment"
            ],

        # =====================================
        # HerStyleAI taxonomy
        # =====================================

        "category":
            garment[
                "category"
            ],

        "subcategory":
            garment[
                "subcategory"
            ],

        "color":
            None,

        "material":
            None,

        "pattern":
            None,

        "sleeve_length":
            sleeve_length,

        "neckline":
            neckline,

        "fit":
            None,

        "design_details":
            design_details,

        "style_tags":
            style_tags,

        # =====================================
        # Source-only attributes
        # =====================================

        "context_tags":
            context_tags,

        "source_garment_length":
            garment_length_tokens,

        "source_sleeve_type":
            sleeve_type_tokens,

        "source_hem":
            hem_tokens,

        "source_waist":
            waist_tokens,

        "unused_tokens":
            unused_tokens,

        # =====================================
        # Audit
        # =====================================

        "category_conflict":
            garment[
                "category_conflict"
            ],

        "sleeve_conflict":
            sleeve_conflict,

        "neckline_conflict":
            neckline_conflict,
    }