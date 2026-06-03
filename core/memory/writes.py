# Re-export shim — logic lives in core/states/memory/writes.py
from ..states.memory.writes import (  # noqa: F401
    apply_slots_from_armour,
    apply_tracked_armour,
    apply_tracked_weapons,
    restore_tracked_weapon_state,
    zero_weapon,
)
