from __future__ import annotations

from CommonClient import logger

from ..data import arm_cutscenes
from ..memory import ARMOUR_ADDRESSES, PLAYER_ARMOUR_SLOTS, MemoryState
from ..state import GameState

# Saves and restores full armour state (sets + slots) across death/respawn
armour_state = MemoryState(lambda: [*ARMOUR_ADDRESSES.values(), *PLAYER_ARMOUR_SLOTS.values()])


def _on_death(gs: GameState, _: int, new: int) -> None:
    gs.is_dead = True
    logger.info(f"Player died (state={new:#x}).")
    arm_cutscenes(gs.ipc, gs.current_planet, "reset")
    armour_state.save(gs.ipc)
    logger.info("  Armour state saved.")


def _on_respawn(gs: GameState, *_) -> None:
    gs.is_dead = False
    armour_state.restore(gs.ipc)
    logger.info("Respawned. Armour state restored.")
