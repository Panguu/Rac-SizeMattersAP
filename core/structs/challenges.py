import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct

CLANK_CHALLENGE_BASE = 0x1F4B3DE
CLANK_CHALLENGE_SIZE = 39

SKYBOARD_BASE = 0x1F4B407

class ClankChallengeStruct(MemoryStruct):

    BASE_ADDRESS = CLANK_CHALLENGE_BASE
    _pack_ = 1
    _fields_ = [
        ("_body", ctypes.c_uint8 * CLANK_CHALLENGE_SIZE),
    ]

class SkyboardStruct(MemoryStruct):

    BASE_ADDRESS = SKYBOARD_BASE
    _pack_ = 1
    _fields_ = [
        ("kalidon_low",        ctypes.c_uint8),
        ("kalidon_high",       ctypes.c_uint8),
        ("outpost_omega_low",  ctypes.c_uint8),
        ("outpost_omega_high", ctypes.c_uint8),
    ]
