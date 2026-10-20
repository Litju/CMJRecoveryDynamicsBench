"""Phase-consistent force/impulse measurement state of single-exposure recovery forecasting."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    BIEXPONENTIAL_EPISODE_RESPONSE,
)
from cmj_recovery_dynamics.metrics.catalog import (
    PHASE_CONSISTENT_POST_EXPOSURE_EVALUATION,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    PREDICTIVE_PROGRESS_EVALUATION,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
)
from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK

PHASE_CONSISTENT_POST_EXPOSURE_RECOVERY = BenchmarkDefinition(
    name="phase_consistent_post_exposure_recovery",
    research_question=(
        "Can participant baseline and context, one current exposure, and four prior episodes "
        "forecast force and net-impulse innovations at H24, H48, and H72 when both outcomes "
        "are derived from the same concentric force trace?"
    ),
    task=POST_EXPOSURE_RECOVERY_TASK,
    observation=PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    dynamics=BIEXPONENTIAL_EPISODE_RESPONSE,
    horizons=POST_EXPOSURE_RECOVERY_TASK.horizons,
    outcomes=POST_EXPOSURE_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.SUPERSEDED,
    dataset_identity=IdentityReference(
        "phase_consistent_episode_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=PHASE_CONSISTENT_POST_EXPOSURE_EVALUATION,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    research_evaluations=(
        POST_EXPOSURE_RESEARCH_EVALUATION,
        PREDICTIVE_PROGRESS_EVALUATION,
    ),
    parent_name="preliminary_post_exposure_recovery",
    disposition_note="Observation-law repair; the episode response law is retained.",
)
