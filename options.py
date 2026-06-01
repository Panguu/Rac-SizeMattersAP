from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, PerGameCommonOptions, Range, Toggle


class ProgressiveWeapons(Toggle):
    """Unlock weapons in a fixed order via Progressive Weapon items rather than as individual items."""
    display_name = "Progressive Weapons"


class ProgressiveArmour(Toggle):
    """Unlock armour pieces in a fixed order via Progressive Armour items rather than as individual pieces."""
    display_name = "Progressive Armour"



class ClankChallenges(Toggle):
    """Include Clank challenge arenas as location checks. Adds 9 locations and makes
    challenge-exclusive items (Polarizer, Shrink Ray, and several armour pieces) accessible."""
    display_name = "Clank Challenges"


class SkyboardChallenges(Toggle):
    """Include Skyboard race challenges as location checks."""
    display_name = "Skyboard Challenges"


class ArmourSetChecks(DefaultOnToggle):
    """Treat equipping a complete armour set as a location check. Adds 13 locations to the pool."""
    display_name = "Armour Set Checks"


class SkillPointsAsChecks(Choice):
    """Treat skill point unlocks as location checks.
    normal: excludes Clank and Skyboard challenge skill points (adds 18 locations).
    with_challenges: includes all skill points (adds 25 locations)."""
    display_name = "Skill Points as Checks"
    option_off            = 0
    option_normal         = 1
    option_with_challenges = 2
    default = 0


class StartingWeapons(Range):
    """Number of random weapons the player begins the game with."""
    display_name = "Starting Weapons"
    range_start = 0
    range_end = 13
    default = 2


class StartingGadgets(Range):
    """Number of random gadgets the player begins the game with. Default of 1 grants the Hypershot."""
    display_name = "Starting Gadgets"
    range_start = 0
    range_end = 8
    default = 1


class DeathAmnesty(Range):
    """Number of deaths allowed before items are removed from the player's inventory on death.
    Higher values are more forgiving."""
    display_name = "Death Amnesty"
    range_start = 0
    range_end = 5
    default = 0


class StartingBolts(Range):
    """Number of bolts the player begins the game with."""
    display_name = "Starting Bolts"
    range_start = 0
    range_end = 100_000
    default = 45_000


@dataclass
class RACSizeMatterOptions(PerGameCommonOptions):
    progressive_weapons: ProgressiveWeapons
    progressive_armour: ProgressiveArmour
    death_link: DeathLink
    death_amnesty: DeathAmnesty
    clank_challenges: ClankChallenges
    skyboard_challenges: SkyboardChallenges
    skill_points_as_checks: SkillPointsAsChecks
    armour_set_checks: ArmourSetChecks
    starting_weapons: StartingWeapons
    starting_gadgets: StartingGadgets
    starting_bolts: StartingBolts
