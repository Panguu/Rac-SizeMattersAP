from __future__ import annotations

from typing import TYPE_CHECKING

from .locations import VENDOR_WEAPON_PLANET, VENDOR_GADGET_PLANET, VENDOR_WEAPON_MOD_PLANET

if TYPE_CHECKING:
    from .world import RACSizeMatterWorld

# (set_display, piece_name, progressive_count_needed)
# progressive_count_needed: 1=chestplate, 2=helmet, 3=gloves, 4=boots
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
    "Lacerator",
    "Concussion Gun",
    "Shock Rocket",
    "Sniper Mine",
    "Laser Tracer",
    "Scorcher",
    "RYNO",
)


def _has_projectile_weapon(state, player: int) -> bool:
    return any(
        state.has(name, player) or state.has(f"{name} Progressive Weapon", player)
        for name in _PROJECTILE_WEAPONS
    )


def set_rules(world: RACSizeMatterWorld) -> None:
    player = world.player
    multiworld = world.multiworld

    # ── Goal condition ────────────────────────────────────────────────────────
    multiworld.completion_condition[player] = lambda state: state.has("Victory", player)

    # ── Skill point rules ─────────────────────────────────────────────────────
    if world.options.skill_points_as_checks:
        multiworld.get_location("Skill Point Train Faster", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player)
        multiworld.get_location("Skill Point Dont Rock The Boat", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player)
        multiworld.get_location("Skill Point Do Cows Get Crabby", player).access_rule = \
            lambda state: _has_projectile_weapon(state, player) and (
                state.has("Mootator", player) or state.has("Mootator Progressive Weapon", player)
            )

    _ryllus_full = lambda state: state.has("Hypershot", player) and state.has("Sprout-O-Matic", player)
    _kalidon = lambda state: state.has("Shrink Ray", player)

    # ── Titanium bolt rules ───────────────────────────────────────────────────
    multiworld.get_location("Pokitaru Titanium Bolt Behind Hut", player).access_rule = \
        lambda state: _has_projectile_weapon(state, player)
    multiworld.get_location("Metalis Titanium Bolt Behind the Polarized Door", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Hypershot", player)
    multiworld.get_location("Ryllus Titanium Bolt After the Wall", player).access_rule = _ryllus_full
    # NOTE: can be reached without Hypershot via a skip, but Hypershot is the intended requirement
    multiworld.get_location("Kalidon Titanium Bolt Behind The Ship", player).access_rule = \
        lambda state: state.has("Hypershot", player)
    multiworld.get_location("Challax Titanium Bolt Hidden Room", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Shrink Ray", player)
    multiworld.get_location("Challax Titanium Bolt Mimic Plant Lob", player).access_rule = \
        lambda state: state.has("Polarizer", player) and state.has("Shrink Ray", player) and state.has("Sprout-O-Matic", player)
    for _loc in (
        "Kalidon Titanium Bolt Side of Mechanoid Factory",
        "Kalidon Titanium Bolt Grav-Ramps",
        "Kalidon Sludge Mk9 Gloves",
        "Kalidon Sludge Mk9 Chestplate",
        "Kalidon Wildfire Boots",
    ):
        multiworld.get_location(_loc, player).access_rule = _kalidon
    if world.options.skill_points_as_checks:
        for _loc in (
            "Skill Point Explosive Ordnance Disposal",
            "Skill Point Super Lombax",
            "Skill Point Be A Cool Skyboarder",
        ):
            multiworld.get_location(_loc, player).access_rule = _kalidon

    multiworld.get_location("Dayni Moon Titanium Bolt Planting at the Barnyard", player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)

    # ── Armour pickup rules ───────────────────────────────────────────────────
    multiworld.get_location("Ryllus Sludge Mk9 Boots", player).access_rule = \
        lambda state: state.has("Sprout-O-Matic", player)
    multiworld.get_location("Ryllus Wildfire Helmet", player).access_rule = _ryllus_full

    # ── Planet access lambdas (chained progression) ──────────────────────────
    def _ryllus_ok(state):
        return _has_projectile_weapon(state, player)

    def _kalidon_ok(state):
        return (_ryllus_ok(state)
                and state.has("Hypershot", player)
                and state.has("Sprout-O-Matic", player))

    def _metalis_ok(state):  # TODO: add specific Metalis entry requirements
        return _kalidon_ok(state) and state.has("Shrink Ray", player)

    def _dreamtime_ok(state):  # TODO: add specific Dreamtime entry requirements
        return _metalis_ok(state)

    def _outpost_omega_ok(state):  # TODO: add specific Outpost Omega entry requirements
        return _dreamtime_ok(state)

    def _challax_ok(state):
        return _outpost_omega_ok(state) and state.has("Polarizer", player)

    def _dayni_moon_ok(state):  # TODO: add specific Dayni Moon entry requirements
        return _challax_ok(state)

    def _inside_clank_ok(state):  # TODO: add specific Inside Clank entry requirements
        return _dayni_moon_ok(state)

    def _quodrona_ok(state):  # TODO: add specific Quodrona entry requirements
        return _inside_clank_ok(state)

    # ── Region access rules ───────────────────────────────────────────────────
    multiworld.get_entrance("To Ryllus",        player).access_rule = _ryllus_ok
    multiworld.get_entrance("To Kalidon",       player).access_rule = _kalidon_ok
    multiworld.get_entrance("To Metalis",       player).access_rule = _metalis_ok
    multiworld.get_entrance("To Dreamtime",     player).access_rule = _dreamtime_ok
    multiworld.get_entrance("To Outpost Omega", player).access_rule = _outpost_omega_ok
    multiworld.get_entrance("To Challax",       player).access_rule = _challax_ok
    multiworld.get_entrance("To Dayni Moon",    player).access_rule = _dayni_moon_ok
    multiworld.get_entrance("To Inside Clank",  player).access_rule = _inside_clank_ok
    multiworld.get_entrance("To Quodrona",      player).access_rule = _quodrona_ok

    # ── Vendor purchase rules ─────────────────────────────────────────────────
    # Planet access already gates these via the region entrance rules above.
    # Kalidon vendor additionally requires Hypershot since the planet does.
    _planet_rule = {
        "Pokitaru":      lambda state: True,
        "Ryllus":        _ryllus_ok,
        "Kalidon":       _kalidon_ok,
        "Dreamtime":     _dreamtime_ok,
        "Outpost Omega": _outpost_omega_ok,
        "Challax":       _challax_ok,
        "Dayni Moon":    _dayni_moon_ok,
        "Inside Clank":  _inside_clank_ok,
        "Quodrona":      _quodrona_ok,
    }
    for name, planet in {**VENDOR_WEAPON_PLANET, **VENDOR_GADGET_PLANET}.items():
        multiworld.get_location(f"Purchase {name}", player).access_rule = _planet_rule[planet]

    for (weapon, mod), planet in VENDOR_WEAPON_MOD_PLANET.items():
        multiworld.get_location(f"Purchase {weapon} {mod}", player).access_rule = _planet_rule[planet]

    # ── Armour set check rules ────────────────────────────────────────────────
    if world.options.armour_set_checks:
        def _pieces_rule(reqs):
            return lambda state: all(
                _has_armour_piece(state, player, sd, pn, pi)
                for sd, pn, pi in reqs
            )
        for loc_name, reqs in _ARMOUR_SET_RULES.items():
            multiworld.get_location(loc_name, player).access_rule = _pieces_rule(reqs)
