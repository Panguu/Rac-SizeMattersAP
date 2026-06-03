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
        self.equipped: dict[str, ArmourPiece]  = dict.fromkeys(ArmourStruct.SLOT_FIELDS, ArmourPiece.NONE)
        self.sets_unlocked: dict[str, bool]    = dict.fromkeys(ArmourStruct.SET_FIELDS, False)
        self.sets_bitmask: dict[str, int]      = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)
        self.location_collected_armour: dict[str, int] = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)
        self.item_pickup_armour: dict[str, int]        = dict.fromkeys(ArmourStruct.SET_FIELDS, 0)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(ArmourStruct, self._on_armour_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(ArmourStruct, self._on_armour_change)

    def _on_armour_change(self, _address: int, new_bytes: bytes) -> None:
        instance = ArmourStruct.from_bytes(new_bytes)
        for name in ArmourStruct.SLOT_FIELDS:
            raw = getattr(instance, name)
            self.equipped[name] = ArmourPiece._value2member_map_.get(raw, ArmourPiece.NONE)
        for name in ArmourStruct.SET_FIELDS:
            raw = getattr(instance, name)
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)

    def sync(self) -> None:
        instance = self.accessor.read_struct(ArmourStruct)
        for name in ArmourStruct.SLOT_FIELDS:
            raw = getattr(instance, name)
            self.equipped[name] = ArmourPiece._value2member_map_.get(raw, ArmourPiece.NONE)
        for name in ArmourStruct.SET_FIELDS:
            raw = getattr(instance, name)
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)

    def sync_slots(self) -> None:
        raw = self.accessor.read_raw(ArmourStruct.BASE_ADDRESS, len(ArmourStruct.SLOT_FIELDS))
        for i, name in enumerate(ArmourStruct.SLOT_FIELDS):
            self.equipped[name] = ArmourPiece._value2member_map_.get(raw[i], ArmourPiece.NONE)

    def apply_location_armour(self) -> None:
        data = bytearray(ArmourStruct.size())
        for name in ArmourStruct.SET_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self.location_collected_armour.get(name, 0)
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(data))

    def apply_item_pickup_armour(self) -> None:
        data = bytearray(ArmourStruct.size())
        for name in ArmourStruct.SLOT_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = int(self.equipped[name])
        for name in ArmourStruct.SET_FIELDS:
            offset = ArmourStruct.field_offset(name)
            data[offset] = self.item_pickup_armour.get(name, 0)
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(data))

    def clear_all_memory(self) -> None:
        self.accessor.write_raw(ArmourStruct.BASE_ADDRESS, bytes(ArmourStruct.size()))

    def add_location_piece(self, set_name: str, piece: ArmourPiece) -> None:
        if set_name in self.location_collected_armour:
            self.location_collected_armour[set_name] |= int(piece)

    def add_item_pickup_piece(self, set_name: str, piece: ArmourPiece) -> None:
        if set_name in self.item_pickup_armour:
            self.item_pickup_armour[set_name] |= int(piece)

    def sync_from_ap(
        self,
        armour_locations: set[str],
        armour_item_pickups: set[tuple[str, ArmourPiece]],
    ) -> None:
        for key in ArmourStruct.SET_FIELDS:
            self.location_collected_armour[key] = 0
            self.item_pickup_armour[key] = 0
        for loc_name in armour_locations:
            flag = CHALLENGE_LOCATION_TO_ARMOUR_FLAG.get(loc_name)
            if flag:
                set_key, piece = flag
                self.location_collected_armour[set_key] |= int(piece)
        for flag in armour_item_pickups:
            if ARMOUR_FLAG_TO_LOCATION.get(flag):
                set_key, piece = flag
                self.item_pickup_armour[set_key] |= int(piece)

    def __repr__(self) -> str:
        unlocked = [n for n, v in self.sets_unlocked.items() if v]
        return f"ArmourState(sets_unlocked={unlocked}, equipped={self.equipped})"
