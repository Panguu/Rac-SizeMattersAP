"""Clank challenge arenas — optional location checks gated by the Clank Challenges option.

Each challenge has a dedicated memory address that goes from 0 to 1+ when completed.
All addresses are 0x00 until confirmed.
"""
from __future__ import annotations

from typing import NamedTuple


class ChallengePickup(NamedTuple):
    address: int   # game address polled for completion; 0x00 = placeholder
    name:    str   # AP location name
    planet:  str   # AP region name


CHALLENGE_PICKUPS: list[ChallengePickup] = [
    ChallengePickup(0x00, "Kalidon Sludge Mk9 Gloves",        "Kalidon"),
    ChallengePickup(0x00, "Metalis Sludge Mk9 Helmet",        "Metalis"),
    ChallengePickup(0x00, "Metalis Crystallix Helmet",         "Metalis"),
    ChallengePickup(0x00, "Metalis Crystallix Gloves",         "Metalis"),
    ChallengePickup(0x00, "Metalis Polarizer",                 "Metalis"),
    ChallengePickup(0x00, "Dayni Moon Mega Bomb Gloves",       "Dayni Moon"),
    ChallengePickup(0x00, "Dayni Moon Mega Bomb Boots",        "Dayni Moon"),
    ChallengePickup(0x00, "Outpost Omega Electroshock Boots",  "Outpost Omega"),
]

# address → location name; excludes 0x00 placeholders — populated as addresses are confirmed
CHALLENGE_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in CHALLENGE_PICKUPS
    if cp.address != 0
}

SKYBOARD_CHALLENGE_PICKUPS: list[ChallengePickup] = [
    # Kalidon skyboard races
    ChallengePickup(0x00, "Kalidon Learner's Permit",   "Kalidon"),
    ChallengePickup(0x00, "Kalidon Speeding Ticket",    "Kalidon"),
    ChallengePickup(0x00, "Kalidon Tricky Air",         "Kalidon"),
    ChallengePickup(0x00, "Kalidon Master's Challenge", "Kalidon"),
    # Outpost Omega skyboard races
    ChallengePickup(0x00, "Outpost Omega Interior Decorating",   "Outpost Omega"),
    ChallengePickup(0x00, "Outpost Omega Danger High Voltage",   "Outpost Omega"),
    ChallengePickup(0x00, "Outpost Omega The Vortex",            "Outpost Omega"),
    ChallengePickup(0x00, "Outpost Omega Vertigo",               "Outpost Omega"),
]

# Skyboard address map — populated once addresses are confirmed
SKYBOARD_ADDRESS_MAP: dict[int, str] = {
    cp.address: cp.name
    for cp in SKYBOARD_CHALLENGE_PICKUPS
    if cp.address != 0
}

# Items only obtainable via challenges; excluded from the item pool when Clank Challenges is off
CHALLENGE_ONLY_ITEMS: frozenset[str] = frozenset({
    "Polarizer",
    "Sludge Mk9 Gloves",
    "Sludge Mk9 Helmet",
    "Crystallix Helmet",
    "Crystallix Gloves",
    "Mega Bomb Gloves",
    "Mega Bomb Boots",
    "Electroshock Boots",
})
