from __future__ import annotations

import asyncio
from functools import partial

from .data.addresses import (
    CURRENT_PLANET_ADDRESS,
    PLAYER_ADDRS, PLAYER_STATE,
)
from .data.cutscenes import Cutscene, CUTSCENES, arm_cutscenes
from .data.planets import BY_ID
from .data.skill_points import SKILL_POINT_ADDRESS, LOCATION_SKILL_POINTS
from .data.titanium_bolts import BOLT_BY_PLANET_AND_DELTA
from .memory import (
    WEAPONS, GADGETS, ARMOUR_ADDRESSES, PLAYER_ARMOUR_SLOTS, BOLTS,
    MemoryState, ItemScanner,
    sync_weapons,
    apply_tracked_armour, apply_slots_from_armour,
    apply_tracked_weapons, restore_tracked_weapon_state,
)
from .state import GameState, PollAddress
from .vendor import VendorPoller

# death/respawn: save and restore full armour state (sets + slots)
armour_state = MemoryState(lambda: [*ARMOUR_ADDRESSES.values(), *PLAYER_ARMOUR_SLOTS.values()])
# pickup: slots have no item identity so they only need clearing, not scanning
_slot_state  = MemoryState(lambda: PLAYER_ARMOUR_SLOTS.values())


def _build_scanners(gs: GameState) -> list[ItemScanner]:
    def on_armour(name: str, val: int) -> None:
        gs.picked_up_items[name] = val
        print(f"  Collected armour: {name} ({val:#04x})")

    def on_weapon(name: str, _: int) -> None:
        print(f"  Collected weapon: {name}")

    def on_gadget(name: str, _: int) -> None:
        print(f"  Collected gadget: {name}")

    return [
        ItemScanner(lambda: ARMOUR_ADDRESSES, on_armour),
        ItemScanner(lambda: {n: w.unlocked for n, w in WEAPONS.items()}, on_weapon),
        ItemScanner(lambda: {n: g.unlocked for n, g in GADGETS.items()}, on_gadget),
    ]

_dead = lambda v: 0x29 <= v <= 0x2F


def _on_planet_change(gs: GameState, _: int, new: int) -> None:
    gs.current_planet = new
    gs.state_addr     = PLAYER_ADDRS.get(new, (PLAYER_STATE,))[0]
    planet_obj        = BY_ID.get(new)
    name              = planet_obj.name if planet_obj else f"unknown id={new:#04x}"
    print(f"Planet changed → {name}")
    sync_weapons(gs.ipc)
    arm_cutscenes(gs.ipc, new, "armed")


def _on_bolt_pickup(gs: GameState, old: int, new: int) -> None:
    bolt_delta = new - old
    name = BOLT_BY_PLANET_AND_DELTA.get((gs.current_planet, bolt_delta), f"Unknown (delta={bolt_delta})")
    print(f"Titanium Bolt picked up: {name}  |  total={new}")
    if gs.on_reward:
        gs.on_reward()


def _on_skill_point(gs: GameState, old: int, new: int) -> None:
    new_bits = new & ~old
    for name, mask in LOCATION_SKILL_POINTS.items():
        if new_bits & mask:
            print(f"Skill Point unlocked: {name}")
    if gs.on_reward:
        gs.on_reward()


def _on_death(gs: GameState, _: int, new: int) -> None:
    gs.is_dead = True
    print(f"Player died (state={new:#x}).")
    arm_cutscenes(gs.ipc, gs.current_planet, "reset")
    armour_state.save(gs.ipc)
    print("  Armour state saved.")


def _on_respawn(gs: GameState, *_) -> None:
    gs.is_dead = False
    armour_state.restore(gs.ipc)
    print("Respawned. Armour state restored.")


def _on_pickup_start(gs: GameState, scanners: list[ItemScanner], *_) -> None:
    gs.is_picking_up = True
    print("Item pickup started: clearing inventory for detection…")
    _slot_state.remove(gs.ipc)
    for scanner in scanners:
        scanner.clear(gs.ipc)


