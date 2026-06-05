from __future__ import annotations

import threading
import time

from .writer import MemoryWriter


class MemoryPoller:

    def __init__(self, writer: MemoryWriter, interval: float = 0.05) -> None:
        self._writer = writer
        self._interval = interval
        self._addresses: dict[int, int] = {}
        self._cache: dict[int, bytes] = {}
        self._thread: threading.Thread | None = None
        self._running = False

    def watch(self, address: int, size: int) -> None:
        self._addresses[address] = size

    def prime(self, address: int, size: int) -> None:
        self._addresses[address] = size
        try:
            self._cache[address] = self._writer.read(address, size)
        except Exception:
            self._cache.pop(address, None)

    def unwatch(self, address: int) -> None:
        self._addresses.pop(address, None)
        self._cache.pop(address, None)

    def clear(self) -> None:
        self._addresses.clear()
        self._cache.clear()

    def poll_once(self) -> None:
        for address, size in list(self._addresses.items()):
            try:
                current = self._writer.read(address, size)
            except Exception:
                continue

            if self._cache.get(address) != current:
                self._cache[address] = current
                self._writer.notify_change(address, current)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        while self._running:
            self.poll_once()
            time.sleep(self._interval)
