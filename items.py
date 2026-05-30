"""AP item definitions for Ratchet & Clank: Size Matters.

Weapon and gadget internal keys are taken verbatim from
size_matters/data/weapons.py (WEAPON_ORDER / GADGET_ORDER).
Display names used in the AP item pool are mapped here.
"""
from typing import NamedTuple

from BaseClasses import ItemClassification

from .core.data import WEAPON_MOD_COUNTS

BASE_ID = 77_700_000


class RACItemData(NamedTuple):
    code: int
    classification: ItemClassification


# ── Display name ↔ internal key mappings ──────────────────────────────────────
# Internal keys match WEAPON_ORDER / GADGET_ORDER in size_matters/data/weapons.py.
# The client uses these to write weapon/gadget unlock flags via PINE.

WEAPON_DISPLAY_TO_INTERNAL: dict[str, str] = {
    "Lacerator":       "lacerator",
    "Concussion Gun":  "concussion_gun",
    "Acid Bomb Glove": "acid_bomb_glove",
    "Agents of Doom":  "agents_of_doom",
    "Bee Mine Glove":  "bee_mine_glove",
    "Static Barrier":  "static_barier",   # intentional: matches game's internal spelling
    "Shock Rocket":    "shock_rocket",
    "Sniper Mine":     "sniper_mine",
    "Scorcher":        "scorchet",         # intentional: matches game's internal spelling
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

# Armour display name → (internal set_key, piece_bitmask)
# set_key matches ArmourAddresses._SET_OFFSETS; piece matches ArmourPiece values.
ARMOUR_DISPLAY_TO_INTERNAL: dict[str, tuple[str, int]] = {
    # Wildfire
    "Wildfire Chestplate":      ("wildfire",     0x01),
    "Wildfire Helmet":          ("wildfire",     0x02),
    "Wildfire Gloves":          ("wildfire",     0x04),
    "Wildfire Boots":           ("wildfire",     0x10),
    # Sludge Mk9
    "Sludge Mk9 Chestplate":    ("sludge",       0x01),
    "Sludge Mk9 Helmet":        ("sludge",       0x02),
    "Sludge Mk9 Gloves":        ("sludge",       0x04),
    "Sludge Mk9 Boots":         ("sludge",       0x10),
    # Crystallix
    "Crystallix Chestplate":    ("crystallix",   0x01),
    "Crystallix Helmet":        ("crystallix",   0x02),
    "Crystallix Gloves":        ("crystallix",   0x04),
    "Crystallix Boots":         ("crystallix",   0x10),
    # Electroshock
    "Electroshock Chestplate":  ("electroshock", 0x01),
    "Electroshock Helmet":      ("electroshock", 0x02),
    "Electroshock Gloves":      ("electroshock", 0x04),
    "Electroshock Boots":       ("electroshock", 0x10),
    # Mega Bomb
    "Mega Bomb Chestplate":     ("mega_bomb",    0x01),
    "Mega Bomb Helmet":         ("mega_bomb",    0x02),
    "Mega Bomb Gloves":         ("mega_bomb",    0x04),
    "Mega Bomb Boots":          ("mega_bomb",    0x10),
    # Hyperborean
    "Hyperborean Chestplate":   ("hyperborean",  0x01),
    "Hyperborean Helmet":       ("hyperborean",  0x02),
    "Hyperborean Gloves":       ("hyperborean",  0x04),
    "Hyperborean Boots":        ("hyperborean",  0x10),
    # Chameleon
    "Chameleon Chestplate":     ("chameleon",    0x01),
    "Chameleon Helmet":         ("chameleon",    0x02),
    "Chameleon Gloves":         ("chameleon",    0x04),
    "Chameleon Boots":          ("chameleon",    0x10),
}

# ── Weapon items (1-13) ───────────────────────────────────────────────────────
# Projectile weapons gate the Ryllus entrance — any one of them is required.
# They must be progression so the fill algorithm treats them as key items.

_PROGRESSION_WEAPONS: frozenset[str] = frozenset({
    # Gate Ryllus — any one required
    "Lacerator",
    "Concussion Gun",
    "Shock Rocket",
    "Sniper Mine",
    "Laser Tracer",
    "Scorcher",
    "RYNO",
    # Required for Skill Point Do Cows Get Crabby
    "Mootator",
})

WEAPON_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(
        BASE_ID + idx,
        ItemClassification.progression if name in _PROGRESSION_WEAPONS else ItemClassification.useful,
    )
    for idx, name in enumerate(WEAPON_DISPLAY_TO_INTERNAL, start=1)
}

# ── Per-weapon progressive items (350-362) ────────────────────────────────────
# Each weapon produces (1 + mod_count) progressive items:
#   receive 1 → weapon unlocked; receive 2 → mod 1; receive 3 → mod 2; etc.

WEAPON_PROGRESSIVE_STEPS: dict[str, int] = {
    display: 1 + WEAPON_MOD_COUNTS.get(internal, 0)
    for display, internal in WEAPON_DISPLAY_TO_INTERNAL.items()
}

WEAPON_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    f"{display} Progressive Weapon": RACItemData(BASE_ID + 350 + idx, ItemClassification.progression)
    for idx, display in enumerate(WEAPON_DISPLAY_TO_INTERNAL)
}

# ── Gadget items (101-108) ────────────────────────────────────────────────────
# Gadgets required to unlock new regions or location tiers are progression.

_PROGRESSION_GADGETS: frozenset[str] = frozenset({"Hypershot", "Sprout-O-Matic", "Shrink Ray", "Polarizer"})

GADGET_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(
        BASE_ID + 100 + idx,
        ItemClassification.progression if name in _PROGRESSION_GADGETS else ItemClassification.useful,
    )
    for idx, name in enumerate(GADGET_DISPLAY_TO_INTERNAL, start=1)
}

# ── Armour sets and piece order ───────────────────────────────────────────────

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

# Bitmasks in unlock order: chestplate, helmet, gloves, boots
ARMOUR_PIECE_BITMASKS: tuple[int, ...] = (0x01, 0x02, 0x04, 0x10)

# ── Armour items (201-220) ────────────────────────────────────────────────────

ARMOUR_ITEM_TABLE: dict[str, RACItemData] = {
    name: RACItemData(BASE_ID + 200 + idx, ItemClassification.useful)
    for idx, name in enumerate(ARMOUR_DISPLAY_TO_INTERNAL, start=1)
}

# ── Per-armour-set progressive items (370-374) ────────────────────────────────
# Each armour set produces 4 progressive items, one per piece in ARMOUR_PIECE_BITMASKS order.

ARMOUR_PROGRESSIVE_ITEM_TABLE: dict[str, RACItemData] = {
    f"{display} Progressive Pickup": RACItemData(BASE_ID + 370 + idx, ItemClassification.useful)
    for idx, (display, _) in enumerate(ARMOUR_SETS)
}

# ── Filler (400) ──────────────────────────────────────────────────────────────

FILLER_ITEM_TABLE: dict[str, RACItemData] = {
    "Bolts": RACItemData(BASE_ID + 400, ItemClassification.filler),
}

# ── Combined lookups ──────────────────────────────────────────────────────────

ALL_ITEMS: dict[str, RACItemData] = {
    **WEAPON_ITEM_TABLE,
    **GADGET_ITEM_TABLE,
    **ARMOUR_ITEM_TABLE,
    **WEAPON_PROGRESSIVE_ITEM_TABLE,
    **ARMOUR_PROGRESSIVE_ITEM_TABLE,
    **FILLER_ITEM_TABLE,
}

ITEM_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_ITEMS.items()}
