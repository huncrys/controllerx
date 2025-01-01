from typing import Any

from appdaemon.plugins.mqtt.mqttapi import Mqtt
from cx_const import DefaultActionsMapping
from cx_core.integration import EventData, Integration


class B2MIntegration(Integration):
    name = "b2m"

    def get_default_actions_mapping(self) -> DefaultActionsMapping | None:
        return self.controller.get_z2m_actions_mapping()

    async def listen_changes(self, controller_id: str) -> None:
        topic_prefix = self.kwargs.get("topic_prefix", "ble2mqtt")
        await Mqtt.listen_event(
            self.controller,
            self.event_callback,
            topic=f"{topic_prefix}/{controller_id}/action",
            namespace="mqtt",
        )

    async def event_callback(
        self, event_name: str, data: EventData, kwargs: dict[str, Any]
    ) -> None:
        self.controller.log(f"MQTT data event: {data}", level="DEBUG")
        if "payload" not in data:
            return
        await self.controller.handle_action(data["payload"])
