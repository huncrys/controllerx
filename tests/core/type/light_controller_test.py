import pytest

from core import LightController, ReleaseHoldController
from tests.utils import hass_mock
from core.stepper import Stepper
from core.stepper.minmax_stepper import MinMaxStepper
from core.stepper.circular_stepper import CircularStepper


@pytest.fixture
def sut(hass_mock):
    c = LightController()
    c.args = {}
    c.delay = 0
    c.light = {"name": "light"}
    c.on_hold = False
    return c


@pytest.mark.parametrize(
    "light_input, light_output",
    [
        ("light.kitchen", {"name": "light.kitchen", "color_mode": "auto"}),
        (
            {"name": "light.kitchen", "color_mode": "auto"},
            {"name": "light.kitchen", "color_mode": "auto"},
        ),
        ({"name": "light.kitchen"}, {"name": "light.kitchen", "color_mode": "auto"}),
        (
            {"name": "light.kitchen", "color_mode": "color_temp"},
            {"name": "light.kitchen", "color_mode": "color_temp"},
        ),
    ],
)
def test_initialize_and_get_light(sut, mocker, light_input, light_output):
    super_initialize_stub = mocker.patch.object(ReleaseHoldController, "initialize")

    sut.args["light"] = light_input
    sut.initialize()

    super_initialize_stub.assert_called_once()
    assert sut.light == light_output


@pytest.mark.parametrize(
    "attribute_input, color_mode, supported_features, attribute_expected, throws_error",
    [
        ("color", "auto", "16", "xy_color", False),  # 16 = xy_color
        ("color", "auto", "2", "color_temp", False),  # 2 = color_temp
        ("color", "auto", "18", "xy_color", False),  # 18 = xy_color + color_temp
        ("brightness", "auto", "0", "brightness", False),
        ("brightness", "auto", "16", "brightness", False),
        ("color", "color_temp", "18", "color_temp", False),
        ("color", "xy_color", "18", "xy_color", False),
        ("color", "auto", "0", "not_important", True),
    ],
)
@pytest.mark.asyncio
async def test_get_attribute(
    sut,
    monkeypatch,
    attribute_input,
    color_mode,
    supported_features,
    attribute_expected,
    throws_error,
):
    async def fake_get_entity_state(entity, attribute=None):

        return supported_features

    sut.light = {"name": "light", "color_mode": color_mode}
    monkeypatch.setattr(sut, "get_entity_state", fake_get_entity_state)
    # SUT
    if throws_error:
        with pytest.raises(ValueError) as e:
            await sut.get_attribute(attribute_input)
    else:
        output = await sut.get_attribute(attribute_input)

        # Checks
        assert output == attribute_expected


@pytest.mark.parametrize(
    "attribute_input, expected_output",
    [
        ("xy_color", None),
        ("brightness", "return_from_fake_get_entity_state"),
        ("color_temp", "return_from_fake_get_entity_state"),
    ],
)
@pytest.mark.asyncio
async def test_get_value_attribute(sut, monkeypatch, attribute_input, expected_output):
    async def fake_get_entity_state(entity, attribute):
        return "return_from_fake_get_entity_state"

    monkeypatch.setattr(sut, "get_entity_state", fake_get_entity_state)

    # SUT
    output = await sut.get_value_attribute(attribute_input)

    assert output == expected_output


@pytest.mark.parametrize(
    "old, attribute, direction, stepper, light_state, smooth_power_on, expected_stop, expected_value_attribute",
    [
        (
            50,
            LightController.ATTRIBUTE_BRIGHTNESS,
            Stepper.UP,
            MinMaxStepper(1, 255, 254),
            "on",
            False,
            False,
            51,
        ),
        (0, "xy_color", Stepper.UP, CircularStepper(0, 30, 30), "on", False, False, 0,),
        (
            499,
            "color_temp",
            Stepper.UP,
            MinMaxStepper(153, 500, 10),
            "on",
            False,
            True,
            500,
        ),
        (
            0,
            LightController.ATTRIBUTE_BRIGHTNESS,
            Stepper.UP,
            MinMaxStepper(1, 255, 254),
            "off",
            True,
            True,
            0,
        ),
    ],
)
@pytest.mark.asyncio
async def test_change_light_state(
    sut,
    mocker,
    monkeypatch,
    old,
    attribute,
    direction,
    stepper,
    light_state,
    smooth_power_on,
    expected_stop,
    expected_value_attribute,
):
    async def fake_get_entity_state(*args, **kwargs):
        return light_state

    called_service_patch = mocker.patch.object(sut, "call_service")
    sut.smooth_power_on = smooth_power_on
    sut.value_attribute = old
    sut.manual_steppers = {attribute: stepper}
    sut.automatic_steppers = {attribute: stepper}
    sut.transition = 300
    monkeypatch.setattr(sut, "get_entity_state", fake_get_entity_state)

    # SUT
    stop = await sut.change_light_state(old, attribute, direction, stepper, "hold")

    # Checks
    assert stop == expected_stop
    assert sut.value_attribute == expected_value_attribute
    called_service_patch.assert_called()


