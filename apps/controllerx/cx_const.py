from collections.abc import Awaitable, Callable
from typing import Any, Optional, Union

ActionFunction = Callable[..., Awaitable[Any]]
ActionParams = tuple[Any, ...]
ActionFunctionWithParams = tuple[ActionFunction, ActionParams]
TypeAction = Union[ActionFunction, ActionFunctionWithParams]
ActionEvent = Union[str, int]
PredefinedActionsMapping = dict[str, TypeAction]
DefaultActionsMapping = dict[ActionEvent, Optional[str]]

CustomAction = Union[str, dict[str, Any]]
CustomActions = Union[list[CustomAction], CustomAction]
CustomActionsMapping = dict[ActionEvent, Optional[CustomActions]]

Number = Union[int, float]


class Light:
    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"
    TOGGLE_FULL_BRIGHTNESS = "toggle_full_brightness"
    TOGGLE_FULL_WHITE_VALUE = "toggle_full_white_value"
    TOGGLE_FULL_COLOR_TEMP = "toggle_full_color_temp"
    TOGGLE_MIN_BRIGHTNESS = "toggle_min_brightness"
    TOGGLE_MIN_WHITE_VALUE = "toggle_min_white_value"
    TOGGLE_MIN_COLOR_TEMP = "toggle_min_color_temp"
    RELEASE = "release"
    ON_FULL_BRIGHTNESS = "on_full_brightness"
    ON_FULL_WHITE_VALUE = "on_full_white_value"
    ON_FULL_COLOR_TEMP = "on_full_color_temp"
    ON_MIN_BRIGHTNESS = "on_min_brightness"
    ON_MIN_WHITE_VALUE = "on_min_white_value"
    ON_MIN_COLOR_TEMP = "on_min_color_temp"
    ON_MIN_MAX_BRIGHTNESS = "on_min_max_brightness"
    ON_MAX_MIN_BRIGHTNESS = "on_max_min_brightness"
    ON_MIN_MAX_COLOR_TEMP = "on_min_max_color_temp"
    ON_MAX_MIN_COLOR_TEMP = "on_max_min_color_temp"
    SET_HALF_BRIGHTNESS = "set_half_brightness"
    SET_HALF_WHITE_VALUE = "set_half_white_value"
    SET_HALF_COLOR_TEMP = "set_half_color_temp"
    SYNC = "sync"
    CLICK = "click"
    CLICK_BRIGHTNESS_UP = "click_brightness_up"
    CLICK_BRIGHTNESS_DOWN = "click_brightness_down"
    CLICK_WHITE_VALUE_UP = "click_white_value_up"
    CLICK_WHITE_VALUE_DOWN = "click_white_value_down"
    CLICK_COLOR_UP = "click_color_up"
    CLICK_COLOR_DOWN = "click_color_down"
    CLICK_COLOR_TEMP_UP = "click_colortemp_up"
    CLICK_COLOR_TEMP_DOWN = "click_colortemp_down"
    CLICK_XY_COLOR_UP = "click_xycolor_up"
    CLICK_XY_COLOR_DOWN = "click_xycolor_down"
    HOLD = "hold"
    HOLD_BRIGHTNESS_UP = "hold_brightness_up"
    HOLD_BRIGHTNESS_DOWN = "hold_brightness_down"
    HOLD_BRIGHTNESS_TOGGLE = "hold_brightness_toggle"
    HOLD_WHITE_VALUE_UP = "hold_white_value_up"
    HOLD_WHITE_VALUE_DOWN = "hold_white_value_down"
    HOLD_WHITE_VALUE_TOGGLE = "hold_white_value_toggle"
    HOLD_COLOR_UP = "hold_color_up"
    HOLD_COLOR_DOWN = "hold_color_down"
    HOLD_COLOR_TOGGLE = "hold_color_toggle"
    HOLD_COLOR_TEMP_UP = "hold_colortemp_up"
    HOLD_COLOR_TEMP_DOWN = "hold_colortemp_down"
    HOLD_COLOR_TEMP_TOGGLE = "hold_colortemp_toggle"
    HOLD_XY_COLOR_UP = "hold_xycolor_up"
    HOLD_XY_COLOR_DOWN = "hold_xycolor_down"
    HOLD_XY_COLOR_TOGGLE = "hold_xycolor_toggle"
    XYCOLOR_FROM_CONTROLLER = "xycolor_from_controller"
    COLORTEMP_FROM_CONTROLLER = "colortemp_from_controller"
    COLORTEMP_FROM_CONTROLLER_STEP = "colortemp_from_controller_step"
    BRIGHTNESS_FROM_CONTROLLER_LEVEL = "brightness_from_controller_level"
    BRIGHTNESS_FROM_CONTROLLER_ANGLE = "brightness_from_controller_angle"
    BRIGHTNESS_FROM_CONTROLLER_STEP = "brightness_from_controller_step"


