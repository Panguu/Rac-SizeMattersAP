from __future__ import annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.menu import MenuStruct, PreloadMenuStruct

logger = logging.getLogger("CommonClient")

if TYPE_CHECKING:
    from .planets import PlanetState
    from .vendor import VendorState

class MenuStateValue(IntEnum):
    CLOSED         = 0x00
    PAUSE_MENU     = 0x03
    WEAPONS_VENDOR = 0x09
    MOD_VENDOR     = 0x0E
    PLANET_MENU    = 0x10
    PRELOAD_READY  = 0x13

class MenuState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.current: MenuStateValue       = MenuStateValue.CLOSED
        self._last_preload: MenuStateValue = MenuStateValue.CLOSED
        self._vendor: VendorState | None   = None
        self._planet: PlanetState | None   = None

    def bind(self, vendor: VendorState, planet: PlanetState) -> None:
        self._vendor = vendor
        self._planet = planet

    def unbind(self) -> None:
        self._vendor = None
        self._planet = None

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        if self._vendor and self.is_vendor:
            self._vendor.on_menu_close()
            self._vendor.deactivate()
        self.current       = MenuStateValue.CLOSED
        self._last_preload = MenuStateValue.CLOSED
        self.unbind()

    def _register_handlers(self) -> None:
        menu_cls    = self._menu_struct()
        preload_cls = self._preload_struct()
        if menu_cls is not None:
            self.accessor.on_struct_change(menu_cls, self._on_menu_change)
        if preload_cls is not None:
            self.accessor.on_struct_change(preload_cls, self._on_preload_change)

    def _unregister_handlers(self) -> None:
        menu_cls    = self._menu_struct()
        preload_cls = self._preload_struct()
        if menu_cls is not None:
            self.accessor.remove_struct_handler(menu_cls, self._on_menu_change)
        if preload_cls is not None:
            self.accessor.remove_struct_handler(preload_cls, self._on_preload_change)

    def _menu_struct(self) -> type[MenuStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, MenuStruct) and cls is not MenuStruct:
                return cls
        return None

    def _preload_struct(self) -> type[PreloadMenuStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, PreloadMenuStruct) and cls is not PreloadMenuStruct:
                return cls
        return None

    def _on_menu_change(self, address: int, new_bytes: bytes) -> None:
        del address
        raw = new_bytes[0] if new_bytes else 0
        try:
            new_state = MenuStateValue(raw)
        except ValueError:
            return
        prev = self.current
        self.current = new_state
        if new_state != prev:
            self._on_transition(prev, new_state)

    def _on_preload_change(self, address: int, new_bytes: bytes) -> None:
        del address
        raw = new_bytes[0] if new_bytes else 0
        try:
            value = MenuStateValue(raw)
        except ValueError:
            value = MenuStateValue.CLOSED
        prev = self._last_preload
        self._last_preload = value

        if value == MenuStateValue.PRELOAD_READY and prev != MenuStateValue.PRELOAD_READY:
            if self._vendor is not None:
                self._vendor.start_menu_preload()
            if self._planet is not None:
                self._planet.on_menu_preload()
        elif prev == MenuStateValue.PRELOAD_READY and value != MenuStateValue.PRELOAD_READY:
            if self._planet is not None:
                self._planet.on_menu_preload_exit()

    def _on_transition(self, prev: MenuStateValue, current: MenuStateValue) -> None:
        if self._vendor is None:
            return
        was_vendor = prev    in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)
        is_vendor  = current in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR)

        if is_vendor and not was_vendor:
            logger.info(f"[RAC] MenuState: vendor opened ({current.name}).")
            self._vendor.exit_menu_preload()
            self._vendor.activate(current)
            self._vendor.on_menu_open()
            if self._planet is not None:
                self._planet.on_menu_open()
        elif was_vendor and not is_vendor:
            logger.info(f"[RAC] MenuState: vendor closed ({prev.name} → {current.name}).")
            self._vendor.on_menu_close()
            self._vendor.deactivate()
            if self._planet is not None:
                self._planet.on_menu_close()

    def sync(self) -> None:
        pass

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

    def __repr__(self) -> str:
        return f"MenuState(current={self.current.name})"
