from __future__ import annotations

import asyncio
from functools import partial

from CommonClient import logger

from ..data import (
    CURRENT_PLANET_ADDRESS,
    CUTSCENES,
    SKILL_POINT_ADDRESS,
)
from ..memory import BOLTS
from ..state import GameState, PollAddress
from ..vendor import VendorPoller
from .checks import _on_bolt_pickup, _on_cutscene, _on_planet_change, _on_skill_point
from .death import _on_death, _on_respawn
from .locks import _enforce_locks
from .pickup import _build_scanners, _on_pickup_end, _on_pickup_start

_dead = lambda v: 0x29 <= v <= 0x2F


def build_pollers(gs: GameState) -> list:
    _state_read = lambda ipc, addr: ipc.read_int16(addr)
    _int32_read = lambda ipc, addr: ipc.read_int32(addr)
    _scanners   = _build_scanners(gs)

    return [
        PollAddress(CURRENT_PLANET_ADDRESS, partial(_on_planet_change, gs)),
        PollAddress(
            BOLTS.pickup,
            partial(_on_bolt_pickup, gs),
            trigger=lambda o, n: n > o,
            read_fn=lambda ipc, addr: ipc.read_int64(addr),
        ),
        PollAddress(
            SKILL_POINT_ADDRESS,
            partial(_on_skill_point, gs),
            trigger=lambda o, n: bool(n & ~o),
            read_fn=lambda ipc, addr: ipc.read_int64(addr),
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_death, gs),
            trigger=lambda o, n: not _dead(o) and _dead(n),
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_respawn, gs),
            trigger=lambda o, n: _dead(o) and n == 0x00,
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_pickup_start, gs, _scanners),
            trigger=lambda o, n: o != 0x43 and n == 0x43,
            read_fn=_state_read,
        ),
        PollAddress(
            lambda: gs.state_addr,
            partial(_on_pickup_end, gs, _scanners),
            trigger=lambda o, n: o == 0x43 and n == 0x00,
            read_fn=_state_read,
        ),
        VendorPoller(gs),
        *[
            PollAddress(
                c.address,
                partial(_on_cutscene, gs, c),
                trigger=lambda o, n: o != 0 and n == 0,
                read_fn=_int32_read,
            )
            for c in CUTSCENES
        ],
    ]


async def poll_loop(gs: GameState) -> None:
    pollers = build_pollers(gs)
    while not gs.goal_reached:
        await asyncio.sleep(0.5)
        try:
            for p in pollers:
                p.tick(gs.ipc)
            _enforce_locks(gs)
        except Exception as e:
            logger.warning(f"Poll error: {type(e).__name__}: {e}")
    logger.info("Polling stopped.")
