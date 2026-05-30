from __future__ import annotations

import asyncio
from collections import defaultdict

from CommonClient import logger

from ..items import (
    ARMOUR_DISPLAY_TO_INTERNAL,
    ARMOUR_PIECE_BITMASKS,
    ARMOUR_SET_DISPLAY_TO_INTERNAL,
    GADGET_DISPLAY_TO_INTERNAL,
    WEAPON_DISPLAY_TO_INTERNAL,
)
from ..locations import (
    VENDOR_GADGET_PLANET,
    VENDOR_WEAPON_MOD_PLANET,
    VENDOR_WEAPON_PLANET,
)

# ── Vendor location → internal name lookups ───────────────────────────────────

_VENDOR_WEAPON_LOC: dict[str, str] = {
    f"Purchase {display}": WEAPON_DISPLAY_TO_INTERNAL[display]
    for display in VENDOR_WEAPON_PLANET
    if display in WEAPON_DISPLAY_TO_INTERNAL
}

_VENDOR_GADGET_LOC: dict[str, str] = {
    f"Purchase {display}": GADGET_DISPLAY_TO_INTERNAL[display]
    for display in VENDOR_GADGET_PLANET
    if display in GADGET_DISPLAY_TO_INTERNAL
}

_SLOTS = ("one", "two", "three")
_by_weapon: dict[str, list[str]] = defaultdict(list)
for (_wd, _mn) in VENDOR_WEAPON_MOD_PLANET:
    _by_weapon[_wd].append(_mn)
_VENDOR_MOD_LOC: dict[str, tuple[str, str]] = {}
for _wd, _mns in _by_weapon.items():
    _int = WEAPON_DISPLAY_TO_INTERNAL.get(_wd)
    if _int:
        for _i, _mn in enumerate(_mns):
            if _i < len(_SLOTS):
                _VENDOR_MOD_LOC[f"Purchase {_wd} {_mn}"] = (_int, _SLOTS[_i])
from ..core.data import PLAYER_BOLT_COUNT, WEAPON_MOD_COUNTS
from ..core.memory import (
    ARMOUR_ADDRESSES,
    GADGETS,
    WEAPONS,
    apply_tracked_weapons,
)
from .constants import BOLT_ITEM_AMOUNT


