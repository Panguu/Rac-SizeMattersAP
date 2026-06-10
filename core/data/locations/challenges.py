from __future__ import annotations

from enum import IntFlag
from typing import NamedTuple

# ── Metalis challenge addresses ────────────────────────────────────────────────

# Challenge type layout per byte is undocumented; written as one 3-byte block.
METALIS_CLANK_UNLOCK_ADDR:  int   = 0x1F4B3DB
METALIS_CLANK_UNLOCK_BYTES: bytes = bytes([0x0F, 0x0F, 0x0F])

_METALIS_CHALLENGES_COMPLETED: dict[str, int] = {
    "Buzzsaw Blitz":              0x1F4B3DE,
    "Take Two For The Team":      0x1F4B3E8,
    "CHARGE!":                    0x1F4B3DF,
    "Bridge The Gap":             0x1F4B3E9,
    "Electric Boogaloo":          0x1F4B3E0,
    "Of Trapeze and Teleporters": 0x1F4B3EA,
    "Showdown":                   0x1F4B3E1,
    "Brain Trip":                 0x1F4B3EB,
    "Smasherbot's Revenge":       0x1F4B3E2,
    "Nigh Impossible":            0x1F4B3EC,
    "Little League":              0x1F4B3E3,
    "Varsity Bracket":            0x1F4B3E4,
    "Collegiate Division":        0x1F4B3E5,
    "Professional Level":         0x1F4B3E6,
    "The Uber Finals":            0x1F4B3E7,
}

# ── Dayni Moon challenge addresses ─────────────────────────────────────────────

# Three consecutive unlock bytes, one per challenge type.
# Written as one 3-byte block starting at the Derby unlock address.
DAYNI_CLANK_DERBY_UNLOCK_ADDR:     int = 0x1F4B3F3
DAYNI_CLANK_DERBY_B_UNLOCK_ADDR:   int = 0x1F4B3F4
DAYNI_CLANK_GADGETBOT_UNLOCK_ADDR: int = 0x1F4B3F5
DAYNI_CLANK_UNLOCK_ADDR:           int = DAYNI_CLANK_DERBY_UNLOCK_ADDR  # = Derby addr
DAYNI_CLANK_UNLOCK_BYTES:        bytes = bytes([0x0F, 0x0F, 0x0F])

_DAYNI_CHALLENGES_COMPLETED: dict[str, int] = {
    "Two's A Crowd":          0x1F4B400,
    "Reverse Into Victory":   0x1F4B401,
    "Emergency Bridge":       0x1F4B402,
    "Leap Of Faith":          0x1F4B403,
    "Infinite Improbability": 0x1F4B404,
    "Welcome to Dayni":       0x1F4B3F6,
    "Round Up!":              0x1F4B3F7,
    "Variety Is Shocking":    0x1F4B3F8,
    "Tom Sawyer":             0x1F4B3F9,
    "Smasherbot Returns!":    0x1F4B3FA,
    "Tri-bomb Tournament":    0x1F4B3FC,
    "A-rooouund the Bend":    0x1F4B3FD,
    "The Thin Bouncy Line":   0x1F4B3FE,
    "The Ultimate Showdown":  0x1F4B3FF,
}

# ── Skyboard addresses ─────────────────────────────────────────────────────────

# Single address pair per planet; cumulative bitmask per race.
# Each entry is (unlock_addr, completed_addr, detection_mask).
_KALIDON_SKYBOARD_COMPLETED: dict[str, tuple[int, int, int]] = {
    "Learner's Permit":   (0x1F4B407, 0x1F4B408, 0x01),
    "Speeding Ticket":    (0x1F4B407, 0x1F4B408, 0x04),
    "Tricky Air":         (0x1F4B407, 0x1F4B408, 0x10),
    "Master's Challenge": (0x1F4B407, 0x1F4B408, 0x40),
}

_OUTPOST_OMEGA_SKYBOARD_COMPLETED: dict[str, tuple[int, int, int]] = {
    "Interior Decorating": (0x1F4B409, 0x1F4B40A, 0x01),
    "Danger, High Voltage": (0x1F4B409, 0x1F4B40A, 0x04),
    "The Vortex":           (0x1F4B409, 0x1F4B40A, 0x10),
    "Vertigo":              (0x1F4B409, 0x1F4B40A, 0x40),
}


class ChallengePickup(NamedTuple):
    address: int   # game address polled for completion; 0x00 = placeholder
    name:    str   # AP location name
    planet:  str   # AP region name


class SkyboardPickup(NamedTuple):
    unlock_addr:    int           # write 1 here at first planet load to unlock the challenge
    completed_addr: int           # poll this for completion bitmask; 0x00 = not yet confirmed
    mask:           SkyboardBit   # bit set in completed_addr when this race finishes
    name:           str           # AP location name
    planet:         str           # AP region name


class SkyboardBit(IntFlag):
    RACE_1 = 0x01
    RACE_2 = 0x04
    RACE_3 = 0x10
    RACE_4 = 0x40


