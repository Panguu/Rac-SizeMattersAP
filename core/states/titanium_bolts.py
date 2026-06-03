from __future__ import annotations

from dataclasses import dataclass

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.titanium_bolts import TitaniumBoltStruct


@dataclass(frozen=True)
class TitaniumBolt:
    planet_id: int
    bit:       int
    region:    str

    @property
    def delta(self) -> int:
        return 1 << self.bit

TITANIUM_BOLTS: dict[str, TitaniumBolt] = {
    "Pokitaru Above Zipline (TB)":                      TitaniumBolt(0x01,  0, "Pokitaru"),
    "Pokitaru Behind Hut (TB)":                         TitaniumBolt(0x01,  1, "Pokitaru"),
    "Ryllus Down The Cliff (TB)":                       TitaniumBolt(0x02,  4, "Ryllus"),
    "Ryllus After the Wall (TB)":                       TitaniumBolt(0x02,  5, "Ryllus"),
    "Kalidon Behind The Ship (TB)":                     TitaniumBolt(0x03,  8, "Kalidon"),
    "Kalidon Side of Mechanoid Factory (TB)":           TitaniumBolt(0x03, 10, "Kalidon"),
    "Kalidon Grav-Ramps (TB)":                          TitaniumBolt(0x03, 11, "Kalidon"),
    "Metalis Behind the Polarized Door (TB)":           TitaniumBolt(0x04, 12, "Metalis"),
    "Dreamtime Jump Across three moving parasols (TB)": TitaniumBolt(0x05, 16, "Dreamtime"),
    "Dreamtime To the left of Ratchets Garage (TB)":   TitaniumBolt(0x05, 17, "Dreamtime"),
    "Dreamtime Apparition of the Scuttle Crab (TB)":   TitaniumBolt(0x05, 18, "Dreamtime"),
    "Outpost Omega Near the Entrance to DreamTime (TB)":TitaniumBolt(0x06, 20, "Outpost Omega"),
    "Challax Beside The Ultra Mech Pad (TB)":           TitaniumBolt(0x07, 24, "Challax"),
    "Challax Hidden Room (TB)":                         TitaniumBolt(0x07, 25, "Challax"),
    "Challax Mimic Plant Lob (TB)":                     TitaniumBolt(0x07, 26, "Challax"),
    "Dayni Moon Planting at the Barnyard (TB)":         TitaniumBolt(0x08, 28, "Dayni Moon"),
    "Dayni Moon Bounce on the Blue mimic (TB)":         TitaniumBolt(0x08, 29, "Dayni Moon"),
    "Inside Clank Walk behind the ladder (TB)":         TitaniumBolt(0x09, 32, "Inside Clank"),
    "Inside Clank Wall jumping Technomite (TB)":        TitaniumBolt(0x09, 33, "Inside Clank"),
    "Quodrona Ratchet Clones and Dummies (TB)":         TitaniumBolt(0x0A, 36, "Quodrona"),
}

BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (bolt.planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
}

class TitaniumBoltState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self._poll_last:   int = 0
        self._synced_mask: int = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _register_handlers(self) -> None:
        self.accessor.on_struct_change(TitaniumBoltStruct, self._on_struct_change)

    def _unregister_handlers(self) -> None:
        self.accessor.remove_struct_handler(TitaniumBoltStruct, self._on_struct_change)

    def _on_struct_change(self, address: int, new_bytes: bytes) -> None:
        del address
        instance = TitaniumBoltStruct.from_bytes(new_bytes)
        current  = instance.pickup
        delta    = current - self._poll_last
        self._poll_last = current
        if delta > 0 and (delta & (delta - 1)) == 0:
            self.on_bolt_delta(delta)

    def sync(self) -> None:
        instance = self.accessor.read_struct(TitaniumBoltStruct)
        self._poll_last = instance.pickup
        new_val = instance.pickup | self._synced_mask
        if new_val != instance.pickup:
            instance.pickup = new_val
            self.accessor.write_struct(instance)

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        mask = 0
        for loc_name, bolt in TITANIUM_BOLTS.items():
            if loc_name in checked_location_names:
                mask |= bolt.delta
        self._synced_mask = mask

    def on_bolt_delta(self, _delta: int) -> None:
        del _delta

    def __repr__(self) -> str:
        collected = bin(self._poll_last).count("1")
        return f"TitaniumBoltState(collected={collected}/{len(TITANIUM_BOLTS)})"
