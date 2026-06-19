from __future__ import annotations

import struct as _struct

from ..constants import RACSMGADGETKEY, RACSMWEAPONKEY
from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .structs.pickups import GadgetStruct, WeaponStruct

# NOTE: ``..items`` and ``..locations`` are imported lazily (see _ensure_loc_data
# below).  Importing them at module top would create a circular import, because
# ``items.py`` imports this module's weapon constants directly, and
# ``locations.py`` imports ``core.weapons`` siblings + items.py.


# ── Weapon data ──────────────────────────────────────────────────────────────────

WEAPON_STRUCT_SIZE = 0x58
WEAPON_MIN_CONSECUTIVE = 4

WEAPON_MOD_COUNTS: dict[str, int] = {
    RACSMWEAPONKEY.LACERATOR:       2,
    RACSMWEAPONKEY.CONCUSSION_GUN:  3,
    RACSMWEAPONKEY.ACID_BOMB_GLOVE: 2,
    RACSMWEAPONKEY.AGENTS_OF_DOOM:  2,
    RACSMWEAPONKEY.BEE_MINE_GLOVE:  2,
    RACSMWEAPONKEY.STATIC_BARRIER:  2,
    RACSMWEAPONKEY.SHOCK_ROCKET:    3,
    RACSMWEAPONKEY.SNIPER_MINE:     2,
    RACSMWEAPONKEY.SCORCHER:        2,
    RACSMWEAPONKEY.LASER_TRACER:    2,
    RACSMWEAPONKEY.SUCK_CANNON:     0,
    RACSMWEAPONKEY.MOOTATOR:        0,
    RACSMWEAPONKEY.RYNO:            0,
}

WEAPON_MAX_LEVELS: dict[str, int] = {
    RACSMWEAPONKEY.LACERATOR:       4,
    RACSMWEAPONKEY.CONCUSSION_GUN:  4,
    RACSMWEAPONKEY.ACID_BOMB_GLOVE: 4,
    RACSMWEAPONKEY.AGENTS_OF_DOOM:  4,
    RACSMWEAPONKEY.BEE_MINE_GLOVE:  4,
    RACSMWEAPONKEY.STATIC_BARRIER:  4,
    RACSMWEAPONKEY.SHOCK_ROCKET:    4,
    RACSMWEAPONKEY.SNIPER_MINE:     4,
    RACSMWEAPONKEY.SCORCHER:        4,
    RACSMWEAPONKEY.LASER_TRACER:    4,
    RACSMWEAPONKEY.SUCK_CANNON:     4,
    RACSMWEAPONKEY.MOOTATOR:        1,
    RACSMWEAPONKEY.RYNO:            4,
}


def is_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    return True


def is_ps2_weapon_candidate(data: bytes, i: int) -> bool:
    if i + 0x46 > len(data):
        return False
    if data[i + 0x3D] > 1 or data[i + 0x3E] > 1 or data[i + 0x3F] > 1:
        return False
    if data[i + 0x45] > 1:
        return False
    level, = _struct.unpack_from("<I", data, i + 0x2D)
    if level > 7:
        return False
    ammo, = _struct.unpack_from("<I", data, i + 0x31)
    if ammo > 9999:
        return False
    icon, = _struct.unpack_from("<I", data, i + 0x1D)
    if icon == 0:
        return False
    item, = _struct.unpack_from("<I", data, i + 0x15)
    if item == 0:
        return False
    return True


class WeaponAddresses:
    _OFFSETS: dict[str, int] = {
        "level":          0x2D,
        "mod_slot_one":   0x3D,
        "mod_slot_two":   0x3E,
        "mod_slot_three": 0x3F,
        "unlocked":       0x45,
    }

    _BYTE_FIELDS: frozenset[str] = frozenset({"mod_slot_one", "mod_slot_two", "mod_slot_three", "unlocked"})

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"WeaponAddresses(base=0x{self.base:08X})\n{fields}"


