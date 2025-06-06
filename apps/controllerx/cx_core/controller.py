import asyncio
import re
import time
from ast import literal_eval
from asyncio import CancelledError, Task
from collections import Counter, defaultdict
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar, overload

import appdaemon.utils as utils
import cx_version
from appdaemon.adapi import ADAPI
from appdaemon.plugins.hass.hassapi import Hass
from appdaemon.plugins.mqtt.mqttapi import Mqtt
from cx_const import (
    ActionEvent,
    ActionFunction,
    CustomActionsMapping,
    DefaultActionsMapping,
    PredefinedActionsMapping,
)
from cx_core import integration as integration_module
from cx_core.action_type import ActionsMapping, parse_actions
from cx_core.action_type.base import ActionType
from cx_core.integration import EventData, Integration

DEFAULT_ACTION_DELTA = 300  # In milliseconds
DEFAULT_MULTIPLE_CLICK_DELAY = 500  # In milliseconds
MULTIPLE_CLICK_TOKEN = "$"

MODE_SINGLE = "single"
MODE_RESTART = "restart"
MODE_QUEUED = "queued"
MODE_PARALLEL = "parallel"

T = TypeVar("T")


def action(method: Callable[..., Awaitable[Any]]) -> ActionFunction:
    @wraps(method)
    async def _action_impl(controller: "Controller", *args: Any, **kwargs: Any) -> None:
        continue_call = await controller.before_action(method.__name__, *args, **kwargs)
        if continue_call:
            await method(controller, *args, **kwargs)

    return _action_impl


def run_in(fn: Callable[..., Any], delay: float, **kwargs: Any) -> "Task[None]":
    """
    It runs the function (fn) in running event loop in `delay` seconds.
    This function has been created because the default run_in function
    from AppDaemon does not accept microseconds.
    """

    async def inner() -> None:
        await asyncio.sleep(delay)
        await fn(kwargs)

    task = asyncio.create_task(inner())
    return task


