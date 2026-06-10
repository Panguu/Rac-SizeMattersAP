from __future__ import annotations

from typing import TYPE_CHECKING

from ._helpers import infobot

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_quodrona_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _checks = lambda state: (state.has("Shrink Ray", player)
                             and state.has("Hypershot", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Elite Annihilation (SP)", player).access_rule = _checks
        mw.get_location("Storm The Front (SP)",    player).access_rule = _checks

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Clone Wars",        player).access_rule = _checks
    mw.get_location("Runnnn from Otto",  player).access_rule = _checks
    mw.get_location("Defeat mecha Otto", player).access_rule = _checks
    mw.get_location("Find Otto Destruct", player).access_rule = _checks

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Quodrona Ratchet Clones and Dummies (TB)", player).access_rule = _checks

    # ── Boss ──────────────────────────────────────────────────────────────────
    mw.get_location("Defeat Otto Destruct", player).access_rule = _checks

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Laser Tracer", player).access_rule = lambda _: True

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    mw.get_location("Purchase Agents of Doom Launcher Mod",  player).access_rule = \
        lambda state: state.can_reach("Purchase Agents of Doom", "Location", player)
    mw.get_location("Purchase Scorcher Spitfire Mod",        player).access_rule = \
        lambda state: state.can_reach("Purchase Scorcher", "Location", player)
    mw.get_location("Purchase Sniper Mine Split Beam Mod",   player).access_rule = \
        lambda state: state.can_reach("Purchase Sniper Mine", "Location", player)
    mw.get_location("Purchase Shock Rocket Lock On Mod",     player).access_rule = \
        lambda state: state.can_reach("Purchase Shock Rocket", "Location", player)
    mw.get_location("Purchase Shock Rocket After Shock Mod", player).access_rule = \
        lambda state: state.can_reach("Purchase Shock Rocket", "Location", player)
