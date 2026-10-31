"""Invented force signals and schedules; no historical or human observations."""

from dataclasses import replace
from math import exp, fsum

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    Gate7PublicFeatureRow,
    _public_row_from_camp_input,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.observations.native_mechanics import (
    gate7_basis_v1,
    native_force_metrics_v1,
)
from cmj_recovery_dynamics.observations.public_builder import generate_gate7_fixture_v1


def _row(horizon: ForecastHorizon = ForecastHorizon.D7) -> Gate7PublicFeatureRow:
    builder = generate_gate7_fixture_v1()
    return _public_row_from_camp_input(builder.build(builder.origins[0].origin_id, horizon))


def _reference_basis(row: Gate7PublicFeatureRow) -> tuple[float, ...]:
    """Independent sum formulation, rather than the implementation's accumulation loop."""
    events = sorted(
        (event.time_from_origin_hours, float(event.duration_minutes) / 100)
        for event in (*row.history_exposures, *row.known_plan)
        if event.duration_minutes is not None
    )
    cumulative = np.cumsum([dose for _, dose in events])
    saturation = 10 * cumulative / (1 + cumulative)
    increments = np.diff(np.insert(saturation, 0, 0))
    return (
        *(
            fsum(dose * exp(-(row.target_time_hours - t) / tau) for t, dose in events)
            for tau in (36, 120)
        ),
        float(saturation[-1]),
        *(
            fsum(
                float(delta) * exp(-(row.target_time_hours - t) / tau)
                for (t, _), delta in zip(events, increments, strict=True)
            )
            for tau in (36, 120)
        ),
    )


def test_basis_all_public_fixture_rows_against_independent_sum_reference() -> None:
    for item in generate_gate7_fixture_v1().inputs():
        row = _public_row_from_camp_input(item)
        assert gate7_basis_v1(row) == pytest.approx(_reference_basis(row), rel=2e-15, abs=1e-15)


def test_basis_is_schedule_only_and_does_not_double_count_index() -> None:
    row = _row()
    original = gate7_basis_v1(row)
    modified = replace(row, baseline_relative_mean_concentric_force=999, history_assessments=())
    assert gate7_basis_v1(modified) == original
    dose = sum(
        x.duration_minutes / 100
        for x in (*row.history_exposures, *row.known_plan)
        if x.duration_minutes is not None
    )
    assert original[2] == pytest.approx(10 * dose / (1 + dose))
    all_zero = replace(
        row,
        history_exposures=tuple(replace(x, duration_minutes=0.0) for x in row.history_exposures),
        index_exposure=replace(row.index_exposure, duration_minutes=0.0),
        known_plan=tuple(replace(x, duration_minutes=0.0) for x in row.known_plan),
    )
    assert gate7_basis_v1(all_zero) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    "mutation", ["future", "unknown", "index", "negative", "missing", "duplicate"]
)
def test_basis_refuses_invalid_temporal_or_schedule_inputs(mutation: str) -> None:
    row = _row()
    plan = list(row.known_plan)
    if mutation == "future":
        plan[-1] = replace(plan[-1], time_from_origin_hours=169)
    elif mutation == "unknown":
        plan[-1] = replace(plan[-1], known_at_origin=False)
    elif mutation == "index":
        duration = plan[0].duration_minutes
        assert duration is not None
        plan[0] = replace(plan[0], duration_minutes=duration + 1)
    elif mutation == "negative":
        plan[-1] = replace(plan[-1], duration_minutes=-1)
    elif mutation == "missing":
        plan = plan[1:]
    else:
        plan[-1] = plan[0]
    with pytest.raises(ValueError):
        gate7_basis_v1(replace(row, known_plan=tuple(plan)))


def test_force_metrics_nonuniform_linear_signal_with_intersample_events() -> None:
    # F(t)=1000+100t on [0,3]; integrate [0.25,2.5] analytically.
    result = native_force_metrics_v1(
        (0, 0.5, 1.7, 3),
        (1000, 1050, 1170, 1300),
        system_mass_kg=80,
        gravity_m_s2=9.80665,
        concentric_onset_s=0.25,
        takeoff_s=2.5,
    )
    gross = 1000 * 2.25 + 50 * (2.5**2 - 0.25**2)
    assert result.gross_integral_n_s == pytest.approx(gross)
    assert result.force_n_per_kg == pytest.approx(gross / (80 * 2.25))
    assert result.net_impulse_m_per_s == pytest.approx(gross / 80 - 9.80665 * 2.25)
    assert result.force_n_per_kg == pytest.approx(9.80665 + result.net_impulse_m_per_s / 2.25)


def test_force_exact_boundary_uses_sample_once_and_excludes_airborne_samples() -> None:
    args = dict(system_mass_kg=50.0, gravity_m_s2=10.0, concentric_onset_s=1.0, takeoff_s=2.0)
    a = native_force_metrics_v1((0, 1, 1.25, 2, 3), (0, 600, 600, 600, 0), **args)
    b = native_force_metrics_v1((0, 1, 1.25, 2, 3), (1e9, 600, 600, 600, -1e9), **args)
    assert a == b
    assert a.force_n_per_kg == 12
    assert a.net_impulse_m_per_s == 2


@pytest.mark.parametrize(
    "times,forces,mass,start,end",
    [
        ((0, 1), (1,), 80, 0, 1),
        ((0, 0), (1, 1), 80, 0, 1),
        ((0, float("nan")), (1, 1), 80, 0, 1),
        ((0, 1), (1, float("inf")), 80, 0, 1),
        ((0, 1), (1, 1), 0, 0, 1),
        ((0, 1), (1, 1), -1, 0, 1),
        ((0, 1), (1, 1), 80, -1, 1),
        ((0, 1), (1, 1), 80, 1, 0),
    ],
)
def test_force_mechanics_fail_closed(
    times: tuple[float, ...], forces: tuple[float, ...], mass: float, start: float, end: float
) -> None:
    with pytest.raises(ValueError):
        native_force_metrics_v1(
            times,
            forces,
            system_mass_kg=mass,
            gravity_m_s2=9.80665,
            concentric_onset_s=start,
            takeoff_s=end,
        )
