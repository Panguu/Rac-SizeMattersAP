"""Tests for the Ratchet & Clank: Size Matters Archipelago world."""
from .bases import RACSizeMatterTestBase
from ..locations import (
    ALL_LOCATIONS,
    TITANIUM_BOLT_LOCATIONS,
    ARMOUR_PICKUP_LOCATIONS,
    BOSS_LOCATIONS,
    SKILL_POINT_LOCATIONS,
    GADGET_PICKUP_LOCATIONS,
    WEAPON_VENDOR_LOCATIONS,
    GADGET_VENDOR_LOCATIONS,
    WEAPON_MOD_VENDOR_LOCATIONS,
)
from ..items import (
    ALL_ITEMS,
    WEAPON_ITEM_TABLE,
    WEAPON_PROGRESSIVE_ITEM_TABLE,
    GADGET_ITEM_TABLE,
    ARMOUR_ITEM_TABLE,
    ARMOUR_PROGRESSIVE_ITEM_TABLE,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

_ANY_PROJECTILE = "Lacerator"   # cheapest projectile weapon to collect in tests
_RYLLUS_ITEMS   = [_ANY_PROJECTILE, "Hypershot", "Sprout-O-Matic"]
_KALIDON_ITEMS  = _RYLLUS_ITEMS
_METALIS_ITEMS  = _KALIDON_ITEMS + ["Shrink Ray"]
_CHALLAX_ITEMS  = _METALIS_ITEMS + ["Polarizer"]
_ALL_PLANETS    = _CHALLAX_ITEMS  # everything needed to reach Quodrona


# ── IDs and registration ───────────────────────────────────────────────────────

class TestRegistration(RACSizeMatterTestBase):
    def test_no_duplicate_location_ids(self) -> None:
        ids = [data.code for data in ALL_LOCATIONS.values()]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate location IDs")

    def test_no_duplicate_item_ids(self) -> None:
        ids = [data.code for data in ALL_ITEMS.values()]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate item IDs")

    def test_all_location_tables_non_empty(self) -> None:
        for table, label in (
            (TITANIUM_BOLT_LOCATIONS,    "titanium bolts"),
            (ARMOUR_PICKUP_LOCATIONS,    "armour pickups"),
            (BOSS_LOCATIONS,             "boss"),
            (GADGET_PICKUP_LOCATIONS,    "gadget pickups"),
            (WEAPON_VENDOR_LOCATIONS,    "weapon vendors"),
            (GADGET_VENDOR_LOCATIONS,    "gadget vendors"),
            (WEAPON_MOD_VENDOR_LOCATIONS, "weapon mod vendors"),
        ):
            self.assertTrue(table, f"{label} table is empty")


# ── Default generation ─────────────────────────────────────────────────────────

class TestDefaultGeneration(RACSizeMatterTestBase):
    """Standard WorldTestBase suite with all defaults."""

    def test_boss_location_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Defeat Otto Destruct", names)

    def test_all_titanium_bolts_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in TITANIUM_BOLT_LOCATIONS:
            self.assertIn(name, names)

    def test_all_armour_pickups_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in ARMOUR_PICKUP_LOCATIONS:
            self.assertIn(name, names)

    def test_all_vendor_locations_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in WEAPON_VENDOR_LOCATIONS:
            self.assertIn(name, names)
        for name in GADGET_VENDOR_LOCATIONS:
            self.assertIn(name, names)
        for name in WEAPON_MOD_VENDOR_LOCATIONS:
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        items = self.multiworld.itempool
        locations = self.multiworld.get_unfilled_locations(self.player)
        self.assertEqual(len(items), len(locations))


# ── Skill points option ────────────────────────────────────────────────────────

class TestSkillPointsDisabled(RACSizeMatterTestBase):
    options = {"skill_points_as_checks": 0}

    def test_skill_point_locations_excluded(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in SKILL_POINT_LOCATIONS:
            self.assertNotIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestSkillPointsEnabled(RACSizeMatterTestBase):
    options = {"skill_points_as_checks": 1}

    def test_skill_point_locations_included(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for name in SKILL_POINT_LOCATIONS:
            self.assertIn(name, names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


# ── Weapon options ─────────────────────────────────────────────────────────────

class TestProgressiveWeapons(RACSizeMatterTestBase):
    options = {"progressive_weapons": 1}

    def test_progressive_weapon_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertTrue(
            any(name.endswith(" Progressive Weapon") for name in pool_names),
            "No progressive weapon items found in pool",
        )

    def test_no_individual_weapons_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for weapon in WEAPON_ITEM_TABLE:
            self.assertNotIn(weapon, pool_names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestNonProgressiveWeapons(RACSizeMatterTestBase):
    options = {"progressive_weapons": 0, "starting_weapons": 0, "starting_gadgets": 0}

    def test_individual_weapon_items_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for weapon in WEAPON_ITEM_TABLE:
            self.assertIn(weapon, pool_names)

    def test_no_progressive_weapon_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertFalse(
            any(name.endswith(" Progressive Weapon") for name in pool_names),
            "Progressive weapon items found in non-progressive pool",
        )


# ── Armour options ─────────────────────────────────────────────────────────────

class TestProgressiveArmour(RACSizeMatterTestBase):
    options = {"progressive_armour": 1}

    def test_progressive_armour_items_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertTrue(
            any(name.endswith(" Progressive Pickup") for name in pool_names),
            "No progressive armour items found in pool",
        )

    def test_no_individual_armour_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for piece in ARMOUR_ITEM_TABLE:
            self.assertNotIn(piece, pool_names)

    def test_item_count_matches_location_count(self) -> None:
        self.assertEqual(
            len(self.multiworld.itempool),
            len(self.multiworld.get_unfilled_locations(self.player)),
        )


class TestNonProgressiveArmour(RACSizeMatterTestBase):
    options = {"progressive_armour": 0}

    def test_individual_armour_items_in_pool(self) -> None:
        pool_names = {item.name for item in self.multiworld.itempool}
        for piece in ARMOUR_ITEM_TABLE:
            self.assertIn(piece, pool_names)

    def test_no_progressive_armour_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool]
        self.assertFalse(
            any(name.endswith(" Progressive Pickup") for name in pool_names),
            "Progressive armour items found in non-progressive pool",
        )


# ── Starting items ─────────────────────────────────────────────────────────────

class TestStartingWeapons(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"progressive_weapons": 0, "starting_weapons": 3}

    def test_precollected_weapon_count(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in WEAPON_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 3)


class TestStartingWeaponsZero(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0}

    def test_no_precollected_weapons(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in WEAPON_ITEM_TABLE
               or item.name.endswith(" Progressive Weapon")
        ]
        self.assertEqual(len(precollected), 0)


class TestStartingGadgets(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_gadgets": 2}

    def test_precollected_gadget_count(self) -> None:
        precollected = [
            item.name for item in self.multiworld.precollected_items[self.player]
            if item.name in GADGET_ITEM_TABLE
        ]
        self.assertEqual(len(precollected), 2)


# ── Region access ──────────────────────────────────────────────────────────────

class TestRegionAccess(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0, "starting_gadgets": 0}

    def test_pokitaru_always_reachable(self) -> None:
        self.assertTrue(self.can_reach_region("Pokitaru"))

    def test_ryllus_unreachable_without_weapon(self) -> None:
        self.assertFalse(self.can_reach_region("Ryllus"))

    def test_ryllus_reachable_with_projectile(self) -> None:
        self.collect_by_name(_ANY_PROJECTILE)
        self.assertTrue(self.can_reach_region("Ryllus"))

    def test_kalidon_unreachable_without_gadgets(self) -> None:
        self.collect_by_name(_ANY_PROJECTILE)
        self.assertFalse(self.can_reach_region("Kalidon"))

    def test_kalidon_reachable_with_items(self) -> None:
        self.collect_by_name(_KALIDON_ITEMS)
        self.assertTrue(self.can_reach_region("Kalidon"))

    def test_metalis_unreachable_without_shrink_ray(self) -> None:
        self.collect_by_name(_KALIDON_ITEMS)
        self.assertFalse(self.can_reach_region("Metalis"))

    def test_metalis_reachable_with_items(self) -> None:
        self.collect_by_name(_METALIS_ITEMS)
        self.assertTrue(self.can_reach_region("Metalis"))

    def test_challax_unreachable_without_polarizer(self) -> None:
        self.collect_by_name(_METALIS_ITEMS)
        self.assertFalse(self.can_reach_region("Challax"))

    def test_challax_reachable_with_items(self) -> None:
        self.collect_by_name(_CHALLAX_ITEMS)
        self.assertTrue(self.can_reach_region("Challax"))

    def test_quodrona_unreachable_with_nothing(self) -> None:
        self.assertFalse(self.can_reach_region("Quodrona"))

    def test_quodrona_reachable_with_all_items(self) -> None:
        self.collect_by_name(_ALL_PLANETS)
        self.assertTrue(self.can_reach_region("Quodrona"))

    def test_later_planets_blocked_without_progression(self) -> None:
        for planet in ("Kalidon", "Metalis", "Dreamtime", "Outpost Omega",
                       "Challax", "Dayni Moon", "Inside Clank", "Quodrona"):
            self.assertFalse(self.can_reach_region(planet),
                             f"{planet} reachable with no items")


# ── Goal and beatable ──────────────────────────────────────────────────────────

class TestGoal(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0, "starting_gadgets": 0, "skill_points_as_checks": 0}

    def test_not_beatable_with_nothing(self) -> None:
        self.assertBeatable(False)

    def test_not_beatable_without_quodrona_access(self) -> None:
        self.collect_by_name(_KALIDON_ITEMS)
        self.assertBeatable(False)

    def test_beatable_with_full_progression(self) -> None:
        self.collect_by_name(_ALL_PLANETS)
        self.assertBeatable(True)

    def test_goal_location_reachable_with_full_progression(self) -> None:
        self.collect_by_name(_ALL_PLANETS)
        self.assertTrue(self.can_reach_location("Defeat Otto Destruct"))

    def test_goal_location_unreachable_without_quodrona(self) -> None:
        self.assertFalse(self.can_reach_location("Defeat Otto Destruct"))


# ── Specific location rules ────────────────────────────────────────────────────

class TestLocationRules(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0, "starting_gadgets": 0, "skill_points_as_checks": 1}

    def test_polarized_door_bolt_needs_polarizer_and_hypershot(self) -> None:
        self.collect_by_name(_METALIS_ITEMS)
        self.assertFalse(
            self.can_reach_location("Metalis Titanium Bolt Behind the Polarized Door"),
            "Polarized door reachable without Polarizer",
        )
        self.collect_by_name(["Polarizer"])
        self.assertTrue(
            self.can_reach_location("Metalis Titanium Bolt Behind the Polarized Door"),
        )

    def test_ryllus_bolt_after_wall_needs_full_gadgets(self) -> None:
        self.collect_by_name([_ANY_PROJECTILE, "Hypershot"])
        self.assertFalse(self.can_reach_location("Ryllus Titanium Bolt After the Wall"))
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(self.can_reach_location("Ryllus Titanium Bolt After the Wall"))

    def test_challax_hidden_bolt_needs_polarizer_and_shrink_ray(self) -> None:
        self.collect_by_name(_CHALLAX_ITEMS)
        self.assertTrue(self.can_reach_location("Challax Titanium Bolt Hidden Room"))

    def test_dayni_moon_barnyard_bolt_needs_sprout(self) -> None:
        # Challax chain (minus Sprout-O-Matic) gets to Dayni Moon but the bolt still requires Sprout-O-Matic.
        # Use Polarizer + Shrink Ray + projectile + Hypershot to reach Challax without Sprout-O-Matic.
        partial = [_ANY_PROJECTILE, "Hypershot", "Shrink Ray", "Polarizer"]
        self.collect_by_name(partial)
        self.assertFalse(
            self.can_reach_location("Dayni Moon Titanium Bolt Planting at the Barnyard"),
            "Barnyard bolt reachable without Sprout-O-Matic",
        )
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(
            self.can_reach_location("Dayni Moon Titanium Bolt Planting at the Barnyard"),
        )

    def test_skill_point_train_faster_needs_projectile(self) -> None:
        self.assertFalse(self.can_reach_location("Skill Point Train Faster"))
        self.collect_by_name([_ANY_PROJECTILE])
        self.assertTrue(self.can_reach_location("Skill Point Train Faster"))

    def test_kalidon_locations_need_shrink_ray(self) -> None:
        self.collect_by_name(_RYLLUS_ITEMS)
        self.assertFalse(self.can_reach_location("Kalidon Titanium Bolt Grav-Ramps"))
        self.collect_by_name(["Shrink Ray"])
        self.assertTrue(self.can_reach_location("Kalidon Titanium Bolt Grav-Ramps"))
