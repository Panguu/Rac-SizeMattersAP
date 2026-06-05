from __future__ import annotations

from ..core.data import ARMOUR_SET_CHECKS


class EventsHandlerMixin:
    def _on_armour_pickup_update(self, key: str, new_value: int) -> None:
        del key, new_value

    def _on_menu_close_for_armour_sets(self) -> None:
        if not self._armour_set_checks_enabled:
            return
        self._armour_slot_state.update(self.pine)
        slot_values = self._armour_slot_state.memory_values
        for name, check in ARMOUR_SET_CHECKS.items():
            if check.matches(slot_values):
                self._append_location_by_name(name)
