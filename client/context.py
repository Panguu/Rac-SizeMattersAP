from __future__ import annotations

import asyncio
import time
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
from NetUtils import ClientStatus

from ..core.data import (
    ARMOUR_FLAG_TO_LOCATION,
    ARMOUR_SET_CHECKS,
    BOLT_BY_PLANET_AND_DELTA,
    CURRENT_PLANET_ADDRESS,
    CUTSCENE_BEFORE_SPROUT_O_MATIC,
    CUTSCENES,
    ENTER_CUTSCENES,
    LOCATION_SKILL_POINTS,
    PLAYER_ADDRS,
    PLAYER_STATE,
    SKILL_POINT_ADDRESS,
    SPROUT_O_MATIC_CUTSCENE,
    arm_cutscenes,
)
from ..core.memory import (
    ARMOUR_ADDRESSES,
    BOLTS,
    GADGETS,
    PLAYER_ARMOUR_SLOTS,
    WEAPONS,
    ItemScanner,
    MemoryState,
)
from ..core.state import GameState
from ..core.vendor import VendorPoller, VendorSession
from ..locations import ALL_LOCATIONS
from ..pypine.pypine.pine import Pine
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, GAME_NAME, POLL_INTERVAL
from .deathlink import DeathLinkMixin, _dead, _death_cause
from .inventory import InventoryMixin
from .vendor_handler import VendorHandlerMixin
from .weapon_scanner import WeaponScannerMixin

_GOAL_CUTSCENE = next(c for c in CUTSCENES if c.kind == "goal")
_SLOT_STATE = MemoryState(lambda: PLAYER_ARMOUR_SLOTS.values())


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


