from __future__ import annotations

from typing import TYPE_CHECKING

from .locations import (
    VENDOR_GADGET_PLANET,
    VENDOR_WEAPON_MOD_PLANET,
    VENDOR_WEAPON_PLANET,
)

if TYPE_CHECKING:
    from .world import RACSizeMatterWorld

# ── Armour-set check helpers ──────────────────────────────────────────────────

_ARMOUR_SET_RULES: dict[str, list[tuple[str, str, int]]] = {
    "Equip Wildfire Armour Set": [
        ("Wildfire", "Chestplate", 1), ("Wildfire", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Wildfire", "Boots", 4),
    ],
    "Equip Wildburst Armour Set": [
        ("Wildfire", "Chestplate", 1), ("Sludge Mk9", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Wildfire", "Boots", 4),
    ],
    "Equip Sludge Mk9 Armour Set": [
        ("Sludge Mk9", "Chestplate", 1), ("Sludge Mk9", "Helmet", 2),
        ("Sludge Mk9", "Gloves", 3), ("Sludge Mk9", "Boots", 4),
    ],
    "Equip Crystallix Armour Set": [
        ("Crystallix", "Chestplate", 1), ("Crystallix", "Helmet", 2),
        ("Crystallix", "Gloves", 3), ("Crystallix", "Boots", 4),
    ],
    "Equip Triple Wave Armour Set": [
        ("Wildfire", "Helmet", 2), ("Electroshock", "Chestplate", 1),
        ("Sludge Mk9", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Shock Crystal Armour Set": [
        ("Electroshock", "Helmet", 2), ("Crystallix", "Chestplate", 1),
        ("Crystallix", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Electroshock Armour Set": [
        ("Electroshock", "Chestplate", 1), ("Electroshock", "Helmet", 2),
        ("Electroshock", "Gloves", 3), ("Electroshock", "Boots", 4),
    ],
    "Equip Mega Bomb Armour Set": [
        ("Mega Bomb", "Chestplate", 1), ("Mega Bomb", "Helmet", 2),
        ("Mega Bomb", "Gloves", 3), ("Mega Bomb", "Boots", 4),
    ],
    "Equip Fire-Bomb Armour Set": [
        ("Mega Bomb", "Chestplate", 1), ("Mega Bomb", "Helmet", 2),
        ("Wildfire", "Gloves", 3), ("Mega Bomb", "Boots", 4),
    ],
    "Equip Hyperborean Armour Set": [
        ("Hyperborean", "Chestplate", 1), ("Hyperborean", "Helmet", 2),
        ("Hyperborean", "Gloves", 3), ("Hyperborean", "Boots", 4),
    ],
    "Equip Ice II Armour Set": [
        ("Hyperborean", "Chestplate", 1), ("Crystallix", "Helmet", 2),
        ("Hyperborean", "Gloves", 3), ("Hyperborean", "Boots", 4),
    ],
    "Equip Chameleon Armour Set": [
        ("Chameleon", "Chestplate", 1), ("Chameleon", "Helmet", 2),
        ("Chameleon", "Gloves", 3), ("Chameleon", "Boots", 4),
    ],
    "Equip Stalker Armour Set": [
        ("Wildfire", "Helmet", 2), ("Chameleon", "Chestplate", 1),
        ("Sludge Mk9", "Gloves", 3), ("Chameleon", "Boots", 4),
    ],
}


def _has_armour_piece(state, player: int, set_display: str, piece_name: str, piece_idx: int) -> bool:
    return (state.has(f"{set_display} {piece_name}", player) or
            state.count(f"{set_display} Progressive Pickup", player) >= piece_idx)


_PROJECTILE_WEAPONS = (
    "Lacerator", "Concussion Gun", "Shock Rocket", "Sniper Mine",
    "Laser Tracer", "Scorcher", "RYNO",
)


def _has_projectile_weapon(state, player: int) -> bool:
    return any(
        state.has(name, player) or state.has(f"{name} Progressive Weapon", player)
        for name in _PROJECTILE_WEAPONS
    )


def _has_weapon(state, player: int, name: str) -> bool:
    return state.has(name, player) or state.has(f"{name} Progressive Weapon", player)


# ── Main rules function ───────────────────────────────────────────────────────

def set_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    multiworld = world.multiworld

    multiworld.completion_condition[player] = lambda state: state.has("Victory", player)

    # Shorthand helpers
    def _has(item: str):
        return lambda state: state.has(item, player)

    def _infobot(planet: str):
        return lambda state: state.has(f"{planet} Infobot", player)

    # ── Entrance rules ────────────────────────────────────────────────────────
    # All planets connect directly from Menu (the in-game planet select screen).
    # Metalis and Outpost Omega are auto-unlocked from the start.
    # Inside Clank and Challax require Shrink Ray (obtained on Kalidon).
    # Dreamtime is auto-unlocked; no extra item requirement.

    multiworld.get_entrance("To Kalidon",       player).access_rule = \
        lambda state: (state.has("Kalidon Infobot", player)
                       and _has_projectile_weapon(state, player)
                       and state.has("Hypershot", player)
                       and state.has("Sprout-O-Matic", player))
    multiworld.get_entrance("To Metalis",       player).access_rule = _infobot("Metalis")
    multiworld.get_entrance("To Dreamtime",     player).access_rule = \
        lambda state: (state.has("Shrink Ray", player)
                       and state.has("Hypershot", player)
                       and state.has("Sprout-O-Matic", player))
    multiworld.get_entrance("To Outpost Omega", player).access_rule = _infobot("Outpost Omega")
    multiworld.get_entrance("To Challax",       player).access_rule = \
        lambda state: (state.has("Challax Infobot", player)
                       and state.has("Shrink Ray", player)
                       and state.has("Polarizer", player))
    multiworld.get_entrance("To Dayni Moon",    player).access_rule = _infobot("Dayni Moon")
    multiworld.get_entrance("To Inside Clank",  player).access_rule = \
        lambda state: (state.has("Dayni Moon Infobot", player)
                       and state.has("Sprout-O-Matic", player)
                       and state.has("Shrink Ray", player)
                       and _has_projectile_weapon(state, player))
    multiworld.get_entrance("To Quodrona",      player).access_rule = \
        lambda state: (state.has("Shrink Ray", player)
                       and state.has("Hypershot", player)
                       and state.has("Polarizer", player))

    # ── Pokitaru ──────────────────────────────────────────────────────────────
    # All checks are freely accessible.
    if world.options.skill_points_as_checks:
        multiworld.get_location("Train Faster (SP)", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player)
        multiworld.get_location("Dont Rock The Boat (SP)", player).access_rule = \
            lambda _: True
        multiworld.get_location("Do Cows Get Crabby (SP)", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player) and _has_weapon(state, player, "Mootator")

    # ── Ryllus ────────────────────────────────────────────────────────────────
    _ryllus_full = lambda state: (state.has("Hypershot", player)
                                  and state.has("Sprout-O-Matic", player))

    multiworld.get_location("Ryllus After the Wall (TB)", player).access_rule = _ryllus_full
    multiworld.get_location("Ryllus Sludge Mk9 Boots",            player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)
    multiworld.get_location("Ryllus Wildfire Helmet",              player).access_rule = _ryllus_full

    if world.options.skill_points_as_checks:
        multiworld.get_location("Bury The Pygmies (SP)", player).access_rule = _ryllus_full
        multiworld.get_location("Ship It (SP)",          player).access_rule = _ryllus_full
        multiworld.get_location("Lights Camera Action (SP)", player).access_rule = \
            lambda _: True

    # ── Kalidon ───────────────────────────────────────────────────────────────
    # Planet entrance requires projectile + Hypershot + Sprout-O-Matic.
    # Some locations additionally require the Shrink Ray item.
    _kalidon_shrink = lambda state: state.has("Shrink Ray", player)
    _kalidon_hard   = lambda state: (state.has("Shrink Ray", player)
                                     and state.has("Hypershot", player))

    multiworld.get_location("Kalidon Behind The Ship (TB)",            player).access_rule = \
        lambda state: state.has("Hypershot", player)
    multiworld.get_location("Kalidon Side of Mechanoid Factory (TB)",  player).access_rule = \
        _kalidon_shrink
    multiworld.get_location("Kalidon Grav-Ramps (TB)",                 player).access_rule = \
        _kalidon_hard
    # All Kalidon armour requires Shrink Ray + Hypershot
    for _loc in (
        "Kalidon Sludge Mk9 Chestplate",
        "Kalidon Wildfire Boots",
    ):
        multiworld.get_location(_loc, player).access_rule = _kalidon_hard

    if world.options.skill_points_as_checks:
        multiworld.get_location("Explosive Ordnance Disposal (SP)",  player).access_rule = \
            _kalidon_hard
        multiworld.get_location("Super Lombax (SP)",                 player).access_rule = \
            lambda state: (state.has("Shrink Ray", player)
                           and state.has("Hypershot", player)
                           and _has_weapon(state, player, "Static Barrier"))
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Be A Cool Skyboarder (SP)",         player).access_rule = \
            _kalidon_shrink

    if world.options.skyboard_challenges.value >= 1:
        for _loc in (
            "Kalidon Learner's Permit (SC)",
            "Kalidon Speeding Ticket (SC)",
            "Kalidon Tricky Air (SC)",
            "Kalidon Master's Challenge (SC)",
        ):
            multiworld.get_location(_loc, player).access_rule = _kalidon_shrink

    # ── Metalis ───────────────────────────────────────────────────────────────
    # Auto-unlocked, all checks freely accessible once on the planet.
    multiworld.get_location("Metalis Behind the Polarized Door (TB)", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Hypershot", player)

    # ── Dreamtime ─────────────────────────────────────────────────────────────
    # Requires Shrink Ray + Hypershot + Sprout-O-Matic (entrance rule above).
    _dreamtime = lambda state: (state.has("Shrink Ray", player)
                                and state.has("Hypershot", player)
                                and state.has("Sprout-O-Matic", player))

    for _loc in (
        "Dreamtime Jump Across three moving parasols (TB)",
        "Dreamtime To the left of Ratchets Garage (TB)",
        "Dreamtime Crystallix Chestplate",
    ):
        multiworld.get_location(_loc, player).access_rule = _dreamtime

    multiworld.get_location(
        "Dreamtime Apparition of the Scuttle Crab (TB)", player
    ).access_rule = lambda state: (_dreamtime(state) and _has_projectile_weapon(state, player))

    if world.options.skill_points_as_checks:
        multiworld.get_location("Friends Dont Hurt Friends (SP)", player).access_rule = _dreamtime
        multiworld.get_location("Night Terrors (SP)",             player).access_rule = _dreamtime

    # ── Outpost Omega ─────────────────────────────────────────────────────────
    # Accessible from the menu but requires Shrink Ray to progress.
    _outpost_omega = lambda state: state.has("Shrink Ray", player)

    for _loc in (
        "Outpost Omega Near the Entrance to DreamTime (TB)",
        "Outpost Omega Crystallix Boots",
        "Purchase Bee Mine Glove",
    ):
        multiworld.get_location(_loc, player).access_rule = _outpost_omega

    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Be An Awesome Skyboarder (SC)", player).access_rule = _outpost_omega

    if world.options.skyboard_challenges.value >= 1:
        multiworld.get_location("Outpost Omega Electroshock Boots (CC)", player).access_rule = _outpost_omega
    if world.options.skyboard_challenges.value >= 2:
        for _loc in (
            "Outpost Omega Interior Decorating (SC)",
            "Outpost Omega Danger, High Voltage (SC)",
            "Outpost Omega The Vortex (SC)",
        ):
            multiworld.get_location(_loc, player).access_rule = _outpost_omega

    # ── Challax ───────────────────────────────────────────────────────────────
    # Entrance requires Shrink Ray + Polarizer (rule above).
    # Some checks additionally require Sprout-O-Matic.
    _challax_base   = lambda state: (state.has("Shrink Ray", player)
                                     and state.has("Polarizer", player))
    _challax_sprout = lambda state: (state.has("Shrink Ray", player)
                                     and state.has("Polarizer", player)
                                     and state.has("Sprout-O-Matic", player))

    # Titanium Bolt Beside The Ultra Mech Pad: just the planet entrance (no extra rule)
    multiworld.get_location("Challax Hidden Room (TB)",    player).access_rule = _challax_base
    multiworld.get_location("Challax Mimic Plant Lob (TB)", player).access_rule = _challax_sprout

    multiworld.get_location("Challax Electroshock Chestplate", player).access_rule = _challax_base
    multiworld.get_location("Challax Electroshock Helmet",    player).access_rule = \
        lambda state: (_challax_base(state)
                       or state.has("Dayni Moon Infobot", player))

    if world.options.skill_points_as_checks:
        multiworld.get_location("High Tech Weapons Master (SP)", player).access_rule = _challax_base
        # Skill Point Take Them Down A Shock is EXCLUDED — there is only one
        # opportunity to complete it in the entire game, making it unreliable
        # for randomisation.  The address (bit 24) is preserved in the data.
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("No More Varmints (SP)",         player).access_rule = _challax_base

    # ── Dayni Moon ────────────────────────────────────────────────────────────
    # Entrance requires Dayni Moon Infobot (rule above).
    _dayni_base = lambda state: (state.has("Sprout-O-Matic", player)
                                  and _has_projectile_weapon(state, player))

    multiworld.get_location("Dayni Moon Planting at the Barnyard (TB)", player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)
    multiworld.get_location("Dayni Moon Bounce on the Blue mimic (TB)", player).access_rule = \
        lambda state: (_dayni_base(state) and state.has("Shrink Ray", player))

    for _loc in ("Dayni Moon Mega Bomb Boots (CC)", "Dayni Moon Mega Bomb Gloves (CC)"):
        multiworld.get_location(_loc, player).access_rule = _dayni_base

    # Mega Bomb Helmet is acquired together with the Dayni Moon Infobot.
    multiworld.get_location("Dayni Moon Mega Bomb Helmet", player).access_rule = \
        _infobot("Dayni Moon")

    if world.options.skill_points_as_checks:
        multiworld.get_location("Wool Protest (SP)",              player).access_rule = _dayni_base
        multiworld.get_location("Bouncy Bouncy Bouncy (SP)",      player).access_rule = \
            lambda state: state.has("Sprout-O-Matic", player)
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Ultimate Gladiator Dayni Moon (SP)", player).access_rule = \
            _infobot("Dayni Moon")

    # ── Inside Clank ──────────────────────────────────────────────────────────
    # Entrance requires Shrink Ray (rule above).
    # Some locations additionally require Polarizer.
    _inside_clank_full = lambda state: (state.has("Shrink Ray", player)
                                        and state.has("Polarizer", player))

    # multiworld.get_location("Inside Clank Mega Bomb Chestplate", player).access_rule = (
    #     _inside_clank_full  # cutscene address not yet found
    # )

    if world.options.skill_points_as_checks:
        multiworld.get_location("Not The Shock of Me Now (SP)", player).access_rule = \
            _inside_clank_full
        multiworld.get_location("Ratchet Just Ratchet (SP)",    player).access_rule = \
            _inside_clank_full

    # ── Quodrona ──────────────────────────────────────────────────────────────
    # Entrance requires Shrink Ray + Hypershot + Polarizer (rule above).
    # Skill points additionally need RYNO.
    _quodrona_sp = lambda state: (state.has("Shrink Ray", player)
                                   and state.has("Hypershot", player)
                                   and state.has("Polarizer", player)
                                   and _has_weapon(state, player, "RYNO"))

    if world.options.skill_points_as_checks:
        multiworld.get_location("Elite Annihilation (SP)", player).access_rule = _quodrona_sp
        multiworld.get_location("Storm The Front (SP)",    player).access_rule = _quodrona_sp

    # ── Vendor access rules ───────────────────────────────────────────────────
    # Planet-level vendor access mirrors the planet entrance rules.
    _planet_rule: dict[str, object] = {
        "Pokitaru":      lambda _: True,
        "Ryllus":        lambda state: _has_projectile_weapon(state, player),
        "Kalidon":       lambda state: (state.has("Kalidon Infobot", player)
                                        and _has_projectile_weapon(state, player)
                                        and state.has("Hypershot", player)
                                        and state.has("Sprout-O-Matic", player)),
        "Metalis":       lambda state: (state.has("Metalis Infobot", player)
                                        and state.has("Shrink Ray", player)),
        "Dreamtime":     _dreamtime,
        "Outpost Omega": lambda state: (state.has("Outpost Omega Infobot", player)
                                        and state.has("Shrink Ray", player)),
        "Challax":       lambda state: (state.has("Challax Infobot", player)
                                        and state.has("Shrink Ray", player)
                                        and state.has("Polarizer", player)),
        "Dayni Moon":    lambda state: (state.has("Dayni Moon Infobot", player)
                                        and state.has("Sprout-O-Matic", player)
                                        and _has_projectile_weapon(state, player)),
        "Inside Clank":  lambda _: True,
        "Quodrona":      lambda state: (state.has("Quodrona Infobot", player)
                                        and state.has("Shrink Ray", player)
                                        and state.has("Hypershot", player)
                                        and state.has("Polarizer", player)),
    }
    for name, planet in {**VENDOR_WEAPON_PLANET, **VENDOR_GADGET_PLANET}.items():
        multiworld.get_location(f"Purchase {name}", player).access_rule = _planet_rule[planet]

    # Sniper Mine and PDA are accessible on Challax with just the infobot + Shrink Ray,
    # without needing Polarizer — override the general Challax planet rule.
    _challax_no_polarizer = lambda state: (state.has("Challax Infobot", player)
                                           and state.has("Shrink Ray", player))
    multiworld.get_location("Purchase Sniper Mine", player).access_rule = _challax_no_polarizer
    multiworld.get_location("Purchase PDA",         player).access_rule = _challax_no_polarizer

    if world.options.vendor_mods_randomized:
        for (weapon, mod), planet in VENDOR_WEAPON_MOD_PLANET.items():
            if mod is None:
                continue  # inaccessible slot sentinel — no AP location
            _weapon_planet  = VENDOR_WEAPON_PLANET.get(weapon)
            _mod_rule       = _planet_rule[planet]
            _weapon_rule    = _planet_rule[_weapon_planet] if _weapon_planet else lambda _: True
            multiworld.get_location(f"Purchase {weapon} {mod}", player).access_rule = (
                lambda state, pr=_mod_rule, wr=_weapon_rule: pr(state) and wr(state)
            )

    # ── Armour-set checks ─────────────────────────────────────────────────────
    if world.options.armour_set_checks:
        def _pieces_rule(reqs):
            return lambda state: all(
                _has_armour_piece(state, player, sd, pn, pi)
                for sd, pn, pi in reqs
            )
        for loc_name, reqs in _ARMOUR_SET_RULES.items():
            multiworld.get_location(loc_name, player).access_rule = _pieces_rule(reqs)
