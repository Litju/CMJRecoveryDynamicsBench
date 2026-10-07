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
        "Mean of the two latest valid qualifying pre-index assessment summaries in the "
        "inclusive 24–240 hour window.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("timestamp", "force", "net impulse", "depth", "validity"),
        "Time-sorted pre-origin assessments; early initial-sample schema details remain "
        "unresolved.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("event kind", "duration", "time", "known-plan kind", "known-plan duration"),
        "Index exposure and fixed plan events known at origin, projected only through the "
        "target bound.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.UNAVAILABLE,
        (),
        "No age or strength predictors; opaque participant key is for grouping only.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("pre-origin assessments",),
        "The selected W01 schedule starts its exposure state at the index; it has no "
        "pre-index carry-in.",
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
        "Canonical baseline assessments use exactly three valid trials, each with a shared "
        "session deviation and independent within-trial error; each assessment and the two-"
        "assessment baseline are arithmetic means. A target uses one session-plus-trial "
        "error draw and three centered criterion trials (force ±0.03 N/kg, impulse ±0.01 "
        "m/s), so their mean is the observed target. The initial-sample details remain unresolved."
    ),
)
