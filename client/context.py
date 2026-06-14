from __future__ import annotations

import asyncio
from typing import Any

tracker_loaded: bool = False
try:
    from worlds.tracker.TrackerClient import (
        TrackerCommandProcessor as ClientCommandProcessor,
    )
    from worlds.tracker.TrackerClient import TrackerGameContext as CommonContext
    tracker_loaded = True
except ImportError:
    from CommonClient import ClientCommandProcessor, CommonContext
from CommonClient import logger

from ..core.data import PLANET_STATE_ADDRESSES, SKILL_POINT_ADDRESS
from ..core.data.controller import ButtonState
from ..core.game_orchestrator import GameOrchestrator as GameWiring
from ..core.states.game_state import GameState
from ..core.memory import (
    ARMOUR_ADDRESSES,
    BOLTS,
    PLAYER_ARMOUR_SLOTS,
    Int64State,
    MemoryItemState,
)
from ..core.states.vendor_session import VendorPoller, VendorSession
from ..locations import ALL_LOCATIONS
from ..pypine.pypine.pine import Pine
from .constants import GAME_NAME
from .cutscene_handler import CutsceneHandlerMixin
from .deathlink import DeathLinkMixin
from .events_handler import EventsHandlerMixin
from .inventory import InventoryMixin
from .pine_mixin import PineMixin
from .vendor_handler import VendorHandlerMixin


