from __future__ import annotations

import json

from CommonClient import logger

from ..size_matters.data.weapons import build_weapons
from ..size_matters.memory import GADGETS, WEAPONS
from ..size_matters.weapons import WEAPON_MIN_CONSECUTIVE, WEAPON_STRUCT_SIZE, is_ps2_weapon_candidate
from .constants import CACHE_FILE, WEAPON_SCAN_LENGTH, WEAPON_SCAN_START


class WeaponScannerMixin:
    def _sync_weapons_cached(self, force_scan: bool = False) -> bool:
        if not force_scan and WEAPONS and GADGETS:
            return True
        if not force_scan and self._load_weapon_cache():
            logger.info(f"[RAC] Weapon array loaded from cache at 0x{self._weapon_array_base:08X}.")
            return True
        return self._scan_weapon_array()

    def _load_weapon_cache(self) -> bool:
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
            array_base = int(data.get("weapon_array_base", 0))
        except Exception:
            return False
        if not array_base:
            return False
        try:
            probe = self.pine.read_bytes(array_base, WEAPON_STRUCT_SIZE * WEAPON_MIN_CONSECUTIVE)
        except Exception:
            return False
        if not all(
            is_ps2_weapon_candidate(probe, i * WEAPON_STRUCT_SIZE)
            for i in range(WEAPON_MIN_CONSECUTIVE)
        ):
            return False
        weapons, gadgets = build_weapons(array_base)
        WEAPONS.clear()
        GADGETS.clear()
        WEAPONS.update(weapons)
        GADGETS.update(gadgets)
        self._weapon_array_base = array_base
        return True

    def _scan_weapon_array(self) -> bool:
        logger.info("[RAC] Scanning PCSX2 memory for weapon array. This can take a moment.")
        try:
            data = self.pine.read_bytes(WEAPON_SCAN_START, WEAPON_SCAN_LENGTH)
        except TimeoutError:
            logger.warning("[RAC] Weapon scan timed out. Use /reconnect after the game is fully loaded.")
            return False
        limit = WEAPON_SCAN_LENGTH - WEAPON_STRUCT_SIZE * WEAPON_MIN_CONSECUTIVE
        for i in range(limit):
            if (WEAPON_SCAN_START + i) % 4 != 3:
                continue
            if not is_ps2_weapon_candidate(data, i):
                continue
            count = 1
            while count < WEAPON_MIN_CONSECUTIVE and is_ps2_weapon_candidate(data, i + count * WEAPON_STRUCT_SIZE):
                count += 1
            if count < WEAPON_MIN_CONSECUTIVE:
                continue
            array_base = WEAPON_SCAN_START + i
            weapons, gadgets = build_weapons(array_base)
            WEAPONS.clear()
            GADGETS.clear()
            WEAPONS.update(weapons)
            GADGETS.update(gadgets)
            self._weapon_array_base = array_base
            with open(CACHE_FILE, "w") as f:
                json.dump({"weapon_array_base": array_base}, f, indent=2)
            logger.info(f"[RAC] Weapon array at 0x{array_base:08X}.")
            return True
        logger.warning("[RAC] Weapon scan found no array. Weapon/gadget rewards will wait for /reconnect.")
        return False
