from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_projectile_weapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_kalidon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _inside = lambda state: (state.has("Hypershot", player)
                             and state.has("Shrink Ray", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Explosive Ordnance Disposal (SP)", player).access_rule = _inside
        mw.get_location("Super Lombax (SP)",                player).access_rule = _inside
        mw.get_location("Be A Cool Skyboarder (SP)",        player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Explore the planet",    player).access_rule = _inside
    mw.get_location("Win the skyboard race", player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Kalidon Behind The Ship (TB)",           player).access_rule = lambda _: True
    mw.get_location("Kalidon Side of Mechanoid Factory (TB)", player).access_rule = \
        lambda state: state.has("Hypershot", player)
    mw.get_location("Kalidon Grav-Ramps (TB)",                player).access_rule = _inside

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location("Kalidon Sludge Mk9 Chestplate", player).access_rule = _inside
    mw.get_location("Kalidon Wildfire Boots",         player).access_rule = _inside

    # ── Skyboard Challenges (skyboard_challenges >= 1) ────────────────────────
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location("Kalidon Learner's Permit (SC)",  player).access_rule = lambda _: True
        mw.get_location("Kalidon Master's Challenge (SC)", player).access_rule = lambda _: True
        mw.get_location("Kalidon Speeding Ticket (SC)",   player).access_rule = lambda _: True
        mw.get_location("Kalidon Tricky Air (SC)",        player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Scorcher", player).access_rule = lambda _: True

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    mw.get_location("Purchase Lacerator Lock On Mod",           player).access_rule = \
        lambda state: state.can_reach("Purchase Lacerator", "Location", player)
    mw.get_location("Purchase Concussion Gun Split Barrel Mod", player).access_rule = \
        lambda state: state.can_reach("Purchase Concussion Gun", "Location", player)
