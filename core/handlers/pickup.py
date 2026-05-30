from __future__ import annotations

from CommonClient import logger

from ..memory import (
    ARMOUR_ADDRESSES,
    GADGETS,
    WEAPONS,
    ItemScanner,
    MemoryState,
    apply_slots_from_armour,
    apply_tracked_armour,
    apply_tracked_weapons,
)
from ..state import GameState

# Slots have no item identity so they only need clearing, not scanning
_slot_state = MemoryState(lambda: ARMOUR_ADDRESSES.values())


def _build_scanners(gs: GameState) -> list[ItemScanner]:
    def on_armour(name: str, val: int) -> None:
        gs.picked_up_items[name] = val
        logger.info(f"  Collected armour: {name} ({val:#04x})")

    def on_weapon(name: str, _: int) -> None:
        logger.info(f"  Collected weapon: {name}")

    def on_gadget(name: str, _: int) -> None:
        logger.info(f"  Collected gadget: {name}")

    return [
        ItemScanner(lambda: ARMOUR_ADDRESSES, on_armour),
        ItemScanner(lambda: {n: w.unlocked for n, w in WEAPONS.items()}, on_weapon),
        ItemScanner(lambda: {n: g.unlocked for n, g in GADGETS.items()}, on_gadget),
    ]


def _on_pickup_start(gs: GameState, scanners: list[ItemScanner], *_) -> None:
    gs.is_picking_up = True
    logger.info("Item pickup started: clearing inventory for detection…")
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
    logger.info("Pickup complete. State reapplied.")
