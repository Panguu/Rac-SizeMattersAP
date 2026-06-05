from __future__ import annotations

from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.armour import ArmourSetCollectedStruct, ArmourStruct
from ..structs.challenges import ClankChallengeStruct, SkyboardStruct
from ..structs.cutscenes import (
    BeforeSproutCutsceneStruct,
    ElectroshockCutsceneStruct,
    GoalCutsceneStruct,
    SproutCutsceneStruct,
)
from ..structs.game_status import ControllerStruct, GameStatusStruct
from ..structs.planet_progress import PlanetProgressStruct
from ..structs.quick_select import QuickSelectStruct
from ..structs.skill_points import SkillPointsStruct
from ..structs.titanium_bolts import TitaniumBoltStruct


def build_global_address_map() -> AddressMap:
    address_map = AddressMap(interface_id="global")
    address_map.register(
        QuickSelectStruct,
        ArmourStruct,
        ArmourSetCollectedStruct,
        TitaniumBoltStruct,
        SkillPointsStruct,
        GameStatusStruct,
        ControllerStruct,
        PlanetProgressStruct,
        ClankChallengeStruct,
        SkyboardStruct,
        GoalCutsceneStruct,
        ElectroshockCutsceneStruct,
        BeforeSproutCutsceneStruct,
        SproutCutsceneStruct,
    )
    return address_map
