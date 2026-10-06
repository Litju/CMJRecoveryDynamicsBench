"""Paired phase-consistent force and net-impulse observation contract."""

from math import isfinite

from cmj_recovery_dynamics.contracts import (
    ForceImpulseRelationship,
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)

GRAVITATIONAL_ACCELERATION_M_PER_S2 = 9.80665
FORCE_IMPULSE_RELATIONSHIP = ForceImpulseRelationship(
    gravitational_acceleration_m_per_s_squared=GRAVITATIONAL_ACCELERATION_M_PER_S2
)


def compute_net_impulse(mean_force_n_per_kg: float, duration_seconds: float) -> float:
    """Derive net impulse in m/s from the paired mean-force and duration measure."""
    if not isfinite(mean_force_n_per_kg) or not isfinite(duration_seconds):
        raise ValueError("force and duration must be finite")
    if duration_seconds <= 0:
        raise ValueError("concentric duration must be positive")
    return (mean_force_n_per_kg - GRAVITATIONAL_ACCELERATION_M_PER_S2) * duration_seconds


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
        ("four episode baselines", "four prior exposures", "four prior outcomes"),
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
        "Each of three valid trials uses a 65-node normalized half-sine net-force trace; "
        "trapezoidal integration spans the concentric phase, with duration 0.075–0.8 s."
    ),
    force_impulse_relationship=FORCE_IMPULSE_RELATIONSHIP,
)