class GadgetAddresses:
    _OFFSETS: dict[str, int] = {
        "icon":     0x1D,
        "unlocked": 0x45,
    }

    _BYTE_FIELDS: frozenset[str] = frozenset({"unlocked"})

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in self._OFFSETS.items():
            setattr(self, name, base + offset)

    def fields(self) -> list[str]:
        return list(self._OFFSETS)

    def is_byte(self, field: str) -> bool:
        return field in self._BYTE_FIELDS

    def __repr__(self) -> str:
        fields = "\n".join(
            f"  {name} = 0x{getattr(self, name):08X}"
            for name in self._OFFSETS
        )
        return f"GadgetAddresses(base=0x{self.base:08X})\n{fields}"


WEAPON_ORDER: list[str | None] = [
    RACSMWEAPONKEY.LACERATOR,        # slot  0
    RACSMWEAPONKEY.CONCUSSION_GUN,   # slot  1
    RACSMWEAPONKEY.ACID_BOMB_GLOVE,  # slot  2
    RACSMWEAPONKEY.AGENTS_OF_DOOM,   # slot  3
    RACSMWEAPONKEY.BEE_MINE_GLOVE,   # slot  4
    RACSMWEAPONKEY.STATIC_BARRIER,   # slot  5
    RACSMWEAPONKEY.SHOCK_ROCKET,     # slot  6
    RACSMWEAPONKEY.SNIPER_MINE,      # slot  7
    RACSMWEAPONKEY.SCORCHER,         # slot  8
    RACSMWEAPONKEY.LASER_TRACER,     # slot  9
    RACSMWEAPONKEY.SUCK_CANNON,      # slot 10
    RACSMWEAPONKEY.MOOTATOR,         # slot 11
    None,                            # slot 12  gap
    RACSMWEAPONKEY.RYNO,             # slot 13
]

GADGET_ORDER: list[str | None] = [
    RACSMGADGETKEY.HYPERSHOT,        # slot 0
    RACSMGADGETKEY.SPROUT_O_MATIC,   # slot 1
    RACSMGADGETKEY.POLARIZER,        # slot 2
    RACSMGADGETKEY.PDA,              # slot 3
    RACSMGADGETKEY.SHRINK_RAY,       # slot 4
    RACSMGADGETKEY.BOLT_GRABBER,     # slot 5
    None,                            # slot 6  gap
    RACSMGADGETKEY.MAP_O_MATIC,      # slot 7
    RACSMGADGETKEY.BOX_BREAKER,      # slot 8
]


def build_weapons(array_base: int) -> tuple[dict[str, WeaponAddresses], dict[str, GadgetAddresses]]:
    weapons: dict[str, WeaponAddresses] = {}
    for i, name in enumerate(WEAPON_ORDER):
        if name is not None:
            weapons[name] = WeaponAddresses(array_base + i * WEAPON_STRUCT_SIZE)

    gadget_base = array_base + len(WEAPON_ORDER) * WEAPON_STRUCT_SIZE
    gadgets: dict[str, GadgetAddresses] = {}
    for i, name in enumerate(GADGET_ORDER):
        if name is not None:
            gadgets[name] = GadgetAddresses(gadget_base + i * WEAPON_STRUCT_SIZE)

    return weapons, gadgets


# ── Weapon state (runtime) ───────────────────────────────────────────────────────

_MOD_SLOTS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")

# Location-derived lookups depend on ``items`` and ``locations`` and are built
# lazily on first use to avoid the import cycle described at the top of the file.
_LOC_DATA_LOADED = False
VENDOR_WEAPON_LOC: dict[str, str] = {}
VENDOR_GADGET_LOC: dict[str, str] = {}
WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {}
_MOD_LOC: dict[str, tuple[str, str]] = {}
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {}


