from __future__ import annotations

from CommonClient import logger

from ...pypine.pypine.pine import Pine
from ..data import (
    ARMOUR_BASE,
    TITANIUM_BOLT_BASE,
    WEAPON_MIN_CONSECUTIVE,
    WEAPON_STRUCT_SIZE,
    ArmourAddresses,
    ArmourPiece,
    GadgetAddresses,
    TitaniumBoltAddresses,
    WeaponAddresses,
    build_weapons,
    is_ps2_weapon_candidate,
)

WEAPONS: dict[str, WeaponAddresses] = {}
GADGETS: dict[str, GadgetAddresses] = {}

_armour              = ArmourAddresses(ARMOUR_BASE)
ARMOUR_ADDRESSES:    dict[str, int] = _armour.sets
PLAYER_ARMOUR_SLOTS: dict[str, int] = _armour.slots

BOLTS = TitaniumBoltAddresses(TITANIUM_BOLT_BASE)

_ARMOUR_PIECES = [ArmourPiece.CHESTPLATE, ArmourPiece.HELMET, ArmourPiece.GLOVES, ArmourPiece.BOOTS]
_PIECE_TO_SLOTS: dict[ArmourPiece, list[str]] = {
    ArmourPiece.CHESTPLATE: ["chestplate"],
    ArmourPiece.HELMET:     ["helmet"],
    ArmourPiece.GLOVES:     ["gloves_left", "gloves_right"],
    ArmourPiece.BOOTS:      ["boots_left", "boots_right"],
}
_ARMOUR_SET_ORDER = ["wildfire", "sludge", "crystallix", "electroshock", "mega_bomb", "hyperborean", "chameleon"]


def sync_weapons(ipc: Pine) -> None:
    SCAN_START  = 0x20F00000
    SCAN_LENGTH = 0x100000

    data  = ipc.read_bytes(SCAN_START, SCAN_LENGTH)
    limit = SCAN_LENGTH - WEAPON_STRUCT_SIZE * WEAPON_MIN_CONSECUTIVE
    for i in range(limit):
        if (SCAN_START + i) % 4 != 3:
            continue
        if not is_ps2_weapon_candidate(data, i):
            continue
        count = 1
        while count < WEAPON_MIN_CONSECUTIVE and is_ps2_weapon_candidate(data, i + count * WEAPON_STRUCT_SIZE):
            count += 1
        if count >= WEAPON_MIN_CONSECUTIVE:
            array_base = SCAN_START + i
            weapons, gadgets = build_weapons(array_base)
            WEAPONS.update(weapons)
            GADGETS.update(gadgets)
            logger.info(f"Weapon array at 0x{array_base:08X}")
            return
    logger.warning("Weapon scan: no consecutive structs found.")
