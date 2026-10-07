"""Source-bound W02 fitness-fatigue impulse-response equations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import exp, fsum, isfinite

import numpy as np
from numpy.typing import ArrayLike, NDArray

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)

HILL_KAPPA = 2.2
HILL_DELTA = 1.0
HILL_GAMMA = 2.0
LOAD_ADJUSTMENT_SLOPE = 0.35
LOAD_ADJUSTMENT_RANGE = (0.6, 1.6)
BOUT_SENSITIVITY = 0.45
BOUT_TIME_SCALE = 3.0
BOUT_COUNT_RANGE = (0, 8)
RESPONSE_RATIO_RANGE = (1.5, 5.0)
FAST_TIME_CONSTANT_RANGE_HOURS = (36.0, 110.0)
SLOW_TIME_CONSTANT_RANGE_HOURS = (100.0, 260.0)
DECREMENT_FLOOR_FRACTION = 0.38


@dataclass(frozen=True, slots=True)
class FitnessFatigueParameters:
    """One participant's parameters for one exposure and one outcome."""

    amplitude_scale: float
    normalized_load: float
    response_ratio: float
    recent_four_week_bout_count: int | float
    slow_time_constant_hours: float
    fast_time_constant_hours: float
    baseline_level: float

    def __post_init__(self) -> None:
        values = (
            self.amplitude_scale,
            self.normalized_load,
            self.response_ratio,
            self.slow_time_constant_hours,
            self.fast_time_constant_hours,
            self.baseline_level,
        )
        if any(not isfinite(value) for value in values):
            raise ValueError("fitness-fatigue parameters must be finite")
        if self.normalized_load < 0:
            raise ValueError("normalized load must be non-negative")
        if not RESPONSE_RATIO_RANGE[0] <= self.response_ratio <= RESPONSE_RATIO_RANGE[1]:
            raise ValueError("response ratio is outside the recovered bounds")
        if (
            type(self.recent_four_week_bout_count) is bool
            or float(self.recent_four_week_bout_count) != int(self.recent_four_week_bout_count)
            or not BOUT_COUNT_RANGE[0] <= self.recent_four_week_bout_count <= BOUT_COUNT_RANGE[1]
        ):
            raise ValueError("four-week bout count must be an integer from 0 through 8")
        if not (
            FAST_TIME_CONSTANT_RANGE_HOURS[0]
            <= self.fast_time_constant_hours
            <= FAST_TIME_CONSTANT_RANGE_HOURS[1]
        ):
            raise ValueError("fast time constant is outside the recovered bounds")
        if not (
            SLOW_TIME_CONSTANT_RANGE_HOURS[0]
            <= self.slow_time_constant_hours
            <= SLOW_TIME_CONSTANT_RANGE_HOURS[1]
        ):
            raise ValueError("slow time constant is outside the recovered bounds")
        if self.baseline_level <= 0:
            raise ValueError("baseline level must be positive")


def hill_load_response(normalized_load: float) -> float:
    """Return the authored Hill response, with its finite-load limit."""
    if not isfinite(normalized_load) or normalized_load < 0:
        raise ValueError("normalized load must be finite and non-negative")
    ratio = normalized_load / HILL_DELTA
    if ratio <= 1.0:
        scaled = ratio**HILL_GAMMA
        return HILL_KAPPA * scaled / (1.0 + scaled)
    inverse = (1.0 / ratio) ** HILL_GAMMA
    return HILL_KAPPA / (1.0 + inverse)


def load_adjustment(normalized_load: float) -> float:
    """Return the clipped load multiplier applied to the fatigue ratio."""
    if not isfinite(normalized_load) or normalized_load < 0:
        raise ValueError("normalized load must be finite and non-negative")
    lower, upper = LOAD_ADJUSTMENT_RANGE
    return min(upper, max(lower, 1.0 + LOAD_ADJUSTMENT_SLOPE * (normalized_load - 1.0)))


def accustomedness(recent_four_week_bout_count: float) -> float:
    """Four-week bout sensitization; public counts range from zero through eight."""
    if not isfinite(recent_four_week_bout_count) or recent_four_week_bout_count < 0:
        raise ValueError("four-week bout count must be finite and non-negative")
    return 1.0 - BOUT_SENSITIVITY * exp(-recent_four_week_bout_count / BOUT_TIME_SCALE)


def _hill_array(load: NDArray[np.float64]) -> NDArray[np.float64]:
    ratio = load / HILL_DELTA
    low = np.minimum(ratio, 1.0) ** HILL_GAMMA
    high_inverse = (1.0 / np.maximum(ratio, 1.0)) ** HILL_GAMMA
    return np.where(
        ratio <= 1.0,
        HILL_KAPPA * low / (1.0 + low),
        HILL_KAPPA / (1.0 + high_inverse),
    )


