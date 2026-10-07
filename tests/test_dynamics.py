"""Hand-computable checks for the recovered dynamics equations."""

from dataclasses import replace
from math import exp

import pytest

from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    BiexponentialEpisodeParameters,
)
from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    episode_response as biexponential_response,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    AssessmentEvent,
    EventTimeParameters,
    ExposureComponent,
    ExposureEvent,
    hill_saturation,
    normalized_exposure_dose,
    simulate_camp_response,
    stretched_exponential_memory,
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

PARAMETERS = EventTimeParameters(10.0, 1.0, 1.0, 24.0, 84.0, 1.0, 2.0, 3.0, 0.5, 0.75)


def _event(event_id: str, time: float, duration: float = 100.0) -> ExposureEvent:
    return ExposureEvent(
        event_id,
        time,
        "training",
        (ExposureComponent("duration", duration, "minutes", 100.0),),
    )


def test_hill_saturation_matches_hand_cases_and_limits() -> None:
    assert hill_saturation(0.0, PARAMETERS) == 0.0
    assert hill_saturation(1.0, PARAMETERS) == pytest.approx(5.0)
    assert hill_saturation(2.0, PARAMETERS) == pytest.approx(20.0 / 3.0)
    assert hill_saturation(2.0, replace(PARAMETERS, dose_exponent_gamma=2.0)) == pytest.approx(8.0)
    assert hill_saturation(1e100, PARAMETERS) < PARAMETERS.dose_response_ceiling_kappa
    assert hill_saturation(1e100, PARAMETERS) == pytest.approx(10.0)


def test_stretched_exponential_kernel_matches_hand_cases_and_limits() -> None:
    assert stretched_exponential_memory(0.0, 24.0, 1.0) == 1.0
    assert stretched_exponential_memory(24.0, 24.0, 1.0) == pytest.approx(exp(-1.0))
    assert stretched_exponential_memory(24.0, 24.0, 0.5) == pytest.approx(exp(-1.0))
    assert stretched_exponential_memory(6.0, 24.0, 1.0) == pytest.approx(exp(-0.25))
    assert stretched_exponential_memory(6.0, 24.0, 0.5) == pytest.approx(exp(-0.5))
    assert stretched_exponential_memory(1e9, 24.0, 1.0) == 0.0


def test_normalized_exposure_components_distinguish_zero_and_missing() -> None:
    components = (
        ExposureComponent("distance", 50.0, "km", 100.0),
        ExposureComponent("duration", 100.0, "minutes", 200.0),
        ExposureComponent("masked", 9.0, "reps", 1.0, day_mask=False),
        ExposureComponent("event_masked", 7.0, "reps", 1.0, event_mask=False),
        ExposureComponent("missing", None, "reps", 1.0, observed=False),
        ExposureComponent("observed_zero", 0.0, "reps", 1.0),
    )
    assert normalized_exposure_dose(components) == pytest.approx(1.0)
    assert components[2].contribution is None
    assert components[3].contribution is None
    assert components[4].contribution is None
    assert components[5].contribution == 0.0
    with pytest.raises(ValueError, match="forbidden data marker"):
        ExposureComponent("private_load", 1.0, "units", 1.0)
    with pytest.raises(ValueError, match="public inputs only"):
        ExposureComponent("load", 1.0, "units", 1.0, source="private")
    with pytest.raises(ValueError, match="not zero dose"):
        normalized_exposure_dose((ExposureComponent("missing", None, "reps", 1.0, False),))


def test_event_level_masks_exclude_all_components() -> None:
    events = (
        ExposureEvent(
            "masked-day",
            0.0,
            "training",
            (ExposureComponent("duration", 100.0, "minutes", 100.0),),
            day_mask=False,
        ),
        ExposureEvent(
            "masked-event",
            0.0,
            "training",
            (ExposureComponent("duration", 100.0, "minutes", 100.0),),
            event_mask=False,
        ),
    )
    for event in events:
        with pytest.raises(ValueError, match="not zero dose"):
            _ = event.joint_dose


@pytest.mark.parametrize("kind", ("friendly", "match"))
def test_friendly_and_match_events_require_the_60_minute_materiality_override(kind: str) -> None:
    with pytest.raises(ValueError, match="at least 60 minutes"):
        ExposureEvent(
            "short",
            0.0,
            kind,
            (ExposureComponent("duration_minutes", 59.99, "minutes", 100.0),),
        )
    ExposureEvent(
        "minimum",
        0.0,
        kind,
        (ExposureComponent("duration_minutes", 60.0, "minutes", 100.0),),
    )
    _event(f"short-training-{kind}", 0.0, 30.0)


def test_one_event_composes_fast_fatigue_and_slow_adaptation() -> None:
    state = simulate_camp_response((_event("index", 0.0),), (24.0,), PARAMETERS).state_at(24.0)
    saturation = hill_saturation(1.0, PARAMETERS)
    assert state.cumulative_dose == pytest.approx(1.0)
    assert state.fatigue_force_n_per_kg == pytest.approx(2.0 * saturation * exp(-1.0))
    assert state.adaptation_force_n_per_kg == pytest.approx(3.0 * saturation * exp(-24.0 / 84.0))
    assert state.fatigue_impulse_m_per_s == pytest.approx(0.5 * saturation * exp(-1.0))
    assert state.adaptation_impulse_m_per_s == pytest.approx(0.75 * saturation * exp(-24.0 / 84.0))
    assert state.net_force_innovation_n_per_kg == pytest.approx(
        state.adaptation_force_n_per_kg - state.fatigue_force_n_per_kg
    )
    assert state.net_impulse_innovation_m_per_s == pytest.approx(
        state.adaptation_impulse_m_per_s - state.fatigue_impulse_m_per_s
    )


