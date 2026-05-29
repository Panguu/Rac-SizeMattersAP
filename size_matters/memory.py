from __future__ import annotations

from typing import Callable, Iterable

from .armour import ArmourPiece, ArmourAddresses
from .pickups import TitaniumBoltAddresses
from .weapons import WeaponAddresses, GadgetAddresses, is_ps2_weapon_candidate, WEAPON_STRUCT_SIZE, WEAPON_MIN_CONSECUTIVE
from .data.addresses import ARMOUR_BASE, TITANIUM_BOLT_BASE
from .data.weapons import build_weapons
from .state import GameState
from ..pypine.pypine.pine import Pine

# ---------------------------------------------------------------------------
# Memory state snapshot
# ---------------------------------------------------------------------------

class MemoryState:
    """Snapshot, clear, and restore a group of int8 memory addresses.

    Accepts a callable so addresses are evaluated lazily — useful when the
    underlying dict (e.g. WEAPONS) is populated after import time.
    """

    def __init__(self, get_addresses: Callable[[], Iterable[int]]) -> None:
        self._get_addresses = get_addresses
        self._saved: dict[int, int] = {}

    def save(self, ipc: Pine) -> None:
        self._saved = {addr: ipc.read_int8(addr) for addr in self._get_addresses()}

    def remove(self, ipc: Pine) -> None:
        for addr in self._get_addresses():
            ipc.write_int8(addr, 0)

    def take(self, ipc: Pine) -> None:
        addrs = list(self._get_addresses())
        self._saved = {addr: ipc.read_int8(addr) for addr in addrs}
        for addr in addrs:
            ipc.write_int8(addr, 0)

    def restore(self, ipc: Pine) -> None:
        if not self._saved:
            raise RuntimeError("restore() called before save()")
        for addr, val in self._saved.items():
            ipc.write_int8(addr, val)


# ---------------------------------------------------------------------------
# Item scanner
# ---------------------------------------------------------------------------

class ItemScanner:
    """Detects items written by the game into memory during a pickup window.

    Addresses are evaluated lazily so the scanner works even when the
    underlying dicts (e.g. WEAPONS) are populated after import time.

    Typical usage:
        scanner.clear(ipc)   # on pickup_start: zero addresses for detection
        scanner.scan(ipc)    # on pickup_end:   read and fire on_detected
        scanner.clear(ipc)   # on pickup_end:   zero again before state restore
    """

    def __init__(
        self,
        get_items: Callable[[], dict[str, int]],
        on_detected: Callable[[str, int], None],
    ) -> None:
        self._get_items  = get_items
        self._on_detected = on_detected

    def clear(self, ipc: Pine) -> None:
        for addr in self._get_items().values():
            ipc.write_int8(addr, 0)

    def scan(self, ipc: Pine) -> None:
        for name, addr in self._get_items().items():
            val = ipc.read_int8(addr)
            if val:
                self._on_detected(name, val)


# ---------------------------------------------------------------------------
# Module-level globals (populated by sync_weapons)
# ---------------------------------------------------------------------------

WEAPONS: dict[str, WeaponAddresses] = {}
GADGETS: dict[str, GadgetAddresses] = {}

_armour             = ArmourAddresses(ARMOUR_BASE)
ARMOUR_ADDRESSES:    dict[str, int] = _armour.sets
PLAYER_ARMOUR_SLOTS: dict[str, int] = _armour.slots

BOLTS = TitaniumBoltAddresses(TITANIUM_BOLT_BASE)

# Piece order and slot mapping — index within this list is the piece_index used
# when computing slot values (slot_value = set_index * 4 + piece_index + 1).
_ARMOUR_PIECES = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]
_PIECE_TO_SLOTS: dict[ArmourPiece, list[str]] = {
    ArmourPiece.CHESTPLATE: ["chestplate"],
    ArmourPiece.HELMET:     ["helmet"],
    ArmourPiece.GLOVES:     ["gloves_left", "gloves_right"],
    ArmourPiece.BOOTS:      ["boots_left", "boots_right"],
}
# Set order must match _SET_OFFSETS in ArmourAddresses — index is set_index.
_ARMOUR_SET_ORDER = ["wildfire", "sludge", "crystallix", "electroshock", "mega_bomb", "hyperborean", "chameleon"]