def _on_pickup_end(gs: GameState, scanners: list[ItemScanner], *_) -> None:
    gs.is_picking_up = False
    for scanner in scanners:
        scanner.scan(gs.ipc)
    _slot_state.remove(gs.ipc)
    for scanner in scanners:
        scanner.clear(gs.ipc)
    if gs.on_reward:
        gs.on_reward()
    apply_tracked_armour(gs)
    apply_slots_from_armour(gs)
    apply_tracked_weapons(gs)
    print("Pickup complete. State reapplied.")


def _on_cutscene(gs: GameState, cutscene: Cutscene, old: int, new: int) -> None:
    if gs.current_planet != cutscene.planet_id:
        return
    if cutscene.kind == "pickup":
        print(f"Cutscene: {cutscene.name} — drawing bag reward…")
        if gs.on_reward:
            gs.on_reward()
    elif cutscene.kind == "goal":
        gs.goal_reached = True
        print(f"\n{'='*50}")
        print(f"  CONGRATULATIONS! Randomizer complete!")
        print(f"  {cutscene.name} — you beat the game!")
        print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# Lock enforcement
# ---------------------------------------------------------------------------

def _enforce_locks(gs: GameState) -> None:
    if gs.is_dead or gs.is_picking_up:
        return
    ipc = gs.ipc

    if not gs.is_in_menu:
        for name, addr in ARMOUR_ADDRESSES.items():
            expected = gs.tracked_armour.get(name, 0)
            if expected and ipc.read_int8(addr) != expected:
                ipc.write_int8(addr, expected)

    if (gs.is_preloaded or gs.is_in_menu) and gs.tracked_vendor is not None:
        gs.vendor_session.enforce(ipc)
    elif not gs.is_in_menu:
        for name, w in WEAPONS.items():
            expected = 1 if name in gs.tracked_weapons else 0
            if ipc.read_int8(w.unlocked) != expected:
                ipc.write_int8(w.unlocked, expected)
        for name, g in GADGETS.items():
            expected = 1 if name in gs.tracked_gadgets else 0
            if ipc.read_int8(g.unlocked) != expected:
                ipc.write_int8(g.unlocked, expected)


# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------

def build_pollers(gs: GameState) -> list:
    _state_read = lambda ipc, addr: ipc.read_int16(addr)
    _int32_read = lambda ipc, addr: ipc.read_int32(addr)
    _scanners   = _build_scanners(gs)

    return [
        PollAddress(CURRENT_PLANET_ADDRESS, partial(_on_planet_change, gs)),
        PollAddress(
            BOLTS.pickup,
            partial(_on_bolt_pickup, gs),
            trigger=lambda o, n: n > o,
            read_fn=lambda ipc, addr: ipc.read_int64(addr),
        ),
        PollAddress(
            SKILL_POINT_ADDRESS,
            partial(_on_skill_point, gs),
            trigger=lambda o, n: bool(n & ~o),
            read_fn=lambda ipc, addr: ipc.read_int64(addr),
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_death, gs),
            trigger=lambda o, n: not _dead(o) and _dead(n),
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_respawn, gs),
            trigger=lambda o, n: _dead(o) and n == 0x00,
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_pickup_start, gs, _scanners),
            trigger=lambda o, n: o != 0x43 and n == 0x43,
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_pickup_end, gs, _scanners),
            trigger=lambda o, n: o == 0x43 and n == 0x00,
            read_fn=_state_read,
        ),
        VendorPoller(gs),
        *[
            PollAddress(
                c.address,
                partial(_on_cutscene, gs, c),
                trigger=lambda o, n: o != 0 and n == 0,
                read_fn=_int32_read,
            )
            for c in CUTSCENES
        ],
    ]


async def poll_loop(gs: GameState) -> None:
    pollers = build_pollers(gs)
    while not gs.goal_reached:
        await asyncio.sleep(0.5)
        try:
            for p in pollers:
                p.tick(gs.ipc)
            _enforce_locks(gs)
        except Exception as e:
            print(f"Poll error: {type(e).__name__}: {e}")
    print("Polling stopped.")
