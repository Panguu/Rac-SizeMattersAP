from __future__ import annotations

from typing import TYPE_CHECKING

from ...items import GADGET_DISPLAY_TO_INTERNAL, WEAPON_DISPLAY_TO_INTERNAL
from ...locations import VENDOR_GADGET_PLANET, VENDOR_WEAPON_PLANET
from ..data.addresses import WEAPON_VENDOR_ITEMS, WEAPON_VENDOR_SLOTS
from ..data.weapons import GADGET_ORDER, WEAPON_ORDER

if TYPE_CHECKING:
    from ...interface_orchestrator.memory.accessor import MemoryAccessor
    from .planet_unlock import PlanetUnlockState
    from .weapon import WeaponState

# Vendor item IDs written to WEAPON_VENDOR_ITEMS.
# Each 4-byte entry identifies one slot in the vendor menu UI.
# Derivation: combined weapon+gadget array slot index + 2 offset.
# lacerator (slot 0) = 0x02 is the only in-game confirmed value.
# All others are inferred from array layout — verify in-game.
WEAPON_VENDOR_IDS: dict[str, int] = {
    # weapons (WEAPON_ORDER slots 0–13; slot 12 is None gap → 0x0E skipped)
    "lacerator":        0x02,  # confirmed
    "concussion_gun":   0x03,
    "acid_bomb_glove":  0x04,
    "agents_of_doom":   0x05,
    "bee_mine_glove":   0x06,
    "static_barrier":   0x07,
    "shock_rocket":     0x08,
    "sniper_mine":      0x09,
    "scorcher":         0x0A,
    "laser_tracer":     0x0B,
    "suck_cannon":      0x0C,
    "mootator":         0x0D,
    # slot 12 gap → 0x0E (no weapon)
    "ryno":             0x0F,
    # gadgets (GADGET_ORDER slots 0–8; slot 6 is None gap → 0x16 skipped)
    "hypershot":        0x10,
    "sprout_o_matic":   0x11,
    "polarizer":        0x12,
    "pda":              0x13,
    "shrink_ray":       0x14,
    "bolt_grabber":     0x15,
    # slot 6 gap → 0x16 (no gadget)
    "map_o_matic":      0x17,
    "box_breaker":      0x18,
}


# Normalise VENDOR_*_PLANET display strings to PlanetUnlockState keys.
_DISPLAY_TO_PLANET_KEY: dict[str, str] = {
    "Pokitaru":      "POKITARU",
    "Ryllus":        "RYLLUS",
    "Kalidon":       "KALIDON",
    "Metalis":       "METALIS",
    "Dreamtime":     "DREAMTIME",
    "Outpost Omega": "OUTPOST_OMEGA",
    "Challax":       "CHALLAX",
    "Dayni Moon":    "DAYNI_MOON",
    "Inside Clank":  "INSIDE_CLANK",
    "Quodrona":      "QUODRONA",
}

# internal weapon name → planet key (derived at import time from VENDOR_WEAPON_PLANET)
_WEAPON_TO_PLANET_KEY: dict[str, str] = {
    WEAPON_DISPLAY_TO_INTERNAL[display]: _DISPLAY_TO_PLANET_KEY[planet]
    for display, planet in VENDOR_WEAPON_PLANET.items()
    if display in WEAPON_DISPLAY_TO_INTERNAL and planet in _DISPLAY_TO_PLANET_KEY
}

# internal gadget name → planet key
_GADGET_TO_PLANET_KEY: dict[str, str] = {
    GADGET_DISPLAY_TO_INTERNAL[display]: _DISPLAY_TO_PLANET_KEY[planet]
    for display, planet in VENDOR_GADGET_PLANET.items()
    if display in GADGET_DISPLAY_TO_INTERNAL and planet in _DISPLAY_TO_PLANET_KEY
}

# Ordered display lists (None gaps stripped) for deterministic slot order.
_WEAPON_DISPLAY_ORDER: list[str] = [n for n in WEAPON_ORDER if n is not None]
_GADGET_DISPLAY_ORDER: list[str] = [n for n in GADGET_ORDER if n is not None]


def _purchased_names(ws: WeaponState) -> frozenset[str]:
    """Return internal names of weapons/gadgets purchased from the vendor."""
    from .weapon import VENDOR_GADGET_LOC, VENDOR_WEAPON_LOC
    result: set[str] = set()
    for loc_name, bought in ws.vendor_locations.items():
        if not bought:
            continue
        if loc_name in VENDOR_WEAPON_LOC:
            result.add(VENDOR_WEAPON_LOC[loc_name])
        elif loc_name in VENDOR_GADGET_LOC:
            result.add(VENDOR_GADGET_LOC[loc_name])
    return frozenset(result)


