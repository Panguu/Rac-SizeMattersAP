from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..memory.accessor import MemoryAccessor
    from ..structs.address_map import AddressMap
    from ..storage.local import LocalStorage

class BaseState(ABC):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        self.accessor = accessor
        self.addresses = addresses
        self.storage = storage

    def set_addresses(self, addresses: AddressMap) -> None:
        self._unregister_handlers()
        self.addresses = addresses
        if self._active:
            self._register_handlers()

    _active: bool = False

    def enter(self) -> None:
        self._active = True
        self._register_handlers()
        self.on_enter()

    def exit(self) -> None:
        self._active = False
        self._unregister_handlers()
        self.on_exit()

    @abstractmethod
    def on_enter(self) -> None:
        ...

    @abstractmethod
    def on_exit(self) -> None:
        ...

    @abstractmethod
    def _register_handlers(self) -> None:
        ...

    @abstractmethod
    def _unregister_handlers(self) -> None:
        ...

    @abstractmethod
    def sync(self) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(active={self._active})"
