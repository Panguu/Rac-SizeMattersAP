from __future__ import annotations

from CommonClient import logger

from ...data import (
    BOLT_BY_PLANET_AND_DELTA,
    BY_ID,
    LOCATION_SKILL_POINTS,
    PLAYER_ADDRS,
    PLAYER_STATE,
    Cutscene,
    arm_cutscenes,
)
from ..game_state import GameState
from ..memory import sync_weapons


def _on_planet_change(gs: GameState, _: int, new: int) -> None:
    gs.current_planet = new
    gs.state_addr     = PLAYER_ADDRS.get(new, (PLAYER_STATE,))[0]
    planet_obj        = BY_ID.get(new)
    name              = planet_obj.name if planet_obj else f"unknown id={new:#04x}"
    logger.info(f"Planet changed → {name}")
    sync_weapons(gs.ipc)
    arm_cutscenes(gs.ipc, new, "armed")


def _on_bolt_pickup(gs: GameState, old: int, new: int) -> None:
    bolt_delta = new - old
    name = BOLT_BY_PLANET_AND_DELTA.get((gs.current_planet, bolt_delta), f"Unknown (delta={bolt_delta})")
    logger.info(f"Titanium Bolt picked up: {name}  |  total={new}")
    if gs.on_reward:
        gs.on_reward()


def _on_skill_point(gs: GameState, old: int, new: int) -> None:
    new_bits = new & ~old
    for name, mask in LOCATION_SKILL_POINTS.items():
        if new_bits & mask:
            logger.info(f"Skill Point unlocked: {name}")
    if gs.on_reward:
        gs.on_reward()


def _on_cutscene(gs: GameState, cutscene: Cutscene, old: int, new: int) -> None:
    if gs.current_planet != cutscene.planet_id:
        return
    if cutscene.kind == "pickup":
        logger.info(f"Cutscene: {cutscene.name} — drawing bag reward…")
        if gs.on_reward:
            gs.on_reward()
    elif cutscene.kind == "goal":
        gs.goal_reached = True
        logger.info(f"\n{'='*50}")
        logger.info("  CONGRATULATIONS! Randomizer complete!")
        logger.info(f"  {cutscene.name} — you beat the game!")
        logger.info(f"{'='*50}\n")