class RACContext(DeathLinkMixin, VendorHandlerMixin, WeaponScannerMixin, InventoryMixin, CommonContext):
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
        self._prev_armour_sets: dict[str, int] = {}
        self._prev_planet = 0
        self._prev_player_state = 0
        self._prev_goal_cutscene = 0
        self._prev_ryllus_enter: int | None = None
        self._prev_before_sprout_cutscene: int | None = None
        self._prev_sprout_cutscene: int | None = None
        self._state_addr = PLAYER_STATE

        self._expected_weapons: dict[str, int] = {}
        self._expected_weapon_mods: dict[str, int] = {}
        self._expected_gadgets: dict[str, int] = {}
        self._expected_armour: dict[str, int] = dict.fromkeys(ARMOUR_ADDRESSES, 0)
        self._processed_item_count = 0
        self._starting_bolts_granted = False
        self._death_count = 0
        self._weapon_array_base: int | None = None
        self._pending_item_apply = True
        self._pending_vendor_checks: list[str] = []
        self._armour_set_checks_enabled = False
        self._gs = GameState(
            ipc=self.pine,
            vendor_session=VendorSession(),
            tracked_armour=self._expected_armour.copy(),
        )
        self._gs.on_vendor_close = self._on_vendor_close_sync
        self._vendor_poller = VendorPoller(self._gs)
        self._scanners = self._build_scanners()
        self._armour_scanner = self._scanners[0]

        self._planet_change_time: float | None = None

        self._death_link_enabled = False
        self._last_death_link = 0.0

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game=self.game)

    def _build_scanners(self) -> list[ItemScanner]:
        def on_armour(name: str, val: int) -> None:
            self._gs.picked_up_items[name] = val

        def on_weapon(name: str, val: int) -> None:
            self._gs.picked_up_items[f"weapon:{name}"] = val

        def on_gadget(name: str, val: int) -> None:
            self._gs.picked_up_items[f"gadget:{name}"] = val

        return [
            ItemScanner(lambda: ARMOUR_ADDRESSES, on_armour),
            ItemScanner(lambda: {name: weapon.unlocked for name, weapon in WEAPONS.items()}, on_weapon),
            ItemScanner(lambda: {name: gadget.unlocked for name, gadget in GADGETS.items()}, on_gadget),
        ]

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)

        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self._death_link_enabled = bool(self.slot_data.get("death_link", False))
            self._armour_set_checks_enabled = bool(self.slot_data.get("armour_set_checks", False))
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

    async def disconnect_pine(self) -> None:
        async with self._pine_lock:
            self.pine_connected = False
            try:
                self.pine.disconnect()
            except Exception:
                pass
        logger.info("[RAC] Disconnected from PCSX2. Use /reconnect to reconnect.")

    async def reconnect_pine(self) -> None:
        async with self._pine_lock:
            self.pine_connected = False
            try:
                self.pine.disconnect()
            except Exception:
                pass
        await self._attempt_pine_connect()

    async def rescan_weapons(self) -> None:
        if not self.pine_connected:
            logger.info("[RAC] Not connected to PCSX2.")
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            scanned = await loop.run_in_executor(None, self._sync_weapons_cached, True)
        if scanned:
            self._pending_item_apply = True
            await self._apply_received_items()

    async def _attempt_pine_connect(self) -> None:
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            try:
                await loop.run_in_executor(None, self.pine.connect)
                game_id = await loop.run_in_executor(None, self.pine.get_game_id)
            except Exception:
                logger.info("[RAC] Could not connect to PCSX2. Use /reconnect once the emulator is running.")
                self.pine_connected = False
                return

            if game_id != EXPECTED_GAME_ID:
                logger.warning(f"[RAC] Wrong game in PCSX2: {game_id!r} (expected {EXPECTED_GAME_ID!r}).")
                self.pine_connected = False
                return

            logger.info("[RAC] Connected to PCSX2 - R&C: Size Matters detected.")
            self.pine_connected = True
            await loop.run_in_executor(None, self._sync_weapons_cached)
            try:
                await loop.run_in_executor(None, self._read_initial_state_sync)
            except Exception as exc:
                logger.warning(f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded.")
                self.pine_connected = False
                return
        await self._apply_received_items()
        await self._send_map_page(self.current_planet)

    async def _read_initial_state(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            async with self._pine_lock:
                await loop.run_in_executor(None, self._read_initial_state_sync)
        except Exception as exc:
            logger.warning(f"[RAC] Initial state read failed: {exc}")

    def _read_initial_state_sync(self) -> None:
        self._prev_skill_points = self.pine.read_int64(SKILL_POINT_ADDRESS)
        self._prev_bolt_pickup = self.pine.read_int64(BOLTS.pickup) & 0x000000FFFFFFFFFF
        self._prev_planet = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        self.current_planet = PLANET_ID_TO_REGION.get(self._prev_planet, "Galaxy")
        self._state_addr = PLAYER_ADDRS.get(self._prev_planet, (PLAYER_STATE,))[0]
        self._prev_player_state = self.pine.read_int16(self._state_addr)
        self._prev_goal_cutscene = self.pine.read_int32(_GOAL_CUTSCENE.address)
        if self._prev_planet == 0x02:
            self._prev_ryllus_enter = self.pine.read_int32(ENTER_CUTSCENES["ryllus"])
            self._prev_before_sprout_cutscene = self.pine.read_int32(CUTSCENE_BEFORE_SPROUT_O_MATIC)
            self._prev_sprout_cutscene = self.pine.read_int32(SPROUT_O_MATIC_CUTSCENE)
        self._prev_armour_sets = {
            name: self.pine.read_int8(address)
            for name, address in ARMOUR_ADDRESSES.items()
        }
        self._gs.current_planet = self._prev_planet
        self._gs.state_addr = self._state_addr
        self._gs.is_dead = _dead(self._prev_player_state)
        self._gs.is_picking_up = self._prev_player_state == 0x43
        self._gs.is_preloaded = False
        self._gs.is_in_menu = False
        self._gs.tracked_vendor = None
        arm_cutscenes(self.pine, self._prev_planet, "armed")

    async def game_watcher(self) -> None:
        while not self.exit_event.is_set():
            await asyncio.sleep(POLL_INTERVAL)
            if not self.pine_connected:
                continue
            try:
                await self._poll_game()
            except Exception as exc:
                logger.warning(f"[RAC] Lost PINE connection or poll failed: {exc}")
                self.pine_connected = False

    async def _poll_game(self) -> None:
        prev_planet = self.current_planet
        async with self._pine_lock:
            checks = self._poll_game_sync()
        if self.current_planet != prev_planet:
            await self._send_map_page(self.current_planet)
        if checks:
            await self._check_locations(checks)

    async def _send_map_page(self, planet: str) -> None:
        if self.slot is None:
            return
        team = getattr(self, "team", 0)
        await self.send_msgs([{
            "cmd": "Set",
            "key": f"rsm_current_planet_{self.slot}_{team}",
            "default": "Galaxy",
            "want_reply": False,
            "operations": [{"operation": "replace", "value": planet}],
        }])

    @property
    def _on_known_planet(self) -> bool:
        return self._prev_planet in PLANET_ID_TO_REGION

    def _poll_game_sync(self) -> list[int]:
        new_checks: list[int] = []

        planet = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        if planet != self._prev_planet:
            self._prev_planet = planet
            self._state_addr = PLAYER_ADDRS.get(planet, (PLAYER_STATE,))[0]
            self._gs.current_planet = planet
            self.current_planet = PLANET_ID_TO_REGION.get(planet, "Galaxy")
            self._gs.state_addr = self._state_addr
            arm_cutscenes(self.pine, planet, "armed")
            self._prev_bolt_pickup = self.pine.read_int64(BOLTS.pickup) & 0x000000FFFFFFFFFF
            self._planet_change_time = time.monotonic()

        if self._planet_change_time is not None and time.monotonic() - self._planet_change_time >= 2.0:
            self._planet_change_time = None
            if self._on_known_planet:
                try:
                    self._sync_weapons_cached(force_scan=True)
                except Exception as exc:
                    logger.warning(f"[RAC] Weapon rescan on planet change failed: {exc}")
                _SLOT_STATE.take(self.pine)
                self._apply_expected_inventory_sync(clear_unreceived=True)
                _SLOT_STATE.restore(self.pine)
            else:
                logger.info(f"[RAC] Unknown planet {self._prev_planet:#04x} — skipping inventory writes.")

        player_state = self.pine.read_int16(self._state_addr)
        if not _dead(self._prev_player_state) and _dead(player_state):
            self._on_player_death(player_state)
        elif _dead(self._prev_player_state) and player_state == 0x00:
            self._on_player_respawn()
        elif self._prev_player_state != 0x43 and player_state == 0x43:
            self._on_pickup_start()
        elif self._prev_player_state == 0x43 and player_state == 0x00:
            self._on_pickup_end(new_checks)
        elif (self._prev_player_state != 0x00
              and player_state == 0x00
              and not _dead(self._prev_player_state)):
            self._on_menu_close(new_checks)
        self._prev_player_state = player_state

        skill_points = self.pine.read_int64(SKILL_POINT_ADDRESS)
        new_skill_bits = skill_points & ~self._prev_skill_points
        if new_skill_bits:
            logger.info(
                f"[RAC] Skill point address changed by 0x{new_skill_bits:016X} (raw value 0x{skill_points:016X})"
            )
        for name, mask in LOCATION_SKILL_POINTS.items():
            if new_skill_bits & mask:
                self._append_location(new_checks, name, "Skill point")
        self._prev_skill_points = skill_points

        bolt_pickup = self.pine.read_int64(BOLTS.pickup) & 0x000000FFFFFFFFFF
        bolt_delta = bolt_pickup - self._prev_bolt_pickup
        if bolt_delta > 0 and (bolt_delta & (bolt_delta - 1)) == 0:
            logger.info(f"[RAC] Titanium bolt address changed by {bolt_delta}")
            name = BOLT_BY_PLANET_AND_DELTA.get((planet, bolt_delta))
            if name:
                self._append_location(new_checks, name, "Titanium bolt")
        elif bolt_delta > 0:
            logger.warning(
                f"[RAC] Titanium bolt delta {bolt_delta} is not a power of 2 — ignoring (likely init noise)."
            )
        self._prev_bolt_pickup = bolt_pickup

        for set_key, address in ARMOUR_ADDRESSES.items():
            current = self.pine.read_int8(address)
            previous = self._prev_armour_sets.get(set_key, 0)
            new_bits = current & ~previous
            for piece in (0x01, 0x02, 0x04, 0x10):
                if new_bits & piece:
                    name = ARMOUR_FLAG_TO_LOCATION.get((set_key, piece))
                    if name:
                        self._append_location(new_checks, name, "Armour")
            self._prev_armour_sets[set_key] = current

        goal_val = self.pine.read_int32(_GOAL_CUTSCENE.address)
        if self._prev_goal_cutscene != 0 and goal_val == 0 and planet == _GOAL_CUTSCENE.planet_id:
            self._append_location(new_checks, "Defeat Otto Destruct", "Goal")
            asyncio.create_task(self._send_goal_status())
        self._prev_goal_cutscene = goal_val

        if planet == 0x02:  # Ryllus
            enter_val = self.pine.read_int32(ENTER_CUTSCENES["ryllus"])
            before_val = self.pine.read_int32(CUTSCENE_BEFORE_SPROUT_O_MATIC)
            sprout_val = self.pine.read_int32(SPROUT_O_MATIC_CUTSCENE)

            if self._prev_before_sprout_cutscene is not None \
                    and self._prev_before_sprout_cutscene != 0 and before_val == 0:
                self._append_location(new_checks, "Ryllus Sprout-O-Matic", "Cutscene")

            if self._prev_sprout_cutscene is not None \
                    and self._prev_sprout_cutscene != 0 and sprout_val == 0:
                if GADGETS and "sprout_o_matic" not in self._expected_gadgets:
                    self.pine.write_int8(GADGETS["sprout_o_matic"].unlocked, 0)

            self._prev_ryllus_enter = enter_val
            self._prev_before_sprout_cutscene = before_val
            self._prev_sprout_cutscene = sprout_val
        else:
            self._prev_ryllus_enter = None
            self._prev_before_sprout_cutscene = None
            self._prev_sprout_cutscene = None

        self._vendor_poller.tick(self.pine)

        for loc_name in self._pending_vendor_checks:
            self._append_location(new_checks, loc_name, "Vendor purchase")
        self._pending_vendor_checks.clear()

        self._enforce_locks()

        return new_checks

    def _append_location(self, checks: list[int], name: str, kind: str) -> None:
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None or loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations and loc_id not in server_locations:
            return
        checks.append(loc_id)
        logger.info(f"[RAC] {kind} checked: {name}")

    async def _check_locations(self, locations: list[int]) -> None:
        unique_locations = set(locations) - self._locally_checked_locations
        if not unique_locations:
            return
        self._locally_checked_locations.update(unique_locations)
        await self.check_locations(unique_locations)

    async def _send_goal_status(self) -> None:
        if not self.finished_game:
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.finished_game = True

    def _on_player_death(self, player_state: int) -> None:
        self._gs.is_dead = True
        self._death_count += 1
        amnesty = int(self.slot_data.get("death_amnesty", 1))
        cause = _death_cause(player_state)
        arm_cutscenes(self.pine, self._gs.current_planet, "reset")
        if WEAPONS:
            for weapon in WEAPONS.values():
                self.pine.write_int8(weapon.unlocked, 0)
                self.pine.write_int8(weapon.mod_slot_one, 0)
                self.pine.write_int8(weapon.mod_slot_two, 0)
                self.pine.write_int8(weapon.mod_slot_three, 0)
            for gadget in GADGETS.values():
                self.pine.write_int8(gadget.unlocked, 0)
        for address in ARMOUR_ADDRESSES.values():
            self.pine.write_int8(address, 0)
        _SLOT_STATE.take(self.pine)
        if self._death_count > amnesty:
            logger.info(
                f"[RAC] Death {self._death_count} (Ratchet {cause}): amnesty exceeded ({amnesty}), DeathLink sent."
            )
            self._send_death_link_from_sync(player_state)
        else:
            logger.info(f"[RAC] Death {self._death_count} (Ratchet {cause}): within amnesty ({amnesty}).")

    def _on_player_respawn(self) -> None:
        self._gs.is_dead = False
        arm_cutscenes(self.pine, self._gs.current_planet, "armed")
        self._apply_expected_inventory_sync(clear_unreceived=True)
        _SLOT_STATE.restore(self.pine)

    def _on_pickup_start(self) -> None:
        self._gs.is_picking_up = True
        _SLOT_STATE.take(self.pine)
        if self._gs.tracked_vendor is not None:
            # Vendor session active — only clear armour; weapon/gadget flags are needed for purchase detection
            self._armour_scanner.clear(self.pine)
        else:
            for scanner in self._scanners:
                scanner.clear(self.pine)

    def _on_menu_close(self, new_checks: list[int]) -> None:
        if not self._armour_set_checks_enabled:
            return
        slot_values = {name: self.pine.read_int8(addr) for name, addr in PLAYER_ARMOUR_SLOTS.items()}
        for name, check in ARMOUR_SET_CHECKS.items():
            if check.matches(slot_values):
                self._append_location(new_checks, name, "Armour set")

    def _on_pickup_end(self, new_checks: list[int]) -> None:
        self._gs.is_picking_up = False
        self._gs.picked_up_items.clear()
        for scanner in self._scanners:
            scanner.scan(self.pine)
        for set_key, value in self._gs.picked_up_items.items():
            if set_key.startswith(("weapon:", "gadget:")):
                continue
            for piece in (0x01, 0x02, 0x04, 0x10):
                if value & piece:
                    name = ARMOUR_FLAG_TO_LOCATION.get((set_key, piece))
                    if name:
                        self._append_location(new_checks, name, "Armour")
        _SLOT_STATE.remove(self.pine)
        for scanner in self._scanners:
            scanner.clear(self.pine)
        self._apply_expected_inventory_sync(clear_unreceived=True)
        _SLOT_STATE.restore(self.pine)

    def _enforce_locks(self) -> None:
        if self._gs.is_dead or self._gs.is_picking_up or not self._on_known_planet:
            return
        if (self._gs.is_in_menu or self._gs.is_preloaded) and self._gs.tracked_vendor is not None:
            self._gs.vendor_session.enforce(self.pine)
            return
        if self._gs.is_in_menu or self._gs.is_preloaded:
            return
        for name, address in ARMOUR_ADDRESSES.items():
            expected = self._expected_armour.get(name, 0)
            current = self.pine.read_int8(address)
            if current != expected:
                self.pine.write_int8(address, expected)
                self._prev_armour_sets[name] = expected
        for name, weapon in WEAPONS.items():
            expected = self._expected_weapons.get(name, 0)
            if self.pine.read_int8(weapon.unlocked) != expected:
                self.pine.write_int8(weapon.unlocked, expected)
            mods = self._expected_weapon_mods.get(name, 0)
            for slot_addr, threshold in (
                (weapon.mod_slot_one, 1),
                (weapon.mod_slot_two, 2),
                (weapon.mod_slot_three, 3),
            ):
                expected_mod = 1 if mods >= threshold else 0
                if self.pine.read_int8(slot_addr) != expected_mod:
                    self.pine.write_int8(slot_addr, expected_mod)
        for name, gadget in GADGETS.items():
            expected = self._expected_gadgets.get(name, 0)
            if self.pine.read_int8(gadget.unlocked) != expected:
                self.pine.write_int8(gadget.unlocked, expected)

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Archipelago R&C: Size Matters Client"
        return ui
