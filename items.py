from typing import NamedTuple

from BaseClasses import ItemClassification

from .core.data import WEAPON_MOD_COUNTS

BASE_ID = 77_700_000


class RACItemData(NamedTuple):
    code: int
    classification: ItemClassification


WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    "Lacerator":       "lacerator",
    "Concussion Gun":  "concussion_gun",
    "Acid Bomb Glove": "acid_bomb_glove",
    "Agents of Doom":  "agents_of_doom",
    "Bee Mine Glove":  "bee_mine_glove",
    "Static Barrier":  "static_barier",
    "Shock Rocket":    "shock_rocket",
    "Sniper Mine":     "sniper_mine",
    "Scorcher":        "scorchet",
    "Laser Tracer":    "laser_tracer",
    "Suck Cannon":     "suck_cannon",
    "Mootator":        "mootator",
    "RYNO":            "ryno",
}

GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    "Hypershot":      "hypershot",
    "Sprout-O-Matic": "sprout_o_matic",
    "Polarizer":      "polarizer",
    "PDA":            "pda",
    "Shrink Ray":     "shrink_ray",
    "Bolt Grabber":   "bolt_grabber",
    "Map-O-Matic":    "map_o_matic",
    "Box Breaker":    "box_breaker",
}

ARMOUR_DISPLAY_TO_INTERNAL: dict[str, tuple[str, int]] = {
    "Wildfire Chestplate":      ("wildfire",     0x01),
    "Wildfire Helmet":          ("wildfire",     0x02),
    "Wildfire Gloves":          ("wildfire",     0x04),
    "Wildfire Boots":           ("wildfire",     0x10),
    "Sludge Mk9 Chestplate":    ("sludge",       0x01),
    "Sludge Mk9 Helmet":        ("sludge",       0x02),
    "Sludge Mk9 Gloves":        ("sludge",       0x04),
    "Sludge Mk9 Boots":         ("sludge",       0x10),
    "Crystallix Chestplate":    ("crystallix",   0x01),
    "Crystallix Helmet":        ("crystallix",   0x02),
    "Crystallix Gloves":        ("crystallix",   0x04),
    "Crystallix Boots":         ("crystallix",   0x10),
    "Electroshock Chestplate":  ("electroshock", 0x01),
    "Electroshock Helmet":      ("electroshock", 0x02),
    "Electroshock Gloves":      ("electroshock", 0x04),
    "Electroshock Boots":       ("electroshock", 0x10),
    "Mega Bomb Chestplate":     ("mega_bomb",    0x01),
    "Mega Bomb Helmet":         ("mega_bomb",    0x02),
    "Mega Bomb Gloves":         ("mega_bomb",    0x04),
    "Mega Bomb Boots":          ("mega_bomb",    0x10),
    "Hyperborean Chestplate":   ("hyperborean",  0x01),
    "Hyperborean Helmet":       ("hyperborean",  0x02),
    "Hyperborean Gloves":       ("hyperborean",  0x04),
    "Hyperborean Boots":        ("hyperborean",  0x10),
    "Chameleon Chestplate":     ("chameleon",    0x01),
    "Chameleon Helmet":         ("chameleon",    0x02),
    "Chameleon Gloves":         ("chameleon",    0x04),
    "Chameleon Boots":          ("chameleon",    0x10),
}

_PROGRESSION_WEAPONS: frozenset[str] = frozenset({
    "Lacerator",
    "Concussion Gun",
    "Shock Rocket",
    "Sniper Mine",
    "Laser Tracer",
    "Scorcher",
    "RYNO",
    "Mootator",
})

WEAPON_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(
        BASE_ID + idx,
        ItemClassification.progression if name in _PROGRESSION_WEAPONS else ItemClassification.useful,
    )
    for idx, name in enumerate(WEAPON_DISPLAY_TO_INTERNAL, start=1)
}

WEAPON_PROGRESSIVE_STEPS: dict[str, int] = {
    display: 1 + WEAPON_MOD_COUNTS.get(internal, 0)
    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
}

WEAPON_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    f"{display} Progressive Weapon": RACItemData(BASE_ID + 350 + idx, ItemClassification.progression)
    for idx, display in enumerate(WEAPON_DISPLAY_TO_INTERNAL)
}


_PROGRESSION_GADGETS: frozenset[str] = frozenset({"Hypershot", "Sprout-O-Matic", "Shrink Ray", "Polarizer"})

GADGET_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(
        BASE_ID + 100 + idx,
        ItemClassification.progression if name in _PROGRESSION_GADGETS else ItemClassification.useful,
    )
    for idx, name in enumerate(GADGET_DISPLAY_TO_INTERNAL, start=1)
}

ARMOUR_SETS: list[tuple[str, str]] = [
    ("Wildfire",     "wildfire"),
    ("Sludge Mk9",   "sludge"),
    ("Crystallix",   "crystallix"),
    ("Electroshock", "electroshock"),
    ("Mega Bomb",    "mega_bomb"),
    ("Hyperborean",  "hyperborean"),
    ("Chameleon",    "chameleon"),
]

ARMOUR_SET_DISPLAY_TO_INTERNAL: dict[str, str] = dict(ARMOUR_SETS)

ARMOUR_PIECE_BITMASKS: tuple[int, ...] = (0x01, 0x02, 0x04, 0x10)


ARMOUR_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 200 + idx, ItemClassification.useful)
    for idx, name in enumerate(ARMOUR_DISPLAY_TO_INTERNAL, start=1)
}

ARMOUR_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    f"{display} Progressive Pickup": RACItemData(BASE_ID + 370 + idx, ItemClassification.useful)
    for idx, (display, _) in enumerate(ARMOUR_SETS)
}

FILLER_ITEM_TABLE: dict[str, RACItemData] = {
    "Bolts": RACItemData(BASE_ID + 400, ItemClassification.filler),
}

from .core.data.infobots import INFOBOT_ITEM_TO_PLANET

INFOBOT_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 500 + idx, ItemClassification.progression)
    for idx, name in enumerate(INFOBOT_ITEM_TO_PLANET, start=1)
}

ALL_ITEMS: dict[str, RACItemData] = {
    **WEAPON_ITEM_TABLE,
    **GADGET_ITEM_TABLE,
    **ARMOUR_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_ITEM_TABLE,
    **ARMOUR_PROGRESSIVE_ITEM_TABLE,
    **INFOBOT_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
}

ITEM_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_ITEMS.items()}
