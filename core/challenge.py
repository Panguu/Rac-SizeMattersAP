from __future__ import annotations

from collections.abc import Callable

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data.challenges import ALL_CLANK_ADDRESS_MAP, CHALLENGE_ADDRESS_MAP


class ChallengePoller:
    """Polls challenge completion addresses each tick.

    Addresses start at 1 (available) and go to 3+ when completed.
    A transition where val > 2 and prev <= 2 fires the location-check callback once.

    mode 1 (item_challenges): polls reward addresses only (CHALLENGE_ADDRESS_MAP).
    mode 2 (all_challenges):  polls all individual challenge addresses (ALL_CLANK_ADDRESS_MAP).
    """

    def __init__(self, log: Callable[[str], None] | None = None) -> None:
        self._log  = log or logger.info
        self._prev: dict[int, int] = {}
        self._mode: int = 1

    def set_mode(self, mode: int) -> None:
        self._mode = mode

    def initialize(self) -> None:
        """Snapshot current game values into _prev so existing completions don't re-fire."""
        self._prev.clear()

    def write_defaults(self, ipc: Pine) -> None:
        """On first planet load: write 1 to every challenge address that is still 0
        (unavailable), making all challenges available. Updates _prev to match."""
        for addr in ALL_CLANK_ADDRESS_MAP:
            val = ipc.read_int8(addr)
            if val == 0:
                ipc.write_int8(addr, 1)
                val = 1
            self._prev[addr] = val

    def tick(self, ipc: Pine, new_checks: list[int], append_fn: Callable[[list[int], str, str], None]) -> None:
        addr_map = ALL_CLANK_ADDRESS_MAP if self._mode >= 2 else CHALLENGE_ADDRESS_MAP
        for addr, loc_name in addr_map.items():
            val  = ipc.read_int8(addr)
            prev = self._prev.get(addr, 1)
            if val >= 2 and prev < 2:
                logger.info(f"[RAC] Challenge completed: {loc_name} (addr=0x{addr:08X} val={val})")
                append_fn(new_checks, loc_name, "Challenge")
            self._prev[addr] = val

    def reset(self) -> None:
        """Clear tracked values on reconnect."""
        self._prev.clear()
