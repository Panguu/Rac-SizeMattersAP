from typing import NamedTuple

from .core.data.locations.armour_pickups import ARMOUR_PICKUPS
from .core.data.locations.challenges import CHALLENGE_PICKUPS, DAYNI_MOON_CLANK_PICKUPS, METALIS_CLANK_PICKUPS
from .core.data.locations.skill_points import SKILL_POINTS
from .core.data.locations.titanium_bolts import TITANIUM_BOLTS

BASE_ID = 77_700_000


class RACLocationData(NamedTuple):
    code: int
    region: str


TITANIUM_BOLT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1000 + idx, bolt.region)
    for idx, (name, bolt) in enumerate(TITANIUM_BOLTS.items(), start=1)
}

ARMOUR_PICKUP_LOCATIONS: dict[str, RACLocationData] = {
    ap.name: RACLocationData(BASE_ID + 1100 + idx, ap.planet)
    for idx, ap in enumerate(ARMOUR_PICKUPS, start=1)
}


BOSS_LOCATIONS: dict[str, RACLocationData] = {
    "Defeat Otto Destruct": RACLocationData(BASE_ID + 1200, "Quodrona"),
}

SKILL_POINT_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1300 + idx, sp.region)
    for idx, (name, sp) in enumerate(SKILL_POINTS.items(), start=1)
}

VENDOR_WEAPON_PLANET: dict[str, str] = {
    "Lacerator":       "Pokitaru",
    "Acid Bomb Glove": "Pokitaru",
    "Concussion Gun":  "Pokitaru",
    "Agents of Doom":  "Ryllus",
    "Scorcher":        "Kalidon",
    "Suck Cannon":     "Dreamtime",
    "Bee Mine Glove":  "Outpost Omega",
    "Sniper Mine":     "Challax",
    "Shock Rocket":    "Dayni Moon",
    "Static Barrier":  "Inside Clank",
    "Laser Tracer":    "Quodrona",
}

VENDOR_GADGET_PLANET: dict[str, str] = {
    "Hypershot":   "Pokitaru",
    "PDA":         "Challax",
    "Map-O-Matic": "Dayni Moon",
}

WEAPON_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    f"Purchase {name}": RACLocationData(BASE_ID + 2000 + idx, planet)
    for idx, (name, planet) in enumerate(VENDOR_WEAPON_PLANET.items(), start=1)
}

GADGET_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    f"Purchase {name}": RACLocationData(BASE_ID + 2100 + idx, planet)
    for idx, (name, planet) in enumerate(VENDOR_GADGET_PLANET.items(), start=1)
}

# None sentinel = mod slot exists in the weapon struct but is not sold at any vendor.
# It is counted for slot-index purposes so subsequent mods land on the correct address.
VENDOR_WEAPON_MOD_PLANET: dict[tuple, str | None] = {
    ("Lacerator",       "Lock On Mod"):       "Kalidon",
    ("Lacerator",       "Double Barrel Mod"): "Challax",
    ("Acid Bomb Glove", "Acid Burn Mod"):     "Challax",
    ("Acid Bomb Glove", "Epoxy Mod"):         "Challax",
    ("Concussion Gun",  "Split Barrel Mod"):  "Kalidon",
    ("Concussion Gun",  "Lock On Mod"):       "Challax",
    ("Concussion Gun",  "Charge Up Mod"):     "Challax",
    ("Agents of Doom",  None):                None,    # mod slot 1 inaccessible at vendor
    ("Agents of Doom",  "Launcher Mod"):      "Quodrona",
    ("Scorcher",        "Spitfire Mod"):      "Quodrona",
    ("Bee Mine Glove",  "Worker Mod"):        "Challax",
    ("Sniper Mine",     "Split Beam Mod"):    "Quodrona",
    ("Shock Rocket",    "Lock On Mod"):       "Quodrona",
    ("Shock Rocket",    "After Shock Mod"):   "Quodrona",
}

