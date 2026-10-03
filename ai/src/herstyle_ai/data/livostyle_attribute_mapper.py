import re

import pandas as pd

from herstyle_ai.data.livostyle_attribute_rules import (
    COLOR_KEYWORDS,
    INVALID_COLOR_VALUES,
    MULTICOLOR_KEYWORDS,
    PATTERN_KEYWORDS,
    MATERIAL_ALIASES,
    STRETCH_FIBERS,
    DOMINANT_MATERIAL_THRESHOLD,
    SLEEVE_LENGTH_KEYWORDS,
    NECKLINE_KEYWORDS,
    FIT_KEYWORDS,
    DESIGN_DETAIL_KEYWORDS,
    STYLE_TAG_KEYWORDS,
)

def normalize_text(value):

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


# =========================================================
# COLOR NORMALIZATION
# =========================================================

def normalize_color(raw_color):

    text = normalize_text(
        raw_color
    )

    if not text:
        return None

    # -----------------------------------------
    # Invalid values
    # -----------------------------------------

    if text in INVALID_COLOR_VALUES:
        return None

    # -----------------------------------------
    # Multicolor
    # -----------------------------------------

    for keyword in MULTICOLOR_KEYWORDS:

        if keyword in text:
            return "multicolor"

    # -----------------------------------------
    # Explicit combined colors
    # -----------------------------------------

    if " and " in text:

        return "multicolor"

    if "/" in text:

        return "multicolor"

    # -----------------------------------------
    # Normal colors
    # -----------------------------------------

    # navy must be checked before generic blue
    ordered_colors = [
        "black",
        "white",
        "gray",
        "beige",
        "brown",
        "navy",
        "blue",
        "red",
        "pink",
        "purple",
        "green",
        "yellow",
        "orange",
        "metallic",
    ]

    for target_color in ordered_colors:

        keywords = COLOR_KEYWORDS[
            target_color
        ]

        for keyword in keywords:

            if keyword in text:

                return target_color

    return None


# =========================================================
# BUILD COLOR METADATA
# =========================================================

def build_product_color_table(
    variants: pd.DataFrame
):

    df = variants.copy()

    df["color"] = (
        df["color"]
        .astype("string")
        .str.strip()
    )

    df = df[
        df["color"].notna()
    ]

    df = df[
        df["color"] != ""
    ]

    # -----------------------------------------
    # Unique raw colors per product
    # -----------------------------------------

    grouped = (
        df
        .groupby("product_id")["color"]
        .apply(
            lambda values:
            sorted(
                set(
                    str(value).strip()
                    for value in values
                    if pd.notna(value)
                    and str(value).strip()
                )
            )
        )
        .reset_index(
            name="source_colors"
        )
    )

    grouped[
        "num_source_colors"
    ] = grouped[
        "source_colors"
    ].apply(len)

    # -----------------------------------------
    # Only trust products with one variant color
    # -----------------------------------------

    grouped[
        "source_color_raw"
    ] = grouped.apply(
        lambda row:
        row["source_colors"][0]
        if row["num_source_colors"] == 1
        else None,
        axis=1
    )

    grouped[
        "color"
    ] = grouped[
        "source_color_raw"
    ].apply(
        normalize_color
    )

    # -----------------------------------------
    # Provenance
    # -----------------------------------------

    grouped[
        "color_source"
    ] = grouped.apply(
        lambda row:
        "variant_single_color"
        if (
            row["num_source_colors"] == 1
            and row["color"] is not None
        )
        else None,
        axis=1
    )

    return grouped


# =========================================================
# APPLY TO PRODUCT TABLE
# =========================================================

def add_color_attributes(
    products: pd.DataFrame,
    variants: pd.DataFrame,
):

    color_table = (
        build_product_color_table(
            variants
        )
    )

    result = products.merge(
        color_table[
            [
                "product_id",
                "source_colors",
                "num_source_colors",
                "source_color_raw",
                "color",
                "color_source",
            ]
        ],
        left_on="id",
        right_on="product_id",
        how="left",
        suffixes=(
            "",
            "_variant"
        ),
    )

    return result

# =========================================================
# TAG UTILITIES
# =========================================================

def split_tags(tags):

    text = normalize_text(tags)

    if not text:
        return []

    return [
        tag.strip()
        for tag in text.split("|")
        if tag.strip()
    ]


# =========================================================
# PATTERN
# =========================================================

