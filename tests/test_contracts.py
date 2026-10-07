"""Checks for the public scientific contract and measurement equations."""

import pytest

import cmj_recovery_dynamics as package
from cmj_recovery_dynamics.contracts import (
    CANONICAL_OUTCOMES,
    ClaimType,
    ForecastHorizon,
    ForecastWindow,
    OutcomeVariable,
    PhysicalUnit,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    GRAVITATIONAL_ACCELERATION_M_PER_S2,
    compute_net_impulse,
)
from cmj_recovery_dynamics.tasks import TASKS


def test_package_imports_and_exposes_canonical_outcomes() -> None:
    assert package.__version__ == "0.1.0"
    assert tuple(outcome.variable for outcome in CANONICAL_OUTCOMES) == (
        OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION,
        OutcomeVariable.NET_IMPULSE_INNOVATION,
    )
    assert tuple(outcome.unit for outcome in CANONICAL_OUTCOMES) == (
        PhysicalUnit.NEWTON_PER_KILOGRAM,
        PhysicalUnit.METER_PER_SECOND,
    )
    assert all("not a percentage" in outcome.semantics for outcome in CANONICAL_OUTCOMES)
    assert all("causal effect" in outcome.semantics for outcome in CANONICAL_OUTCOMES)


def test_lineage_exports_remain_available_on_demand() -> None:
    assert package.LINEAGE_REGISTRY
    assert package.get_benchmark_lineage("rich_history_camp_recovery")


def test_exactly_two_task_families_have_distinct_horizon_contracts() -> None:
    assert len(TASKS) == 2
    camp_task, episode_task = TASKS
    assert camp_task.horizons == (ForecastHorizon.H72, ForecastHorizon.D7)
    assert episode_task.horizons == (
        ForecastHorizon.H24,
        ForecastHorizon.H48,
        ForecastHorizon.H72,
    )
    assert camp_task.outcomes == episode_task.outcomes == CANONICAL_OUTCOMES


def test_forecast_windows_reject_invalid_time_order() -> None:
    with pytest.raises(ValueError, match="end must not precede"):
        ForecastWindow(ForecastHorizon.H24, 25, 24)


def test_phase_consistent_impulse_uses_the_established_force_relation() -> None:
    assert GRAVITATIONAL_ACCELERATION_M_PER_S2 == 9.80665
    assert compute_net_impulse(12.0, 0.5) == pytest.approx((12.0 - 9.80665) * 0.5)
    with pytest.raises(ValueError, match="duration must be positive"):
        compute_net_impulse(12.0, 0.0)


def test_claim_types_cover_the_scientific_ceiling() -> None:
    assert len(ClaimType) == 5
