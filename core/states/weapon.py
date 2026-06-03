import asyncio
from collections import defaultdict
from collections.abc import Callable

from worlds.rac_size_matters.core.data.weapons import (
    GadgetAddresses,
    WeaponAddresses,
    build_weapons,
)
from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.items import (
    GADGET_DISPLAY_TO_INTERNAL,
    WEAPON_DISPLAY_TO_INTERNAL,
)
from worlds.rac_size_matters.locations import (
    VENDOR_GADGET_PLANET,
    VENDOR_WEAPON_MOD_PLANET,
    VENDOR_WEAPON_PLANET,
)
from worlds.rac_size_matters.pypine.pypine.pine import Pine

_MOD_SLOTS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")
_SLOT_INDEX = {f"mod_slot_{n}": n for n in ("one", "two", "three")}

# AP location name → internal name / (weapon, slot) lookups built once at import
_WEAPON_LOC: dict[str, str] = {
    f"Purchase {display}": WEAPON_DISPLAY_TO_INTERNAL[display]
    for display in VENDOR_WEAPON_PLANET
    if display in WEAPON_DISPLAY_TO_INTERNAL
}

_GADGET_LOC: dict[str, str] = {
    f"Purchase {display}": GADGET_DISPLAY_TO_INTERNAL[display]
    for display in VENDOR_GADGET_PLANET
    if display in GADGET_DISPLAY_TO_INTERNAL
}

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


WEAPON_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in _WEAPON_LOC.items()}
GADGET_INTERNAL_TO_LOCATION: dict[str, str] = {v: k for k, v in _GADGET_LOC.items()}
MOD_INTERNAL_TO_LOCATION: dict[tuple[str, str], str] = {v: k for k, v in _MOD_LOC.items()}


