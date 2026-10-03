from itertools import (
    product,
)

from herstyle_ai.recommendation.garment_role_resolver import (
    GarmentRoleResolver,
)

from herstyle_ai.styling.structure_analyzer import (
    OutfitStructureAnalyzer,
)


# =========================================================
# COMPATIBILITY SLOTS
# =========================================================

SLOTS = [
    "top",
    "bottom",
    "dress",
    "outerwear",
    "shoes",
]


# =========================================================
# ALLOWED OUTFIT STRUCTURES
#
# Must match structures used in V1 training.
# =========================================================

OUTFIT_STRUCTURES = [

    (
        "top",
        "bottom",
    ),

    (
        "top",
        "bottom",
        "shoes",
    ),

    (
        "top",
        "bottom",
        "outerwear",
    ),

    (
        "top",
        "bottom",
        "outerwear",
        "shoes",
    ),

    (
        "dress",
        "shoes",
    ),

    (
        "dress",
        "outerwear",
    ),

    (
        "dress",
        "outerwear",
        "shoes",
    ),
]


# =========================================================
# SLOT MAPPING
# =========================================================

def wardrobe_item_to_slot(
    item,
    role_resolver=None,
):

    resolver = (
        role_resolver
        or GarmentRoleResolver()
    )

    roles = resolver.roles_for_item(
        item
    )

    for slot in SLOTS:

        if slot in roles:

            return slot

    return None


# =========================================================
# GENERATOR
# =========================================================

class OutfitCandidateGenerator:

    def __init__(
        self,
        max_candidates=5000,
        role_resolver=None,
        structure_analyzer=None,
    ):

        self.max_candidates = int(
            max_candidates
        )

        self.role_resolver = (
            role_resolver
            or GarmentRoleResolver()
        )

        self.structure_analyzer = (
            structure_analyzer
            or OutfitStructureAnalyzer()
        )

    # =====================================================
    # GROUP ITEMS BY SLOT
    # =====================================================

    def group_by_slot(
        self,
        wardrobe_items,
    ):

        groups = {

            slot: []

            for slot in SLOTS
        }

        for item in wardrobe_items:

            category = item.get(
                "category"
            )

            office_relevance = item.get(
                "office_relevance"
            )

            # =====================================
            # OFFICE POLICY
            # =====================================

            office_relevance = item.get(
                "office_relevance"
            )

            office_relevance_reasons = (
                item.get(
                    "office_relevance_reasons",
                    [],
                )
                or []
            )

            # -------------------------------------
            # Standard office-approved item
            # -------------------------------------

            if office_relevance == "positive":

                pass

            # -------------------------------------
            # Shoes may be REVIEW because their
            # subcategory belongs to the extended
            # office / business-casual group.
            #
            # Examples:
            # sneakers, boots, sandals, other_shoes
            # -------------------------------------

            elif (
                category == "shoes"
                and
                office_relevance == "review"
                and
                any(
                    reason.startswith(
                        "extended_subcategory:"
                    )
                    for reason
                    in office_relevance_reasons
                )
            ):

                pass

            # -------------------------------------
            # Everything else is excluded
            # -------------------------------------

            else:

                continue

            # =====================================
            # MAP TO COMPATIBILITY SLOT
            # =====================================

            roles = (
                self.role_resolver
                .roles_for_item(
                    item
                )
            )

            for slot in SLOTS:

                if slot not in roles:

                    continue

                groups[
                    slot
                ].append(
                    item
                )

        return groups

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(
        self,
        wardrobe_items,
    ):

        groups = self.group_by_slot(
            wardrobe_items
        )

        candidates = []

        for structure in OUTFIT_STRUCTURES:

            # All slots required by this structure
            # must contain at least one item.
            if any(
                len(
                    groups[
                        slot
                    ]
                )
                == 0

                for slot in structure
            ):

                continue

            slot_lists = [

                groups[
                    slot
                ]

                for slot in structure
            ]

            for combination in product(
                *slot_lists
            ):

                selected_items = list(
                    combination
                )

                item_keys = [
                    (
                        item.get(
                            "item_id"
                        )
                        if item.get(
                            "item_id"
                        ) is not None
                        else id(
                            item
                        )
                    )
                    for item in selected_items
                ]

                # A cardigan can be valid for both top and outerwear.
                # Never use that same physical item twice.
                if len(
                    item_keys
                ) != len(
                    set(
                        item_keys
                    )
                ):

                    continue

                items = {

                    slot:
                        item

                    for slot, item
                    in zip(
                        structure,
                        combination,
                    )
                }

                candidate = {

                    "structure":
                        "+".join(
                            structure
                        ),

                    "slots":
                        list(
                            structure
                        ),

                    "items":
                        items,
                }

                structure_metadata = (
                    self.structure_analyzer
                    .analyze(
                        candidate
                    )
                    .to_dict()
                )

                candidate[
                    "structure_analysis"
                ] = structure_metadata

                candidates.append(
                    candidate
                )

                if (
                    len(
                        candidates
                    )
                    >= self.max_candidates
                ):

                    return candidates

        return candidates
