from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_projectile_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dreamtime_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # Entrance already requires Hypershot + Sprout-O-Matic.
    _base = lambda state: (state.has("Hypershot", player)
                           and state.has("Sprout-O-Matic", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Friends Dont Hurt Friends (SP)", player).access_rule = _base
        mw.get_location("Night Terrors (SP)",              player).access_rule = _base

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("??????????", player).access_rule = _base

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Dreamtime Atop the floating hat (TB)",            player).access_rule = _base
    mw.get_location("Dreamtime To the left of Ratchets Garage (TB)",   player).access_rule = _base
    mw.get_location("Dreamtime Apparition of the Scuttle Crab (TB)",   player).access_rule = \
        lambda state: (_base(state) and has_projectile_weapon(state, player))

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location("Dreamtime Crystallix Chestplate", player).access_rule = _base

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Suck Cannon", player).access_rule = _base
