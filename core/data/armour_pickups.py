"""Physical armour pickups found in the game world, keyed for both AP location
creation and client-side detection via armour set bitmask monitoring.

set_key   — matches ArmourAddresses._SET_OFFSETS keys in armour.py
piece     — ArmourPiece flag (CHESTPLATE/HELMET/GLOVES/BOOTS)
name      — canonical AP location name
planet    — AP region name
"""
from typing import NamedTuple

from .armour import ArmourPiece


class ArmourPickup(NamedTuple):
    set_key: str
    piece: ArmourPiece
    name: str
    planet: str


ARMOUR_PICKUPS: list[ArmourPickup] = [
    # Pokitaru
    ArmourPickup("wildfire", ArmourPiece.CHESTPLATE, "Pokitaru Wildfire Chestplate",          "Pokitaru"),
    ArmourPickup("wildfire", ArmourPiece.GLOVES, "Pokitaru Wildfire Gloves",              "Pokitaru"),
    # Ryllus
    ArmourPickup("sludge",   ArmourPiece.BOOTS, "Ryllus Sludge Mk9 Boots",              "Ryllus"),
    ArmourPickup("wildfire", ArmourPiece.HELMET, "Ryllus Wildfire Helmet",                "Ryllus"),
    # Kalidon
    ArmourPickup("sludge",   ArmourPiece.GLOVES, "Kalidon Sludge Mk9 Gloves",            "Kalidon"),
    ArmourPickup("sludge",   ArmourPiece.CHESTPLATE, "Kalidon Sludge Mk9 Chestplate",        "Kalidon"),
    ArmourPickup("wildfire", ArmourPiece.BOOTS, "Kalidon Wildfire Boots",                "Kalidon"),
    # Metalis
    ArmourPickup("sludge",       ArmourPiece.HELMET, "Metalis Sludge Mk9 Helmet",        "Metalis"),
    ArmourPickup("crystallix",   ArmourPiece.HELMET, "Metalis Crystallix Helmet",         "Metalis"),
    ArmourPickup("crystallix",   ArmourPiece.GLOVES, "Metalis Crystallix Gloves",         "Metalis"),
    ArmourPickup("electroshock", ArmourPiece.GLOVES, "Metalis Electroshock Gloves",       "Metalis"),
    # Dreamtime
    ArmourPickup("crystallix",   ArmourPiece.CHESTPLATE, "Dreamtime Crystallix Chestplate",   "Dreamtime"),
    # Outpost Omega
    ArmourPickup("electroshock", ArmourPiece.BOOTS, "Outpost Omega Electroshock Boots",  "Outpost Omega"),
    ArmourPickup("crystallix",   ArmourPiece.BOOTS, "Outpost Omega Crystallix Boots",    "Outpost Omega"),
    # Challax
    ArmourPickup("electroshock", ArmourPiece.CHESTPLATE, "Challax Electroshock Chestplate",   "Challax"),
    ArmourPickup("electroshock", ArmourPiece.HELMET, "Challax Electroshock Helmet",       "Challax"),
    # Dayni Moon
    ArmourPickup("mega_bomb", ArmourPiece.BOOTS, "Dayni Moon Mega Bomb Boots",           "Dayni Moon"),
    ArmourPickup("mega_bomb", ArmourPiece.GLOVES, "Dayni Moon Mega Bomb Gloves",          "Dayni Moon"),
    ArmourPickup("mega_bomb", ArmourPiece.HELMET, "Dayni Moon Mega Bomb Helmet",          "Dayni Moon"),
    # Inside Clank
    ArmourPickup("mega_bomb", ArmourPiece.CHESTPLATE, "Inside Clank Mega Bomb Chestplate",    "Inside Clank"),
]

# (set_key, piece_bitmask) → location name — used by the client to map a
# detected bitmask change to an AP location check.
ARMOUR_FLAG_TO_LOCATION: dict[tuple[str, ArmourPiece], str] = {
    (ap.set_key, ap.piece): ap.name
    for ap in ARMOUR_PICKUPS
}
