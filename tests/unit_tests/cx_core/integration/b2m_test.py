from typing import Any

import pytest
from appdaemon.plugins.mqtt.mqttapi import Mqtt
from cx_core.controller import Controller
from cx_core.integration import EventData
from cx_core.integration.b2m import B2MIntegration
from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    "data, handle_action_called, expected_called_with",
    [
        ({"payload": "action_1"}, True, "action_1"),
        ({}, False, Any),
    ],
)
async def test_event_callback(
    fake_controller: Controller,
    mocker: MockerFixture,
    data: EventData,
    handle_action_called: bool,
    expected_called_with: str,
) -> None:
    handle_action_patch = mocker.patch.object(fake_controller, "handle_action")
    b2m_integration = B2MIntegration(fake_controller, {})
    await b2m_integration.event_callback("test", data, {})

    if handle_action_called:
        handle_action_patch.assert_called_once_with(expected_called_with)
    else:
        handle_action_patch.assert_not_called()


@pytest.mark.parametrize(
    "topic_prefix, expected_topic",
    [
        (None, "ble2mqtt/controller_id/action"),
        ("my_prefix", "my_prefix/controller_id/action"),
    ],
)
async def test_listen_changes(
    fake_controller: Controller,
    mocker: MockerFixture,
    topic_prefix: str | None,
    expected_topic: str,
) -> None:
    kwargs: dict[str, Any] = {}
    if topic_prefix is not None:
        kwargs["topic_prefix"] = topic_prefix

    mqtt_listen_event_mock = mocker.patch.object(Mqtt, "listen_event")
    b2m_integration = B2MIntegration(fake_controller, kwargs)

    await b2m_integration.listen_changes("controller_id")

    mqtt_listen_event_mock.assert_called_once_with(
        fake_controller,
        b2m_integration.event_callback,
        topic=expected_topic,
        namespace="mqtt",
    )
