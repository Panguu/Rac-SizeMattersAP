from __future__ import annotations

from dataclasses import dataclass, field

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data import BY_ID, WEAPON_MOD_COUNTS, TextBoxDisplayAddrs
from .memory import GADGETS, WEAPONS, restore_tracked_weapon_state, zero_weapon

_TEXTBOX_BY_PLANET: dict[int, object] = {tb.planet_id: tb for tb in TextBoxDisplayAddrs}

from .state import GameState


@dataclass
class VendorSession:
    weapons: dict[str, int]            = field(default_factory=dict)
    gadgets: dict[str, int]            = field(default_factory=dict)
    mods:    dict[str, dict[str, int]] = field(default_factory=dict)

    purchased_weapons: list[str]             = field(default_factory=list)
    purchased_gadgets: list[str]             = field(default_factory=list)
    purchased_mods:    list[tuple[str, str]] = field(default_factory=list)

    def refresh(
        self,
        tracked_vendor_weapons: dict[str, int],
        tracked_vendor_gadgets: dict[str, int],
        tracked_vendor_mods:    dict[str, set[str]],
    ) -> None:
        self.weapons = {name: (1 if name in tracked_vendor_weapons else 0) for name in WEAPONS}
        self.gadgets = {name: (1 if name in tracked_vendor_gadgets else 0) for name in GADGETS}
        _slots = ("one", "two", "three")
        self.mods    = {
            name: {slot: (1 if slot in tracked_vendor_mods.get(name, set()) else 0)
                   for slot in _slots[:WEAPON_MOD_COUNTS.get(name, 0)]}
            for name in WEAPONS
        }
        self.purchased_weapons.clear()
        self.purchased_gadgets.clear()
        self.purchased_mods.clear()

    def apply(self, ipc: Pine) -> None:
        for name, val in self.weapons.items():
            if name not in WEAPONS:
                continue
            w = WEAPONS[name]
            if val == 0:
                zero_weapon(ipc, w)
            else:
                ipc.write_int8(w.unlocked, 1)
                for slot, sval in self.mods.get(name, {}).items():
                    ipc.write_int8(getattr(w, f"mod_slot_{slot}"), sval)
        for name, val in self.gadgets.items():
            if name in GADGETS:
                ipc.write_int8(GADGETS[name].unlocked, val)

    def detect_purchases(self, ipc: Pine) -> None:
        for name, w in WEAPONS.items():
            if self.weapons.get(name, 0) == 0:
                if ipc.read_int8(w.unlocked):
                    self._add_weapon(name)
                    self.weapons[name] = 1
            else:
                for slot, sval in self.mods.get(name, {}).items():
                    if sval == 0 and ipc.read_int8(getattr(w, f"mod_slot_{slot}")):
                        self._add_mod(name, slot)
                        self.mods[name][slot] = 1
        for name, g in GADGETS.items():
            if self.gadgets.get(name, 0) == 0 and ipc.read_int8(g.unlocked):
                self._add_gadget(name)
                self.gadgets[name] = 1

    def enforce(self, ipc: Pine) -> None:
        for name, val in self.weapons.items():
            if name not in WEAPONS:
                continue
            w = WEAPONS[name]
            if val == 0:
                if ipc.read_int8(w.unlocked):
                    zero_weapon(ipc, w)
            else:
                if not ipc.read_int8(w.unlocked):
                    ipc.write_int8(w.unlocked, 1)
                for slot, sval in self.mods.get(name, {}).items():
                    if ipc.read_int8(getattr(w, f"mod_slot_{slot}")) != sval:
                        ipc.write_int8(getattr(w, f"mod_slot_{slot}"), sval)
        for name, val in self.gadgets.items():
            if name in GADGETS and ipc.read_int8(GADGETS[name].unlocked) != val:
                ipc.write_int8(GADGETS[name].unlocked, val)

    def _add_weapon(self, name: str) -> None:
        if name not in self.purchased_weapons:
            self.purchased_weapons.append(name)
            logger.info(f"  Purchase detected: weapon {name}")

    def _add_gadget(self, name: str) -> None:
        if name not in self.purchased_gadgets:
            self.purchased_gadgets.append(name)
            logger.info(f"  Purchase detected: gadget {name}")

    def _add_mod(self, weapon: str, slot: str) -> None:
        if (weapon, slot) not in self.purchased_mods:
            self.purchased_mods.append((weapon, slot))
            logger.info(f"  Purchase detected: mod {weapon} slot {slot}")

    def total(self) -> int:
        return len(self.purchased_weapons) + len(self.purchased_gadgets) + len(self.purchased_mods)


