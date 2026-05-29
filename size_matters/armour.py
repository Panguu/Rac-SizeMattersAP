from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag


class ArmourAddresses:
    """Resolves all armour field addresses from a single base address.

    Layout (identical on PSP and PS2):
      +0x00  chestplate slot
      +0x01  helmet slot
      +0x02  gloves_left slot
      +0x03  gloves_right slot
      +0x04  boots_left slot
      +0x05  boots_right slot
      +0x06  wildfire set
      +0x07  sludge set
      +0x08  crystallix set
      +0x09  electroshock set
      +0x0A  mega_bomb set
      +0x0B  hyperborean set
      +0x0C  chameleon set
    """

    _SLOT_OFFSETS: dict[str, int] = {
        "chestplate":   0x00,
        "helmet":       0x01,
        "gloves_left":  0x02,
        "gloves_right": 0x03,
        "boots_left":   0x04,
        "boots_right":  0x05,
    }

    _SET_OFFSETS: dict[str, int] = {
        "wildfire":     0x06,
        "sludge":       0x07,
        "crystallix":   0x08,
        "electroshock": 0x09,
        "mega_bomb":    0x0A,
        "hyperborean":  0x0B,
        "chameleon":    0x0C,
    }

    def __init__(self, base: int) -> None:
        self.base = base
        for name, offset in {**self._SLOT_OFFSETS, **self._SET_OFFSETS}.items():
            setattr(self, name, base + offset)

    @property
    def slots(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in self._SLOT_OFFSETS}

    @property
    def sets(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in self._SET_OFFSETS}


class ArmourPiece(IntFlag):
    NONE       = 0
    CHESTPLATE = 0x01
    HELMET     = 0x02
    GLOVES     = 0x04
    BOOTS      = 0x10
    ALL        = 0x17


@dataclass(frozen=True)
class PlayerArmour:
    pieces: ArmourPiece

    @classmethod
    def from_value(cls, value: int) -> PlayerArmour:
        return cls(pieces=ArmourPiece(value))

    @property
    def chestplate(self) -> bool:
        return ArmourPiece.CHESTPLATE in self.pieces

    @property
    def helmet(self) -> bool:
        return ArmourPiece.HELMET in self.pieces

    @property
    def gloves(self) -> bool:
        return ArmourPiece.GLOVES in self.pieces

    @property
    def boots(self) -> bool:
        return ArmourPiece.BOOTS in self.pieces

    def has(self, piece: ArmourPiece) -> bool:
        return piece in self.pieces

    def with_piece(self, piece: ArmourPiece) -> PlayerArmour:
        return PlayerArmour(self.pieces | piece)

    def without_piece(self, piece: ArmourPiece) -> PlayerArmour:
        return PlayerArmour(self.pieces & ~piece)

    def to_value(self) -> int:
        return int(self.pieces)

    def __repr__(self) -> str:
        return f"PlayerArmour({self.pieces!r})"
