from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.addresses import MENU_ADDR_BY_PLANET_ID
from ..data.armour import ArmourPiece
from ..data.cutscenes import arm_cutscenes, suppress_disabled_cutscenes
from ..structs.game_status import GameStatusStruct

if TYPE_CHECKING:
    from ..data.addresses import DisplayedTextBox
    from .armour import ArmourState
    from .display_text_box import DisplayTextBoxState, DisplayedTextBoxState
    from .menu import MenuState
    from .player import PlayerState
    from .vendor import VendorState
    from .weapon import WeaponState

logger = logging.getLogger("CommonClient")

_PIECE_ORDER = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]


@dataclass(frozen=True)
class Planet:
    name:      str
    planet_id: int
    menu_addr: int | None = None


class PlanetState(BaseState):
    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
        name: str,
        planet_id: int,
        menu_addr: int | None = None,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.name      = name
        self.planet_id = planet_id
        self.menu_addr = menu_addr

        self._armour:             ArmourState | None           = None
        self._weapons:            WeaponState | None           = None
        self._player:             PlayerState | None           = None
        self._menu:               MenuState | None             = None
        self._vendor:             VendorState | None           = None
        self._display_text:       DisplayTextBoxState | None   = None
        self._displayed_text_box: DisplayedTextBoxState | None = None
        self._display_text_cfg:   DisplayedTextBox | None     = None

        self._reapply_inv:        Callable[[], None]     | None = None
        self._get_checked_locs:   Callable[[], set[str]] | None = None
        self._on_enter_callbacks: list[Callable[[], None]] = []
        self._on_exit_callbacks:  list[Callable[[], None]] = []
        self._active_planet: int = 0

    def set_player_state(self, player: PlayerState) -> None:
        self._player = player

    def set_weapon_state(self, weapons: WeaponState) -> None:
        self._weapons = weapons

    def set_armour(self, armour: ArmourState) -> None:
        self._armour = armour

    def set_menu_state(self, menu: MenuState, vendor: VendorState) -> None:
        self._menu   = menu
        self._vendor = vendor

    def set_display_text_box(
        self,
        display_text: DisplayTextBoxState,
        config: DisplayedTextBox,
    ) -> None:
        self._display_text     = display_text
        self._display_text_cfg = config

    def set_displayed_text_box(self, displayed_text_box: DisplayedTextBoxState) -> None:
        self._displayed_text_box = displayed_text_box

    def set_inventory_callbacks(
        self,
        reapply_inv: Callable[[], None],
        get_checked_locations: Callable[[], set[str]],
    ) -> None:
        self._reapply_inv      = reapply_inv
        self._get_checked_locs = get_checked_locations

    def add_enter_callback(self, fn: Callable[[], None]) -> None:
        self._on_enter_callbacks.append(fn)

    def add_exit_callback(self, fn: Callable[[], None]) -> None:
        self._on_exit_callbacks.append(fn)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(GameStatusStruct, self._on_game_status_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(GameStatusStruct, self._on_game_status_change)

    def _on_game_status_change(self, address: int, new_bytes: bytes) -> None:
        del address
        offset = GameStatusStruct.field_offset("current_planet")
        if len(new_bytes) <= offset:
            return
        new_planet = new_bytes[offset]
        was_active = self._active_planet == self.planet_id
        now_active = new_planet == self.planet_id
        self._active_planet = new_planet
        if now_active and not was_active:
            self.planet_enter()
        elif was_active and not now_active:
            self.planet_exit()

    def sync(self) -> None:
        pass

    def planet_enter(self) -> None:
        logger.info(f"[RAC] [{self.name}] planet_enter")
        arm_cutscenes(self._pine_proxy(), self.planet_id, "armed")
        for cb in self._on_enter_callbacks:
            cb()
        if self._player is not None:
            self._player.set_planet(self.planet_id)
        if self._menu is not None and self._vendor is not None:
            self._menu.bind(self._vendor, self)
        if self._display_text is not None and self._display_text_cfg is not None:
            self._display_text.activate(self._display_text_cfg)
            self._display_text.on_vendor_prompt_shown  = self.on_menu_preload
            self._display_text.on_vendor_prompt_hidden = self.on_menu_preload_exit
        if self._displayed_text_box is not None and self._display_text_cfg is not None:
            self._displayed_text_box.activate(self._display_text_cfg)
        if self._get_checked_locs is not None and self._weapons is not None:
            self._weapons.sync_from_ap(self._get_checked_locs())
        if self._reapply_inv is not None:
            self._reapply_inv()

    def planet_exit(self) -> None:
        logger.info(f"[RAC] [{self.name}] planet_exit")
        for cb in self._on_exit_callbacks:
            cb()
        if self._menu is not None:
            self._menu.on_exit()
        if self._display_text is not None:
            self._display_text.deactivate()
        if self._displayed_text_box is not None:
            self._displayed_text_box.deactivate()

    def _pine_proxy(self):
        accessor = self.accessor

        class _Proxy:
            def read_int8(self, addr: int) -> int:
                raw = accessor.read_raw(addr, 1)
                return raw[0] if raw else 0
            def write_int8(self, addr: int, val: int) -> None:
                accessor.write_raw(addr, bytes([val & 0xFF]))
            def read_int16(self, addr: int) -> int:
                raw = accessor.read_raw(addr, 2)
                return int.from_bytes(raw, "little", signed=True) if len(raw) >= 2 else 0
            def write_int16(self, addr: int, val: int) -> None:
                accessor.write_raw(addr, val.to_bytes(2, "little", signed=True))
            def read_int32(self, addr: int) -> int:
                raw = accessor.read_raw(addr, 4)
                return int.from_bytes(raw, "little", signed=True) if len(raw) >= 4 else 0
            def write_int32(self, addr: int, val: int) -> None:
                accessor.write_raw(addr, val.to_bytes(4, "little", signed=False))
            def read_int64(self, addr: int) -> int:
                raw = accessor.read_raw(addr, 8)
                return int.from_bytes(raw, "little") if len(raw) >= 8 else 0
            def write_int64(self, addr: int, val: int) -> None:
                accessor.write_raw(addr, val.to_bytes(8, "little"))
            def read_bytes(self, addr: int, size: int) -> bytes:
                return accessor.read_raw(addr, size)
            def write_bytes(self, addr: int, data: bytes) -> None:
                accessor.write_raw(addr, data)

        return _Proxy()

    def on_pickup_start(self) -> None:
        suppress_disabled_cutscenes(self._pine_proxy(), self.planet_id)
        logger.info(f"[RAC] [{self.name}] Pickup start — applying collected armour")
        if self._armour is not None:
            self._armour.sync_slots()
            self._armour.apply_location_armour()

    def on_pickup_end(self) -> None:
        suppress_disabled_cutscenes(self._pine_proxy(), self.planet_id)
        logger.info(f"[RAC] [{self.name}] Pickup end — reading armour state")
        if self._armour is None:
            return
        self._armour.sync()
        bitmask_summary = {k: hex(v) for k, v in self._armour.sets_bitmask.items() if v}
        logger.info(f"[RAC] [{self.name}] Pickup end sets_bitmask: {bitmask_summary}")
        for name, mask in self._armour.sets_bitmask.items():
            new_bits = mask & ~self._armour.location_collected_armour.get(name, 0)
            for piece in _PIECE_ORDER:
                if new_bits & int(piece):
                    self.on_armour_acquired(name, piece)
        self._armour.apply_item_pickup_armour()

    def on_armour_acquired(self, _name: str, _piece: ArmourPiece) -> None:
        del _name, _piece

    def on_menu_preload(self) -> None:
        logger.info(f"[RAC] [{self.name}] Vendor preload started.")
        if self._vendor is not None:
            self._vendor.start_menu_preload()
        if self._weapons is not None:
            self._weapons.apply_vendor_locations()

    def on_menu_preload_exit(self) -> None:
        from .vendor import VendorSessionState
        session = self._vendor.session if self._vendor is not None else VendorSessionState.CLOSED
        logger.info(f"[RAC] [{self.name}] Vendor preload exit — session={session.name}.")
        if session != VendorSessionState.PRELOADING:
            return
        if self._vendor is not None:
            self._vendor.deactivate()
        if self._reapply_inv is not None:
            self._reapply_inv()

    def on_menu_open(self) -> None:
        logger.info(f"[RAC] [{self.name}] Vendor menu open.")
        if self._weapons is not None:
            self._weapons.apply_vendor_locations()

    def on_menu_close(self) -> None:
        logger.info(f"[RAC] [{self.name}] Vendor menu closed — restoring AP inventory.")
        if self._vendor is not None:
            self._vendor.deactivate()
        if self._reapply_inv is not None:
            self._reapply_inv()

    def on_vendor_weapon_purchased(self, _name: str) -> None:
        del _name

    def on_vendor_gadget_purchased(self, _name: str) -> None:
        del _name

    def on_vendor_mod_purchased(self, _weapon: str, _slot: str) -> None:
        del _weapon, _slot

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanetState):
            return NotImplemented
        return self.planet_id == other.planet_id

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(self.planet_id)

    def __repr__(self) -> str:
        return f"PlanetState(name={self.name!r}, planet_id={self.planet_id:#04x})"


