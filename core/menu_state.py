from __future__ import annotations

from enum import IntEnum

from ..pypine.pypine.pine import Pine
from .data import BY_ID
from .data.addresses import PRELOAD_MENU_ADDR_BY_PLANET_ID


class MenuStateValue(IntEnum):
    CLOSED         = 0x00
    PAUSE_MENU     = 0x03
    WEAPONS_VENDOR = 0x09
    MOD_VENDOR     = 0x0E
    PLANET_MENU    = 0x10
    PRELOAD_READY  = 0x13


class MenuState:
    """Single-read snapshot of the current menu and preload state for a planet."""

    def __init__(self, value: int, preload: int, menu_addr: int | None, preload_addr: int | None) -> None:
        self._value       = value
        self._preload     = preload
        self._menu_addr   = menu_addr
        self._preload_addr = preload_addr

    @classmethod
    def read(cls, ipc: Pine, planet_id: int) -> MenuState:
        planet_obj   = BY_ID.get(planet_id)
        menu_addr    = planet_obj.menu_addr if planet_obj else None
        preload_addr = PRELOAD_MENU_ADDR_BY_PLANET_ID.get(planet_id)
        value   = ipc.read_int8(menu_addr)    if menu_addr    else 0
        preload = ipc.read_int8(preload_addr) if preload_addr else 0
        return cls(value, preload, menu_addr, preload_addr)

    def write(self, ipc: Pine, state: MenuStateValue) -> bool:
        """Write state to the preload address then the menu address."""
        if not self._menu_addr:
            return False
        ipc.write_int8(self._menu_addr, state)
        return True

    # ── raw ───────────────────────────────────────────────────────────────────

    @property
    def raw(self) -> int:
        return self._value

    # ── preload ───────────────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        """True when the vendor area is preloaded and interactable."""
        return self._preload == MenuStateValue.PRELOAD_READY

    # ── named states ─────────────────────────────────────────────────────────

    @property
    def is_weapons_vendor(self) -> bool:
        return self._value == MenuStateValue.WEAPONS_VENDOR

    @property
    def is_mod_vendor(self) -> bool:
        return self._value == MenuStateValue.MOD_VENDOR

    @property
    def is_vendor(self) -> bool:
        return self._value in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

    @property
    def is_planet_menu(self) -> bool:
        return self._value == MenuStateValue.PLANET_MENU

    @property
    def is_pause_menu(self) -> bool:
        return self._value == MenuStateValue.PAUSE_MENU

    @property
    def is_open(self) -> bool:
        return self._value in MenuStateValue._value2member_map_

    # ── repr ──────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        try:
            name = MenuStateValue(self._value).name
        except ValueError:
            name = f"UNKNOWN({self._value:#04x})"
        ready = " ready" if self.is_ready else ""
        return f"MenuState({name}{ready})"
