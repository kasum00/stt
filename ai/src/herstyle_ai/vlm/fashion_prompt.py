# =========================================================
# CATEGORY
# =========================================================

CATEGORY = [
    "top",
    "bottom",
    "dress",
    "outerwear",
    "shoes",
    "accessory",
]


# =========================================================
# SUBCATEGORY BY CATEGORY
# =========================================================

SUBCATEGORY_BY_CATEGORY = {

    "top": [
        "blouse",
        "shirt",
        "t_shirt",
        "polo",
        "sweater",
        "cardigan",
        "vest",
        "other_top",
    ],

    "bottom": [
        "trousers",
        "jeans",
        "skirt",
        "shorts",
        "other_bottom",
    ],

    "dress": [
        "sheath_dress",
        "shirt_dress",
        "wrap_dress",
        "a_line_dress",
        "midi_dress",
        "other_dress",
    ],

    "outerwear": [
        "blazer",
        "jacket",
        "coat",
        "trench_coat",
        "other_outerwear",
    ],

    "shoes": [
        "heels",
        "flats",
        "loafers",
        "sneakers",
        "boots",
        "sandals",
        "other_shoes",
    ],

    "accessory": [
        "bag",
        "handbag",
        "tote_bag",
        "shoulder_bag",
        "crossbody_bag",
        "clutch",
        "backpack",
        "other_accessory",
    ],
}


SUBCATEGORY = [

    subcategory

    for category_items
    in SUBCATEGORY_BY_CATEGORY.values()

    for subcategory
    in category_items
]


# =========================================================
# COLOR
# =========================================================

COLOR = [
    "black",
    "white",
    "gray",
    "beige",
    "brown",
    "blue",
    "navy",
    "red",
    "pink",
    "purple",
    "green",
    "yellow",
    "orange",
    "metallic",
    "multicolor",
    "other",
]


# =========================================================
# MATERIAL
# =========================================================

MATERIAL = [
    "cotton",
    "polyester",
    "viscose_rayon",
    "wool",
    "linen",
    "silk",
    "denim",
    "leather",
    "synthetic",
    "blended",
    "other",
]


# =========================================================
# PATTERN
# =========================================================

PATTERN = [
    "solid",
    "striped",
    "checked",
    "plaid",
    "floral",
    "polka_dot",
    "geometric",
    "animal_print",
    "abstract",
    "graphic",
    "other",
]


# =========================================================
# SLEEVE LENGTH
# =========================================================

SLEEVE_LENGTH = [
    "sleeveless",
    "short",
    "elbow",
    "three_quarter",
    "long",
    "other",
]


# =========================================================
# NECKLINE
# =========================================================

NECKLINE = [
    "round",
    "v_neck",
    "square",
    "boat",
    "collared",
    "turtleneck",
    "sweetheart",
    "halter",
    "strapless",
    "other",
]


# =========================================================
# FIT
# =========================================================

FIT = [
    "slim",
    "regular",
    "relaxed",
    "oversized",
    "fitted",
    "straight",
    "other",
]


# =========================================================
# DESIGN DETAILS
# =========================================================

DESIGN_DETAILS = [
    "asymmetric",
    "backless",
    "beaded",
    "bow",
    "buttons",
    "cutout",
    "embroidered",
    "lace_detail",
    "pleated",
    "ruffled",
    "sequined",
    "slit",
    "tie",
    "zipper",
]


# =========================================================
# PROMPT
# =========================================================

def build_fashion_prompt():

    return f"""
You are a fashion garment attribute recognition system.

Analyze ONLY the primary fashion item visible in the image.

The item may be:
- top
- bottom
- dress
- outerwear
- shoes
- accessory (including handbags and other bags)

Return exactly one JSON object.
Do not write markdown.
Do not explain your reasoning.
Do not invent labels outside the allowed values.

Allowed taxonomy:

category:
{CATEGORY}

subcategory by category:
{SUBCATEGORY_BY_CATEGORY}

color:
{COLOR}

material:
{MATERIAL}

pattern:
{PATTERN}

sleeve_length:
{SLEEVE_LENGTH}

neckline:
{NECKLINE}

fit:
{FIT}

design_details:
{DESIGN_DETAILS}

Rules:

1. category, subcategory, color, pattern, sleeve_length,
   neckline and fit must use only the allowed labels.

2. category and subcategory must be hierarchically consistent.

3. If an attribute cannot be reliably determined from the image,
   return null.

4. Material is especially uncertain from appearance alone.
   Return null unless there is strong visual evidence.

5. design_details must be a JSON list.
   Use [] when no listed detail is clearly visible.

6. Do not infer material from color or garment category.

7. Ignore brand text, model name, background and packaging.

8. Always prefer the most specific visible subcategory.

9. Use an other_* subcategory only when none of the more
   specific subcategories reasonably describe the item.

10. Examples:
    - visible blouse -> blouse, not other_top
    - visible polo -> polo, not other_top
    - visible jeans -> jeans, not other_bottom
    - visible blazer -> blazer, not other_outerwear
    - visible sneakers -> sneakers, not other_shoes
    - visible loafers -> loafers, not other_shoes
    - visible handbag -> category accessory, subcategory handbag
    - visible tote bag -> category accessory, subcategory tote_bag
    - visible shoulder or crossbody bag -> category accessory, the matching bag subcategory
    - visible bag with uncertain construction -> category accessory, subcategory bag

11. For shoes:
    - heels -> clearly elevated heel
    - flats -> flat women's shoes without loafer structure
    - loafers -> slip-on loafer/moccasin structure
    - sneakers -> athletic/casual sneaker structure
    - boots -> footwear extending above the ankle
    - sandals -> open footwear with straps
    - other_shoes -> only when none of the above apply

12. Attributes that are not applicable should be null.

Examples:
- shoes normally have sleeve_length = null
- shoes normally have neckline = null
- shoes normally have fit = null
- bottoms normally have sleeve_length = null
- bottoms normally have neckline = null
- accessories normally have sleeve_length = null, neckline = null and fit = null

Return this exact schema:

{{
  "category": null,
  "subcategory": null,
  "color": null,
  "material": null,
  "pattern": null,
  "sleeve_length": null,
  "neckline": null,
  "fit": null,
  "design_details": []
}}
""".strip()
