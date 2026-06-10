from __future__ import annotations

import asyncio
import time

from ..address_maps.planet_map import build_combined_address_map
from ..data.addresses import CURRENT_PLANET_ADDRESS
from ..data.cutscenes import POKITARU_RYLLUS_ALT_TRIGGER
from ..memory import load_weapons_for_planet
from ..data.planets import Planets
from ._constants import PLANET_NAMES, POLL_INTERVAL

_TRANSITION_SETTLE_S = 1.0


class PlanetLifecycleMixin:
    """Planet enter/exit, address-map swaps, initial load, and transition handling."""

    def _on_travel_menu_close(self) -> None:
        self._travel_close_time = time.monotonic() + 3.0
        self._log("[RAC] Travel menu closed — writes blocked for 3 s.")
        asyncio.create_task(self._reapply_after_challenge_close())

    async def _reapply_after_challenge_close(self) -> None:
        await asyncio.sleep(3.1)
        self._reapply_inv()

    def _poll_planet_transition(self) -> None:
        if self._transition_start_time is None:
            return
        if time.monotonic() - self._transition_start_time < _TRANSITION_SETTLE_S:
            return
        try:
            raw = self._orchestrator.accessor.read_raw(CURRENT_PLANET_ADDRESS, 1)
            planet_id = raw[0] if raw else 0
        except Exception:
            return
        if planet_id in PLANET_NAMES:
            self._log(
                f"[RAC] Transition fallback: {PLANET_NAMES[planet_id]} detected "
                f"via CURRENT_PLANET_ADDRESS — firing planet_enter."
            )
            self._on_planet_enter(planet_id)

    def _on_planet_enter(self, planet_id: int) -> None:
        if planet_id not in PLANET_NAMES:
            return
        self._transitioning         = False
        self._travel_close_time     = None
        self._transition_start_time = None
        self._active_planet_id      = planet_id
        self.clank.write_unlocks()
        self.skyboard.write_defaults()
        self.skin.apply(self._orchestrator.accessor)
        load_weapons_for_planet(planet_id)
        self._on_initial_planet_load(planet_id)
        if self._initial_load_done:
            self._reapply_inv()
        self.armour.apply_world_armour()
        self.armour.restore_equipped_slots()
        if self._swap_task:
            self._swap_task.cancel()
        self._swap_task = asyncio.create_task(self._swap_to_planet(planet_id))

    def _on_planet_exit(self, planet_id: int) -> None:
        if self._active_planet_id == planet_id:
            self._active_planet_id = 0
        self._transitioning         = True
        self._travel_close_time     = None
        self._transition_start_time = time.monotonic()
        self.armour.sync_slots()
        self.quick_select.freeze()
        if self._swap_task:
            self._swap_task.cancel()
            self._swap_task = None
        self._orchestrator.swap_interface(self._pine_iface, self._global_map)
        self._log(
            f"[RAC] Address map reverted to global on exit from "
            f"{PLANET_NAMES.get(planet_id, hex(planet_id))}."
        )

    async def _swap_to_planet(self, planet_id: int) -> None:
        combined = build_combined_address_map(planet_id, self._global_map)
        self._orchestrator.swap_interface(self._pine_iface, combined)
        self._log(f"[RAC] Address map swapped for {PLANET_NAMES.get(planet_id, hex(planet_id))}.")
        await asyncio.sleep(2.0)
        if not self._first_swap_done:
            self._first_swap_done = True
            self.quick_select.zero()
        else:
            # Write the snapshot BEFORE enabling polling so the poller's first
            # read after unfreeze sees our values, not the game's defaults.
            self.quick_select.restore()
            self.quick_select.unfreeze()

    def _on_initial_planet_load(self, planet_id: int) -> None:
        if self._initial_load_done:
            return
        if planet_id not in PLANET_NAMES:
            return
        self._initial_load_done = True
        self._log(f"[RAC] Initial load on {PLANET_NAMES[planet_id]} — applying world state.")
        self.clank.write_defaults()
        self.quick_select.zero()
        if planet_id == Planets.POKITARU.planet_id:
            asyncio.create_task(self._monitor_ryllus_cutscene())
        self.missions.preset_missions()
        self.bolts.sync()
        self.skill_points.sync()
        self.armour_sets.sync()
        self._reapply_inv()
        self.armour.apply_world_armour()

    async def _monitor_ryllus_cutscene(self) -> None:
        await asyncio.sleep(1.0)
        last = int.from_bytes(
            self._orchestrator.accessor.read_raw(POKITARU_RYLLUS_ALT_TRIGGER, 4), "little"
        )
        while True:
            await asyncio.sleep(POLL_INTERVAL)
            current = int.from_bytes(
                self._orchestrator.accessor.read_raw(POKITARU_RYLLUS_ALT_TRIGGER, 4), "little"
            )
            if last == 0x00 and current != 0x00:
                self.planet_unlock.on_ryllus_cutscene_ended()
                self.planet_unlock.sync()
                return
            last = current
