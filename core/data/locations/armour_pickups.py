"""Physical armour pickups found in the game world, keyed for both AP location
creation and client-side detection via armour set bitmask monitoring.

set_key   — matches ArmourAddresses._SET_OFFSETS keys in armour.py
piece     — ArmourPiece flag (CHESTPLATE/HELMET/GLOVES/BOOTS)
name      — canonical AP location name
planet    — AP region name

Challenge-exclusive pickups (Sludge Mk9 Gloves, Sludge Mk9 Helmet,
Crystallix Helmet, Crystallix Gloves, Mega Bomb Gloves, Mega Bomb Boots,
Electroshock Boots) are defined in challenges.py, not here.
"""
from typing import NamedTuple

from ..armour import ArmourPiece


class ArmourPickup(NamedTuple):
    set_key: str
    piece: ArmourPiece
    name: str
    planet: str


ARMOUR_PICKUPS: list[ArmourPickup] = [
    # Pokitaru
    ArmourPickup("wildfire", ArmourPiece.CHESTPLATE, "Pokitaru Wildfire Chestplate",   "Pokitaru"),
    ArmourPickup("wildfire", ArmourPiece.GLOVES,     "Pokitaru Wildfire Gloves",       "Pokitaru"),
    # Ryllus
    ArmourPickup("sludge",   ArmourPiece.BOOTS,      "Ryllus Sludge Mk9 Boots",        "Ryllus"),
    ArmourPickup("wildfire", ArmourPiece.HELMET,     "Ryllus Wildfire Helmet",         "Ryllus"),
    # Kalidon
    ArmourPickup("sludge",   ArmourPiece.CHESTPLATE, "Kalidon Sludge Mk9 Chestplate",  "Kalidon"),
    ArmourPickup("wildfire", ArmourPiece.BOOTS,      "Kalidon Wildfire Boots",         "Kalidon"),
    # Metalis
    # ArmourPickup("electroshock", ArmourPiece.GLOVES, "Metalis Electroshock Gloves",
    #              "Metalis"),  # currently unreachable
    # Dreamtime
    ArmourPickup("crystallix", ArmourPiece.CHESTPLATE, "Dreamtime Crystallix Chestplate", "Dreamtime"),
    # Outpost Omega
    ArmourPickup("crystallix", ArmourPiece.BOOTS,    "Outpost Omega Crystallix Boots", "Outpost Omega"),
    # Challax
    ArmourPickup("electroshock", ArmourPiece.CHESTPLATE, "Challax Electroshock Chestplate", "Challax"),
    ArmourPickup("electroshock", ArmourPiece.HELMET, "Challax Electroshock Helmet",    "Challax"),
    # Dayni Moon
    ArmourPickup("mega_bomb", ArmourPiece.HELMET,    "Dayni Moon Mega Bomb Helmet",    "Dayni Moon"),
    # Inside Clank
    # ArmourPickup("mega_bomb", ArmourPiece.CHESTPLATE, "Inside Clank Mega Bomb Chestplate",
    #              "Inside Clank"),  # cutscene address not yet found
]

# (set_key, piece_bitmask) → location name — used by the client to map a
# detected bitmask change to an AP location check.
ARMOUR_FLAG_TO_LOCATION: dict[tuple[str, ArmourPiece], str] = {
    (ap.set_key, ap.piece): ap.name
    for ap in ARMOUR_PICKUPS
}

# Challenge reward locations that grant armour: location name → (set_key, piece).
# Used by ArmourState.sync_from_ap() to restore location_collected_armour on connect.
CHALLENGE_LOCATION_TO_ARMOUR_FLAG: dict[str, tuple[str, ArmourPiece]] = {
    "Metalis Smasherbot's Revenge - Crystallix Helmet (CC)":          ("crystallix",   ArmourPiece.HELMET),
    "Metalis The Uber Finals - Crystallix Gloves (CC)":               ("crystallix",   ArmourPiece.GLOVES),
    "Metalis Nigh Impossible - Sludge Mk9 Gloves (CC)":               ("sludge",       ArmourPiece.GLOVES),
    "Dayni Moon The Ultimate Showdown - Mega Bomb Gloves (CC)":       ("mega_bomb",    ArmourPiece.GLOVES),
    "Dayni Moon Infinite Improbability - Mega Bomb Boots (CC)":       ("mega_bomb",    ArmourPiece.BOOTS),
    "Outpost Omega Vertigo - Electroshock Boots (SC)":                ("electroshock", ArmourPiece.BOOTS),
}
