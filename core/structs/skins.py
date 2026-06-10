import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct


class SkinStruct(MemoryStruct):
    # +0x00 unlocked — bitmask; bit N = skin N is available.
    # +0x01 equipped — ID of the skin Ratchet is currently wearing.
    BASE_ADDRESS = 0x21F4B45A
    _pack_ = 1
    _fields_ = [
        ("unlocked", ctypes.c_uint8),
        ("equipped", ctypes.c_uint8),
    ]
