from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_challax_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    mw = world.multiworld

    _base   = lambda state: (state.has("Shrink Ray", player)
                             and state.has("Polarizer", player))
    _sprout = lambda state: (state.has("Shrink Ray", player)
                             and state.has("Polarizer", player)
                             and state.has("Sprout-O-Matic", player))

    # ── Skill Points ──────────────────────────────────────────────────────────
    if world.options.skill_points:
        mw.get_location("High Tech Weapons Master (SP)", player).access_rule = _sprout
        mw.get_location("No More Varmints (SP)",         player).access_rule = _sprout

    # ── Missions ──────────────────────────────────────────────────────────────
    mw.get_location("Start giant clank",        player).access_rule = lambda _: True
    mw.get_location("Destroy the space fortress", player).access_rule = lambda _: True

    # ── Titanium Bolts ────────────────────────────────────────────────────────
    mw.get_location("Challax Beside The Ultra Mech Pad (TB)", player).access_rule = lambda _: True
    mw.get_location("Challax Hidden Room (TB)",               player).access_rule = _base
    mw.get_location("Challax Mimic Plant Lob (TB)",           player).access_rule = _sprout

    # ── Armour ────────────────────────────────────────────────────────────────
    mw.get_location("Challax Electroshock Helmet", player).access_rule = \
        lambda state: (_base(state) or state.has("Dayni Moon Infobot", player))

    # ── Vendors ───────────────────────────────────────────────────────────────
    _shrink_ray = lambda state: (state.has("Shrink Ray", player))
    mw.get_location("Purchase Sniper Mine", player).access_rule = _shrink_ray
    mw.get_location("Purchase PDA",         player).access_rule = _shrink_ray

    # ── Weapon Mod Vendor ─────────────────────────────────────────────────────
    mw.get_location("Purchase Lacerator Double Barrel Mod",    player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Lacerator", "Location", player)
    mw.get_location("Purchase Acid Bomb Glove Acid Burn Mod",  player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Acid Bomb Glove", "Location", player)
    mw.get_location("Purchase Acid Bomb Glove Epoxy Mod",      player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Acid Bomb Glove", "Location", player)
    mw.get_location("Purchase Concussion Gun Lock On Mod",     player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Concussion Gun", "Location", player)
    mw.get_location("Purchase Concussion Gun Charge Up Mod",   player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Concussion Gun", "Location", player)
    mw.get_location("Purchase Bee Mine Glove Worker Mod",      player).access_rule = \
        lambda state: _base(state) and state.can_reach("Purchase Bee Mine Glove", "Location", player)
