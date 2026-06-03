# Re-export shim — logic lives in core/states/memory/singletons.py
from ..states.memory.singletons import (  # noqa: F401
    _ARMOUR_PIECES,
    _ARMOUR_SET_ORDER,
    _PIECE_TO_SLOTS,
    ARMOUR_ADDRESSES,
    BOLTS,
    GADGETS,
    PLAYER_ARMOUR_SLOTS,
    WEAPONS,
    load_weapons_for_planet,
    sync_weapons,
)