def _ensure_loc_data() -> None:
    """Populate the location/item-derived module globals (lazy, idempotent)."""
    global _LOC_DATA_LOADED, VENDOR_WEAPON_LOC, VENDOR_GADGET_LOC
    global WEAPON_INTERNAL_TO_LOCATION, GADGET_INTERNAL_TO_LOCATION
    global _MOD_LOC, MOD_INTERNAL_TO_LOCATION
    if _LOC_DATA_LOADED:
        return
    from ..locations import (
        GADGET_INTERNAL_TO_LOCATION as _GADGET_INTERNAL_TO_LOCATION,
        MOD_INTERNAL_TO_LOCATION as _MOD_INTERNAL_TO_LOCATION,
        VENDOR_GADGET_LOC as _VENDOR_GADGET_LOC,
        VENDOR_WEAPON_LOC as _VENDOR_WEAPON_LOC,
        WEAPON_INTERNAL_TO_LOCATION as _WEAPON_INTERNAL_TO_LOCATION,
    )
    VENDOR_WEAPON_LOC = _VENDOR_WEAPON_LOC
    VENDOR_GADGET_LOC = _VENDOR_GADGET_LOC
    WEAPON_INTERNAL_TO_LOCATION = _WEAPON_INTERNAL_TO_LOCATION
    GADGET_INTERNAL_TO_LOCATION = _GADGET_INTERNAL_TO_LOCATION
    MOD_INTERNAL_TO_LOCATION = _MOD_INTERNAL_TO_LOCATION
    _MOD_LOC = {v: k for k, v in _MOD_INTERNAL_TO_LOCATION.items()}
    _LOC_DATA_LOADED = True


