from __future__ import annotations

_PROJECTILE_WEAPONS = (
    "Lacerator", "Concussion Gun", "Shock Rocket", "Sniper Mine",
    "Laser Tracer", "Scorcher", "RYNO",
)


def has_projectile_weapon(state, player: int) -> bool:
    return any(
        state.has(name, player) or state.has(f"{name} Progressive Weapon", player)
        for name in _PROJECTILE_WEAPONS
    )


def has_armour_piece(state, player: int, set_display: str, piece_name: str, piece_idx: int) -> bool:
    return (state.has(f"{set_display} {piece_name}", player) or
            state.count(f"{set_display} Progressive Pickup", player) >= piece_idx)


def infobot(item_name: str, player: int):
    return lambda state: state.has(item_name, player)


def has_weapon(state, player: int, weapon: str) -> bool:
    return state.has(weapon, player) or state.has(f"{weapon} Progressive Weapon", player)
