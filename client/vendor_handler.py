from __future__ import annotations

from collections import defaultdict

from ..items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL
from ..locations import VENDOR_WEAPON_MOD_PLANET

_INTERNAL_TO_WEAPON_DISPLAY: dict[str, str] = {v: k for k, v in WEAPON_DISPLAY_TO_INTERNAL.items()}
_INTERNAL_TO_GADGET_DISPLAY: dict[str, str] = {v: k for k, v in GADGET_DISPLAY_TO_INTERNAL.items()}

_SLOTS = ("one", "two", "three")

def _build_mod_slot_to_location() -> dict[tuple[str, str], str]:
    by_weapon: dict[str, list[str]] = defaultdict(list)
    for weapon_display, mod_name in VENDOR_WEAPON_MOD_PLANET:
        by_weapon[weapon_display].append(mod_name)
    result: dict[tuple[str, str], str] = {}
    for weapon_display, mod_names in by_weapon.items():
        internal = WEAPON_DISPLAY_TO_INTERNAL.get(weapon_display)
        if not internal:
            continue
        for idx, mod_name in enumerate(mod_names):
            if idx < len(_SLOTS):
                result[(internal, _SLOTS[idx])] = f"Purchase {weapon_display} {mod_name}"
    return result

_MOD_SLOT_TO_LOCATION: dict[tuple[str, str], str] = _build_mod_slot_to_location()


class VendorHandlerMixin:
    def _on_vendor_close_sync(self) -> None:
        vs = self._gs.vendor_session
        for internal in vs.purchased_weapons:
            display = _INTERNAL_TO_WEAPON_DISPLAY.get(internal)
            if display:
                self._pending_vendor_checks.append(f"Purchase {display}")
        for internal in vs.purchased_gadgets:
            display = _INTERNAL_TO_GADGET_DISPLAY.get(internal)
            if display:
                self._pending_vendor_checks.append(f"Purchase {display}")
        for weapon_internal, slot in vs.purchased_mods:
            loc_name = _MOD_SLOT_TO_LOCATION.get((weapon_internal, slot))
            if loc_name:
                self._pending_vendor_checks.append(loc_name)
