from __future__ import annotations

import struct
from collections.abc import Callable

from CommonClient import logger

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.addresses import PLANET_MISSION_ADDRESSES
from ..data.locations.missions import PRESET_MISSION_BITS, VALIDATED_MISSION_MAP
from ..structs.missions import MissionsStruct

# Reverse map: address -> planet name for log messages
_PLANET_BY_ADDR: dict[int, str] = {v: k for k, v in PLANET_MISSION_ADDRESSES.items()}


class MissionsState(BaseState):
    """Watches the per-planet 2-byte mission progress values, logs any raw value
    change, and fires a callback when a known mission's complete value is reached."""

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._completed: set[str]                        = set()
        self._snapshots: dict[int, int]                  = {}   # addr -> last seen value
        self._on_mission_complete: Callable[[str], None] = lambda _: None

    def set_mission_complete_callback(self, cb: Callable[[str], None]) -> None:
        self._on_mission_complete = cb

    def on_exit(self) -> None:
        self._on_mission_complete = lambda _: None

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(MissionsStruct, self._on_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(MissionsStruct, self._on_change)

    def _on_change(self, address: int, new_bytes: bytes) -> None:
        del address, new_bytes
        for addr, planet in _PLANET_BY_ADDR.items():
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            prev  = self._snapshots.get(addr)
            if prev is not None and value != prev:
                logger.debug(
                    f"[RAC] Mission change  {planet:<16}  {addr:#010x}  "
                    f"{prev:#06x} -> {value:#06x}  (XOR {value ^ prev:#06x})"
                )
            self._snapshots[addr] = value

        self._check_all()

    def _check_all(self) -> None:
        for (addr, mask), name in VALIDATED_MISSION_MAP.items():
            if name in self._completed:
                continue
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            if value & mask:
                self._completed.add(name)
                self._on_mission_complete(name)

    def preset_missions(self) -> None:
        """OR preset bits into memory and mark them done so they never fire as checks."""
        for addr, mask in PRESET_MISSION_BITS:
            raw = self.accessor.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                continue
            value = struct.unpack_from("<H", raw)[0]
            self.accessor.write_raw(addr, struct.pack("<H", value | mask))

    def sync(self) -> None:
        for addr in _PLANET_BY_ADDR:
            raw = self.accessor.read_raw(addr, 2)
            if raw and len(raw) >= 2:
                self._snapshots[addr] = struct.unpack_from("<H", raw)[0]
        self._check_all()

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self._completed.update(
            name for name in checked_locations
            if name in VALIDATED_MISSION_MAP.values()
        )

    def __repr__(self) -> str:
        total = len(VALIDATED_MISSION_MAP)
        return f"MissionsState(completed={len(self._completed)}/{total})"
