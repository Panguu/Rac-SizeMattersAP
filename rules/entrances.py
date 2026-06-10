from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_projectile_weapon, infobot

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_entrance_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    mw.get_entrance("To Kalidon",       player).access_rule = infobot("Kalidon", player)
    mw.get_entrance("To Metalis",       player).access_rule = infobot("Metalis", player)
    mw.get_entrance("To Dreamtime",     player).access_rule = \
        lambda state: (state.has("Outpost Omega Infobot", player)
                       and state.has("Hypershot", player)
                       and state.has("Sprout-O-Matic", player))
    mw.get_entrance("To Outpost Omega", player).access_rule = infobot("Outpost Omega", player)
    mw.get_entrance("To Challax",       player).access_rule = \
        lambda state: (state.has("Challax Infobot", player)
                       and state.has("Shrink Ray", player)
                       and state.has("Polarizer", player))
    mw.get_entrance("To Dayni Moon",    player).access_rule = infobot("Dayni Moon", player)
    mw.get_entrance("To Inside Clank",  player).access_rule = \
        lambda state: (state.has("Dayni Moon Infobot", player)
                       and state.has("Sprout-O-Matic", player)
                       and state.has("Shrink Ray", player)
                       and has_projectile_weapon(state, player)
                       and state.has("Hypershot", player)
                       and state.has("Polarizer", player))
    mw.get_entrance("To Quodrona",      player).access_rule = infobot("Quodrona", player)
