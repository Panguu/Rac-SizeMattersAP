"""Clank challenge arenas — location checks gated by the Clank Challenges option.

item_challenges (1): only the armour/gadget reward locations (CHALLENGE_PICKUPS).
all_challenges  (2): every individual challenge completion is also a location.
"""
from __future__ import annotations

from enum import IntFlag
from typing import NamedTuple

from .addresses import (
    DAYNI_MOON_CLANK_CHALLENGES_COMPLETED_ADDR,
    KAILDON_SKYBOARD_CHALLENGES_COMPLETED_ADDR,
    METALIS_CLANK_CHALLENGES_COMPLETED_ADDR,
    OUTPOST_OMEGA_SKYBOARD_CHALLENGES_COMPLETED_ADDR,
)


class ChallengePickup(NamedTuple):
    address: int   # game address polled for completion; 0x00 = placeholder
    name:    str   # AP location name
    planet:  str   # AP region name


class SkyboardPickup(NamedTuple):
    unlock_addr:    int           # write 1 here at first planet load to unlock the challenge
    completed_addr: int           # poll this for completion bitmask; 0x00 = not yet confirmed
    mask:           SkyboardBit # bit set in completed_addr when this race finishes
    name:           str           # AP location name
    planet:         str           # AP region name


class SkyboardBit(IntFlag):
    RACE_1 = 0x01
    RACE_2 = 0x04
    RACE_3 = 0x10
    RACE_4 = 0x40


# ── Reward locations (item_challenges + all_challenges) ───────────────────────
CHALLENGE_PICKUPS: list[ChallengePickup] = [
    # Metalis — each address is the completion flag for the named challenge
    ChallengePickup(0x1F4B3DE, "Metalis Polarizer (CC)",            "Metalis"),   # Buzzsaw Blitz
    ChallengePickup(0x1F4B3E2, "Metalis Crystallix Helmet (CC)",    "Metalis"),   # Smasherbot's Revenge
    ChallengePickup(0x1F4B3E7, "Metalis Crystallix Gloves (CC)",    "Metalis"),   # The Uber Finals
    ChallengePickup(0x1F4B3EC, "Metalis Sludge Mk9 Helmet (CC)",    "Metalis"),   # Nigh Impossible
    # Dayni Moon
    ChallengePickup(0x1F4B3FF, "Dayni Moon Mega Bomb Gloves (CC)",  "Dayni Moon"),  # The Ultimate Showdown
    ChallengePickup(0x1F4B404, "Dayni Moon Mega Bomb Boots (CC)",   "Dayni Moon"),  # Infinite Improbability
    # Outpost Omega — detected via SkyboardPoller (Vertigo completion)
    # ChallengePickup(0x00, "Outpost Omega Electroshock Boots (CC)", "Outpost Omega"),
]

# Reward address map (used by item_challenges and for _append_location lookup)
CHALLENGE_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in CHALLENGE_PICKUPS
    if cp.address != 0
}

# ── Individual completion locations (all_challenges only) ─────────────────────
METALIS_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, f"Metalis {name} (CC)", "Metalis")
    for name, addr in METALIS_CLANK_CHALLENGES_COMPLETED_ADDR.items()
]

DAYNI_MOON_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, f"Dayni Moon {name} (CC)", "Dayni Moon")
    for name, addr in DAYNI_MOON_CLANK_CHALLENGES_COMPLETED_ADDR.items()
]

# All individual + reward addresses — used for initialization and all_challenges polling
ALL_CLANK_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in (CHALLENGE_PICKUPS + METALIS_CLANK_PICKUPS + DAYNI_MOON_CLANK_PICKUPS)
    if cp.address != 0
}

# ── Skyboard challenge pickups ────────────────────────────────────────────────
KALIDON_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask), f"Kalidon {name} (SC)", "Kalidon")
    for name, (unlock_addr, completed_addr, mask) in KAILDON_SKYBOARD_CHALLENGES_COMPLETED_ADDR.items()
]

# Vertigo (last race) is the condition for Outpost Omega Electroshock Boots
_OO_SKYBOARD_NAMES: dict[str, str] = {
    "Interior Decorating": "Outpost Omega Interior Decorating (SC)",
    "Danger, High Voltage": "Outpost Omega Danger, High Voltage (SC)",
    "The Vortex":           "Outpost Omega The Vortex (SC)",
    "Vertigo":              "Outpost Omega Electroshock Boots (CC)",
}

OUTPOST_OMEGA_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask),
                   _OO_SKYBOARD_NAMES[name], "Outpost Omega")
    for name, (unlock_addr, completed_addr, mask) in OUTPOST_OMEGA_SKYBOARD_CHALLENGES_COMPLETED_ADDR.items()
]

ALL_SKYBOARD_PICKUPS: list[SkyboardPickup] = KALIDON_SKYBOARD_PICKUPS + OUTPOST_OMEGA_SKYBOARD_PICKUPS

# (completed_addr, mask) → location name — used by SkyboardPoller
SKYBOARD_ADDRESS_MASK_MAP: dict[tuple[int, int], str] = {
    (sp.completed_addr, int(sp.mask)): sp.name
    for sp in ALL_SKYBOARD_PICKUPS
    if sp.completed_addr != 0
}

# unlock_addr → OR of all race masks for that planet (0x55 when all 4 races present).
# Written to the unlock address at first planet load to make all races available.
SKYBOARD_UNLOCK_MASK: dict[int, int] = {}
for _sp in ALL_SKYBOARD_PICKUPS:
    if _sp.unlock_addr != 0:
        SKYBOARD_UNLOCK_MASK[_sp.unlock_addr] = SKYBOARD_UNLOCK_MASK.get(_sp.unlock_addr, 0) | int(_sp.mask)

# ── Challenge-only AP items ───────────────────────────────────────────────────
CHALLENGE_ONLY_ITEMS: frozenset[str] = frozenset({
    "Polarizer",
    "Sludge Mk9 Helmet",
    "Crystallix Helmet",
    "Crystallix Gloves",
    "Mega Bomb Gloves",
    "Mega Bomb Boots",
    "Electroshock Boots",
})
