import abc
from dataclasses import dataclass

from cx_const import Number, StepperDir


class MinMax:
    def __init__(self, min: Number, max: Number, margin: float = 0.05) -> None:
        self._min = min
        self._max = max
        self.margin_dist = (max - min) * margin

    @property
    def min(self) -> Number:
        return self._min

    @property
    def max(self) -> Number:
        return self._max

    def is_min(self, value: Number) -> bool:
        return self._min == value

    def is_max(self, value: Number) -> bool:
        return self._max == value

    def is_between(self, value: Number) -> bool:
        return self._min < value < self._max

    def in_min_boundaries(self, value: Number) -> bool:
        return self._min <= value <= (self._min + self.margin_dist)

    def in_max_boundaries(self, value: Number) -> bool:
        return (self._max - self.margin_dist) <= value <= self._max

    def clip(self, value: Number) -> Number:
        return max(self._min, min(value, self._max))

    def __repr__(self) -> str:
        return f"MinMax({self.min}, {self.max})"


@dataclass
class StepperOutput:
    next_value: Number
    next_direction: str | None

    @property
    def exceeded(self) -> bool:
        return self.next_direction is None


class Stepper(abc.ABC):
    sign_mapping = {StepperDir.UP: 1, StepperDir.DOWN: -1}

    min_max: MinMax
    steps: Number
    previous_direction: str
    relative_steps: bool

    @staticmethod
    def invert_direction(direction: str) -> str:
        return StepperDir.UP if direction == StepperDir.DOWN else StepperDir.DOWN

    @staticmethod
    def sign(direction: str) -> int:
        return Stepper.sign_mapping[direction]

    @staticmethod
    def apply_sign(value: Number, direction: str) -> Number:
        return Stepper.sign(direction) * value

    def __init__(
        self,
        min_max: MinMax,
        steps: Number,
        previous_direction: str = StepperDir.DOWN,
        relative_steps: bool = True,
    ) -> None:
        self.min_max = min_max
        self.steps = steps
        self.previous_direction = previous_direction
        self.relative_steps = relative_steps

    def _compute_step(self) -> float:
        if self.relative_steps:
            max_ = self.min_max.max
            min_ = self.min_max.min
            return (max_ - min_) / self.steps
        else:
            return self.steps

    def get_direction(self, value: Number, direction: str) -> str:
        if direction == StepperDir.TOGGLE:
            direction = Stepper.invert_direction(self.previous_direction)
            self.previous_direction = direction
        return direction

    @abc.abstractmethod
    def step(self, value: Number, direction: str) -> StepperOutput:
        """
        This function updates the value according to the steps
        that needs to take and returns the new value together with
        the new direction it will need to go. If next_direction is
        None, the loop will stop executing.
        """
        raise NotImplementedError


class InvertStepper(Stepper):
    def step(self, value: Number, direction: str) -> StepperOutput:
        return StepperOutput(self.apply_sign(value, direction), next_direction=None)
