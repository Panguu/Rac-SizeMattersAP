import asyncio
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine


class MenuStateValue(IntEnum):
    CLOSED         = 0x00
    PAUSE_MENU     = 0x03
    WEAPONS_VENDOR = 0x09
    MOD_VENDOR     = 0x0E
    PLANET_MENU    = 0x10
    PRELOAD_READY  = 0x13

if TYPE_CHECKING:
    from worlds.rac_size_matters.core.states.planets import PlanetState
    from worlds.rac_size_matters.core.states.vendor import VendorState


class MenuState(State):
    """
    Global coordinator for menu state. Polls the planet-specific menu address
    and drives VendorState when a vendor menu is detected.

    Activated per-planet by PlanetState.on_enter() with that planet's addresses.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.current: MenuStateValue     = MenuStateValue.CLOSED
        self._preload_addr: int | None   = None
        self._vendor: VendorState | None = None
        self._planet: PlanetState | None = None
        self._task: asyncio.Task | None  = None

    # --- State interface ---

    async def read(self) -> bool:
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: MenuStateValue | None = None
        last_preload: int = 0
        while True:
            async with self._lock:
                raw     = self.pine.read_int8(mem_address)
                preload = self.pine.read_int8(self._preload_addr) if self._preload_addr else 0
            try:
                current = MenuStateValue(raw)
            except ValueError:
                current = self.current

            preload_became_ready = (
                preload == MenuStateValue.PRELOAD_READY
                and last_preload != MenuStateValue.PRELOAD_READY
            )

            if last is not None and current != last:
                callback(int(last), int(current))
                self._on_transition(last, current)

            if preload_became_ready and not self.is_vendor:
                if self._vendor:
                    self._vendor.start_menu_preload()
                if self._planet:
                    asyncio.create_task(self._planet.on_menu_preload())

            self.current = current
            last = current
            last_preload = preload
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(
        self,
        menu_addr: int,
        preload_addr: int,
        vendor: "VendorState",
        planet: "PlanetState",
        interval: int,
        callback: Callable[[int, int], None],
    ) -> None:
        """Start polling. Called from PlanetState.on_enter()."""
        if self._task is not None:
            return
        self._preload_addr = preload_addr
        self._vendor = vendor
        self._planet = planet
        self._task = asyncio.create_task(self.poll(menu_addr, interval, callback))

    async def deactivate(self) -> None:
        """Stop polling. Called from PlanetState.on_exit()."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        if self._vendor and self.is_vendor:
            self._vendor.on_menu_close()
            self._vendor.deactivate()
        self.current = MenuStateValue.CLOSED
        self._vendor = None
        self._planet = None

    # --- Transition handler ---

    def _on_transition(self, prev: MenuStateValue, current: MenuStateValue) -> None:
        if self._vendor is None:
            return
        was_vendor = prev    in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

        if is_vendor and not was_vendor:
            self._vendor.exit_menu_preload()
            self._vendor.activate(current)
            self._vendor.on_menu_open()
            if self._planet:
                asyncio.create_task(self._planet.on_menu_open())
        elif was_vendor and not is_vendor:
            self._vendor.on_menu_close()
            self._vendor.deactivate()
            if self._planet:
                asyncio.create_task(self._planet.on_menu_close())

    # --- Properties ---

    @property
    def is_vendor(self) -> bool:
        return self.current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

    @property
    def is_weapons_vendor(self) -> bool:
        return self.current == MenuStateValue.WEAPONS_VENDOR

    @property
    def is_mod_vendor(self) -> bool:
        return self.current == MenuStateValue.MOD_VENDOR

    @property
    def is_pause_menu(self) -> bool:
        return self.current == MenuStateValue.PAUSE_MENU

    @property
    def is_planet_menu(self) -> bool:
        return self.current == MenuStateValue.PLANET_MENU

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MenuState):
            return NotImplemented
        return self.current == other.current

    def __repr__(self) -> str:
        return f"MenuState(current={self.current.name})"
