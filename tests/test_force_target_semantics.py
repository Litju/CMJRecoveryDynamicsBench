"""RES-585: the registered force cell is baseline-relative *mean* concentric force.

The legacy score-cell identifier ``relative_peak_mean_force_innovation`` is preserved for
frozen results, but the generated target is the criterion-assessment mean of three
concentric-phase *mean* forces minus the baseline-assessment mean (N/kg). It is neither peak
force nor net impulse.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from cmj_recovery_dynamics.contracts import OutcomeVariable
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    GRAVITATIONAL_ACCELERATION_M_PER_S2 as G,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PhaseConsistentAssessment,
    compute_net_impulse,
    realize_concentric_trial,
)
from cmj_recovery_dynamics.reproduction.single_exposure import TARGET_FIELDS, TARGET_UNITS
from cmj_recovery_dynamics.studies.fixed_mode_reference_study import OUTCOME_TARGETS

ROOT = Path(__file__).resolve().parents[1]


def test_registered_cell_maps_to_mean_concentric_force_target() -> None:
    assert OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value == (
        "relative_peak_mean_force_innovation"
    )
    mapping = {outcome.value: field for outcome, field in OUTCOME_TARGETS}
    assert mapping["relative_peak_mean_force_innovation"] == (
        "label.relative_mean_concentric_force_innovation"
    )
    assert mapping["net_impulse_innovation"] == ("label.relative_concentric_net_impulse_innovation")
    assert TARGET_UNITS[TARGET_FIELDS[0]] == "N/kg"
    assert TARGET_UNITS[TARGET_FIELDS[1]] == "m/s"


def test_frozen_results_keep_the_legacy_registered_identifier() -> None:
    results = json.loads((ROOT / "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text())
    cells = set(results["protocol"]["registered_cells"])
    assert {f"H{h}/relative_peak_mean_force_innovation" for h in (24, 48, 72)} <= cells
    assert len(cells) == 6


def test_target_is_gross_mean_force_not_peak_force_or_net_impulse() -> None:
    mean_force, net_impulse = 24.0, 1.9
    trial = realize_concentric_trial(mean_force, net_impulse)
    duration = trial.concentric_duration_seconds
    assert math.isclose(trial.mean_force_n_per_kg, mean_force, rel_tol=1e-12)
    # Gross mean force (N/kg) is the trapezoidal time-average of the force trace.
    area = sum(
        (a + b) * 0.5 * (t1 - t0)
        for a, b, t0, t1 in zip(
            trial.vertical_force_n_per_kg,
            trial.vertical_force_n_per_kg[1:],
            trial.time_seconds,
            trial.time_seconds[1:],
            strict=False,
        )
    )
    assert math.isclose(area / duration, trial.mean_force_n_per_kg, rel_tol=1e-12)
    # Peak force is strictly larger than the mean for a half-sine phase; they are distinct.
    assert max(trial.vertical_force_n_per_kg) > trial.mean_force_n_per_kg * 1.2
    # Net impulse (m/s) is the gravity-adjusted integral, with different units and value.
    assert math.isclose(
        trial.net_impulse_m_per_s, compute_net_impulse(mean_force, duration), rel_tol=1e-12
    )
    assert math.isclose(trial.net_impulse_m_per_s, (mean_force - G) * duration, rel_tol=1e-12)
    assert not math.isclose(trial.net_impulse_m_per_s, trial.mean_force_n_per_kg, rel_tol=0.1)


def test_assessment_is_three_trial_mean_and_innovation_is_criterion_minus_baseline() -> None:
    forces = (22.0, 23.0, 27.0)
    trials = tuple(realize_concentric_trial(f, 1.8) for f in forces)
    assessment = PhaseConsistentAssessment(trials)  # type: ignore[arg-type]
    assert math.isclose(assessment.force_mean, sum(forces) / 3.0, rel_tol=1e-12)
    baseline = PhaseConsistentAssessment(
        tuple(realize_concentric_trial(f, 1.8) for f in (20.0, 20.0, 20.0))  # type: ignore[arg-type]
    )
    innovation = assessment.force_mean - baseline.force_mean
    assert math.isclose(innovation, 24.0 - 20.0, rel_tol=1e-12)