class RACCommandProcessor(ClientCommandProcessor):
    ctx: RACContext

    def _cmd_reconnect(self) -> bool:
        """Reconnect to PCSX2 and re-apply received Archipelago items."""
        asyncio.create_task(self.ctx.reconnect_pine())
        return True

    def _cmd_disconnect_game(self) -> bool:
        """Disconnect from PCSX2 without closing the client."""
        asyncio.create_task(self.ctx.disconnect_pine())
        return True

    def _cmd_scan(self) -> bool:
        """Force a fresh weapon array scan."""
        asyncio.create_task(self.ctx.rescan_weapons())
        return True

    def _cmd_button_debug(self) -> bool:
        """Read and log the current controller button state."""
        ctx = self.ctx
        if not ctx.pine_connected:
            logger.info("[RAC] Not connected to PPSSPP.")
            return False
        btn = ButtonState.read(ctx.pine)
        logger.info(f"[RAC] Pause/Select buttons : {btn.pause_sel!r}  (raw {int(btn.pause_sel):#04x})")
        logger.info(f"[RAC] Controller buttons   : {btn.buttons!r}  (raw {int(btn.buttons):#04x})")
        return True

    def _cmd_debug(self) -> bool:
        """Toggle verbose debug logging for R&C: Size Matters."""
        self.ctx._debug_messages = not self.ctx._debug_messages
        state = "enabled" if self.ctx._debug_messages else "disabled"
        logger.info(f"[RAC] Debug messages {state}.")
        return True

    def _cmd_vendor(self) -> bool:
        """Log current vendor unlock state (owned weapons + planet-unlocked purchasables)."""
        if not self.ctx.pine_connected:
            logger.info("[RAC] Not connected to PCSX2.")
            return False
        for line in self.ctx._wiring.vendor_unlock.debug_lines():
            logger.info(line)
        return True

    def _cmd_mission_change(self) -> bool:
        """Show the 2-byte mission progress at each planet's address.
        Run before and after completing a mission to observe value changes."""
        import struct as _struct
        from ..core.data.addresses import PLANET_MISSION_ADDRESSES

        ctx = self.ctx
        if not ctx.pine_connected:
            logger.info("[RAC] Not connected to PCSX2.")
            return False

        acc      = ctx._wiring._orchestrator.accessor
        snapshot: dict[str, int] = getattr(self, "_mission_snapshot", {})

        logger.info("[RAC] ── Mission state (2-byte per planet) ───────────────────")
        for planet, addr in PLANET_MISSION_ADDRESSES.items():
            raw = acc.read_raw(addr, 2)
            if not raw or len(raw) < 2:
                logger.info(f"[RAC]   {planet:<16}  {addr:#010x}  <read error>")
                continue
            value = _struct.unpack_from("<H", raw)[0]
            prev  = snapshot.get(planet)
            if prev is not None and value != prev:
                delta = f"  =>  {prev:#06x} -> {value:#06x}  (XOR {value ^ prev:#06x})"
            else:
                delta = ""
            logger.info(f"[RAC]   {planet:<16}  {addr:#010x}  {value:#06x}{delta}")
            snapshot[planet] = value

        self._mission_snapshot = snapshot
        logger.info("[RAC] ─────────────────────────────────────────────────────────")
        return True

    def _cmd_state(self) -> bool:
        """Log all current client states."""
        ctx = self.ctx
        gs  = ctx._gs
        vs  = gs.vendor_session

        logger.info(f"[RAC] Planet         : {ctx.current_planet}")
        logger.info(f"[RAC] PINE connected : {ctx.pine_connected}")
        logger.info(f"[RAC] Game flags     : dead={gs.is_dead}  picking_up={gs.is_picking_up}"
                    f"  in_menu={gs.is_in_menu}  preloaded={gs.is_preloaded}")
        logger.info(f"[RAC] Planet state   : {ctx._planet_state!r}")
        logger.info(f"[RAC] Armour pickup  : {ctx._armour_pickup_state!r}")
        logger.info(f"[RAC] Player armour  : {ctx._player_armour_state!r}")
        logger.info(f"[RAC] Armour slots   : {ctx._armour_slot_state!r}")
        logger.info(f"[RAC] Player weapons : {ctx._player_weapon_state!r}")
        logger.info(f"[RAC] Player gadgets : {ctx._player_gadget_state!r}")
        if gs.tracked_vendor is not None:
            logger.info(f"[RAC] Vendor session : planet={gs.tracked_vendor}")
            logger.info(f"[RAC]   weapon state : {vs.weapon_state!r}")
            logger.info(f"[RAC]   gadget state : {vs.gadget_state!r}")
            logger.info(f"[RAC]   pending      : weapons={vs.purchased_weapons}  gadgets={vs.purchased_gadgets}"
                        f"  mods={vs.purchased_mods}")
        else:
            logger.info("[RAC] Vendor session : inactive")
        logger.info(f"[RAC] Tracked armour : {gs.tracked_armour!r}")
        logger.info(f"[RAC] Titanium bolts : {ctx._titanium_bolt_state!r}")
        logger.info(f"[RAC] Skill points   : {ctx._skill_point_state!r}")
        logger.info(f"[RAC] Pending pickup locs : {ctx._pending_armour_pickup_locs or 'none'}")
        return True

    def _cmd_skill_points(self) -> bool:
        """Show current skill point bitmask and earned status for each SP.
        Run again after earning a skill point to see what changed."""
        import struct as _struct
        from ..core.states.skill_points import SKILL_POINTS, SKILL_POINT_ADDRESS

        ctx = self.ctx
        sp  = ctx._wiring.skill_points

        if not ctx.pine_connected:
            logger.info("[RAC] Not connected to PPSSPP.")
            return False

        # Fresh read directly from memory — bypasses cached _bits.
        raw = ctx._wiring._orchestrator.accessor.read_raw(SKILL_POINT_ADDRESS, 8)
        if not raw or len(raw) < 8:
            logger.info(f"[RAC] Could not read skill point memory at {SKILL_POINT_ADDRESS:#010x}.")
            return False
        live = _struct.unpack_from("<Q", raw)[0]

        prev: int | None = getattr(self, "_sp_snapshot", None)
        self._sp_snapshot = live
        changed = live ^ prev if prev is not None else 0

        logger.info(
            f"[RAC] ── Skill Points  addr={SKILL_POINT_ADDRESS:#010x}"
            f"  raw={live:#018x}"
            f"  cached={sp._bits:#018x}"
            f"  planet_loaded={sp._planet_loaded}"
            f"  enabled={sp._enabled} ──"
        )
        if prev is not None:
            logger.info(f"[RAC]   prev={prev:#018x}  delta={changed:#018x}  ({bin(changed).count('1')} changed)")

        for name, info in SKILL_POINTS.items():
            earned  = bool(live & info.mask)
            marker  = "✓" if earned else " "
            chg     = "  <-- changed" if (changed & info.mask) else ""
            logger.info(f"[RAC]  [{marker}] bit {info.bit:2d}  mask={info.mask:#018x}  {name}{chg}")

        total = bin(live).count("1")
        logger.info(f"[RAC] ── {total}/{len(SKILL_POINTS)} earned ─────────────────────────────────────────")
        return True


