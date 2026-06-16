from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants.cutscenes import RacSMCutsceneLocations
from ..constants.skillpoints import RACSMSKILLPOINT
from ..constants.skyboard_challenges import RACSMTCLANK as RACSMSKY
from ..constants.tbolts import RACSMTBOLT
from ..constants.vendors import RACSMVENDORLOCATION

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
        mw.get_location(RACSMSKILLPOINT.OUTPOST_OMEGA_AWESOME, player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    if world.options.all_cutscenes:
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA,        player).access_rule = _facility
    if world.options.all_missions:
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA_ESCAPE,  player).access_rule = _facility
        mw.get_location(RacSMCutsceneLocations.OUTPOST_OMEGA_REMATCH, player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.OUTPOST_OMEGA_DREAM, player).access_rule = lambda _: True

    # ── Skyboard Challenges (skyboard_challenges >= 1) ────────────────────────
    if world.options.skyboard_challenges.value >= 1:
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VERTIGO,  player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_INTERIOR, player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_DANGER,   player).access_rule = lambda _: True
        mw.get_location(RACSMSKY.OUTPOST_OMEGA_VORTEX,   player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.OUTPOST_OMEGA_BEE, player).access_rule = \
        lambda state: state.has("Shrink Ray", player)
