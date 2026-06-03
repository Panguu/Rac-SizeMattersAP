import asyncio
from collections.abc import Callable
from enum import IntEnum

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

PLANET_UNLOCK_BASE: int = 0x21F4C661  # Pokitaru — rest follow sequentially


class PlanetLockValue(IntEnum):
    LOCKED   = 0x00
    UNLOCKED = 0x03

PLANET_UNLOCK_ORDER: list[str] = [
    "POKITARU",
    "RYLLUS",
    "KALIDON",
    "METALIS",
    "DREAMTIME",
    "OUTPOST_OMEGA",
    "CHALLAX",
    "DAYNI_MOON",
    "INSIDE_CLANK",
    "QUODRONA",
]

# Planets always forced unlocked — no infobot item in the AP pool for these.
_AUTO_UNLOCK_NAMES: frozenset[str] = frozenset({
    "POKITARU",       # mandatory starting planet
    "METALIS",        # auto-unlocked from start
    "DREAMTIME",      # auto-unlocked via Outpost Omega
    "OUTPOST_OMEGA",  # auto-unlocked from start
    "INSIDE_CLANK",   # sub-area accessible only from Dayni Moon
})

_COUNT = len(PLANET_UNLOCK_ORDER)


class PlanetUnlockState(State):
    """
    Global planet unlock tracker. Reads and writes all planet unlock bytes
    in a single contiguous read_bytes/write_bytes call.

    Each byte is 0x03 (unlocked) or 0x00 (locked), starting at PLANET_UNLOCK_BASE.

    self.unlocked  — last state read from memory (used for transition callbacks).
    self._desired  — authoritative desired state written by enforcement.
    Enforcement is inactive until set_unlocked_planets() is first called (after AP connects).
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.unlocked: dict[str, bool]   = dict.fromkeys(PLANET_UNLOCK_ORDER, False)
        self._desired: dict[str, bool]   = {p: p in _AUTO_UNLOCK_NAMES for p in PLANET_UNLOCK_ORDER}
        self._desired["RYLLUS"]          = True   # temporary: enforced until opening cutscene ends
        self._enforce_active: bool       = True
        self._ryllus_released: bool      = False
        self._infobot_planets: set[str]  = set()
        self._task: asyncio.Task | None  = None


    async def read(self) -> bool:
        async with self._lock:
            data = self.pine.read_bytes(PLANET_UNLOCK_BASE, _COUNT)
        for i, name in enumerate(PLANET_UNLOCK_ORDER):
            self.unlocked[name] = data[i] == PlanetLockValue.UNLOCKED
        return True

    async def apply(self) -> bool:
        """Write _desired state to memory."""
        data = bytes(
            PlanetLockValue.UNLOCKED if self._desired[name] else PlanetLockValue.LOCKED
            for name in PLANET_UNLOCK_ORDER
        )
        async with self._lock:
            self.pine.write_bytes(PLANET_UNLOCK_BASE, data)
        return True

    async def _enforce_desired(self) -> None:
        """Re-write any planet whose memory value differs from _desired."""
        if not self._enforce_active:
            return
        if any(self.unlocked[n] != self._desired[n] for n in PLANET_UNLOCK_ORDER):
            await self.apply()
            for name in PLANET_UNLOCK_ORDER:
                self.unlocked[name] = self._desired[name]

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        while True:
            prev = dict(self.unlocked)
            await self.read()
            await self._enforce_desired()
            for name in PLANET_UNLOCK_ORDER:
                if self.unlocked[name] and not prev[name]:
                    self.on_planet_unlocked(name)
                elif not self.unlocked[name] and prev[name]:
                    self.on_planet_locked(name)
            await asyncio.sleep(interval / 1000)


    async def activate(self, interval: int, callback: Callable[[int, int], None]) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self.poll(0, interval, callback))

    async def deactivate(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None


    def set_unlocked_planets(self, planets: set[str]) -> None:
        """Update desired state from AP-received infobots.

        planets — uppercase planet names from PLANET_UNLOCK_ORDER that have been
                  unlocked via infobot items.  Auto-unlock planets are always forced
                  True regardless of this set.
        """
        self._infobot_planets = set(planets)
        for name in PLANET_UNLOCK_ORDER:
            self._desired[name] = name in planets or name in _AUTO_UNLOCK_NAMES
        if not self._ryllus_released:
            self._desired["RYLLUS"] = True

    def on_ryllus_cutscene_ended(self) -> None:
        """Called when the Pokitaru opening cutscene ends (0x2CC522 → 0x00).

        Releases the temporary Ryllus enforcement; Ryllus reverts to its infobot state.
        """
        if self._ryllus_released:
            return
        self._ryllus_released = True
        self._desired["RYLLUS"] = "RYLLUS" in self._infobot_planets

    def reset_session(self) -> None:
        """Reset temporary Ryllus state for a fresh PINE session (called on disconnect)."""
        self._ryllus_released = False
        self._desired["RYLLUS"] = True

    def unlock(self, planet: str) -> None:
        """Mark a planet as desired-unlocked. Takes effect on the next poll tick."""
        self._desired[planet] = True

    def lock(self, planet: str) -> None:
        """Mark a planet as desired-locked (has no effect on auto-unlock planets)."""
        if planet not in _AUTO_UNLOCK_NAMES:
            self._desired[planet] = False

    def is_unlocked(self, planet: str) -> bool:
        return self._desired.get(planet, False)


    def on_planet_unlocked(self, _planet: str) -> None:
        """Fired when a planet transitions from locked to unlocked."""
        del _planet

    def on_planet_locked(self, _planet: str) -> None:
        """Fired when a planet transitions from unlocked to locked."""
        del _planet


    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanetUnlockState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        count = sum(self.unlocked.values())
        return f"PlanetUnlockState(unlocked={count}/{_COUNT})"
