from __future__ import annotations

import asyncio
import time
from typing import Any

from CommonClient import logger

from ..size_matters.data.addresses import PLAYER_ADDRS, PLAYER_HEALTH, PLAYER_STATE
from ..size_matters.data.planets import BY_ID as PLANETS_BY_ID


_DEATH_CAUSES: dict[int, str] = {
    0x29: "got eaten by a fish",
    0x2A: "was faded out of existance",
    0x2B: "got electrocuted",
    0x2C: "fell out of the world",
    0x2D: "met an untimely end",
    0x2E: "tried to swim in lava",
    0x2F: "died under mysterious circumstances",
}


def _dead(player_state: int) -> bool:
    return 0x29 <= player_state <= 0x2F


def _death_cause(player_state: int) -> str:
    return _DEATH_CAUSES.get(player_state, "died")


class DeathLinkMixin:
    def _send_death_link_from_sync(self, player_state: int) -> None:
        if not self._death_link_enabled:
            return
        now = time.time()
        if now - self._last_death_link < 1:
            return
        self._last_death_link = now
        source = self.auth or "Ratchet"
        planet_name = (
            PLANETS_BY_ID[self._gs.current_planet].name
            if self._gs.current_planet in PLANETS_BY_ID
            else "an unknown planet"
        )
        asyncio.create_task(
            self.send_msgs([
                {
                    "cmd": "Bounce",
                    "tags": ["DeathLink"],
                    "data": {
                        "time": now,
                        "source": source,
                        "cause": f"{source} {_death_cause(player_state)} on {planet_name} in Ratchet & Clank: Size Matters.",
                    },
                }
            ])
        )

    async def _receive_death_link(self, data: dict[str, Any]) -> None:
        if not self.pine_connected:
            return
        timestamp = float(data.get("time", 0))
        if timestamp and timestamp <= self._last_death_link:
            return
        self._last_death_link = max(timestamp, time.time())
        cause = data.get("cause")
        if cause:
            logger.info(f"[RAC] DeathLink received: {cause}")
        loop = asyncio.get_event_loop()
        async with self._pine_lock:
            await loop.run_in_executor(None, self._kill_player_sync)

    def _kill_player_sync(self) -> None:
        health_addr = PLAYER_ADDRS.get(self._prev_planet, (PLAYER_STATE, PLAYER_HEALTH))[1]
        self.pine.write_int16(health_addr, 0)