def __getattr__(name: str):
    # Resolve the lazily-built location lookups when imported via
    # ``from core.weapons import <name>`` (e.g. by core._hooks / core.vendor).
    if name in (
        "VENDOR_WEAPON_LOC", "VENDOR_GADGET_LOC",
        "WEAPON_INTERNAL_TO_LOCATION", "GADGET_INTERNAL_TO_LOCATION",
        "MOD_INTERNAL_TO_LOCATION", "_MOD_LOC",
    ):
        _ensure_loc_data()
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class WeaponState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        _ensure_loc_data()
        self.weapons: dict[str, bool]           = {}
        self.gadgets: dict[str, bool]           = {}
        self.mods: dict[str, dict[str, bool]]   = {}
        self.vendor_locations: dict[str, bool]  = dict.fromkeys(
            (*VENDOR_WEAPON_LOC, *VENDOR_GADGET_LOC, *_MOD_LOC), False
        )

    def on_exit(self) -> None:
        self.weapons.clear()
        self.gadgets.clear()
        self.mods.clear()

    def _register_handlers(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                self.accessor.on_struct_change(cls, self._make_weapon_handler(cls.__name__))
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                self.accessor.on_struct_change(cls, self._make_gadget_handler(cls.__name__))

    def _unregister_handlers(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                self.accessor.remove_struct_handler(cls, self._make_weapon_handler(cls.__name__))
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                self.accessor.remove_struct_handler(cls, self._make_gadget_handler(cls.__name__))

    def _make_weapon_handler(self, cls_name: str):
        weapon_name = cls_name.removeprefix("WeaponStruct_")

        def handler(address: int, new_bytes: bytes) -> None:
            del address
            instance     = WeaponStruct.from_bytes(new_bytes)
            was_unlocked = self.weapons.get(weapon_name, False)
            is_unlocked  = bool(instance.unlocked)
            self.weapons[weapon_name] = is_unlocked
            prev_mods = dict(self.mods.get(weapon_name, dict.fromkeys(_MOD_SLOTS, False)))
            self.mods.setdefault(weapon_name, dict.fromkeys(_MOD_SLOTS, False))
            self.mods[weapon_name]["mod_slot_one"]   = bool(instance.mod_slot_one)
            self.mods[weapon_name]["mod_slot_two"]   = bool(instance.mod_slot_two)
            self.mods[weapon_name]["mod_slot_three"] = bool(instance.mod_slot_three)
            if is_unlocked and not was_unlocked:
                self.on_weapon_acquired(weapon_name)
            elif not is_unlocked and was_unlocked:
                self.on_weapon_lost(weapon_name)
            for slot in _MOD_SLOTS:
                is_mod  = self.mods[weapon_name][slot]
                was_mod = prev_mods.get(slot, False)
                if is_mod and not was_mod:
                    self.on_mod_acquired(weapon_name, slot)
                elif not is_mod and was_mod:
                    self.on_mod_lost(weapon_name, slot)
        return handler

    def _make_gadget_handler(self, cls_name: str):
        gadget_name = cls_name.removeprefix("GadgetStruct_")

        def handler(address: int, new_bytes: bytes) -> None:
            del address
            instance     = GadgetStruct.from_bytes(new_bytes)
            was_unlocked = self.gadgets.get(gadget_name, False)
            is_unlocked  = bool(instance.unlocked)
            self.gadgets[gadget_name] = is_unlocked
            if is_unlocked and not was_unlocked:
                self.on_gadget_acquired(gadget_name)
            elif not is_unlocked and was_unlocked:
                self.on_gadget_lost(gadget_name)
        return handler

    def sync(self) -> None:
        self._write_inventory()

    def sync_slots(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                name = cls.__name__.removeprefix("WeaponStruct_")
                raw  = self.accessor.read_raw(cls.BASE_ADDRESS, cls.size())
                inst = WeaponStruct.from_bytes(raw)
                self.weapons[name] = bool(inst.unlocked)
                self.mods.setdefault(name, dict.fromkeys(_MOD_SLOTS, False))
                self.mods[name]["mod_slot_one"]   = bool(inst.mod_slot_one)
                self.mods[name]["mod_slot_two"]   = bool(inst.mod_slot_two)
                self.mods[name]["mod_slot_three"] = bool(inst.mod_slot_three)
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                name = cls.__name__.removeprefix("GadgetStruct_")
                raw  = self.accessor.read_raw(cls.BASE_ADDRESS, cls.size())
                inst = GadgetStruct.from_bytes(raw)
                self.gadgets[name] = bool(inst.unlocked)

    def _write_inventory(self) -> None:
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                name = cls.__name__.removeprefix("WeaponStruct_")
                inst = cls()
                inst.unlocked       = int(self.weapons.get(name, False))
                inst.mod_slot_one   = int(self.mods.get(name, {}).get("mod_slot_one", False))
                inst.mod_slot_two   = int(self.mods.get(name, {}).get("mod_slot_two", False))
                inst.mod_slot_three = int(self.mods.get(name, {}).get("mod_slot_three", False))
                self.accessor.write_raw(cls.BASE_ADDRESS, bytes(inst))
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                name = cls.__name__.removeprefix("GadgetStruct_")
                inst = cls()
                inst.unlocked = int(self.gadgets.get(name, False))
                self.accessor.write_field(cls, "unlocked", inst.unlocked)

    def apply_vendor_locations(self, allowed_extra: frozenset[str] = frozenset()) -> None:
        """Zero all weapon/gadget memory then restore what the player may keep.

        Restored if purchased from vendor (and still owned) OR if name is in
        allowed_extra (owned weapon whose vendor planet is unlocked).
        Mods are always restored when purchased regardless of allowed_extra.
        """
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                self.accessor.write_field(cls, "unlocked", 0)
                self.accessor.write_field(cls, "mod_slot_one", 0)
                self.accessor.write_field(cls, "mod_slot_two", 0)
                self.accessor.write_field(cls, "mod_slot_three", 0)
            elif issubclass(cls, GadgetStruct) and cls is not GadgetStruct:
                self.accessor.write_field(cls, "unlocked", 0)

        for loc_name, purchased in self.vendor_locations.items():
            if not purchased:
                continue
            if loc_name in VENDOR_WEAPON_LOC:
                name = VENDOR_WEAPON_LOC[loc_name]
                # Guard: only restore if player actually owns it (edge-case safety).
                if self.weapons.get(name, False):
                    cls = self.addresses.get(f"WeaponStruct_{name}")
                    if cls:
                        self.accessor.write_field(cls, "unlocked", 1)
            elif loc_name in VENDOR_GADGET_LOC:
                name = VENDOR_GADGET_LOC[loc_name]
                if self.gadgets.get(name, False):
                    cls = self.addresses.get(f"GadgetStruct_{name}")
                    if cls:
                        self.accessor.write_field(cls, "unlocked", 1)
            elif loc_name in _MOD_LOC:
                weapon, slot = _MOD_LOC[loc_name]
                cls = self.addresses.get(f"WeaponStruct_{weapon}")
                if cls:
                    self.accessor.write_field(cls, slot, 1)

        # Restore weapons/gadgets owned via AP items whose vendor planet is unlocked.
        for name in allowed_extra:
            cls = self.addresses.get(f"WeaponStruct_{name}")
            if cls:
                self.accessor.write_field(cls, "unlocked", 1)
            cls = self.addresses.get(f"GadgetStruct_{name}")
            if cls:
                self.accessor.write_field(cls, "unlocked", 1)

    def apply_mod_vendor_locations(self) -> None:
        """Zero all mod slots then restore only purchased mods."""
        for cls in self.addresses.structs():
            if issubclass(cls, WeaponStruct) and cls is not WeaponStruct:
                self.accessor.write_field(cls, "mod_slot_one",   0)
                self.accessor.write_field(cls, "mod_slot_two",   0)
                self.accessor.write_field(cls, "mod_slot_three", 0)

        for loc_name, purchased in self.vendor_locations.items():
            if not purchased or loc_name not in _MOD_LOC:
                continue
            weapon, slot = _MOD_LOC[loc_name]
            cls = self.addresses.get(f"WeaponStruct_{weapon}")
            if cls:
                self.accessor.write_field(cls, slot, 1)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        for loc in checked_locations:
            if loc in self.vendor_locations:
                self.vendor_locations[loc] = True
            if loc in VENDOR_WEAPON_LOC:
                self.weapons[VENDOR_WEAPON_LOC[loc]] = True
            elif loc in VENDOR_GADGET_LOC:
                self.gadgets[VENDOR_GADGET_LOC[loc]] = True
            elif loc in _MOD_LOC:
                weapon, slot = _MOD_LOC[loc]
                self.mods.setdefault(weapon, dict.fromkeys(_MOD_SLOTS, False))
                self.mods[weapon][slot] = True

    def has_weapon(self, name: str) -> bool:
        return self.weapons.get(name, False)

    def has_gadget(self, name: str) -> bool:
        return self.gadgets.get(name, False)

    def has_mod(self, weapon: str, slot: str) -> bool:
        return self.mods.get(weapon, {}).get(slot, False)

    def on_weapon_acquired(self, _name: str) -> None:
        del _name

    def on_weapon_lost(self, _name: str) -> None:
        del _name

    def on_gadget_acquired(self, _name: str) -> None:
        del _name

    def on_gadget_lost(self, _name: str) -> None:
        del _name

    def on_mod_acquired(self, _weapon: str, _slot: str) -> None:
        del _weapon, _slot

    def on_mod_lost(self, _weapon: str, _slot: str) -> None:
        del _weapon, _slot

    def __repr__(self) -> str:
        unlocked_w = [n for n, v in self.weapons.items() if v]
        unlocked_g = [n for n, v in self.gadgets.items() if v]
        return f"WeaponState(weapons={unlocked_w}, gadgets={unlocked_g})"
