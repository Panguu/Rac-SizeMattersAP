from __future__ import annotations

from enum import IntEnum

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.planet_unlock import PLANET_UNLOCKS
from ..structs.planet_progress import PlanetProgressStruct

PLANET_UNLOCK_BASE: int = PlanetProgressStruct.BASE_ADDRESS

class PlanetLockValue(IntEnum):
    LOCKED   = 0x00
    UNLOCKED = 0x03

PLANET_UNLOCK_ORDER: list[str] = list(PlanetProgressStruct.PLANET_NAME_ORDER)

_AUTO_UNLOCK_NAMES: frozenset[str] = frozenset({
    "POKITARU",
    "DREAMTIME",
    "INSIDE_CLANK",
})

# Planets auto-unlocked in memory but gated behind different AP progress.
# Maps auto-unlock planet → the planet whose AP status we check for vendor access.
_VENDOR_PLANET_GATE: dict[str, str] = {
    "DREAMTIME":    "OUTPOST_OMEGA",  # reachable only once Outpost Omega infobot received
    "INSIDE_CLANK": "DAYNI_MOON",    # reachable only once Dayni Moon infobot received
}

_COUNT = len(PLANET_UNLOCK_ORDER)

class PlanetUnlockState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.unlocked: dict[str, bool] = dict.fromkeys(PLANET_UNLOCK_ORDER, False)
        self._desired: dict[str, bool] = {p: p in _AUTO_UNLOCK_NAMES for p in PLANET_UNLOCK_ORDER}
        self._desired["RYLLUS"]        = True
        self._enforce_active: bool     = True
        self._ryllus_released: bool    = False
        self._infobot_planets: set[str] = set()

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(PlanetProgressStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(PlanetProgressStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        instance = PlanetProgressStruct.from_bytes(new_bytes)
        prev = dict(self.unlocked)
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER):
            self.unlocked[name] = getattr(instance, field) == PlanetLockValue.UNLOCKED

        self._enforce_desired()

        for name in PLANET_UNLOCK_ORDER:
            if self.unlocked[name] and not prev[name]:
                self.on_planet_unlocked(name)
            elif not self.unlocked[name] and prev[name]:
                self.on_planet_locked(name)

    def sync(self) -> None:
        instance = self.accessor.read_struct(PlanetProgressStruct)
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER):
            self.unlocked[name] = getattr(instance, field) == PlanetLockValue.UNLOCKED
        self._enforce_desired()

    def _enforce_desired(self) -> None:
        if not self._enforce_active:
            return
        if any(self.unlocked[n] != self._desired[n] for n in PLANET_UNLOCK_ORDER):
            self._write_desired()
            for name in PLANET_UNLOCK_ORDER:
                self.unlocked[name] = self._desired[name]

    def _write_desired(self) -> None:
        instance = PlanetProgressStruct()
        for field, name in zip(PlanetProgressStruct.PLANET_ORDER, PLANET_UNLOCK_ORDER):
            unlock_val = PlanetLockValue.UNLOCKED if self._desired[name] else PlanetLockValue.LOCKED
            setattr(instance, field, unlock_val)
            pu = PLANET_UNLOCKS.get(name)
            if pu is not None:
                state_val = max(int(unlock_val), pu.default_state)
                self.accessor.write_raw(pu.state_addr, bytes([state_val]))
        self.accessor.write_struct(instance)

    def set_unlocked_planets(self, planets: set[str]) -> None:
        self._infobot_planets = set(planets)
        for name in PLANET_UNLOCK_ORDER:
            self._desired[name] = name in planets or name in _AUTO_UNLOCK_NAMES
        if not self._ryllus_released:
            self._desired["RYLLUS"] = True

    def on_ryllus_cutscene_ended(self) -> None:
        if self._ryllus_released:
            return
        self._ryllus_released = True
        self._desired["RYLLUS"] = "RYLLUS" in self._infobot_planets

    def reset_session(self) -> None:
        self._ryllus_released = False
        self._desired["RYLLUS"] = True

    def unlock(self, planet: str) -> None:
        self._desired[planet] = True

    def lock(self, planet: str) -> None:
        if planet not in _AUTO_UNLOCK_NAMES:
            self._desired[planet] = False

    def is_unlocked(self, planet: str) -> bool:
        return self._desired.get(planet, False)

    def is_vendor_accessible(self, planet: str) -> bool:
        gate = _VENDOR_PLANET_GATE.get(planet, planet)
        return self._desired.get(gate, False)

    def on_planet_unlocked(self, _planet: str) -> None:
        del _planet

    def on_planet_locked(self, _planet: str) -> None:
        del _planet

    def __repr__(self) -> str:
        count = sum(self.unlocked.values())
        return f"PlanetUnlockState(unlocked={count}/{_COUNT})"
