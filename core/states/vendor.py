from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap

if TYPE_CHECKING:
    from .menu import MenuStateValue

class VendorSessionState(IntEnum):
    CLOSED     = 0
    PRELOADING = 1
    OPEN       = 2

class VendorState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.session: VendorSessionState        = VendorSessionState.CLOSED
        self.vendor_type: MenuStateValue | None = None
        self.vendor_locations: dict[str, bool]  = {}

    def activate(self, vendor_type: MenuStateValue) -> None:
        self.vendor_type = vendor_type
        self.session = VendorSessionState.OPEN

    def deactivate(self) -> None:
        self.vendor_type = None
        self.session = VendorSessionState.CLOSED

    def start_menu_preload(self) -> None:
        self.session = VendorSessionState.PRELOADING

    def exit_menu_preload(self) -> None:
        pass

    def on_menu_open(self) -> None:
        pass

    def on_menu_close(self) -> None:
        pass

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        self.vendor_locations.clear()
        for loc_name in checked_location_names:
            if loc_name.startswith("Purchase "):
                self.vendor_locations[loc_name] = True

    def on_purchase(self, kind: str, name: str, slot: str | None) -> None:
        del kind, name, slot

    def __repr__(self) -> str:
        t = self.vendor_type.name if self.vendor_type else "None"
        return f"VendorState(session={self.session.name}, type={t})"