# Maps Metalis challenge name → reward item name for challenges that grant a reward.
# Used to build combined "Challenge - Reward (CC)" location names.
METALIS_CHALLENGE_REWARD: dict[str, str] = {
    "Buzzsaw Blitz":        "Polarizer",
    "Smasherbot's Revenge": "Crystallix Helmet",
    "The Uber Finals":      "Crystallix Gloves",
    "Nigh Impossible":      "Sludge Mk9 Gloves",
}

# ── Reward locations (item_challenges + all_challenges) ───────────────────────
CHALLENGE_PICKUPS: list[ChallengePickup] = [
    # Metalis — combined "Challenge - Reward" names so item_challenges and
    # all_challenges modes use the same location name for reward-granting challenges.
    ChallengePickup(0x1F4B3DE, "Metalis Buzzsaw Blitz - Polarizer (CC)",               "Metalis"),
    ChallengePickup(0x1F4B3E2, "Metalis Smasherbot's Revenge - Crystallix Helmet (CC)", "Metalis"),
    ChallengePickup(0x1F4B3E7, "Metalis The Uber Finals - Crystallix Gloves (CC)",     "Metalis"),
    ChallengePickup(0x1F4B3EC, "Metalis Nigh Impossible - Sludge Mk9 Gloves (CC)",     "Metalis"),
    # Dayni Moon
    ChallengePickup(0x1F4B3FF, "Dayni Moon The Ultimate Showdown - Mega Bomb Gloves (CC)", "Dayni Moon"),
    ChallengePickup(0x1F4B404, "Dayni Moon Infinite Improbability - Mega Bomb Boots (CC)", "Dayni Moon"),
]

# Reward address map (used by item_challenges and for _append_location lookup)
CHALLENGE_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in CHALLENGE_PICKUPS
    if cp.address != 0
}

# ── Individual completion locations (all_challenges only) ─────────────────────
def _metalis_pickup_name(name: str) -> str:
    reward = METALIS_CHALLENGE_REWARD.get(name)
    return f"Metalis {name} - {reward} (CC)" if reward else f"Metalis {name} (CC)"

METALIS_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, _metalis_pickup_name(name), "Metalis")
    for name, addr in _METALIS_CHALLENGES_COMPLETED.items()
]

DAYNI_MOON_CHALLENGE_REWARD: dict[str, str] = {
    "The Ultimate Showdown": "Mega Bomb Gloves",
    "Infinite Improbability": "Mega Bomb Boots",
}

def _dayni_pickup_name(name: str) -> str:
    reward = DAYNI_MOON_CHALLENGE_REWARD.get(name)
    return f"Dayni Moon {name} - {reward} (CC)" if reward else f"Dayni Moon {name} (CC)"

DAYNI_MOON_CLANK_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(addr, _dayni_pickup_name(name), "Dayni Moon")
    for name, addr in _DAYNI_CHALLENGES_COMPLETED.items()
]

# Addresses that use count-increase detection (unlock via single bitmask write).
COUNT_BASED_CHALLENGE_ADDRS: frozenset[int] = (
    frozenset(_METALIS_CHALLENGES_COMPLETED.values())
    | frozenset(_DAYNI_CHALLENGES_COMPLETED.values())
)

# All individual + reward addresses — used for initialization and all_challenges polling
ALL_CLANK_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in (CHALLENGE_PICKUPS + METALIS_CLANK_PICKUPS + DAYNI_MOON_CLANK_PICKUPS)
    if cp.address != 0
}

# ── Skyboard challenge pickups ────────────────────────────────────────────────
KALIDON_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask), f"Kalidon {name} (SC)", "Kalidon")
    for name, (unlock_addr, completed_addr, mask) in _KALIDON_SKYBOARD_COMPLETED.items()
]

# Vertigo (last race) grants Electroshock Boots — combined race-reward name.
_OO_SKYBOARD_NAMES: dict[str, str] = {
    "Interior Decorating": "Outpost Omega Interior Decorating (SC)",
    "Danger, High Voltage": "Outpost Omega Danger, High Voltage (SC)",
    "The Vortex":           "Outpost Omega The Vortex (SC)",
    "Vertigo":              "Outpost Omega Vertigo - Electroshock Boots (SC)",
}

OUTPOST_OMEGA_SKYBOARD_PICKUPS: list[SkyboardPickup] = [
    SkyboardPickup(unlock_addr, completed_addr, SkyboardBit(mask),
                   _OO_SKYBOARD_NAMES[name], "Outpost Omega")
    for name, (unlock_addr, completed_addr, mask) in _OUTPOST_OMEGA_SKYBOARD_COMPLETED.items()
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
    "Sludge Mk9 Gloves",
    "Crystallix Helmet",
    "Crystallix Gloves",
    "Mega Bomb Gloves",
    "Mega Bomb Boots",
    "Electroshock Boots",
})