# ---------------------------------------------------------------------------
# Weapon scan
# ---------------------------------------------------------------------------

def sync_weapons(ipc: Pine) -> None:
    SCAN_START  = 0x20F00000
    SCAN_LENGTH = 0x100000

    data  = ipc.read_bytes(SCAN_START, SCAN_LENGTH)
    limit = SCAN_LENGTH - WEAPON_STRUCT_SIZE * WEAPON_MIN_CONSECUTIVE
    for i in range(limit):
        if (SCAN_START + i) % 4 != 3:
            continue
        if not is_ps2_weapon_candidate(data, i):
            continue
        count = 1
        while count < WEAPON_MIN_CONSECUTIVE and is_ps2_weapon_candidate(data, i + count * WEAPON_STRUCT_SIZE):
            count += 1
        if count >= WEAPON_MIN_CONSECUTIVE:
            array_base = SCAN_START + i
            weapons, gadgets = build_weapons(array_base)
            WEAPONS.update(weapons)
            GADGETS.update(gadgets)
            print(f"Weapon array at 0x{array_base:08X}")
            return
    print("Weapon scan: no consecutive structs found.")

# ---------------------------------------------------------------------------
# Memory write helpers
# ---------------------------------------------------------------------------

def zero_weapon(ipc: Pine, w: WeaponAddresses) -> None:
    ipc.write_int8(w.unlocked, 0)
    ipc.write_int8(w.mod_slot_one, 0)
    ipc.write_int8(w.mod_slot_two, 0)
    ipc.write_int8(w.mod_slot_three, 0)
    ipc.write_int32(w.level, 0)
    ipc.write_int32(w.experience, 0)


def apply_tracked_armour(gs: GameState) -> None:
    for name, val in gs.tracked_armour.items():
        gs.ipc.write_int8(ARMOUR_ADDRESSES[name], val)


def apply_slots_from_armour(gs: GameState) -> None:
    slot_vals: dict[str, int] = {slot: 0 for slot in PLAYER_ARMOUR_SLOTS}
    for set_idx, set_name in enumerate(_ARMOUR_SET_ORDER):
        val = gs.tracked_armour.get(set_name, 0)
        if not val:
            continue
        for piece_idx, piece in enumerate(_ARMOUR_PIECES):
            if piece in ArmourPiece(val):
                slot_value = set_idx * 4 + piece_idx + 1
                for slot in _PIECE_TO_SLOTS[piece]:
                    slot_vals[slot] = slot_value
    for slot, v in slot_vals.items():
        gs.ipc.write_int8(PLAYER_ARMOUR_SLOTS[slot], v)


def apply_tracked_weapons(gs: GameState) -> None:
    for name, val in gs.tracked_weapons.items():
        if name in WEAPONS:
            gs.ipc.write_int8(WEAPONS[name].unlocked, val)
    for name, val in gs.tracked_gadgets.items():
        if name in GADGETS:
            gs.ipc.write_int8(GADGETS[name].unlocked, val)


def restore_tracked_weapon_state(gs: GameState) -> None:
    for w in WEAPONS.values():
        zero_weapon(gs.ipc, w)
    for g in GADGETS.values():
        gs.ipc.write_int8(g.unlocked, 0)
    for name, val in gs.tracked_weapons.items():
        if name in WEAPONS:
            gs.ipc.write_int8(WEAPONS[name].unlocked, val)
    for name, slots in gs.tracked_mods.items():
        if name in WEAPONS:
            for slot in slots:
                gs.ipc.write_int8(getattr(WEAPONS[name], f"mod_slot_{slot}"), 1)
    for name, val in gs.tracked_gadgets.items():
        if name in GADGETS:
            gs.ipc.write_int8(GADGETS[name].unlocked, val)
