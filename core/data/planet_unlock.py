from dataclasses import dataclass

from .addresses import PLANET_STATE_OFFSET, PLANET_UNLOCK_ADDRESSES


@dataclass(frozen=True)
class PlanetUnlock:
    """
    Data record for a planet's unlock information.
    This is used for monitoring and modifying planet unlock states in the game.
    """

    unlock_addr:   int
    state_addr:    int
    default_state: int = 0  # minimum value always written to state_addr


_DEFAULT_STATES: dict[str, int] = {
    "DREAMTIME":     3,
    "OUTPOST_OMEGA": 3,
}

PLANET_UNLOCKS: dict[str, PlanetUnlock] = {
    name: PlanetUnlock(
        unlock_addr=addr,
        state_addr=addr + PLANET_STATE_OFFSET,
        default_state=_DEFAULT_STATES.get(name, 0),
    )
    for name, addr in PLANET_UNLOCK_ADDRESSES.items()
}
