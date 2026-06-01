from __future__ import annotations

import asyncio

from CommonClient import logger

from ..core.data import (
    AUTO_UNLOCK_ADDRESSES,
    BOLT_BY_PLANET_AND_DELTA,
    BOLT_PICKUP_MASK,
    CURRENT_PLANET_ADDRESS,
    CUTSCENE_BEFORE_SPROUT_O_MATIC,
    ELECTROSHOCK_GLOVES_CUTSCENE,
    ENTER_CUTSCENES,
    INFOBOT_UNLOCK_VALUE,
    LOCATION_SKILL_POINTS,
    PLANET_STATE_ADDRESSES,
    PLAYER_ADDRS,
    PLAYER_STATE,
    SKILL_POINT_ADDRESS,
    SPROUT_O_MATIC_CUTSCENE,
    Planets,
    PlayerState,
    arm_cutscenes,
)
from ..core.memory import BOLTS, load_weapons_for_planet
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, POLL_INTERVAL
from .cutscene_handler import _GOAL_CUTSCENE
from .deathlink import _dead


class PineMixin:
    async def disconnect_pine(self) -> None:
        async with self._pine_lock:
            self.pine_connected = False
            try:
                self.pine.disconnect()
            except Exception:
                pass
        self._log("[RAC] Disconnected from PCSX2. Use /reconnect to reconnect.")

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
            self._log("[RAC] Not connected to PCSX2.")
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            loaded = await loop.run_in_executor(None, load_weapons_for_planet, self._prev_planet)
        if loaded:
            self._log(f"[RAC] Weapon addresses reloaded for planet {self._prev_planet:#04x}.")
            self._pending_item_apply = True
            await self._apply_received_items()
        else:
            self._log(f"[RAC] No weapon addresses for planet {self._prev_planet:#04x}.", "warning")

    async def _attempt_pine_connect(self) -> None:
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            try:
                await loop.run_in_executor(None, self.pine.connect)
                game_id = await loop.run_in_executor(None, self.pine.get_game_id)
            except Exception:
                self._log("[RAC] Could not connect to PCSX2. Use /reconnect once the emulator is running.")
                self.pine_connected = False
                return

            if game_id != EXPECTED_GAME_ID:
                self._log(f"[RAC] Wrong game in PCSX2: {game_id!r} (expected {EXPECTED_GAME_ID!r}).", "warning")
                self.pine_connected = False
                return

            self._log("[RAC] Connected to PCSX2 - R&C: Size Matters detected.")
            self.pine_connected = True
            try:
                await loop.run_in_executor(None, self._read_initial_state_sync)
            except Exception as exc:
                self._log(
                    f"[RAC] Initial state read failed: {exc}. Use /reconnect once the game is fully loaded.",
                    "warning",
                )
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
            self._log(f"[RAC] Initial state read failed: {exc}", "warning")

    def _read_initial_state_sync(self) -> None:
        self._challenge_defaults_written = False
        self._challenge_poller.initialize()
        self._prev_skill_points = self.pine.read_int64(SKILL_POINT_ADDRESS)
        self._prev_bolt_pickup = self.pine.read_int64(BOLTS.pickup) & BOLT_PICKUP_MASK
        self._prev_planet = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        self.current_planet = PLANET_ID_TO_REGION.get(self._prev_planet, "Galaxy")
        self._gs.weapons_ready = load_weapons_for_planet(self._prev_planet)
        self._state_addr = PLAYER_ADDRS.get(self._prev_planet, (PLAYER_STATE,))[0]
        self._prev_player_state = self.pine.read_int16(self._state_addr)
        self._prev_goal_cutscene = self.pine.read_int32(_GOAL_CUTSCENE.address)
        if self._prev_planet == Planets.RYLLUS.planet_id:
            self._prev_ryllus_enter = self.pine.read_int32(ENTER_CUTSCENES["ryllus"])
            self._prev_before_sprout_cutscene = self.pine.read_int32(CUTSCENE_BEFORE_SPROUT_O_MATIC)
            self._prev_sprout_cutscene = self.pine.read_int32(SPROUT_O_MATIC_CUTSCENE)
        if self._prev_planet == Planets.METALIS.planet_id:
            self._prev_electroshock_cutscene = self.pine.read_int32(ELECTROSHOCK_GLOVES_CUTSCENE)
        self._gs.current_planet = self._prev_planet
        self._gs.state_addr = self._state_addr
        self._gs.is_dead = _dead(self._prev_player_state)
        self._gs.is_picking_up = self._prev_player_state == PlayerState.Pickup
        self._gs.is_preloaded = False
        self._gs.is_in_menu = False
        self._gs.tracked_vendor = self._prev_planet if self._on_known_planet else None
        arm_cutscenes(self.pine, self._prev_planet, "armed")
        self._skyboard_poller.initialize(self.pine)
        self._apply_player_inventory_sync()
        self._apply_world_states_sync()

    async def game_watcher(self) -> None:
        while not self.exit_event.is_set():
            await asyncio.sleep(POLL_INTERVAL)
            if not self.pine_connected:
                continue
            try:
                await self._poll_game()
            except Exception as exc:
                self._log(f"[RAC] Lost PINE connection or poll failed: {exc}", "warning")
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
        planet_changed = planet != self._prev_planet
        if planet_changed:
            self._prev_planet = planet
            self._state_addr = PLAYER_ADDRS.get(planet, (PLAYER_STATE,))[0]
            self._gs.current_planet = planet
            self.current_planet = PLANET_ID_TO_REGION.get(planet, "Galaxy")
            self._gs.state_addr = self._state_addr
            arm_cutscenes(self.pine, planet, "armed")
            self._prev_bolt_pickup = self.pine.read_int64(BOLTS.pickup) & BOLT_PICKUP_MASK
            logger.info(f"[RAC] Planet loaded: {self.current_planet}")
            if not self._challenge_defaults_written:
                self._challenge_poller.write_defaults(self.pine)
                self._skyboard_poller.write_defaults(self.pine)
                self._challenge_defaults_written = True
                logger.info("[RAC] Challenge and skyboard addresses initialised.")
            if self._on_known_planet:
                load_weapons_for_planet(planet)
                self._gs.weapons_ready = True
                self._gs.tracked_vendor = planet
                self._apply_player_inventory_sync()
                self._apply_world_states_sync()
            else:
                self._gs.weapons_ready = False
                self._gs.tracked_vendor = None
                self._log(f"[RAC] Unknown planet {self._prev_planet:#04x} — skipping inventory writes.")

        player_state = self.pine.read_int16(self._state_addr)
        if not _dead(self._prev_player_state) and _dead(player_state):
            self._on_player_death(player_state)
        elif _dead(self._prev_player_state) and player_state == PlayerState.Alive:
            self._on_player_respawn()
        elif self._prev_player_state != PlayerState.Pickup and player_state == PlayerState.Pickup:
            self._on_pickup_start()
        elif self._prev_player_state == PlayerState.Pickup and player_state != PlayerState.Pickup:
            self._on_pickup_end(new_checks)
        elif (self._prev_player_state != PlayerState.Alive
              and player_state == PlayerState.Alive
              and not _dead(self._prev_player_state)):
            self._on_menu_close(new_checks)
        self._prev_player_state = player_state

        skill_points = self.pine.read_int64(SKILL_POINT_ADDRESS)
        new_skill_bits = skill_points & ~self._prev_skill_points
        if new_skill_bits:
            self._log(
                f"[RAC] Skill point address changed by 0x{new_skill_bits:016X} (raw value 0x{skill_points:016X})"
            )
        for name, mask in LOCATION_SKILL_POINTS.items():
            if new_skill_bits & mask:
                self._append_location(new_checks, name, "Skill point")
        self._prev_skill_points = skill_points

        bolt_pickup = self.pine.read_int64(BOLTS.pickup) & BOLT_PICKUP_MASK
        bolt_delta = bolt_pickup - self._prev_bolt_pickup
        if bolt_delta > 0 and (bolt_delta & (bolt_delta - 1)) == 0:
            self._log(f"[RAC] Titanium bolt address changed by {bolt_delta}")
            name = BOLT_BY_PLANET_AND_DELTA.get((planet, bolt_delta))
            if name:
                self._append_location(new_checks, name, "Titanium bolt")
        elif bolt_delta > 0:
            self._log(
                f"[RAC] Titanium bolt delta {bolt_delta} is not a power of 2 — ignoring (likely init noise).",
                "warning",
            )
        self._prev_bolt_pickup = bolt_pickup

        self._poll_cutscenes_sync(planet, new_checks)

        self._vendor_poller.tick(self.pine)
        self._challenge_poller.tick(self.pine, new_checks, self._append_location)
        self._skyboard_poller.tick(self.pine, new_checks, self._append_location)

        for loc_name in self._pending_vendor_checks:
            self._append_location(new_checks, loc_name, "Vendor purchase")
        self._pending_vendor_checks.clear()

        self._enforce_locks(new_checks)
        if not planet_changed:
            self._enforce_planet_unlocks()

        return new_checks

    def _append_location(self, checks: list[int], name: str, kind: str) -> None:
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None:
            logger.warning(f"[RAC] {kind}: unknown location {name!r} — not in location table")
            return
        if loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations and loc_id not in server_locations:
            logger.warning(f"[RAC] {kind}: {name!r} (id={loc_id}) not in server locations"
                           " — was game generated with the current options?")
            return
        checks.append(loc_id)
        logger.info(f"[RAC] {kind} checked: {name}")

    async def _check_locations(self, locations: list[int]) -> None:
        unique_locations = set(locations) - self._locally_checked_locations
        if not unique_locations:
            return
        self._locally_checked_locations.update(unique_locations)
        await self.check_locations(unique_locations)

    def _enforce_planet_unlocks(self) -> None:
        """Enforce planet-unlock addresses every tick.

        The game increments a planet's unlock address when the player
        completes it normally (e.g. finishing Ryllus sets the Kalidon address
        to 3).  We reset any AP-gated address the game bumped without the
        player having received the matching infobot from AP.

        Auto-unlock planets (Ryllus, Metalis, Dreamtime, Inside Clank) are
        always held at INFOBOT_UNLOCK_VALUE since they have no infobot item.
        """
        for key, addr in PLANET_STATE_ADDRESSES.items():
            if addr == 0:
                continue  # placeholder — real address not yet confirmed
            expected = self._planet_state.get(key)
            if self.pine.read_int8(addr) != expected:
                self.pine.write_int8(addr, expected)

        for addr in AUTO_UNLOCK_ADDRESSES:
            if self.pine.read_int8(addr) < INFOBOT_UNLOCK_VALUE:
                self.pine.write_int8(addr, INFOBOT_UNLOCK_VALUE)

    def _enforce_locks(self, new_checks: list[int]) -> None:
        if self._gs.is_picking_up or not self._on_known_planet:
            return
        if self._gs.is_dead:
            return
        if (self._gs.is_in_menu or self._gs.is_preloaded) and self._gs.tracked_vendor is not None:
            self._gs.vendor_session.enforce(self.pine)
            return
        if self._gs.is_in_menu or self._gs.is_preloaded:
            return