WEAPON_MOD_VENDOR_LOCATIONS: dict[str, RACLocationData] = {
    f"Purchase {weapon} {mod}": RACLocationData(BASE_ID + 2200 + idx, planet)
    for idx, ((weapon, mod), planet) in enumerate(VENDOR_WEAPON_MOD_PLANET.items(), start=1)
    if mod is not None
}

from .core.data.locations.armour_set_checks import ARMOUR_SET_CHECKS

ARMOUR_SET_CHECK_LOCATIONS: dict[str, RACLocationData] = {
    name: RACLocationData(BASE_ID + 1500 + idx, "Pokitaru")
    for idx, name in enumerate(ARMOUR_SET_CHECKS, start=1)
}

GADGET_PICKUP_LOCATIONS: dict[str, RACLocationData] = {
    "Ryllus Sprout-O-Matic":            RACLocationData(BASE_ID + 1401, "Ryllus"),
    "Metalis Electroshock Gloves":      RACLocationData(BASE_ID + 1406, "Metalis"),
}

# ── Skyboard challenge locations ──────────────────────────────────────────────
# item_checks (1): races that award a randomised item only.
SKYBOARD_ITEM_LOCATIONS: dict[str, RACLocationData] = {
    "Kalidon Learner's Permit (SC)":                   RACLocationData(BASE_ID + 1402, "Kalidon"),
    "Kalidon Master's Challenge (SC)":                 RACLocationData(BASE_ID + 1405, "Kalidon"),
    "Outpost Omega Vertigo - Electroshock Boots (SC)": RACLocationData(BASE_ID + 1800, "Outpost Omega"),
    "Outpost Omega Interior Decorating (SC)":          RACLocationData(BASE_ID + 1801, "Outpost Omega"),
}

# all_challenges (2): non-item races added on top of item_checks.
EXTRA_SKYBOARD_LOCATIONS: dict[str, RACLocationData] = {
    "Kalidon Speeding Ticket (SC)":            RACLocationData(BASE_ID + 1403, "Kalidon"),
    "Kalidon Tricky Air (SC)":                 RACLocationData(BASE_ID + 1404, "Kalidon"),
    "Outpost Omega Danger, High Voltage (SC)": RACLocationData(BASE_ID + 1802, "Outpost Omega"),
    "Outpost Omega The Vortex (SC)":           RACLocationData(BASE_ID + 1803, "Outpost Omega"),
}

CHALLENGE_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(BASE_ID + 1600 + idx, cp.planet)
    for idx, cp in enumerate(CHALLENGE_PICKUPS, start=1)
}

_ALL_CLANK_PICKUPS = METALIS_CLANK_PICKUPS + DAYNI_MOON_CLANK_PICKUPS
ALL_CLANK_LOCATIONS: dict[str, RACLocationData] = {
    cp.name: RACLocationData(BASE_ID + 1700 + idx, cp.planet)
    for idx, cp in enumerate(_ALL_CLANK_PICKUPS, start=1)
    if cp.name not in CHALLENGE_LOCATIONS  # combined reward-challenge names live in CHALLENGE_LOCATIONS
}

ALL_LOCATIONS: dict[str, RACLocationData] = {
    **TITANIUM_BOLT_LOCATIONS,
    **ARMOUR_PICKUP_LOCATIONS,
    **BOSS_LOCATIONS,
    **SKILL_POINT_LOCATIONS,
    **GADGET_PICKUP_LOCATIONS,
    **WEAPON_VENDOR_LOCATIONS,
    **GADGET_VENDOR_LOCATIONS,
    **WEAPON_MOD_VENDOR_LOCATIONS,
    **ARMOUR_SET_CHECK_LOCATIONS,
    **CHALLENGE_LOCATIONS,
    **ALL_CLANK_LOCATIONS,
    **SKYBOARD_ITEM_LOCATIONS,
    **EXTRA_SKYBOARD_LOCATIONS,
}

LOCATION_ID_TO_NAME: dict[int, str] = {data.code: name for name, data in ALL_LOCATIONS.items()}
