from __future__ import annotations

import struct as _struct
from collections.abc import Callable

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..data.addresses import CURRENT_PLANET_ADDRESS
from ..data.planets import Planets
from ..structs.cutscenes import (
    BeforeSproutCutsceneStruct,
    ElectroshockCutsceneStruct,
    GoalCutsceneStruct,
    SproutCutsceneStruct,
)


def _read_i32(accessor: MemoryAccessor, address: int) -> int:
    raw = accessor.read_raw(address, 4)
    return _struct.unpack_from("<i", raw)[0] if len(raw) >= 4 else 0


class CutsceneState(BaseState):
    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._prev_goal:         int = 0
        self._prev_electroshock: int = 0
        self._prev_before_sprout: int = 0
        self._prev_sprout:       int = 0

        self.on_goal:                Callable[[], None]       = lambda: None
        self.on_electroshock_gloves: Callable[[], None]       = lambda: None
        self.on_before_sprout:       Callable[[], None]       = lambda: None
        self.on_sprout_cutscene:     Callable[[], None]       = lambda: None

    def on_enter(self) -> None:
        self._prev_goal          = _read_i32(self.accessor, GoalCutsceneStruct.BASE_ADDRESS)
        self._prev_electroshock  = _read_i32(self.accessor, ElectroshockCutsceneStruct.BASE_ADDRESS)
        self._prev_before_sprout = _read_i32(self.accessor, BeforeSproutCutsceneStruct.BASE_ADDRESS)
        self._prev_sprout        = _read_i32(self.accessor, SproutCutsceneStruct.BASE_ADDRESS)

    def on_exit(self) -> None:
        pass

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(GoalCutsceneStruct,         self._on_goal_change)
        self.accessor.on_struct_change(ElectroshockCutsceneStruct, self._on_electroshock_change)
        self.accessor.on_struct_change(BeforeSproutCutsceneStruct, self._on_before_sprout_change)
        self.accessor.on_struct_change(SproutCutsceneStruct,       self._on_sprout_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(GoalCutsceneStruct,         self._on_goal_change)
        self.accessor.remove_struct_handler(ElectroshockCutsceneStruct, self._on_electroshock_change)
        self.accessor.remove_struct_handler(BeforeSproutCutsceneStruct, self._on_before_sprout_change)
        self.accessor.remove_struct_handler(SproutCutsceneStruct,       self._on_sprout_change)

    def _current_planet(self) -> int:
        raw = self.accessor.read_raw(CURRENT_PLANET_ADDRESS, 1)
        return raw[0] if raw else 0

    def _on_goal_change(self, address: int, new_bytes: bytes) -> None:
        del address
        val = _struct.unpack_from("<i", new_bytes)[0] if len(new_bytes) >= 4 else 0
        if self._prev_goal != 0 and val == 0 and self._current_planet() == Planets.QUODRONA.planet_id:
            self.on_goal()
        self._prev_goal = val

    def _on_electroshock_change(self, address: int, new_bytes: bytes) -> None:
        del address
        val = _struct.unpack_from("<i", new_bytes)[0] if len(new_bytes) >= 4 else 0
        if self._prev_electroshock != 0 and val == 0 and self._current_planet() == Planets.METALIS.planet_id:
            self.on_electroshock_gloves()
        self._prev_electroshock = val

    def _on_before_sprout_change(self, address: int, new_bytes: bytes) -> None:
        del address
        val = _struct.unpack_from("<i", new_bytes)[0] if len(new_bytes) >= 4 else 0
        if self._prev_before_sprout != 0 and val == 0 and self._current_planet() == Planets.RYLLUS.planet_id:
            self.on_before_sprout()
        self._prev_before_sprout = val

    def _on_sprout_change(self, address: int, new_bytes: bytes) -> None:
        del address
        val = _struct.unpack_from("<i", new_bytes)[0] if len(new_bytes) >= 4 else 0
        if self._prev_sprout != 0 and val == 0 and self._current_planet() == Planets.RYLLUS.planet_id:
            self.on_sprout_cutscene()
        self._prev_sprout = val

    def sync(self) -> None:
        self._prev_goal          = _read_i32(self.accessor, GoalCutsceneStruct.BASE_ADDRESS)
        self._prev_electroshock  = _read_i32(self.accessor, ElectroshockCutsceneStruct.BASE_ADDRESS)
        self._prev_before_sprout = _read_i32(self.accessor, BeforeSproutCutsceneStruct.BASE_ADDRESS)
        self._prev_sprout        = _read_i32(self.accessor, SproutCutsceneStruct.BASE_ADDRESS)

    def reset(self) -> None:
        self._prev_goal          = 0
        self._prev_electroshock  = 0
        self._prev_before_sprout = 0
        self._prev_sprout        = 0
