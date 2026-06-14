from __future__ import annotations

from collections.abc import Callable

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.locations.challenges import (
    ALL_CLANK_ADDRESS_MAP,
    CHALLENGE_ADDRESS_MAP,
    COUNT_BASED_CHALLENGE_ADDRS,
    DAYNI_CLANK_UNLOCK_ADDR,
    DAYNI_CLANK_UNLOCK_BYTES,
    METALIS_CLANK_UNLOCK_ADDR,
    METALIS_CLANK_UNLOCK_BYTES,
    SKYBOARD_ADDRESS_MASK_MAP,
)
from ..structs.challenges import ClankChallengeStruct, SkyboardStruct


class ClankChallengeState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                     = set()
        self._metalis_counts: dict[int, int]          = {}
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._all_challenges: bool                    = False
        self._enabled:        bool                    = True

    def set_mode(self, mode: int) -> None:
        self._enabled       = mode >= 1
        self._all_challenges = mode >= 2

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        if self._enabled:
            self.accessor.on_struct_change(ClankChallengeStruct, self._on_region_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ClankChallengeStruct, self._on_region_change)

    def _on_region_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        addr_map = ALL_CLANK_ADDRESS_MAP if self._all_challenges else CHALLENGE_ADDRESS_MAP
        for addr, name in addr_map.items():
            if name in self._completed:
                continue
            raw = self.accessor.read_raw(addr, 1)
            count = raw[0] if raw else 0
            if addr in COUNT_BASED_CHALLENGE_ADDRS:
                prev = self._metalis_counts.get(addr, 0)
                self._metalis_counts[addr] = count
                if count > prev:
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_challenge_completed(name)
            else:
                if count >= 2:
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_challenge_completed(name)

    def sync(self) -> None:
        for addr, name in ALL_CLANK_ADDRESS_MAP.items():
            raw = self.accessor.read_raw(addr, 1)
            count = raw[0] if raw else 0
            if addr in COUNT_BASED_CHALLENGE_ADDRS:
                self._metalis_counts[addr] = count
                if count > 0:
                    self._completed.add(name)
            else:
                if count >= 2:
                    self._completed.add(name)

    def write_unlocks(self) -> None:
        if not self._enabled:
            return
        self.accessor.write_raw(METALIS_CLANK_UNLOCK_ADDR, METALIS_CLANK_UNLOCK_BYTES)
        self.accessor.write_raw(DAYNI_CLANK_UNLOCK_ADDR, DAYNI_CLANK_UNLOCK_BYTES)

    def write_defaults(self) -> None:
        if not self._enabled:
            return
        self.write_unlocks()
        if self._all_challenges:
            return  # don't preset values — every completion is a check
        for addr in ALL_CLANK_ADDRESS_MAP:
            if addr not in COUNT_BASED_CHALLENGE_ADDRS:
                raw = self.accessor.read_raw(addr, 1)
                if raw and raw[0] == 0:
                    self.accessor.write_raw(addr, b"\x01")

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in ALL_CLANK_ADDRESS_MAP.values()
        )

    def on_challenge_completed(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        return f"ClankChallengeState(completed={len(self._completed)}/{len(ALL_CLANK_ADDRESS_MAP)})"

class SkyboardChallengeState(BaseState):
    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                     = set()
        self._on_location_check: Callable[[str], None] = lambda _: None
        self._enabled: bool                           = True

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        if self._enabled:
            self.accessor.on_struct_change(SkyboardStruct, self._on_region_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(SkyboardStruct, self._on_region_change)

    def _on_region_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
            if name not in self._completed:
                val = self.accessor.read_raw(addr, 1)
                if val and (val[0] & mask):
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_race_completed(name)

    def sync(self) -> None:
        for (addr, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items():
            val = self.accessor.read_raw(addr, 1)
            if val and (val[0] & mask):
                self._completed.add(name)

    def write_defaults(self) -> None:
        pass

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in SKYBOARD_ADDRESS_MASK_MAP.values()
        )

    def on_race_completed(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        return f"SkyboardChallengeState(completed={len(self._completed)}/{len(SKYBOARD_ADDRESS_MASK_MAP)})"
