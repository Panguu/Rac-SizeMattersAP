from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import has_projectile_weapon, infobot

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_dayni_moon_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base      = lambda state: (state.has("Sprout-O-Matic", player)
                                and has_projectile_weapon(state, player))
    _shrink_ray = lambda state: (_base(state) and state.has("Shrink Ray", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Ultimate Gladiator Dayni Moon (SP)", player).access_rule = lambda _: True
        mw.get_location("Wool Protest (SP)",                  player).access_rule = _base
        mw.get_location("Bouncy Bouncy Bouncy (SP)",          player).access_rule = _base

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Catch Luna",        player).access_rule = _shrink_ray
    mw.get_location("Luna fight pt 1",   player).access_rule = _shrink_ray
    mw.get_location("Luna fight pt 2",   player).access_rule = _shrink_ray
    mw.get_location("'Disable' Luna",    player).access_rule = _shrink_ray
    mw.get_location("Escape from clank", player).access_rule = _shrink_ray

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Dayni Moon Planting at the Barnyard (TB)", player).access_rule = _base
    mw.get_location("Dayni Moon Bounce on the Blue mimic (TB)", player).access_rule = _shrink_ray

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location("Dayni Moon Mega Bomb Helmet", player).access_rule = _base

    # ── Clank Challenges — item rewards (clank_challenges >= 1) ───────────────
    if world.options.clank_challenges.value >= 1:
        mw.get_location("Dayni Moon The Ultimate Showdown - Mega Bomb Gloves (CC)", player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Infinite Improbability - Mega Bomb Boots (CC)", player).access_rule = lambda _: True

    # ── Clank Challenges — individual completions (clank_challenges >= 2) ─────
    if world.options.clank_challenges.value >= 2:
        mw.get_location("Dayni Moon Two's A Crowd (CC)",        player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Reverse Into Victory (CC)", player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Emergency Bridge (CC)",     player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Leap Of Faith (CC)",        player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Welcome to Dayni (CC)",     player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Round Up! (CC)",            player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Variety Is Shocking (CC)",  player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Tom Sawyer (CC)",           player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Smasherbot Returns! (CC)",  player).access_rule = lambda _: True
        mw.get_location("Dayni Moon Tri-bomb Tournament (CC)",  player).access_rule = lambda _: True
        mw.get_location("Dayni Moon A-rooouund the Bend (CC)",  player).access_rule = lambda _: True
        mw.get_location("Dayni Moon The Thin Bouncy Line (CC)", player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Shock Rocket", player).access_rule = lambda _: True
    mw.get_location("Purchase Map-O-Matic",  player).access_rule = lambda _: True
