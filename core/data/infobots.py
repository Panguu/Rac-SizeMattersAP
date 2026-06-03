"""Infobot planet-unlock items for Ratchet & Clank: Size Matters.

Infobots are AP items given to the player.  When received they set the
corresponding planet's unlock-status address to INFOBOT_UNLOCK_VALUE (3),
which allows Ratchet to travel to (or enter) that planet.

Planets that are auto-unlocked from the start (no infobot item):
  Dreamtime    -- unlocked through Outpost Omega automatically
  Inside Clank -- entrance only accessible from Dayni Moon; requires Shrink Ray
"""
from __future__ import annotations

from .addresses import PLANET_UNLOCK_ADDRESSES

INFOBOT_UNLOCK_VALUE = 3  # value written to the planet status address

# Display name -> planet key used in PLANET_STATE_ADDRESSES
INFOBOT_ITEM_TO_PLANET: dict[str, str] = {
    "Pokitaru Infobot":     "pokitaru",
    "Ryllus Infobot":       "ryllus",
    "Kalidon Infobot":      "kalidon",
    "Metalis Infobot":      "metalis",
    "Outpost Omega Infobot": "outpost_omega",
    "Challax Infobot":      "challax",
    "Dayni Moon Infobot":   "dayni_moon",
    "Quodrona Infobot":     "quodrona",
}

PLANET_STATE_ADDRESSES: dict[str, int] = {
    "pokitaru":     PLANET_UNLOCK_ADDRESSES["POKITARU"],
    "ryllus":       PLANET_UNLOCK_ADDRESSES["RYLLUS"],
    "kalidon":      PLANET_UNLOCK_ADDRESSES["KALIDON"],
    "metalis":      PLANET_UNLOCK_ADDRESSES["METALIS"],
    "outpost_omega": PLANET_UNLOCK_ADDRESSES["OUTPOST_OMEGA"],
    "challax":      PLANET_UNLOCK_ADDRESSES["CHALLAX"],
    "dayni_moon":   PLANET_UNLOCK_ADDRESSES["DAYNI_MOON"],
    "quodrona":     PLANET_UNLOCK_ADDRESSES["QUODRONA"],
}

# Planet unlock addresses always forced to INFOBOT_UNLOCK_VALUE because
# these planets have no collectible infobot in the AP item pool.
AUTO_UNLOCK_ADDRESSES: list[int] = [
    0x21F4C661,  # Pokitaru      -- mandatory starting planet, always accessible
    0x21F4C665,  # Dreamtime     -- auto-unlocked via Outpost Omega
    0x21F4C669,  # Inside Clank  -- sub-area, entrance only from Dayni Moon
]
