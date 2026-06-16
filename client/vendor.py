from __future__ import annotations

import asyncio
import random

from ..core import (
    ALL_TRAPS,
    ARMOUR_ADDRESSES,
    ARMOUR_FLAG_TO_LOCATION,
    AUTO_UNLOCK_ADDRESSES,
    GADGETS,
    INFOBOT_ITEM_TO_PLANET,
    INFOBOT_UNLOCK_VALUE,
    PLAYER_ARMOUR_SLOTS,
    SKILL_POINTS,
    TITANIUM_BOLTS,
    WEAPON_MAX_LEVELS,
    WEAPON_MOD_COUNTS,
    WEAPONS,
    ArmourPiece,
    SmallTextBoxAddrs,
    TextColour,
    activate_trap,
    colored_text,
)
from ..core.address_maps import BOLT_PICKUP_MASK, PLAYER_BOLT_COUNT
from ..core.memory.singletons import _ARMOUR_PIECES, _ARMOUR_SET_ORDER, _PIECE_TO_SLOTS
from ..items import (
    ARMOUR_DISPLAY_TO_INTERNAL,
    ARMOUR_PIECE_BITMASKS,
    ARMOUR_SET_DISPLAY_TO_INTERNAL,
    GADGET_DISPLAY_TO_INTERNAL,
    WEAPON_DISPLAY_TO_INTERNAL,
)
from ..locations import (
    GADGET_INTERNAL_TO_LOCATION,
    MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION,
    VENDOR_GADGET_LOC,
    VENDOR_WEAPON_LOC,
    WEAPON_INTERNAL_TO_LOCATION,
)

_SMALL_BOX_BY_PLANET = {tb.planet_id: tb for tb in SmallTextBoxAddrs}


# ── Vendor handler ───────────────────────────────────────────────────────────────

# (internal_weapon, "one"/"two"/"three") → AP location name — matches VendorSession._SLOT_NAMES
_MOD_SLOT_TO_LOCATION = MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION


class VendorHandlerMixin:
    def _on_vendor_purchase(self, kind: str, name: str, slot: str | None) -> None:
        """Fired immediately when a weapon, gadget, or mod purchase is detected.
        Queues the AP location check straight away rather than waiting for close.
        """
        if kind == "weapon":
            loc_name = WEAPON_INTERNAL_TO_LOCATION.get(name)
            if loc_name:
                self._pending_vendor_checks.append(loc_name)
        elif kind == "gadget":
            loc_name = GADGET_INTERNAL_TO_LOCATION.get(name)
            if loc_name:
                self._pending_vendor_checks.append(loc_name)
        elif kind == "mod" and slot is not None:
            loc_name = _MOD_SLOT_TO_LOCATION.get((name, slot))
            if loc_name:
                self._pending_vendor_checks.append(loc_name)

    def _on_vendor_close_sync(self) -> None:
        """Called when the vendor menu closes. Flushes pending purchase checks."""
        for loc_name in self._pending_vendor_checks:
            self._append_location_by_name(loc_name)
        self._pending_vendor_checks.clear()

    async def _send_vendor_hints(self) -> None:
        """Send AP location hints for all currently purchasable vendor items.

        Called each time the vendor menu opens. Skips locations that have already
        been hinted or checked this session.
        """
        if self.slot is None or not self.pine_connected:
            return
        vendor_type = self._wiring.vendor.vendor_type
        loc_names = self._wiring.vendor_unlock.purchasable_loc_names(vendor_type)
        checked   = self.checked_locations | self._locally_checked_locations
        new_ids: list[int] = []
        for name in loc_names:
            loc_id = self._location_name_to_id.get(name)
            if loc_id is None or loc_id in self._already_hinted or loc_id in checked:
                continue
            new_ids.append(loc_id)
        if not new_ids:
            return
        await self.send_msgs([
            {"cmd": "LocationScouts", "locations": new_ids, "create_as_hint": 2}
        ])
        self._already_hinted.update(new_ids)


# ── Inventory ────────────────────────────────────────────────────────────────────

# AP location name → (internal weapon, "one"/"two"/"three") — for inventory sync
_VENDOR_MOD_LOC: dict[str, tuple[str, str]] = {
    v: k for k, v in MOD_INTERNAL_TO_VENDOR_SLOT_LOCATION.items()
}

_LOCATION_TO_ARMOUR: dict[str, tuple[str, int]] = {
    name: (set_key, int(piece))
    for (set_key, piece), name in ARMOUR_FLAG_TO_LOCATION.items()
}

