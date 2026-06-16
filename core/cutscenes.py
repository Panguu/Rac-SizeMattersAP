from __future__ import annotations

import struct as _struct
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..interface_orchestrator.memory.accessor import MemoryAccessor
from ..interface_orchestrator.state.base_state import BaseState
from ..interface_orchestrator.storage.local import LocalStorage
from ..interface_orchestrator.structs.address_map import AddressMap
from .address_maps import CURRENT_PLANET_ADDRESS
from .planets import Planets
from .structs.game import (
    BeforeSproutCutsceneStruct,
    ElectroshockCutsceneStruct,
    GoalCutsceneStruct,
    SproutCutsceneStruct,
)

if TYPE_CHECKING:
    from ..pypine.pypine.pine import Pine


# ── Data ────────────────────────────────────────────────────────────────────────

def arm_cutscenes(ipc: Pine, planet_id: int, label: str) -> None:
    from CommonClient import logger
    for c in CUTSCENES:
        if c.planet_id == planet_id:
            ipc.write_int32(c.address, c.init_val)
            logger.debug(f"  Cutscene {label}: {c.name} @ {c.address:#010x} = {c.init_val:#04x}")


def suppress_disabled_cutscenes(ipc: Pine, planet_id: int) -> None:
    """Force all 'disabled' cutscene addresses to 0 for the given planet.

    Called on pickup start and pickup end so the game cannot trigger a
    disabled cutscene during the pickup animation window.
    """
    for c in CUTSCENES:
        if c.planet_id == planet_id and c.kind == "disabled":
            ipc.write_int32(c.address, 0x00)


@dataclass(frozen=True)
class Cutscene:
    """
    Data record for a cutscene in game.
    This is used for preventing and tracking cutscenes that are relevant to the randomizer.
    Cutscenes can only be monitored once the planet is loaded in memory.
    """
    name:      str
    planet_id: int   # planet the cutscene belongs to
    address:   int   # memory address to monitor; goes to 0 when cutscene has played
    kind:      str   # "pickup" — draw a bag reward | "goal" — randomizer complete
    init_val:  int   = 0x01  # value written to address on planet arrival
ENTER_CUTSCENES: dict[str, int] = {
    "pokitaru": 0xF3F250,
    "ryllus":   0xF3B6D0,
    "kalidon":  0x00F56DD0,
}

# Ryllus Sprout-O-Matic sequence (addresses imported from .structs.game above):
#   CUTSCENE_BEFORE_SPROUT_O_MATIC → goes to 0 first → fire AP location check
#   SPROUT_O_MATIC_CUTSCENE        → goes to 0 second → game gifts Sprout-O-Matic;
#                                     remove it from inventory if not yet received via AP
POKITARU_RYLLUS_ALT_TRIGGER:        int = 0x2F9CC6  # releases Ryllus when it changes from 0x00 to any value

CUTSCENES: list[Cutscene] = [
    Cutscene("End Boss",                           planet_id=0x0A, address=0x3D7FC8,  kind="goal"),
    Cutscene("Electroshock Gloves",                planet_id=0x04, address=0x1CE9C0,  kind="pickup"),
    Cutscene("Disable Pokitaru Complete Cutscene", planet_id=0x01, address=0x2CC454,  kind="disabled", init_val=0x00),
    # Cutscene("Disable Kalidon Complete Cutscene", planet_id=0x03, address=0xF52BD9, kind="disabled", init_val=0x00),
]

# pokitaru
# vendor 4
# ryllus
# vendor 1


# ── State (runtime) ──────────────────────────────────────────────────────────────

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
