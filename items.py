from typing import NamedTuple

from BaseClasses import ItemClassification

from .constants.items import RACSMITEM
from .core.data import WEAPON_MAX_LEVELS, WEAPON_MOD_COUNTS
from .core.data.infobots import INFOBOT_ITEM_TO_PLANET
from .core.traps import TRAP_DURATIONS

BASE_ID = 77_700_000


class RACItemData(NamedTuple):
    code: int
    classification: ItemClassification


WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    RACSMITEM.LACERATOR:       "lacerator",
    RACSMITEM.CONCUSSION_GUN:  "concussion_gun",
    RACSMITEM.ACID_BOMB_GLOVE: "acid_bomb_glove",
    RACSMITEM.AGENTS_OF_DOOM:  "agents_of_doom",
    RACSMITEM.BEE_MINE_GLOVE:  "bee_mine_glove",
    RACSMITEM.STATIC_BARRIER:  "static_barrier",
    RACSMITEM.SHOCK_ROCKET:    "shock_rocket",
    RACSMITEM.SNIPER_MINE:     "sniper_mine",
    RACSMITEM.SCORCHER:        "scorcher",
    RACSMITEM.LASER_TRACER:    "laser_tracer",
    RACSMITEM.SUCK_CANNON:     "suck_cannon",
    RACSMITEM.MOOTATOR:        "mootator",
    RACSMITEM.RYNO:            "ryno",
}

GADGET_DISPLAY_TO_INTERNAL: dict[str, str] = {
    RACSMITEM.HYPERSHOT:      "hypershot",
    RACSMITEM.SPROUT_O_MATIC: "sprout_o_matic",
    RACSMITEM.POLARIZER:      "polarizer",
    RACSMITEM.PDA:            "pda",
    RACSMITEM.SHRINK_RAY:     "shrink_ray",
    RACSMITEM.BOLT_GRABBER:   "bolt_grabber",
    RACSMITEM.MAP_O_MATIC:    "map_o_matic",
    RACSMITEM.BOX_BREAKER:    "box_breaker",
}

ARMOUR_DISPLAY_TO_INTERNAL: dict[str, tuple[str, int]] = {
    RACSMITEM.WILDFIRE_CHESTPLATE:     ("wildfire",     0x01),
    RACSMITEM.WILDFIRE_HELMET:         ("wildfire",     0x02),
    RACSMITEM.WILDFIRE_GLOVES:         ("wildfire",     0x04),
    RACSMITEM.WILDFIFE_BOOTS:          ("wildfire",     0x10),
    RACSMITEM.SLUDGE_MK9_CHESTPLATE:   ("sludge",       0x01),
    RACSMITEM.SLUDGE_MK9_HELMET:       ("sludge",       0x02),
    RACSMITEM.SLUDGE_MK9_GLOVES:       ("sludge",       0x04),
    RACSMITEM.SLUDGE_MK9_BOOTS:        ("sludge",       0x10),
    RACSMITEM.CRYSTALLIX_CHESTPLATE:   ("crystallix",   0x01),
    RACSMITEM.CRYSTALLIX_HELMET:       ("crystallix",   0x02),
    RACSMITEM.CRYSTALLIX_GLOVES:       ("crystallix",   0x04),
    RACSMITEM.CRYSTALLIX_BOOTS:        ("crystallix",   0x10),
    RACSMITEM.ELECTROSHOCK_CHESTPLATE: ("electroshock", 0x01),
    RACSMITEM.ELECTROSHOCK_HELMET:     ("electroshock", 0x02),
    RACSMITEM.ELECTROSHOCK_GLOVES:     ("electroshock", 0x04),
    RACSMITEM.ELECTROSHOCK_BOOTS:      ("electroshock", 0x10),
    RACSMITEM.MEGA_BOMB_CHESTPLATE:    ("mega_bomb",    0x01),
    RACSMITEM.MEGA_BOMB_HELMET:        ("mega_bomb",    0x02),
    RACSMITEM.MEGA_BOMB_GLOVES:        ("mega_bomb",    0x04),
    RACSMITEM.MEGA_BOMB_BOOTS:         ("mega_bomb",    0x10),
    RACSMITEM.HYPERBOREAN_CHESTPLATE:  ("hyperborean",  0x01),
    RACSMITEM.HYPERBOREAN_HELMET:      ("hyperborean",  0x02),
    RACSMITEM.HYPERBOREAN_GLOVES:      ("hyperborean",  0x04),
    RACSMITEM.HYPERBOREAN_BOOTS:       ("hyperborean",  0x10),
    RACSMITEM.CHAMELEON_CHESTPLATE:    ("chameleon",    0x01),
    RACSMITEM.CHAMELEON_HELMET:        ("chameleon",    0x02),
    RACSMITEM.CHAMELEON_GLOVES:        ("chameleon",    0x04),
    RACSMITEM.CHAMELEON_BOOTS:         ("chameleon",    0x10),
}

