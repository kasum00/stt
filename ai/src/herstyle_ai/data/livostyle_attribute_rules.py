# =========================================================
# LIVOSTYLE ATTRIBUTE NORMALIZATION RULES
# =========================================================


# ---------------------------------------------------------
# VALUES THAT ARE NOT COLORS
# ---------------------------------------------------------

INVALID_COLOR_VALUES = {
    "plaid",
    "stripe",
    "striped",

    "tie dye",
    "pastel tie dye",

    "leopard",
    "floral",

    "medium",
    "pattern",
    "printed",
    "print",

    "as shown",
    "dark",
}

# ---------------------------------------------------------
# HERSTYLEAI COLOR KEYWORDS
# ---------------------------------------------------------

COLOR_KEYWORDS = {

    "black": [
        "black",
    ],

    "white": [
        "white",
        "ivory",
        "off white",
        "off-white",
    ],

    "gray": [
        "gray",
        "grey",
        "charcoal",
    ],

    "beige": [
        "beige",
        "cream",
        "khaki",
        "taupe",
        "tan",
        "oatmeal",
        "sand",

        # NEW
        "natural",
        "ecru",
        "almond",
        "champagne",
    ],

    "brown": [
        "brown",
        "camel",
        "coffee",
        "mocha",
        "caramel",

        # NEW
        "cinnamon",
        "hazelnut",
        "cappuccino",
    ],

    "navy": [
        "navy",
    ],

    "blue": [
        "blue",
        "aqua",
        "turquoise",
        "teal",
        "cobalt",
        "denim",

        # NEW
        "azure",
        "deep sky",
        "royal",
        "indigo",
    ],

    "red": [
        "red",
        "burgundy",
        "wine",
        "scarlet",
        "cerise",
        "brick",

        # NEW
        "cabernet",
        "tomato",
    ],

    "pink": [
        "pink",
        "blush",
        "fuchsia",
        "fuschia",

        # typo + aliases
        "fuchisa",
        "rose",
        "magenta",
    ],

    "purple": [
        "purple",
        "lavender",
        "lilac",
        "violet",
        "mauve",

        # NEW
        "plum",
    ],

    "green": [
        "green",
        "sage",
        "mint",
        "olive",
        "moss",
        "matcha",
        "army",
        "gum leaf",

        # NEW
        "jade",
        "lime",
        "pistachio",
        "forest",
        "hunter",
    ],

    "yellow": [
        "yellow",
        "mustard",
        "ochre",
        "banana",
    ],

    "orange": [
        "orange",
        "coral",
        "rust",
        "apricot",
        "peach",
    ],

    "metallic": [
        "metallic",
        "silver",
        "gold",

        # NEW
        "hologram",
    ],
}


MULTICOLOR_KEYWORDS = [
    "multicolor",
    "multi color",
    "multi-color",
    "multi",
    "black and white",
    "blue and white",
    "red and white",
    "pink and white",
]

# =========================================================
# PATTERN RULES
# =========================================================

PATTERN_KEYWORDS = {

    "solid": [
        "solid",
        "solid color",
    ],

    "striped": [
        "stripe",
        "striped",
    ],

    "checked": [
        "check",
        "checked",
        "checkered",
        "gingham",
    ],

    "plaid": [
        "plaid",
        "buffalo plaid",
        "tartan",
    ],

    "floral": [
        "floral",
        "floral print",
        "flower print",
    ],

    "polka_dot": [
        "polka dot",
        "polka dots",
        "dotted",
    ],

    "geometric": [
        "geometric",
        "geometric print",
    ],

    "animal_print": [
        "leopard",
        "leopard print",
        "zebra",
        "snake print",
        "animal print",
    ],

    "abstract": [
        "abstract",
        "abstract print",
        "tie dye",
        "tie-dye",
    ],

    "graphic": [
        "graphic",
        "graphic print",
    ],
}

# =========================================================
# MATERIAL RULES
# =========================================================

MATERIAL_ALIASES = {

    # Natural / major fibers
    "cotton": "cotton",
    "polyester": "polyester",

    "viscose": "viscose_rayon",
    "rayon": "viscose_rayon",
    "modal": "viscose_rayon",
    "lyocell": "viscose_rayon",
    "tencel": "viscose_rayon",

    "wool": "wool",
    "linen": "linen",
    "silk": "silk",

    # Visual fabric/material fallback
    "denim": "denim",
    "leather": "leather",
    "faux leather": "leather",

    # Other synthetic fibers
    "acrylic": "synthetic",
    "nylon": "synthetic",
    "polyamide": "synthetic",
    "pbt": "synthetic",
}


# Stretch fibers are normally additives,
# not the primary material label.
STRETCH_FIBERS = {
    "spandex",
    "elastane",
}


# If one main material reaches this percentage,
# use it instead of "blended".
DOMINANT_MATERIAL_THRESHOLD = 80

