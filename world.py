from __future__ import annotations

from typing import Any, ClassVar

from BaseClasses import Item, ItemClassification, Location, Tutorial

from worlds.AutoWorld import WebWorld, World

from .items import (
    ALL_ITEMS,
    ARMOUR_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_ITEM_TABLE,
    ARMOUR_SETS,
    GADGET_ITEM_TABLE,
    INFOBOT_ITEM_TABLE,
    WEAPON_ITEM_TABLE,
    WEAPON_PROGRESSIVE_ITEM_TABLE,
    WEAPON_PROGRESSIVE_STEPS,
)
from .locations import ALL_LOCATIONS
from .options import RACSizeMatterOptions
from .regions import create_regions
from .rules import set_rules
from .universal_tracker import setup_options_from_slot_data, tracker_world


class RACItem(Item):
    game: str = "Ratchet & Clank: Size Matters"


class RACLocation(Location):
    game: str = "Ratchet & Clank: Size Matters"


class RACWeb(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Ratchet & Clank: Size Matters for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Archipelago Community"],
        )
    ]


class RACSizeMatterWorld(World):
    """Ratchet & Clank: Size Matters is a 2007 PSP/PS2 action platformer following
    Ratchet and Clank as they unravel the mystery of the Technomites across ten planets.
    Weapons, gadgets, and armour pieces are shuffled across all locations.
    Defeat Otto Destruct on Quodrona to complete your goal."""

    game = "Ratchet & Clank: Size Matters"
    web = RACWeb()
    options_dataclass = RACSizeMatterOptions
    options: RACSizeMatterOptions

    item_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_ITEMS.items()}
    location_name_to_id: dict[str, int] = {name: data.code for name, data in ALL_LOCATIONS.items()}

    using_ut: bool = False
    passthrough: dict[str, Any]
    ut_can_gen_without_yaml: bool = True
    disable_ut: bool = False
    tracker_world: ClassVar = tracker_world

    def create_item(self, name: str) -> RACItem:
        data = ALL_ITEMS[name]
        classification = data.classification
        # Armour pieces gate armour set check locations, so they must be tracked
        # as progression items for AP's reachability sweep to work correctly.
        if (classification == ItemClassification.useful
                and self.options.armour_set_checks
                and (name in ARMOUR_ITEM_TABLE or name in ARMOUR_PROGRESSIVE_ITEM_TABLE)):
            classification = ItemClassification.progression_skip_balancing
        return RACItem(name, classification, data.code, self.player)

    def create_event(self, name: str) -> RACItem:
        return RACItem(name, ItemClassification.progression, None, self.player)

    def generate_early(self) -> None:
        setup_options_from_slot_data(self)

    def create_regions(self) -> None:
        create_regions(self)

    def set_rules(self) -> None:
        set_rules(self)

    def create_items(self) -> None:
        pool: list[str] = []
        if self.options.progressive_weapons:
            for display, steps in WEAPON_PROGRESSIVE_STEPS.items():
                pool += [f"{display} Progressive Weapon"] * steps
        else:
            pool += list(WEAPON_ITEM_TABLE)

        pool += list(GADGET_ITEM_TABLE)
        pool += list(INFOBOT_ITEM_TABLE)

        if self.options.progressive_armour:
            for display, _ in ARMOUR_SETS:
                pool += [f"{display} Progressive Pickup"] * 4
        else:
            pool += list(ARMOUR_ITEM_TABLE)

        # Fill any remaining slots (e.g. when skill_points_as_checks adds locations)
        unfilled = len(self.multiworld.get_unfilled_locations(self.player))
        filler_needed = max(0, unfilled - len(pool))
        pool += ["Bolts"] * filler_needed

        for name in pool:
            self.multiworld.itempool.append(self.create_item(name))

    def _precollect(self, name: str) -> None:
        """Precollect an item and replace its copy in the pool with Bolts filler."""
        self.multiworld.push_precollected(self.create_item(name))
        for item in self.multiworld.itempool:
            if item.player == self.player and item.name == name:
                self.multiworld.itempool.remove(item)
                self.multiworld.itempool.append(self.create_item("Bolts"))
                break

    def generate_basic(self) -> None:
        # The player always starts on Pokitaru — there is currently no way to
        # change the starting planet, so the Pokitaru Infobot is always granted.
        self._precollect("Pokitaru Infobot")

        if self.options.starting_bolts.value > 0:
            self.multiworld.push_precollected(self.create_item("Bolts"))

        weapon_count = self.options.starting_weapons.value
        if weapon_count > 0:
            if self.options.progressive_weapons:
                pool = list(WEAPON_PROGRESSIVE_ITEM_TABLE.keys())
            else:
                pool = list(WEAPON_ITEM_TABLE.keys())
            for name in self.random.sample(pool, min(weapon_count, len(pool))):
                self._precollect(name)

        gadget_count = self.options.starting_gadgets.value
        if gadget_count > 0:
            pool = list(GADGET_ITEM_TABLE.keys())
            for name in self.random.sample(pool, min(gadget_count, len(pool))):
                self._precollect(name)

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "death_link": bool(self.options.death_link.value),
            "clank_challenges": self.options.clank_challenges.value,
            "vendor_mods_randomized": bool(self.options.vendor_mods_randomized.value),
            "skill_points_as_checks": self.options.skill_points_as_checks.value,
            "armour_set_checks": bool(self.options.armour_set_checks.value),
            "starting_bolts": self.options.starting_bolts.value,
            "death_amnesty": self.options.death_amnesty.value,
            "progressive_weapons": self.options.progressive_weapons.value,
            "progressive_armour": self.options.progressive_armour.value,
            "starting_weapons": self.options.starting_weapons.value,
            "starting_gadgets": self.options.starting_gadgets.value,
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

    def get_filler_item_name(self) -> str:
        return "Bolts"
