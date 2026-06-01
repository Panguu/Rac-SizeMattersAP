from __future__ import annotations

import asyncio

from NetUtils import ClientStatus

from ..core.data import (
    CUTSCENE_BEFORE_SPROUT_O_MATIC,
    CUTSCENES,
    ELECTROSHOCK_GLOVES_CUTSCENE,
    ENTER_CUTSCENES,
    SPROUT_O_MATIC_CUTSCENE,
    Planets,
)
from ..core.memory import GADGETS

_GOAL_CUTSCENE = next(c for c in CUTSCENES if c.kind == "goal")


class CutsceneHandlerMixin:
    def _poll_cutscenes_sync(self, planet: int, new_checks: list[int]) -> None:
        goal_val = self.pine.read_int32(_GOAL_CUTSCENE.address)
        if self._prev_goal_cutscene != 0 and goal_val == 0 and planet == _GOAL_CUTSCENE.planet_id:
            self._append_location(new_checks, "Defeat Otto Destruct", "Goal")
            asyncio.create_task(self._send_goal_status())
        self._prev_goal_cutscene = goal_val

        if planet == Planets.RYLLUS.planet_id:
            enter_val = self.pine.read_int32(ENTER_CUTSCENES["ryllus"])
            before_val = self.pine.read_int32(CUTSCENE_BEFORE_SPROUT_O_MATIC)
            sprout_val = self.pine.read_int32(SPROUT_O_MATIC_CUTSCENE)

            if self._prev_before_sprout_cutscene is not None \
                    and self._prev_before_sprout_cutscene != 0 and before_val == 0:
                self._append_location(new_checks, "Ryllus Sprout-O-Matic", "Cutscene")

            if self._prev_sprout_cutscene is not None \
                    and self._prev_sprout_cutscene != 0 and sprout_val == 0:
                if GADGETS and not self._player_gadget_state.get("sprout_o_matic"):
                    self.pine.write_int8(GADGETS["sprout_o_matic"].unlocked, 0)

            self._prev_ryllus_enter = enter_val
            self._prev_before_sprout_cutscene = before_val
            self._prev_sprout_cutscene = sprout_val
        else:
            self._prev_ryllus_enter = None
            self._prev_before_sprout_cutscene = None
            self._prev_sprout_cutscene = None

        if planet == Planets.METALIS.planet_id:
            electroshock_val = self.pine.read_int32(ELECTROSHOCK_GLOVES_CUTSCENE)
            if self._prev_electroshock_cutscene is not None \
                    and self._prev_electroshock_cutscene != 0 and electroshock_val == 0:
                self._append_location(new_checks, "Metalis Electroshock Gloves", "Cutscene")
            self._prev_electroshock_cutscene = electroshock_val
        else:
            self._prev_electroshock_cutscene = None

    async def _send_goal_status(self) -> None:
        if not self.finished_game:
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.finished_game = True
