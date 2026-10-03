from herstyle_ai.vlm.fashion_prompt import (
    CATEGORY,
    SUBCATEGORY,
    SUBCATEGORY_BY_CATEGORY,
    COLOR,
    MATERIAL,
    PATTERN,
    SLEEVE_LENGTH,
    NECKLINE,
    FIT,
    DESIGN_DETAILS,
)


# =========================================================
# TAXONOMY
# =========================================================

SINGLE_VALUE_FIELDS = {

    "category":
        set(CATEGORY),

    "subcategory":
        set(SUBCATEGORY),

    "color":
        set(COLOR),

    "material":
        set(MATERIAL),

    "pattern":
        set(PATTERN),

    "sleeve_length":
        set(SLEEVE_LENGTH),

    "neckline":
        set(NECKLINE),

    "fit":
        set(FIT),
}


MULTI_VALUE_FIELDS = {

    "design_details":
        set(DESIGN_DETAILS),
}


# =========================================================
# SUBCATEGORY PARENT
# =========================================================

SUBCATEGORY_PARENT = {

    subcategory:
        category

    for category, subcategories
    in SUBCATEGORY_BY_CATEGORY.items()

    for subcategory
    in subcategories
}


# =========================================================
# VALIDATE SINGLE VALUE
# =========================================================

def validate_single_value(
    field,
    value,
):

    if value is None:

        return None

    if not isinstance(
        value,
        str,
    ):

        return None

    value = (
        value.strip()
    )

    if (
        value
        in
        SINGLE_VALUE_FIELDS[
            field
        ]
    ):

        return value

    return None


# =========================================================
# VALIDATE MULTI VALUE
# =========================================================

def validate_multi_value(
    field,
    value,
):

    if value is None:

        return []

    if not isinstance(
        value,
        list,
    ):

        return []

    allowed = (
        MULTI_VALUE_FIELDS[
            field
        ]
    )

    result = []

    seen = set()

    for item in value:

        if not isinstance(
            item,
            str,
        ):

            continue

        item = (
            item.strip()
        )

        if (
            item in allowed
            and
            item not in seen
        ):

            seen.add(
                item
            )

            result.append(
                item
            )

    return result


# =========================================================
# CATEGORY / SUBCATEGORY CONSISTENCY
# =========================================================

def enforce_category_consistency(
    result,
):

    category = (
        result.get(
            "category"
        )
    )

    subcategory = (
        result.get(
            "subcategory"
        )
    )

    if subcategory is None:

        return result

    expected_category = (
        SUBCATEGORY_PARENT.get(
            subcategory
        )
    )

    if expected_category is None:

        result[
            "subcategory"
        ] = None

        return result

    # Trust the more specific subcategory.
    if category != expected_category:

        result[
            "category"
        ] = expected_category

    return result


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_prediction(
    prediction,
):

    if not isinstance(
        prediction,
        dict,
    ):

        raise ValueError(
            "Prediction must be a dictionary."
        )

    result = {}

    rejected = {}

    # =====================================================
    # SINGLE VALUES
    # =====================================================

    for field in (
        SINGLE_VALUE_FIELDS
    ):

        raw_value = (
            prediction.get(
                field
            )
        )

        validated = (
            validate_single_value(
                field,
                raw_value,
            )
        )

        result[
            field
        ] = validated

        if (
            raw_value is not None
            and
            validated is None
        ):

            rejected[
                field
            ] = raw_value

    # =====================================================
    # MULTI VALUE
    # =====================================================

    for field in (
        MULTI_VALUE_FIELDS
    ):

        raw_value = (
            prediction.get(
                field
            )
        )

        validated = (
            validate_multi_value(
                field,
                raw_value,
            )
        )

        result[
            field
        ] = validated

        if raw_value is None:

            raw_items = []

        elif isinstance(
            raw_value,
            list,
        ):

            raw_items = (
                raw_value
            )

        else:

            rejected[
                field
            ] = raw_value

            raw_items = []

        rejected_items = [

            item

            for item in raw_items

            if (
                not isinstance(
                    item,
                    str,
                )
                or
                item.strip()
                not in
                MULTI_VALUE_FIELDS[
                    field
                ]
            )
        ]

        if rejected_items:

            rejected[
                field
            ] = (
                rejected_items
            )

    # =====================================================
    # CATEGORY CONSISTENCY
    # =====================================================

    result = (
        enforce_category_consistency(
            result
        )
    )

    return {

        "prediction":
            result,

        "rejected":
            rejected,
    }