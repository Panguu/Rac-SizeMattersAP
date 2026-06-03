from __future__ import annotations

from ..core.data import (
    ARMOUR_FLAG_TO_LOCATION,
    ARMOUR_SET_CHECKS,
    ArmourPiece,
    arm_cutscenes,
    suppress_disabled_cutscenes,
)
from .deathlink import _death_cause


class EventsHandlerMixin:
    def _on_player_death(self, player_state: int) -> None:
        self._gs.is_dead = True
        self._gs.is_picking_up = False
        self._death_count += 1
        amnesty = int(self.slot_data.get("death_amnesty", 1))
        cause = _death_cause(player_state)
        arm_cutscenes(self.pine, self._gs.current_planet, "reset")
        # Death start: zero out then apply physical pickups.
        self._armour_pickup_state.remove(self.pine)
        self._armour_pickup_state.give(self.pine)
        self._log(
            f"[RAC] Death start — applied pickup={self._armour_pickup_state!r}"
            f"  (AP={self._player_armour_state!r} on respawn)"
        )
        if self._death_count > amnesty:
            self._log(
                f"[RAC] Death {self._death_count} (Ratchet {cause}): amnesty exceeded ({amnesty}), DeathLink sent."
            )
            self._send_death_link_from_sync(player_state)
        else:
            self._log(f"[RAC] Death {self._death_count} (Ratchet {cause}): within amnesty ({amnesty}).")

    def _on_player_respawn(self) -> None:
        self._gs.is_dead = False
        arm_cutscenes(self.pine, self._gs.current_planet, "armed")
        self._armour_pickup_state.remove(self.pine)
        self._apply_player_inventory_sync()
        self._log(
            f"[RAC] Death end — applied AP={self._player_armour_state!r}"
            f"  pickup={self._armour_pickup_state!r}"
        )

    def _on_pickup_start(self) -> None:
        self._gs.is_picking_up = True
        suppress_disabled_cutscenes(self.pine, self._gs.current_planet)
        self._armour_slot_state.take(self.pine)
        self._armour_pickup_state.take(self.pine)

    def _on_menu_close(self, new_checks: list[int]) -> None:
        if not self._armour_set_checks_enabled:
            return
        self._armour_slot_state.update(self.pine)
        slot_values = self._armour_slot_state.memory_values
        for name, check in ARMOUR_SET_CHECKS.items():
            if check.matches(slot_values):
                self._append_location(new_checks, name, "Armour set")

    def _on_pickup_end(self, new_checks: list[int]) -> None:
        self._gs.is_picking_up = False
        suppress_disabled_cutscenes(self.pine, self._gs.current_planet)
        self._armour_pickup_state.update(self.pine)
        for loc_name in self._pending_armour_pickup_locs:
            self._append_location(new_checks, loc_name, "Armour")
        self._pending_armour_pickup_locs.clear()
        self._armour_pickup_state.restore(self.pine)
        self._armour_slot_state.restore(self.pine)

    def _on_armour_pickup_update(self, key: str, new_value: int) -> None:
        """Callback fired by _armour_pickup_state.update() when the game writes
        to an armour-set address during a pickup window.

        Accumulates the new piece into the pickup state, syncs the player state,
        and queues the corresponding AP location name so _on_pickup_end can
        append it to new_checks.
        """
        old = self._armour_pickup_state.get(key)
        new_bits = new_value & ~old
        self._armour_pickup_state.add(key, old | new_value)
        self._sync_game_state_inventory()
        for piece in (ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS):
            if new_bits & piece:
                loc_name = ARMOUR_FLAG_TO_LOCATION.get((key, piece))
                if loc_name:
                    self._pending_armour_pickup_locs.append(loc_name)
