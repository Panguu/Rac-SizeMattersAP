import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import TITANIUM_BOLT_BASE


class TitaniumBoltStruct(MemoryStruct):

    BASE_ADDRESS = TITANIUM_BOLT_BASE
    _pack_ = 1
    _fields_ = [
        ("pickup", ctypes.c_uint8),
        ("_pad",   ctypes.c_uint8 * 4),
        ("total",  ctypes.c_uint8),
    ]
