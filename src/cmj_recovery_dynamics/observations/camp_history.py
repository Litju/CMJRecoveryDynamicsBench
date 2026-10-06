"""Public camp-history information boundary for multi-exposure forecasting."""

from cmj_recovery_dynamics.contracts import (
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)

CAMP_HISTORY_OBSERVATION = ObservationContract(
    name="camp_history",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("relative force summary", "net impulse summary"),
        "Two latest valid qualifying pre-index summaries, 24–240 hours before origin.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("timestamp", "force", "net impulse", "depth", "validity"),
        "Time-sorted pre-origin assessments; early schema details remain unresolved.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("event kind", "duration", "time", "known-plan kind", "known-plan duration"),
        "Prior and index events plus plans known at origin within the target bound.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.UNAVAILABLE,
        (),
        "No age or strength predictors; opaque participant key is for grouping only.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("pre-origin assessments", "pre-index exposures"),
        "Available camp trajectory before the prediction origin.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff="History and plans available at the index origin.",
        history_scope="Pre-origin history; known plans only within the target bound.",
        plans_known_at_origin_available=True,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "world and cluster identity",
            "latent states and response parameters",
            "dose response and random generator state",
            "future target labels",
            "scorer identity",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("raw athlete identifiers", "random generator state", "future target labels", "scorer"),
        "The participant grouping key is not a predictor.",
    ),
    measurement_construction=(
        "Three valid criterion trials; early initial-sample schema and baseline trial count "
        "remain unresolved."
    ),
)
