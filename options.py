from dataclasses import dataclass

from Options import (Choice, DeathLink, DefaultOnToggle, PerGameCommonOptions, Range, Toggle,
                     Accessibility, ProgressionBalancing, OptionGroup)


class ProgressiveWeapons(Choice):
    """Controls how weapons, mods, and level upgrades are distributed.
    off: Weapons, mods, and levels are individual random items.
    progressive_mods: Progressive Weapon items unlock the weapon then grant mods in sequence.
    progressive_levels: Progressive Weapon items unlock the weapon then grant level upgrades.
    all_progressive: Progressive Weapon items grant the unlock, mods, then level upgrades in sequence."""
    display_name = "Progressive Weapons"
    option_off                = 0
    option_progressive_mods   = 1
    option_progressive_levels = 2
    option_all_progressive    = 3
    default = 0


class ProgressiveArmour(Toggle):
    """Unlock armour pieces in a fixed order via Progressive Armour items rather than as individual pieces."""
    display_name = "Progressive Armour"


class ClankChallenges(Choice):
    """Controls how Clank challenge arenas are included as location checks.
    item_challenges: only the armour/gadget reward for each challenge arena (default).
    all_challenges: every individual challenge completion is a separate check."""
    display_name = "Clank Challenges"
    option_off             = 0
    option_item_challenges = 1
    option_all_challenges  = 2
    default = 1


class SkyboardChallenges(Choice):
    """Controls whether Skyboard race challenges are included as location checks.
    all_challenges: every individual race completion is a separate check."""
    display_name = "Skyboard Challenges"
    option_off            = 0
    option_all_challenges = 1
    default = 0



class ArmourSetChecks(DefaultOnToggle):
    """Treat equipping a complete armour set as a location check. Adds 13 locations to the pool."""
    display_name = "Armour Set Checks"


class SkillPoints(Toggle):
    """Include skill point challenges as location checks."""
    display_name = "Skill Points"


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


class StartingSkin(Choice):
    """Cosmetic skin for Ratchet. Applied automatically on each planet load.
    All skins are unlocked in-game regardless of this choice."""
    display_name = "Starting Skin"
    option_default          = 0
    option_pirate_ratchet   = 1
    option_godzilla_ratchet = 2
    option_trash_ratchet    = 3
    option_swim_ratchet     = 4
    option_kanga_ratchet    = 5
    option_hiro_ratchet     = 6
    default = 0


@dataclass
class RACSizeMatterOptions(PerGameCommonOptions):
    progressive_weapons: ProgressiveWeapons
    progressive_armour: ProgressiveArmour
    death_link: DeathLink
    death_amnesty: DeathAmnesty
    clank_challenges: ClankChallenges
    skyboard_challenges: SkyboardChallenges
    armour_set_checks: ArmourSetChecks
    skill_points: SkillPoints
    starting_weapons: StartingWeapons
    starting_gadgets: StartingGadgets
    starting_bolts: StartingBolts
    starting_skin: StartingSkin

racsm_option_groups = [
    OptionGroup("Generic Options", [
        ProgressionBalancing,
        Accessibility,
        DeathLink,
        DeathAmnesty,
    ]),
    OptionGroup("RACSM Item Options", [
        StartingWeapons,
        StartingGadgets,
        StartingBolts,
        ProgressiveWeapons,
        ProgressiveArmour,
    ]),
    OptionGroup("RACSM Location Options", [
        ClankChallenges,
        SkyboardChallenges,
        SkillPoints,
        ArmourSetChecks,
    ]),
    OptionGroup("RACSM Cosmetic Options", [
        StartingSkin,
    ])
]