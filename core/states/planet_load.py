from __future__ import annotations

from collections.abc import Callable

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.planet_load import PlanetLoadStruct


class PlanetLoadState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._start_prev:    int = 0
        self._complete_prev: int = 0

        self.on_start_load:    Callable[[], None] = lambda: None
        self.on_load_complete: Callable[[], None] = lambda: None

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(PlanetLoadStruct, self._on_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(PlanetLoadStruct, self._on_change)

    def _on_change(self, _address: int, new_bytes: bytes) -> None:
        instance = PlanetLoadStruct.from_bytes(new_bytes)

        if instance.start_load and not self._start_prev:
            self.on_start_load()

        if instance.load_complete and not self._complete_prev:
            self.on_load_complete()

        self._start_prev    = instance.start_load
        self._complete_prev = instance.load_complete

    def sync(self) -> None:
        instance            = self.accessor.read_struct(PlanetLoadStruct)
        self._start_prev    = instance.start_load
        self._complete_prev = instance.load_complete
