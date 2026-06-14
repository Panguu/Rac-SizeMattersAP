import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct


class QuickSelectStruct(MemoryStruct):
    BASE_ADDRESS = 0x21F4B364
    _pack_ = 1
    _fields_ = [
        ("right",         ctypes.c_uint32),
        ("top_right",     ctypes.c_uint32),
        ("top_middle",    ctypes.c_uint32),
        ("top_left",      ctypes.c_uint32),
        ("left",          ctypes.c_uint32),
        ("bottom_left",   ctypes.c_uint32),
        ("bottom_middle", ctypes.c_uint32),
        ("bottom_right",  ctypes.c_uint32),
    ]

    SLOT_ORDER: tuple[str, ...] = (
        "right", "top_right", "top_middle", "top_left",
        "left", "bottom_left", "bottom_middle", "bottom_right",
    )
