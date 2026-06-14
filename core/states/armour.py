from __future__ import annotations

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.armour import ArmourPiece
from ..data.locations.armour_pickups import (
    ARMOUR_FLAG_TO_LOCATION,
    CHALLENGE_LOCATION_TO_ARMOUR_FLAG,
)
from ..structs.armour import ArmourStruct


class ArmourState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        # Slot bytes store set indices (1-7), not ArmourPiece bitmask values — keep as int.
        self.equipped: dict[str, int]  = dict.fromkeys(ArmourStruct.SLOT_FIELDS, 0)
        # Stable snapshot — only updated by freeze_slots()/sync_slots()/sync().
        self._stable_slots: dict[str, int] = dict.fromkeys(ArmourStruct.SLOT_FIELDS, 0)
        self.sets_unlocked: dict[str, bool]    = dict.fromkeys(ArmourStruct.SET_FIELDS, False)
        self.sets_bitmask: dict[str, int]      = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)
        self.world_collected_armour: dict[str, int] = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)
        self.ap_armour: dict[str, int]                 = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(ArmourStruct, self._on_armour_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ArmourStruct, self._on_armour_change)

    def _on_armour_change(self, _address: int, new_bytes: bytes) -> None:
        instance = ArmourStruct.from_bytes(new_bytes)
        for name in ArmourStruct.SLOT_FIELDS:
            self.equipped[name] = getattr(instance, name)
        for name in ArmourStruct.SET_FIELDS:
            raw = getattr(instance, name)
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)

    def sync(self) -> None:
        instance = self.accessor.read_struct(ArmourStruct)
        for name in ArmourStruct.SLOT_FIELDS:
            raw = getattr(instance, name)
            self.equipped[name]      = raw
            self._stable_slots[name] = raw
        for name in ArmourStruct.SET_FIELDS:
            raw = getattr(instance, name)
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)

    def sync_bitmasks(self) -> None:
        """Read only the set bitmasks from memory without touching _stable_slots.

        Used in on_pickup_end so that the slot snapshot taken at pickup_start is
        preserved for restore_equipped_slots() after the detection window closes.
        """
        instance = self.accessor.read_struct(ArmourStruct)
        for name in ArmourStruct.SET_FIELDS:
            raw = getattr(instance, name)
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)

    def sync_slots(self) -> None:
        raw = self.accessor.read_raw(ArmourStruct.BASE_ADDRESS, len(ArmourStruct.SLOT_FIELDS))
        for i, name in enumerate(ArmourStruct.SLOT_FIELDS):
            self.equipped[name]      = raw[i]
            self._stable_slots[name] = raw[i]

    def freeze_slots(self) -> None:
        """Snapshot equipped into _stable_slots from the live dict, not from memory.

        Called on death so we capture the last known good state before the game
        clears armour memory as part of its death sequence.
        """
        for name in ArmourStruct.SLOT_FIELDS:
            self._stable_slots[name] = self.equipped[name]

    def restore_equipped_slots(self) -> None:
        """Write the stable slot snapshot back to memory without touching the set bytes."""
        slot_bytes = bytes(self._stable_slots[name] for name in ArmourStruct.SLOT_FIELDS)
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, slot_bytes)

    def apply_world_armour(self) -> None:
        data = bytearray(ArmourStruct.size())
        for name in ArmourStruct.SLOT_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self._stable_slots[name]
        for name in ArmourStruct.SET_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self.world_collected_armour.get(name, 0)
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(data))

    def apply_ap_armour(self) -> None:
        data = bytearray(ArmourStruct.size())
        for name in ArmourStruct.SLOT_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self._stable_slots[name]
        for name in ArmourStruct.SET_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self.ap_armour.get(name, 0)
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(data))

    def clear_all_memory(self) -> None:
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(ArmourStruct.size()))

    def add_world_armour_piece(self, set_name: str, piece: ArmourPiece) -> None:
        if set_name in self.world_collected_armour:
            self.world_collected_armour[set_name] |= int(piece)

    def add_ap_armour_piece(self, set_name: str, piece: ArmourPiece) -> None:
        if set_name in self.ap_armour:
            self.ap_armour[set_name] |= int(piece)

    def sync_from_ap(
        self,
        checked_locations: set[str],
        armour_item_pickups: set[tuple[str, ArmourPiece]] = frozenset(),
    ) -> None:
        _loc_to_flag: dict[str, tuple[str, ArmourPiece]] = {
            v: k for k, v in ARMOUR_FLAG_TO_LOCATION.items()
        }
        for key in ArmourStruct.SET_FIELDS:
            self.world_collected_armour[key] = 0
            self.ap_armour[key] = 0
        for loc_name in checked_locations:
            flag = _loc_to_flag.get(loc_name) or CHALLENGE_LOCATION_TO_ARMOUR_FLAG.get(loc_name)
            if flag:
                set_key, piece = flag
                self.world_collected_armour[set_key] |= int(piece)
        for flag in armour_item_pickups:
            if ARMOUR_FLAG_TO_LOCATION.get(flag):
                set_key, piece = flag
                self.ap_armour[set_key] |= int(piece)

    def __repr__(self) -> str:
        unlocked  = [n for n, v in self.sets_unlocked.items() if v]
        slots = {k: v for k, v in self.equipped.items() if v}
        return f"ArmourState(sets_unlocked={unlocked}, equipped_slots={slots})"