class VendorPoller:
    """Handles all three vendor stages: preload → menu open → menu close."""

    def __init__(self, gs: GameState) -> None:
        self._gs = gs

    def tick(self, ipc: Pine) -> None:
        gs           = self._gs
        planet_obj   = BY_ID.get(gs.current_planet)
        menu_addr    = planet_obj.menu_addr if planet_obj else None
        menu_state   = ipc.read_int8(menu_addr) if menu_addr else 0
        textbox      = _TEXTBOX_BY_PLANET.get(gs.current_planet)
        if textbox:
            raw      = ipc.read_int16(textbox.message_str_pointer)
            msg_val  = ((raw & 0xFF) << 8) | (raw >> 8)  # byte-swap: pine reads little-endian, PS2 is big-endian
            is_preloaded = msg_val == textbox.vendor_value and bool(ipc.read_int8(textbox.is_visible))
        else:
            is_preloaded = False
        is_in_menu    = menu_state in (0x09, 0x0E)
        was_preloaded = gs.is_preloaded
        was_in_menu   = gs.is_in_menu

        # Stage 1: preload rising edge
        if is_preloaded and not was_preloaded and not is_in_menu and not gs.is_dead and not gs.is_picking_up:
            if not WEAPONS:
                logger.warning("Vendor preload: WEAPONS empty. Use /scan after the game is loaded.")
                return
            if gs.tracked_vendor is None:
                gs.tracked_vendor = gs.current_planet
                gs.vendor_session.refresh(gs.tracked_vendor_weapons, gs.tracked_vendor_gadgets, gs.tracked_vendor_mods)
                logger.info("Vendor preload detected.")
            else:
                logger.info("Vendor re-preloaded (session preserved).")
            gs.vendor_session.apply(ipc)
            logger.info(
                f"Vendor state applied: {len(gs.vendor_session.weapons)} weapons, "
                f"{len(gs.vendor_session.gadgets)} gadgets."
            )

        # Stage 1: falling edge — player left without opening menu
        if was_preloaded and not is_preloaded and not is_in_menu and not was_in_menu:
            gs.tracked_vendor = None
            restore_tracked_weapon_state(gs)
            logger.info("Vendor area left. State restored.")

        # Stage 2: menu opened
        if is_in_menu and not was_in_menu and not gs.is_dead and not gs.is_picking_up:
            logger.info(f"Vendor menu opened (menu={menu_state:#04x}).")
            if not WEAPONS:
                logger.warning("Vendor menu: WEAPONS empty. Use /scan after the game is loaded.")
                return
            gs.vendor_session.apply(ipc)
            if menu_addr:
                ipc.write_int8(menu_addr, 0x01)
                ipc.write_int8(menu_addr, menu_state)
                logger.info("Vendor menu refreshed.")

        # Stage 2: ongoing purchase detection
        # Allow detection even during is_picking_up — vendor purchases trigger the 0x43 pickup
        # animation, so blocking on is_picking_up would cause the detection window to be missed.
        if is_in_menu and not gs.is_dead:
            gs.vendor_session.detect_purchases(ipc)

        # Stage 3: menu closed
        if was_in_menu and not is_in_menu:
            self._process_close(gs, ipc)

        gs.is_preloaded = is_preloaded
        gs.is_in_menu   = is_in_menu

    def _process_close(self, gs: GameState, ipc: Pine) -> None:
        vs    = gs.vendor_session
        total = vs.total()
        logger.info(f"Vendor closed. Processing {total} purchase(s)…")
        if total == 0:
            logger.info("  No purchases detected.")
        for name in vs.purchased_weapons:
            logger.info(f"  Purchased weapon: {name}")
            gs.tracked_vendor_weapons[name] = 1
            if gs.on_reward:
                gs.on_reward()
        for name in vs.purchased_gadgets:
            logger.info(f"  Purchased gadget: {name}")
            gs.tracked_vendor_gadgets[name] = 1
            if gs.on_reward:
                gs.on_reward()
        for weapon, slot in vs.purchased_mods:
            logger.info(f"  Purchased mod: {weapon} slot {slot}")
            gs.tracked_vendor_mods.setdefault(weapon, set()).add(slot)
            if gs.on_reward:
                gs.on_reward()
        if gs.on_vendor_close:
            gs.on_vendor_close()
        gs.tracked_vendor = None
        restore_tracked_weapon_state(gs)
        logger.info("Vendor state restored.")
