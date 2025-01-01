import json
from typing import Any

from cx_core.type.z2m_light_controller import Z2MLightController


class ESPHomeLightController(Z2MLightController):
    async def _mqtt_call(self, payload: dict[str, Any]) -> None:
        await self._mqtt_fn[self.entity.mode](
            f"{self.entity.topic_prefix}/{self.entity.name}/command",
            json.dumps(payload),
        )