_PROGRESSION_WEAPONS: frozenset[str] = frozenset({
    RACSMITEM.LACERATOR,
    RACSMITEM.CONCUSSION_GUN,
    RACSMITEM.SHOCK_ROCKET,
    RACSMITEM.SNIPER_MINE,
    RACSMITEM.LASER_TRACER,
    RACSMITEM.SCORCHER,
    RACSMITEM.RYNO,
    RACSMITEM.MOOTATOR,
})

WEAPON_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(
        BASE_ID + idx,
        ItemClassification.progression if name in _PROGRESSION_WEAPONS else ItemClassification.useful,
    )
    for idx, name in enumerate(WEAPON_DISPLAY_TO_INTERNAL, start=1)
}

# Steps for the "Progressive {Weapon}" item: 1 copy unlocks the weapon, each
# subsequent copy grants the next level up.
WEAPON_PROGRESSIVE_STEPS: dict[str, int] = {
    display: 1 + max(0, WEAPON_MAX_LEVELS.get(internal, 1) - 1)
    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
}

PROGRESSIVE_WEAPON_NAME: dict[str, str] = {
    RACSMITEM.LACERATOR:       RACSMITEM.PROGRESSIVE_LACERATOR,
    RACSMITEM.CONCUSSION_GUN:  RACSMITEM.PROGRESSIVE_CONCUSSION_GUN,
    RACSMITEM.ACID_BOMB_GLOVE: RACSMITEM.PROGRESSIVE_ACID_BOMB_GLOVE,
    RACSMITEM.AGENTS_OF_DOOM:  RACSMITEM.PROGRESSIVE_AGENTS_OF_DOOM,
    RACSMITEM.BEE_MINE_GLOVE:  RACSMITEM.PROGRESSIVE_BEE_MINE_GLOVE,
    RACSMITEM.STATIC_BARRIER:  RACSMITEM.PROGRESSIVE_STATIC_BARRIER,
    RACSMITEM.SHOCK_ROCKET:    RACSMITEM.PROGRESSIVE_SHOCK_ROCKET,
    RACSMITEM.SNIPER_MINE:     RACSMITEM.PROGRESSIVE_SNIPER_MINE,
    RACSMITEM.SCORCHER:        RACSMITEM.PROGRESSIVE_SCORCHER,
    RACSMITEM.LASER_TRACER:    RACSMITEM.PROGRESSIVE_LASER_TRACER,
    RACSMITEM.SUCK_CANNON:     RACSMITEM.PROGRESSIVE_SUCK_CANNON,
    RACSMITEM.MOOTATOR:        RACSMITEM.PROGRESSIVE_MOOTATOR,
    RACSMITEM.RYNO:            RACSMITEM.PROGRESSIVE_RYNO,
}

WEAPON_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_WEAPON_NAME[display]: RACItemData(BASE_ID + 350 + idx, ItemClassification.progression)
    for idx, display in enumerate(WEAPON_DISPLAY_TO_INTERNAL)
}

# Weapons with at least one mod slot (suck_cannon/mootator/ryno have none).
_WEAPONS_WITH_MODS: list[str] = [
    display for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
    if WEAPON_MOD_COUNTS.get(internal, 0) > 0
]

