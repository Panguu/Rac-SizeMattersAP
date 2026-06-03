import asyncio
from collections.abc import Callable
from enum import IntFlag

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine


class PauseSelectButtons(IntFlag):
    SELECT = 0x01
    START  = 0x08


class ControllerButtons(IntFlag):
    L1       = 0x01
    R1       = 0x02
    L2       = 0x04
    R2       = 0x08
    TRIANGLE = 0x10
    CIRCLE   = 0x20
    CROSS    = 0x40
    SQUARE   = 0x80


class ButtonState:
    """Snapshot of both controller bytes at a single point in time."""

    def __init__(self, pause_sel: int, buttons: int) -> None:
        self.pause_sel = PauseSelectButtons(pause_sel & 0xFF)
        self.buttons   = ControllerButtons(buttons & 0xFF)

    def pressed(self, *flags: PauseSelectButtons | ControllerButtons) -> bool:
        """Return True if every supplied flag is currently held."""
        for f in flags:
            if isinstance(f, PauseSelectButtons):
                if not (self.pause_sel & f):
                    return False
            else:
                if not (self.buttons & f):
                    return False
        return True

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ButtonState):
            return NotImplemented
        return self.pause_sel == other.pause_sel and self.buttons == other.buttons

    def __repr__(self) -> str:
        return f"ButtonState(pause_sel={self.pause_sel}, buttons={self.buttons})"


class ControllerState(State):
    """
    Global controller state. Polls planet-specific button addresses.
    Activated per-planet by PlanetState.on_enter() with that planet's addresses.
    Override on_input_change() to react to button events.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.current: ButtonState | None = None
        self._pause_sel_addr: int | None = None
        self._buttons_addr: int | None = None
        self._task: asyncio.Task | None = None

    # --- State interface ---

    async def read(self) -> bool:
        if self._pause_sel_addr is None or self._buttons_addr is None:
            return False
        async with self._lock:
            pause_sel = self.pine.read_int8(self._pause_sel_addr)
            buttons   = self.pine.read_int8(self._buttons_addr)
        self.current = ButtonState(pause_sel, buttons)
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address, callback  # ControllerState polls its own addresses; use on_input_change
        last: ButtonState | None = None
        while True:
            await self.read()
            current = self.current
            if current is not None and last is not None and current != last:
                self.on_input_change(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(
        self,
        pause_sel_addr: int,
        buttons_addr: int,
        interval: int,
        callback: Callable[[int, int], None],
    ) -> None:
        """Start polling. Called from PlanetState.on_enter()."""
        if self._task is not None:
            return
        self._pause_sel_addr = pause_sel_addr
        self._buttons_addr   = buttons_addr
        self._task = asyncio.create_task(self.poll(0, interval, callback))

    async def deactivate(self) -> None:
        """Stop polling. Called from PlanetState.on_exit()."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self.current = None

    # --- Convenience ---

    def pressed(self, *flags: PauseSelectButtons | ControllerButtons) -> bool:
        """Return True if every supplied flag is currently held."""
        return self.current.pressed(*flags) if self.current else False

    # --- Hook (override per use case) ---

    def on_input_change(self, _prev: ButtonState, _current: ButtonState) -> None:
        """Fired when any button state changes."""
        del _prev, _current

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ControllerState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        return f"ControllerState(current={self.current!r})"
