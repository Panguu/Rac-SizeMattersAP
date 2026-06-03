import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine

SKILL_POINT_ADDRESS = 0x21F4B437


@dataclass(frozen=True)
class SkillPoint:
    planet_id: int  # used with mask for detection context
    bit:       int
    region:    str

    @property
    def mask(self) -> int:
        return 1 << self.bit



SKILL_POINTS: dict[str, SkillPoint] = {
    # Pokitaru
    "Train Faster (SP)":                  SkillPoint(0x01,  0, "Pokitaru"),
    "Dont Rock The Boat (SP)":            SkillPoint(0x01,  1, "Pokitaru"),
    "Do Cows Get Crabby (SP)":            SkillPoint(0x01,  2, "Pokitaru"),
    # Ryllus
    "Bury The Pygmies (SP)":              SkillPoint(0x02,  4, "Ryllus"),
    "Lights Camera Action (SP)":          SkillPoint(0x02,  5, "Ryllus"),
    "Ship It (SP)":                       SkillPoint(0x02,  6, "Ryllus"),
    # Kalidon
    "Explosive Ordnance Disposal (SP)":   SkillPoint(0x03,  8, "Kalidon"),
    "Super Lombax (SP)":                  SkillPoint(0x03,  9, "Kalidon"),
    "Be A Cool Skyboarder (SP)":          SkillPoint(0x03, 10, "Kalidon"),
    # Metalis
    "Shutout (SP)":                       SkillPoint(0x04, 12, "Metalis"),
    "Terror of the Skies (SP)":           SkillPoint(0x04, 13, "Metalis"),
    "Ultimate Gladiator (SP)":            SkillPoint(0x04, 14, "Metalis"),
    # Dreamtime
    "Friends Dont Hurt Friends (SP)":     SkillPoint(0x05, 16, "Dreamtime"),
    "Night Terrors (SP)":                 SkillPoint(0x05, 17, "Dreamtime"),
    # Outpost Omega
    "Be An Awesome Skyboarder (SC)":      SkillPoint(0x06, 20, "Outpost Omega"),
    # Challax
    # "Take Them Down A Shock (SP)": SkillPoint(0x07, 24, "Challax")
    # Excluded: only one opportunity to complete this in the whole game (bit 24).
    "High Tech Weapons Master (SP)":      SkillPoint(0x07, 25, "Challax"),
    "No More Varmints (SP)":              SkillPoint(0x07, 26, "Challax"),
    # Dayni Moon
    "Ultimate Gladiator Dayni Moon (SP)": SkillPoint(0x08, 28, "Dayni Moon"),
    "Wool Protest (SP)":                  SkillPoint(0x08, 29, "Dayni Moon"),
    "Bouncy Bouncy Bouncy (SP)":          SkillPoint(0x08, 30, "Dayni Moon"),
    # Inside Clank
    "Not The Shock of Me Now (SP)":       SkillPoint(0x09, 32, "Inside Clank"),
    "Ratchet Just Ratchet (SP)":          SkillPoint(0x09, 33, "Inside Clank"),
    # Quodrona
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

# (planet_id, mask) → location name — mirrors BOLT_BY_PLANET_AND_DELTA
SKILL_POINT_BY_PLANET_AND_MASK: dict[tuple[int, int], str] = {
    (sp.planet_id, sp.mask): name
    for name, sp in SKILL_POINTS.items()
}

# Flat mask lookup used by the client (bits are globally unique so planet not needed for detection)
LOCATION_SKILL_POINTS: dict[str, int] = {
    name: sp.mask for name, sp in SKILL_POINTS.items()
}


class SkillPointState(State):
    """
    Global skill point tracker. Reads a fixed int64 bitmask and fires
    on_skill_point_earned() when a new bit is set. No planet-specific addresses.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self._bits: int = 0
        self._synced_mask: int = 0
        self._task: asyncio.Task | None = None

    # --- State interface ---

    async def read(self) -> bool:
        async with self._lock:
            self._bits = self.pine.read_int64(SKILL_POINT_ADDRESS)
        return True

    async def apply(self) -> bool:
        """OR the AP-confirmed skill point bits into memory, preserving any the game set."""
        async with self._lock:
            current = self.pine.read_int64(SKILL_POINT_ADDRESS)
            new_val = current | self._synced_mask
            if new_val != current:
                self.pine.write_int64(SKILL_POINT_ADDRESS, new_val)
        return True

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        """Rebuild _synced_mask from AP-confirmed checked skill-point locations."""
        mask = 0
        for name, sp in SKILL_POINTS.items():
            if name in checked_locations:
                mask |= sp.mask
        self._synced_mask = mask

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback
        last: int = 0
        while True:
            async with self._lock:
                current = self.pine.read_int64(SKILL_POINT_ADDRESS)
            newly_set = current & ~last
            if newly_set:
                for name, sp in SKILL_POINTS.items():
                    if newly_set & sp.mask:
                        self.on_skill_point_earned(name)
            last = current
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

    def on_skill_point_earned(self, _name: str) -> None:
        """Fired when a skill point is newly earned."""
        del _name

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SkillPointState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        earned = bin(self._bits).count("1")
        return f"SkillPointState(earned={earned}/{len(SKILL_POINTS)})"
