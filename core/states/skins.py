from __future__ import annotations

from typing import TYPE_CHECKING

from ..data.skins import ALL_SKINS_UNLOCK_MASK, SKIN_BY_EQUIP_ID, Skin
from ..structs.skins import SkinStruct

if TYPE_CHECKING:
    from ...interface_orchestrator.memory.accessor import MemoryAccessor


class SkinState:

    def __init__(self) -> None:
        self._skin: Skin = Skin.DEFAULT

    def set_skin(self, skin: Skin) -> None:
        self._skin = skin

    def set_skin_by_option(self, value: int) -> None:
        self._skin = SKIN_BY_EQUIP_ID.get(value, Skin.DEFAULT)

    def apply(self, accessor: MemoryAccessor) -> None:
        accessor.write_field(SkinStruct, "unlocked", ALL_SKINS_UNLOCK_MASK)
        accessor.write_field(SkinStruct, "equipped", self._skin.equip_id)

    def __repr__(self) -> str:
        return f"SkinState(skin={self._skin.name})"