class RACContext(
    PineMixin, CutsceneHandlerMixin, EventsHandlerMixin,
    DeathLinkMixin, VendorHandlerMixin, InventoryMixin, CommonContext,
):
    game = GAME_NAME
    command_processor = RACCommandProcessor
    items_handling = 0b111
    current_planet: str = "Galaxy"
    tags = CommonContext.tags - {"Tracker"}

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)

        self.pine = Pine()
        self.pine_connected = False
        self._pine_lock = asyncio.Lock()
        self.slot_data: dict[str, Any] = {}

        self._location_name_to_id = {name: data.code for name, data in ALL_LOCATIONS.items()}
        self._locally_checked_locations: set[int] = set()

        self._prev_skill_points = 0
        self._prev_bolt_pickup = 0
        self._planet_state = MemoryItemState(
            PLANET_STATE_ADDRESSES,
            name="PlanetState",
            debug_log=self._log,
        )
        self._prev_planet = 0

        self._armour_pickup_state = MemoryItemState(
            ARMOUR_ADDRESSES,
            on_change=self._on_armour_pickup_update,
            name="ArmourPickupState",
            debug_log=self._log,
        )
        self._player_armour_state = MemoryItemState(
            ARMOUR_ADDRESSES,
            name="PlayerArmourState",
            debug_log=self._log,
        )
        self._player_weapon_state = MemoryItemState(
            {},
            name="PlayerWeaponState",
            debug_log=self._log,
        )
        self._player_gadget_state = MemoryItemState(
            {},
            name="PlayerGadgetState",
            debug_log=self._log,
        )
        self._armour_slot_state = MemoryItemState(
            PLAYER_ARMOUR_SLOTS,
            name="ArmourSlotState",
            debug_log=self._log,
        )
        self._titanium_bolt_state = Int64State(
            BOLTS.pickup,
            name="TitaniumBoltState",
            debug_log=self._log,
        )
        self._skill_point_state = Int64State(
            SKILL_POINT_ADDRESS,
            name="SkillPointState",
            debug_log=self._log,
        )
        self._pending_armour_pickup_locs: list[str] = []
        self._processed_item_count = 0
        self._starting_bolts_granted = False
        self._death_count = 0
        self._weapon_array_base: int | None = None
        self._pending_item_apply = True
        self._pending_vendor_checks: list[str] = []
        self._armour_set_checks_enabled = False
        self._gs = GameState(
            ipc=self.pine,
            vendor_session=VendorSession(log=self._log, on_purchase=self._on_vendor_purchase),
        )
        self._gs.on_vendor_close = self._on_vendor_close_sync
        self._vendor_poller = VendorPoller(self._gs, log=self._log)

        self._death_link_enabled = False
        self._last_death_link = 0.0
        self._debug_messages = False
        self._challenge_defaults_written = False

        self._wiring = GameWiring(self.pine, log=self._log)

    def _checked_location_names(self) -> set[str]:
        id_to_name = {v: k for k, v in self._location_name_to_id.items()}
        return {
            id_to_name[lid]
            for lid in (self.checked_locations | self._locally_checked_locations)
            if lid in id_to_name
        }

    def _log(self, msg: str, level: str = "info") -> None:
        if not self._debug_messages:
            return
        if level == "warning":
            logger.warning(msg)
        else:
            logger.info(msg)

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game=self.game)

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)

        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self._death_link_enabled = bool(self.slot_data.get("death_link", False))
            self._armour_set_checks_enabled = bool(self.slot_data.get("armour_set_checks", False))
            self._wiring.clank.set_mode(int(self.slot_data.get("clank_challenges", 1)))
            self._wiring.skyboard.set_enabled(int(self.slot_data.get("skyboard_challenges", 0)) >= 1)
            self._wiring.skill_points.set_enabled(
                bool(self.slot_data.get("skill_points", False)),
                planet_loaded=self._wiring._initial_load_done,
            )
            self._wiring.skin.set_skin_by_option(int(self.slot_data.get("starting_skin", 0)))
            self._gs.vendor_session.mods_randomized = True
            if self._death_link_enabled:
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": ["DeathLink"]}]))
            self._wiring.wire(
                send_location      = self._append_location_by_name,
                send_deathlink     = self._send_death_link_from_sync,
                kill_player        = self._kill_player_sync,
                reapply_inv        = self._apply_player_inventory_sync,
                death_amnesty      = lambda: int(self.slot_data.get("death_amnesty", 1)),
                death_link_enabled = lambda: self._death_link_enabled,
                on_goal            = lambda: asyncio.create_task(self._send_goal_status()),
                on_vendor_close    = self._on_menu_close_for_armour_sets,
            )
            checked = self._checked_location_names()
            asyncio.create_task(self._wiring.on_ap_connected(self.slot_data, checked))
            self._pending_item_apply = True
            asyncio.create_task(self._apply_received_items())
            return

        if cmd == "ReceivedItems":
            checked = self._checked_location_names()
            asyncio.create_task(self._wiring.on_ap_received_items(checked))
            self._pending_item_apply = True
            asyncio.create_task(self._apply_received_items())
            return

        if cmd == "Bounced" and self._death_link_enabled and "DeathLink" in args.get("tags", []):
            data = args.get("data", {})
            if data.get("source") != self.auth:
                asyncio.create_task(self._receive_death_link(data))

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Archipelago R&C: Size Matters Client"
        return ui
