from __future__ import annotations

import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct

class MenuStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

class PreloadMenuStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

def make_menu_cls(planet_name: str, menu_addr: int) -> type[MenuStruct]:
    return type(
        f"MenuStruct_{planet_name}",
        (MenuStruct,),
        {"BASE_ADDRESS": menu_addr},
    )

def make_preload_menu_cls(planet_name: str, preload_addr: int) -> type[PreloadMenuStruct]:
    return type(
        f"PreloadMenuStruct_{planet_name}",
        (PreloadMenuStruct,),
        {"BASE_ADDRESS": preload_addr},
    )
