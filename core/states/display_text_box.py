import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

if TYPE_CHECKING:
    from worlds.rac_size_matters.core.data.addresses import DisplayedTextBox


class DisplayTextBoxState(State):
    """
    Global vendor proximity tracker. Polls the planet-specific is_visible
    address and fires hooks when the vendor prompt appears or disappears.

    vendor_value is the int16 value written to is_visible when the vendor
    text box is active — it differs per planet.

    Activated per-planet by PlanetState.on_enter() with that planet's config.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self._is_visible_addr: int | None = None
        self._vendor_value: int           = 0
        self.is_vendor_prompt: bool       = False
        self._task: asyncio.Task | None   = None

    # --- State interface ---

    async def read(self) -> bool:
        if self._is_visible_addr is None:
            return False
        async with self._lock:
            raw = self.pine.read_int16(self._is_visible_addr)
        self.is_vendor_prompt = raw == self._vendor_value
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        last: bool | None = None
        while True:
            async with self._lock:
                raw = self.pine.read_int16(self._is_visible_addr)
            current = raw == self._vendor_value
            if last is not None and current != last:
                if current:
                    self.on_vendor_prompt_shown()
                else:
                    self.on_vendor_prompt_hidden()
            self.is_vendor_prompt = current
            last = current
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(self, config: "DisplayedTextBox", interval: int) -> None:
        """Start polling. Called from PlanetState.on_enter()."""
        if self._task is not None:
            return
        self._is_visible_addr = config.is_visible
        self._vendor_value    = config.vendor_value
        self._task = asyncio.create_task(self.poll(0, interval, lambda *_: None))

    async def deactivate(self) -> None:
        """Stop polling. Called from PlanetState.on_exit()."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self.is_vendor_prompt = False

    # --- Hooks ---

    def on_vendor_prompt_shown(self) -> None:
        """Fired when the player enters vendor range. This is the menu preload signal."""

    def on_vendor_prompt_hidden(self) -> None:
        """Fired when the player leaves vendor range."""

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DisplayTextBoxState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        return f"DisplayTextBoxState(vendor_prompt={self.is_vendor_prompt})"
