"""Clank challenge arenas — location checks gated by the Clank Challenges option.

item_challenges (1): only the armour/gadget reward locations (CHALLENGE_PICKUPS).
all_challenges  (2): every individual challenge completion is also a location.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import IntFlag
from typing import NamedTuple

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

from ..data.addresses import (
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


class ClankChallengeState(State):
    """
    Global Clank challenge arena tracker. Polls int8 completion flags.

    On completion, sends the AP location check via the injected callback.
    Call sync_from_ap() on (re)connect to restore already-checked locations
    so they are never re-sent.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self._completed: set[str]                    = set()
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._task: asyncio.Task | None              = None

    async def read(self) -> bool:
        async with self._lock:
            for addr, name in ALL_CLANK_ADDRESS_MAP.items():
                if self.pine.read_int8(addr) >= 2:
                    self._completed.add(name)
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        while True:
            async with self._lock:
                for addr, name in ALL_CLANK_ADDRESS_MAP.items():
                    if name not in self._completed and self.pine.read_int8(addr) >= 2:
                        self._completed.add(name)
                        self._on_location_check(name)
                        self.on_challenge_completed(name)
            await asyncio.sleep(interval / 1000)

    async def activate(self, interval: int, on_location_check: Callable[[str], None]) -> None:
        """Start polling. on_location_check is called for each newly completed location."""
        if self._task is not None:
            return
        self._on_location_check = on_location_check
        self._task = asyncio.create_task(self.poll(0, interval, lambda *_: None))

    async def deactivate(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._on_location_check = lambda _: None

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Pre-populate from AP-confirmed locations on (re)connect."""
        self._completed.update(
            name for name in checked_locations if name in ALL_CLANK_ADDRESS_MAP
        )

    def write_defaults(self) -> None:
        """Write 1 to every challenge address currently at 0, making all challenges available."""
        for addr in ALL_CLANK_ADDRESS_MAP:
            if self.pine.read_int8(addr) == 0:
                self.pine.write_int8(addr, 1)

    def on_challenge_completed(self, _name: str) -> None:
        """Hook fired after the AP location check is sent. Override for extra logic."""
        del _name

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClankChallengeState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        return f"ClankChallengeState(completed={len(self._completed)}/{len(ALL_CLANK_ADDRESS_MAP)})"


class SkyboardChallengeState(State):
    """
    Global Skyboard race tracker. Polls int8 bitmasks for race completion.

    On completion, sends the AP location check via the injected callback.
    Call sync_from_ap() on (re)connect to restore already-checked locations
    so they are never re-sent.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self._completed: set[str]                    = set()
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._task: asyncio.Task | None              = None

    async def read(self) -> bool:
        async with self._lock:
            for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
                if self.pine.read_int8(addr) & mask:
                    self._completed.add(name)
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        while True:
            async with self._lock:
                for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
                    if name not in self._completed and self.pine.read_int8(addr) & mask:
                        self._completed.add(name)
                        self._on_location_check(name)
                        self.on_race_completed(name)
            await asyncio.sleep(interval / 1000)

    async def activate(self, interval: int, on_location_check: Callable[[str], None]) -> None:
        """Start polling. on_location_check is called for each newly completed race."""
        if self._task is not None:
            return
        self._on_location_check = on_location_check
        self._task = asyncio.create_task(self.poll(0, interval, lambda *_: None))

    async def deactivate(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._on_location_check = lambda _: None

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Pre-populate from AP-confirmed locations on (re)connect."""
        self._completed.update(
            name for name in checked_locations if name in SKYBOARD_ADDRESS_MASK_MAP.values()
        )

    def write_defaults(self) -> None:
        """OR the full race-unlock bitmask into each planet's skyboard unlock address."""
        for addr, full_mask in SKYBOARD_UNLOCK_MASK.items():
            current = self.pine.read_int8(addr)
            if current | full_mask != current:
                self.pine.write_int8(addr, current | full_mask)

    def on_race_completed(self, _name: str) -> None:
        """Hook fired after the AP location check is sent. Override for extra logic."""
        del _name

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SkyboardChallengeState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        return f"SkyboardChallengeState(completed={len(self._completed)}/{len(SKYBOARD_ADDRESS_MASK_MAP)})"
