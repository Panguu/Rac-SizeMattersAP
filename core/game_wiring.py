"""
Central startup and wiring for the new state management system.

Creates all global and per-planet state instances, wires their hooks to AP
client callbacks, and starts the async polling tasks.

Usage from the client:

    wiring = GameWiring(pine)
    wiring.wire(
        send_location  = ctx._append_location_by_name,
        send_deathlink = ctx._send_death_link_from_sync,
        kill_player    = ctx._kill_player_sync,
        reapply_inv    = ctx._apply_player_inventory_sync,
        death_amnesty  = lambda: ctx.death_amnesty,
    )
    await wiring.start()

On AP connect / reconnect:
    await wiring.on_ap_connected(slot_data, ctx.checked_location_names)

On items received:
    await wiring.on_ap_received_items(ctx.checked_location_names)
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data.addresses import (
    ARMOUR_BASE,
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    PLAYER_ADDRS,
    PRELOAD_MENU_ADDR_BY_PLANET_ID,
    TITANIUM_BOLT_BASE,
    WEAPON_ARRAY_BASE_BY_PLANET,
    TextBoxDisplayAddrs,
)
from .data.armour import ArmourPiece
from .data.armour_pickups import ARMOUR_FLAG_TO_LOCATION
from .data.cutscenes import POKITARU_RYLLUS_ALT_TRIGGER, arm_cutscenes
from .states.armour import ArmourState
from .states.challenges import ClankChallengeState, SkyboardChallengeState
from .states.controller import ControllerState
from .states.display_text_box import DisplayTextBoxState
from .states.menu import MenuState
from .states.planet_unlock import PlanetUnlockState
from .states.planets import Planets, PlanetState
from .states.player import PlayerMovementState, PlayerState
from .states.skill_points import SkillPointState
from .states.titanium_bolts import BOLT_BY_PLANET_AND_DELTA, TitaniumBoltState
from .states.vendor import VendorState
from .states.weapon import (
    GADGET_INTERNAL_TO_LOCATION,
    MOD_INTERNAL_TO_LOCATION,
    WEAPON_INTERNAL_TO_LOCATION,
    WeaponState,
)

_POLL_MS = 100  # matches old POLL_INTERVAL

# planet_id → display name (for logging)
_PLANET_NAMES: dict[int, str] = {
    p.planet_id: p.name
    for p in vars(Planets).values()
    if hasattr(p, "planet_id")
}

_TEXT_BOX_BY_PLANET = {tb.planet_id: tb for tb in TextBoxDisplayAddrs}


class GameWiring:
    """Owns all state instances and connects them to the AP client."""

    def __init__(self, pine: Pine) -> None:
        # ── global fixed-address states ──────────────────────────────────────
        self.armour        = ArmourState(pine, ARMOUR_BASE)
        self.bolts         = TitaniumBoltState(pine, TITANIUM_BOLT_BASE)
        self.skill_points  = SkillPointState(pine)
        self.planet_unlock = PlanetUnlockState(pine)
        self.clank         = ClankChallengeState(pine)
        self.skyboard      = SkyboardChallengeState(pine)

        # ── global states activated per planet ───────────────────────────────
        self.weapons      = WeaponState(pine)
        self.player       = PlayerState(pine)
        self.menu         = MenuState(pine)
        self.vendor       = VendorState(pine)
        self.controller   = ControllerState(pine)
        self.display_text = DisplayTextBoxState(pine)

        # ── runtime ──────────────────────────────────────────────────────────
        self._tasks: list[asyncio.Task] = []
        self._death_count: int = 0
        self._checked_locations: set[str] = set()
        self._active_planet_id: int = 0
        self._defaults_written: bool = False
        self._initial_load_done: bool = False

        # callbacks — set by wire()
        self._send_location:  Callable[[str], None]  = lambda _: None
        self._send_deathlink: Callable[[int], None]  = lambda _: None
        self._kill_player:    Callable[[], None]     = lambda: None
        self._reapply_inv:    Callable[[], None]     = lambda: None

        # ── per-planet states ────────────────────────────────────────────────
        self.planet_states: dict[int, PlanetState] = self._build_planet_states(pine)
        self._death_amnesty:  Callable[[], int]      = lambda: 1

    @property
    def vendor_active(self) -> bool:
        """True while a vendor session is preloading or open — used to guard inventory writes."""
        from .states.vendor import VendorSessionState
        return self.vendor.session != VendorSessionState.CLOSED

    # ── public API ────────────────────────────────────────────────────────────

    def wire(
        self,
        send_location:  Callable[[str], None],
        send_deathlink: Callable[[int], None],
        kill_player:    Callable[[], None],
        reapply_inv:    Callable[[], None],
        death_amnesty:  Callable[[], int],
    ) -> None:
        """Bind AP client callbacks then wire all state hooks."""
        self._send_location  = lambda name: send_location(name) if self._initial_load_done else None
        self._send_deathlink = send_deathlink
        self._kill_player    = kill_player
        self._reapply_inv    = reapply_inv
        self._death_amnesty  = death_amnesty
        self._wire_hooks()

    async def start(self) -> None:
        """Start all persistent polling tasks."""
        interval = _POLL_MS

        # Enforce auto-unlock planet state immediately on PINE connect, before the first poll tick.
        asyncio.create_task(self.planet_unlock.apply())

        # Global always-on states
        self._tasks += [
            asyncio.create_task(self.bolts.poll(0, interval, lambda *_: None)),
            asyncio.create_task(self.skill_points.poll(0, interval, lambda *_: None)),
            asyncio.create_task(self.planet_unlock.poll(0, interval, lambda *_: None)),
            asyncio.create_task(self.clank.poll(0, interval, lambda *_: None)),
            asyncio.create_task(self.skyboard.poll(0, interval, lambda *_: None)),
        ]

        # Seed active planet from current memory so pickup routing works immediately
        try:
            self._active_planet_id = self.player.pine.read_int8(CURRENT_PLANET_ADDRESS)
        except Exception:
            self._active_planet_id = 0

        # Per-planet planet-detection polls — each watches CURRENT_PLANET_ADDRESS
        def make_planet_cb(pid: int):
            def cb(old: int, new: int) -> None:
                if new == pid:
                    self._active_planet_id = pid
                elif self._active_planet_id == pid:
                    self._active_planet_id = 0
            return cb

        for ps in self.planet_states.values():
            self._tasks.append(
                asyncio.create_task(
                    ps.poll(CURRENT_PLANET_ADDRESS, interval, make_planet_cb(ps.planet_id))
                )
            )

    async def _monitor_ryllus_cutscene(self) -> None:
        """Poll the Pokitaru alt-trigger address; release Ryllus when it changes from 0x00 to any value."""
        await asyncio.sleep(1.0)
        pine = self.planet_unlock.pine
        last = pine.read_int32(POKITARU_RYLLUS_ALT_TRIGGER)
        while True:
            await asyncio.sleep(_POLL_MS / 1000)
            current = pine.read_int32(POKITARU_RYLLUS_ALT_TRIGGER)
            if last == 0x00 and current != 0x00:
                self.planet_unlock.on_ryllus_cutscene_ended()
                await self.planet_unlock.apply()
                return
            last = current

    async def stop(self) -> None:
        """Cancel all polling tasks."""
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
        self._defaults_written = False
        self._initial_load_done = False
        self.planet_unlock.reset_session()
        await self.player.deactivate()
        await self.weapons.deactivate()
        await self.menu.deactivate()
        await self.display_text.deactivate()

    async def on_ap_connected(
        self,
        slot_data: dict[str, Any],
        checked_location_names: set[str],
    ) -> None:
        """
        Called when the AP server confirms connection.
        Syncs all state from already-checked locations and applies to memory.
        """
        self._checked_locations = checked_location_names

        # Challenges sync their own completed sets
        self.clank.sync_from_ap(checked_location_names)
        self.skyboard.sync_from_ap(checked_location_names)

        # Sync vendor purchase state (apply() deferred until InventoryMixin is removed)
        self.weapons.sync_from_ap(checked_location_names)

        # Titanium bolts and skill points — synced here, applied on first planet load
        self.bolts.sync_from_ap(checked_location_names)
        self.skill_points.sync_from_ap(checked_location_names)

        # Planet unlock state is enforced every poll tick via PlanetUnlockState

    async def on_ap_received_items(self, checked_location_names: set[str]) -> None:
        """Called when new items arrive from AP. Reapplies inventory to memory."""
        self._checked_locations = checked_location_names
        self.weapons.sync_from_ap(checked_location_names)
        self.bolts.sync_from_ap(checked_location_names)
        self.skill_points.sync_from_ap(checked_location_names)
        self._reapply_inv()

    # ── internal: hook wiring ─────────────────────────────────────────────────

    def _wire_hooks(self) -> None:
        self._wire_player_hooks()
        self._wire_bolt_hooks()
        self._wire_skill_point_hooks()
        self._wire_challenge_hooks()
        self._wire_planet_hooks()

    def _maybe_write_defaults(self) -> None:
        if self._defaults_written:
            return
        self._defaults_written = True
        self.clank.write_defaults()
        self.skyboard.write_defaults()
        logger.info("[RAC] Challenge and skyboard defaults written.")

    def _on_initial_planet_load(self, planet_id: int) -> None:
        """Called on every planet entry but only acts on the first known planet per session.

        Applies all persistent AP state to memory: bolts, skill points, armour,
        weapons, and planet unlock state. Skipped entirely on unknown planets.
        """
        if self._initial_load_done:
            return
        if planet_id not in _PLANET_NAMES:
            return
        self._initial_load_done = True
        logger.info(f"[RAC] Initial planet load on {_PLANET_NAMES[planet_id]} — applying world state.")
        if planet_id == Planets.POKITARU.planet_id:
            asyncio.create_task(self._monitor_ryllus_cutscene())
        asyncio.create_task(self.bolts.apply())
        asyncio.create_task(self.skill_points.apply())
        self._reapply_inv()

    def _wire_player_hooks(self) -> None:
        def on_death(cause: PlayerMovementState) -> None:
            arm_cutscenes(self.player.pine, self._current_planet_id(), "reset")
            self._death_count += 1
            amnesty = self._death_amnesty()
            if self._death_count > amnesty:
                logger.info(
                    f"[RAC] Death {self._death_count} ({cause.name}): "
                    f"amnesty exceeded ({amnesty}), DeathLink sent."
                )
                self._send_deathlink(int(cause))
            else:
                logger.info(
                    f"[RAC] Death {self._death_count} ({cause.name}): "
                    f"within amnesty ({amnesty})."
                )
            logger.info(f"[RAC] Death — Armour Locations: {self.armour.location_collected_armour}")
            logger.info(f"[RAC] Death — sets_bitmask:     {self.armour.sets_bitmask}")
            async def _death_armour_reset(a=self.armour):
                await a.read_armour_slots()
                await a.apply_location_armour()
            asyncio.create_task(_death_armour_reset())

        def on_respawn() -> None:
            self._death_count = 0
            arm_cutscenes(self.player.pine, self._current_planet_id(), "armed")
            logger.info(f"[RAC] Respawn — Armour Locations: {self.armour.location_collected_armour}")
            logger.info(f"[RAC] Respawn — sets_bitmask:     {self.armour.sets_bitmask}")
            self._reapply_inv()
            asyncio.create_task(self.armour.apply_item_pickup_armour())

        def on_pickup_start() -> None:
            if self.vendor_active:
                logger.info("[RAC] Pickup start suppressed — vendor session active.")
                return
            planet_id = self._current_planet_id()
            ps = self.planet_states.get(planet_id)
            logger.info(f"[RAC] Pickup start — planet {planet_id:#04x}, state found: {ps is not None}")
            if ps:
                asyncio.create_task(ps.on_pickup_start())

        def on_pickup_end() -> None:
            if self.vendor_active:
                logger.info("[RAC] Pickup end suppressed — vendor session active.")
                return
            planet_id = self._current_planet_id()
            ps = self.planet_states.get(planet_id)
            logger.info(f"[RAC] Pickup end   — planet {planet_id:#04x}, state found: {ps is not None}")
            if ps:
                asyncio.create_task(ps.on_pickup_end())

        self.player.on_death         = on_death
        self.player.on_respawn       = on_respawn
        self.player.on_pickup_start  = on_pickup_start
        self.player.on_pickup_end    = on_pickup_end

        # DeathLink receive: kill the player
        # caller should set: wiring.receive_death = lambda: wiring._kill_player()

    def _wire_bolt_hooks(self) -> None:
        def on_bolt_delta(delta: int) -> None:
            planet_id = self._current_planet_id()
            name = BOLT_BY_PLANET_AND_DELTA.get((planet_id, delta))
            if name:
                logger.info(f"[RAC] Titanium bolt collected: {name}")
                self._send_location(name)
            else:
                logger.warning(f"[RAC] Unknown bolt delta {delta} on planet {planet_id:#04x}")

        self.bolts.on_bolt_delta = on_bolt_delta

    def _wire_skill_point_hooks(self) -> None:
        def on_skill_point_earned(name: str) -> None:
            logger.info(f"[RAC] Skill point earned: {name}")
            self._send_location(name)

        self.skill_points.on_skill_point_earned = on_skill_point_earned

    def _wire_challenge_hooks(self) -> None:
        def on_challenge(name: str) -> None:
            logger.info(f"[RAC] Clank challenge completed: {name}")
            self._send_location(name)

        def on_race(name: str) -> None:
            logger.info(f"[RAC] Skyboard race completed: {name}")
            self._send_location(name)

        self.clank.on_challenge_completed   = on_challenge
        self.skyboard.on_race_completed     = on_race

    def _wire_planet_hooks(self) -> None:
        for planet_id, ps in self.planet_states.items():
            # Armour pickup
            def make_armour_hook(pid: int):
                def on_armour_acquired(name: str, piece: ArmourPiece) -> None:
                    self.armour.add_location_piece(name, piece)
                    loc = ARMOUR_FLAG_TO_LOCATION.get((name, piece))
                    if loc:
                        logger.info(f"[RAC] Armour piece acquired on planet {pid:#04x}: {loc}")
                        self._send_location(loc)
                    else:
                        logger.warning(f"[RAC] Unknown armour pickup on planet {pid:#04x}: {name} {piece.name}")
                return on_armour_acquired
            ps.on_armour_acquired = make_armour_hook(planet_id)

            # Vendor purchases
            def make_weapon_hook(pid: int):
                def on_weapon_purchased(name: str) -> None:
                    loc = WEAPON_INTERNAL_TO_LOCATION.get(name)
                    if loc:
                        logger.info(f"[RAC] Vendor weapon purchased on planet {pid:#04x}: {loc}")
                        self._send_location(loc)
                return on_weapon_purchased
            ps.on_vendor_weapon_purchased = make_weapon_hook(planet_id)

            def make_gadget_hook(pid: int):
                def on_gadget_purchased(name: str) -> None:
                    loc = GADGET_INTERNAL_TO_LOCATION.get(name)
                    if loc:
                        logger.info(f"[RAC] Vendor gadget purchased on planet {pid:#04x}: {loc}")
                        self._send_location(loc)
                return on_gadget_purchased
            ps.on_vendor_gadget_purchased = make_gadget_hook(planet_id)

            def make_mod_hook(pid: int):
                def on_mod_purchased(weapon: str, slot: str) -> None:
                    loc = MOD_INTERNAL_TO_LOCATION.get((weapon, slot))
                    if loc:
                        logger.info(f"[RAC] Vendor mod purchased on planet {pid:#04x}: {loc}")
                        self._send_location(loc)
                return on_mod_purchased
            ps.on_vendor_mod_purchased = make_mod_hook(planet_id)

    # ── internal: planet state construction ───────────────────────────────────

    def _build_planet_states(self, pine: Pine) -> dict[int, PlanetState]:
        states: dict[int, PlanetState] = {}
        for planet_id, (movement_addr, health_addr) in PLAYER_ADDRS.items():
            name = _PLANET_NAMES.get(planet_id, f"Planet {planet_id:#04x}")
            ps = PlanetState(
                pine=pine,
                name=name,
                planet_id=planet_id,
                current_planet_addr=CURRENT_PLANET_ADDRESS,
                menu_addr=MENU_ADDR_BY_PLANET_ID.get(planet_id),
            )
            ps.set_poll_interval(_POLL_MS)
            ps.add_enter_callback(self._maybe_write_defaults)
            ps.add_enter_callback(lambda pid=planet_id: self._on_initial_planet_load(pid))
            ps.set_armour(self.armour)
            ps.set_player_state(self.player, movement_addr, health_addr)

            if planet_id in WEAPON_ARRAY_BASE_BY_PLANET:
                ps.set_weapon_state(self.weapons, WEAPON_ARRAY_BASE_BY_PLANET[planet_id])

            menu_addr = MENU_ADDR_BY_PLANET_ID.get(planet_id)
            if menu_addr:
                preload_addr = PRELOAD_MENU_ADDR_BY_PLANET_ID.get(planet_id, 0)
                ps.set_menu_state(self.menu, preload_addr, self.vendor)

            text_box = _TEXT_BOX_BY_PLANET.get(planet_id)
            if text_box:
                ps.set_display_text_box(self.display_text, text_box)

            ps.set_inventory_callbacks(
                reapply_inv           = self._reapply_inv,
                get_checked_locations = lambda: self._checked_locations,
            )
            states[planet_id] = ps
        return states

    def _current_planet_id(self) -> int:
        return self._active_planet_id
