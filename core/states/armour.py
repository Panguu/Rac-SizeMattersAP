from collections.abc import Callable

from worlds.rac_size_matters.core.data.armour import ArmourAddresses, ArmourPiece
from worlds.rac_size_matters.core.data.armour_pickups import (
    ARMOUR_FLAG_TO_LOCATION,
    CHALLENGE_LOCATION_TO_ARMOUR_FLAG,
)
from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

_TOTAL_BYTES = 0x0D  # slots (0x00-0x05) + sets (0x06-0x0C)


class ArmourState(State):
    """
    Global armour state. Read from memory to snapshot current equipped pieces
    and unlocked sets. Write back via apply() to push changes to memory.

    equipped      — current ArmourPiece in each slot (chestplate, helmet, etc.)
    sets_unlocked — whether each armour set is unlocked (wildfire, sludge, etc.)
    """

    def __init__(self, pine: Pine, base: int):
        super().__init__(pine)
        self._addrs = ArmourAddresses(base)
        self.equipped: dict[str, ArmourPiece] = dict.fromkeys(self._addrs.slots, ArmourPiece.NONE)
        self.sets_unlocked: dict[str, bool] = dict.fromkeys(self._addrs.sets, False)
        self.sets_bitmask: dict[str, int] = dict.fromkeys(self._addrs.sets, 0)
        self.location_collected_armour: dict[str, int] = dict.fromkeys(self._addrs.sets, 0)
        self.item_pickup_armour: dict[str, int] = dict.fromkeys(self._addrs.sets, 0)

    async def read(self) -> bool:
        async with self._lock:
            data = self.pine.read_bytes(self._addrs.base, _TOTAL_BYTES)
        for name, offset in self._addrs._SLOT_OFFSETS.items():
            self.equipped[name] = ArmourPiece._value2member_map_.get(data[offset], ArmourPiece.NONE)
        for name, offset in self._addrs._SET_OFFSETS.items():
            raw = data[offset]
            self.sets_bitmask[name]  = raw
            self.sets_unlocked[name] = bool(raw)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, interval, callback

    async def apply(self) -> bool:
        return True

    async def read_armour_slots(self) -> None:
        async with self._lock:
            data = self.pine.read_bytes(self._addrs.base, _TOTAL_BYTES)
        for name, offset in self._addrs._SLOT_OFFSETS.items():
            self.equipped[name] = ArmourPiece._value2member_map_.get(data[offset], ArmourPiece.NONE)
    # Armour Management
    async def apply_location_armour(self) -> bool:
        data = bytearray(_TOTAL_BYTES)
        for name, offset in self._addrs._SET_OFFSETS.items():
            data[offset] = self.location_collected_armour.get(name, 0)
        async with self._lock:
            self.pine.write_bytes(self._addrs.base, bytes(data))
        return True

    async def apply_item_pickup_armour(self) -> bool:
        data = bytearray(_TOTAL_BYTES)
        for name, offset in self._addrs._SLOT_OFFSETS.items():
            data[offset] = int(self.equipped[name])
        for name, offset in self._addrs._SET_OFFSETS.items():
            data[offset] = self.item_pickup_armour.get(name, 0)
        async with self._lock:
            self.pine.write_bytes(self._addrs.base, bytes(data))
        return True

    def add_location_piece(self, set_name: str, piece: ArmourPiece) -> None:
        """Record a physically picked-up armour piece for this session."""
        if set_name in self.location_collected_armour:
            self.location_collected_armour[set_name] |= int(piece)

    def add_item_pickup_piece(self, set_name: str, piece: ArmourPiece) -> None:
        """Record an armour piece granted from an AP item pickup for this session."""
        if set_name in self.item_pickup_armour:
            self.item_pickup_armour[set_name] |= int(piece)


    async def clear_all_memory(self) -> None:
        """Zero all armour bytes (slots + sets). Used at pickup start so the game
        writes only the new piece, making detection unambiguous."""
        async with self._lock:
            self.pine.write_bytes(self._addrs.base, bytes(_TOTAL_BYTES))

    def sync_from_ap(self, armour_locations: set[str], armour_item_pickups: set[tuple[str, ArmourPiece]]) -> None:
        """Populate location_collected_armour from challenge reward locations and
        item_pickup_armour from world pickup flags."""
        for key in self._addrs._SET_OFFSETS:
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

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArmourState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        unlocked = [n for n, v in self.sets_unlocked.items() if v]
        return f"ArmourState(sets_unlocked={unlocked}, equipped={self.equipped})"
