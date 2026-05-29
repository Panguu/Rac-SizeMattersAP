"""AP location definitions for Ratchet & Clank: Size Matters.

All names are sourced directly from the game data files in size_matters/data/
to guarantee consistency between the AP world and the client's detection logic.
"""
from typing import Dict, NamedTuple

# Data sources — standalone files with no broken imports
from .size_matters.data.titanium_bolts import TITANIUM_BOLTS
from .size_matters.data.skill_points import SKILL_POINTS
from .size_matters.data.armour_pickups import ARMOUR_PICKUPS
from .items import WEAPON_DISPLAY_TO_INTERNAL, GADGET_DISPLAY_TO_INTERNAL

BASE_ID = 77_700_000




class RACLocationData(NamedTuple):
    code: int
    region: str


# ── Titanium Bolt locations (1001–1020) ───────────────────────────────────────
# Region and unique index sourced from size_matters/data/titanium_bolts.py.
# Client detection uses (planet_id, delta) via BOLT_BY_PLANET_AND_DELTA.

TITANIUM_BOLT_LOCATIONS: Dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1000 + idx, bolt.region)
    for idx, (name, bolt) in enumerate(TITANIUM_BOLTS.items(), start=1)
}

# ── Armour pickup locations (1101–1120) ───────────────────────────────────────
# Names sourced from size_matters/data/armour_pickups.py.
# Client detection: monitor each armour set bitmask at ARMOUR_BASE + set_offset
# for new bits; look up (set_key, new_bit) in ARMOUR_FLAG_TO_LOCATION.

ARMOUR_PICKUP_LOCATIONS: Dict[str, RACLocationData] = {
    ap.name: RACLocationData(BASE_ID + 1100 + idx, ap.planet)
    for idx, ap in enumerate(ARMOUR_PICKUPS, start=1)
}

# ── Boss location (1200) ──────────────────────────────────────────────────────
# Checking "Defeat Otto Destruct" also triggers the victory event in the client.

BOSS_LOCATIONS: Dict[str, RACLocationData] = {
    "Defeat Otto Destruct": RACLocationData(BASE_ID + 1200, "Quodrona"),
}

# ── Skill point locations (1301–1325) ─────────────────────────────────────────
# Names sourced from size_matters/data/skill_points.py (LOCATION_SKILL_POINTS keys).
# Client detection: read int64 at SKILL_POINT_ADDRESS, compare new_bits & ~old_bits.

SKILL_POINT_LOCATIONS: Dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1300 + idx, sp.region)
    for idx, (name, sp) in enumerate(SKILL_POINTS.items(), start=1)
}

# ── Vendor purchase locations (2001–2012 weapons, 2101 gadgets) ───────────────
# Maps each purchasable weapon to the planet where its vendor slot first appears.
# RYNO is not vendor-sold and is excluded. Hypershot is a gadget sold at Pokitaru.

VENDOR_WEAPON_PLANET: Dict[str, str] = {
    "Lacerator":       "Pokitaru",
    "Acid Bomb Glove": "Pokitaru",
    "Concussion Gun":  "Pokitaru",
    "Agents of Doom":  "Ryllus",
    "Scorcher":        "Kalidon",
    "Suck Cannon":     "Dreamtime",
    "Bee Mine Glove":  "Outpost Omega",
    "Sniper Mine":     "Challax",
    "Mootator":        "Dayni Moon",
    "Shock Rocket":    "Dayni Moon",
    "Static Barrier":  "Inside Clank",
    "Laser Tracer":    "Quodrona",
}

VENDOR_GADGET_PLANET: Dict[str, str] = {
    "Hypershot": "Pokitaru",
}

WEAPON_VENDOR_LOCATIONS: Dict[str, RACLocationData] = {
    f"Purchase {name}": RACLocationData(BASE_ID + 2000 + idx, planet)
    for idx, (name, planet) in enumerate(VENDOR_WEAPON_PLANET.items(), start=1)
}

GADGET_VENDOR_LOCATIONS: Dict[str, RACLocationData] = {
    f"Purchase {name}": RACLocationData(BASE_ID + 2100 + idx, planet)
    for idx, (name, planet) in enumerate(VENDOR_GADGET_PLANET.items(), start=1)
}

# ── Weapon mod vendor locations (2201+) ──────────────────────────────────────
# Mods marked (CM) in the source data are not AP locations and are excluded.
# Entries without a known "first available" planet are listed as TODO comments.

VENDOR_WEAPON_MOD_PLANET: Dict[tuple, str] = {
    ("Lacerator",       "Lock On Mod"):       "Kalidon",
    ("Lacerator",       "Double Barrel Mod"): "Challax",
    ("Acid Bomb Glove", "Acid Burn Mod"):     "Challax",
    ("Acid Bomb Glove", "Epoxy Mod"):         "Challax",
    ("Concussion Gun",  "Split Barrel Mod"):  "Kalidon",
    ("Concussion Gun",  "Lock On Mod"):       "Challax",
    ("Concussion Gun",  "Charge Up Mod"):     "Challax",
    ("Agents of Doom",  "Launcher Mod"):      "Quodrona",
    ("Scorcher",        "Spitfire Mod"):      "Quodrona",
    ("Bee Mine Glove",  "Worker Mod"):        "Challax",
    ("Sniper Mine",     "Split Beam Mod"):    "Quodrona",
    ("Shock Rocket",    "Lock On Mod"):       "Quodrona",
    ("Shock Rocket",    "After Shock Mod"):   "Quodrona",
}

WEAPON_MOD_VENDOR_LOCATIONS: Dict[str, RACLocationData] = {
    f"Purchase {weapon} {mod}": RACLocationData(BASE_ID + 2200 + idx, planet)
    for idx, ((weapon, mod), planet) in enumerate(VENDOR_WEAPON_MOD_PLANET.items(), start=1)
}

# ── Armour set check locations (1501–1505) ───────────────────────────────────
# Triggered when the player equips a complete armour set and closes the menu.
# Region is Pokitaru — equipping can happen anywhere, so the first accessible
# region is used; progression rules require owning all four pieces.

from .size_matters.data.armour_set_checks import ARMOUR_SET_CHECKS

ARMOUR_SET_CHECK_LOCATIONS: Dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1500 + idx, "Pokitaru")
    for idx, name in enumerate(ARMOUR_SET_CHECKS, start=1)
}

# ── Gadget pickup locations (1401+) ──────────────────────────────────────────
# World-space gadget pickups detected via cutscene address transitions.

GADGET_PICKUP_LOCATIONS: Dict[str, RACLocationData] = {
    "Ryllus Sprout-O-Matic": RACLocationData(BASE_ID + 1401, "Ryllus"),
}

# ── Combined lookup ───────────────────────────────────────────────────────────

ALL_LOCATIONS: Dict[str, RACLocationData] = {
    **TITANIUM_BOLT_LOCATIONS,
    **ARMOUR_PICKUP_LOCATIONS,
    **BOSS_LOCATIONS,
    **SKILL_POINT_LOCATIONS,
    **GADGET_PICKUP_LOCATIONS,
    **WEAPON_VENDOR_LOCATIONS,
    **GADGET_VENDOR_LOCATIONS,
    **WEAPON_MOD_VENDOR_LOCATIONS,
    **ARMOUR_SET_CHECK_LOCATIONS,
}

LOCATION_ID_TO_NAME: Dict[int, str] = {data.code: name for name, data in ALL_LOCATIONS.items()}
