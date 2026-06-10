from __future__ import annotations

from ...interface_orchestrator.memory.base import MemoryInterface
from ...pypine.pypine.pine import Pine


class PineInterface(MemoryInterface):
    """
    This is a wrapper for Pine interface. 
    The Plan is to implement PSP interface here matchin Memory Interface and then swap out the Interface per game as There is very little logic differences in these games memory
    """

    def __init__(self, pine: Pine) -> None:
        self._pine = pine

    def read(self, address: int, size: int) -> bytes:
        return self._pine.read_bytes(address, size)

    def write(self, address: int, data: bytes) -> None:
        self._pine.write_bytes(address, data)

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass
