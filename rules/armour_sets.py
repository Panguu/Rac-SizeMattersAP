from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_armour_piece

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


_ARMOUR_SET_RULES: dict[str, list[tuple[str, str, int]]] = {
    "Equip Wildfire Armour Set": [
        ("Wildfire", "Chestplate", 1), ("Wildfire", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Wildfire", "Boots", 4),
    ],
    "Equip Wildburst Armour Set": [
        ("Wildfire", "Chestplate", 1), ("Sludge Mk9", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Wildfire", "Boots", 4),
    ],
    "Equip Sludge Mk9 Armour Set": [
        ("Sludge Mk9", "Chestplate", 1), ("Sludge Mk9", "Helmet", 2),
        ("Sludge Mk9", "Gloves", 3), ("Sludge Mk9", "Boots", 4),
    ],
    "Equip Crystallix Armour Set": [
        ("Crystallix", "Chestplate", 1), ("Crystallix", "Helmet", 2),
        ("Crystallix", "Gloves", 3), ("Crystallix", "Boots", 4),
    ],
    "Equip Triple Wave Armour Set": [
        ("Wildfire", "Helmet", 2), ("Electroshock", "Chestplate", 1),
        ("Sludge Mk9", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Shock Crystal Armour Set": [
        ("Electroshock", "Helmet", 2), ("Crystallix", "Chestplate", 1),
        ("Crystallix", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Electroshock Armour Set": [
        ("Electroshock", "Chestplate", 1), ("Electroshock", "Helmet", 2),
        ("Electroshock", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Mega Bomb Armour Set": [
        ("Mega Bomb", "Chestplate", 1), ("Mega Bomb", "Helmet", 2),
        ("Mega Bomb", "Gloves", 3), ("Mega Bomb", "Boots", 4),
    ],
    "Equip Fire-Bomb Armour Set": [
        ("Mega Bomb", "Chestplate", 1), ("Mega Bomb", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Mega Bomb", "Boots", 4),
    ],
    "Equip Hyperborean Armour Set": [
        ("Hyperborean", "Chestplate", 1), ("Hyperborean", "Helmet", 2),
        ("Hyperborean", "Gloves", 3), ("Hyperborean", "Boots", 4),
    ],
    "Equip Ice II Armour Set": [
        ("Hyperborean", "Chestplate", 1), ("Crystallix", "Helmet", 2),
        ("Hyperborean", "Gloves", 3), ("Hyperborean", "Boots", 4),
    ],
    "Equip Chameleon Armour Set": [
        ("Chameleon", "Chestplate", 1), ("Chameleon", "Helmet", 2),
        ("Chameleon", "Gloves", 3), ("Chameleon", "Boots", 4),
    ],
    "Equip Stalker Armour Set": [
        ("Wildfire", "Helmet", 2), ("Chameleon", "Chestplate", 1),
        ("Sludge Mk9", "Gloves", 3), ("Chameleon", "Boots", 4),
    ],
}


def set_armour_set_rules(world: RACSizeMatterWorld) -> None:
    if not world.options.armour_set_checks:
        return

    player = world.player
    mw = world.multiworld

    def _pieces_rule(reqs):
        return lambda state: all(
            has_armour_piece(state, player, sd, pn, pi)
            for sd, pn, pi in reqs
        )

    for loc_name, reqs in _ARMOUR_SET_RULES.items():
        mw.get_location(loc_name, player).access_rule = _pieces_rule(reqs)
