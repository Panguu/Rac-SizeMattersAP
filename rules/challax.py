from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants.general import RACSMLOCATION
from ..constants.items import RACSMITEM
from ..constants.skillpoints import RACSMSKILLPOINT
from ..constants.tbolts import RACSMTBOLT
from ..constants.vendors import RACSMVENDORLOCATION

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_challax_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base   = lambda state: (state.has(RACSMITEM.SHRINK_RAY, player)
                             and state.has(RACSMITEM.POLARIZER, player))
    _sprout = lambda state: (state.has(RACSMITEM.SHRINK_RAY, player)
                             and state.has(RACSMITEM.POLARIZER, player)
                             and state.has(RACSMITEM.SPROUT_O_MATIC, player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points.value >= 1:
        mw.get_location(RACSMSKILLPOINT.CHALLAX_VARMINTS, player).access_rule = _sprout
    if world.options.skill_points.value >= 2:
        mw.get_location(RACSMSKILLPOINT.CHALLAX_MASTER,   player).access_rule = _sprout

    # ── Missions ──────────────────────────────────────────────────────────────
    # Giant Clank disabled/unreachable — METALIS_CLANK and CHALLAX_CLANK are
    # commented out of the location pool in locations.py, so no rule is set here.

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location(RACSMTBOLT.CHALLAX_MECH_PAD, player).access_rule = lambda _: True
    mw.get_location(RACSMTBOLT.CHALLAX_ROOM,      player).access_rule = _base
    mw.get_location(RACSMTBOLT.CHALLAX_PLANT,     player).access_rule = _sprout

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location(RACSMLOCATION.CHALLAX_HELMET, player).access_rule = \
        lambda state: (_base(state) or state.has(RACSMITEM.DAYNI_MOON, player))

    # ── Vendors ───────────────────────────────────────────────────────────────
    _shrink_ray = lambda state: (state.has(RACSMITEM.SHRINK_RAY, player))
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_SNIPER, player).access_rule = _shrink_ray
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_PDA,    player).access_rule = _shrink_ray

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_LACERATOR_DOUBLE,  player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.POKITARU_LACERATOR, "Location", player)
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_ACID_BURN,         player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.POKITARU_ACID, "Location", player)
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_ACID_EPOXY,        player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.POKITARU_ACID, "Location", player)
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_CONCUSSION_LOCK,   player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.POKITARU_CONCUSSION, "Location", player)
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_CONCUSSION_CHARGE, player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.POKITARU_CONCUSSION, "Location", player)
    mw.get_location(RACSMVENDORLOCATION.CHALLAX_BEE_WORKER,        player).access_rule = \
        lambda state: _base(state) and state.can_reach(RACSMVENDORLOCATION.OUTPOST_OMEGA_BEE, "Location", player)
