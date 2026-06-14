from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Not The Shock of Me Now (SP)", player).access_rule = lambda _: True
        mw.get_location("Ratchet Just Ratchet (SP)",    player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Defeat all technomites", player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Inside Clank Walk behind the ladder (TB)",   player).access_rule = lambda _: True
    mw.get_location("Inside Clank Wall jumping Technomite (TB)",  player).access_rule = lambda _: True

    # ── Vendors ───────────────────────────────────────────────────────────────
    # Static Barrier vendor — freely accessible on arrival.
    mw.get_location("Purchase Static Barrier", player).access_rule = lambda _: True