_MOD_SLOT_ATTRS = ("mod_slot_one", "mod_slot_two", "mod_slot_three")


def _build_weapon_addresses() -> dict[str, int]:
    """Build key→address map for PlayerWeaponState from the currently-loaded WEAPONS."""
    addrs: dict[str, int] = {}
    for name, w in WEAPONS.items():
        addrs[name] = w.unlocked
        for i, attr in enumerate(_MOD_SLOT_ATTRS, 1):
            if i <= WEAPON_MOD_COUNTS.get(name, 0):
                addrs[f"{name}_mod_{i}"] = getattr(w, attr)
    return addrs


def _build_gadget_addresses() -> dict[str, int]:
    return {name: g.unlocked for name, g in GADGETS.items()}


class InventoryMixin:
    async def _apply_inventory_after_pickup(self) -> None:
        """Deferred inventory flush called after pickup ends.

        GameWiring's on_pickup_end reads armour from memory after a 0.3 s sleep.
        We wait 0.5 s so that detection window has closed before we write AP items,
        preventing false armour-pickup location checks.
        """
        await asyncio.sleep(0.5)
        if not self._pending_item_apply or self._wiring.is_picking_up:
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            await loop.run_in_executor(None, self._apply_world_states_sync)
            await loop.run_in_executor(None, self._apply_player_inventory_sync)
        self._pending_item_apply = False

    async def force_sync(self) -> None:
        """Force the player's in-game state to match what was received from AP,
        regardless of pickup/menu guards or what's already been applied."""
        if not self.pine_connected:
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            await loop.run_in_executor(None, self._apply_player_inventory_sync)
            await loop.run_in_executor(None, self._apply_world_states_sync)
        self._pending_item_apply = False

    async def _apply_received_items(self) -> None:
        if not self.pine_connected:
            self._pending_item_apply = True
            return
        if not self.items_received:
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            # Always rebuild internal inventory state (weapons/armour/gadgets)
            # so it is up-to-date even during a pickup animation.
            # _apply_player_inventory_sync guards game-memory writes internally
            # when is_picking_up is True, so only the state rebuild runs.
            await loop.run_in_executor(None, self._apply_player_inventory_sync)
            # Bolts/traps don't depend on the weapon/armour pickup-detection
            # window, so apply them immediately rather than deferring behind
            # is_picking_up — otherwise a trap received mid-pickup-animation
            # sits pending indefinitely (the post-pickup retry path doesn't
            # re-check for new bolts/traps).
            self._grant_new_bolt_items()
            self._grant_new_trap_items()
            if self._wiring.is_picking_up:
                self._pending_item_apply = True
                return
            await loop.run_in_executor(None, self._apply_world_states_sync)
        self._show_new_item_notifications()
        self._pending_item_apply = False

    # ── Rebuild from received AP items ────────────────────────────────────────

    def _rebuild_player_inventory(self) -> None:
        """Recompute all three player states from items_received."""
        # Reset armour and planet states
        for key in ARMOUR_ADDRESSES:
            self._player_armour_state.add(key, 0)
        for key in self._planet_state.values:
            self._planet_state.add(key, 0)

        weapon_prog_counts: dict[str, int] = {}
        armour_prog_counts: dict[str, int] = {}
        weapon_unlocked:    dict[str, int] = {}
        gadget_unlocked:    dict[str, int] = {}
        weapon_mods:        dict[str, int] = {}  # internal_name → max mods count

        infobot_planets: set[str] = set()
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

            if item_name in INFOBOT_ITEM_TO_PLANET:
                planet_key = INFOBOT_ITEM_TO_PLANET[item_name]
                self._planet_state.add(planet_key, INFOBOT_UNLOCK_VALUE)
                if planet_key == "outpost_omega":
                    self._planet_state.add("outpost_omega_oo2", INFOBOT_UNLOCK_VALUE)
                infobot_planets.add(planet_key.upper())
            elif item_name in WEAPON_DISPLAY_TO_INTERNAL:
                weapon_unlocked[WEAPON_DISPLAY_TO_INTERNAL[item_name]] = 1
            elif item_name in GADGET_DISPLAY_TO_INTERNAL:
                gadget_unlocked[GADGET_DISPLAY_TO_INTERNAL[item_name]] = 1
            elif item_name in ARMOUR_DISPLAY_TO_INTERNAL:
                set_key, piece = ARMOUR_DISPLAY_TO_INTERNAL[item_name]
                self._player_armour_state.add(
                    set_key,
                    self._player_armour_state.get(set_key) | int(piece),
                )

        self._wiring.planet_unlock.set_unlocked_planets(infobot_planets)

        # Progressive armour
        for display, count in armour_prog_counts.items():
            internal = ARMOUR_SET_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            bitmask = 0
            for i, bit in enumerate(ARMOUR_PIECE_BITMASKS):
                if i < count:
                    bitmask |= bit
            self._player_armour_state.add(internal, bitmask)

        # Progressive weapons
        prog_mode = int(self.slot_data.get("progressive_weapons", 0))
        weapon_levels: dict[str, int] = {}
        for display, count in weapon_prog_counts.items():
            internal = WEAPON_DISPLAY_TO_INTERNAL.get(display)
            if not internal:
                continue
            if count >= 1:
                weapon_unlocked[internal] = 1
            n_mods = WEAPON_MOD_COUNTS.get(internal, 0)
            if prog_mode == 1:  # progressive_mods: unlock then mods, no levels
                weapon_mods[internal] = min(count - 1, n_mods)
                weapon_levels[internal] = 0
            elif prog_mode == 2:  # progressive_levels: unlock then levels, no mods
                weapon_mods[internal] = 0
                weapon_levels[internal] = min(max(0, count - 1), WEAPON_MAX_LEVELS.get(internal, 1) - 1)
            else:  # all_progressive (3): unlock, mods, then levels
                weapon_mods[internal] = min(count - 1, n_mods)
                level_steps = max(0, count - 1 - n_mods)
                weapon_levels[internal] = min(level_steps, WEAPON_MAX_LEVELS.get(internal, 1) - 1)
        self._gs.tracked_weapon_levels = weapon_levels

        # Populate weapon/gadget player states (updates addresses if weapons are loaded)
        if WEAPONS:
            self._player_weapon_state.update_addresses(_build_weapon_addresses())
            for name in WEAPONS:
                self._player_weapon_state.add(name, weapon_unlocked.get(name, 0))
                mods = weapon_mods.get(name, 0)
                for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                    self._player_weapon_state.add(f"{name}_mod_{i}", 1 if mods >= i else 0)

        if GADGETS:
            self._player_gadget_state.update_addresses(_build_gadget_addresses())
            for name in GADGETS:
                self._player_gadget_state.add(name, gadget_unlocked.get(name, 0))

        self._sync_game_state_inventory()

    # ── Pickup state seed ─────────────────────────────────────────────────────

    def _seed_armour_pickup_state(self) -> None:
        """OR already-checked armour-pickup locations into the pickup state."""
        checked = self.checked_locations | self._locally_checked_locations
        for loc_name, (set_key, piece) in _LOCATION_TO_ARMOUR.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                self._armour_pickup_state.add(
                    set_key,
                    self._armour_pickup_state.get(set_key) | piece,
                )

    # ── Game-state sync ───────────────────────────────────────────────────────

    def _sync_game_state_inventory(self) -> None:
        self._seed_armour_pickup_state()

        self._gs.tracked_armour = {
            key: self._player_armour_state.get(key) | self._armour_pickup_state.get(key)
            for key in ARMOUR_ADDRESSES
        }

        # tracked_weapons / tracked_gadgets come from player states
        self._gs.tracked_weapons = {
            name: self._player_weapon_state.get(name) for name in WEAPONS
        }
        self._gs.tracked_gadgets = {
            name: self._player_gadget_state.get(name) for name in GADGETS
        }

        # tracked_mods: convert mod_i keys back to the "one/two/three" scheme
        # used by restore_tracked_weapon_state
        slot_names = {1: "one", 2: "two", 3: "three"}
        tracked_mods: dict[str, set[str]] = {}
        for name in WEAPONS:
            for i in range(1, WEAPON_MOD_COUNTS.get(name, 0) + 1):
                if self._player_weapon_state.get(f"{name}_mod_{i}", 0):
                    tracked_mods.setdefault(name, set()).add(slot_names[i])
        self._gs.tracked_mods = tracked_mods

        # Vendor baseline from completed vendor location checks
        checked = self.checked_locations | self._locally_checked_locations
        vendor_weapons: dict[str, int] = {}
        vendor_gadgets: dict[str, int] = {}
        vendor_mods: dict[str, set[str]] = {}
        for loc_name, internal in VENDOR_WEAPON_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_weapons[internal] = 1
        for loc_name, internal in VENDOR_GADGET_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_gadgets[internal] = 1
        for loc_name, (internal, slot) in _VENDOR_MOD_LOC.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                vendor_mods.setdefault(internal, set()).add(slot)
        self._gs.tracked_vendor_weapons = vendor_weapons
        self._gs.tracked_vendor_gadgets = vendor_gadgets
        self._gs.tracked_vendor_mods    = vendor_mods

    # ── Slot state ────────────────────────────────────────────────────────────

    def _sync_armour_slot_state(self) -> None:
        """Compute slot values from tracked_armour and store them in _armour_slot_state.

        The value written to each slot address is the 1-based set index — the slot
        address itself (chestplate/helmet/boots/…) encodes which piece it is, so the
        value only needs to identify the set (wildfire=1, sludge=2, …).
        """
        slot_vals: dict[str, int] = dict.fromkeys(PLAYER_ARMOUR_SLOTS, 0)
        for set_idx, set_name in enumerate(_ARMOUR_SET_ORDER):
            val = self._gs.tracked_armour.get(set_name, 0)
            if not val:
                continue
            slot_value = set_idx + 1
            for piece in _ARMOUR_PIECES:
                if piece in ArmourPiece(val):
                    for slot in _PIECE_TO_SLOTS[piece]:
                        slot_vals[slot] = slot_value
        for slot, v in slot_vals.items():
            self._armour_slot_state.add(slot, v)

    # ── Write to game memory ──────────────────────────────────────────────────

    def _apply_player_inventory_sync(self) -> None:
        """Rebuild from items_received, sync addresses, and write all states to memory.

        Rebuilding here ensures every call site (respawn, pickup end, planet load,
        AP item receive) always uses a fresh inventory — never stale values.
        """
        self._rebuild_player_inventory()
        if WEAPONS:
            self._player_weapon_state.update_addresses(_build_weapon_addresses())
        if GADGETS:
            self._player_gadget_state.update_addresses(_build_gadget_addresses())
        # _rebuild_player_inventory already called _sync_game_state_inventory;
        # re-run it here to pick up the freshly updated weapon/gadget addresses.
        self._sync_game_state_inventory()
        if self._wiring.is_picking_up:
            return
        if self._wiring.writes_blocked:
            self._log("[RAC] _apply_player_inventory_sync: all writes blocked — planet transition or travel menu open")
            return
        self._planet_state.give(self.pine)
        for key, addr in ARMOUR_ADDRESSES.items():
            ap_val = self._player_armour_state.get(key)
            existing = self.pine.read_int8(addr)
            self.pine.write_int8(addr, existing | ap_val)
        # Never write weapons or gadgets while vendor owns the weapon state.
        if self._gs.is_preloaded or self._gs.is_in_menu or self._wiring.vendor_active:
            self._log(f"[RAC] _apply_player_inventory_sync: weapon write blocked — "
                      f"is_preloaded={self._gs.is_preloaded}, is_in_menu={self._gs.is_in_menu}, "
                      f"vendor_active={self._wiring.vendor_active}")
            return
        unlocked = [k for k, v in self._player_weapon_state.values.items() if v and "_mod_" not in k]
        self._log(f"[RAC] _apply_player_inventory_sync: writing {len(unlocked)} AP weapons: {unlocked}")
        if WEAPONS:
            self._player_weapon_state.give(self.pine)
            for name, level in self._gs.tracked_weapon_levels.items():
                if name in WEAPONS:
                    self.pine.write_int32(WEAPONS[name].level, level)
        if GADGETS:
            self._player_gadget_state.give(self.pine)

    # ── Bonus weapon pickup ───────────────────────────────────────────────────

    def _grant_random_bonus_item(self, trigger_name: str) -> None:
        """Called when lacerator/acid_bomb_glove/concussion_gun transitions
        locked->unlocked in-game. Force-unlocks a random AP-unlocked weapon
        or gadget the player doesn't already have equipped on this planet."""
        if not self.pine_connected:
            return
        candidates: list[int] = []
        for name, unlocked in self._gs.tracked_weapons.items():
            if unlocked and name in WEAPONS and name != trigger_name:
                candidates.append(WEAPONS[name].unlocked)
        for name, unlocked in self._gs.tracked_gadgets.items():
            if unlocked and name in GADGETS:
                candidates.append(GADGETS[name].unlocked)
        if not candidates:
            return
        addr = random.choice(candidates)
        try:
            self.pine.write_int8(addr, 1)
        except Exception:
            pass

    # ── Notification helper ───────────────────────────────────────────────────

    def _write_notification_text(self, msg: bytes) -> None:
        if not self.pine_connected:
            return
        if self._wiring.is_in_menu or self._wiring.is_transitioning:
            return
        tb = _SMALL_BOX_BY_PLANET.get(self._prev_planet)
        if tb is None:
            return
        try:
            tb.write_text(self.pine, msg)
        except Exception:
            pass

    # ── Item notifications ────────────────────────────────────────────────────

    def _show_new_item_notifications(self) -> None:
        new_items = self.items_received[self._notification_item_index:]
        self._notification_item_index = len(self.items_received)
        if not new_items or not self.pine_connected:
            return
        net_item = new_items[-1]
        item_name   = self.item_names[self.game].get(net_item.item, "???")
        player_name = self.player_names.get(net_item.player, f"Player {net_item.player}")
        msg = colored_text(
            "Received ", TextColour.PURPLE, item_name,
            TextColour.WHITE, " from ", TextColour.ORANGE, player_name, TextColour.WHITE,
        )
        self._write_notification_text(msg)

    # ── Bolt items ────────────────────────────────────────────────────────────

    def _grant_new_bolt_items(self) -> None:
        new_items = self.items_received[self._processed_item_count:]
        self._processed_item_count = len(self.items_received)

        bolt_items_to_grant = 0
        starting_bolts = int(self.slot_data.get("starting_bolts", 0))
        for network_item in new_items:
            item_name = self.item_names[self.game].get(network_item.item, "")
            if item_name != "Bolts":
                continue
            if starting_bolts and not self._starting_bolts_granted:
                self._starting_bolts_granted = True
                if not self.pine_connected:
                    continue
                try:
                    current = self.pine.read_int32(PLAYER_BOLT_COUNT)
                    self.pine.write_int32(PLAYER_BOLT_COUNT, current + starting_bolts)
                except Exception as exc:
                    self._log(f"[RAC] Could not grant bolts: {exc}", "warning")
            else:
                bolt_items_to_grant += 1

        if bolt_items_to_grant <= 0 or not self.pine_connected:
            return
        try:
            current = self.pine.read_int32(PLAYER_BOLT_COUNT)
            for _ in range(bolt_items_to_grant):
                grant = min(200000, max(75000, int(current * 0.2)))
                current += grant
            self.pine.write_int32(PLAYER_BOLT_COUNT, current)
        except Exception as exc:
            self._log(f"[RAC] Could not grant bolts: {exc}", "warning")

    # ── Trap items ────────────────────────────────────────────────────────────

    def _grant_new_trap_items(self) -> None:
        new_items = self.items_received[self._processed_trap_count:]
        self._processed_trap_count = len(self.items_received)

        if not self.pine_connected:
            return
        for network_item in new_items:
            item_name = self.item_names[self.game].get(network_item.item, "")
            if item_name not in ALL_TRAPS:
                continue
            try:
                activate_trap(self.pine, item_name)
            except Exception as exc:
                self._log(f"[RAC] Could not activate trap {item_name!r}: {exc}", "warning")

    # ── World-state restore (crash recovery) ──────────────────────────────────

    def _seed_world_states(self) -> None:
        """Compute bolt and skill-point states from already-completed locations."""
        self._titanium_bolt_state.reset()
        self._skill_point_state.reset()
        checked = self.checked_locations | self._locally_checked_locations
        for loc_name, bolt in TITANIUM_BOLTS.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                self._titanium_bolt_state.add(bolt.delta)
        for loc_name, sp in SKILL_POINTS.items():
            loc_id = self._location_name_to_id.get(loc_name)
            if loc_id and loc_id in checked:
                self._skill_point_state.add(sp.mask)

    def _apply_world_states_sync(self) -> None:
        """Write bolt, skill-point, and infobot states to memory."""
        self._seed_world_states()
        new_bolt = self._titanium_bolt_state.apply_or(self.pine)
        self._prev_bolt_pickup = new_bolt & BOLT_PICKUP_MASK
        new_sp   = self._skill_point_state.apply_or(self.pine)
        self._prev_skill_points = new_sp
        # Write infobot-unlocked planet states (populated by _rebuild_player_inventory).
        self._planet_state.give(self.pine)
        # Force-unlock planets that have no collectible infobot in the AP world.
        for address in AUTO_UNLOCK_ADDRESSES:
            self.pine.write_int8(address, INFOBOT_UNLOCK_VALUE)
        self._log(
            f"[RAC] World state restored: {self._titanium_bolt_state!r}"
            f"  {self._skill_point_state!r}"
        )

    async def _restore_world_states(self) -> None:
        """Seed and apply bolt/skill-point states.  Called only on connection events."""
        if not self.pine_connected:
            return
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            await loop.run_in_executor(None, self._apply_world_states_sync)
