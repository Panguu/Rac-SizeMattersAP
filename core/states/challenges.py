from __future__ import annotations

from collections.abc import Callable

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.locations.challenges import ALL_CLANK_ADDRESS_MAP, SKYBOARD_ADDRESS_MASK_MAP, SKYBOARD_UNLOCK_MASK
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
        self._on_location_check: Callable[[str], None] = lambda _: None

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(ClankChallengeStruct, self._on_region_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ClankChallengeStruct, self._on_region_change)

    def _on_region_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        for addr, name in ALL_CLANK_ADDRESS_MAP.items():
            if name not in self._completed:
                val = self.accessor.read_raw(addr, 1)
                if val and val[0] >= 2:
                    self._completed.add(name)
                    self._on_location_check(name)
                    self.on_challenge_completed(name)

    def sync(self) -> None:
        for addr, name in ALL_CLANK_ADDRESS_MAP.items():
            val = self.accessor.read_raw(addr, 1)
            if val and val[0] >= 2:
                self._completed.add(name)

    def write_defaults(self) -> None:
        for addr in ALL_CLANK_ADDRESS_MAP:
            val = self.accessor.read_raw(addr, 1)
            if val and val[0] == 0:
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

    def set_location_check_callback(self, cb: Callable[[str], None]) -> None:
        self._on_location_check = cb

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        self._on_location_check = lambda _: None

    def _register_handlers(self) -> None:
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
        for addr, full_mask in SKYBOARD_UNLOCK_MASK.items():
            val = self.accessor.read_raw(addr, 1)
            current = val[0] if val else 0
            if current | full_mask != current:
                self.accessor.write_raw(addr, bytes([current | full_mask]))

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in SKYBOARD_ADDRESS_MASK_MAP.values()
        )

    def on_race_completed(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        return f"SkyboardChallengeState(completed={len(self._completed)}/{len(SKYBOARD_ADDRESS_MASK_MAP)})"
