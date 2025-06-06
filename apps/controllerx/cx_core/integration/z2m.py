import json
from typing import Any

from appdaemon.plugins.hass.hassapi import Hass
from appdaemon.plugins.mqtt.mqttapi import Mqtt
from cx_const import DefaultActionsMapping
from cx_core.integration import EventData, Integration

LISTENS_TO_HA = "ha"
LISTENS_TO_MQTT = "mqtt"
LISTENS_TO_EVENT = "event"


class Z2MIntegration(Integration):
    name = "z2m"

    def get_default_actions_mapping(self) -> DefaultActionsMapping | None:
        return self.controller.get_z2m_actions_mapping()

    async def listen_changes(self, controller_id: str) -> None:
        listens_to = self.kwargs.get("listen_to", LISTENS_TO_HA)
        if listens_to == LISTENS_TO_HA:
            self.controller.log(
                "⚠️ Listening to HA sensor actions is now deprecated and will be removed in the future. Use `listen_to: mqtt` or `listen_to: event` instead."
                " Read more about it here: https://xaviml.github.io/controllerx/others/z2m-ha-sensor-deprecated",
                level="WARNING",
                ascii_encode=False,
            )
            await Hass.listen_state(self.controller, self.state_callback, controller_id)
        elif listens_to == LISTENS_TO_MQTT:
            topic_prefix = self.kwargs.get("topic_prefix", "zigbee2mqtt")
            await Mqtt.listen_event(
                self.controller,
                self.event_callback,
                topic=f"{topic_prefix}/{controller_id}",
                namespace="mqtt",
            )
        elif listens_to == LISTENS_TO_EVENT:
            await Hass.listen_state(
                self.controller,
                self.state_callback,
                f"event.{controller_id}",
                attribute="event_type",
            )
        else:
            raise ValueError(
                "`listen_to` has to be either `ha`, `mqtt` or `event`. Default is `ha`."
            )

    async def event_callback(
        self, event_name: str, data: EventData, kwargs: dict[str, Any]
    ) -> None:
        self.controller.log(f"MQTT data event: {data}", level="DEBUG")
        action_key = self.kwargs.get("action_key", "action")
        action_group_key = self.kwargs.get("action_group_key", "action_group")
        if "payload" not in data:
            return
        payload = json.loads(data["payload"])
        if action_key not in payload:
            self.controller.log(
                f"There is no `{action_key}` in the MQTT topic payload",
                level="DEBUG",
            )
            return
        if action_group_key in payload and "action_group" in self.kwargs:
            action_group = self.controller.get_list(self.kwargs["action_group"])
            if payload["action_group"] not in action_group:
                self.controller.log(
                    f"Action group {payload['action_group']} not found in "
                    f"action groups: {action_group}",
                    level="DEBUG",
                )
                return
        await self.controller.handle_action(payload[action_key], extra=payload)

    async def state_callback(
        self,
        entity: str | None,
        attribute: str | None,
        old: str | None,
        new: str,
        kwargs: dict[str, Any],
    ) -> None:
        await self.controller.handle_action(new, previous_state=old)
