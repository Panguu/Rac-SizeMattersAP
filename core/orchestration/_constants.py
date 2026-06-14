from __future__ import annotations

from ..data.planets import Planet, Planets

POLL_INTERVAL: float = 0.1

PLANET_NAMES: dict[int, str] = {
    p.planet_id: p.name
    for p in vars(Planets).values()
    if isinstance(p, Planet)
}