def test_event_contributions_compose_in_time_order_and_ignore_input_order() -> None:
    events = (_event("later", 12.0), AssessmentEvent("assessment", 12.0), _event("first", 0.0))
    forward = simulate_camp_response(events, (24.0,), PARAMETERS)
    reverse = simulate_camp_response(tuple(reversed(events)), (24.0,), PARAMETERS)
    state = forward.state_at(24.0)
    assert state == reverse.state_at(24.0)
    assert tuple(item.event_id for item in forward.transitions) == (
        "first",
        "later",
        "assessment",
    )
    first_increment = hill_saturation(1.0, PARAMETERS)
    second_increment = hill_saturation(2.0, PARAMETERS) - first_increment
    fast_half = exp(-12.0 / 24.0)
    slow_half = exp(-12.0 / 84.0)
    expected_fatigue = (2.0 * first_increment * fast_half + 2.0 * second_increment) * fast_half
    expected_adaptation = (3.0 * first_increment * slow_half + 3.0 * second_increment) * slow_half
    assert state.fatigue_force_n_per_kg == pytest.approx(expected_fatigue)
    assert state.adaptation_force_n_per_kg == pytest.approx(expected_adaptation)


def test_event_kind_is_metadata_and_does_not_weight_dose() -> None:
    component = (ExposureComponent("duration_minutes", 100.0, "minutes", 100.0),)
    training = ExposureEvent("training", 0.0, "training", component)
    match = ExposureEvent("match", 0.0, "match", component)

    assert training.joint_dose == match.joint_dose == 1.0
    assert simulate_camp_response((training,), (24.0,), PARAMETERS).state_at(24.0) == (
        simulate_camp_response((match,), (24.0,), PARAMETERS).state_at(24.0)
    )


def test_w01_state_starts_at_index_without_pre_index_carry_in() -> None:
    response = simulate_camp_response((), (0.0, 72.0, 168.0), PARAMETERS)

    assert response.state_at(0.0).cumulative_dose == 0.0
    assert response.state_at(0.0).net_force_innovation_n_per_kg == 0.0
    with pytest.raises(ValueError, match="finite and non-negative"):
        _event("prior", -96.0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        simulate_camp_response((), (-24.0,), PARAMETERS)


def test_future_events_do_not_change_an_earlier_query() -> None:
    before_future_event = simulate_camp_response((_event("index", 0.0),), (72.0,), PARAMETERS)
    with_future_event = simulate_camp_response(
        (_event("index", 0.0), _event("later", 100.0, 200.0)), (72.0,), PARAMETERS
    )
    assert before_future_event.state_at(72.0) == with_future_event.state_at(72.0)


def test_d7_includes_authorized_exposures_through_its_query_time() -> None:
    index_and_first_plan = (_event("index", 0.0), _event("training-48", 48.0))
    full_camp = (*index_and_first_plan, _event("training-120", 120.0, 140.0))
    without_last_training = simulate_camp_response(index_and_first_plan, (72.0, 168.0), PARAMETERS)
    with_last_training = simulate_camp_response(full_camp, (72.0, 168.0), PARAMETERS)
    assert without_last_training.state_at(72.0) == with_last_training.state_at(72.0)
    assert without_last_training.state_at(168.0) != with_last_training.state_at(168.0)


def test_event_time_domains_and_parameter_bounds_fail_closed() -> None:
    with pytest.raises(ValueError, match="dose"):
        hill_saturation(-1.0, PARAMETERS)
    with pytest.raises(ValueError, match="elapsed time"):
        stretched_exponential_memory(-1.0, 24.0, 1.0)
    with pytest.raises(ValueError, match="time constant"):
        stretched_exponential_memory(1.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="β"):
        stretched_exponential_memory(1.0, 24.0, 0.0)
    with pytest.raises(ValueError, match="β"):
        replace(PARAMETERS, memory_shape_beta=1.6)
    with pytest.raises(ValueError, match="δ"):
        replace(PARAMETERS, dose_half_saturation_delta=0.0)
    with pytest.raises(ValueError, match="fast τ"):
        replace(PARAMETERS, fast_fatigue_time_constant_hours=5.0)
    independently_drawn_time_constants = replace(
        PARAMETERS,
        fast_fatigue_time_constant_hours=84.0,
        slow_adaptation_time_constant_hours=72.0,
    )
    assert independently_drawn_time_constants.fast_fatigue_time_constant_hours > (
        independently_drawn_time_constants.slow_adaptation_time_constant_hours
    )
    with pytest.raises(ValueError, match="impulse fatigue amplitude"):
        replace(PARAMETERS, fatigue_impulse_amplitude_m_per_s=2.1)
    with pytest.raises(ValueError, match="exposure values"):
        ExposureComponent("bad", -1.0, "minutes", 100.0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        ExposureEvent(
            "pre-index",
            -1.0,
            "training",
            (ExposureComponent("duration", 60.0, "minutes", 100.0),),
        )
    with pytest.raises(ValueError, match="query times"):
        simulate_camp_response((), (-1.0,), PARAMETERS)
    with pytest.raises(ValueError, match="query times"):
        simulate_camp_response((), (float("inf"),), PARAMETERS)


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
