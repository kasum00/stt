import pandas as pd

from herstyle_ai.data.livostyle_mapping_rules import (
    PRODUCT_TYPE_MAPPING,
)


def map_product_type(
    product_type
):

    if pd.isna(product_type):
        return None

    return PRODUCT_TYPE_MAPPING.get(
        product_type
    )


def map_livostyle_taxonomy(
    df: pd.DataFrame
):

    result = df.copy()

    mapped = result[
        "product_type"
    ].apply(
        map_product_type
    )

    result["category"] = mapped.apply(
        lambda x: (
            x.get("category")
            if x
            else None
        )
    )

    result["subcategory"] = mapped.apply(
        lambda x: (
            x.get("subcategory")
            if x
            else None
        )
    )

    return result