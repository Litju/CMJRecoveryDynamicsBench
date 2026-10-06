"""Initial and canonical public-sample states of the camp recovery benchmark."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    UNRESOLVED_EVALUATION_IDENTITY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    EVENT_TIME_ADAPTATION_RECOVERY,
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
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
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
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    parent_name="initial_preseason_camp_recovery",
    disposition_note="Canonical query surface and sample; not a new task or world law.",
)
