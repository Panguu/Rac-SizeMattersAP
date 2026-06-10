from __future__ import annotations

from collections.abc import Callable

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.locations.armour_set_checks import ARMOUR_SET_CHECK_MASKS
from ..structs.armour import ArmourSetCollectedStruct


class ArmourSetCollectedState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._prev:      int       = 0
        self._completed: set[str]  = set()
        self.on_location_check: Callable[[str], None] = lambda _: None

    def on_exit(self) -> None:
        self.on_location_check = lambda _: None

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(ArmourSetCollectedStruct, self._on_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ArmourSetCollectedStruct, self._on_change)

    def _on_change(self, _address: int, new_bytes: bytes) -> None:
        byte0 = new_bytes[0] if new_bytes else 0
        byte1 = new_bytes[1] if len(new_bytes) > 1 else 0
        current = byte0 | (byte1 << 8)
        if current == self._prev:
            return
        self._prev = current
        self._check(current)

    def _check(self, value: int) -> None:
        for name, mask in ARMOUR_SET_CHECK_MASKS.items():
            if name not in self._completed and (value & mask) == mask:
                self._completed.add(name)
                self.on_location_check(name)

    def sync(self) -> None:
        raw = self.accessor.read_raw(ArmourSetCollectedStruct.BASE_ADDRESS, 2)
        byte0 = raw[0] if raw else 0
        byte1 = raw[1] if len(raw) > 1 else 0
        self._prev = byte0 | (byte1 << 8)
        self._check(self._prev)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations if name in ARMOUR_SET_CHECK_MASKS
        )

    def __repr__(self) -> str:
        return f"ArmourSetCollectedState(prev=0x{self._prev:02X}, completed={len(self._completed)})"
