from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

logger = logging.getLogger("CommonClient")

from worlds.rac_size_matters.core.data.armour import ArmourPiece
from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

from ..data.addresses import MENU_ADDR_BY_PLANET_ID
from ..data.cutscenes import arm_cutscenes, suppress_disabled_cutscenes

_PIECE_ORDER = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]

if TYPE_CHECKING:
    from worlds.rac_size_matters.core.data.addresses import DisplayedTextBox
    from worlds.rac_size_matters.core.states.armour import ArmourState
    from worlds.rac_size_matters.core.states.display_text_box import DisplayTextBoxState
    from worlds.rac_size_matters.core.states.menu import MenuState
    from worlds.rac_size_matters.core.states.player import PlayerState
    from worlds.rac_size_matters.core.states.vendor import VendorState
    from worlds.rac_size_matters.core.states.weapon import WeaponState


@dataclass(frozen=True)
class Planet:
    name:      str
    planet_id: int
    menu_addr: int | None = None


class PlanetState(State):
    """
    State for a single planet. Activated when the player lands; deactivated on exit.

    Call the set_* methods to bind global states and addresses, then poll() to
    start detecting planet transitions. on_enter / on_exit activate and deactivate
    all bound states with this planet's addresses.
    """

    def __init__(
        self,
        pine: Pine,
        name: str,
        planet_id: int,
        current_planet_addr: int,
        menu_addr: int | None = None,
    ):
        super().__init__(pine)
        self.name                = name
        self.planet_id           = planet_id
        self.current_planet_addr = current_planet_addr
        self.menu_addr           = menu_addr

        # ── global state references (set via set_* methods) ───────────────────
        self._armour:       ArmourState | None        = None
        self._weapons:      WeaponState | None        = None
        self._player:       PlayerState | None        = None
        self._menu:         MenuState | None          = None
        self._vendor:       VendorState | None        = None
        self._display_text: DisplayTextBoxState | None = None

        # ── per-planet addresses ──────────────────────────────────────────────
        self._movement_addr:      int | None          = None
        self._health_addr:        int | None          = None
        self._weapon_array_base:  int | None          = None
        self._preload_addr:       int                 = 0
        self._display_text_cfg:   DisplayedTextBox | None = None

        # ── callbacks ─────────────────────────────────────────────────────────
        self._reapply_inv:         Callable[[], None]       | None = None
        self._get_checked_locs:    Callable[[], set[str]]   | None = None

        # ── internal ──────────────────────────────────────────────────────────
        self._poll_interval:       int                = 100
        self._vendor_poll_task:    asyncio.Task | None = None
        self._on_enter_callbacks:  list[Callable[[], None]] = []

    # ── wiring setters ────────────────────────────────────────────────────────

    def set_player_state(
        self,
        player: PlayerState,
        movement_addr: int,
        health_addr: int,
    ) -> None:
        self._player       = player
        self._movement_addr = movement_addr
        self._health_addr   = health_addr

    def set_weapon_state(self, weapons: WeaponState, array_base: int) -> None:
        self._weapons            = weapons
        self._weapon_array_base  = array_base

    def set_armour(self, armour: ArmourState) -> None:
        self._armour = armour

    def set_menu_state(
        self,
        menu: MenuState,
        preload_addr: int,
        vendor: VendorState,
    ) -> None:
        self._menu         = menu
        self._preload_addr = preload_addr
        self._vendor       = vendor

    def set_display_text_box(
        self,
        display_text: DisplayTextBoxState,
        config: DisplayedTextBox,
    ) -> None:
        self._display_text     = display_text
        self._display_text_cfg = config
        display_text.on_vendor_prompt_shown  = lambda: asyncio.create_task(self.on_menu_preload())
        display_text.on_vendor_prompt_hidden = lambda: asyncio.create_task(self.on_menu_preload_exit())

    def set_inventory_callbacks(
        self,
        reapply_inv: Callable[[], None],
        get_checked_locations: Callable[[], set[str]],
    ) -> None:
        self._reapply_inv      = reapply_inv
        self._get_checked_locs = get_checked_locations

    def set_poll_interval(self, ms: int) -> None:
        self._poll_interval = ms

    def add_enter_callback(self, fn: Callable[[], None]) -> None:
        self._on_enter_callbacks.append(fn)

    # ── State interface ───────────────────────────────────────────────────────

    async def read(self) -> bool:
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: int | None = None
        while True:
            async with self._lock:
                current = self.pine.read_int8(mem_address)
            if last is None:
                if current == self.planet_id:
                    asyncio.create_task(self.on_enter())
            elif current != last:
                callback(last, current)
                now_active = current == self.planet_id
                was_active = last    == self.planet_id
                if now_active and not was_active:
                    asyncio.create_task(self.on_enter())
                elif was_active and not now_active:
                    asyncio.create_task(self.on_exit())
            last = current
            await asyncio.sleep(interval / 1000)

    # ── Planet lifecycle ──────────────────────────────────────────────────────

    async def on_enter(self) -> None:
        """Activate all per-planet states and apply AP inventory."""
        arm_cutscenes(self.pine, self.planet_id, "armed")
        for cb in self._on_enter_callbacks:
            cb()
        interval = self._poll_interval

        if self._player and self._movement_addr is not None:
            await self._player.activate(
                self._movement_addr, self._health_addr, interval, lambda *_: None
            )

        if self._weapons and self._weapon_array_base is not None:
            await self._weapons.activate(self._weapon_array_base, interval, lambda *_: None)

        if self._menu and self.menu_addr is not None and self._vendor is not None:
            await self._menu.activate(
                self.menu_addr, self._preload_addr,
                self._vendor, self, interval, lambda *_: None,
            )

        if self._display_text and self._display_text_cfg is not None:
            await self._display_text.activate(self._display_text_cfg, interval)

        if self._get_checked_locs and self._weapons:
            self._weapons.sync_from_ap(self._get_checked_locs())

        if self._reapply_inv:
            self._reapply_inv()

    async def on_exit(self) -> None:
        """Deactivate all per-planet states."""
        if self._player:
            await self._player.deactivate()
        if self._weapons:
            await self._weapons.deactivate()
        if self._menu:
            await self._menu.deactivate()
        if self._display_text:
            await self._display_text.deactivate()
        if self._vendor_poll_task:
            self._vendor_poll_task.cancel()
            self._vendor_poll_task = None

    # ── Pickup hooks ──────────────────────────────────────────────────────────

    async def on_pickup_start(self) -> None:
        """Reads slot state, applies location armour so the game writes only the new piece during animation."""
        suppress_disabled_cutscenes(self.pine, self.planet_id)
        logger.info(f"[RAC] [{self.name}] Pickup start — applying collected armour")
        if self._armour is not None:
            await self._armour.read_armour_slots()
            await self._armour.apply_location_armour()

    async def on_pickup_end(self) -> None:
        """Detects newly written armour bits, fires location checks, then restores AP state."""
        suppress_disabled_cutscenes(self.pine, self.planet_id)
        logger.info(f"[RAC] [{self.name}] Pickup end — reading armour state")
        if self._armour is None:
            return
        await asyncio.sleep(0.3)
        await self._armour.read()
        bitmask_summary = {k: hex(v) for k, v in self._armour.sets_bitmask.items() if v}
        logger.info(f"[RAC] [{self.name}] Pickup end sets_bitmask: {bitmask_summary}")
        for name, mask in self._armour.sets_bitmask.items():
            new_bits = mask & ~self._armour.location_collected_armour.get(name, 0)
            for piece in _PIECE_ORDER:
                if new_bits & int(piece):
                    self.on_armour_acquired(name, piece)
        await self._armour.apply_item_pickup_armour()

    def on_armour_acquired(self, _name: str, _piece: ArmourPiece) -> None:
        """Fired for each newly acquired armour piece after a pickup."""
        del _name, _piece

    # ── Menu hooks ────────────────────────────────────────────────────────────

    async def on_menu_preload(self) -> None:
        """Sets vendor session to preloading and applies vendor purchase locations to memory."""
        if self._vendor is not None:
            self._vendor.start_menu_preload()
        if self._weapons is not None:
            await self._weapons.apply_vendor_locations()

    async def on_menu_preload_exit(self) -> None:
        """Closes vendor session and restores full AP inventory."""
        if self._vendor is not None:
            self._vendor.deactivate()
        if self._reapply_inv:
            self._reapply_inv()

    async def on_menu_open(self) -> None:
        """Polls weapon/mod/gadget unlock addresses for purchases while the vendor is open."""
        if self._weapons is None:
            return
        from worlds.rac_size_matters.core.states.weapon import (
            GADGET_INTERNAL_TO_LOCATION,
            MOD_INTERNAL_TO_LOCATION,
            WEAPON_INTERNAL_TO_LOCATION,
        )
        await self._weapons.apply_vendor_locations()
        snapshot_vendor = dict(self._weapons.vendor_locations)

        async def _poll_purchases() -> None:
            while True:
                await self._weapons.read()
                for name, unlocked in self._weapons.weapons.items():
                    loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
                    if unlocked and loc and not snapshot_vendor.get(loc, False):
                        snapshot_vendor[loc] = True
                        self._weapons.vendor_locations[loc] = True
                        self.on_vendor_weapon_purchased(name)
                for name, unlocked in self._weapons.gadgets.items():
                    loc = GADGET_INTERNAL_TO_LOCATION.get(name)
                    if unlocked and loc and not snapshot_vendor.get(loc, False):
                        snapshot_vendor[loc] = True
                        self._weapons.vendor_locations[loc] = True
                        self.on_vendor_gadget_purchased(name)
                for weapon, slots in self._weapons.mods.items():
                    for slot, unlocked in slots.items():
                        loc = MOD_INTERNAL_TO_LOCATION.get((weapon, slot))
                        if unlocked and loc and not snapshot_vendor.get(loc, False):
                            snapshot_vendor[loc] = True
                            self._weapons.vendor_locations[loc] = True
                            self.on_vendor_mod_purchased(weapon, slot)
                await asyncio.sleep(self._poll_interval / 1000)

        self._vendor_poll_task = asyncio.create_task(_poll_purchases())

    async def on_menu_close(self) -> None:
        """Stops purchase polling and restores full AP inventory."""
        if self._vendor_poll_task is not None:
            self._vendor_poll_task.cancel()
            self._vendor_poll_task = None
        if self._reapply_inv:
            self._reapply_inv()

    def on_vendor_weapon_purchased(self, _name: str) -> None:
        """Fired when a weapon is purchased from the vendor."""
        del _name

    def on_vendor_gadget_purchased(self, _name: str) -> None:
        """Fired when a gadget is purchased from the vendor."""
        del _name

    def on_vendor_mod_purchased(self, _weapon: str, _slot: str) -> None:
        """Fired when a weapon mod is purchased from the vendor."""
        del _weapon, _slot

    # ── Dunder ────────────────────────────────────────────────────────────────

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanetState):
            return NotImplemented
        return self.planet_id == other.planet_id

    def __repr__(self) -> str:
        return f"PlanetState(name={self.name!r}, planet_id={self.planet_id:#04x})"


