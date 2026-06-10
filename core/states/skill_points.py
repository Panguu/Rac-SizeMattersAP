from __future__ import annotations

from CommonClient import logger

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.locations.skill_points import (
    CHALLENGE_SKILL_POINTS,
    LOCATION_SKILL_POINTS,
    SKILL_POINT_ADDRESS,
    SKILL_POINT_BY_PLANET_AND_MASK,
    SKILL_POINTS,
    SkillPoint,
)
from ..structs.skill_points import SkillPointsStruct

__all__ = [
    "SkillPoint",
    "SKILL_POINTS",
    "CHALLENGE_SKILL_POINTS",
    "SKILL_POINT_BY_PLANET_AND_MASK",
    "LOCATION_SKILL_POINTS",
    "SKILL_POINT_ADDRESS",
    "SkillPointState",
]


class SkillPointState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._bits:          int  = 0
        self._synced_mask:   int  = 0
        self._planet_loaded: bool = False
        self._enabled:       bool = False

    def set_enabled(self, enabled: bool, planet_loaded: bool = False) -> None:
        was_enabled = self._enabled
        self._enabled = enabled
        if enabled:
            # Always remove then re-add to avoid duplicates on reconnect.
            self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)
            self.accessor.on_struct_change(SkillPointsStruct, self._on_struct_change)
            self._read_bits()
            if planet_loaded:
                self._planet_loaded = True
        elif was_enabled:
            self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)

    def mark_planet_loaded(self) -> None:
        self._planet_loaded = True

    def _register_handlers(self) -> None:
        # Re-register after interface swap if already enabled.
        if self._enabled:
            self.accessor.on_struct_change(SkillPointsStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        instance  = SkillPointsStruct.from_bytes(new_bytes)
        current   = instance.bitmask
        newly_set = current & ~self._bits
        prev      = self._bits
        self._bits = current
        if not self._planet_loaded:
            return
        if newly_set:
            logger.info(
                f"[RAC] Skill point bits: {prev:#010x} -> {current:#010x}  (earned: {newly_set:#010x})"
            )
            for name, sp in SKILL_POINTS.items():
                if newly_set & sp.mask:
                    logger.info(f"[RAC] Skill point earned: {name}")
                    self.on_skill_point_earned(name)

    def _read_bits(self) -> None:
        try:
            instance = self.accessor.read_struct(SkillPointsStruct)
            self._bits = instance.bitmask
        except Exception:
            pass

    def sync(self) -> None:
        if not self._enabled:
            return
        instance = self.accessor.read_struct(SkillPointsStruct)
        self._bits = instance.bitmask
        self.mark_planet_loaded()
        new_val = instance.bitmask | self._synced_mask
        if new_val != instance.bitmask:
            instance.bitmask = new_val
            self.accessor.write_struct(instance)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        mask = 0
        for name, sp in SKILL_POINTS.items():
            if name in checked_locations:
                mask |= sp.mask
        self._synced_mask = mask

    def on_skill_point_earned(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        earned = bin(self._bits).count("1")
        return f"SkillPointState(earned={earned}/{len(SKILL_POINTS)})"
