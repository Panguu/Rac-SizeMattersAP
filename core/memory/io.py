from __future__ import annotations

from collections.abc import Callable, Iterable

from ...pypine.pypine.pine import Pine


class MemoryState:
    """Snapshot, clear, and restore a group of int8 memory addresses.

    Accepts a callable so addresses are evaluated lazily — useful when the
    underlying dict (e.g. WEAPONS) is populated after import time.
    """

    def __init__(self, get_addresses: Callable[[], Iterable[int]]) -> None:
        self._get_addresses = get_addresses
        self._saved: dict[int, int] = {}

    def save(self, ipc: Pine) -> None:
        self._saved = {addr: ipc.read_int8(addr) for addr in self._get_addresses()}

    def remove(self, ipc: Pine) -> None:
        for addr in self._get_addresses():
            ipc.write_int8(addr, 0)

    def take(self, ipc: Pine) -> None:
        addrs = list(self._get_addresses())
        self._saved = {addr: ipc.read_int8(addr) for addr in addrs}
        for addr in addrs:
            ipc.write_int8(addr, 0)

    def restore(self, ipc: Pine) -> None:
        if not self._saved:
            raise RuntimeError("restore() called before save()")
        for addr, val in self._saved.items():
            ipc.write_int8(addr, val)


class ItemScanner:
    """Detects items written by the game into memory during a pickup window.

    Addresses are evaluated lazily so the scanner works even when the
    underlying dicts (e.g. WEAPONS) are populated after import time.

    Typical usage:
        scanner.clear(ipc)   # on pickup_start: zero addresses for detection
        scanner.scan(ipc)    # on pickup_end:   read and fire on_detected
        scanner.clear(ipc)   # on pickup_end:   zero again before state restore
    """

    def __init__(
        self,
        get_items: Callable[[], dict[str, int]],
        on_detected: Callable[[str, int], None],
    ) -> None:
        self._get_items   = get_items
        self._on_detected = on_detected

    def clear(self, ipc: Pine) -> None:
        for addr in self._get_items().values():
            ipc.write_int8(addr, 0)

    def scan(self, ipc: Pine) -> None:
        for name, addr in self._get_items().items():
            val = ipc.read_int8(addr)
            if val:
                self._on_detected(name, val)
