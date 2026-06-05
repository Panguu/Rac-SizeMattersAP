import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.cutscenes import (
    CUTSCENE_BEFORE_SPROUT_O_MATIC,
    ELECTROSHOCK_GLOVES_CUTSCENE,
    SPROUT_O_MATIC_CUTSCENE,
)

_GOAL_ADDR = 0x3D7FC8


class CutsceneValueStruct(MemoryStruct):
    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("value", ctypes.c_int32)]


class GoalCutsceneStruct(CutsceneValueStruct):
    BASE_ADDRESS = _GOAL_ADDR


class ElectroshockCutsceneStruct(CutsceneValueStruct):
    BASE_ADDRESS = ELECTROSHOCK_GLOVES_CUTSCENE


class BeforeSproutCutsceneStruct(CutsceneValueStruct):
    BASE_ADDRESS = CUTSCENE_BEFORE_SPROUT_O_MATIC


class SproutCutsceneStruct(CutsceneValueStruct):
    BASE_ADDRESS = SPROUT_O_MATIC_CUTSCENE
