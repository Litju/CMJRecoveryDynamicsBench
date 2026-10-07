"""Active candidate with fixed response modes and bounded smooth discrepancy."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    FIXED_MODE_DISCREPANCY_RESPONSE,
)
from cmj_recovery_dynamics.metrics.catalog import (
    FIXED_MODE_DISCREPANCY_EVALUATION,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    PREDICTIVE_PROGRESS_EVALUATION,
    PROGRESS_RATIO_EVALUATION,
    RELATIVE_PROGRESS_GAIN_EVALUATION,
    RELATIVE_PROGRESS_LOSS_EVALUATION,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
)
from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK

FIXED_MODE_DISCREPANCY_RECOVERY = BenchmarkDefinition(
    name="fixed_mode_discrepancy_recovery",
    research_question=(
        "Can fixed mathematical response modes with bounded smooth discrepancy forecast "
        "force and net-impulse innovations at H24, H48, and H72 under correlated exposures?"
    ),
    task=POST_EXPOSURE_RECOVERY_TASK,
    observation=PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    dynamics=FIXED_MODE_DISCREPANCY_RESPONSE,
    horizons=POST_EXPOSURE_RECOVERY_TASK.horizons,
    outcomes=POST_EXPOSURE_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.ACTIVE_CANDIDATE,
    dataset_identity=IdentityReference(
        "fixed_mode_recovery_candidate_sample",
        ReferenceStatus.IDENTIFIED,
        "Candidate split identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=FIXED_MODE_DISCREPANCY_EVALUATION,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    research_evaluations=(
        POST_EXPOSURE_RESEARCH_EVALUATION,
        PREDICTIVE_PROGRESS_EVALUATION,
        PROGRESS_RATIO_EVALUATION,
        RELATIVE_PROGRESS_GAIN_EVALUATION,
        RELATIVE_PROGRESS_LOSS_EVALUATION,
    ),
    parent_name="correlated_exposure_recovery",
    disposition_note=(
        "Active candidate; fixed modes are mathematical anchors, not biological compartments."
    ),
)
