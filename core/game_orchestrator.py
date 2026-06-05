
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from CommonClient import logger

from ..interface_orchestrator import Orchestrator
from ..pypine.pypine.pine import Pine
from .address_maps.global_map import build_global_address_map
from .address_maps.planet_map import build_combined_address_map, build_planet_address_map
from .data.addresses import (
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    PLAYER_ADDRS,
    WEAPON_ARRAY_BASE_BY_PLANET,
    TextBoxDisplayAddrs,
)
from .data.armour import ArmourPiece
from .data.cutscenes import POKITARU_RYLLUS_ALT_TRIGGER, arm_cutscenes
from .data.locations.armour_pickups import ARMOUR_FLAG_TO_LOCATION
from .memory.pine_interface import PineInterface
from .states.armour import ArmourState
from .states.armour_sets import ArmourSetCollectedState
from .states.challenges import ClankChallengeState, SkyboardChallengeState
from .states.cutscene import CutsceneState
from .states.display_text_box import DisplayedTextBoxState, DisplayTextBoxState
from .states.memory import load_weapons_for_planet
from .states.menu import MenuState
from .states.planet_unlock import PlanetUnlockState
from .states.planets import Planet, Planets, PlanetState
from .states.player import PlayerMovementState, PlayerState
from .states.quick_select import QuickSelectState
from .states.skill_points import SkillPointState
from .states.titanium_bolts import BOLT_BY_PLANET_AND_DELTA, TitaniumBoltState
from .states.vendor import VendorState
from .states.weapon import (
    GADGET_INTERNAL_TO_LOCATION,
    MOD_INTERNAL_TO_LOCATION,
    WEAPON_INTERNAL_TO_LOCATION,
    WeaponState,
)

_POLL_INTERVAL = 0.1

_PLANET_NAMES: dict[int, str] = {
    p.planet_id: p.name
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}

_TEXT_BOX_BY_PLANET = {tb.planet_id: tb for tb in TextBoxDisplayAddrs}

