import numpy as np
import pandas as pd


# =========================================================
# OFFICE CONTEXT
# =========================================================

POSITIVE_CONTEXT = {
    "Office",
    "Business",
    "Commute",
    "Workwear",
}


NEGATIVE_CONTEXT = {
    "Homewear",
    "Sport",
    "Wedding",
    "Home",
}


REVIEW_CONTEXT = {
    "Party",
    "Date",
    "Campus",
    "Travel",
}


REVIEW_SOURCE_TOKENS = {
    "Sexy",
}


UNSUPPORTED_GARMENTS = {
    "Jumpsuit",
}


# =========================================================
# HELPERS
# =========================================================

def to_set(value):

    if value is None:
        return set()

    if isinstance(
        value,
        np.ndarray
    ):
        return set(
            value.tolist()
        )

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        )
    ):
        return set(value)

    try:

        if pd.isna(value):
            return set()

    except (
        TypeError,
        ValueError,
    ):
        pass

    return {
        value
    }


# =========================================================
# OFFICE RELEVANCE
# =========================================================

def evaluate_office_relevance(
    row
):

    context_tags = to_set(
        row.get(
            "context_tags"
        )
    )

    source_tokens = to_set(
        row.get(
            "source_tokens"
        )
    )

    garment = row.get(
        "source_garment"
    )

    positive = (
        context_tags
        & POSITIVE_CONTEXT
    )

    negative = (
        context_tags
        & NEGATIVE_CONTEXT
    )

    review = (
        context_tags
        & REVIEW_CONTEXT
    )

    risky = (
        source_tokens
        & REVIEW_SOURCE_TOKENS
    )

    reasons = []

    # =========================================
    # Taxonomy support is independent
    # =========================================

    taxonomy_supported = (
        garment
        not in UNSUPPORTED_GARMENTS
        and garment is not None
    )

    # =========================================
    # Duplicate annotation uncertainty
    # =========================================

    duplicate_caption_conflict = bool(
        row.get(
            "duplicate_caption_conflict",
            False,
        )
    )

    duplicate_label_conflict = bool(
        row.get(
            "duplicate_label_conflict",
            False,
        )
    )

    if (
        duplicate_caption_conflict
        or
        duplicate_label_conflict
    ):

        reasons.append(
            "duplicate_annotation_conflict"
        )

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "review",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # Contradictory context
    # =========================================

    if positive and negative:

        reasons.append(
            "conflicting_positive_negative_context"
        )

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "review",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # Clear negative
    # =========================================

    if negative:

        reasons.extend([
            f"context:{value}"
            for value in sorted(
                negative
            )
        ])

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "negative",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # Positive + ambiguous context
    # Conservative office-clean rule
    # =========================================

    if (
        positive
        and (
            review
            or risky
        )
    ):

        reasons.extend([
            f"context:{value}"
            for value in sorted(
                positive
            )
        ])

        reasons.append(
            "mixed_office_context"
        )

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "review",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # Clear positive
    # =========================================

    if positive:

        reasons.extend([
            f"context:{value}"
            for value in sorted(
                positive
            )
        ])

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "positive",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # Ambiguous context
    # =========================================

    if review or risky:

        reasons.extend([
            f"context:{value}"
            for value in sorted(
                review
            )
        ])

        reasons.extend([
            f"token:{value}"
            for value in sorted(
                risky
            )
        ])

        return {
            "taxonomy_supported":
                taxonomy_supported,

            "office_relevance":
                "review",

            "office_relevance_reasons":
                reasons,
        }

    # =========================================
    # No explicit signal
    # =========================================

    return {
        "taxonomy_supported":
            taxonomy_supported,

        "office_relevance":
            "review",

        "office_relevance_reasons": [
            "no_explicit_office_signal"
        ],
    }


def add_office_relevance(
    df
):

    result = df.copy()

    evaluated = result.apply(
        evaluate_office_relevance,
        axis=1,
    )

    result[
        "taxonomy_supported"
    ] = evaluated.apply(
        lambda x:
        x["taxonomy_supported"]
    )

    result[
        "office_relevance"
    ] = evaluated.apply(
        lambda x:
        x["office_relevance"]
    )

    result[
        "office_relevance_reasons"
    ] = evaluated.apply(
        lambda x:
        x[
            "office_relevance_reasons"
        ]
    )

    result[
        "office_clean_eligible"
    ] = (
        (
            result[
                "taxonomy_supported"
            ] == True
        )
        &
        (
            result[
                "office_relevance"
            ] == "positive"
        )
    )

    return result