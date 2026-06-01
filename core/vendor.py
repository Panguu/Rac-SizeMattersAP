from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data import WEAPON_MOD_COUNTS, TextBoxDisplayAddrs
from .memory import GADGETS, WEAPONS, MemoryItemState, restore_tracked_weapon_state, zero_weapon
from .menu_state import MenuState, MenuStateValue

_TEXTBOX_BY_PLANET: dict[int, object] = {tb.planet_id: tb for tb in TextBoxDisplayAddrs}

_MOD_SLOT_ATTRS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")
_SLOT_NAMES = {1: "one", 2: "two", 3: "three"}

from .state import GameState


def _build_vendor_weapon_addresses() -> dict[str, int]:
    addrs: dict[str, int] = {}
    for name, w in WEAPONS.items():
        addrs[name] = w.unlocked
        for i, attr in enumerate(_MOD_SLOT_ATTRS, 1):
            if i <= WEAPON_MOD_COUNTS.get(name, 0):
                addrs[f"{name}_mod_{i}"] = getattr(w, attr)
    return addrs


def _build_vendor_gadget_addresses() -> dict[str, int]:
    return {name: g.unlocked for name, g in GADGETS.items()}


@dataclass
class VendorSession:
    """Tracks the state of a vendor interaction.

    on_purchase fires immediately when a weapon, gadget, or mod is detected —
    args are (kind, internal_name, slot_or_None) where kind is "weapon",
    "gadget", or "mod".  This lets the client queue the AP location check
    straight away rather than waiting for the session to close.
    """
    purchased_weapons:  list[str]                              = field(default_factory=list)
    purchased_gadgets:  list[str]                              = field(default_factory=list)
    purchased_mods:     list[tuple[str, str]]                  = field(default_factory=list)
    mods_randomized:    bool                                   = field(default=True)
    log:                Callable[[str], None]                  = field(default=logger.info, repr=False, compare=False)
    on_purchase:        Callable[[str, str, str | None], None] | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.weapon_state = MemoryItemState({}, name="VendorWeaponState", debug_log=self.log)
        self.gadget_state = MemoryItemState({}, name="VendorGadgetState", debug_log=self.log)

    def refresh(
        self,
        tracked_vendor_weapons: dict[str, int],
        tracked_vendor_gadgets: dict[str, int],
        tracked_vendor_mods:    dict[str, set[str]],
    ) -> None:
        """Rebuild vendor state from already-purchased locations."""
        if WEAPONS:
            self.weapon_state.update_addresses(_build_vendor_weapon_addresses())
            for name in WEAPONS:
                self.weapon_state.add(name, 1 if name in tracked_vendor_weapons else 0)
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    slot = _SLOT_NAMES[i]
                    purchased = slot in tracked_vendor_mods.get(name, set())
                    self.weapon_state.add(f"{name}_mod_{i}", 1 if purchased else 0)
        if GADGETS:
            self.gadget_state.update_addresses(_build_vendor_gadget_addresses())
            for name in GADGETS:
                self.gadget_state.add(name, 1 if name in tracked_vendor_gadgets else 0)
        self.purchased_weapons.clear()
        self.purchased_gadgets.clear()
        self.purchased_mods.clear()

    # ── Ammo passthrough ─────────────────────────────────────────────────────

    def _snapshot_ammo(self, ipc: Pine) -> dict[str, int]:
        return {name: ipc.read_int32(w.ammo) for name, w in WEAPONS.items()}

    def _restore_ammo(self, ipc: Pine, ammo: dict[str, int]) -> None:
        for name, w in WEAPONS.items():
            if name in ammo:
                ipc.write_int32(w.ammo, ammo[name])

    # ── Memory operations ─────────────────────────────────────────────────────

    def apply(self, ipc: Pine) -> None:
        """Write vendor state to memory.  Snapshots ammo because the game
        resets it when unlocked flips 0→1."""
        ammo = self._snapshot_ammo(ipc)
        for w in WEAPONS.values():
            zero_weapon(ipc, w)
        for g in GADGETS.values():
            ipc.write_int8(g.unlocked, 0)
        self.weapon_state.give(ipc)
        self.gadget_state.give(ipc)
        self._restore_ammo(ipc, ammo)

    def detect_purchases(self, ipc: Pine, gs: GameState) -> None:
        """Poll addresses; fire on_purchase immediately for each new detection
        and update tracked vendor state so re-opened sessions are accurate."""
        for name, w in WEAPONS.items():
            if self.weapon_state.get(name) == 0 and ipc.read_int8(w.unlocked):
                self._add_weapon(name, gs)
                self.weapon_state.add(name, 1)
            if self.mods_randomized:
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    attr = _MOD_SLOT_ATTRS[i - 1]
                    if self.weapon_state.get(f"{name}_mod_{i}") == 0 and ipc.read_int8(getattr(w, attr)):
                        slot = _SLOT_NAMES[i]
                        self._add_mod(name, slot, gs)
                        self.weapon_state.add(f"{name}_mod_{i}", 1)
        for name, g in GADGETS.items():
            if self.gadget_state.get(name) == 0 and ipc.read_int8(g.unlocked):
                self._add_gadget(name, gs)
                self.gadget_state.add(name, 1)

    def enforce(self, ipc: Pine) -> None:
        """Re-enforce vendor state (correct drift while menu is open)."""
        for name, w in WEAPONS.items():
            expected_unlocked = self.weapon_state.get(name)
            if ipc.read_int8(w.unlocked) != expected_unlocked:
                if expected_unlocked == 0:
                    zero_weapon(ipc, w)
                else:
                    ipc.write_int8(w.unlocked, 1)
            if self.mods_randomized:
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    attr = _MOD_SLOT_ATTRS[i - 1]
                    exp_mod = self.weapon_state.get(f"{name}_mod_{i}")
                    if ipc.read_int8(getattr(w, attr)) != exp_mod:
                        ipc.write_int8(getattr(w, attr), exp_mod)
        for name, g in GADGETS.items():
            exp = self.gadget_state.get(name)
            if ipc.read_int8(g.unlocked) != exp:
                ipc.write_int8(g.unlocked, exp)

    def total(self) -> int:
        return len(self.purchased_weapons) + len(self.purchased_gadgets) + len(self.purchased_mods)

    # ── Purchase recording ────────────────────────────────────────────────────

    def _add_weapon(self, name: str, gs: GameState) -> None:
        if name not in self.purchased_weapons:
            self.purchased_weapons.append(name)
            gs.tracked_vendor_weapons[name] = 1
            self.log(f"  Purchase detected: weapon {name}")
            if self.on_purchase:
                self.on_purchase("weapon", name, None)

    def _add_gadget(self, name: str, gs: GameState) -> None:
        if name not in self.purchased_gadgets:
            self.purchased_gadgets.append(name)
            gs.tracked_vendor_gadgets[name] = 1
            self.log(f"  Purchase detected: gadget {name}")
            if self.on_purchase:
                self.on_purchase("gadget", name, None)

    def _add_mod(self, weapon: str, slot: str, gs: GameState) -> None:
        if (weapon, slot) not in self.purchased_mods:
            self.purchased_mods.append((weapon, slot))
            gs.tracked_vendor_mods.setdefault(weapon, set()).add(slot)
            self.log(f"  Purchase detected: mod {weapon} slot {slot}")
            if self.on_purchase:
                self.on_purchase("mod", weapon, slot)


