from typing import Any

from cx_core.action_type.base import ActionType
from cx_core.integration import EventData


class SceneActionType(ActionType):
    scene: str

    def initialize(self, **kwargs: Any) -> None:
        self.scene = kwargs["scene"]

    async def run(self, extra: EventData | None = None) -> None:
        await self.controller.call_service("scene/turn_on", entity_id=self.scene)

    def __str__(self) -> str:
        return f"Scene ({self.scene})"
