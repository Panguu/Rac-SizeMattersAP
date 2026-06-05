import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct

CLANK_CHALLENGE_BASE = 0x1F4B3DB  # starts at Metalis unlock addr; Dayni Moon unlock at +0x18
CLANK_CHALLENGE_SIZE = 42          # covers 0x1F4B3DB–0x1F4B404

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
