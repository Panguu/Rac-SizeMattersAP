"""Physical armour pickups found in the game world, keyed for both AP location
creation and client-side detection via armour set bitmask monitoring.

set_key   — matches ArmourAddresses._SET_OFFSETS keys in armour.py
piece     — bitmask: CHESTPLATE=0x01, HELMET=0x02, GLOVES=0x04, BOOTS=0x10
name      — canonical AP location name
planet    — AP region name
"""
from typing import NamedTuple


class ArmourPickup(NamedTuple):
    set_key: str
    piece: int
    name: str
    planet: str


ARMOUR_PICKUPS: list[ArmourPickup] = [
    # Pokitaru
    ArmourPickup("wildfire", 0x01, "Pokitaru Wildfire Chestplate",          "Pokitaru"),
    ArmourPickup("wildfire", 0x04, "Pokitaru Wildfire Gloves",              "Pokitaru"),
    # Ryllus
    ArmourPickup("sludge",   0x10, "Ryllus Sludge Mk9 Boots",              "Ryllus"),
    ArmourPickup("wildfire", 0x02, "Ryllus Wildfire Helmet",                "Ryllus"),
    # Kalidon
    ArmourPickup("sludge",   0x04, "Kalidon Sludge Mk9 Gloves",            "Kalidon"),
    ArmourPickup("sludge",   0x01, "Kalidon Sludge Mk9 Chestplate",        "Kalidon"),
    ArmourPickup("wildfire", 0x10, "Kalidon Wildfire Boots",                "Kalidon"),
    # Metalis
    ArmourPickup("sludge",       0x02, "Metalis Sludge Mk9 Helmet",        "Metalis"),
    ArmourPickup("crystallix",   0x02, "Metalis Crystallix Helmet",         "Metalis"),
    ArmourPickup("crystallix",   0x04, "Metalis Crystallix Gloves",         "Metalis"),
    ArmourPickup("electroshock", 0x04, "Metalis Electroshock Gloves",       "Metalis"),
    # Dreamtime
    ArmourPickup("crystallix",   0x01, "Dreamtime Crystallix Chestplate",   "Dreamtime"),
    # Outpost Omega
    ArmourPickup("electroshock", 0x10, "Outpost Omega Electroshock Boots",  "Outpost Omega"),
    ArmourPickup("crystallix",   0x10, "Outpost Omega Crystallix Boots",    "Outpost Omega"),
    # Challax
    ArmourPickup("electroshock", 0x01, "Challax Electroshock Chestplate",   "Challax"),
    ArmourPickup("electroshock", 0x02, "Challax Electroshock Helmet",       "Challax"),
    # Dayni Moon
    ArmourPickup("mega_bomb", 0x10, "Dayni Moon Mega Bomb Boots",           "Dayni Moon"),
    ArmourPickup("mega_bomb", 0x04, "Dayni Moon Mega Bomb Gloves",          "Dayni Moon"),
    ArmourPickup("mega_bomb", 0x02, "Dayni Moon Mega Bomb Helmet",          "Dayni Moon"),
    # Inside Clank
    ArmourPickup("mega_bomb", 0x01, "Inside Clank Mega Bomb Chestplate",    "Inside Clank"),
]

# (set_key, piece_bitmask) → location name — used by the client to map a
# detected bitmask change to an AP location check.
ARMOUR_FLAG_TO_LOCATION: dict[tuple[str, int], str] = {
    (ap.set_key, ap.piece): ap.name
    for ap in ARMOUR_PICKUPS
}
