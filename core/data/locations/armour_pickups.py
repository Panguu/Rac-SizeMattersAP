from typing import NamedTuple

from ..armour import ArmourPiece


class ArmourPickup(NamedTuple):
    """
    Data record for an armour pickup's information.
    This is used for monitoring and modifying armour pickups in the game.
    """
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
    # ArmourPickup("electroshock", ArmourPiece.CHESTPLATE, "Challax Electroshock Chestplate", "Challax"),  # not reachable
    ArmourPickup("electroshock", ArmourPiece.HELMET, "Challax Electroshock Helmet",    "Challax"),
    # Dayni Moon
    ArmourPickup("mega_bomb", ArmourPiece.HELMET,    "Dayni Moon Mega Bomb Helmet",    "Dayni Moon"),
    # Inside Clank
    # ArmourPickup("mega_bomb", ArmourPiece.CHESTPLATE, "Inside Clank Mega Bomb Chestplate",
    #              "Inside Clank"),  # cutscene address not yet found
]

ARMOUR_FLAG_TO_LOCATION: dict[tuple[str, ArmourPiece], str] = {
    (ap.set_key, ap.piece): ap.name
    for ap in ARMOUR_PICKUPS
}

CHALLENGE_LOCATION_TO_ARMOUR_FLAG: dict[str, tuple[str, ArmourPiece]] = {
    "Metalis Smasherbot's Revenge - Crystallix Helmet (CC)":          ("crystallix",   ArmourPiece.HELMET),
    "Metalis The Uber Finals - Crystallix Gloves (CC)":               ("crystallix",   ArmourPiece.GLOVES),
    "Metalis Nigh Impossible - Sludge Mk9 Gloves (CC)":               ("sludge",       ArmourPiece.GLOVES),
    "Dayni Moon The Ultimate Showdown - Mega Bomb Gloves (CC)":       ("mega_bomb",    ArmourPiece.GLOVES),
    "Dayni Moon Infinite Improbability - Mega Bomb Boots (CC)":       ("mega_bomb",    ArmourPiece.BOOTS),
    "Outpost Omega Vertigo - Electroshock Boots (SC)":                ("electroshock", ArmourPiece.BOOTS),
}
