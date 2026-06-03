__all__ = [
    # armour address resolvers
    "ArmourAddresses", "ArmourPiece", "PlayerArmour",
    # weapon/gadget address resolvers + data
    "WeaponAddresses", "GadgetAddresses",
    "WEAPON_MOD_COUNTS", "WEAPON_STRUCT_SIZE", "WEAPON_MIN_CONSECUTIVE",
    "is_weapon_candidate", "is_ps2_weapon_candidate",
    "WEAPON_ORDER", "GADGET_ORDER", "build_weapons",
    # pickup address resolvers
    "TitaniumBoltAddresses",
    # raw addresses
    "ARMOUR_BASE", "TITANIUM_BOLT_BASE", "CHEATS",
    "BOLT_PICKUP_MASK", "CURRENT_PLANET_ADDRESS", "PLAYER_BOLT_COUNT", "PLANET_LOAD_ADDRESS",
    "PLAYER_ADDRS", "PLAYER_STATE", "PLAYER_HEALTH",
    "MENU_ADDR_BY_PLANET_ID", "PRELOAD_MENU_ADDR_BY_PLANET_ID", "WEAPON_ARRAY_BASE_BY_PLANET",
    "DisplayedTextBox", "TextBoxDisplayAddrs",
    # planets
    "Planet", "Planets", "BY_ID",
    # cutscenes
    "Cutscene", "arm_cutscenes", "suppress_disabled_cutscenes",
    "ENTER_CUTSCENES", "CUTSCENE_BEFORE_SPROUT_O_MATIC", "SPROUT_O_MATIC_CUTSCENE",
    "ELECTROSHOCK_GLOVES_CUTSCENE", "POKITARU_RYLLUS_ALT_TRIGGER", "CUTSCENES",
    # skill points
    "SkillPoint", "SKILL_POINT_ADDRESS", "SKILL_POINTS", "LOCATION_SKILL_POINTS", "SKILL_POINT_BY_PLANET_AND_MASK",
    "CHALLENGE_SKILL_POINTS",
    # titanium bolts
    "TitaniumBolt", "TITANIUM_BOLTS", "BOLT_BY_PLANET_AND_DELTA",
    # armour pickups
    "ArmourPickup", "ARMOUR_PICKUPS", "ARMOUR_FLAG_TO_LOCATION",
    # challenges
    "ChallengePickup", "CHALLENGE_PICKUPS", "CHALLENGE_ADDRESS_MAP", "CHALLENGE_ONLY_ITEMS",
    "METALIS_CLANK_PICKUPS", "DAYNI_MOON_CLANK_PICKUPS", "ALL_CLANK_ADDRESS_MAP",
    # armour set checks
    "ArmourSets", "ArmourSetCheck", "ARMOUR_SET_CHECKS",
    # player states
    "PlayerState",
    # infobots / planet state
    "INFOBOT_ITEM_TO_PLANET", "INFOBOT_UNLOCK_VALUE", "AUTO_UNLOCK_ADDRESSES", "PLANET_STATE_ADDRESSES",
]

# ── Armour address resolvers ───────────────────────────────────────────────────
# ── Raw addresses ──────────────────────────────────────────────────────────────
from .addresses import (
    ARMOUR_BASE,
    BOLT_PICKUP_MASK,
    CHEATS,
    CURRENT_PLANET_ADDRESS,
    MENU_ADDR_BY_PLANET_ID,
    PLANET_LOAD_ADDRESS,
    PLAYER_ADDRS,
    PLAYER_BOLT_COUNT,
    PLAYER_HEALTH,
    PLAYER_STATE,
    PRELOAD_MENU_ADDR_BY_PLANET_ID,
    TITANIUM_BOLT_BASE,
    WEAPON_ARRAY_BASE_BY_PLANET,
    DisplayedTextBox,
    TextBoxDisplayAddrs,
)
from .armour import ArmourAddresses, ArmourPiece, PlayerArmour

# ── Armour pickups ────────────────────────────────────────────────────────────
from .locations.armour_pickups import ARMOUR_FLAG_TO_LOCATION, ARMOUR_PICKUPS, ArmourPickup

# ── Armour set checks ─────────────────────────────────────────────────────────
from .locations.armour_set_checks import ARMOUR_SET_CHECKS, ArmourSetCheck, ArmourSets

# ── Challenges ────────────────────────────────────────────────────────────────
from .locations.challenges import (
    ALL_CLANK_ADDRESS_MAP,
    CHALLENGE_ADDRESS_MAP,
    CHALLENGE_ONLY_ITEMS,
    CHALLENGE_PICKUPS,
    DAYNI_MOON_CLANK_PICKUPS,
    METALIS_CLANK_PICKUPS,
    ChallengePickup,
)

# ── Cutscenes ─────────────────────────────────────────────────────────────────
from .cutscenes import (
    CUTSCENE_BEFORE_SPROUT_O_MATIC,
    CUTSCENES,
    ELECTROSHOCK_GLOVES_CUTSCENE,
    ENTER_CUTSCENES,
    POKITARU_RYLLUS_ALT_TRIGGER,
    SPROUT_O_MATIC_CUTSCENE,
    Cutscene,
    arm_cutscenes,
    suppress_disabled_cutscenes,
)

# ── Infobots ──────────────────────────────────────────────────────────────────
from .infobots import AUTO_UNLOCK_ADDRESSES, INFOBOT_ITEM_TO_PLANET, INFOBOT_UNLOCK_VALUE, PLANET_STATE_ADDRESSES

# ── Pickup address resolvers ───────────────────────────────────────────────────
from .pickups import TitaniumBoltAddresses

# ── Planets ────────────────────────────────────────────────────────────────────
from .planets import BY_ID, Planet, Planets

# ── Player states ──────────────────────────────────────────────────────────────
from .player_states import PlayerState

# ── Skill points ──────────────────────────────────────────────────────────────
from .locations.skill_points import (
    CHALLENGE_SKILL_POINTS,
    LOCATION_SKILL_POINTS,
    SKILL_POINT_ADDRESS,
    SKILL_POINT_BY_PLANET_AND_MASK,
    SKILL_POINTS,
    SkillPoint,
)

# ── Titanium bolts ────────────────────────────────────────────────────────────
from .locations.titanium_bolts import BOLT_BY_PLANET_AND_DELTA, TITANIUM_BOLTS, TitaniumBolt

# ── Weapon/gadget address resolvers ───────────────────────────────────────────
from .weapons import (
    GADGET_ORDER,
    WEAPON_MIN_CONSECUTIVE,
    WEAPON_MOD_COUNTS,
    WEAPON_ORDER,
    WEAPON_STRUCT_SIZE,
    GadgetAddresses,
    WeaponAddresses,
    build_weapons,
    is_ps2_weapon_candidate,
    is_weapon_candidate,
)
