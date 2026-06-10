from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...pypine.pypine.pine import Pine


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

# Ryllus Sprout-O-Matic sequence:
#   CUTSCENE_BEFORE_SPROUT_O_MATIC → goes to 0 first → fire AP location check
#   SPROUT_O_MATIC_CUTSCENE        → goes to 0 second → game gifts Sprout-O-Matic;
#                                     remove it from inventory if not yet received via AP
CUTSCENE_BEFORE_SPROUT_O_MATIC: int = 0x5A7904
SPROUT_O_MATIC_CUTSCENE:        int = 0x5A6EA8

ELECTROSHOCK_GLOVES_CUTSCENE:       int = 0x1CE9C0
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
