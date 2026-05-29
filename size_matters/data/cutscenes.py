from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...pypine.pypine.pine import Pine


def arm_cutscenes(ipc: Pine, planet_id: int, label: str) -> None:
    for c in CUTSCENES:
        if c.planet_id == planet_id:
            ipc.write_int32(c.address, c.init_val)
            print(f"  Cutscene {label}: {c.name} @ {c.address:#010x} = {c.init_val:#04x}")


@dataclass(frozen=True)
class Cutscene:
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

CUTSCENES: list[Cutscene] = [
    Cutscene("End Boss", planet_id=0x0A, address=0x3D7FC8, kind="goal"),
]

# pokitaru
# vendor 4
# ryllus
# vendor 1
