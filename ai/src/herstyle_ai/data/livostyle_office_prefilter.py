import pandas as pd
import numpy as np


TARGET_FIELDS = [
    "color",
    "material",
    "pattern",
]


def normalize_text(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except (
        TypeError,
        ValueError,
    ):
        pass

    return str(
        value
    ).strip().lower()


def to_string_set(value):

    if value is None:
        return set()

    if isinstance(
        value,
        np.ndarray
    ):

        return {
            str(item).strip()
            for item in value.tolist()
            if str(item).strip()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        )
    ):

        return {
            str(item).strip()
            for item in value
            if str(item).strip()
        }

    try:

        if pd.isna(value):
            return set()

    except (
        TypeError,
        ValueError,
    ):
        pass

    text = str(
        value
    ).strip()

    if not text:
        return set()

    return {
        text
    }


def split_source_tags(tags):

    if tags is None:
        return set()

    if isinstance(
        tags,
        np.ndarray
    ):

        return {
            normalize_text(tag)
            for tag in tags.tolist()
            if normalize_text(tag)
        }

    if isinstance(
        tags,
        (
            list,
            tuple,
            set,
        )
    ):

        return {
            normalize_text(tag)
            for tag in tags
            if normalize_text(tag)
        }

    text = normalize_text(
        tags
    )

    if not text:
        return set()

    return {
        tag.strip()
        for tag in text.split("|")
        if tag.strip()
    }


def count_target_fields(row):

    count = 0

    for field in TARGET_FIELDS:

        value = row.get(field)

        if value is not None:

            try:

                if pd.notna(value):
                    count += 1

            except (TypeError, ValueError):
                pass

    return count


def evaluate_office_item(
    row,
    config,
):

    reasons = []

    review_reasons = []

    category = row.get(
        "category"
    )

    subcategory = row.get(
        "subcategory"
    )

    design_details = to_string_set(
        row.get(
            "design_details"
        )
    )

    source_tags = split_source_tags(
        row.get(
            "tags"
        )
    )

    # =========================================
    # CATEGORY
    # =========================================

    if category not in set(
        config[
            "allowed_categories"
        ]
    ):

        reasons.append(
            f"category:{category}"
        )

    # =========================================
    # SUBCATEGORY
    # =========================================

    core = set(
        config[
            "core_subcategories"
        ]
    )

    extended = set(
        config[
            "extended_subcategories"
        ]
    )

    if subcategory in core:

        subcategory_status = "core"

    elif subcategory in extended:

        subcategory_status = "extended"

    else:

        subcategory_status = "unknown"

        reasons.append(
            f"subcategory:{subcategory}"
        )

    # =========================================
    # DESIGN DETAILS
    # =========================================

    hard_design = set(
        config[
            "hard_exclude_design_details"
        ]
    )

    review_design = set(
        config[
            "review_design_details"
        ]
    )

    detected_hard_design = (
        design_details
        & hard_design
    )

    if detected_hard_design:

        reasons.append(
            "design:"
            + ",".join(
                sorted(
                    detected_hard_design
                )
            )
        )

    detected_review_design = (
        design_details
        & review_design
    )

    if detected_review_design:

        review_reasons.append(
            "design:"
            + ",".join(
                sorted(
                    detected_review_design
                )
            )
        )

    # =========================================
    # SOURCE TAGS
    # =========================================

    hard_tags = set(
        config[
            "hard_exclude_tags"
        ]
    )

    review_tags = set(
        config[
            "review_tags"
        ]
    )

    detected_hard_tags = (
        source_tags
        & hard_tags
    )

    if detected_hard_tags:

        reasons.append(
            "tag:"
            + ",".join(
                sorted(
                    detected_hard_tags
                )
            )
        )

    detected_review_tags = (
        source_tags
        & review_tags
    )

    if detected_review_tags:

        review_reasons.append(
            "tag:"
            + ",".join(
                sorted(
                    detected_review_tags
                )
            )
        )

    # =========================================
    # ATTRIBUTE COMPLETENESS
    # =========================================

    target_count = (
        count_target_fields(
            row
        )
    )

    minimum = int(
        config.get(
            "minimum_target_fields",
            2
        )
    )

    if target_count < minimum:

        review_reasons.append(
            f"target_fields:{target_count}"
        )

    # =========================================
    # FINAL STATUS
    # =========================================

    if reasons:

        status = "exclude"

    elif review_reasons:

        status = "review"

    else:

        status = "keep"

    return {
        "office_prefilter":
            status,

        "office_exclude_reasons":
            reasons,

        "office_review_reasons":
            review_reasons,

        "target_field_count":
            target_count,

        "subcategory_status":
            subcategory_status,
    }


def apply_office_prefilter(
    df,
    config,
):

    result = df.copy()

    evaluated = result.apply(
        lambda row:
        evaluate_office_item(
            row,
            config,
        ),
        axis=1,
    )

    result[
        "office_prefilter"
    ] = evaluated.apply(
        lambda x:
        x["office_prefilter"]
    )

    result[
        "office_exclude_reasons"
    ] = evaluated.apply(
        lambda x:
        x[
            "office_exclude_reasons"
        ]
    )

    result[
        "office_review_reasons"
    ] = evaluated.apply(
        lambda x:
        x[
            "office_review_reasons"
        ]
    )

    result[
        "target_field_count"
    ] = evaluated.apply(
        lambda x:
        x[
            "target_field_count"
        ]
    )

    result[
        "subcategory_status"
    ] = evaluated.apply(
        lambda x:
        x[
            "subcategory_status"
        ]
    )

    return result