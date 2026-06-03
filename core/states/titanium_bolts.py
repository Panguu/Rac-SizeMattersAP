import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine


class TitaniumBoltAddresses:
    """Resolves titanium bolt field addresses from a single base address.

    Layout (identical on PSP and PS2):
      +0x00  pickup  — increments each time a bolt is picked up
      +0x05  total   — cumulative bolt count
    """

    def __init__(self, base: int) -> None:
        self.base   = base
        self.pickup = base + 0x00
        self.total  = base + 0x05

@dataclass(frozen=True)
class TitaniumBolt:
    planet_id: int  # used with delta for unambiguous detection
    bit:       int  # bit position in the pickup int64
    region:    str  # AP region name

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

# (planet_id, delta) → location name — used by the client for unambiguous detection
BOLT_BY_PLANET_AND_DELTA: dict[tuple[int, int], str] = {
    (bolt.planet_id, bolt.delta): name
    for name, bolt in TITANIUM_BOLTS.items()
}


class TitaniumBoltState(State):
    """
    Global titanium bolt tracker. Reads a fixed-address int64 bitmask and fires
    on_bolt_collected() when a new bit is set. No planet-specific addresses.
    """

    def __init__(self, pine: Pine, base: int):
        super().__init__(pine)
        self._addrs       = TitaniumBoltAddresses(base)
        self._pickup:     int = 0
        self._synced_mask: int = 0
        self._poll_last:  int = 0
        self._task: asyncio.Task | None = None

    # --- State interface ---

    async def read(self) -> bool:
        async with self._lock:
            self._pickup = self.pine.read_int64(self._addrs.pickup)
        return True

    async def apply(self) -> bool:
        async with self._lock:
            current = self.pine.read_int64(self._addrs.pickup)
            new_val = current | self._synced_mask
            self.pine.write_int64(self._addrs.pickup, new_val)
            self._poll_last = new_val
        return True

    def sync_from_ap(self, checked_location_names: set[str]) -> None:
        """Rebuild _synced_mask from AP-confirmed checked bolt locations."""
        mask = 0
        for loc_name, bolt in TITANIUM_BOLTS.items():
            if loc_name in checked_location_names:
                mask |= bolt.delta
        self._synced_mask = mask

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        while True:
            async with self._lock:
                current = self.pine.read_int64(self._addrs.pickup)
            delta = current - self._poll_last
            self._poll_last = current
            if delta > 0 and (delta & (delta - 1)) == 0:
                self.on_bolt_delta(delta)
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(self, interval: int, callback: Callable[[int, int], None]) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self.poll(0, interval, callback))

    async def deactivate(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    # --- Hook ---

    def on_bolt_delta(self, _delta: int) -> None:
        """Fired with the arithmetic delta when a single new bolt is detected."""
        del _delta

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TitaniumBoltState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        collected = bin(self._poll_last).count("1")
        return f"TitaniumBoltState(collected={collected}/{len(TITANIUM_BOLTS)})"