@pytest.mark.parametrize(
    "attributes_input, transition, attributes_expected",
    [
        ({"test": "test"}, 300, {"test": "test", "transition": 0.3}),
        ({"test": "test", "transition": 0.5}, 300, {"test": "test", "transition": 0.5}),
        ({}, 1000, {"transition": 1}),
    ],
)
@pytest.mark.asyncio
async def test_on(sut, mocker, attributes_input, transition, attributes_expected):
    called_service_patch = mocker.patch.object(sut, "call_service")
    sut.transition = transition
    await sut.on(**attributes_input)
    called_service_patch.assert_called_once_with(
        "homeassistant/turn_on", entity_id=sut.light["name"], **attributes_expected
    )


@pytest.mark.asyncio
async def test_off(sut, mocker):
    called_service_patch = mocker.patch.object(sut, "call_service")
    await sut.off()
    called_service_patch.assert_called_once_with(
        "homeassistant/turn_off", entity_id=sut.light["name"]
    )


@pytest.mark.asyncio
async def test_toggle(sut, mocker):
    called_service_patch = mocker.patch.object(sut, "call_service")
    await sut.toggle()
    called_service_patch.assert_called_once_with(
        "homeassistant/toggle", entity_id=sut.light["name"]
    )


@pytest.mark.parametrize(
    "min_max, fraction, expected_value",
    [
        ((1, 255), 0, 1),
        ((1, 255), 1, 255),
        ((0, 10), 0.5, 5),
        ((0, 100), 0.2, 20),
        ((0, 100), -1, 0),
        ((0, 100), 1.5, 100),
    ],
)
@pytest.mark.asyncio
async def test_set_value(sut, mocker, min_max, fraction, expected_value):
    attribute = "test_attribute"
    on_patch = mocker.patch.object(sut, "on")
    stepper = MinMaxStepper(min_max[0], min_max[1], 1)
    sut.automatic_steppers = {attribute: stepper}

    # SUT
    await sut.set_value(attribute, fraction)

    # Checks
    on_patch.assert_called_once_with(**{attribute: expected_value})


@pytest.mark.asyncio
async def test_on_full(sut, mocker):
    attribute = "test_attribute"
    max_ = 10
    on_patch = mocker.patch.object(sut, "on")
    stepper = MinMaxStepper(1, max_, 10)
    stepper.previous_direction = Stepper.TOGGLE_DOWN
    sut.automatic_steppers = {attribute: stepper}

    # SUT
    await sut.on_full(attribute)

    # Checks
    on_patch.assert_called_once_with(**{attribute: max_})
    assert stepper.previous_direction == Stepper.TOGGLE_UP


@pytest.mark.asyncio
async def test_on_min(sut, mocker):
    attribute = "test_attribute"
    min_ = 1
    on_patch = mocker.patch.object(sut, "on")
    stepper = MinMaxStepper(min_, 10, 10)
    stepper.previous_direction = Stepper.TOGGLE_UP
    sut.automatic_steppers = {attribute: stepper}

    # SUT
    await sut.on_min(attribute)

    # Checks
    on_patch.assert_called_once_with(**{attribute: min_})
    assert stepper.previous_direction == Stepper.TOGGLE_DOWN


@pytest.mark.parametrize(
    "max_brightness, color_attribute, expected_color_attributes",
    [
        (255, "color_temp", {"color_temp": 370}),
        (255, "xy_color", {"xy_color": (0.323, 0.329)}),
        (120, "error", {}),
    ],
)
@pytest.mark.asyncio
async def test_sync(
    sut, monkeypatch, mocker, max_brightness, color_attribute, expected_color_attributes
):
    sut.max_brightness = max_brightness
    sut.light = {"name": "test_light"}
    sut.transition = 300

    async def fake_get_attribute(*args, **kwargs):
        if color_attribute == "error":
            raise ValueError()
        return color_attribute

    monkeypatch.setattr(sut, "get_attribute", fake_get_attribute)
    called_service_patch = mocker.patch.object(sut, "call_service")

    await sut.sync()

    called_service_patch.assert_any_call(
        "homeassistant/turn_on",
        entity_id="test_light",
        brightness=max_brightness,
        transition=0,
    )

    if color_attribute == "error":
        assert called_service_patch.call_count == 1
    else:
        assert called_service_patch.call_count == 2
        called_service_patch.assert_any_call(
            "homeassistant/turn_on",
            entity_id="test_light",
            **{"transition": 0.3, **expected_color_attributes}
        )


