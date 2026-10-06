"""Proposed participant-weighted threshold-response recovery benchmark state."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    UNRESOLVED_EVALUATION_IDENTITY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.threshold_response import THRESHOLD_RESPONSE
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
)
from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK

THRESHOLD_RESPONSE_RECOVERY = BenchmarkDefinition(
    name="threshold_response_recovery",
    research_question=(
        "Does a participant-weighted high/low-load threshold response define a useful "
        "alternate for forecasting force and net-impulse innovations at H24, H48, and H72?"
    ),
    task=POST_EXPOSURE_RECOVERY_TASK,
    observation=PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    dynamics=THRESHOLD_RESPONSE,
    horizons=POST_EXPOSURE_RECOVERY_TASK.horizons,
    outcomes=POST_EXPOSURE_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.PROPOSED,
    dataset_identity=IdentityReference(
        "threshold_response_proposed_sample",
        ReferenceStatus.IDENTIFIED,
        "Proposed sample identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    parent_name="correlated_exposure_recovery",
    disposition_note="Proposed alternate, not an accepted successor formulation.",
)
