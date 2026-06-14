import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import NEW_PLANET_START_LOAD_ADDR


class PlanetLoadStruct(MemoryStruct):
    """Two consecutive uint32 values that signal planet load lifecycle events.

    start_load    (0x21F4A744): becomes non-zero when a new planet begins loading.
    load_complete (0x21F4A748): becomes non-zero when loading has finished.
    """

    BASE_ADDRESS = NEW_PLANET_START_LOAD_ADDR
    _pack_ = 1
    _fields_ = [
        ("start_load",    ctypes.c_uint32),
        ("load_complete", ctypes.c_uint32),
    ]
