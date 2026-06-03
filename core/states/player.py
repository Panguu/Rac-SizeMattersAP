import asyncio
from collections.abc import Callable
from enum import IntEnum

from worlds.rac_size_matters.core.states.state import State
from worlds.rac_size_matters.pypine.pypine.pine import Pine


class PlayerMovementState(IntEnum):
    Alive           = 0x00
    FishDeath       = 0x29
    FadeDeath       = 0x2A
    Electrocution   = 0x2B
    VoidDeath       = 0x2C
    UnknownDeath    = 0x2D
    SwimDeath       = 0x2E
    MysteriousDeath = 0x2F
    Pickup          = 0x43

    @staticmethod
    def is_dead(state: int) -> bool:
        return PlayerMovementState.FishDeath <= state <= PlayerMovementState.MysteriousDeath


class PlayerState(State):
    """
    Global player state. Polls planet-specific movement and health addresses.
    Activated per-planet by PlanetState.on_enter() with that planet's addresses.
    Override on_* hooks to react to player events.
    """

    def __init__(self, pine: Pine):
        super().__init__(pine)
        self.movement_state: PlayerMovementState = PlayerMovementState.Alive
        self.health: int = 0
        self._movement_addr: int | None = None
        self._health_addr: int | None = None
        self._task: asyncio.Task | None = None

    # --- State interface ---

    async def read(self) -> bool:
        if self._movement_addr is None:
            return False
        async with self._lock:
            raw = self.pine.read_int8(self._movement_addr)
            if self._health_addr is not None:
                self.health = self.pine.read_int32(self._health_addr)
        try:
            self.movement_state = PlayerMovementState(raw)
        except ValueError:
            pass
        return True

    async def apply(self) -> bool:
        return True

    async def poll(self, mem_address: int, interval: int, callback: Callable[[int, int], None]) -> None:
        del mem_address  # PlayerState polls its own addresses via read()
        last: PlayerMovementState | None = None
        while True:
            await self.read()
            current = self.movement_state
            if last is not None and current != last:
                callback(int(last), int(current))
                self._on_transition(last, current)
            last = current
            await asyncio.sleep(interval / 1000)

    # --- Lifecycle ---

    async def activate(
        self,
        movement_addr: int,
        health_addr: int,
        interval: int,
        callback: Callable[[int, int], None],
    ) -> None:
        """Start polling. Called from PlanetState.on_enter()."""
        if self._task is not None:
            return
        self._movement_addr = movement_addr
        self._health_addr   = health_addr
        self._task = asyncio.create_task(self.poll(0, interval, callback))

    async def deactivate(self) -> None:
        """Stop polling. Called from PlanetState.on_exit()."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self.movement_state = PlayerMovementState.Alive
        self.health = 0

    # --- Transition handler ---

    def _on_transition(self, prev: PlayerMovementState, current: PlayerMovementState) -> None:
        was_dead    = PlayerMovementState.is_dead(int(prev))
        is_dead     = PlayerMovementState.is_dead(int(current))
        was_pickup  = prev    == PlayerMovementState.Pickup
        is_pickup   = current == PlayerMovementState.Pickup

        if is_dead and not was_dead:
            self.on_death(current)
        elif not is_dead and was_dead:
            self.on_respawn()

        if is_pickup and not was_pickup:
            self.on_pickup_start()
        elif not is_pickup and was_pickup:
            self.on_pickup_end()

    # --- Properties ---

    @property
    def is_dead(self) -> bool:
        return PlayerMovementState.is_dead(int(self.movement_state))

    @property
    def is_picking_up(self) -> bool:
        return self.movement_state == PlayerMovementState.Pickup

    # --- Hooks (override per use case) ---

    def on_death(self, _cause: PlayerMovementState) -> None:
        """Fired when the player enters a death state."""
        del _cause

    def on_respawn(self) -> None:
        """Fired when the player returns to Alive after death."""

    def on_pickup_start(self) -> None:
        """Fired when the player enters the Pickup movement state."""

    def on_pickup_end(self) -> None:
        """Fired when the player leaves the Pickup movement state."""

    # --- Dunder ---

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlayerState):
            return NotImplemented
        return self is other

    def __repr__(self) -> str:
        return f"PlayerState(movement={self.movement_state.name}, health={self.health})"