@pytest.mark.parametrize(
    "attribute_input, direction_input, light_state, smooth_power_on, expected_calls",
    [
        (LightController.ATTRIBUTE_BRIGHTNESS, Stepper.UP, "off", True, 1),
        ("color_temp", Stepper.UP, "off", True, 0),
        ("color_temp", Stepper.UP, "on", True, 1),
    ],
)
@pytest.mark.asyncio
async def test_click(
    sut,
    monkeypatch,
    mocker,
    attribute_input,
    direction_input,
    light_state,
    smooth_power_on,
    expected_calls,
):
    value_attribute = 10

    async def fake_get_entity_state(*args, **kwargs):
        return light_state

    async def fake_get_value_attribute(*args, **kwargs):
        return value_attribute

    async def fake_get_attribute(*args, **kwargs):
        return attribute_input

    monkeypatch.setattr(sut, "get_entity_state", fake_get_entity_state)
    monkeypatch.setattr(sut, "get_value_attribute", fake_get_value_attribute)
    monkeypatch.setattr(sut, "get_attribute", fake_get_attribute)
    change_light_state_patch = mocker.patch.object(sut, "change_light_state")
    sut.smooth_power_on = smooth_power_on
    stepper = MinMaxStepper(1, 10, 10)
    sut.manual_steppers = {attribute_input: stepper}

    # SUT
    await sut.click(attribute_input, direction_input)

    # Checks
    assert change_light_state_patch.call_count == expected_calls


@pytest.mark.parametrize(
    "attribute_input, direction_input, previous_direction, light_state, smooth_power_on, expected_calls, expected_direction",
    [
        (
            LightController.ATTRIBUTE_BRIGHTNESS,
            Stepper.UP,
            Stepper.UP,
            "off",
            True,
            1,
            Stepper.UP,
        ),
        ("color_temp", Stepper.UP, Stepper.UP, "off", True, 0, Stepper.UP),
        ("color_temp", Stepper.UP, Stepper.UP, "on", True, 1, Stepper.UP),
        (
            "color_temp",
            Stepper.TOGGLE,
            Stepper.TOGGLE_DOWN,
            "on",
            True,
            1,
            Stepper.TOGGLE_UP,
        ),
    ],
)
@pytest.mark.asyncio
async def test_hold(
    sut,
    monkeypatch,
    mocker,
    attribute_input,
    direction_input,
    previous_direction,
    light_state,
    smooth_power_on,
    expected_calls,
    expected_direction,
):
    value_attribute = 10

    async def fake_get_entity_state(*args, **kwargs):
        return light_state

    async def fake_get_value_attribute(*args, **kwargs):
        return value_attribute

    async def fake_get_attribute(*args, **kwargs):
        return attribute_input

    monkeypatch.setattr(sut, "get_entity_state", fake_get_entity_state)
    monkeypatch.setattr(sut, "get_value_attribute", fake_get_value_attribute)
    monkeypatch.setattr(sut, "get_attribute", fake_get_attribute)
    sut.smooth_power_on = smooth_power_on
    stepper = MinMaxStepper(1, 10, 10)
    stepper.previous_direction = previous_direction
    sut.automatic_steppers = {attribute_input: stepper}
    super_hold_patch = mocker.patch.object(ReleaseHoldController, "hold")

    # SUT
    await sut.hold(attribute_input, direction_input)

    # Checks
    assert super_hold_patch.call_count == expected_calls
    if expected_calls > 0:
        super_hold_patch.assert_called_with(attribute_input, expected_direction)


@pytest.mark.asyncio
async def test_hold_loop(sut, mocker):
    attribute = "test_attribute"
    direction = Stepper.UP
    sut.value_attribute = 10
    change_light_state_patch = mocker.patch.object(sut, "change_light_state")
    stepper = MinMaxStepper(1, 10, 10)
    sut.automatic_steppers = {attribute: stepper}
    await sut.hold_loop(attribute, direction)
    change_light_state_patch.assert_called_once_with(
        sut.value_attribute, attribute, direction, stepper, "hold"
    )