class Planets:
    POKITARU        = Planet("Pokitaru",        0x01, menu_addr=MENU_ADDR_BY_PLANET_ID[0x01])
    RYLLUS          = Planet("Ryllus",          0x02, menu_addr=MENU_ADDR_BY_PLANET_ID[0x02])
    KALIDON         = Planet("Kalidon",         0x03, menu_addr=MENU_ADDR_BY_PLANET_ID[0x03])
    METALIS         = Planet("Metalis",         0x04, menu_addr=MENU_ADDR_BY_PLANET_ID[0x04])
    DREAMTIME       = Planet("Dreamtime",       0x05, menu_addr=MENU_ADDR_BY_PLANET_ID[0x05])
    CHALLAX         = Planet("Challax",         0x07, menu_addr=MENU_ADDR_BY_PLANET_ID[0x07])
    DAYNI_MOON      = Planet("Dayni Moon",      0x08, menu_addr=MENU_ADDR_BY_PLANET_ID[0x08])
    INSIDE_CLANK    = Planet("Inside Clank",    0x09)
    QUODRONA        = Planet("Quodrona",        0x0A, menu_addr=MENU_ADDR_BY_PLANET_ID[0x0A])
    OUTPOST_OMEGA_2 = Planet("Outpost Omega 2", 0x17, menu_addr=MENU_ADDR_BY_PLANET_ID[0x17])


BY_ID: dict[int, Planet] = {
    p.planet_id: p
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}
