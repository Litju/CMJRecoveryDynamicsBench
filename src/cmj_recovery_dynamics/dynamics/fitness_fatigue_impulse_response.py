"""Parameterized per-exposure fitness-fatigue impulse-response equation."""

from dataclasses import dataclass
from math import exp, isfinite

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)

LOAD_ADJUSTMENT_SLOPE = 0.35
LOAD_ADJUSTMENT_RANGE = (0.6, 1.6)
BOUT_SENSITIVITY = 0.45
BOUT_TIME_SCALE = 3.0
DECREMENT_FLOOR_FRACTION = 0.38


@dataclass(frozen=True, slots=True)
class FitnessFatigueParameters:
    amplitude_scale: float
    hill_load_response: float
    normalized_load: float
    response_ratio: float
    recent_four_week_bout_count: float
    slow_time_constant_hours: float
    fast_time_constant_hours: float
    baseline_measurement: float

    def __post_init__(self) -> None:
        finite_values = (
            self.amplitude_scale,
            self.hill_load_response,
            self.normalized_load,
            self.response_ratio,
            self.recent_four_week_bout_count,
            self.slow_time_constant_hours,
            self.fast_time_constant_hours,
            self.baseline_measurement,
        )
        if any(not isfinite(value) for value in finite_values):
            raise ValueError("fitness-fatigue parameters must be finite")
        if (
            min(
                self.amplitude_scale,
                self.hill_load_response,
                self.normalized_load,
                self.response_ratio,
                self.recent_four_week_bout_count,
            )
            < 0
        ):
            raise ValueError("load, amplitude, ratio, and bout count must be non-negative")
        if self.slow_time_constant_hours <= 0 or self.fast_time_constant_hours <= 0:
            raise ValueError("time constants must be positive")
        if self.baseline_measurement <= 0:
            raise ValueError("baseline measurement must be positive")


def episode_response(lag_hours: float, parameters: FitnessFatigueParameters) -> float:
    """Return the bounded per-exposure response at a non-negative lag."""
    if not isfinite(lag_hours) or lag_hours < 0:
        raise ValueError("lag must be finite and non-negative")
    lower, upper = LOAD_ADJUSTMENT_RANGE
    load_adjustment = min(
        upper,
        max(lower, 1 + LOAD_ADJUSTMENT_SLOPE * (parameters.normalized_load - 1)),
    )
    adjusted_ratio = parameters.response_ratio * load_adjustment
    bout_sensitivity = 1 - BOUT_SENSITIVITY * exp(
        -parameters.recent_four_week_bout_count / BOUT_TIME_SCALE
    )
    amplitude = parameters.amplitude_scale * parameters.hill_load_response
    response = amplitude * (
        exp(-lag_hours / parameters.slow_time_constant_hours)
        - adjusted_ratio * bout_sensitivity * exp(-lag_hours / parameters.fast_time_constant_hours)
    )
    return max(response, -DECREMENT_FLOOR_FRACTION * parameters.baseline_measurement)


FITNESS_FATIGUE_IMPULSE_RESPONSE = DynamicsModel(
    name="fitness_fatigue_impulse_response",
    family=DynamicsFamily.FITNESS_FATIGUE_IMPULSE_RESPONSE,
    equation_summary=(
        "Per-exposure difference of slow and bout-sensitized fast exponential modes, "
        "with load-dependent response ratio and a baseline-scaled decrement floor."
    ),
    implementation_status=ModelImplementationStatus.PARTIAL_EQUATION,
)
