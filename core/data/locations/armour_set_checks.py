from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ArmourSets(IntEnum):
    """
    Enum representing different armour sets in the game.
    This is the value which is set in armour slots to represent what armour is currently equiped.
    """
    Wildfire     = 1
    Sludge       = 2
    Crystallix   = 3
    Electroshock = 4
    MegaBomb     = 5
    Hyperborean  = 6
    Chameleon    = 7


@dataclass(frozen=True)
class ArmourSetCheck:
    chestplate: int | None = None
    helmet:     int | None = None
    gloves:     int | None = None
    boots:      int | None = None

    def required_mask(self) -> int:
        mask = 0
        for val in {self.chestplate, self.helmet, self.gloves, self.boots} - {None}:
            mask |= 1 << (val - 1)
        return mask

    def matches(self, slot_values: dict[str, int]) -> bool:
        if self.chestplate is not None:
            if slot_values.get("chestplate", 0) != self.chestplate:
                return False
        if self.helmet is not None:
            if slot_values.get("helmet", 0) != self.helmet:
                return False
        if self.gloves is not None:
            if slot_values.get("gloves_left",  0) != self.gloves:
                return False
            if slot_values.get("gloves_right", 0) != self.gloves:
                return False
        if self.boots is not None:
            if slot_values.get("boots_left",  0) != self.boots:
                return False
            if slot_values.get("boots_right", 0) != self.boots:
                return False
        return True

ARMOUR_SET_CHECKS: dict[str, ArmourSetCheck] = {
    "Equip Wildfire Armour Set":      ArmourSetCheck(chestplate=ArmourSets.Wildfire,     helmet=ArmourSets.Wildfire,     gloves=ArmourSets.Wildfire,     boots=ArmourSets.Wildfire),
    "Equip Wildburst Armour Set":     ArmourSetCheck(chestplate=ArmourSets.Wildfire,     helmet=ArmourSets.Sludge,       gloves=ArmourSets.Wildfire,     boots=ArmourSets.Wildfire),
    "Equip Sludge Mk9 Armour Set":    ArmourSetCheck(chestplate=ArmourSets.Sludge,       helmet=ArmourSets.Sludge,       gloves=ArmourSets.Sludge,       boots=ArmourSets.Sludge),
    "Equip Crystallix Armour Set":    ArmourSetCheck(chestplate=ArmourSets.Crystallix,   helmet=ArmourSets.Crystallix,   gloves=ArmourSets.Crystallix,   boots=ArmourSets.Crystallix),
    "Equip Triple Wave Armour Set":   ArmourSetCheck(chestplate=ArmourSets.Electroshock, helmet=ArmourSets.Wildfire,     gloves=ArmourSets.Sludge,       boots=ArmourSets.Electroshock),
    "Equip Shock Crystal Armour Set": ArmourSetCheck(chestplate=ArmourSets.Crystallix,   helmet=ArmourSets.Electroshock, gloves=ArmourSets.Crystallix,   boots=ArmourSets.Electroshock),
    "Equip Electroshock Armour Set":  ArmourSetCheck(chestplate=ArmourSets.Electroshock, helmet=ArmourSets.Electroshock, gloves=ArmourSets.Electroshock, boots=ArmourSets.Electroshock),
    "Equip Mega Bomb Armour Set":     ArmourSetCheck(chestplate=ArmourSets.MegaBomb,     helmet=ArmourSets.MegaBomb,     gloves=ArmourSets.MegaBomb,     boots=ArmourSets.MegaBomb),
    "Equip Fire-Bomb Armour Set":     ArmourSetCheck(chestplate=ArmourSets.MegaBomb,     helmet=ArmourSets.MegaBomb,     gloves=ArmourSets.Wildfire,     boots=ArmourSets.MegaBomb),
    "Equip Hyperborean Armour Set":   ArmourSetCheck(chestplate=ArmourSets.Hyperborean,  helmet=ArmourSets.Hyperborean,  gloves=ArmourSets.Hyperborean,  boots=ArmourSets.Hyperborean),
    "Equip Ice II Armour Set":        ArmourSetCheck(chestplate=ArmourSets.Hyperborean,  helmet=ArmourSets.Crystallix,   gloves=ArmourSets.Hyperborean,  boots=ArmourSets.Hyperborean),
    "Equip Chameleon Armour Set":     ArmourSetCheck(chestplate=ArmourSets.Chameleon,    helmet=ArmourSets.Chameleon,    gloves=ArmourSets.Chameleon,    boots=ArmourSets.Chameleon),
    "Equip Stalker Armour Set":       ArmourSetCheck(chestplate=ArmourSets.Chameleon,    helmet=ArmourSets.Wildfire,     gloves=ArmourSets.Sludge,       boots=ArmourSets.Chameleon),
}

_HYBRID_BYTE1_BITS: dict[str, int] = {
    "Equip Shock Crystal Armour Set": 0x01,
    "Equip Wildburst Armour Set":     0x02,
    "Equip Triple Wave Armour Set":   0x04,
    "Equip Ice II Armour Set":        0x08,
    "Equip Stalker Armour Set":       0x10,
}

ARMOUR_SET_CHECK_MASKS: dict[str, int] = {
    name: (_HYBRID_BYTE1_BITS[name] << 8) if name in _HYBRID_BYTE1_BITS
          else check.required_mask()
    for name, check in ARMOUR_SET_CHECKS.items()
}
