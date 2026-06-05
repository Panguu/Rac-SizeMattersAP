from __future__ import annotations

import ctypes

from ...interface_orchestrator.structs.base import MemoryStruct


class PlayerMovementStruct(MemoryStruct):

    BASE_ADDRESS = 0
    _pack_ = 1
    _fields_ = [
        ("state", ctypes.c_uint8),
    ]

def make_player_movement_cls(planet_name: str, movement_addr: int) -> type[PlayerMovementStruct]:
    return type(
        f"PlayerMovementStruct_{planet_name}",
        (PlayerMovementStruct,),
        {"BASE_ADDRESS": movement_addr},
    )