def detect_pattern_candidates(tags):

    tag_list = split_tags(tags)

    detected = set()

    for tag in tag_list:

        for target_pattern, keywords in (
            PATTERN_KEYWORDS.items()
        ):

            for keyword in keywords:

                if keyword in tag:

                    detected.add(
                        target_pattern
                    )

                    break

    return sorted(detected)


def normalize_pattern(tags):

    candidates = (
        detect_pattern_candidates(
            tags
        )
    )

    # High-confidence only:
    # exactly one pattern detected
    if len(candidates) == 1:
        return candidates[0]

    return None


def add_pattern_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    result[
        "pattern_candidates"
    ] = result[
        "tags"
    ].apply(
        detect_pattern_candidates
    )

    result[
        "pattern_candidate_count"
    ] = result[
        "pattern_candidates"
    ].apply(len)

    result[
        "pattern"
    ] = result[
        "pattern_candidates"
    ].apply(
        lambda values:
        values[0]
        if len(values) == 1
        else None
    )

    result[
        "pattern_source"
    ] = result[
        "pattern"
    ].apply(
        lambda value:
        "tags"
        if pd.notna(value)
        else None
    )

    result[
        "pattern_conflict"
    ] = (
        result[
            "pattern_candidate_count"
        ] > 1
    )

    return result

# =========================================================
# MATERIAL
# =========================================================

MATERIAL_COMPONENT_PATTERN = re.compile(
    r"(\d{1,3})\s*%\s*"
    r"(cotton|polyester|viscose|rayon|acrylic|nylon|"
    r"spandex|elastane|linen|wool|silk|modal|lyocell|"
    r"tencel|polyamide|pbt)",
    flags=re.IGNORECASE,
)


def extract_material_composition(
    description
):

    text = normalize_text(
        description
    )

    composition = []

    for percent, raw_material in (
        MATERIAL_COMPONENT_PATTERN.findall(
            text
        )
    ):

        raw_material = (
            raw_material
            .strip()
            .lower()
        )

        composition.append(
            {
                "material": raw_material,
                "percent": int(percent),
            }
        )

    return composition


def normalize_material_name(
    raw_material
):

    raw_material = normalize_text(
        raw_material
    )

    return MATERIAL_ALIASES.get(
        raw_material
    )


def infer_material_from_composition(
    composition
):

    if not composition:
        return None

    totals = {}

    # -----------------------------------------
    # Aggregate normalized materials
    # -----------------------------------------

    for item in composition:

        raw_material = item[
            "material"
        ]

        percent = item[
            "percent"
        ]

        # Ignore small stretch additives
        if raw_material in STRETCH_FIBERS:

            continue

        normalized = (
            normalize_material_name(
                raw_material
            )
        )

        if normalized is None:
            continue

        totals[normalized] = (
            totals.get(
                normalized,
                0
            )
            + percent
        )

    if not totals:
        return None

    # -----------------------------------------
    # Only one meaningful material
    # -----------------------------------------

    if len(totals) == 1:

        return next(
            iter(totals)
        )

    # -----------------------------------------
    # Find dominant material
    # -----------------------------------------

    dominant_material = max(
        totals,
        key=totals.get
    )

    dominant_percent = totals[
        dominant_material
    ]

    if (
        dominant_percent
        >= DOMINANT_MATERIAL_THRESHOLD
    ):

        return dominant_material

    # -----------------------------------------
    # Genuine blend
    # -----------------------------------------

    return "blended"


def infer_material_fallback(
    description
):

    text = normalize_text(
        description
    )

    if not text:
        return None

    # Longer terms first
    ordered_terms = sorted(
        MATERIAL_ALIASES.keys(),
        key=len,
        reverse=True,
    )

    detected = set()

    for term in ordered_terms:

        if term in text:

            normalized = (
                MATERIAL_ALIASES[
                    term
                ]
            )

            detected.add(
                normalized
            )

    if len(detected) == 1:

        return next(
            iter(detected)
        )

    if len(detected) > 1:

        return "blended"

    return None


def infer_material(
    description
):

    composition = (
        extract_material_composition(
            description
        )
    )

    # Highest-confidence source
    if composition:

        material = (
            infer_material_from_composition(
                composition
            )
        )

        if material:

            return {
                "material": material,
                "material_source":
                    "percentage_composition",
                "material_composition":
                    composition,
            }

    # Fallback for descriptions such as:
    # "cotton-viscose blend"
    material = (
        infer_material_fallback(
            description
        )
    )

    if material:

        return {
            "material": material,
            "material_source":
                "description_text",
            "material_composition":
                composition,
        }

    return {
        "material": None,
        "material_source": None,
        "material_composition":
            composition,
    }


