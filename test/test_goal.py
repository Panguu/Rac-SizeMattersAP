"""Tests for goal beatability and specific location rules."""
from .bases import (
    ALL_PLANETS,
    ANY_PROJECTILE,
    CHALLAX_ITEMS,
    KALIDON_ITEMS,
    METALIS_ITEMS,
    RYLLUS_ITEMS,
    RACSizeMatterTestBase,
)

_BASE = {"starting_weapons": 0, "starting_gadgets": 0, "skill_points_as_checks": 0}


class TestGoal(RACSizeMatterTestBase):
    run_default_tests = False
    options = _BASE

    def test_not_beatable_with_nothing(self) -> None:
        self.assertBeatable(False)

    def test_not_beatable_without_quodrona_access(self) -> None:
        self.collect_by_name(KALIDON_ITEMS)
        self.assertBeatable(False)

    def test_beatable_with_full_progression(self) -> None:
        self.collect_by_name(ALL_PLANETS)
        self.assertBeatable(True)

    def test_goal_location_reachable_with_full_progression(self) -> None:
        self.collect_by_name(ALL_PLANETS)
        self.assertTrue(self.can_reach_location("Defeat Otto Destruct"))

    def test_goal_location_unreachable_without_quodrona(self) -> None:
        self.assertFalse(self.can_reach_location("Defeat Otto Destruct"))

    def test_not_beatable_with_only_projectile(self) -> None:
        self.collect_by_name([ANY_PROJECTILE])
        self.assertBeatable(False)

    def test_not_beatable_with_metalis_items_only(self) -> None:
        self.collect_by_name(METALIS_ITEMS)
        self.assertBeatable(False)


class TestLocationRules(RACSizeMatterTestBase):
    run_default_tests = False
    options = {"starting_weapons": 0, "starting_gadgets": 0, "skill_points_as_checks": 1}

    def test_polarized_door_bolt_needs_polarizer_and_hypershot(self) -> None:
        self.collect_by_name(METALIS_ITEMS)
        self.assertFalse(
            self.can_reach_location("Metalis Titanium Bolt Behind the Polarized Door"),
            "Polarized door reachable without Polarizer",
        )
        self.collect_by_name(["Polarizer"])
        self.assertTrue(self.can_reach_location("Metalis Titanium Bolt Behind the Polarized Door"))

    def test_ryllus_bolt_after_wall_needs_full_gadgets(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Hypershot"])
        self.assertFalse(self.can_reach_location("Ryllus Titanium Bolt After the Wall"))
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(self.can_reach_location("Ryllus Titanium Bolt After the Wall"))

    def test_challax_hidden_bolt_needs_polarizer_and_shrink_ray(self) -> None:
        self.collect_by_name(CHALLAX_ITEMS)
        self.assertTrue(self.can_reach_location("Challax Titanium Bolt Hidden Room"))

    def test_challax_mimic_plant_lob_needs_sprout(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Hypershot", "Shrink Ray", "Polarizer"])
        self.assertFalse(
            self.can_reach_location("Challax Titanium Bolt Mimic Plant Lob"),
            "Mimic Plant Lob reachable without Sprout-O-Matic",
        )
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(self.can_reach_location("Challax Titanium Bolt Mimic Plant Lob"))

    def test_dayni_moon_barnyard_bolt_needs_sprout(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Hypershot", "Shrink Ray", "Polarizer"])
        self.assertFalse(
            self.can_reach_location("Dayni Moon Titanium Bolt Planting at the Barnyard"),
            "Barnyard bolt reachable without Sprout-O-Matic",
        )
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(self.can_reach_location("Dayni Moon Titanium Bolt Planting at the Barnyard"))

    def test_kalidon_bolt_behind_ship_needs_hypershot(self) -> None:
        self.collect_by_name(RYLLUS_ITEMS)
        self.assertFalse(
            self.can_reach_location("Kalidon Titanium Bolt Behind The Ship"),
            "Kalidon bolt reachable without Hypershot when at Kalidon",
        )
        self.collect_by_name(["Shrink Ray"])
        self.assertTrue(self.can_reach_location("Kalidon Titanium Bolt Behind The Ship"))

    def test_kalidon_locations_need_shrink_ray(self) -> None:
        self.collect_by_name(RYLLUS_ITEMS)
        self.assertFalse(self.can_reach_location("Kalidon Titanium Bolt Grav-Ramps"))
        self.collect_by_name(["Shrink Ray"])
        self.assertTrue(self.can_reach_location("Kalidon Titanium Bolt Grav-Ramps"))

    def test_skill_point_train_faster_needs_projectile(self) -> None:
        self.assertFalse(self.can_reach_location("Skill Point Train Faster"))
        self.collect_by_name([ANY_PROJECTILE])
        self.assertTrue(self.can_reach_location("Skill Point Train Faster"))
