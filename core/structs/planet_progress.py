import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct

PLANET_PROGRESS_BASE = 0x21F4C661

class PlanetProgressStruct(MemoryStruct):

    BASE_ADDRESS = PLANET_PROGRESS_BASE
    _pack_ = 1
    _fields_ = [
        ("pokitaru",      ctypes.c_uint8),
        ("ryllus",        ctypes.c_uint8),
        ("kalidon",       ctypes.c_uint8),
        ("metalis",       ctypes.c_uint8),
        ("dreamtime",     ctypes.c_uint8),
        ("outpost_omega", ctypes.c_uint8),
        ("challax",       ctypes.c_uint8),
        ("dayni_moon",    ctypes.c_uint8),
        ("inside_clank",  ctypes.c_uint8),
        ("quodrona",      ctypes.c_uint8),
    ]

    PLANET_ORDER: tuple[str, ...] = (
        "pokitaru", "ryllus", "kalidon", "metalis", "dreamtime",
        "outpost_omega", "challax", "dayni_moon", "inside_clank", "quodrona",
    )
    PLANET_NAME_ORDER: tuple[str, ...] = (
        "POKITARU", "RYLLUS", "KALIDON", "METALIS", "DREAMTIME",
        "OUTPOST_OMEGA", "CHALLAX", "DAYNI_MOON", "INSIDE_CLANK", "QUODRONA",
    )
