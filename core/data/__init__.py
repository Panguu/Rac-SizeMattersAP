"""Backwards-compatibility shim.

The ``core.data`` package was flattened into top-level ``core`` domain modules
(``core.weapons``, ``core.planets``, ``core.armour`` …).  This shim re-exports
the few symbols still imported through the old ``core.data`` path so that
``items.py`` (and any other external consumer) keeps working unchanged.
"""
from ..planets import INFOBOT_ITEM_TO_PLANET
from ..weapons import WEAPON_MAX_LEVELS, WEAPON_MOD_COUNTS

__all__ = [
    "WEAPON_MAX_LEVELS",
    "WEAPON_MOD_COUNTS",
    "INFOBOT_ITEM_TO_PLANET",
]
