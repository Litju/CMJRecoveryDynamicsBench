"""Checks for the parameterized equations that are fully recoverable."""

from math import exp

import pytest

from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    BiexponentialEpisodeParameters,
)
from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    episode_response as biexponential_response,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    EventTimeParameters,
    exponential_memory_kernel,
    hill_saturation,
)
from cmj_recovery_dynamics.dynamics.fitness_fatigue_impulse_response import (
    FitnessFatigueParameters,
)
from cmj_recovery_dynamics.dynamics.fitness_fatigue_impulse_response import (
    episode_response as fitness_fatigue_response,
)
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    fixed_mode_response,
)
from cmj_recovery_dynamics.dynamics.threshold_response import (
    ThresholdResponseParameters,
    threshold_response_score,
)


def test_event_time_equation_pieces_are_parameterized() -> None:
    parameters = EventTimeParameters(2.0, 1.0, 2.0, 24.0, 1.0)
    assert hill_saturation(0.0, parameters) == 0.0
    assert hill_saturation(1.0, parameters) == pytest.approx(1.0)
    assert exponential_memory_kernel(24.0, parameters) == pytest.approx(exp(-1.0))


def test_fitness_fatigue_response_obeys_the_recovered_decrement_floor() -> None:
    parameters = FitnessFatigueParameters(
        amplitude_scale=1.0,
        hill_load_response=1.0,
        normalized_load=1.0,
        response_ratio=100.0,
        recent_four_week_bout_count=0.0,
        slow_time_constant_hours=84.0,
        fast_time_constant_hours=24.0,
        baseline_measurement=10.0,
    )
    assert fitness_fatigue_response(0.0, parameters) == pytest.approx(-3.8)


def test_biexponential_response_uses_two_negative_modes() -> None:
    parameters = BiexponentialEpisodeParameters(2.0, 1.0, 24.0, 84.0)
    assert biexponential_response(0.0, parameters) == -3.0
    assert biexponential_response(24.0, parameters) == pytest.approx(
        -2.0 * exp(-1.0) - exp(-24.0 / 84.0)
    )


def test_threshold_response_is_stable_above_the_threshold() -> None:
    parameters = ThresholdResponseParameters((0.2,) * 7, 0.5, 0.0)
    result = threshold_response_score((1_000.0,) * 7, parameters)
    assert result == pytest.approx(4.0 * (1400.0 - 0.5))


def test_fixed_modes_use_the_mathematical_24_and_84_hour_scales() -> None:
    assert fixed_mode_response(0.0, 2.0, 1.0) == -3.0
    assert fixed_mode_response(24.0, 2.0, 1.0) == pytest.approx(
        -2.0 * exp(-1.0) - exp(-24.0 / 84.0)
    )
