import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import (
    CONTROLLER_BUTTONS_ADDRESS,
    CONTROLLER_PAUSE_SELECT_ADDRESS,
    PLAYER_BOLT_COUNT,
)


class GameStatusStruct(MemoryStruct):

    BASE_ADDRESS = PLAYER_BOLT_COUNT
    _pack_ = 1
    _fields_ = [
        ("bolt_count",     ctypes.c_uint32),
        ("current_planet", ctypes.c_uint8),
        ("_pad1",          ctypes.c_uint8 * 3),
        ("planet_load",    ctypes.c_uint8),
        ("_pad2",          ctypes.c_uint8 * 7),
        ("challenge_mode", ctypes.c_uint8),
    ]

class ControllerStruct(MemoryStruct):

    BASE_ADDRESS = CONTROLLER_PAUSE_SELECT_ADDRESS
    _pack_ = 1
    _fields_ = [
        ("pause_select", ctypes.c_uint8),
        ("buttons",      ctypes.c_uint8),
    ]

    assert BASE_ADDRESS + 1 == CONTROLLER_BUTTONS_ADDRESS
