import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import PLANET_MISSION_ADDRESSES as _ADDRS

MISSIONS_BASE = _ADDRS["Pokitaru"]  # 0x21F4B3C4


class MissionsStruct(MemoryStruct):
    """2-byte mission progress value for each planet, contiguous from Pokitaru."""

    BASE_ADDRESS = MISSIONS_BASE
    _pack_ = 1
    _fields_ = [
        ("pokitaru",        ctypes.c_uint16),  # +0x00  0x21F4B3C4
        ("ryllus",          ctypes.c_uint16),  # +0x02  0x21F4B3C6
        ("kalidon",         ctypes.c_uint16),  # +0x04  0x21F4B3C8
        ("metalis",         ctypes.c_uint16),  # +0x06  0x21F4B3CA
        ("dreamtime",       ctypes.c_uint16),  # +0x08  0x21F4B3CC
        ("outpost_omega",   ctypes.c_uint16),  # +0x0A  0x21F4B3CE
        ("challax",         ctypes.c_uint16),  # +0x0C  0x21F4B3D0
        ("dayni_moon",      ctypes.c_uint16),  # +0x0E  0x21F4B3D2
        ("inside_clank",    ctypes.c_uint16),  # +0x10  0x21F4B3D4
        ("quodrona",        ctypes.c_uint16),  # +0x12  0x21F4B3D6
        ("outpost_omega_2", ctypes.c_uint16),  # +0x14  0x21F4B3D8
    ]
