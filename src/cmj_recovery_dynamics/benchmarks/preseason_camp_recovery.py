"""Initial and canonical public-sample states of the camp recovery benchmark."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    EVENT_TIME_ADAPTATION_RECOVERY,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    EMPIRICAL_ENERGY_QUALIFICATION_EVALUATION,
    INITIAL_PRESEASON_CAMP_EVALUATION,
    POSTERIOR_COVARIANCE_QUALIFICATION_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    STANDARDIZED_EUCLIDEAN_QUALIFICATION_EVALUATION,
)
from cmj_recovery_dynamics.observations.camp_history import CAMP_HISTORY_OBSERVATION
from cmj_recovery_dynamics.tasks.preseason_camp_recovery import PRESEASON_CAMP_RECOVERY_TASK

INITIAL_PRESEASON_CAMP_RECOVERY = BenchmarkDefinition(
    name="initial_preseason_camp_recovery",
    research_question=(
        "Can pre-origin force and impulse assessments, camp exposure history, the index "
        "exposure, and known plans forecast the two observed innovations at H72 and D7 "
        "in the initial synthetic public sample?"
    ),
    task=PRESEASON_CAMP_RECOVERY_TASK,
    observation=CAMP_HISTORY_OBSERVATION,
    dynamics=EVENT_TIME_ADAPTATION_RECOVERY,
    horizons=PRESEASON_CAMP_RECOVERY_TASK.horizons,
    outcomes=PRESEASON_CAMP_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.SUPERSEDED,
    dataset_identity=IdentityReference(
        "initial_preseason_camp_public_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=INITIAL_PRESEASON_CAMP_EVALUATION,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    qualification_evaluations=(
        EMPIRICAL_ENERGY_QUALIFICATION_EVALUATION,
        POSTERIOR_COVARIANCE_QUALIFICATION_EVALUATION,
        STANDARDIZED_EUCLIDEAN_QUALIFICATION_EVALUATION,
    ),
    model_selection_evaluations=(PUBLIC_REFERENCE_SELECTION_EVALUATION,),
    disposition_note=(
        "Superseded sample/surface; direct parent is unresolved; task and world law match "
        "the canonical state."
    ),
)

CANONICAL_PRESEASON_CAMP_RECOVERY = BenchmarkDefinition(
    name="canonical_preseason_camp_recovery",
    research_question=(
        "Can pre-origin force and impulse assessments, camp exposure history, the index "
        "exposure, and known plans forecast the two observed innovations at H72 and D7 "
        "in the canonical horizon-row sample?"
    ),
    task=PRESEASON_CAMP_RECOVERY_TASK,
    observation=CAMP_HISTORY_OBSERVATION,
    dynamics=EVENT_TIME_ADAPTATION_RECOVERY,
    horizons=PRESEASON_CAMP_RECOVERY_TASK.horizons,
    outcomes=PRESEASON_CAMP_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.SUPERSEDED,
    dataset_identity=IdentityReference(
        "canonical_preseason_camp_horizon_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=CANONICAL_PRESEASON_CAMP_EVALUATION,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    parent_name="initial_preseason_camp_recovery",
    disposition_note="Canonical query surface and sample; not a new task or world law.",
)
