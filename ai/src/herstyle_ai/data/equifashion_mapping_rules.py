# =========================================================
# GARMENT
# =========================================================

GARMENT_MAPPING = {

    "Blouse": (
        "top",
        "blouse",
    ),

    "Shirt": (
        "top",
        "shirt",
    ),

    "Sweater": (
        "top",
        "sweater",
    ),

    "Skirt": (
        "bottom",
        "skirt",
    ),

    "Pant": (
        "bottom",
        "trousers",
    ),

    "Dress": (
        "dress",
        "other_dress",
    ),

    "Coat": (
        "outerwear",
        "coat",
    ),

    # Do NOT force jumpsuit -> dress
    "Jumpsuit": (
        None,
        None,
    ),
}


# =========================================================
# SLEEVE LENGTH
# =========================================================

SLEEVE_LENGTH_MAPPING = {

    "Sleeveless":
        "sleeveless",

    "Short Sleeve":
        "short",

    "Elbow-length Sleeve":
        "elbow",

    # Source uses Mid-length Sleeve
    # separately from Elbow-length Sleeve.
    "Mid-length Sleeve":
        "three_quarter",

    "Long Sleeve":
        "long",
}


# =========================================================
# NECKLINE
# =========================================================

NECKLINE_MAPPING = {

    "Round Collar":
        "round",

    "V-Neck":
        "v_neck",

    "Square Collar":
        "square",

    "Boat Neck":
        "boat",

    "Lapel Collar":
        "collared",

    "Tailor Collar":
        "collared",

    "Stand Collar":
        "collared",

    "T-neck":
        "turtleneck",

    # Existing taxonomy does not
    # have direct equivalents.
    "U-Neck":
        "other",

    "Closed Collar":
        "other",

    "A-Line Collar":
        "other",

    "Irregular Collar":
        "other",

    "Swinging Collar":
        "other",
}


# =========================================================
# DESIGN DETAILS
# =========================================================

DESIGN_DETAIL_MAPPING = {

    "Ruffle Hem":
        "ruffled",

    "Ruffle Sleeve":
        "ruffled",

    "Pleated Hem":
        "pleated",

    "Slit Hem":
        "slit",

    "Lace Hem":
        "lace_detail",
}


# =========================================================
# STYLE TAGS
# =========================================================

STYLE_TAG_MAPPING = {

    "Elegant":
        "elegant",

    "Simple Style":
        "minimal",

    "Casual":
        "casual",

    "Casual and Relaxed Feeling":
        "casual",

    "Office":
        "office",

    "Office Lady":
        "office",

    "Business":
        "business",

    "Business Gentleman":
        "business",
}


# =========================================================
# CONTEXT / OCCASION
# =========================================================

CONTEXT_TOKENS = {

    "Party",
    "Date",
    "Commute",
    "Office",
    "Homewear",
    "Campus",
    "Sport",
    "Business",
    "Workwear",
    "Travel",
    "Wedding",
    "Home",
}


# =========================================================
# GARMENT LENGTH
# Source-only metadata.
# Do NOT force into HerStyleAI taxonomy.
# =========================================================

GARMENT_LENGTH_TOKENS = {

    "Short Blouse",
    "Mid-length Blouse",
    "Ultra-short Blouse",

    "Midi Shirt",
    "Mid-length Shirt",

    "Short Sweater",
    "Mid-length Sweater",
    "Ultra-short Sweater",

    "Long Dress",
    "Short Dress",
    "Knee-length Dress",
    "Midi Dress",
    "Mid-length Dress",
    "Ultra-short Dress",

    "Long Jumpsuit",
    "Midi Jumpsuit",
    "Short Jumpsuit",
    "Mid-length Jumpsuit",
    "Ultra-short Jumpsuit",

    "Long Pant",
    "Mid-length Pant",
    "Short Pant",
    "Midi Pant",
    "Knee-length Pant",
    "Ultra-short Pant",

    "Long Skirt",
    "Midi Skirt",
    "Mid-length Skirt",
    "Short Skirt",
    "Ultra-short Skirt",

    "Long Coat",
    "Mid-length Coat",
    "Knee-length Coat",
    "Short Coat",
    "Ultra-short Coat",
}


# =========================================================
# SLEEVE TYPE
# Source-only metadata
# =========================================================

SLEEVE_TYPE_TOKENS = {

    "Kimono Sleeve",
    "Shirt Sleeve",
    "Lantern Sleeve",
    "Flare Sleeve",
    "Regular Sleeve",
    "Ruffle Sleeve",
    "Flutter Sleeve",
    "Wrapped Sleeve",
    "Layered Sleeve",
    "Drop-shoulder Sleeve",
    "Princess Sleeve",
    "Raglan Sleeve",
    "Puffed Sleeve",
    "Petal Sleeve",
    "Dolman Sleeve",
}


# =========================================================
# HEM TYPE
# Source-only metadata
# =========================================================

HEM_TOKENS = {

    "Flat Hem",
    "Draped Hem",
    "Ruffle Hem",
    "Loose Hem",
    "Curved Hem",
    "Wavy Hem",
    "Slit Hem",
    "Tight-strap Hem",
    "Lace Hem",
    "Ankle-tied Hem",
    "Pleated Hem",
    "Irregular Hem",
    "Striped Hem",
    "Raw Hem",
    "Layered Hem",
    "Flared Hem",
    "Curled Hem",
    "Flanging Hem",
    "Drawstring Hem",
    "Low Waist Hem",
}


# =========================================================
# WAIST
# Source-only metadata
# =========================================================

WAIST_TOKENS = {

    "High Waist",
    "Natural Waist",
    "Mid Waist",
    "Low Waist",
    "Elastic Waist",
    "Relaxed Waist",
    "Ultra-low Waist",
}