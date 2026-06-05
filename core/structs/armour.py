import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct
from ..data.addresses import ARMOUR_BASE, ARMOUR_SET_COLLECTED_ADDR


class ArmourStruct(MemoryStruct):

    BASE_ADDRESS = ARMOUR_BASE
    _pack_ = 1
    _fields_ = [
        ("chestplate",   ctypes.c_uint8),
        ("helmet",       ctypes.c_uint8),
        ("gloves_left",  ctypes.c_uint8),
        ("gloves_right", ctypes.c_uint8),
        ("boots_left",   ctypes.c_uint8),
        ("boots_right",  ctypes.c_uint8),
        ("wildfire",     ctypes.c_uint8),
        ("sludge",       ctypes.c_uint8),
        ("crystallix",   ctypes.c_uint8),
        ("electroshock", ctypes.c_uint8),
        ("mega_bomb",    ctypes.c_uint8),
        ("hyperborean",  ctypes.c_uint8),
        ("chameleon",    ctypes.c_uint8),
    ]

    SLOT_FIELDS: tuple[str, ...] = (
        "chestplate", "helmet", "gloves_left", "gloves_right", "boots_left", "boots_right",
    )
    SET_FIELDS: tuple[str, ...] = (
        "wildfire", "sludge", "crystallix", "electroshock", "mega_bomb", "hyperborean", "chameleon",
    )


class ArmourSetCollectedStruct(MemoryStruct):
    """Two bytes starting at ARMOUR_SET_COLLECTED_ADDR.

    Byte 0 (0x21F4B442) — pure armour sets collected:
        bit 0 (0x01) = Wildfire      bit 4 (0x10) = Mega Bomb
        bit 1 (0x02) = Sludge Mk9   bit 5 (0x20) = Hyperborean
        bit 2 (0x04) = Crystallix   bit 6 (0x40) = Chameleon
        bit 3 (0x08) = Electroshock

    Byte 1 (0x21F4B443) — hybrid combos equipped:
        bit 0 (0x01) = Shock Crystal   bit 3 (0x08) = Ice II
        bit 1 (0x02) = Wildburst       bit 4 (0x10) = Stalker
        bit 2 (0x04) = Triple Wave
    """
    BASE_ADDRESS = ARMOUR_SET_COLLECTED_ADDR
    _pack_ = 1
    _fields_ = [
        ("pure_sets",   ctypes.c_uint8),
        ("hybrid_sets", ctypes.c_uint8),
    ]