class VendorPoller:
    """Handles all three vendor stages: preload → menu open → menu close."""

    def __init__(self, gs: GameState, log: Callable[[str], None] | None = None) -> None:
        self._gs  = gs
        self._log = log or logger.info

    def tick(self, ipc: Pine) -> None:
        gs           = self._gs
        ms           = MenuState.read(ipc, gs.current_planet)
        textbox      = _TEXTBOX_BY_PLANET.get(gs.current_planet)
        if textbox:
            raw      = ipc.read_int16(textbox.message_str_pointer)
            msg_val  = ((raw & 0xFF) << 8) | (raw >> 8)
            is_preloaded = msg_val == textbox.vendor_value and bool(ipc.read_int8(textbox.is_visible))
        else:
            is_preloaded = False
        is_in_menu    = ms.is_vendor
        was_preloaded = gs.is_preloaded
        was_in_menu   = gs.is_in_menu

        # Stage 1: preload rising edge — player entered vendor proximity
        if is_preloaded and not was_preloaded and not is_in_menu and not gs.is_dead and not gs.is_picking_up:
            if not WEAPONS or not gs.weapons_ready:
                logger.warning("Vendor preload: weapon addresses not ready yet — waiting for planet load.")
                return
            gs.vendor_session.refresh(gs.tracked_vendor_weapons, gs.tracked_vendor_gadgets, gs.tracked_vendor_mods)
            self._log("Vendor preload detected.")
            gs.vendor_session.apply(ipc)
            self._log(
                f"Vendor state applied: {gs.vendor_session.weapon_state!r}  "
                f"{gs.vendor_session.gadget_state!r}"
            )

        # Stage 1: falling edge — player left without opening menu
        if was_preloaded and not is_preloaded and not is_in_menu and not was_in_menu:
            restore_tracked_weapon_state(gs)
            self._log("Vendor area left. State restored.")

        # Stage 2: menu opened
        if is_in_menu and not was_in_menu and not gs.is_dead and not gs.is_picking_up:
            self._log(f"Vendor menu opened ({ms!r}).")
            if not WEAPONS or not gs.weapons_ready:
                logger.warning("Vendor menu: weapon addresses not ready yet.")
                return
            gs.vendor_session.apply(ipc)
            ms.write(ipc, MenuStateValue.CLOSED)
            ms.write(ipc, MenuStateValue(ms.raw))
            self._log("Vendor menu refreshed.")

        # Stage 2: ongoing purchase detection — fires on_purchase immediately per item
        if is_in_menu and not gs.is_dead:
            gs.vendor_session.detect_purchases(ipc, gs)

        # Stage 3: menu closed
        if was_in_menu and not is_in_menu:
            self._process_close(gs, ipc)

        gs.is_preloaded = is_preloaded
        gs.is_in_menu   = is_in_menu

    def _process_close(self, gs: GameState, ipc: Pine) -> None:
        vs = gs.vendor_session
        # Final sweep in case anything was missed during the pickup animation.
        vs.detect_purchases(ipc, gs)
        total = vs.total()
        self._log(f"Vendor closed. {total} purchase(s) processed.")
        ammo = vs._snapshot_ammo(ipc)
        restore_tracked_weapon_state(gs)
        vs._restore_ammo(ipc, ammo)
        self._log("Vendor state restored.")
