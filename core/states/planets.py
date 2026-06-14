from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.armour import ArmourPiece
from ..structs.game_status import GameStatusStruct

if TYPE_CHECKING:
    from ..data.display_text_box import DisplayedTextBox
    from .armour import ArmourState
    from .display_text_box import DisplayedTextBoxState, DisplayTextBoxState
    from .menu import MenuState
    from .player import PlayerState
    from .vendor import VendorState
    from .vendor_unlock import VendorUnlockState
    from .weapon import WeaponState

logger = logging.getLogger("CommonClient")

_PIECE_ORDER = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]



class PlanetState(BaseState):
    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
        name: str,
        planet_id: int,
        menu_addr: int | None = None,
        log: Callable[..., None] | None = None,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.name      = name
        self.planet_id = planet_id
        self.menu_addr = menu_addr
        self._log      = log or logger.info

        self._armour:             ArmourState | None           = None
        self._weapons:            WeaponState | None           = None
        self._player:             PlayerState | None           = None
        self._menu:               MenuState | None             = None
        self._vendor:             VendorState | None           = None
        self._vendor_unlock:      VendorUnlockState | None     = None
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

    def set_vendor_unlock(self, vendor_unlock: VendorUnlockState) -> None:
        self._vendor_unlock = vendor_unlock

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

    def planet_enter(self) -> None:
        self._log(f"[RAC] [{self.name}] planet_enter")
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
        self._log(f"[RAC] [{self.name}] planet_exit")
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
        self._log(f"[RAC] [{self.name}] Pickup start — zeroing armour for clean pickup read")
        if self._armour is not None:
            self._armour.sync_slots()
            self._armour.clear_all_memory()

    def on_pickup_end(self) -> None:
        self._log(f"[RAC] [{self.name}] Pickup end — reading armour state")
        if self._armour is None:
            return
        self._armour.sync_bitmasks()
        bitmask_summary = {k: hex(v) for k, v in self._armour.sets_bitmask.items() if v}
        self._log(f"[RAC] [{self.name}] Pickup end sets_bitmask: {bitmask_summary}")
        for name, mask in self._armour.sets_bitmask.items():
            new_bits = mask & ~self._armour.world_collected_armour.get(name, 0)
            for piece in _PIECE_ORDER:
                if new_bits & int(piece):
                    self.on_armour_acquired(name, piece)

    def on_armour_acquired(self, _name: str, _piece: ArmourPiece) -> None:
        del _name, _piece

    def on_menu_preload(self) -> None:
        self._log(f"[RAC] [{self.name}] Vendor preload started.")
        if self._vendor is not None:
            self._vendor.start_menu_preload()
        if self._weapons is not None:
            allowed = (
                self._vendor_unlock.allowed_weapons_for_inventory()
                if self._vendor_unlock is not None else frozenset()
            )
            self._weapons.apply_vendor_locations(allowed)
            self._weapons.apply_mod_vendor_locations()

    def on_menu_preload_exit(self) -> None:
        from .vendor import VendorSessionState
        session = self._vendor.session if self._vendor is not None else VendorSessionState.CLOSED
        self._log(f"[RAC] [{self.name}] Vendor preload exit — session={session.name}.")
        if session != VendorSessionState.PRELOADING:
            return
        if self._vendor is not None:
            self._vendor.deactivate()
        if self._reapply_inv is not None:
            self._reapply_inv()

    def on_menu_open(self) -> None:
        from .menu import MenuStateValue
        self._log(f"[RAC] [{self.name}] Vendor menu open.")
        if self._weapons is not None:
            allowed = (
                self._vendor_unlock.allowed_weapons_for_inventory()
                if self._vendor_unlock is not None else frozenset()
            )
            self._weapons.apply_vendor_locations(allowed)
            self._weapons.on_weapon_acquired = lambda name: self.on_vendor_weapon_purchased(name)
            self._weapons.on_gadget_acquired = lambda name: self.on_vendor_gadget_purchased(name)
            self._weapons.on_mod_acquired    = lambda weapon, slot: self.on_vendor_mod_purchased(weapon, slot)
        is_weapon_vendor = (
            self._vendor is not None
            and self._vendor.vendor_type == MenuStateValue.WEAPONS_VENDOR
        )
        if is_weapon_vendor and self._vendor_unlock is not None:
            self._vendor_unlock.apply(self.accessor)

    def on_menu_close(self) -> None:
        self._log(f"[RAC] [{self.name}] Vendor menu closed — restoring AP inventory.")
        if self._weapons is not None:
            self._weapons.on_weapon_acquired = lambda _: None
            self._weapons.on_gadget_acquired = lambda _: None
            self._weapons.on_mod_acquired    = lambda *_: None
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


