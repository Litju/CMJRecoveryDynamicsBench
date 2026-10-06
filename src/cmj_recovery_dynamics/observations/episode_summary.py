"""Scalar-trial episode-history information boundary before phase consistency."""

from cmj_recovery_dynamics.contracts import (
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)

EPISODE_SUMMARY_OBSERVATION = ObservationContract(
    name="episode_summary",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("force", "net impulse", "depth"),
        "One dedicated three-trial baseline approximately two hours before exposure.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.UNAVAILABLE,
        (),
        "The contract uses four prior episodes rather than a camp-wide assessment history.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("eight current-exposure fields",),
        "Current exposure occurs at time zero.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("training age", "strength"),
        "Camp identifier and participant response effects are hidden.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("four episode baselines", "four prior exposures", "six outcomes per episode"),
        "Episodes are in generator order; inter-episode elapsed time is not provided.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff=(
            "Current baseline, exposure, participant context, and four prior episodes."
        ),
        history_scope="No additional material exposure through H72; future labels are unavailable.",
        plans_known_at_origin_available=False,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent response weights and kinetics",
            "participant and camp effects",
            "true recovery state",
            "measurement discrepancy and noise",
            "random generator state",
            "future targets",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.PARTIALLY_SPECIFIED,
        ("episode keys", "future labels"),
        "Keys and labels are not predictor features; other exclusions remain unresolved.",
    ),
    measurement_construction=(
        "Three scalar force and impulse trials are arithmetically averaged; no shared phase "
        "trace or force–impulse identity is frozen."
    ),
)
