import asyncio
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

if TYPE_CHECKING:
    from worlds.rac_size_matters.core.states.menu import MenuStateValue


class VendorSessionState(IntEnum):
    CLOSED     = 0
    PRELOADING = 1
    OPEN       = 2


class VendorState(State):
    """
    Global vendor session tracker. Lifecycle is driven entirely by MenuState —
    activate()/deactivate() are called when MenuState detects a vendor opening or closing.
    Override the on_* hooks to add vendor-specific logic.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.session: VendorSessionState = VendorSessionState.CLOSED
        self.vendor_type: MenuStateValue | None = None
        self.vendor_locations: dict[str, bool] = {}

    # --- State interface ---

    async def read(self) -> bool:
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback  # polling driven by MenuState, not this instance
        while True:
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle (called by MenuState) ---

    def activate(self, vendor_type: "MenuStateValue") -> None:
        """Called by MenuState when a vendor menu opens."""
        self.vendor_type = vendor_type
        self.session = VendorSessionState.OPEN

    def deactivate(self) -> None:
        """Called by MenuState when the vendor menu closes."""
        self.vendor_type = None
        self.session = VendorSessionState.CLOSED

    # --- Hooks (override per use case) ---

    def start_menu_preload(self) -> None:
        """Fired by MenuState when PRELOAD_READY is detected before the vendor opens."""
        self.session = VendorSessionState.PRELOADING

    def exit_menu_preload(self) -> None:
        """Fired by MenuState when the vendor menu transitions from preload to open."""

    def on_menu_open(self) -> None:
        """Fired by MenuState when the vendor menu is fully open."""

    def on_menu_close(self) -> None:
        """Fired by MenuState when the vendor menu closes."""

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        """Rebuild vendor_locations from AP-confirmed purchase locations."""
        self.vendor_locations.clear()
        for loc_name in checked_location_names:
            if loc_name.startswith("Purchase "):
                self.vendor_locations[loc_name] = True

    def on_purchase(self, kind: str, name: str, slot: str | None) -> None:
        """Fired when a weapon, gadget, or mod purchase is detected."""

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VendorState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        t = self.vendor_type.name if self.vendor_type else "None"
        return f"VendorState(session={self.session.name}, type={t})"