class InventoryMixin:
    async def _apply_received_items(self) -> None:
        self._rebuild_expected_inventory()
        if not self.pine_connected:
            self._pending_item_apply = True
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            await loop.run_in_executor(None, self._apply_expected_inventory_sync, True)
            self._grant_new_bolt_items()
        weapon_items_waiting = bool(self._expected_weapons or self._expected_gadgets) and not (WEAPONS and GADGETS)
        self._pending_item_apply = weapon_items_waiting
        armour_piece_count = sum(value.bit_count() for value in self._expected_armour.values())
        logger.info(
            "[RAC] Applied AP inventory: "
            f"{len(self._expected_weapons)} weapons, "
            f"{len(self._expected_gadgets)} gadgets, "
            f"{armour_piece_count} armour pieces."
        )
        if weapon_items_waiting:
            logger.warning("[RAC] Weapon/gadget items are pending until the weapon array is found. Use /scan.")

    def _rebuild_expected_inventory(self) -> None:
        self._expected_weapons = {}
        self._expected_weapon_mods = {}
        self._expected_gadgets = {}
        self._expected_armour = dict.fromkeys(ARMOUR_ADDRESSES, 0)

        weapon_prog_counts: dict[str, int] = {}
        armour_prog_counts: dict[str, int] = {}

        for network_item in self.items_received:
            item_name = self.item_names[self.game].get(network_item.item, "")

            if item_name.endswith(" Progressive Weapon"):
                display = item_name[: -len(" Progressive Weapon")]
                weapon_prog_counts[display] = weapon_prog_counts.get(display, 0) + 1
                continue
            if item_name.endswith(" Progressive Pickup"):
                display = item_name[: -len(" Progressive Pickup")]
                armour_prog_counts[display] = armour_prog_counts.get(display, 0) + 1
                continue

            if item_name in WEAPON_DISPLAY_TO_INTERNAL:
                self._expected_weapons[WEAPON_DISPLAY_TO_INTERNAL[item_name]] = 1
            elif item_name in GADGET_DISPLAY_TO_INTERNAL:
                self._expected_gadgets[GADGET_DISPLAY_TO_INTERNAL[item_name]] = 1
            elif item_name in ARMOUR_DISPLAY_TO_INTERNAL:
                set_key, piece = ARMOUR_DISPLAY_TO_INTERNAL[item_name]
                if set_key in self._expected_armour:
                    self._expected_armour[set_key] |= piece

        for display, count in armour_prog_counts.items():
            internal = ARMOUR_SET_DISPLAY_TO_INTERNAL.get(display)
            if not internal or internal not in self._expected_armour:
                continue
            bitmask = 0
            for i, bit in enumerate(ARMOUR_PIECE_BITMASKS):
                if i < count:
                    bitmask |= bit
            self._expected_armour[internal] = bitmask

        for display, count in weapon_prog_counts.items():
            internal = WEAPON_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            if count >= 1:
                self._expected_weapons[internal] = 1
            self._expected_weapon_mods[internal] = min(count - 1, WEAPON_MOD_COUNTS.get(internal, 0))

        self._sync_game_state_inventory()

    def _sync_game_state_inventory(self) -> None:
        self._gs.tracked_weapons = self._expected_weapons.copy()
        self._gs.tracked_gadgets = self._expected_gadgets.copy()
        self._gs.tracked_armour = self._expected_armour.copy()
        # Vendor baseline: derived from completed vendor location checks, not received items.
        # "Purchase Lacerator" checked → lacerator was bought → show as already purchased.
        # This is correct in multiworld where the item received != the item purchased.
        checked = self.checked_locations | self._locally_checked_locations
        vendor_weapons: dict[str, int] = {}
        vendor_gadgets: dict[str, int] = {}
        vendor_mods: dict[str, set[str]] = {}
        for loc_name, internal in _VENDOR_WEAPON_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_weapons[internal] = 1
        for loc_name, internal in _VENDOR_GADGET_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_gadgets[internal] = 1
        for loc_name, (internal, slot) in _VENDOR_MOD_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_mods.setdefault(internal, set()).add(slot)
        self._gs.tracked_vendor_weapons = vendor_weapons
        self._gs.tracked_vendor_gadgets = vendor_gadgets
        self._gs.tracked_vendor_mods = vendor_mods

    def _apply_expected_inventory_sync(self, clear_unreceived: bool = False) -> None:
        if not WEAPONS:
            self._sync_weapons_cached()
        self._sync_game_state_inventory()

        if WEAPONS:
            for name, weapon in WEAPONS.items():
                if clear_unreceived or name in self._expected_weapons:
                    self.pine.write_int8(weapon.unlocked, self._expected_weapons.get(name, 0))
                if clear_unreceived or name in self._expected_weapon_mods:
                    mods = self._expected_weapon_mods.get(name, 0)
                    self.pine.write_int8(weapon.mod_slot_one,   1 if mods >= 1 else 0)
                    self.pine.write_int8(weapon.mod_slot_two,   1 if mods >= 2 else 0)
                    self.pine.write_int8(weapon.mod_slot_three, 1 if mods >= 3 else 0)
            for name, gadget in GADGETS.items():
                if clear_unreceived or name in self._expected_gadgets:
                    self.pine.write_int8(gadget.unlocked, self._expected_gadgets.get(name, 0))

        if not self._gs.is_picking_up:
            for name, address in ARMOUR_ADDRESSES.items():
                value = self._expected_armour.get(name, 0)
                self.pine.write_int8(address, value)
                self._prev_armour_sets[name] = value
        if WEAPONS:
            apply_tracked_weapons(self._gs)

    def _grant_new_bolt_items(self) -> None:
        new_items = self.items_received[self._processed_item_count:]
        self._processed_item_count = len(self.items_received)

        bolts_to_add = 0
        starting_bolts = int(self.slot_data.get("starting_bolts", 0))
        for network_item in new_items:
            item_name = self.item_names[self.game].get(network_item.item, "")
            if item_name != "Bolts":
                continue
            if starting_bolts and not self._starting_bolts_granted:
                bolts_to_add += starting_bolts
                self._starting_bolts_granted = True
            else:
                bolts_to_add += BOLT_ITEM_AMOUNT

        if bolts_to_add <= 0 or not self.pine_connected:
            return
        try:
            current = self.pine.read_int32(PLAYER_BOLT_COUNT)
            self.pine.write_int32(PLAYER_BOLT_COUNT, current + bolts_to_add)
        except Exception as exc:
            logger.warning(f"[RAC] Could not grant bolts: {exc}")
