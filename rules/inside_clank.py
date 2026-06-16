from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants.cutscenes import RacSMCutsceneLocations
from ..constants.skillpoints import RACSMSKILLPOINT
from ..constants.tbolts import RACSMTBOLT
from ..constants.vendors import RACSMVENDORLOCATION

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location(RACSMSKILLPOINT.INSIDE_CLANK_SHOCK,   player).access_rule = lambda _: True
        mw.get_location(RACSMSKILLPOINT.INSIDE_CLANK_RATCHET, player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.INSIDE_CLANK_ESCAPE,      player).access_rule = lambda _: True
        mw.get_location(RacSMCutsceneLocations.INSIDE_CLANK_TECHNOMITES, player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.INSIDE_CLANK_LADDER, player).access_rule = lambda _: True
    mw.get_location(RACSMTBOLT.INSIDE_CLANK_WALL,   player).access_rule = lambda _: True

    # ── Armour ────────────────────────────────────────────────────────────────
    # Mega Bomb Chestplate pickup is commented out in core/armour.py ("cutscene
    # address not yet found") — no such location exists, so no rule is set here.
    # mw.get_location(RACSMITEM.MEGA_BOMB_CHESTPLATE, player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    # Static Barrier vendor — freely accessible on arrival.
    mw.get_location(RACSMVENDORLOCATION.INSIDE_CLANK_STATIC, player).access_rule = lambda _: True
