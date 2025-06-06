from typing import Any

from cx_core.action_type.base import ActionType
from cx_core.integration import EventData


class DelayActionType(ActionType):
    delay: int

    def initialize(self, **kwargs: Any) -> None:
        self.delay = kwargs["delay"]

    async def run(self, extra: EventData | None = None) -> None:
        await self.controller.sleep(self.delay)

    def __str__(self) -> str:
        return f"Delay ({self.delay} seconds)"
