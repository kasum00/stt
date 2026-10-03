from typing import (
    Any,
    Mapping,
    Set,
)


class GarmentRoleResolver:
    """Resolve outfit roles without changing the garment taxonomy."""

    @staticmethod
    def roles_for_item(
        item: Mapping[str, Any],
    ) -> Set[str]:

        roles = set()

        category = item.get(
            "category"
        )

        subcategory = item.get(
            "subcategory"
        )

        if category:

            roles.add(
                str(
                    category
                ).casefold()
            )

        # Cardigan remains category=top in the model taxonomy, but can
        # function as an outer layer when building an outfit.
        if (
            str(
                subcategory
            ).casefold()
            == "cardigan"
        ):

            roles.add(
                "outerwear"
            )

        return roles


__all__ = [
    "GarmentRoleResolver",
]
