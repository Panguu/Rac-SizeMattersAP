from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_metalis_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("Shutout (SP)",             player).access_rule = lambda _: True
        mw.get_location("Terror of the Skies (SP)", player).access_rule = lambda _: True
        mw.get_location("Ultimate Gladiator (SP)",  player).access_rule = lambda _: True

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Survive Robot War III", player).access_rule = lambda _: True
    mw.get_location("Escape the planet",     player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Metalis Behind the Polarized Door (TB)", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Hypershot", player)

    # ── Clank Challenges — item rewards (clank_challenges >= 1) ───────────────
    if world.options.clank_challenges.value >= 1:
        mw.get_location("Metalis Buzzsaw Blitz - Polarizer (CC)",               player).access_rule = lambda _: True
        mw.get_location("Metalis Smasherbot's Revenge - Crystallix Helmet (CC)", player).access_rule = lambda _: True
        mw.get_location("Metalis The Uber Finals - Crystallix Gloves (CC)",     player).access_rule = lambda _: True
        mw.get_location("Metalis Nigh Impossible - Sludge Mk9 Gloves (CC)",     player).access_rule = lambda _: True

    # ── Clank Challenges — individual completions (clank_challenges >= 2) ─────
    if world.options.clank_challenges.value >= 2:
        mw.get_location("Metalis Take Two For The Team (CC)",              player).access_rule = lambda _: True
        mw.get_location("Metalis CHARGE! (CC)",                            player).access_rule = lambda _: True
        mw.get_location("Metalis Electric Boogaloo (CC)",                  player).access_rule = lambda _: True
        mw.get_location("Metalis Showdown (CC)",                           player).access_rule = lambda _: True
        mw.get_location("Metalis Little League (CC)",                      player).access_rule = lambda _: True
        mw.get_location("Metalis Varsity Bracket (CC)",                    player).access_rule = lambda _: True
        mw.get_location("Metalis Collegiate Division (CC)",                player).access_rule = lambda _: True
        mw.get_location("Metalis Professional Level (CC)",                 player).access_rule = lambda _: True
        mw.get_location("Metalis Bridge The Gap (CC)",                     player).access_rule = lambda _: True
        mw.get_location("Metalis Of Trapeze and Teleporters (CC)",         player).access_rule = lambda _: True
        mw.get_location("Metalis Brain Trip (CC)",                         player).access_rule = lambda _: True

    # ── No vendor on Metalis ──────────────────────────────────────────────────
