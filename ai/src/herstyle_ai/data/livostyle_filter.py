# 

import pandas as pd

from herstyle_ai.data.livostyle_mapping_rules import (
    ALLOWED_PRODUCT_TYPES,
)


def filter_garments(
    products: pd.DataFrame
):

    result = products.copy()

    result = result[
        result["product_type"].isin(
            ALLOWED_PRODUCT_TYPES
        )
    ].copy()

    return result