from __future__ import annotations

import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct

class CountdownTimerStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("timer", ctypes.c_float)]

class VendorVisibilityStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [("visibility", ctypes.c_int16)]

def make_countdown_cls(planet_name: str, countdown_addr: int) -> type[CountdownTimerStruct]:
    return type(
        f"CountdownTimerStruct_{planet_name}",
        (CountdownTimerStruct,),
        {"BASE_ADDRESS": countdown_addr},
    )

def make_vendor_visibility_cls(planet_name: str, is_visible_addr: int) -> type[VendorVisibilityStruct]:
    return type(
        f"VendorVisibilityStruct_{planet_name}",
        (VendorVisibilityStruct,),
        {"BASE_ADDRESS": is_visible_addr},
    )
