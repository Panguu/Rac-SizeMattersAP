from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

from .locations import (
    ARMOUR_PICKUP_LOCATIONS,
    ARMOUR_SET_CHECK_LOCATIONS,
    BOSS_LOCATIONS,
    GADGET_PICKUP_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    SKILL_POINT_LOCATIONS,
    TITANIUM_BOLT_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
)

if TYPE_CHECKING:
    from .world import RACSizeMatterWorld

PLANET_NAMES: tuple[str, ...] = (
    "Pokitaru",
    "Ryllus",
    "Kalidon",
    "Metalis",
    "Dreamtime",
    "Outpost Omega",
    "Challax",
    "Dayni Moon",
    "Inside Clank",
    "Quodrona",
)


def create_regions(world: RACSizeMatterWorld) -> None:
    from .world import RACLocation

    player = world.player
    multiworld = world.multiworld

    menu_region = Region("Menu", player, multiworld)
    planet_regions: dict[str, Region] = {
        name: Region(name, player, multiworld)
        for name in PLANET_NAMES
    }

    # ── Place locations ───────────────────────────────────────────────────────

    location_tables = [
        TITANIUM_BOLT_LOCATIONS,
        ARMOUR_PICKUP_LOCATIONS,
        BOSS_LOCATIONS,
        GADGET_PICKUP_LOCATIONS,
        WEAPON_VENDOR_LOCATIONS,
        GADGET_VENDOR_LOCATIONS,
        WEAPON_MOD_VENDOR_LOCATIONS,
    ]
    if world.options.skill_points_as_checks:
        location_tables.append(SKILL_POINT_LOCATIONS)
    if world.options.armour_set_checks:
        location_tables.append(ARMOUR_SET_CHECK_LOCATIONS)

    for table in location_tables:
        for loc_name, loc_data in table.items():
            region = planet_regions[loc_data.region]
            location = RACLocation(player, loc_name, loc_data.code, region)
            region.locations.append(location)

    # ── Victory event ─────────────────────────────────────────────────────────
    # Separate from the "Defeat Otto Destruct" check location.  The client sends
    # ClientStatus.CLIENT_GOAL when it detects the end-boss cutscene completing.
    quodrona = planet_regions["Quodrona"]
    victory_loc = RACLocation(player, "Quodrona Completed", None, quodrona)
    victory_loc.place_locked_item(world.create_event("Victory"))
    quodrona.locations.append(victory_loc)

    # ── Region connections ────────────────────────────────────────────────────
    # Pokitaru is always reachable from the menu (starting planet).
    # Subsequent planets connect linearly; entrance rules are set in rules.py.
    menu_region.connect(planet_regions["Pokitaru"], "To Pokitaru")
    for i in range(len(PLANET_NAMES) - 1):
        planet_regions[PLANET_NAMES[i]].connect(
            planet_regions[PLANET_NAMES[i + 1]],
            f"To {PLANET_NAMES[i + 1]}",
        )

    multiworld.regions += [menu_region, *planet_regions.values()]