# =========================================================
# SLEEVE LENGTH RULES
# =========================================================

SLEEVE_LENGTH_KEYWORDS = {

    "sleeveless": [
        "sleeveless",
        "tank",
        "tank top",
        "spaghetti strap",
        "strapless",
        "cami",
        "camisole",
    ],

    "short": [
        "short sleeve",
        "short-sleeve",
        "cap sleeve",
    ],

    "elbow": [
        "elbow sleeve",
        "elbow-length sleeve",
        "half sleeve",
    ],

    "three_quarter": [
        "three-quarter sleeve",
        "3/4 sleeve",
        "three quarter sleeve",
    ],

    "long": [
        "long sleeve",
        "long-sleeve",
        "full sleeve",
    ],
}


# =========================================================
# NECKLINE RULES
# =========================================================

NECKLINE_KEYWORDS = {

    "round": [
        "round neck",
        "round neckline",
        "crew neck",
        "crew neckline",
    ],

    "v_neck": [
        "v-neck",
        "v neck",
        "v-neckline",
    ],

    "square": [
        "square neck",
        "square neckline",
    ],

    "boat": [
        "boat neck",
        "boat neckline",
        "bateau neck",
    ],

    "collared": [
        "collared",
        "collared neckline",
        "shirt collar",
        "polo neck",
        "polo collar",
    ],

    "turtleneck": [
        "turtleneck",
        "turtle neck",
        "mock neck",
        "mock-neck",
    ],

    "sweetheart": [
        "sweetheart",
        "sweetheart neckline",
    ],

    "halter": [
        "halter",
        "halter neck",
        "halter neckline",
    ],

    "strapless": [
        "strapless",
        "bandeau",
    ],
}

# =========================================================
# FIT RULES
# =========================================================

FIT_KEYWORDS = {

    "slim": [
        "slim fit",
        "slim-fit",
    ],

    "fitted": [
        "fitted",
        "fitted fit",
        "bodycon",
        "body-con",
        "form fitting",
        "form-fitting",
    ],

    "regular": [
        "regular fit",
    ],

    "relaxed": [
        "relaxed fit",
        "loose fit",
        "loose-fitting",
        "slouchy fit",
    ],

    "oversized": [
        "oversized",
        "oversize",
        "oversized fit",
    ],

    "straight": [
        "straight fit",
        "straight-fit",
        "straight leg",
        "straight-leg",
    ],
}

# =========================================================
# DESIGN DETAILS RULES
# =========================================================

DESIGN_DETAIL_KEYWORDS = {

    "asymmetric": [
        "asymmetric",
        "asymmetrical",
    ],

    "backless": [
        "backless",
        "open back",
        "open-back",
    ],

    "beaded": [
        "beaded",
        "bead detail",
    ],

    "bow": [
        "bow",
        "bow detail",
        "bow tie",
    ],

    "buttons": [
        "button detail",
        "buttoned",
        "button front",
        "button-front",
        "button-down",
        "button-up",
    ],

    "cutout": [
        "cutout",
        "cut out",
        "cold shoulder",
        "open shoulder",
    ],

    "embroidered": [
        "embroidered",
        "embroidery",
    ],

    "lace_detail": [
        "lace",
        "lace detail",
        "lace trim",
        "crochet lace",
    ],

    "pleated": [
        "pleated",
        "pleat",
    ],

    "ruffled": [
        "ruffled",
        "ruffle",
        "frill",
        "frilled",
    ],

    "sequined": [
        "sequin",
        "sequined",
        "sequinned",
    ],

    "slit": [
        "slit",
        "side slit",
        "front slit",
    ],

    "tie": [
        "tie detail",
        "tie neck",
        "back tie",
        "waist tie",
        "self tie",
        "self-tie",
    ],

    "zipper": [
        "zipper",
        "zip front",
        "zip-front",
        "half zip",
        "half-zip",
        "quarter zip",
        "quarter-zip",
    ],
}

# =========================================================
# STYLE TAG RULES
# =========================================================

STYLE_TAG_KEYWORDS = {

    "office": [
        "office",
        "workwear",
        "work wear",
        "workday",
    ],

    "business": [
        "business",
        "professional",
    ],

    "business_casual": [
        "business casual",
        "business-casual",
    ],

    "formal": [
        "formal",
        "dressy",
    ],

    "smart_casual": [
        "smart casual",
        "smart-casual",
    ],

    "casual": [
        "casual",
        "daytime",
        "daywear",
        "everyday",
    ],

    "minimal": [
        "minimal",
        "minimalist",
    ],

    "elegant": [
        "elegant",
        "polished",
        "refined",
        "chic",
    ],

    "classic": [
        "classic",
        "timeless",
    ],

    "feminine": [
        "feminine",
        "romantic",
    ],

    "modern": [
        "modern",
        "contemporary",
    ],
}