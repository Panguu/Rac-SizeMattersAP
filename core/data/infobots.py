"""Infobot planet-unlock items for Ratchet & Clank: Size Matters.

Infobots are AP items given to the player.  When received they set the
corresponding planet's unlock-status address to INFOBOT_UNLOCK_VALUE (3),
which allows Ratchet to travel to (or enter) that planet.

The PlanetState address map is currently all 0x00 — final addresses will be
provided separately and slotted in here.

Planets that have no collectible infobot and are auto-unlocked by the game:
  Ryllus       — accessed going through Pokitaru
  Metalis      — teleported there automatically on Kalidon completion
  Dreamtime    — unlocked through Outpost Omega the same way
  Inside Clank — entrance only accessible from Dayni Moon; requires Shrink Ray
"""
from __future__ import annotations

from .addresses import PLANET_UNLOCK_ADDRESSES

INFOBOT_UNLOCK_VALUE = 3  # value written to the planet status address

# Display name → planet key used in PLANET_STATE_ADDRESSES
INFOBOT_ITEM_TO_PLANET: dict[str, str] = {
    "Pokitaru Infobot":      "pokitaru",
    "Kalidon Infobot":       "kalidon",
    "Outpost Omega Infobot": "outpost_omega",
    "Challax Infobot":       "challax",
    "Dayni Moon Infobot":    "dayni_moon",
    "Quodrona Infobot":      "quodrona",
}

PLANET_STATE_ADDRESSES: dict[str, int] = {
    "pokitaru":      PLANET_UNLOCK_ADDRESSES["POKITARU"],
    "kalidon":       PLANET_UNLOCK_ADDRESSES["KALIDON"],
    "outpost_omega": PLANET_UNLOCK_ADDRESSES["OUTPOST_OMEGA"],
    "challax":       PLANET_UNLOCK_ADDRESSES["CHALLAX"],
    "dayni_moon":    PLANET_UNLOCK_ADDRESSES["DAYNI_MOON"],
    "quodrona":      PLANET_UNLOCK_ADDRESSES["QUODRONA"],
}

# Planet unlock addresses always forced to INFOBOT_UNLOCK_VALUE because
# these planets have no collectible infobot in the AP item pool.
AUTO_UNLOCK_ADDRESSES: list[int] = [
    0x21F4C662,  # Ryllus       — auto-accessed via Pokitaru
    0x21F4C664,  # Metalis      — auto-unlocked by completing Kalidon
    0x21F4C665,  # Dreamtime    — auto-unlocked by completing Outpost Omega
    0x21F4C669,  # Inside Clank — sub-area, entrance only from Dayni Moon
]
