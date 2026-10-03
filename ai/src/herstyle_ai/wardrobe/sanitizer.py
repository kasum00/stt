# =========================================================
# CATEGORY-AWARE ATTRIBUTE SANITIZER
# =========================================================


def sanitize_wardrobe_item(
    item,
):
    """
    Remove attributes that are semantically invalid
    for a garment category.

    The function mutates and returns WardrobeItem.
    """

    category = getattr(
        item,
        "category",
        None,
    )

    # =====================================================
    # BOTTOM
    # =====================================================

    if category == "bottom":

        item.sleeve_length = None
        item.neckline = None

    # =====================================================
    # SHOES
    # =====================================================

    elif category == "shoes":

        item.sleeve_length = None
        item.neckline = None
        item.fit = None

        # Current design-detail taxonomy is
        # garment-oriented, not shoe-oriented.
        item.design_details = []

    # =====================================================
    # ACCESSORIES / BAGS
    # =====================================================

    elif category == "accessory":

        item.sleeve_length = None
        item.neckline = None
        item.fit = None

        # The current design-detail taxonomy is garment-oriented.
        item.design_details = []

    return item
