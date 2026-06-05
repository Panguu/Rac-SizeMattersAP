from __future__ import annotations

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.quick_select import QuickSelectStruct

_ZERO_BYTES = bytes(4 * len(QuickSelectStruct.SLOT_ORDER))


class QuickSelectState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._snapshot: dict[str, int] = dict.fromkeys(QuickSelectStruct.SLOT_ORDER, 0)
        self._polling = False

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        self._stop_polling()

    # Starts frozen — polling only begins after zero() is called on first planet load.
    def _register_handlers(self) -> None:
        pass

    def _unregister_handlers(self) -> None:
        self._stop_polling()

    def freeze(self) -> None:
        """Stop updating the snapshot (planet transition or vendor open)."""
        self._stop_polling()

    def unfreeze(self) -> None:
        """Resume snapshot updates."""
        self._start_polling()

    def _start_polling(self) -> None:
        if not self._polling:
            self.accessor.on_struct_change(QuickSelectStruct, self._on_change)
            self._polling = True

    def _stop_polling(self) -> None:
        if self._polling:
            self.accessor.remove_struct_handler(QuickSelectStruct, self._on_change)
            self._polling = False

    def _on_change(self, _address: int, new_bytes: bytes) -> None:
        instance = QuickSelectStruct.from_bytes(new_bytes)
        for name in QuickSelectStruct.SLOT_ORDER:
            self._snapshot[name] = getattr(instance, name)

    def sync(self) -> None:
        instance = self.accessor.read_struct(QuickSelectStruct)
        for name in QuickSelectStruct.SLOT_ORDER:
            self._snapshot[name] = getattr(instance, name)

    def zero(self) -> None:
        """Zero all slots in memory and snapshot, then start polling."""
        self.accessor.write_raw(QuickSelectStruct.BASE_ADDRESS, _ZERO_BYTES)
        for name in QuickSelectStruct.SLOT_ORDER:
            self._snapshot[name] = 0
        self._start_polling()

    def apply(self) -> None:
        """Write the current snapshot back to memory, zeroing any empty slots."""
        if not self._polling:
            return
        instance = QuickSelectStruct()
        for name in QuickSelectStruct.SLOT_ORDER:
            setattr(instance, name, self._snapshot[name])
        self.accessor.write_struct(instance)
