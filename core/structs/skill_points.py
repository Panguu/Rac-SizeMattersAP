import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import SKILL_POINTS as SKILL_POINTS_ADDRESS

class SkillPointsStruct(MemoryStruct):

    BASE_ADDRESS = SKILL_POINTS_ADDRESS
    _pack_ = 1
    _fields_ = [
        ("bitmask", ctypes.c_uint64),
    ]
