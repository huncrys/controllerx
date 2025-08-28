from typing import Any

from cx_const import DefaultActionsMapping, Light, Z2MLight
from cx_core import LightController, Z2MLightController
from cx_core.integration import EventData


def get_zha_action_LegrandWallController(data: dict[str, Any]) -> str:
    endpoint_id = data.get("endpoint_id", 1)
    command: str = data["command"]
    action = command
    args = data.get("args", {})
    args_mapping = {0: "up", 1: "down"}
    if command == "move":
        action = "_".join((action, args_mapping[args[0]]))
    action = "_".join((str(endpoint_id), action))
    return action


class Legrand600083LightController(LightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle": Light.TOGGLE,
            "on": Light.ON,
            "off": Light.OFF,
            "brightness_move_up": Light.HOLD_BRIGHTNESS_UP,
            "brightness_move_down": Light.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop": Light.RELEASE,
        }

    def get_zha_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "1_toggle": Light.TOGGLE,
            "1_on": Light.ON,
            "1_off": Light.OFF,
            "1_move_up": Light.HOLD_BRIGHTNESS_UP,
            "1_move_down": Light.HOLD_BRIGHTNESS_DOWN,
            "1_stop": Light.RELEASE,
        }

    def get_zha_action(self, data: EventData) -> str:
        return get_zha_action_LegrandWallController(data)


class Legrand600083Z2MLightController(Z2MLightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle": Z2MLight.TOGGLE,
            "on": Z2MLight.ON,
            "off": Z2MLight.OFF,
            "brightness_move_up": Z2MLight.HOLD_BRIGHTNESS_UP,
            "brightness_move_down": Z2MLight.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop": Z2MLight.RELEASE,
        }


class Legrand600088LightController(LightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_left": Light.TOGGLE,
            "on_left": Light.ON,
            "off_left": Light.OFF,
            "brightness_move_up_left": Light.HOLD_COLOR_UP,
            "brightness_move_down_left": Light.HOLD_COLOR_DOWN,
            "brightness_stop_left": Light.RELEASE,
            "toggle_right": Light.TOGGLE_FULL_BRIGHTNESS,
            "on_right": Light.ON_FULL_BRIGHTNESS,
            "off_right": Light.ON_MIN_BRIGHTNESS,
            "brightness_move_up_right": Light.HOLD_BRIGHTNESS_UP,
            "brightness_move_down_right": Light.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop_right": Light.RELEASE,
        }

    def get_zha_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "1_toggle": Light.TOGGLE,
            "1_on": Light.ON,
            "1_off": Light.OFF,
            "1_move_up": Light.HOLD_COLOR_UP,
            "1_move_down": Light.HOLD_COLOR_DOWN,
            "1_stop": Light.RELEASE,
            "2_toggle": Light.TOGGLE_FULL_BRIGHTNESS,
            "2_on": Light.ON_FULL_BRIGHTNESS,
            "2_off": Light.ON_MIN_BRIGHTNESS,
            "2_move_up": Light.HOLD_BRIGHTNESS_UP,
            "2_move_down": Light.HOLD_BRIGHTNESS_DOWN,
            "2_stop": Light.RELEASE,
        }

    def get_zha_action(self, data: EventData) -> str:
        return get_zha_action_LegrandWallController(data)


class Legrand600088LeftLightController(LightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_left": Light.TOGGLE,
            "on_left": Light.ON,
            "off_left": Light.OFF,
            "brightness_move_up_left": Light.HOLD_COLOR_UP,
            "brightness_move_down_left": Light.HOLD_COLOR_DOWN,
            "brightness_stop_left": Light.RELEASE,
        }

    def get_zha_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "1_toggle": Light.TOGGLE,
            "1_on": Light.ON,
            "1_off": Light.OFF,
            "1_move_up": Light.HOLD_COLOR_UP,
            "1_move_down": Light.HOLD_COLOR_DOWN,
            "1_stop": Light.RELEASE,
        }

    def get_zha_action(self, data: EventData) -> str:
        return get_zha_action_LegrandWallController(data)


class Legrand600088RightLightController(LightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_right": Light.TOGGLE,
            "on_right": Light.ON,
            "off_right": Light.OFF,
            "brightness_move_up_right": Light.HOLD_COLOR_UP,
            "brightness_move_down_right": Light.HOLD_COLOR_DOWN,
            "brightness_stop_right": Light.RELEASE,
        }

    def get_zha_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "2_toggle": Light.TOGGLE,
            "2_on": Light.ON,
            "2_off": Light.OFF,
            "2_move_up": Light.HOLD_COLOR_UP,
            "2_move_down": Light.HOLD_COLOR_DOWN,
            "2_stop": Light.RELEASE,
        }

    def get_zha_action(self, data: EventData) -> str:
        return get_zha_action_LegrandWallController(data)


class Legrand600088Z2MLightController(Z2MLightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_left": Z2MLight.TOGGLE,
            "on_left": Z2MLight.ON,
            "off_left": Z2MLight.OFF,
            "brightness_move_up_left": Z2MLight.HOLD_COLOR_TEMP_UP,
            "brightness_move_down_left": Z2MLight.HOLD_COLOR_TEMP_DOWN,
            "brightness_stop_left": Z2MLight.RELEASE,
            "toggle_right": Z2MLight.TOGGLE_FULL_BRIGHTNESS,
            "on_right": Z2MLight.ON_FULL_BRIGHTNESS,
            "off_right": Z2MLight.ON_MIN_BRIGHTNESS,
            "brightness_move_up_right": Z2MLight.HOLD_BRIGHTNESS_UP,
            "brightness_move_down_right": Z2MLight.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop_right": Z2MLight.RELEASE,
        }


class Legrand600088LeftZ2MLightController(Z2MLightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_left": Z2MLight.TOGGLE,
            "on_left": Z2MLight.ON,
            "off_left": Z2MLight.OFF,
            "brightness_move_up_left": Z2MLight.HOLD_BRIGHTNESS_UP,
            "brightness_move_down_left": Z2MLight.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop_left": Z2MLight.RELEASE,
        }


class Legrand600088RightZ2MLightController(Z2MLightController):
    def get_z2m_actions_mapping(self) -> DefaultActionsMapping:
        return {
            "toggle_right": Z2MLight.TOGGLE,
            "on_right": Z2MLight.ON,
            "off_right": Z2MLight.OFF,
            "brightness_move_up_right": Z2MLight.HOLD_BRIGHTNESS_UP,
            "brightness_move_down_right": Z2MLight.HOLD_BRIGHTNESS_DOWN,
            "brightness_stop_right": Z2MLight.RELEASE,
        }
