from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_projectile_weapon, has_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_pokitaru_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Train Faster (SP)",       player).access_rule = \
            lambda state: has_projectile_weapon(state, player)
        mw.get_location("Dont Rock The Boat (SP)", player).access_rule = lambda _: True
        mw.get_location("Do Cows Get Crabby (SP)", player).access_rule = \
            lambda state: has_weapon(state, player, "Mootator")

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Fight some robots", player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Pokitaru Above Zipline (TB)", player).access_rule = lambda _: True
    mw.get_location("Pokitaru Behind Hut (TB)",    player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    # Weapons and gadgets freely accessible on arrival.
    mw.get_location("Purchase Lacerator",       player).access_rule = lambda _: True
    mw.get_location("Purchase Acid Bomb Glove", player).access_rule = lambda _: True
    mw.get_location("Purchase Concussion Gun",  player).access_rule = lambda _: True
    mw.get_location("Purchase Hypershot",       player).access_rule = lambda _: True
