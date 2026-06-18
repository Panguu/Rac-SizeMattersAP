from __future__ import annotations

import asyncio

from CommonClient import logger

from ..core import CURRENT_PLANET_ADDRESS, TextColour, colored_text, load_weapons_for_planet
from ..universal_tracker import PLANET_ID_TO_REGION
from .constants import EXPECTED_GAME_ID, POLL_INTERVAL


class PineMixin:
    async def reconnect_pine(self) -> None:
        async with self._pine_lock:
            self.pine_connected = False
            try:
                self.pine.disconnect()
            except Exception:
                pass
        await self._attempt_pine_connect(is_reconnect=True)

    async def _attempt_pine_connect(self, is_reconnect: bool = False) -> None:
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

            self._log(
                "[RAC] Reconnected to PCSX2 - R&C: Size Matters detected."
                if is_reconnect else
                "[RAC] Connected to PCSX2 - R&C: Size Matters detected."
            )
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
        await self._wiring.start()
        # Baseline before applying so the catch-up batch of items already
        # received before this PCSX2 connection doesn't pop a notification.
        self._notification_item_index = len(self.items_received)
        await self._apply_received_items()
        await self._send_map_page(self.current_planet)
        if is_reconnect:
            self._write_notification_text(colored_text(
                "Reconnected to ", TextColour.YELLOW, "PCSX2", TextColour.WHITE,
            ))

    async def _read_initial_state(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            async with self._pine_lock:
                await loop.run_in_executor(None, self._read_initial_state_sync)
        except Exception as exc:
            self._log(f"[RAC] Initial state read failed: {exc}", "warning")

    def _read_initial_state_sync(self) -> None:
        self._prev_planet = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        self.current_planet = PLANET_ID_TO_REGION.get(self._prev_planet, "Galaxy")
        self._gs.weapons_ready = load_weapons_for_planet(self._prev_planet)
        self._gs.current_planet = self._prev_planet
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
        planet = self.pine.read_int8(CURRENT_PLANET_ADDRESS)
        if planet != self._prev_planet:
            self._prev_planet = planet
            self._gs.current_planet = planet
            self.current_planet = PLANET_ID_TO_REGION.get(planet, "Galaxy")
            load_weapons_for_planet(planet)
        return []

    def _append_location_by_name(self, name: str) -> None:
        """Single-name variant used by GameWiring hooks — dispatches async immediately."""
        checks: list[int] = []
        self._append_location(checks, name, "GameWiring")
        if checks:
            asyncio.create_task(self._check_locations(checks))

    def _append_location(self, checks: list[int], name: str, kind: str) -> None:
        loc_id = self._location_name_to_id.get(name)
        if loc_id is None:
            logger.warning(f"[RAC] {kind}: unknown location {name!r} — not in location table")
            return
        if loc_id in self._locally_checked_locations or loc_id in self.checked_locations:
            return
        server_locations = getattr(self, "server_locations", None)
        if server_locations is not None and loc_id not in server_locations:
            logger.warning(f"[RAC] {kind}: {name!r} (id={loc_id}) not in server locations"
                           " — was game generated with the current options?")
            return
        checks.append(loc_id)
        self._log(f"[RAC] {kind} checked: {name}")

    async def _check_locations(self, locations: list[int]) -> None:
        unique_locations = set(locations) - self._locally_checked_locations
        if not unique_locations:
            return
        self._locally_checked_locations.update(unique_locations)
        await self.check_locations(unique_locations)