def exposure_response_values(
    lag_hours: ArrayLike,
    amplitude_scale: ArrayLike,
    normalized_load: ArrayLike,
    response_ratio: ArrayLike,
    recent_four_week_bout_count: ArrayLike,
    slow_time_constant_hours: ArrayLike,
    fast_time_constant_hours: ArrayLike,
) -> NDArray[np.float64]:
    """Vector form of the selected-source per-exposure equation.

    Nonpositive lags contribute zero. The camp decrement floor is applied by
    ``camp_state`` after all exposure contributions have been summed.
    """
    raw = tuple(
        np.asarray(value, dtype=float)
        for value in (
            lag_hours,
            amplitude_scale,
            normalized_load,
            response_ratio,
            recent_four_week_bout_count,
            slow_time_constant_hours,
            fast_time_constant_hours,
        )
    )
    if any(not np.isfinite(value).all() for value in raw):
        raise ValueError("fitness-fatigue inputs must be finite")
    lag, amplitude, load, ratio, bouts, tau_slow, tau_fast = np.broadcast_arrays(*raw)
    if np.any(load < 0):
        raise ValueError("normalized load must be non-negative")
    if np.any((ratio < RESPONSE_RATIO_RANGE[0]) | (ratio > RESPONSE_RATIO_RANGE[1])):
        raise ValueError("response ratio is outside the recovered bounds")
    if np.any((bouts < BOUT_COUNT_RANGE[0]) | (bouts > BOUT_COUNT_RANGE[1])):
        raise ValueError("four-week bout count is outside the recovered bounds")
    if np.any(bouts != np.floor(bouts)):
        raise ValueError("four-week bout count must be an integer")
    if np.any(
        (tau_slow < SLOW_TIME_CONSTANT_RANGE_HOURS[0])
        | (tau_slow > SLOW_TIME_CONSTANT_RANGE_HOURS[1])
    ):
        raise ValueError("slow time constant is outside the recovered bounds")
    if np.any(
        (tau_fast < FAST_TIME_CONSTANT_RANGE_HOURS[0])
        | (tau_fast > FAST_TIME_CONSTANT_RANGE_HOURS[1])
    ):
        raise ValueError("fast time constant is outside the recovered bounds")

    load_factor = np.clip(1.0 + LOAD_ADJUSTMENT_SLOPE * (load - 1.0), *LOAD_ADJUSTMENT_RANGE)
    rho = 1.0 - BOUT_SENSITIVITY * np.exp(-bouts / BOUT_TIME_SCALE)
    positive_lag = lag > 0
    elapsed = np.where(positive_lag, lag, 0.0)
    response = (
        amplitude
        * _hill_array(load)
        * (np.exp(-elapsed / tau_slow) - ratio * load_factor * rho * np.exp(-elapsed / tau_fast))
    )
    return np.asarray(np.where(positive_lag, response, 0.0), dtype=float)


def episode_response(lag_hours: float, parameters: FitnessFatigueParameters) -> float:
    """Return one exposure's unfloored fitness-fatigue contribution."""
    if not isfinite(lag_hours):
        raise ValueError("lag must be finite")
    return float(
        exposure_response_values(
            lag_hours,
            parameters.amplitude_scale,
            parameters.normalized_load,
            parameters.response_ratio,
            parameters.recent_four_week_bout_count,
            parameters.slow_time_constant_hours,
            parameters.fast_time_constant_hours,
        )
    )


def camp_state(lag_hours: Sequence[float], parameters: Sequence[FitnessFatigueParameters]) -> float:
    """Sum a participant's exposure responses, then apply the authored floor."""
    if len(lag_hours) != len(parameters):
        raise ValueError("camp lags and exposure parameters must have the same length")
    if not parameters:
        return 0.0
    baseline = parameters[0].baseline_level
    if any(item.baseline_level != baseline for item in parameters[1:]):
        raise ValueError("one camp state must use a shared participant baseline level")
    net = fsum(episode_response(lag, item) for lag, item in zip(lag_hours, parameters, strict=True))
    return max(net, -DECREMENT_FLOOR_FRACTION * baseline)


FITNESS_FATIGUE_IMPULSE_RESPONSE = DynamicsModel(
    name="fitness_fatigue_impulse_response",
    family=DynamicsFamily.FITNESS_FATIGUE_IMPULSE_RESPONSE,
    equation_summary=(
        "Each exposure contributes Hill-scaled slow-positive minus load- and bout-adjusted "
        "fast-negative response; contributions sum before the latent-level decrement floor."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)
