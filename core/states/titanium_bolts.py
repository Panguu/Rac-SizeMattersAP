from __future__ import annotations

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.locations.titanium_bolts import (
    BOLT_BY_PLANET_AND_DELTA,
    TITANIUM_BOLTS,
    TitaniumBolt,
)
from ..structs.titanium_bolts import TitaniumBoltStruct

__all__ = [
    "TitaniumBolt",
    "TITANIUM_BOLTS",
    "BOLT_BY_PLANET_AND_DELTA",
    "TitaniumBoltState",
]


class TitaniumBoltState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._poll_last:   int = 0
        self._synced_mask: int = 0

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(TitaniumBoltStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(TitaniumBoltStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        current = int.from_bytes(new_bytes[:5], "little")
        delta   = current - self._poll_last
        self._poll_last = current
        if delta > 0 and (delta & (delta - 1)) == 0:
            self.on_bolt_delta(delta)

    def sync(self) -> None:
        raw     = self.accessor.read_raw(TitaniumBoltStruct.BASE_ADDRESS, 5)
        current = int.from_bytes(raw, "little") if raw else 0
        self._poll_last = current
        new_val = current | self._synced_mask
        if new_val != current:
            self.accessor.write_raw(TitaniumBoltStruct.BASE_ADDRESS, new_val.to_bytes(5, "little"))

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        mask = 0
        for loc_name, bolt in TITANIUM_BOLTS.items():
            if loc_name in checked_location_names:
                mask |= bolt.delta
        self._synced_mask = mask

    def on_bolt_delta(self, _delta: int) -> None:
        del _delta

    def __repr__(self) -> str:
        collected = bin(self._poll_last).count("1")
        return f"TitaniumBoltState(collected={collected}/{len(TITANIUM_BOLTS)})"