PROGRESSIVE_MOD_NAME: dict[str, str] = {
    RACSMITEM.LACERATOR:       RACSMITEM.PROGRESSIVE_LACERATOR_MOD,
    RACSMITEM.CONCUSSION_GUN:  RACSMITEM.PROGRESSIVE_CONCUSSION_GUN_MOD,
    RACSMITEM.ACID_BOMB_GLOVE: RACSMITEM.PROGRESSIVE_ACID_BOMB_GLOVE_MOD,
    RACSMITEM.AGENTS_OF_DOOM:  RACSMITEM.PROGRESSIVE_AGENTS_OF_DOOM_MOD,
    RACSMITEM.BEE_MINE_GLOVE:  RACSMITEM.PROGRESSIVE_BEE_MINE_GLOVE_MOD,
    RACSMITEM.STATIC_BARRIER:  RACSMITEM.PROGRESSIVE_STATIC_BARRIER_MOD,
    RACSMITEM.SHOCK_ROCKET:    RACSMITEM.PROGRESSIVE_SHOCK_ROCKET_MOD,
    RACSMITEM.SNIPER_MINE:     RACSMITEM.PROGRESSIVE_SNIPER_MINE_MOD,
    RACSMITEM.SCORCHER:        RACSMITEM.PROGRESSIVE_SCORCHER_MOD,
    RACSMITEM.LASER_TRACER:    RACSMITEM.PROGRESSIVE_LASER_TRACER_MOD,
}

# One "Progressive {Weapon} Mod" item per mod slot — each additional copy
# unlocks the next mod slot, independent of the weapon's unlock/level item.
WEAPON_PROGRESSIVE_MOD_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_MOD_NAME[display]: RACItemData(BASE_ID + 380 + idx, ItemClassification.useful)
    for idx, display in enumerate(_WEAPONS_WITH_MODS)
}

# Individual numbered mod items used when Progressive Mods is off — one item
# per mod slot, each independently grants that specific slot.
WEAPON_MOD_ITEM_TABLE: dict[str, RACItemData] = {
    f"{display} Mod {i}": RACItemData(BASE_ID + 700 + idx, ItemClassification.useful)
    for idx, (display, i) in enumerate(
        (display, i)
        for display in _WEAPONS_WITH_MODS
        for i in range(1, WEAPON_MOD_COUNTS.get(WEAPON_DISPLAY_TO_INTERNAL[display], 0) + 1)
    )
}

# "{Weapon} Mod {i}" item name -> (weapon display name, 1-indexed slot number)
WEAPON_MOD_NAME_TO_SLOT: dict[str, tuple[str, int]] = {
    name: (display, i)
    for display in _WEAPONS_WITH_MODS
    for i in range(1, WEAPON_MOD_COUNTS.get(WEAPON_DISPLAY_TO_INTERNAL[display], 0) + 1)
    for name in (f"{display} Mod {i}",)
}


_PROGRESSION_GADGETS: frozenset[str] = frozenset({
    RACSMITEM.HYPERSHOT, RACSMITEM.SPROUT_O_MATIC, RACSMITEM.SHRINK_RAY, RACSMITEM.POLARIZER,
})

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

PROGRESSIVE_ARMOUR_NAME: dict[str, str] = {
    "Wildfire":     RACSMITEM.PROGRESSIVE_WILDFIRE,
    "Sludge Mk9":   RACSMITEM.PROGRESSIVE_SLUDGE_MK9,
    "Crystallix":   RACSMITEM.PROGRESSIVE_CRYSTALLIX,
    "Electroshock": RACSMITEM.PROGRESSIVE_ELECTROSHOCK,
    "Mega Bomb":    RACSMITEM.PROGRESSIVE_MEGA_BOMB,
    "Hyperborean":  RACSMITEM.PROGRESSIVE_HYPERBOREAN,
    "Chameleon":    RACSMITEM.PROGRESSIVE_CHAMELEON,
}

ARMOUR_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    PROGRESSIVE_ARMOUR_NAME[display]: RACItemData(BASE_ID + 370 + idx, ItemClassification.useful)
    for idx, (display, _) in enumerate(ARMOUR_SETS)
}

FILLER_ITEM_TABLE: dict[str, RACItemData] = {
    RACSMITEM.BOLTS: RACItemData(BASE_ID + 400, ItemClassification.filler),
}

INFOBOT_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 500 + idx, ItemClassification.progression)
    for idx, name in enumerate(INFOBOT_ITEM_TO_PLANET, start=1)
}

TRAP_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 600 + idx, ItemClassification.trap)
    for idx, name in enumerate(TRAP_DURATIONS, start=1)
}

ALL_ITEMS: dict[str, RACItemData] = {
    **WEAPON_ITEM_TABLE,
    **GADGET_ITEM_TABLE,
    **ARMOUR_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_MOD_ITEM_TABLE,
    **WEAPON_MOD_ITEM_TABLE,
    **ARMOUR_PROGRESSIVE_ITEM_TABLE,
    **INFOBOT_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
    **TRAP_ITEM_TABLE,
}

ITEM_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_ITEMS.items()}