class Z2MLight:
    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"
    TOGGLE_FULL_BRIGHTNESS = "toggle_full_brightness"
    RELEASE = "release"
    ON_FULL_BRIGHTNESS = "on_full_brightness"
    ON_FULL_COLOR_TEMP = "on_full_color_temp"
    ON_MIN_BRIGHTNESS = "on_min_brightness"
    ON_MIN_COLOR_TEMP = "on_min_color_temp"
    SET_HALF_BRIGHTNESS = "set_half_brightness"
    SET_HALF_COLOR_TEMP = "set_half_color_temp"
    CLICK = "click"
    CLICK_BRIGHTNESS_UP = "click_brightness_up"
    CLICK_BRIGHTNESS_DOWN = "click_brightness_down"
    CLICK_COLOR_TEMP_UP = "click_colortemp_up"
    CLICK_COLOR_TEMP_DOWN = "click_colortemp_down"
    HOLD = "hold"
    HOLD_BRIGHTNESS_UP = "hold_brightness_up"
    HOLD_BRIGHTNESS_DOWN = "hold_brightness_down"
    HOLD_BRIGHTNESS_TOGGLE = "hold_brightness_toggle"
    HOLD_COLOR_TEMP_UP = "hold_colortemp_up"
    HOLD_COLOR_TEMP_DOWN = "hold_colortemp_down"
    HOLD_COLOR_TEMP_TOGGLE = "hold_colortemp_toggle"
    XYCOLOR_FROM_CONTROLLER = "xycolor_from_controller"
    COLORTEMP_FROM_CONTROLLER = "colortemp_from_controller"
    BRIGHTNESS_FROM_CONTROLLER_LEVEL = "brightness_from_controller_level"
    BRIGHTNESS_FROM_CONTROLLER_ANGLE = "brightness_from_controller_angle"
    SCENE_RECALL = "scene_recall"


class MediaPlayer:
    HOLD_VOLUME_DOWN = "hold_volume_down"
    HOLD_VOLUME_UP = "hold_volume_up"
    CLICK_VOLUME_DOWN = "click_volume_down"
    CLICK_VOLUME_UP = "click_volume_up"
    VOLUME_SET = "volume_set"
    RELEASE = "release"
    PLAY = "play"
    PAUSE = "pause"
    PLAY_PAUSE = "play_pause"
    NEXT_TRACK = "next_track"
    PREVIOUS_TRACK = "previous_track"
    NEXT_SOURCE = "next_source"
    PREVIOUS_SOURCE = "previous_source"
    MUTE = "mute"
    TTS = "tts"
    VOLUME_FROM_CONTROLLER_ANGLE = "volume_from_controller_angle"


class Switch:
    ON = "on"
    OFF = "off"
    TOGGLE = "toggle"


class Cover:
    OPEN = "open"
    CLOSE = "close"
    STOP = "stop"
    TOGGLE_OPEN = "toggle_open"
    TOGGLE_CLOSE = "toggle_close"


class StepperDir:
    UP = "up"
    DOWN = "down"
    TOGGLE = "toggle"


class StepperMode:
    STOP = "stop"
    LOOP = "loop"
    BOUNCE = "bounce"
