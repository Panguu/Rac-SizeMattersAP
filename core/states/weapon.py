from __future__ import annotations

from collections import defaultdict

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ...items import WEAPON_DISPLAY_TO_INTERNAL
from ...locations import (
    VENDOR_WEAPON_LOC,
    VENDOR_GADGET_LOC,
    VENDOR_WEAPON_MOD_PLANET,
    WEAPON_INTERNAL_TO_LOCATION,
    GADGET_INTERNAL_TO_LOCATION,
)
from ..structs.weapon import GadgetStruct, WeaponStruct

_MOD_SLOTS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")

_by_weapon: dict[str, list[str | None]] = defaultdict(list)
for _wd, _mn in VENDOR_WEAPON_MOD_PLANET:
    _by_weapon[_wd].append(_mn)

_MOD_LOC: dict[str, tuple[str, str]] = {}
for _wd, _mns in _by_weapon.items():
    _int = WEAPON_DISPLAY_TO_INTERNAL.get(_wd)
    if _int:
        for _i, _mn in enumerate(_mns):
            if _i < len(_MOD_SLOTS) and _mn is not None:
                _MOD_LOC[f"Purchase {_wd} {_mn}"] = (_int, _MOD_SLOTS[_i])

MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {v: k for k, v in _MOD_LOC.items()}

class WeaponState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
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
