from __future__ import annotations

from collections.abc import Callable

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data.challenges import CHALLENGE_ADDRESS_MAP


class ChallengePoller:
    """Polls challenge completion addresses each tick.

    Each address in CHALLENGE_ADDRESS_MAP is an int8 that starts at 0 and goes to
    1+ when the challenge is completed.  A 0 → positive transition fires the
    location-check callback once.
    """

    def __init__(self, log: Callable[[str], None] | None = None) -> None:
        self._log  = log or logger.info
        self._prev: dict[int, int] = {}

    def tick(self, ipc: Pine, new_checks: list[int], append_fn: Callable[[list[int], str, str], None]) -> None:
        for addr, loc_name in CHALLENGE_ADDRESS_MAP.items():
            val  = ipc.read_int8(addr)
            prev = self._prev.get(addr, 0)
            if val > 0 and prev == 0:
                self._log(f"[RAC] Challenge completed: {loc_name}")
                append_fn(new_checks, loc_name, "Challenge")
            self._prev[addr] = val

    def reset(self) -> None:
        """Clear tracked values on reconnect / planet change."""
        self._prev.clear()
