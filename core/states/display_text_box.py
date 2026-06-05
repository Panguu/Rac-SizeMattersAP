from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from ...interface_orchestrator.memory.accessor import MemoryAccessor
from ...interface_orchestrator.state.base_state import BaseState
from ...interface_orchestrator.storage.local import LocalStorage
from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.display_text import CountdownTimerStruct, VendorVisibilityStruct

if TYPE_CHECKING:
    from ..data.addresses import DisplayedTextBox

class DisplayedTextBoxState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.is_displayed: bool = False
        self._active_config: DisplayedTextBox | None = None

    def activate(self, config: DisplayedTextBox) -> None:
        self._active_config = config

    def deactivate(self) -> None:
        self._active_config = None
        self.is_displayed = False

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        self.is_displayed = False

    def _register_handlers(self) -> None:
        cls = self._countdown_struct()
        if cls is not None:
            self.accessor.on_struct_change(cls, self._on_countdown_change)

    def _unregister_handlers(self) -> None:
        cls = self._countdown_struct()
        if cls is not None:
            self.accessor.remove_struct_handler(cls, self._on_countdown_change)

    def _countdown_struct(self) -> type[CountdownTimerStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, CountdownTimerStruct) and cls is not CountdownTimerStruct:
                return cls
        return None

    def _on_countdown_change(self, address: int, new_bytes: bytes) -> None:
        del address
        if len(new_bytes) < 4:
            return
        timer = struct.unpack_from("<f", new_bytes)[0]
        was_displayed = self.is_displayed
        self.is_displayed = timer > 0
        if self.is_displayed and not was_displayed:
            self.on_text_box_shown()
        elif not self.is_displayed and was_displayed:
            self.on_text_box_hidden()

    def sync(self) -> None:
        cls = self._countdown_struct()
        if cls is None:
            return
        raw = self.accessor.read_raw(cls.BASE_ADDRESS, 4)
        if len(raw) < 4:
            return
        timer = struct.unpack_from("<f", raw)[0]
        self.is_displayed = timer > 0

    def on_text_box_shown(self) -> None:
        pass

    def on_text_box_hidden(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"DisplayedTextBoxState(is_displayed={self.is_displayed})"

class DisplayTextBoxState(BaseState):

    def __init__(
        self,
        accessor: MemoryAccessor,
        addresses: AddressMap,
        storage: LocalStorage,
    ) -> None:
        super().__init__(accessor, addresses, storage)
        self.is_vendor_prompt: bool    = False
        self._vendor_value: int        = 0
        self._active_config: DisplayedTextBox | None = None
        self.on_vendor_prompt_shown:  callable = lambda: None
        self.on_vendor_prompt_hidden: callable = lambda: None

    def activate(self, config: DisplayedTextBox) -> None:
        self._active_config = config
        self._vendor_value  = config.vendor_value

    def deactivate(self) -> None:
        self._active_config = None
        self.is_vendor_prompt = False

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        self.is_vendor_prompt = False

    def _register_handlers(self) -> None:
        cls = self._visibility_struct()
        if cls is not None:
            self.accessor.on_struct_change(cls, self._on_visibility_change)

    def _unregister_handlers(self) -> None:
        cls = self._visibility_struct()
        if cls is not None:
            self.accessor.remove_struct_handler(cls, self._on_visibility_change)

    def _visibility_struct(self) -> type[VendorVisibilityStruct] | None:
        for cls in self.addresses.structs():
            if issubclass(cls, VendorVisibilityStruct) and cls is not VendorVisibilityStruct:
                return cls
        return None

    def _on_visibility_change(self, address: int, new_bytes: bytes) -> None:
        del address
        if len(new_bytes) < 2:
            return
        raw = struct.unpack_from("<h", new_bytes)[0]
        was_prompt = self.is_vendor_prompt
        self.is_vendor_prompt = (raw == self._vendor_value)
        if self.is_vendor_prompt and not was_prompt:
            self.on_vendor_prompt_shown()
        elif not self.is_vendor_prompt and was_prompt:
            self.on_vendor_prompt_hidden()

    def sync(self) -> None:
        cls = self._visibility_struct()
        if cls is None:
            return
        raw_bytes = self.accessor.read_raw(cls.BASE_ADDRESS, 2)
        if len(raw_bytes) < 2:
            return
        raw = struct.unpack_from("<h", raw_bytes)[0]
        self.is_vendor_prompt = (raw == self._vendor_value)

    def __repr__(self) -> str:
        return f"DisplayTextBoxState(vendor_prompt={self.is_vendor_prompt})"
