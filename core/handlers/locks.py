from __future__ import annotations

from ..memory import ARMOUR_ADDRESSES, GADGETS, WEAPONS
from ..state import GameState


def _enforce_locks(gs: GameState) -> None:
    if gs.is_dead or gs.is_picking_up:
        return
    ipc = gs.ipc

    if not gs.is_in_menu:
        for name, addr in ARMOUR_ADDRESSES.items():
            expected = gs.tracked_armour.get(name, 0)
            if expected and ipc.read_int8(addr) != expected:
                ipc.write_int8(addr, expected)

    if (gs.is_preloaded or gs.is_in_menu) and gs.tracked_vendor is not None:
        gs.vendor_session.enforce(ipc)
    elif not gs.is_in_menu:
        for name, w in WEAPONS.items():
            expected = 1 if name in gs.tracked_weapons else 0
            if ipc.read_int8(w.unlocked) != expected:
                ipc.write_int8(w.unlocked, expected)
        for name, g in GADGETS.items():
            expected = 1 if name in gs.tracked_gadgets else 0
            if ipc.read_int8(g.unlocked) != expected:
                ipc.write_int8(g.unlocked, expected)
