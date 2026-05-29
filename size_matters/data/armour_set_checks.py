"""Armour slot check definitions for Ratchet & Clank: Size Matters.

Each armour slot (chestplate, helmet, gloves_left, gloves_right, boots_left, boots_right)
holds a uint8 value encoding which piece is currently equipped:

    slot_value = set_index * 4 + piece_index + 1

    Sets  (set_index): wildfire=0, sludge=1, crystallix=2, electroshock=3, mega_bomb=4
    Pieces(piece_index): chestplate=0, helmet=1, gloves=2, boots=3
    0 means the slot is empty.

ArmourSetCheck describes the expected slot values for a location check.
None means "don't care" — that slot is not required by this check.
Gloves / boots are symmetric: both left and right must match the expected value.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ── Slot value namespaces ──────────────────────────────────────────────────────

class Wildfire:
    Chestplate = 1   # 0*4 + 0 + 1
    Helmet     = 2   # 0*4 + 1 + 1
    Gloves     = 3   # 0*4 + 2 + 1
    Boots      = 4   # 0*4 + 3 + 1


class Sludge:
    Chestplate = 5   # 1*4 + 0 + 1
    Helmet     = 6   # 1*4 + 1 + 1
    Gloves     = 7   # 1*4 + 2 + 1
    Boots      = 8   # 1*4 + 3 + 1


class Crystallix:
    Chestplate = 9   # 2*4 + 0 + 1
    Helmet     = 10  # 2*4 + 1 + 1
    Gloves     = 11  # 2*4 + 2 + 1
    Boots      = 12  # 2*4 + 3 + 1


class Electroshock:
    Chestplate = 13  # 3*4 + 0 + 1
    Helmet     = 14  # 3*4 + 1 + 1
    Gloves     = 15  # 3*4 + 2 + 1
    Boots      = 16  # 3*4 + 3 + 1


class MegaBomb:
    Chestplate = 17  # 4*4 + 0 + 1
    Helmet     = 18  # 4*4 + 1 + 1
    Gloves     = 19  # 4*4 + 2 + 1
    Boots      = 20  # 4*4 + 3 + 1


class Hyperborean:
    Chestplate = 21  # 5*4 + 0 + 1
    Helmet     = 22  # 5*4 + 1 + 1
    Gloves     = 23  # 5*4 + 2 + 1
    Boots      = 24  # 5*4 + 3 + 1


class Chameleon:
    Chestplate = 25  # 6*4 + 0 + 1
    Helmet     = 26  # 6*4 + 1 + 1
    Gloves     = 27  # 6*4 + 2 + 1
    Boots      = 28  # 6*4 + 3 + 1


# ── Check definition ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ArmourSetCheck:
    """Expected slot values for a single armour-equip location check.

    Only the slots set to a non-None value are tested.  This allows both full-set
    checks and single-piece checks (e.g. just helmet).

    Gloves and boots are symmetric — both left/right slots must match the value.
    """
    chestplate: Optional[int] = None
    helmet:     Optional[int] = None
    gloves:     Optional[int] = None
    boots:      Optional[int] = None

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


# ── Check dictionary ───────────────────────────────────────────────────────────
# Keys are the AP location names.  Add or remove entries freely — each one
# becomes a location check when the option is enabled.

ARMOUR_SET_CHECKS: dict[str, ArmourSetCheck] = {
    # ── Full sets ──────────────────────────────────────────────────────────────
    "Equip Wildfire Armour Set": ArmourSetCheck(
        chestplate=Wildfire.Chestplate,
        helmet=Wildfire.Helmet,
        gloves=Wildfire.Gloves,
        boots=Wildfire.Boots,
    ),
    "Equip Wildburst Armour Set": ArmourSetCheck(
        chestplate=Wildfire.Chestplate,
        helmet=Sludge.Helmet,
        gloves=Wildfire.Gloves,
        boots=Wildfire.Boots,
    ),
    "Equip Sludge Mk9 Armour Set": ArmourSetCheck(
        chestplate=Sludge.Chestplate,
        helmet=Sludge.Helmet,
        gloves=Sludge.Gloves,
        boots=Sludge.Boots,
    ),
    "Equip Crystallix Armour Set": ArmourSetCheck(
        chestplate=Crystallix.Chestplate,
        helmet=Crystallix.Helmet,
        gloves=Crystallix.Gloves,
        boots=Crystallix.Boots,
    ),
    "Equip Triple Wave Armour Set": ArmourSetCheck(
        chestplate=Electroshock.Chestplate,
        helmet=Wildfire.Helmet,
        gloves=Sludge.Gloves,
        boots=Electroshock.Boots,
    ),
    "Equip Shock Crystal Armour Set": ArmourSetCheck(
        chestplate=Crystallix.Chestplate,
        helmet=Electroshock.Helmet,
        gloves=Crystallix.Gloves,
        boots=Electroshock.Boots,
    ),
    "Equip Electroshock Armour Set": ArmourSetCheck(
        chestplate=Electroshock.Chestplate,
        helmet=Electroshock.Helmet,
        gloves=Electroshock.Gloves,
        boots=Electroshock.Boots,
    ),
    "Equip Mega Bomb Armour Set": ArmourSetCheck(
        chestplate=MegaBomb.Chestplate,
        helmet=MegaBomb.Helmet,
        gloves=MegaBomb.Gloves,
        boots=MegaBomb.Boots,
    ),
    "Equip Fire-Bomb Armour Set": ArmourSetCheck(
        chestplate=MegaBomb.Chestplate,
        helmet=MegaBomb.Helmet,
        gloves=Wildfire.Gloves,
        boots=MegaBomb.Boots,
    ),
    "Equip Hyperborean Armour Set": ArmourSetCheck(
        chestplate=Hyperborean.Chestplate,
        helmet=Hyperborean.Helmet,
        gloves=Hyperborean.Gloves,
        boots=Hyperborean.Boots,
    ),
    "Equip Ice II Armour Set": ArmourSetCheck(
        chestplate=Hyperborean.Chestplate,
        helmet=Crystallix.Helmet,
        gloves=Hyperborean.Gloves,
        boots=Hyperborean.Boots,
    ),
    "Equip Chameleon Armour Set": ArmourSetCheck(
        chestplate=Chameleon.Chestplate,
        helmet=Chameleon.Helmet,
        gloves=Chameleon.Gloves,
        boots=Chameleon.Boots,
    ),
    "Equip Stalker Armour Set": ArmourSetCheck(
        chestplate=Chameleon.Chestplate,
        helmet=Wildfire.Helmet,
        gloves=Sludge.Gloves,
        boots=Chameleon.Boots,
    ),
}