class WeaponState(State):
    """
    Global weapon, gadget, and mod inventory tracker. Polls planet-specific
    weapon array addresses to detect when items are acquired or lost.

    Activated per-planet by PlanetState.on_enter() with that planet's array_base.
    apply() writes the full current state back to memory (called on menu preload).
    Override on_* hooks to react to inventory changes.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.weapons: dict[str, bool]                   = {}
        self.gadgets: dict[str, bool]                   = {}
        self.mods: dict[str, dict[str, bool]]           = {}
        self.vendor_locations: dict[str, bool]          = dict.fromkeys((*_WEAPON_LOC, *_GADGET_LOC, *_MOD_LOC), False)
        self._weapon_addrs: dict[str, WeaponAddresses] | None = None
        self._gadget_addrs: dict[str, GadgetAddresses] | None = None
        self._task: asyncio.Task | None                 = None

    # --- State interface ---

    async def read(self) -> bool:
        if self._weapon_addrs is None:
            return False
        async with self._lock:
            for name, addrs in self._weapon_addrs.items():
                self.weapons[name] = bool(self.pine.read_int8(addrs.unlocked))
                self.mods[name] = {
                    slot: bool(self.pine.read_int8(getattr(addrs, slot)))
                    for slot in _MOD_SLOTS
                }
            for name, addrs in self._gadget_addrs.items():
                self.gadgets[name] = bool(self.pine.read_int8(addrs.unlocked))
        return True

    async def apply(self) -> bool:
        if self._weapon_addrs is None:
            return False
        async with self._lock:
            for name, addrs in self._weapon_addrs.items():
                self.pine.write_int8(addrs.unlocked, int(self.weapons.get(name, False)))
                for slot in _MOD_SLOTS:
                    self.pine.write_int8(
                        getattr(addrs, slot),
                        int(self.mods.get(name, {}).get(slot, False)),
                    )
            for name, addrs in self._gadget_addrs.items():
                self.pine.write_int8(addrs.unlocked, int(self.gadgets.get(name, False)))
        return True

    async def apply_vendor_locations(self) -> bool:
        """Zero all weapon/gadget/mod unlocks then write only vendor-purchased ones."""
        if self._weapon_addrs is None:
            return False
        async with self._lock:
            for addrs in self._weapon_addrs.values():
                self.pine.write_int8(addrs.unlocked, 0)
                for slot in _MOD_SLOTS:
                    self.pine.write_int8(getattr(addrs, slot), 0)
            for addrs in self._gadget_addrs.values():
                self.pine.write_int8(addrs.unlocked, 0)
            for loc_name, purchased in self.vendor_locations.items():
                if not purchased:
                    continue
                if loc_name in _WEAPON_LOC:
                    name = _WEAPON_LOC[loc_name]
                    if name in self._weapon_addrs:
                        self.pine.write_int8(self._weapon_addrs[name].unlocked, 1)
                elif loc_name in _GADGET_LOC:
                    name = _GADGET_LOC[loc_name]
                    if name in self._gadget_addrs:
                        self.pine.write_int8(self._gadget_addrs[name].unlocked, 1)
                elif loc_name in _MOD_LOC:
                    weapon, slot = _MOD_LOC[loc_name]
                    if weapon in self._weapon_addrs:
                        self.pine.write_int8(getattr(self._weapon_addrs[weapon], slot), 1)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        while True:
            prev_weapons = dict(self.weapons)
            prev_gadgets = dict(self.gadgets)
            prev_mods    = {n: dict(s) for n, s in self.mods.items()}
            await self.read()
            self._detect_changes(prev_weapons, self.weapons, self.on_weapon_acquired, self.on_weapon_lost)
            self._detect_changes(prev_gadgets, self.gadgets, self.on_gadget_acquired, self.on_gadget_lost)
            for name, slots in self.mods.items():
                for slot, unlocked in slots.items():
                    was = prev_mods.get(name, {}).get(slot, False)
                    if unlocked and not was:
                        self.on_mod_acquired(name, slot)
                    elif not unlocked and was:
                        self.on_mod_lost(name, slot)
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(
        self,
        array_base: int,
        interval: int,
        callback: Callable[[int, int], None],
    ) -> None:
        """Start polling. Called from PlanetState.on_enter()."""
        if self._task is not None:
            return
        self._weapon_addrs, self._gadget_addrs = build_weapons(array_base)
        # Initialise key sets so sync_from_ap and apply() work before the first read()
        self.weapons = dict.fromkeys(self._weapon_addrs, False)
        self.gadgets = dict.fromkeys(self._gadget_addrs, False)
        self.mods    = {name: dict.fromkeys(_MOD_SLOTS, False) for name in self._weapon_addrs}
        self._task = asyncio.create_task(self.poll(0, interval, callback))

    async def deactivate(self) -> None:
        """Stop polling. Called from PlanetState.on_exit()."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._weapon_addrs = None
        self._gadget_addrs = None

    # --- AP sync ---

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Pre-populate weapons, gadgets, mods, and vendor_locations from AP-confirmed locations."""
        for loc in checked_locations:
            if loc in self.vendor_locations:
                self.vendor_locations[loc] = True
            if loc in _WEAPON_LOC:
                name = _WEAPON_LOC[loc]
                if name in self.weapons:
                    self.weapons[name] = True
            elif loc in _GADGET_LOC:
                name = _GADGET_LOC[loc]
                if name in self.gadgets:
                    self.gadgets[name] = True
            elif loc in _MOD_LOC:
                weapon, slot = _MOD_LOC[loc]
                if weapon in self.mods and slot in self.mods[weapon]:
                    self.mods[weapon][slot] = True

    # --- Change detection ---

    @staticmethod
    def _detect_changes(
        prev: dict[str, bool],
        current: dict[str, bool],
        on_acquired: Callable[[str], None],
        on_lost: Callable[[str], None],
    ) -> None:
        for name, unlocked in current.items():
            was_unlocked = prev.get(name, False)
            if unlocked and not was_unlocked:
                on_acquired(name)
            elif not unlocked and was_unlocked:
                on_lost(name)

    # --- Properties ---

    def has_weapon(self, name: str) -> bool:
        return self.weapons.get(name, False)

    def has_gadget(self, name: str) -> bool:
        return self.gadgets.get(name, False)

    def has_mod(self, weapon: str, slot: str) -> bool:
        return self.mods.get(weapon, {}).get(slot, False)

    # --- Hooks (override per use case) ---

    def on_weapon_acquired(self, _name: str) -> None:
        """Fired when a weapon is newly unlocked."""
        del _name

    def on_weapon_lost(self, _name: str) -> None:
        """Fired when a weapon is removed from inventory."""
        del _name

    def on_gadget_acquired(self, _name: str) -> None:
        """Fired when a gadget is newly unlocked."""
        del _name

    def on_gadget_lost(self, _name: str) -> None:
        """Fired when a gadget is removed from inventory."""
        del _name

    def on_mod_acquired(self, _weapon: str, _slot: str) -> None:
        """Fired when a weapon mod slot is newly unlocked."""
        del _weapon, _slot

    def on_mod_lost(self, _weapon: str, _slot: str) -> None:
        """Fired when a weapon mod slot is removed."""
        del _weapon, _slot

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WeaponState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        unlocked_w = [n for n, v in self.weapons.items() if v]
        unlocked_g = [n for n, v in self.gadgets.items() if v]
        return f"WeaponState(weapons={unlocked_w}, gadgets={unlocked_g})"
