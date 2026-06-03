"""Armour slot check definitions for Ratchet & Clank: Size Matters.

Each armour slot (chestplate, helmet, gloves_left, gloves_right, boots_left, boots_right)
holds a uint8 value encoding which piece is currently equipped:

    slot_value = set_index + 1   (wildfire=1, sludge=2, crystallix=3, …)

    The slot address itself identifies the piece (chestplate/helmet/gloves/boots);
    the value only encodes which set is equipped in that slot. 0 means empty.

ArmourSetCheck describes the expected slot values for a location check.
None means "don't care" — that slot is not required by this check.
Gloves / boots are symmetric: both left and right must match the expected value.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ArmourSets(IntEnum):
    Wildfire     = 1
    Sludge       = 2
    Crystallix   = 3
    Electroshock = 4
    MegaBomb     = 5
    Hyperborean  = 6
    Chameleon    = 7


@dataclass(frozen=True)
class ArmourSetCheck:
    """Expected slot values for a single armour-equip location check.

    Only the slots set to a non-None value are tested.  This allows both full-set
    checks and single-piece checks (e.g. just helmet).

    Gloves and boots are symmetric — both left/right slots must match the value.
    """
    chestplate: int | None = None
    helmet:     int | None = None
    gloves:     int | None = None
    boots:      int | None = None

    def matches(self, slot_values: dict[str, int]) -> bool:
        """Return True when the current slot values satisfy every non-None field."""
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
