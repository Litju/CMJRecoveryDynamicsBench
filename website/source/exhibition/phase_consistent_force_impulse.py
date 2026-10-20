"""Shared concentric force phase for force and net-impulse measurements."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isclose, isfinite, pi, sin

from cmj_recovery_dynamics.contracts import (
    ForceImpulseRelationship,
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)
from cmj_recovery_dynamics.observations.episode_summary import assessment_trials
from cmj_recovery_dynamics.reproduction.single_exposure import KeyedRandomStreams

GRAVITATIONAL_ACCELERATION_M_PER_S2 = 9.80665
TRACE_NODE_COUNT = 65
CONCENTRIC_DURATION_SUPPORT_SECONDS = (0.075, 0.80)
PHASE_SEMANTICS_ID = "CMJ-CONCENTRIC-ONSET-TO-TAKEOFF-HALFSINE-1.0.0"
CONCENTRIC_ONSET_DEFINITION = (
    "lowest center-of-mass point where vertical velocity crosses from non-positive to positive"
)
CONCENTRIC_TAKEOFF_DEFINITION = (
    "last force-plate contact sample before flight; integrate over the "
    "half-open onset-to-takeoff interval"
)
FORCE_IMPULSE_RELATIONSHIP = ForceImpulseRelationship(
    gravitational_acceleration_m_per_s_squared=GRAVITATIONAL_ACCELERATION_M_PER_S2
)


@dataclass(frozen=True, slots=True)
class ConcentricTrial:
    phase_semantics_id: str
    onset_definition: str
    takeoff_definition: str
    time_seconds: tuple[float, ...]
    vertical_force_n_per_kg: tuple[float, ...]
    concentric_duration_seconds: float
    mean_force_n_per_kg: float
    net_impulse_m_per_s: float


@dataclass(frozen=True, slots=True)
class PhaseConsistentAssessment:
    trials: tuple[ConcentricTrial, ConcentricTrial, ConcentricTrial]

    def __post_init__(self) -> None:
        if len(self.trials) != 3 or any(
            len(trial.time_seconds) != TRACE_NODE_COUNT
            or len(trial.vertical_force_n_per_kg) != TRACE_NODE_COUNT
            for trial in self.trials
        ):
            raise ValueError("phase-consistent assessment requires exactly three 65-node trials")

    @property
    def force_mean(self) -> float:
        return fsum(trial.mean_force_n_per_kg for trial in self.trials) / 3.0

    @property
    def impulse_mean(self) -> float:
        return fsum(trial.net_impulse_m_per_s for trial in self.trials) / 3.0


def _trapezoidal_integral(values: tuple[float, ...], times: tuple[float, ...]) -> float:
    if len(values) != len(times) or len(values) < 2:
        raise ValueError("a force trace requires matching values at two or more times")
    if not all(isfinite(value) for value in (*values, *times)):
        raise ValueError("force trace values and times must be finite")
    if any(right <= left for left, right in zip(times, times[1:], strict=False)):
        raise ValueError("force trace times must increase strictly")
    return fsum(
        (values[index] + values[index + 1]) * 0.5 * (times[index + 1] - times[index])
        for index in range(len(values) - 1)
    )


def compute_net_impulse(mean_force_n_per_kg: float, duration_seconds: float) -> float:
    if not isfinite(mean_force_n_per_kg) or not isfinite(duration_seconds):
        raise ValueError("force and duration must be finite")
    if duration_seconds <= 0.0:
        raise ValueError("concentric duration must be positive")
    return (mean_force_n_per_kg - GRAVITATIONAL_ACCELERATION_M_PER_S2) * duration_seconds


def realize_concentric_trial(
    force_target_n_per_kg: float,
    impulse_target_m_per_s: float,
) -> ConcentricTrial:
    gravity = GRAVITATIONAL_ACCELERATION_M_PER_S2
    if not (
        isfinite(force_target_n_per_kg)
        and force_target_n_per_kg > gravity
        and isfinite(impulse_target_m_per_s)
        and impulse_target_m_per_s > 0.0
    ):
        raise ValueError("concentric force must exceed gravity and net impulse must be positive")
    duration = impulse_target_m_per_s / (force_target_n_per_kg - gravity)
    lower, upper = CONCENTRIC_DURATION_SUPPORT_SECONDS
    if not lower <= duration <= upper:
        raise ValueError(
            f"concentric duration {duration:.9g} escaped support [{lower}, {upper}] seconds"
        )

    times = tuple(duration * index / (TRACE_NODE_COUNT - 1) for index in range(TRACE_NODE_COUNT))
    shape = tuple(sin(pi * index / (TRACE_NODE_COUNT - 1)) for index in range(TRACE_NODE_COUNT))
    shape_mean = _trapezoidal_integral(shape, times) / duration
    if not isfinite(shape_mean) or shape_mean <= 0.0:
        raise RuntimeError("normalized half-sine phase has invalid area")
    net_force_mean = force_target_n_per_kg - gravity
    force = tuple(gravity + net_force_mean * value / shape_mean for value in shape)
    force_mean = _trapezoidal_integral(force, times) / duration
    net_impulse = _trapezoidal_integral(tuple(value - gravity for value in force), times)
    if not isclose(
        net_impulse,
        compute_net_impulse(force_mean, duration),
        rel_tol=2e-14,
        abs_tol=2e-14,
    ):
        raise RuntimeError("force trace violates its shared force/impulse identity")
    return ConcentricTrial(
        phase_semantics_id=PHASE_SEMANTICS_ID,
        onset_definition=CONCENTRIC_ONSET_DEFINITION,
        takeoff_definition=CONCENTRIC_TAKEOFF_DEFINITION,
        time_seconds=times,
        vertical_force_n_per_kg=force,
        concentric_duration_seconds=duration,
        mean_force_n_per_kg=force_mean,
        net_impulse_m_per_s=net_impulse,
    )


def measure_phase_consistent_assessment(
    truth_force_n_per_kg: float,
    truth_impulse_m_per_s: float,
    streams: KeyedRandomStreams,
    *,
    assessment_key: str,
) -> PhaseConsistentAssessment:
    """Build exactly three valid paired trials and aggregate their arithmetic means."""
    force_targets = assessment_trials(
        truth_force_n_per_kg,
        metric="force",
        streams=streams,
        assessment_key=assessment_key,
    )
    impulse_targets = assessment_trials(
        truth_impulse_m_per_s,
        metric="impulse",
        streams=streams,
        assessment_key=assessment_key,
    )
    trials = tuple(
        realize_concentric_trial(force, impulse)
        for force, impulse in zip(force_targets, impulse_targets, strict=True)
    )
    return PhaseConsistentAssessment(trials)  # type: ignore[arg-type]


PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION = ObservationContract(
    name="phase_consistent_force_impulse",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("force", "net impulse", "depth"),
        "One dedicated baseline about two hours before exposure; three-trial arithmetic mean.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.UNAVAILABLE,
        (),
        "Four prior episode records are carried as episode information.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("eight current-exposure fields",),
        "The current exposure occurs at time zero.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("training age", "strength"),
        "Camp and participant response effects remain hidden.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("four episode baselines", "four prior exposures", "six outcomes per episode"),
        "Prior records are available in generator order.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff="Current baseline, exposure, context, and four prior episodes.",
        history_scope="No additional material current-episode exposure through H72.",
        plans_known_at_origin_available=False,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent response parameters and effects",
            "measurement discrepancy and noise",
            "random generator state",
            "future outcome",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.PARTIALLY_SPECIFIED,
        ("episode keys", "future labels"),
        "Keys and labels are not predictor features; other exclusions remain unresolved.",
    ),
    measurement_construction=(
        "Each of exactly three valid trials uses 65 nodes on the normalized half-sine net-force "
        "phase from concentric onset to take-off. Force and net impulse integrate the same trace."
    ),
    force_impulse_relationship=FORCE_IMPULSE_RELATIONSHIP,
)

__all__ = [
    "CONCENTRIC_DURATION_SUPPORT_SECONDS",
    "CONCENTRIC_ONSET_DEFINITION",
    "CONCENTRIC_TAKEOFF_DEFINITION",
    "ConcentricTrial",
    "FORCE_IMPULSE_RELATIONSHIP",
    "GRAVITATIONAL_ACCELERATION_M_PER_S2",
    "PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION",
    "PHASE_SEMANTICS_ID",
    "PhaseConsistentAssessment",
    "TRACE_NODE_COUNT",
    "compute_net_impulse",
    "measure_phase_consistent_assessment",
    "realize_concentric_trial",
]