class GameOrchestrator:

    def __init__(self, pine: Pine, log: Callable[[str], None] | None = None) -> None:
        self._pine          = pine
        self._pine_iface    = PineInterface(pine)
        self._global_map    = build_global_address_map()
        self._log           = log or logger.info

        self._orchestrator  = Orchestrator(
            self._pine_iface, self._global_map, poll_rate=_POLL_INTERVAL
        )
        acc     = self._orchestrator.accessor
        storage = self._orchestrator.storage

        self.armour        = ArmourState(acc, self._global_map, storage)
        self.armour_sets   = ArmourSetCollectedState(acc, self._global_map, storage)
        self.bolts         = TitaniumBoltState(acc, self._global_map, storage)
        self.skill_points  = SkillPointState(acc, self._global_map, storage)
        self.planet_unlock  = PlanetUnlockState(acc, self._global_map, storage)
        self.quick_select   = QuickSelectState(acc, self._global_map, storage)
        self.clank          = ClankChallengeState(acc, self._global_map, storage)
        self.skyboard      = SkyboardChallengeState(acc, self._global_map, storage)

        self.weapons            = WeaponState(acc, self._global_map, storage)
        self.player             = PlayerState(acc, self._global_map, storage)
        self.menu               = MenuState(acc, self._global_map, storage, log=self._log)
        self.vendor             = VendorState(acc, self._global_map, storage)
        self.display_text       = DisplayTextBoxState(acc, self._global_map, storage)
        self.displayed_text_box = DisplayedTextBoxState(acc, self._global_map, storage)
        self.cutscene           = CutsceneState(acc, self._global_map, storage)

        self._send_location:       Callable[[str], None] = lambda _: None
        self._send_deathlink:     Callable[[int], None] = lambda _: None
        self._kill_player:        Callable[[], None]    = lambda: None
        self._reapply_inv:        Callable[[], None]    = lambda: None
        self._death_amnesty:      Callable[[], int]     = lambda: 1
        self._on_goal:            Callable[[], None]    = lambda: None
        self._on_vendor_close:    Callable[[], None]    = lambda: None
        self._on_pause_close:     Callable[[], None]    = lambda: None
        self._on_sprout_suppress: Callable[[], None]    = lambda: None

        self.planet_states: dict[int, PlanetState] = self._build_planet_states(acc, storage)

        state_registry: dict[str, Any] = {
            "armour":             self.armour,
            "armour_sets":        self.armour_sets,
            "bolts":              self.bolts,
            "skill_points":       self.skill_points,
            "planet_unlock":      self.planet_unlock,
            "quick_select":       self.quick_select,
            "clank":              self.clank,
            "skyboard":           self.skyboard,
            "weapons":            self.weapons,
            "player":             self.player,
            "menu":               self.menu,
            "vendor":             self.vendor,
            "display_text":       self.display_text,
            "displayed_text_box": self.displayed_text_box,
            "cutscene":           self.cutscene,
        }
        for pid, ps in self.planet_states.items():
            state_registry[f"planet_{pid:#04x}"] = ps
        self._orchestrator.register_states(state_registry)

        for state in (
            self.armour, self.armour_sets, self.bolts, self.skill_points, self.planet_unlock,
            self.quick_select, self.clank, self.skyboard, self.weapons, self.player,
            self.menu, self.vendor, self.display_text, self.displayed_text_box,
            self.cutscene,
        ):
            state.enter()
        for ps in self.planet_states.values():
            ps.enter()

        self._poll_task: asyncio.Task | None      = None
        self._swap_task: asyncio.Task | None      = None
        self._active_planet_id: int               = 0
        self._checked_locations: set[str]         = set()
        self._defaults_written: bool              = False
        self._initial_load_done: bool             = False
        self._death_count: int                    = 0
        self._transitioning: bool                 = False
        self._travel_close_time: float | None     = None
        self._transition_start_time: float | None = None

    def wire(
        self,
        send_location:       Callable[[str], None],
        send_deathlink:      Callable[[int], None],
        kill_player:         Callable[[], None],
        reapply_inv:         Callable[[], None],
        death_amnesty:       Callable[[], int],
        on_goal:             Callable[[], None] = lambda: None,
        on_vendor_close:     Callable[[], None] = lambda: None,
        on_pause_close:      Callable[[], None] = lambda: None,
        on_sprout_suppress:  Callable[[], None] = lambda: None,
    ) -> None:
        self._send_location      = lambda name: send_location(name) if self._initial_load_done else None
        self._send_deathlink     = send_deathlink
        self._kill_player        = kill_player
        _raw_reapply             = reapply_inv
        self._reapply_inv        = lambda: (_raw_reapply(), self.quick_select.apply())
        self._death_amnesty      = death_amnesty
        self._on_goal            = on_goal
        self._on_vendor_close    = on_vendor_close
        self._on_pause_close     = on_pause_close
        self._on_sprout_suppress = on_sprout_suppress
        self._wire_hooks()

    async def start(self) -> None:
        self.planet_unlock.sync()

        try:
            raw = self._orchestrator.accessor.read_raw(CURRENT_PLANET_ADDRESS, 1)
            self._active_planet_id = raw[0] if raw else 0
        except Exception:
            self._active_planet_id = 0

        if self._active_planet_id in self.planet_states:
            self._log(
                f"[RAC] Connection on {_PLANET_NAMES[self._active_planet_id]} "
                f"— triggering planet_enter immediately."
            )
            self._on_planet_enter(self._active_planet_id)

        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        if self._swap_task:
            self._swap_task.cancel()
            self._swap_task = None

        for state in (
            self.armour, self.armour_sets, self.bolts, self.skill_points, self.planet_unlock,
            self.quick_select, self.clank, self.skyboard, self.weapons, self.player,
            self.menu, self.vendor, self.display_text, self.displayed_text_box,
            self.cutscene,
        ):
            state.exit()
        for ps in self.planet_states.values():
            ps.exit()

        self._defaults_written       = False
        self._initial_load_done      = False
        self._transitioning         = False
        self._travel_close_time     = None
        self._transition_start_time = None
        self.planet_unlock.reset_session()

    async def on_ap_connected(
        self,
        slot_data: dict[str, Any],
        checked_location_names: set[str],
    ) -> None:
        self._checked_locations = checked_location_names
        self.clank.sync_from_ap(checked_location_names)
        self.skyboard.sync_from_ap(checked_location_names)
        self.weapons.sync_from_ap(checked_location_names)
        self.skill_points.sync_from_ap(checked_location_names)
        self.armour.sync_from_ap(checked_location_names)
        self.armour_sets.sync_from_ap(checked_location_names)

    async def on_ap_received_items(self, checked_location_names: set[str]) -> None:
        self._checked_locations = checked_location_names
        self.weapons.sync_from_ap(checked_location_names)
        self._reapply_inv()

    @property
    def vendor_active(self) -> bool:
        from .states.vendor import VendorSessionState
        return self.vendor.session != VendorSessionState.CLOSED

    @property
    def is_picking_up(self) -> bool:
        return self.player.is_picking_up

    @property
    def writes_blocked(self) -> bool:
        """True while a travel menu is open, in the cooldown after it closes, or during a planet transition."""
        from .states.menu import MenuStateValue
        if self.menu.current in (MenuStateValue.SKYBOARD_MENU, MenuStateValue.PLANET_MENU):
            return True
        if self._transitioning:
            return True
        if self._travel_close_time is not None and time.monotonic() < self._travel_close_time:
            return True
        return False

    async def _poll_loop(self) -> None:
        while True:
            try:
                self._orchestrator.poll()
                if self._transitioning:
                    self._poll_planet_transition()
            except Exception as exc:
                logger.warning(f"[RAC] Poll error: {exc}")
            await asyncio.sleep(_POLL_INTERVAL)

    def _on_travel_menu_close(self) -> None:
        """Called when SKYBOARD_MENU or PLANET_MENU closes. Keeps writes blocked for 1 s
        to cover the gap before the planet actually changes."""
        self._travel_close_time = time.monotonic() + 3.0
        self._log("[RAC] Travel menu closed — writes blocked for 3 s.")

    # ── Planet transition fallback ────────────────────────────────────────────

    _TRANSITION_SETTLE_S = 1.0  # minimum seconds after exit before firing the fallback

    def _poll_planet_transition(self) -> None:
        """Fallback planet detection while _transitioning is True.

        If the PlanetState callback didn't fire (e.g. the planet-specific address
        didn't change as expected), CURRENT_PLANET_ADDRESS is polled instead.
        Once a known planet is visible and the settle delay has passed, _on_planet_enter
        is called to clear the transition flag and restore game state.
        """
        if self._transition_start_time is None:
            return
        if time.monotonic() - self._transition_start_time < self._TRANSITION_SETTLE_S:
            return
        try:
            raw = self._orchestrator.accessor.read_raw(CURRENT_PLANET_ADDRESS, 1)
            planet_id = raw[0] if raw else 0
        except Exception:
            return
        if planet_id in _PLANET_NAMES:
            self._log(
                f"[RAC] Transition fallback: {_PLANET_NAMES[planet_id]} detected "
                f"via CURRENT_PLANET_ADDRESS — firing planet_enter."
            )
            self._on_planet_enter(planet_id)

    def _on_planet_enter(self, planet_id: int) -> None:
        if planet_id not in _PLANET_NAMES:
            return
        self._transitioning          = False
        self._travel_close_time      = None
        self._transition_start_time  = None
        self._active_planet_id  = planet_id
        self._maybe_write_defaults()
        load_weapons_for_planet(planet_id)
        self._on_initial_planet_load(planet_id)
        if self._initial_load_done:
            self._reapply_inv()
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
        self.cutscene.reset()
        self._orchestrator.swap_interface(self._pine_iface, self._global_map)
        self._log(f"[RAC] Address map reverted to global on exit from {_PLANET_NAMES.get(planet_id, hex(planet_id))}.")

    async def _swap_to_planet(self, planet_id: int) -> None:
        combined = build_combined_address_map(planet_id, self._global_map)
        self._orchestrator.swap_interface(self._pine_iface, combined)
        self._log(f"[RAC] Address map swapped for {_PLANET_NAMES.get(planet_id, hex(planet_id))}.")
        await asyncio.sleep(1.5)
        self.quick_select.apply()
        self.quick_select.unfreeze()

    def _maybe_write_defaults(self) -> None:
        if self._defaults_written:
            return
        self._defaults_written = True
        self.clank.write_defaults()
        self.skyboard.write_defaults()
        self.quick_select.zero()
        self._log("[RAC] Challenge and skyboard defaults written.")

    def _on_initial_planet_load(self, planet_id: int) -> None:
        if self._initial_load_done:
            return
        if planet_id not in _PLANET_NAMES:
            return
        self._initial_load_done = True
        self._log(f"[RAC] Initial load on {_PLANET_NAMES[planet_id]} — applying world state.")
        if planet_id == Planets.POKITARU.planet_id:
            asyncio.create_task(self._monitor_ryllus_cutscene())
        self.bolts.sync()
        self.skill_points.sync()
        self.armour_sets.sync()
        self._reapply_inv()

    async def _monitor_ryllus_cutscene(self) -> None:
        await asyncio.sleep(1.0)
        last = int.from_bytes(
            self._orchestrator.accessor.read_raw(POKITARU_RYLLUS_ALT_TRIGGER, 4), "little"
        )
        while True:
            await asyncio.sleep(_POLL_INTERVAL)
            current = int.from_bytes(
                self._orchestrator.accessor.read_raw(POKITARU_RYLLUS_ALT_TRIGGER, 4), "little"
            )
            if last == 0x00 and current != 0x00:
                self.planet_unlock.on_ryllus_cutscene_ended()
                self.planet_unlock.sync()
                return
            last = current

    def _wire_hooks(self) -> None:
        self._wire_player_hooks()
        self._wire_bolt_hooks()
        self._wire_skill_point_hooks()
        self._wire_armour_set_hooks()
        self._wire_challenge_hooks()
        self._wire_cutscene_hooks()
        self._wire_planet_hooks()

    def _wire_player_hooks(self) -> None:
        def _pine_proxy():
            acc = self._orchestrator.accessor

            class _P:
                def read_int8(self, a: int) -> int:
                    r = acc.read_raw(a, 1)
                    return r[0] if r else 0
                def write_int8(self, a: int, v: int) -> None:
                    acc.write_raw(a, bytes([v & 0xFF]))
                def read_int16(self, a: int) -> int:
                    r = acc.read_raw(a, 2)
                    return int.from_bytes(r, "little", signed=True) if len(r) >= 2 else 0
                def write_int16(self, a: int, v: int) -> None:
                    acc.write_raw(a, v.to_bytes(2, "little", signed=True))
                def read_int32(self, a: int) -> int:
                    r = acc.read_raw(a, 4)
                    return int.from_bytes(r, "little", signed=True) if len(r) >= 4 else 0
                def write_int32(self, a: int, v: int) -> None:
                    acc.write_raw(a, v.to_bytes(4, "little", signed=False))
                def read_int64(self, a: int) -> int:
                    r = acc.read_raw(a, 8)
                    return int.from_bytes(r, "little") if len(r) >= 8 else 0
                def write_int64(self, a: int, v: int) -> None:
                    acc.write_raw(a, v.to_bytes(8, "little"))
                def read_bytes(self, a: int, n: int) -> bytes:
                    return acc.read_raw(a, n)
                def write_bytes(self, a: int, d: bytes) -> None:
                    acc.write_raw(a, d)
            return _P()

        def on_death(cause: PlayerMovementState) -> None:
            if not self.writes_blocked:
                arm_cutscenes(_pine_proxy(), self._active_planet_id, "reset")
            self.armour.freeze_slots()
            self.armour.clear_all_memory()
            self.armour.apply_item_pickup_armour()
            self._death_count += 1
            amnesty = self._death_amnesty()
            if self._death_count > amnesty:
                logger.info(f"[RAC] Death {self._death_count} ({cause.name}): DeathLink sent.")
                self._send_deathlink(int(cause))
            else:
                logger.info(f"[RAC] Death {self._death_count} ({cause.name}): within amnesty.")

        def on_respawn() -> None:
            self._death_count = 0
            if not self.writes_blocked:
                arm_cutscenes(_pine_proxy(), self._active_planet_id, "armed")
            self._reapply_inv()
            self.armour.restore_equipped_slots()

        def on_pickup_start() -> None:
            if self.vendor_active:
                return
            ps = self.planet_states.get(self._active_planet_id)
            if ps:
                ps.on_pickup_start()

        def on_pickup_end() -> None:
            if self.vendor_active:
                return
            ps = self.planet_states.get(self._active_planet_id)
            if ps:
                asyncio.create_task(_delayed_pickup_end(ps))

        async def _delayed_pickup_end(ps: PlanetState) -> None:
            await asyncio.sleep(0.3)
            ps.on_pickup_end()
            await asyncio.sleep(0.2)
            self._reapply_inv()
            self.armour.restore_equipped_slots()

        self.player.on_death        = on_death
        self.player.on_respawn      = on_respawn
        self.player.on_pickup_start = on_pickup_start
        self.player.on_pickup_end   = on_pickup_end

    def _wire_bolt_hooks(self) -> None:
        def on_bolt_delta(delta: int) -> None:
            name = BOLT_BY_PLANET_AND_DELTA.get((self._active_planet_id, delta))
            if name:
                self._log(f"[RAC] Titanium bolt collected: {name}")
                self._send_location(name)
            else:
                logger.warning(f"[RAC] Unknown bolt delta {delta} on {self._active_planet_id:#04x}")

        self.bolts.on_bolt_delta = on_bolt_delta

    def _wire_skill_point_hooks(self) -> None:
        def on_skill_point_earned(name: str) -> None:
            self._log(f"[RAC] Skill point earned: {name}")
            self._send_location(name)

        self.skill_points.on_skill_point_earned = on_skill_point_earned

    def _wire_armour_set_hooks(self) -> None:
        def on_armour_set_collected(name: str) -> None:
            self._log(f"[RAC] Armour set collected: {name}")
            self._send_location(name)

        self.armour_sets.on_location_check = on_armour_set_collected

    def _wire_cutscene_hooks(self) -> None:
        def on_goal() -> None:
            asyncio.create_task(_deferred_goal())

        async def _deferred_goal() -> None:
            if self._active_planet_id != Planets.QUODRONA.planet_id:
                return
            self._log("[RAC] Goal cutscene fired — Defeat Otto Destruct.")
            self._send_location("Defeat Otto Destruct")
            self._on_goal()

        def on_electroshock() -> None:
            asyncio.create_task(_deferred_electroshock())

        async def _deferred_electroshock() -> None:
            if self._active_planet_id != Planets.METALIS.planet_id:
                return
            self._log("[RAC] Electroshock Gloves cutscene fired.")
            self._send_location("Metalis Electroshock Gloves")

        def on_before_sprout() -> None:
            asyncio.create_task(_deferred_sprout())

        async def _deferred_sprout() -> None:
            if self._active_planet_id != Planets.RYLLUS.planet_id:
                return
            self._log("[RAC] Sprout-O-Matic cutscene fired.")
            self._send_location("Ryllus Sprout-O-Matic")

        def on_sprout_cutscene() -> None:
            self._on_sprout_suppress()
            self._reapply_inv()

        self.cutscene.on_goal                = on_goal
        self.cutscene.on_electroshock_gloves = on_electroshock
        self.cutscene.on_before_sprout       = on_before_sprout
        self.cutscene.on_sprout_cutscene     = on_sprout_cutscene
        self.vendor.on_menu_open            = lambda: self.quick_select.freeze()
        self.vendor.on_menu_close           = lambda: (self.quick_select.unfreeze(), self._on_vendor_close())
        self.menu.set_pause_close_callback(lambda: self._on_pause_close())
        self.menu.on_travel_menu_close      = lambda: self._on_travel_menu_close()

    def _wire_challenge_hooks(self) -> None:
        self.clank.set_location_check_callback(
            lambda name: (self._log(f"[RAC] Clank challenge completed: {name}"),
                          self._send_location(name))
        )
        self.skyboard.set_location_check_callback(
            lambda name: (self._log(f"[RAC] Skyboard race completed: {name}"),
                          self._send_location(name))
        )

    def _wire_planet_hooks(self) -> None:
        for planet_id, ps in self.planet_states.items():
            def make_armour_hook(pid: int):
                def on_armour_acquired(name: str, piece: ArmourPiece) -> None:
                    self.armour.add_location_piece(name, piece)
                    loc = ARMOUR_FLAG_TO_LOCATION.get((name, piece))
                    if loc:
                        self._log(f"[RAC] Armour acquired on {pid:#04x}: {loc}")
                        self._send_location(loc)
                return on_armour_acquired
            ps.on_armour_acquired = make_armour_hook(planet_id)

            def make_weapon_hook(pid: int):
                def on_weapon_purchased(name: str) -> None:
                    loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
                    if loc:
                        self._send_location(loc)
                return on_weapon_purchased
            ps.on_vendor_weapon_purchased = make_weapon_hook(planet_id)

            def make_gadget_hook(pid: int):
                def on_gadget_purchased(name: str) -> None:
                    loc = GADGET_INTERNAL_TO_LOCATION.get(name)
                    if loc:
                        self._send_location(loc)
                return on_gadget_purchased
            ps.on_vendor_gadget_purchased = make_gadget_hook(planet_id)

            def make_mod_hook(pid: int):
                def on_mod_purchased(weapon: str, slot: str) -> None:
                    loc = MOD_INTERNAL_TO_LOCATION.get((weapon, slot))
                    if loc:
                        self._send_location(loc)
                return on_mod_purchased
            ps.on_vendor_mod_purchased = make_mod_hook(planet_id)

    def _build_planet_states(self, acc, storage) -> dict[int, PlanetState]:
        states: dict[int, PlanetState] = {}
        for planet_id in PLAYER_ADDRS:
            name = _PLANET_NAMES.get(planet_id, f"Planet {planet_id:#04x}")
            planet_map = build_planet_address_map(planet_id)

            ps = PlanetState(
                accessor=acc,
                addresses=planet_map,
                storage=storage,
                name=name,
                planet_id=planet_id,
                menu_addr=MENU_ADDR_BY_PLANET_ID.get(planet_id),
                log=self._log,
            )

            ps.add_enter_callback(lambda pid=planet_id: self._on_planet_enter(pid))
            ps.add_exit_callback(lambda pid=planet_id: self._on_planet_exit(pid))
            ps.set_armour(self.armour)
            ps.set_player_state(self.player)

            if planet_id in WEAPON_ARRAY_BASE_BY_PLANET:
                ps.set_weapon_state(self.weapons)

            if planet_id in MENU_ADDR_BY_PLANET_ID:
                ps.set_menu_state(self.menu, self.vendor)

            tb = _TEXT_BOX_BY_PLANET.get(planet_id)
            if tb:
                ps.set_display_text_box(self.display_text, tb)
                ps.set_displayed_text_box(self.displayed_text_box)

            ps.set_inventory_callbacks(
                reapply_inv           = lambda: self._reapply_inv(),
                get_checked_locations = lambda: self._checked_locations,
            )
            states[planet_id] = ps
        return states

    def _current_planet_id(self) -> int:
        return self._active_planet_id
