from __future__ import annotations

from ..constants.items import RACSMITEM
from ..items import PROGRESSIVE_ARMOUR_NAME, PROGRESSIVE_WEAPON_NAME

_PROJECTILE_WEAPONS = (
    RACSMITEM.LACERATOR, RACSMITEM.CONCUSSION_GUN, RACSMITEM.SHOCK_ROCKET,
    RACSMITEM.SNIPER_MINE, RACSMITEM.LASER_TRACER, RACSMITEM.SCORCHER, RACSMITEM.RYNO,
)


def has_projectile_weapon(state, player: int) -> bool:
    return any(
        state.has(name, player) or state.has(PROGRESSIVE_WEAPON_NAME[name], player)
        for name in _PROJECTILE_WEAPONS
    )


def has_armour_piece(state, player: int, set_display: str, piece_name: str, piece_idx: int) -> bool:
    return (state.has(f"{set_display} {piece_name}", player) or
            state.count(PROGRESSIVE_ARMOUR_NAME[set_display], player) >= piece_idx)


def infobot(item_name: str, player: int):
    return lambda state: state.has(item_name, player)


def has_weapon(state, player: int, weapon: str) -> bool:
    return state.has(weapon, player) or state.has(PROGRESSIVE_WEAPON_NAME[weapon], player)
