"""Richer camp-monitoring information boundary with variable history availability."""

from cmj_recovery_dynamics.contracts import (
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)

RICH_MONITORING_OBSERVATION = ObservationContract(
    name="rich_monitoring",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("relative force", "net impulse"),
        "Mean of two latest valid qualifying assessments, each at least 60 hours after exposure.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("time", "force", "net impulse", "depth", "trial count", "validity"),
        "Up to 14 assessments with explicit missing and invalid monitoring states.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("time", "kind", "duration", "dose", "index exposure", "known plans"),
        "Three to six prior exposures in 21–28 days and up to three plans known at origin.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("training age", "strength", "prior four-week bout count"),
        "Latent participant and camp effects are hidden.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("prior exposure history", "prior assessments"),
        "Monitoring history is variable and filtered by availability at origin.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff="Pre-origin records and plans available at the index origin.",
        history_scope="Assessments at 14–40 and 60–84 hours; prior exposures in 21–28 days.",
        plans_known_at_origin_available=True,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent kinetics and amplitudes",
            "latent state and camp effects",
            "target-time depth",
            "future outcomes",
            "random generator state",
            "scorer truth",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.PARTIALLY_SPECIFIED,
        ("target-time depth", "future outcomes", "scorer truth"),
        "Other forbidden serialized fields are not repeated in this semantic contract.",
    ),
    measurement_construction=(
        "Five valid standardized-depth target trials; variable monitoring quality is retained."
    ),
)