def add_material_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    inferred = result[
        "description"
    ].apply(
        infer_material
    )

    result[
        "material"
    ] = inferred.apply(
        lambda x:
        x["material"]
    )

    result[
        "material_source"
    ] = inferred.apply(
        lambda x:
        x["material_source"]
    )

    result[
        "material_composition"
    ] = inferred.apply(
        lambda x:
        x["material_composition"]
    )

    return result

# =========================================================
# GENERIC TAG ATTRIBUTE DETECTOR
# =========================================================

def detect_tag_attribute_candidates(
    tags,
    rules,
):

    tag_list = split_tags(tags)

    detected = set()

    for tag in tag_list:

        for target, keywords in rules.items():

            for keyword in keywords:

                if keyword in tag:

                    detected.add(
                        target
                    )

                    break

    return sorted(detected)


# =========================================================
# SLEEVE LENGTH
# =========================================================

def add_sleeve_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    result[
        "sleeve_candidates"
    ] = result[
        "tags"
    ].apply(
        lambda tags:
        detect_tag_attribute_candidates(
            tags,
            SLEEVE_LENGTH_KEYWORDS,
        )
    )

    result[
        "sleeve_candidate_count"
    ] = result[
        "sleeve_candidates"
    ].apply(len)

    result[
        "sleeve_length"
    ] = result[
        "sleeve_candidates"
    ].apply(
        lambda values:
        values[0]
        if len(values) == 1
        else None
    )

    result[
        "sleeve_source"
    ] = result[
        "sleeve_length"
    ].apply(
        lambda x:
        "tags"
        if pd.notna(x)
        else None
    )

    result[
        "sleeve_conflict"
    ] = (
        result[
            "sleeve_candidate_count"
        ] > 1
    )

    return result


# =========================================================
# NECKLINE
# =========================================================

def add_neckline_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    result[
        "neckline_candidates"
    ] = result[
        "tags"
    ].apply(
        lambda tags:
        detect_tag_attribute_candidates(
            tags,
            NECKLINE_KEYWORDS,
        )
    )

    result[
        "neckline_candidate_count"
    ] = result[
        "neckline_candidates"
    ].apply(len)

    result[
        "neckline"
    ] = result[
        "neckline_candidates"
    ].apply(
        resolve_neckline_candidates
    )

    result[
        "neckline_source"
    ] = result[
        "neckline"
    ].apply(
        lambda x:
        "tags"
        if pd.notna(x)
        else None
    )

    result[
        "neckline_conflict"
    ] = (
        result["neckline"].isna()
        &
        (
            result[
                "neckline_candidate_count"
            ] > 1
        )
    )

    return result

def resolve_neckline_candidates(
    candidates
):

    candidates = set(
        candidates
    )

    if not candidates:
        return None

    if len(candidates) == 1:
        return next(
            iter(candidates)
        )

    # =========================================
    # Structural neckline has priority
    # =========================================

    if "turtleneck" in candidates:
        return "turtleneck"

    if "halter" in candidates:
        return "halter"

    if "strapless" in candidates:
        return "strapless"

    if "collared" in candidates:
        return "collared"

    # =========================================
    # Otherwise conflict remains unresolved
    # =========================================

    return None

# =========================================================
# FIT
# =========================================================

def extract_fit_section(
    description
):

    text = normalize_text(
        description
    )

    if not text:
        return ""

    match = re.search(
        r"fit\s*&\s*sizing\s*"
        r"(.*?)"
        r"(?:wear\s+it\s+with|$)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return match.group(1).strip()


def detect_fit_from_tags(
    tags
):

    tag_list = split_tags(
        tags
    )

    detected = set()

    for tag in tag_list:

        normalized_tag = (
            normalize_text(tag)
        )

        for target, keywords in (
            FIT_KEYWORDS.items()
        ):

            for keyword in keywords:

                keyword = (
                    normalize_text(
                        keyword
                    )
                )

                # Exact tag match only
                if normalized_tag == keyword:

                    detected.add(
                        target
                    )

    return sorted(detected)


def detect_fit_from_section(
    description
):

    section = extract_fit_section(
        description
    )

    if not section:
        return []

    detected = set()

    for target, keywords in (
        FIT_KEYWORDS.items()
    ):

        for keyword in keywords:

            keyword = normalize_text(
                keyword
            )

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                section,
            ):

                detected.add(
                    target
                )

                break

    return sorted(detected)


