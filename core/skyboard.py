from __future__ import annotations

from collections.abc import Callable

from CommonClient import logger

from ..pypine.pypine.pine import Pine
from .data.challenges import SKYBOARD_ADDRESS_MASK_MAP, SKYBOARD_UNLOCK_MASK


class SkyboardPoller:
    """Detects skyboard race completions via cumulative bitmask on a per-planet completed address.

    At first planet load, write_defaults() writes 1 to each unlock address to make
    all challenges available. Each tick, the completed address is polled and a location
    check fires when a new bit is set.
    """

    def __init__(self, log: Callable[[str], None] | None = None) -> None:
        self._log  = log or logger.info
        self._prev: dict[int, int] = {}

    def initialize(self, ipc: Pine) -> None:
        """Snapshot current completed-address values so existing completions don't re-fire."""
        for addr in {addr for addr, _ in SKYBOARD_ADDRESS_MASK_MAP}:
            self._prev[addr] = ipc.read_int8(addr)

    def write_defaults(self, ipc: Pine) -> None:
        """OR the full race-unlock bitmask into each planet's unlock address, then snapshot completed values."""
        for addr, full_mask in SKYBOARD_UNLOCK_MASK.items():
            current = ipc.read_int8(addr)
            if current | full_mask != current:
                ipc.write_int8(addr, current | full_mask)
        for addr in {addr for addr, _ in SKYBOARD_ADDRESS_MASK_MAP}:
            self._prev[addr] = ipc.read_int8(addr)

    def tick(self, ipc: Pine, new_checks: list[int], append_fn: Callable[[list[int], str, str], None]) -> None:
        unique: dict[int, int] = {}
        for addr, _ in SKYBOARD_ADDRESS_MASK_MAP:
            if addr not in unique:
                unique[addr] = ipc.read_int8(addr)

        for (addr, mask), loc_name in SKYBOARD_ADDRESS_MASK_MAP.items():
            val  = unique[addr]
            prev = self._prev.get(addr, 0)
            if (val & mask) and not (prev & mask):
                logger.info(f"[RAC] Skyboard completed: {loc_name} (addr={addr:#010x} val={val:#04x})")
                append_fn(new_checks, loc_name, "Skyboard")

        for addr, val in unique.items():
            self._prev[addr] = val