class VendorUnlockState:

    def __init__(self, weapon_state: WeaponState, planet_unlock: PlanetUnlockState) -> None:
        self._ws = weapon_state
        self._pu = planet_unlock


    def apply(self, accessor: MemoryAccessor) -> None:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        seen: set[int] = set()
        items: list[int] = []

        def _add(name: str) -> None:
            vid = WEAPON_VENDOR_IDS.get(name)
            if vid is not None and vid not in seen:
                seen.add(vid)
                items.append(vid)

        # Ammo-refill slots: player owns the weapon AND
        #   (a) its vendor planet is not yet accessible — remove from inventory would be wrong, or
        #   (b) the purchase location was already checked (bought from vendor before).
        for name in _WEAPON_DISPLAY_ORDER:
            if name not in _WEAPON_TO_PLANET_KEY or not ws.weapons.get(name, False):
                continue
            planet_key = _WEAPON_TO_PLANET_KEY[name]
            if not pu.is_vendor_accessible(planet_key) or name in purchased:
                _add(name)

        for name in _GADGET_DISPLAY_ORDER:
            if name not in _GADGET_TO_PLANET_KEY or not ws.gadgets.get(name, False):
                continue
            planet_key = _GADGET_TO_PLANET_KEY[name]
            if not pu.is_vendor_accessible(planet_key) or name in purchased:
                _add(name)

        # Purchasable slots: planet accessible AND location not yet checked.
        for name, planet_key in _WEAPON_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)
        for name, planet_key in _GADGET_TO_PLANET_KEY.items():
            if pu.is_vendor_accessible(planet_key) and name not in purchased:
                _add(name)

        accessor.write_raw(WEAPON_VENDOR_SLOTS, len(items).to_bytes(4, "little"))
        for i, item_id in enumerate(items):
            accessor.write_raw(WEAPON_VENDOR_ITEMS + i * 4, item_id.to_bytes(4, "little"))

    def allowed_weapons_for_inventory(self) -> frozenset[str]:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        allowed: set[str] = set()

        for name in _WEAPON_DISPLAY_ORDER:
            if not ws.weapons.get(name, False):
                continue
            planet_key = _WEAPON_TO_PLANET_KEY.get(name)
            if planet_key is None or not pu.is_vendor_accessible(planet_key) or name in purchased:
                allowed.add(name)

        for name in _GADGET_DISPLAY_ORDER:
            if not ws.gadgets.get(name, False):
                continue
            planet_key = _GADGET_TO_PLANET_KEY.get(name)
            if planet_key is None or not pu.is_vendor_accessible(planet_key) or name in purchased:
                allowed.add(name)

        return frozenset(allowed)


    def debug_lines(self) -> list[str]:
        ws        = self._ws
        pu        = self._pu
        purchased = _purchased_names(ws)
        lines: list[str] = ["[RAC] Vendor unlock state:"]

        accessible = [k for k in _DISPLAY_TO_PLANET_KEY.values() if pu.is_vendor_accessible(k)]
        lines.append(f"  Accessible planets : {', '.join(accessible) or 'none'}")
        lines.append(f"  Purchased          : {', '.join(sorted(purchased)) or 'none'}")

        for display_planet, planet_key in _DISPLAY_TO_PLANET_KEY.items():
            if not pu.is_vendor_accessible(planet_key):
                continue
            w_here = [n for n, pk in _WEAPON_TO_PLANET_KEY.items() if pk == planet_key and n not in purchased]
            g_here = [n for n, pk in _GADGET_TO_PLANET_KEY.items() if pk == planet_key and n not in purchased]
            available = w_here + g_here
            if available:
                lines.append(f"  {display_planet:<14} → available: {', '.join(available)}")

        # Weapons owned but planet accessible and not purchased — removed from
        # inventory so vendor shows them as purchasable rather than ammo-refill.
        pending_purchase = [
            n for n in _WEAPON_DISPLAY_ORDER + _GADGET_DISPLAY_ORDER
            if (ws.weapons.get(n) or ws.gadgets.get(n))
            and (n in _WEAPON_TO_PLANET_KEY or n in _GADGET_TO_PLANET_KEY)
            and pu.is_vendor_accessible((_WEAPON_TO_PLANET_KEY | _GADGET_TO_PLANET_KEY).get(n, ""))
            and n not in purchased
        ]
        if pending_purchase:
            lines.append(f"  Owned → purchasable slot (removed from inv): {', '.join(pending_purchase)}")

        return lines

    def __repr__(self) -> str:
        pu = self._pu
        purchased = len(_purchased_names(self._ws))
        accessible = sum(1 for pk in _DISPLAY_TO_PLANET_KEY.values() if pu.is_vendor_accessible(pk))
        return f"VendorUnlockState(accessible_planets={accessible}, purchased={purchased})"
