from __future__ import annotations

import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct


class WeaponStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("mod_slot_one",   ctypes.c_uint8),
        ("mod_slot_two",   ctypes.c_uint8),
        ("mod_slot_three", ctypes.c_uint8),
        ("_pad",           ctypes.c_uint8 * 5),
        ("unlocked",       ctypes.c_uint8),
    ]

    _MOD_FIELD_OFFSET = 0x3D
    _UNLOCK_FIELD_OFFSET = 0x45

class GadgetStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("icon",     ctypes.c_uint32),
        ("_pad",     ctypes.c_uint8 * 0x24),
        ("unlocked", ctypes.c_uint8),
    ]

    _ICON_FIELD_OFFSET = 0x1D
    _UNLOCK_FIELD_OFFSET = 0x45

def make_weapon_struct_cls(name: str, weapon_base: int) -> type[WeaponStruct]:
    return type(
        f"WeaponStruct_{name}",
        (WeaponStruct,),
        {"BASE_ADDRESS": weapon_base + WeaponStruct._MOD_FIELD_OFFSET},
    )

def make_gadget_struct_cls(name: str, gadget_base: int) -> type[GadgetStruct]:
    return type(
        f"GadgetStruct_{name}",
        (GadgetStruct,),
        {"BASE_ADDRESS": gadget_base + GadgetStruct._ICON_FIELD_OFFSET},
    )