def resolve_fit_candidates(
    candidates
):

    candidates = set(
        candidates
    )

    if not candidates:
        return None

    if len(candidates) == 1:

        return next(
            iter(candidates)
        )

    # -----------------------------------------
    # regular is weakest
    # -----------------------------------------

    if "regular" in candidates:

        candidates.remove(
            "regular"
        )

    if len(candidates) == 1:

        return next(
            iter(candidates)
        )

    # -----------------------------------------
    # oversized > relaxed
    # -----------------------------------------

    if candidates == {
        "oversized",
        "relaxed",
    }:

        return "oversized"

    # -----------------------------------------
    # fitted > slim
    # -----------------------------------------

    if candidates == {
        "fitted",
        "slim",
    }:

        return "fitted"

    return None


def infer_fit(
    tags,
    description,
):

    # =========================================
    # Priority 1: explicit tags
    # =========================================

    tag_candidates = (
        detect_fit_from_tags(
            tags
        )
    )

    if tag_candidates:

        return {
            "fit_candidates":
                tag_candidates,

            "fit":
                resolve_fit_candidates(
                    tag_candidates
                ),

            "fit_source":
                "tags",
        }

    # =========================================
    # Priority 2: Fit & sizing section
    # =========================================

    section_candidates = (
        detect_fit_from_section(
            description
        )
    )

    if section_candidates:

        return {
            "fit_candidates":
                section_candidates,

            "fit":
                resolve_fit_candidates(
                    section_candidates
                ),

            "fit_source":
                "fit_section",
        }

    return {
        "fit_candidates": [],
        "fit": None,
        "fit_source": None,
    }


def add_fit_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    inferred = result.apply(
        lambda row:
        infer_fit(
            row.get("tags"),
            row.get("description"),
        ),
        axis=1,
    )

    result[
        "fit_candidates"
    ] = inferred.apply(
        lambda x:
        x["fit_candidates"]
    )

    result[
        "fit"
    ] = inferred.apply(
        lambda x:
        x["fit"]
    )

    result[
        "fit_source"
    ] = inferred.apply(
        lambda x:
        x["fit_source"]
    )

    result[
        "fit_conflict"
    ] = result.apply(
        lambda row:
        (
            len(
                row[
                    "fit_candidates"
                ]
            ) > 1
            and pd.isna(
                row["fit"]
            )
        ),
        axis=1,
    )

    return result

# =========================================================
# DESIGN DETAILS
# =========================================================

def detect_design_details(
    tags,
    title,
):

    text = " ".join([
        normalize_text(tags),
        normalize_text(title),
    ])

    detected = set()

    for target, keywords in (
        DESIGN_DETAIL_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                detected.add(target)
                break

    return sorted(detected)


def add_design_detail_attributes(
    products: pd.DataFrame
):

    result = products.copy()

    result[
        "design_details"
    ] = result.apply(
        lambda row:
        detect_design_details(
            row.get("tags"),
            row.get("title"),
        ),
        axis=1,
    )

    result[
        "design_detail_count"
    ] = result[
        "design_details"
    ].apply(len)

    result[
        "design_details_source"
    ] = result[
        "design_details"
    ].apply(
        lambda values:
        "tags_title"
        if len(values) > 0
        else None
    )

    return result

# =========================================================
# STYLE TAGS
# =========================================================

def detect_style_tags(
    tags,
    title,
):

    text = " ".join([
        normalize_text(tags),
        normalize_text(title),
    ])

    detected = set()

    for target, keywords in (
        STYLE_TAG_KEYWORDS.items()
    ):

        for keyword in keywords:

            keyword = normalize_text(
                keyword
            )

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text
            ):

                detected.add(
                    target
                )

                break

    return sorted(detected)


def add_style_tags(
    products: pd.DataFrame
):

    result = products.copy()

    result[
        "style_tags"
    ] = result.apply(
        lambda row:
        detect_style_tags(
            row.get("tags"),
            row.get("title"),
        ),
        axis=1,
    )

    result[
        "style_tag_count"
    ] = result[
        "style_tags"
    ].apply(len)

    result[
        "style_tags_source"
    ] = result[
        "style_tags"
    ].apply(
        lambda values:
        "tags_title"
        if len(values) > 0
        else None
    )

    return result