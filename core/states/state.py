import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable

from worlds.rac_size_matters.pypine.pypine.pine import Pine


class State(ABC):
    _lock: asyncio.Lock = asyncio.Lock()
    __hash__ = object.__hash__

    def __init__(self, pine: Pine):
        self.pine = pine

    @abstractmethod
    async def apply(self) -> bool: ...

    @abstractmethod
    async def read(self) -> bool: ...

    @abstractmethod
    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None: ...

    __hash__ = object.__hash__

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    @abstractmethod
    def __repr__(self) -> str: ...


class State8(State):
    def __init__(self, pine: Pine, addr: int):
        super().__init__(pine)
        self.addr = addr
        self.value: int = 0

    async def read(self) -> bool:
        async with self._lock:
            self.value = self.pine.read_int8(self.addr)
        return True

    async def apply(self) -> bool:
        async with self._lock:
            self.pine.write_int8(self.addr, self.value)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: int | None = None
        while True:
            async with self._lock:
                current = self.pine.read_int8(mem_address)
            if last is not None and current != last:
                callback(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State8):
            return NotImplemented
        return self.addr == other.addr and self.value == other.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(addr={self.addr:#010x}, value={self.value})"


class State16(State):
    def __init__(self, pine: Pine, addr: int):
        super().__init__(pine)
        self.addr = addr
        self.value: int = 0

    async def read(self) -> bool:
        async with self._lock:
            self.value = self.pine.read_int16(self.addr)
        return True

    async def apply(self) -> bool:
        async with self._lock:
            self.pine.write_int16(self.addr, self.value)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: int | None = None
        while True:
            async with self._lock:
                current = self.pine.read_int16(mem_address)
            if last is not None and current != last:
                callback(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State16):
            return NotImplemented
        return self.addr == other.addr and self.value == other.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(addr={self.addr:#010x}, value={self.value})"


class State32(State):
    def __init__(self, pine: Pine, addr: int):
        super().__init__(pine)
        self.addr = addr
        self.value: int = 0

    async def read(self) -> bool:
        async with self._lock:
            self.value = self.pine.read_int32(self.addr)
        return True

    async def apply(self) -> bool:
        async with self._lock:
            self.pine.write_int32(self.addr, self.value)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: int | None = None
        while True:
            async with self._lock:
                current = self.pine.read_int32(mem_address)
            if last is not None and current != last:
                callback(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State32):
            return NotImplemented
        return self.addr == other.addr and self.value == other.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(addr={self.addr:#010x}, value={self.value})"


class State64(State):
    def __init__(self, pine: Pine, addr: int):
        super().__init__(pine)
        self.addr = addr
        self.value: int = 0

    async def read(self) -> bool:
        async with self._lock:
            self.value = self.pine.read_int64(self.addr)
        return True

    async def apply(self) -> bool:
        async with self._lock:
            self.pine.write_int64(self.addr, self.value)
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        last: int | None = None
        while True:
            async with self._lock:
                current = self.pine.read_int64(mem_address)
            if last is not None and current != last:
                callback(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State64):
            return NotImplemented
        return self.addr == other.addr and self.value == other.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(addr={self.addr:#010x}, value={self.value})"
