from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag


class ArmourAddresses:
    """
    Armour Address Struct
    This is the layout of Armour in Static Memory
    Slot Offsets are the currently equiped armour pieces
    Set Offsets are the unlock addresses for the Armour
    We only need one read and one write to handle these addresses as they are next to eachother in memory
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
    """
    Armour pieces are represented as bits in a byte, with the following mapping:
    - Bit 0 (0x01): Chestplate
    - Bit 1 (0x02): Helmet
    - Bit 2 (0x04): Gloves
    - Bit 4 (0x10): Boots (any value with bit 4 set is considered to have boots equipped)
    """
    NONE       = 0
    CHESTPLATE = 0x01
    HELMET     = 0x02
    GLOVES     = 0x04
    BOOTS      = 0x10 # Boots changes it is any value with bit 4 set, this is because the game treats left and right boots as one piece, so any value with bit 4 set is considered to have boots equipped
    ALL        = 0x17


@dataclass(frozen=True)
class PlayerArmour:
    """
    Wrapper for armour piece bitmask.
    This sets up named boolean properties for each piece and helper methods for working with the bitmask.
    """
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
