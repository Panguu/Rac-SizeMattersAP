from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_ryllus_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _full = lambda state: (state.has("Hypershot", player)
                           and state.has("Sprout-O-Matic", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Bury The Pygmies (SP)",     player).access_rule = _full
        mw.get_location("Lights Camera Action (SP)", player).access_rule = lambda _: True
        mw.get_location("Ship It (SP)",              player).access_rule = _full

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Buzzing Cameras",          player).access_rule = lambda _: True
    mw.get_location("Investigate the artifact", player).access_rule = _full
    mw.get_location("Unlock the temple",        player).access_rule = _full

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Ryllus Down The Cliff (TB)", player).access_rule = lambda _: True
    mw.get_location("Ryllus After the Wall (TB)", player).access_rule = _full
    mw.get_location("Ryllus Wildfire Helmet",     player).access_rule = _full
    mw.get_location("Ryllus Sludge Mk9 Boots",    player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location("Purchase Agents of Doom", player).access_rule = lambda _: True
