from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_outpost_omega_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _facility = lambda state: (state.has("Shrink Ray", player)
                               and state.has("Hypershot", player)
                               and state.has("Sprout-O-Matic", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Be An Awesome Skyboarder (SC)", player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Escape from facility pt 1",   player).access_rule = _facility
    mw.get_location("Escape the medical facility", player).access_rule = _facility
    mw.get_location("Rematch - Skyboard racers",   player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Outpost Omega Near the Entrance to DreamTime (TB)", player).access_rule = \
        lambda _: True

    # ── Skyboard Challenges (skyboard_challenges >= 1) ────────────────────────
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location("Outpost Omega Vertigo - Electroshock Boots (SC)", player).access_rule = lambda _: True
        mw.get_location("Outpost Omega Interior Decorating (SC)",          player).access_rule = lambda _: True
        mw.get_location("Outpost Omega Danger, High Voltage (SC)",         player).access_rule = lambda _: True
        mw.get_location("Outpost Omega The Vortex (SC)",                   player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Bee Mine Glove", player).access_rule = \
        lambda state: state.has("Shrink Ray", player)
