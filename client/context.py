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

from ..core.challenge import ChallengePoller
from ..core.data import PLANET_STATE_ADDRESSES, PLAYER_STATE, SKILL_POINT_ADDRESS
from ..core.data.controller import ButtonState
from ..core.memory import (
    ARMOUR_ADDRESSES,
    BOLTS,
    PLAYER_ARMOUR_SLOTS,
    Int64State,
    MemoryItemState,
)
from ..core.skyboard import SkyboardPoller
from ..core.state import GameState
from ..core.vendor import VendorPoller, VendorSession
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


class RACContext(
    PineMixin, CutsceneHandlerMixin, EventsHandlerMixin,
    DeathLinkMixin, VendorHandlerMixin, InventoryMixin, CommonContext,
):
    game = GAME_NAME
    command_processor = RACCommandProcessor
    items_handling = 0b111
    current_planet: str = "Galaxy"

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
        self._prev_player_state = 0
        self._prev_goal_cutscene = 0
        self._prev_ryllus_enter: int | None = None
        self._prev_before_sprout_cutscene: int | None = None
        self._prev_sprout_cutscene: int | None = None
        self._prev_electroshock_cutscene: int | None = None
        self._state_addr = PLAYER_STATE

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
        self._vendor_poller   = VendorPoller(self._gs, log=self._log)
        self._skyboard_poller = SkyboardPoller(log=self._log)
        self._challenge_poller = ChallengePoller(log=self._log)

        self._death_link_enabled = False
        self._last_death_link = 0.0
        self._debug_messages = False
        self._challenge_defaults_written = False

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
            self._challenge_poller.set_mode(int(self.slot_data.get("clank_challenges", 1)))
            self._gs.vendor_session.mods_randomized = bool(self.slot_data.get("vendor_mods_randomized", True))
            if self._death_link_enabled:
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": ["DeathLink"]}]))
            self._pending_item_apply = True
            asyncio.create_task(self._apply_received_items())
            return

        if cmd == "ReceivedItems":
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
