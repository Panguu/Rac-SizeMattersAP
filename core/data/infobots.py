"""Backwards-compatibility shim — infobot data now lives in ``core.planets``."""
from ..planets import (
    AUTO_UNLOCK_ADDRESSES,
    INFOBOT_ITEM_TO_PLANET,
    INFOBOT_UNLOCK_VALUE,
    PLANET_STATE_ADDRESSES,
)

__all__ = [
    "AUTO_UNLOCK_ADDRESSES",
    "INFOBOT_ITEM_TO_PLANET",
    "INFOBOT_UNLOCK_VALUE",
    "PLANET_STATE_ADDRESSES",
]
