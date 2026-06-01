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
    # Pokitaru and Ryllus are free (starting planets).
    # Metalis and Dreamtime are auto-unlocked by the game (no infobot item).
    # Inside Clank is accessible once Kalidon is accessible (Shrink Ray obtained naturally).

    multiworld.get_entrance("To Ryllus",        player).access_rule = lambda _: True
    multiworld.get_entrance("To Kalidon",       player).access_rule = _infobot("Kalidon")
    multiworld.get_entrance("To Metalis",       player).access_rule = lambda _: True
    multiworld.get_entrance("To Dreamtime",     player).access_rule = lambda _: True
    multiworld.get_entrance("To Outpost Omega", player).access_rule = _infobot("Outpost Omega")
    multiworld.get_entrance("To Challax",       player).access_rule = _infobot("Challax")
    multiworld.get_entrance("To Dayni Moon",    player).access_rule = _infobot("Dayni Moon")
    multiworld.get_entrance("To Inside Clank",  player).access_rule = \
        lambda state: state.has("Kalidon Infobot", player)
    multiworld.get_entrance("To Quodrona",      player).access_rule = \
        lambda state: (state.has("Quodrona Infobot", player)
                       and state.has("Kalidon Infobot", player)
                       and state.has("Hypershot", player))

    # ── Pokitaru ──────────────────────────────────────────────────────────────
    # All checks are freely accessible.
    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Train Faster", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player)
        multiworld.get_location("Skill Point Dont Rock The Boat", player).access_rule = \
            lambda _: True
        multiworld.get_location("Skill Point Do Cows Get Crabby", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player) and _has_weapon(state, player, "Mootator")

    # ── Ryllus ────────────────────────────────────────────────────────────────
    _ryllus_full = lambda state: (state.has("Hypershot", player)
                                  and state.has("Sprout-O-Matic", player))

    multiworld.get_location("Ryllus Titanium Bolt After the Wall", player).access_rule = _ryllus_full
    multiworld.get_location("Ryllus Sludge Mk9 Boots",            player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)
    multiworld.get_location("Ryllus Wildfire Helmet",              player).access_rule = _ryllus_full

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Bury The Pygmies", player).access_rule = _ryllus_full
        multiworld.get_location("Skill Point Ship It",          player).access_rule = _ryllus_full
        multiworld.get_location("Skill Point Lights Camera Action", player).access_rule = \
            lambda _: True

    # ── Kalidon ───────────────────────────────────────────────────────────────
    # Base requirement to be on Kalidon: Kalidon Infobot (entrance rule above).
    _kalidon_shrink = lambda state: state.has("Kalidon Infobot", player)
    _kalidon_hard   = lambda state: (state.has("Kalidon Infobot", player)
                                     and state.has("Hypershot", player))

    multiworld.get_location("Kalidon Titanium Bolt Behind The Ship",            player).access_rule = \
        lambda state: state.has("Hypershot", player)
    multiworld.get_location("Kalidon Titanium Bolt Side of Mechanoid Factory",  player).access_rule = \
        _kalidon_shrink
    multiworld.get_location("Kalidon Titanium Bolt Grav-Ramps",                 player).access_rule = \
        _kalidon_hard
    # All Kalidon armour requires Shrink Ray + Hypershot
    for _loc in (
        "Kalidon Sludge Mk9 Gloves",
        "Kalidon Sludge Mk9 Chestplate",
        "Kalidon Wildfire Boots",
    ):
        multiworld.get_location(_loc, player).access_rule = _kalidon_hard

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Explosive Ordnance Disposal",  player).access_rule = \
            _kalidon_hard
        multiworld.get_location("Skill Point Super Lombax",                 player).access_rule = \
            lambda state: (state.has("Kalidon Infobot", player)
                           and state.has("Hypershot", player)
                           and state.has("Static Barrier", player))
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Skill Point Be A Cool Skyboarder",         player).access_rule = \
            _kalidon_shrink

    # ── Metalis ───────────────────────────────────────────────────────────────
    # Auto-unlocked, all checks freely accessible once on the planet.
    multiworld.get_location("Metalis Titanium Bolt Behind the Polarized Door", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Hypershot", player)

    # ── Dreamtime ─────────────────────────────────────────────────────────────
    # Auto-unlocked via Outpost Omega.  All checks require Hypershot + Sprout-O-Matic.
    _dreamtime = lambda state: (state.has("Hypershot", player)
                                and state.has("Sprout-O-Matic", player))

    for _loc in (
        "Dreamtime Titanium Bolt Jump Across three moving parasols",
        "Dreamtime Titanium Bolt To the left of Ratchets Garage",
        "Dreamtime Crystallix Chestplate",
    ):
        multiworld.get_location(_loc, player).access_rule = _dreamtime

    multiworld.get_location(
        "Dreamtime Titanium Bolt Apparition of the Scuttle Crab", player
    ).access_rule = lambda state: (_dreamtime(state) and _has_projectile_weapon(state, player))

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Friends Dont Hurt Friends", player).access_rule = _dreamtime
        multiworld.get_location("Skill Point Night Terrors",             player).access_rule = _dreamtime

    # ── Outpost Omega ─────────────────────────────────────────────────────────
    # All checks just require the Outpost Omega Infobot (entrance rule).
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Be An Awesome Skyboarder", player).access_rule = lambda _: True

    # ── Challax ───────────────────────────────────────────────────────────────
    # Entrance requires Challax Infobot (rule above).
    # Most checks additionally require Shrink Ray + Polarizer.
    _challax_base  = lambda state: (state.has("Kalidon Infobot", player)
                                    and state.has("Polarizer", player))
    _challax_sprout = lambda state: (state.has("Kalidon Infobot", player)
                                     and state.has("Polarizer", player)
                                     and state.has("Sprout-O-Matic", player))

    # Titanium Bolt Beside The Ultra Mech Pad: just the planet entrance (no extra rule)
    multiworld.get_location("Challax Titanium Bolt Hidden Room",    player).access_rule = _challax_base
    multiworld.get_location("Challax Titanium Bolt Mimic Plant Lob", player).access_rule = _challax_sprout

    for _loc in (
        "Challax Electroshock Chestplate",
        "Challax Electroshock Helmet",
    ):
        multiworld.get_location(_loc, player).access_rule = _challax_base

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point High Tech Weapons Master", player).access_rule = _challax_base
        # Skill Point Take Them Down A Shock is EXCLUDED — there is only one
        # opportunity to complete it in the entire game, making it unreliable
        # for randomisation.  The address (bit 24) is preserved in the data.
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Skill Point No More Varmints",         player).access_rule = _challax_base

    # ── Dayni Moon ────────────────────────────────────────────────────────────
    # Entrance requires Dayni Moon Infobot (rule above).
    _dayni_base = lambda state: (state.has("Sprout-O-Matic", player)
                                  and _has_projectile_weapon(state, player))

    multiworld.get_location("Dayni Moon Titanium Bolt Planting at the Barnyard", player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)
    multiworld.get_location("Dayni Moon Titanium Bolt Bounce on the Blue mimic", player).access_rule = \
        _dayni_base

    for _loc in ("Dayni Moon Mega Bomb Boots", "Dayni Moon Mega Bomb Gloves"):
        multiworld.get_location(_loc, player).access_rule = _dayni_base

    # Mega Bomb Helmet is acquired together with the Dayni Moon Infobot.
    multiworld.get_location("Dayni Moon Mega Bomb Helmet", player).access_rule = \
        _infobot("Dayni Moon")

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Wool Protest",              player).access_rule = _dayni_base
        multiworld.get_location("Skill Point Bouncy Bouncy Bouncy",      player).access_rule = \
            lambda state: state.has("Sprout-O-Matic", player)
    if world.options.skill_points_as_checks.value >= 2:
        multiworld.get_location("Skill Point Ultimate Gladiator Dayni Moon", player).access_rule = \
            _infobot("Dayni Moon")

    # ── Inside Clank ──────────────────────────────────────────────────────────
    # Inside Clank entrance requires Kalidon Infobot (Shrink Ray obtained naturally).
    # Full access also needs Polarizer.
    _inside_clank_full = lambda state: (state.has("Kalidon Infobot", player)
                                        and state.has("Polarizer", player))

    multiworld.get_location("Inside Clank Mega Bomb Chestplate", player).access_rule = _inside_clank_full

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Not The Shock of Me Now", player).access_rule = \
            _inside_clank_full
        multiworld.get_location("Skill Point Ratchet Just Ratchet",    player).access_rule = \
            _inside_clank_full

    # ── Quodrona ──────────────────────────────────────────────────────────────
    # Entrance requires Quodrona Infobot + Shrink Ray + Hypershot (rule above).
    # Skill points additionally need RYNO.
    _quodrona_sp = lambda state: (state.has("Quodrona Infobot", player)
                                   and state.has("Kalidon Infobot", player)
                                   and state.has("Hypershot", player)
                                   and _has_weapon(state, player, "RYNO"))

    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Elite Annihilation", player).access_rule = _quodrona_sp
        multiworld.get_location("Skill Point Storm The Front",    player).access_rule = _quodrona_sp

    # ── Vendor access rules ───────────────────────────────────────────────────
    # Planet-level vendor access.  Challax vendor also needs Polarizer + Shrink Ray.
    _planet_rule: dict[str, object] = {
        "Pokitaru":      lambda _: True,
        "Ryllus":        lambda _: True,
        "Kalidon":       _infobot("Kalidon"),
        "Metalis":       lambda _: True,
        "Dreamtime":     _dreamtime,
        "Outpost Omega": _infobot("Outpost Omega"),
        # Challax and Dayni Moon vendor rules must include the infobot so that
        # mod-vendor locations on those planets require unlocking the planet first.
        "Challax":       lambda state: (state.has("Challax Infobot", player)
                                        and state.has("Kalidon Infobot", player)
                                        and state.has("Polarizer", player)),
        "Dayni Moon":    lambda state: (state.has("Dayni Moon Infobot", player)
                                        and state.has("Sprout-O-Matic", player)
                                        and _has_projectile_weapon(state, player)),
        "Inside Clank":  _inside_clank_full,
        "Quodrona":      lambda state: (state.has("Quodrona Infobot", player)
                                        and state.has("Kalidon Infobot", player)
                                        and state.has("Hypershot", player)),
    }
    for name, planet in {**VENDOR_WEAPON_PLANET, **VENDOR_GADGET_PLANET}.items():
        multiworld.get_location(f"Purchase {name}", player).access_rule = _planet_rule[planet]

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
