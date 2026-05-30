"""Tests for the Skill Points as Checks option."""
from ..locations import SKILL_POINT_LOCATIONS
from .bases import ANY_PROJECTILE, RYLLUS_ITEMS, RACSizeMatterTestBase

_BASE = {"starting_weapons": 0, "starting_gadgets": 0, "skill_points_as_checks": 1}


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


class TestSkillPointRules(RACSizeMatterTestBase):
    run_default_tests = False
    options = _BASE

    def test_train_faster_needs_projectile(self) -> None:
        self.assertFalse(self.can_reach_location("Skill Point Train Faster"))
        self.collect_by_name([ANY_PROJECTILE])
        self.assertTrue(self.can_reach_location("Skill Point Train Faster"))

    def test_dont_rock_the_boat_needs_projectile(self) -> None:
        self.assertFalse(self.can_reach_location("Skill Point Dont Rock The Boat"))
        self.collect_by_name([ANY_PROJECTILE])
        self.assertTrue(self.can_reach_location("Skill Point Dont Rock The Boat"))

    def test_cows_get_crabby_needs_mootator(self) -> None:
        self.collect_by_name([ANY_PROJECTILE])
        self.assertFalse(self.can_reach_location("Skill Point Do Cows Get Crabby"))
        self.collect_by_name(["Mootator"])
        self.assertTrue(self.can_reach_location("Skill Point Do Cows Get Crabby"))

    def test_bury_the_pygmies_needs_sprout_and_hypershot(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Sprout-O-Matic"])
        self.assertFalse(
            self.can_reach_location("Skill Point Bury The Pygmies"),
            "Bury The Pygmies reachable without Hypershot",
        )
        self.collect_by_name(["Hypershot"])
        self.assertTrue(self.can_reach_location("Skill Point Bury The Pygmies"))

    def test_bury_the_pygmies_needs_sprout(self) -> None:
        self.collect_by_name([ANY_PROJECTILE, "Hypershot"])
        self.assertFalse(
            self.can_reach_location("Skill Point Bury The Pygmies"),
            "Bury The Pygmies reachable without Sprout-O-Matic",
        )
        self.collect_by_name(["Sprout-O-Matic"])
        self.assertTrue(self.can_reach_location("Skill Point Bury The Pygmies"))

    def test_kalidon_skill_points_need_shrink_ray(self) -> None:
        self.collect_by_name(RYLLUS_ITEMS)
        for loc in (
            "Skill Point Explosive Ordnance Disposal",
            "Skill Point Super Lombax",
            "Skill Point Be A Cool Skyboarder",
        ):
            self.assertFalse(self.can_reach_location(loc), f"{loc} reachable without Shrink Ray")
        self.collect_by_name(["Shrink Ray"])
        for loc in (
            "Skill Point Explosive Ordnance Disposal",
            "Skill Point Super Lombax",
            "Skill Point Be A Cool Skyboarder",
        ):
            self.assertTrue(self.can_reach_location(loc))