class Planets:
    POKITARU        = Planet("Pokitaru",              0x01, menu_addr=MENU_ADDR_BY_PLANET_ID[0x01])
    RYLLUS          = Planet("Ryllus",                0x02, menu_addr=MENU_ADDR_BY_PLANET_ID[0x02])
    KALIDON         = Planet("Kalidon",               0x03, menu_addr=MENU_ADDR_BY_PLANET_ID[0x03])
    METALIS         = Planet("Metalis",               0x04, menu_addr=MENU_ADDR_BY_PLANET_ID[0x04])
    DREAMTIME       = Planet("Dreamtime",             0x05, menu_addr=MENU_ADDR_BY_PLANET_ID[0x05])
    # OUTPOST_OMEGA_1 = Planet("Outpost Omega 1",       0x06)
    CHALLAX         = Planet("Challax",               0x07, menu_addr=MENU_ADDR_BY_PLANET_ID[0x07])
    DAYNI_MOON      = Planet("Dayni Moon",            0x08, menu_addr=MENU_ADDR_BY_PLANET_ID[0x08])
    INSIDE_CLANK    = Planet("Inside Clank",          0x09)
    QUODRONA        = Planet("Quodrona",              0x0A, menu_addr=MENU_ADDR_BY_PLANET_ID[0x0A])
    # GIANT_CLANK_META = Planet("Giant Clank (Metalis)", 0x0F)
    # GIANT_CLANK_CHAL = Planet("Giant Clank (Challax)", 0x15)
    # KALIDON_RACE    = Planet("Kalidon Race Track",    0x16)
    OUTPOST_OMEGA_2 = Planet("Outpost Omega 2",       0x17, menu_addr=MENU_ADDR_BY_PLANET_ID[0x17])


BY_ID: dict[int, Planet] = {
    p.planet_id: p
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}
