from __future__ import annotations

from dataclasses import dataclass

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.skill_points import SkillPointsStruct


@dataclass(frozen=True)
class SkillPoint:
    planet_id: int
    bit:       int
    region:    str

    @property
    def mask(self) -> int:
        return 1 << self.bit

SKILL_POINTS: dict[str, SkillPoint] = {
    "Train Faster (SP)":                  SkillPoint(0x01,  0, "Pokitaru"),
    "Dont Rock The Boat (SP)":            SkillPoint(0x01,  1, "Pokitaru"),
    "Do Cows Get Crabby (SP)":            SkillPoint(0x01,  2, "Pokitaru"),
    "Bury The Pygmies (SP)":              SkillPoint(0x02,  4, "Ryllus"),
    "Lights Camera Action (SP)":          SkillPoint(0x02,  5, "Ryllus"),
    "Ship It (SP)":                       SkillPoint(0x02,  6, "Ryllus"),
    "Explosive Ordnance Disposal (SP)":   SkillPoint(0x03,  8, "Kalidon"),
    "Super Lombax (SP)":                  SkillPoint(0x03,  9, "Kalidon"),
    "Be A Cool Skyboarder (SP)":          SkillPoint(0x03, 10, "Kalidon"),
    "Shutout (SP)":                       SkillPoint(0x04, 12, "Metalis"),
    "Terror of the Skies (SP)":           SkillPoint(0x04, 13, "Metalis"),
    "Ultimate Gladiator (SP)":            SkillPoint(0x04, 14, "Metalis"),
    "Friends Dont Hurt Friends (SP)":     SkillPoint(0x05, 16, "Dreamtime"),
    "Night Terrors (SP)":                 SkillPoint(0x05, 17, "Dreamtime"),
    "Be An Awesome Skyboarder (SC)":      SkillPoint(0x06, 20, "Outpost Omega"),
    "High Tech Weapons Master (SP)":      SkillPoint(0x07, 25, "Challax"),
    "No More Varmints (SP)":              SkillPoint(0x07, 26, "Challax"),
    "Ultimate Gladiator Dayni Moon (SP)": SkillPoint(0x08, 28, "Dayni Moon"),
    "Wool Protest (SP)":                  SkillPoint(0x08, 29, "Dayni Moon"),
    "Bouncy Bouncy Bouncy (SP)":          SkillPoint(0x08, 30, "Dayni Moon"),
    "Not The Shock of Me Now (SP)":       SkillPoint(0x09, 32, "Inside Clank"),
    "Ratchet Just Ratchet (SP)":          SkillPoint(0x09, 33, "Inside Clank"),
    "Elite Annihilation (SP)":            SkillPoint(0x0A, 36, "Quodrona"),
    "Storm The Front (SP)":               SkillPoint(0x0A, 37, "Quodrona"),
}

CHALLENGE_SKILL_POINTS: frozenset[str] = frozenset({
    "Be A Cool Skyboarder (SP)",
    "Shutout (SP)",
    "Terror of the Skies (SP)",
    "Ultimate Gladiator (SP)",
    "Ultimate Gladiator Dayni Moon (SP)",
    "Be An Awesome Skyboarder (SC)",
    "No More Varmints (SP)",
})

SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}

SKILL_POINT_ADDRESS = SkillPointsStruct.BASE_ADDRESS

class SkillPointState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._bits:        int = 0
        self._synced_mask: int = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(SkillPointsStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(SkillPointsStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        instance = SkillPointsStruct.from_bytes(new_bytes)
        current  = instance.bitmask
        newly_set = current & ~self._bits
        self._bits = current
        if newly_set:
            for name, sp in SKILL_POINTS.items():
                if newly_set & sp.mask:
                    self.on_skill_point_earned(name)

    def sync(self) -> None:
        instance = self.accessor.read_struct(SkillPointsStruct)
        self._bits = instance.bitmask
        new_val = instance.bitmask | self._synced_mask
        if new_val != instance.bitmask:
            instance.bitmask = new_val
            self.accessor.write_struct(instance)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        mask = 0
        for name, sp in SKILL_POINTS.items():
            if name in checked_locations:
                mask |= sp.mask
        self._synced_mask = mask

    def on_skill_point_earned(self, _name: str) -> None:
        del _name

    def __repr__(self) -> str:
        earned = bin(self._bits).count("1")
        return f"SkillPointState(earned={earned}/{len(SKILL_POINTS)})"