class Controller(Hass, Mqtt):  # type: ignore[misc]
    """
    This is the parent Controller, all controllers must extend from this class.
    """

    args: dict[str, Any]
    integration: Integration
    actions_mapping: ActionsMapping
    action_handles: defaultdict[ActionEvent, Task[None] | None]
    action_delay_handles: dict[ActionEvent, str | None]
    multiple_click_actions: set[ActionEvent]
    action_delay: dict[ActionEvent, int]
    action_delta: dict[ActionEvent, int]
    action_times: dict[str, float]
    previous_states: dict[ActionEvent, str | None]
    multiple_click_action_times: dict[str, float]
    click_counter: Counter[ActionEvent]
    multiple_click_action_delay_tasks: defaultdict[ActionEvent, Task[None] | None]
    multiple_click_delay: int

    async def initialize(self) -> None:
        self.log(f"🎮 ControllerX {cx_version.__version__}", ascii_encode=False)
        await self.init()

    async def init(self) -> None:
        controllers_ids: list[str] = self.get_list(self.args["controller"])
        self.integration = self.get_integration(self.args["integration"])

        if "mapping" in self.args and "merge_mapping" in self.args:
            raise ValueError("`mapping` and `merge_mapping` cannot be used together")

        custom_mapping: CustomActionsMapping | None = self.args.get("mapping", None)
        merge_mapping: CustomActionsMapping | None = self.args.get(
            "merge_mapping", None
        )

        if custom_mapping is None:
            default_actions_mapping = self.get_default_actions_mapping(self.integration)
            self.actions_mapping = self.parse_action_mapping(default_actions_mapping)  # type: ignore[arg-type]
        else:
            self.actions_mapping = self.parse_action_mapping(custom_mapping)

        if merge_mapping is not None:
            self.actions_mapping.update(self.parse_action_mapping(merge_mapping))

        # Filter actions with include and exclude
        if "actions" in self.args and "excluded_actions" in self.args:
            raise ValueError("`actions` and `excluded_actions` cannot be used together")
        include: list[ActionEvent] = self.get_list(
            self.args.get("actions", list(self.actions_mapping.keys()))
        )
        exclude: list[ActionEvent] = self.get_list(
            self.args.get("excluded_actions", [])
        )
        self.actions_mapping = self.filter_actions(
            self.actions_mapping, set(include), set(exclude)
        )

        # Action delay
        self.action_delay = self.get_mapping_per_action(
            self.actions_mapping,
            custom=self.args.get("action_delay"),
            default=0,
        )
        self.action_delay_handles = defaultdict(lambda: None)
        self.action_handles = defaultdict(lambda: None)

        # Action delta
        self.action_delta = self.get_mapping_per_action(
            self.actions_mapping,
            custom=self.args.get("action_delta"),
            default=DEFAULT_ACTION_DELTA,
        )
        self.action_times = defaultdict(float)

        # Previous state
        self.previous_states = self.get_mapping_per_action(
            self.actions_mapping,
            custom=self.args.get("previous_state"),
            default=None,
        )

        # Multiple click
        self.multiple_click_actions = self.get_multiple_click_actions(
            self.actions_mapping
        )
        self.multiple_click_delay = self.args.get(
            "multiple_click_delay", DEFAULT_MULTIPLE_CLICK_DELAY
        )
        self.multiple_click_action_times = defaultdict(float)
        self.click_counter = Counter()
        self.multiple_click_action_delay_tasks = defaultdict(lambda: None)

        # Mode
        self.mode = self.get_mapping_per_action(
            self.actions_mapping, custom=self.args.get("mode"), default=MODE_SINGLE
        )

        # Listen for device changes
        for controller_id in controllers_ids:
            await self.integration.listen_changes(controller_id)

    def filter_actions(
        self,
        actions_mapping: ActionsMapping,
        include: set[ActionEvent],
        exclude: set[ActionEvent],
    ) -> ActionsMapping:
        allowed_actions = include - exclude
        return {
            key: value
            for key, value in actions_mapping.items()
            if key in allowed_actions
        }

    @staticmethod
    def get_option(value: str, options: list[str], ctx: str | None = None) -> str:
        if value in options:
            return value
        else:
            raise ValueError(
                f"{f'{ctx} - ' if ctx is not None else ''}`{value}` is not an option. "
                f"The options are {options}"
            )

    def parse_integration(
        self, integration: str | dict[str, Any] | Any
    ) -> dict[str, str]:
        if isinstance(integration, str):
            return {"name": integration}
        elif isinstance(integration, dict):
            if "name" in integration:
                return integration
            else:
                raise ValueError("'name' attribute is mandatory")
        else:
            raise ValueError(
                f"Type {type(integration)} is not supported for `integration` attribute"
            )

    def get_integration(self, integration: str | dict[str, Any]) -> Integration:
        parsed_integration = self.parse_integration(integration)
        kwargs = {k: v for k, v in parsed_integration.items() if k != "name"}
        integrations = integration_module.get_integrations(self, kwargs)
        integration_argument = self.get_option(
            parsed_integration["name"], [i.name for i in integrations]
        )
        return next(i for i in integrations if i.name == integration_argument)

    def get_default_actions_mapping(
        self, integration: Integration
    ) -> DefaultActionsMapping:
        actions_mapping = integration.get_default_actions_mapping()
        if actions_mapping is None:
            raise ValueError(
                f"This controller does not support {integration.name}. Use `mapping` to define the actions."
            )
        return actions_mapping

    @overload
    def get_list(self, entities: list[T]) -> list[T]: ...

    @overload
    def get_list(self, entities: T) -> list[T]: ...

    def get_list(self, entities: list[T] | T) -> list[T]:
        if isinstance(entities, (list, tuple)):
            return list(entities)
        return [entities]

    @overload
    def get_mapping_per_action(
        self,
        actions_mapping: ActionsMapping,
        *,
        custom: T | dict[ActionEvent, T] | None,
        default: None,
    ) -> dict[ActionEvent, T | None]: ...

    @overload
    def get_mapping_per_action(
        self,
        actions_mapping: ActionsMapping,
        *,
        custom: T | dict[ActionEvent, T] | None,
        default: T,
    ) -> dict[ActionEvent, T]: ...

    def get_mapping_per_action(
        self,
        actions_mapping: ActionsMapping,
        *,
        custom: T | dict[ActionEvent, T] | None,
        default: None | T,
    ) -> dict[ActionEvent, T | None] | dict[ActionEvent, T]:
        if custom is not None and not isinstance(custom, dict):
            default = custom
        mapping = {action: default for action in actions_mapping}
        if custom is not None and isinstance(custom, dict):
            mapping.update(custom)
        return mapping

    def parse_action_mapping(self, mapping: CustomActionsMapping) -> ActionsMapping:
        return {
            event: parse_actions(self, action)
            for event, action in mapping.items()
            if action is not None
        }

    def get_multiple_click_actions(self, mapping: ActionsMapping) -> set[ActionEvent]:
        to_return: set[ActionEvent] = set()
        for key in mapping.keys():
            if not isinstance(key, str) or MULTIPLE_CLICK_TOKEN not in key:
                continue
            splitted = key.split(MULTIPLE_CLICK_TOKEN)
            assert 1 <= len(splitted) <= 2
            action_key, _ = splitted
            try:
                to_return.add(int(action_key))
            except ValueError:
                to_return.add(action_key)
        return to_return

    def format_multiple_click_action(
        self, action_key: ActionEvent, click_count: int
    ) -> str:
        return (
            str(action_key) + MULTIPLE_CLICK_TOKEN + str(click_count)
        )  # e.g. toggle$2

    async def _render_template(self, template: str) -> Any:
        result = await self.call_service(
            "template/render",
            render_template=False,
            template=template,
            return_result=True,
        )
        if result is None:
            raise ValueError(f"Template {template} returned None")
        try:
            return literal_eval(result)
        except (SyntaxError, ValueError):
            return result

    _TEMPLATE_RE = re.compile(r"\s*\{\{.*\}\}")

    def contains_templating(self, template: str) -> bool:
        is_template = self._TEMPLATE_RE.search(template) is not None
        if not is_template:
            self.log(f"`{template}` is not recognized as a template", level="DEBUG")
        return is_template

    async def render_value(self, value: Any) -> Any:
        if isinstance(value, str) and self.contains_templating(value):
            return await self._render_template(value)
        else:
            return value

    async def render_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        new_attributes: dict[str, Any] = {}
        for key, value in attributes.items():
            new_value = await self.render_value(value)
            if isinstance(value, dict):
                new_value = await self.render_attributes(value)
            new_attributes[key] = new_value
        return new_attributes

    async def call_service(
        self, service: str, render_template: bool = True, **attributes: Any
    ) -> Any | None:
        service = service.replace(".", "/")
        to_log = ["\n", f"🤖 Service: \033[1m{service.replace('/', '.')}\033[0m"]
        if service != "template/render" and render_template:
            attributes = await self.render_attributes(attributes)
        for attribute, value in attributes.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            to_log.append(f"  - {attribute}: {value}")
        self.log("\n".join(to_log), level="INFO", ascii_encode=False)
        return await ADAPI.call_service(self, service, **attributes)

    @utils.sync_wrapper  # type: ignore[misc]
    async def get_state(
        self,
        entity_id: str | None = None,
        attribute: str | None = None,
        default: Any = None,
        copy: bool = True,
        **kwargs: Any,
    ) -> Any | None:
        rendered_entity_id = await self.render_value(entity_id)
        return await super().get_state(
            rendered_entity_id, attribute, default, copy, **kwargs
        )

    async def handle_action(
        self,
        action_key: str,
        previous_state: str | None = None,
        extra: EventData | None = None,
    ) -> None:
        if (
            action_key in self.actions_mapping
            and self.previous_states[action_key] is not None
            and previous_state != self.previous_states[action_key]
        ):
            self.log(
                f"🎮 `{action_key}` not triggered because previous action was `{previous_state}`",
                level="DEBUG",
                ascii_encode=False,
            )
            return
        if (
            action_key in self.actions_mapping
            and action_key not in self.multiple_click_actions
        ):
            previous_call_time = self.action_times[action_key]
            now = time.time() * 1000
            self.action_times[action_key] = now
            if now - previous_call_time > self.action_delta[action_key]:
                await self.call_action(action_key, extra=extra)
        elif action_key in self.multiple_click_actions:
            now = time.time() * 1000
            previous_call_time = self.multiple_click_action_times.get(action_key, now)
            self.multiple_click_action_times[action_key] = now
            if now - previous_call_time > self.multiple_click_delay:
                pass

            previous_task = self.multiple_click_action_delay_tasks[action_key]
            if previous_task is not None:
                previous_task.cancel()

            self.click_counter[action_key] += 1
            click_count = self.click_counter[action_key]

            new_task = run_in(
                self.multiple_click_call_action,
                self.multiple_click_delay / 1000,
                action_key=action_key,
                extra=extra,
                click_count=click_count,
            )
            self.multiple_click_action_delay_tasks[action_key] = new_task
        else:
            self.log(
                f"🎮 Button event triggered, but not registered: `{action_key}`",
                level="DEBUG",
                ascii_encode=False,
            )

    async def multiple_click_call_action(self, kwargs: dict[str, Any]) -> None:
        action_key: ActionEvent = kwargs["action_key"]
        extra: EventData = kwargs["extra"]
        click_count: int = kwargs["click_count"]
        self.multiple_click_action_delay_tasks[action_key] = None
        self.log(
            f"🎮 {action_key} clicked `{click_count}` time(s)",
            level="DEBUG",
            ascii_encode=False,
        )
        self.click_counter[action_key] = 0
        click_action_key = self.format_multiple_click_action(action_key, click_count)
        if click_action_key in self.actions_mapping:
            await self.call_action(click_action_key, extra=extra)
        elif action_key in self.actions_mapping and click_count == 1:
            await self.call_action(action_key, extra=extra)

    async def call_action(
        self, action_key: ActionEvent, extra: EventData | None = None
    ) -> None:
        self.log(
            f"🎮 Button event triggered: `{action_key}`",
            level="INFO",
            ascii_encode=False,
        )
        self.log(
            f"Extra:\n{extra}",
            level="DEBUG",
        )
        delay = self.action_delay[action_key]
        if delay > 0:
            handle = self.action_delay_handles[action_key]
            if handle is not None:
                await self.cancel_timer(handle)
            self.log(
                f"🕒 Running action(s) from `{action_key}` in {delay} seconds",
                level="INFO",
                ascii_encode=False,
            )
            new_handle = await self.run_in(
                self.action_timer_callback, delay, action_key=action_key, extra=extra
            )
            self.action_delay_handles[action_key] = new_handle
        else:
            await self.action_timer_callback({"action_key": action_key, "extra": extra})

    async def _apply_mode_strategy(self, action_key: ActionEvent) -> bool:
        previous_task = self.action_handles[action_key]
        if previous_task is None or previous_task.done():
            return False
        if self.mode[action_key] == MODE_SINGLE:
            self.log(
                f"There is already an action executing for `{action_key}`. "
                "If you want a different behaviour change `mode` parameter, "
                "the default value is `single`.",
                level="WARNING",
            )
            return True
        elif self.mode[action_key] == MODE_RESTART:
            previous_task.cancel()
        elif self.mode[action_key] == MODE_QUEUED:
            await previous_task
        elif self.mode[action_key] == MODE_PARALLEL:
            pass
        else:
            raise ValueError(
                f"`{self.mode[action_key]}` is not a possible value for `mode` parameter."
                "Possible values: `single`, `restart`, `queued` and `parallel`."
            )
        return False

    async def action_timer_callback(self, kwargs: dict[str, Any]) -> None:
        action_key: ActionEvent = kwargs["action_key"]
        extra: EventData = kwargs["extra"]
        self.action_delay_handles[action_key] = None
        skip = await self._apply_mode_strategy(action_key)
        if skip:
            return
        action_types = self.actions_mapping[action_key]
        task = asyncio.create_task(self.call_action_types(action_types, extra))
        self.action_handles[action_key] = task
        try:
            await task
        except CancelledError:
            self.log(
                f"Task(s) from `{action_key}` was/were canceled and executed again",
                level="DEBUG",
            )

    async def call_action_types(
        self, action_types: list[ActionType], extra: EventData | None = None
    ) -> None:
        for action_type in action_types:
            self.log(
                f"🏃 Running `{action_type}` now",
                level="INFO",
                ascii_encode=False,
            )
            await action_type.run(extra=extra)

    async def before_action(self, action: str, *args: str, **kwargs: Any) -> bool:
        """
        Controllers have the option to implement this function, which is called
        everytime before an action is called and it has the check_before_action decorator.
        It should return True if the action shoul be called.
        Otherwise it should return False.
        """
        return True

    def get_z2m_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the states that a controller can take and the functions as values.
        This is used for zigbee2mqtt support.
        """
        return None

    def get_deconz_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the event id that a controller can take and the functions as values.
        This is used for deCONZ support.
        """
        return None

    def get_zha_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for ZHA support.
        """
        return None

    def get_zha_action(self, data: EventData) -> str | None:
        """
        This method can be override for controllers that do not support
        the standard extraction of the actions on cx_core/integration/zha.py
        """
        return None

    def get_lutron_caseta_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for Lutron support.
        """
        return None

    def get_state_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for State integration support.
        """
        return None

    def get_homematic_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for Homematic support.
        """
        return None

    def get_shelly_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for Shelly support.
        """
        return None

    def get_shellyforhass_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for Shelly for HASS support.
        """
        return None

    def get_tasmota_actions_mapping(self) -> DefaultActionsMapping | None:
        """
        Controllers can implement this function. It should return a dict
        with the command that a controller can take and the functions as values.
        This is used for Tasmota support.
        """
        return None

    def get_predefined_actions_mapping(self) -> PredefinedActionsMapping:
        return {}
