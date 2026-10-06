"""Correlated-exposure participant-conditioned recovery benchmark state."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    UNRESOLVED_EVALUATION_IDENTITY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
    CORRELATED_EXPOSURE_RESPONSE,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
)
from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK

CORRELATED_EXPOSURE_RECOVERY = BenchmarkDefinition(
    name="correlated_exposure_recovery",
    research_question=(
        "How does a correlated four-factor exposure distribution alter single-exposure "
        "force and net-impulse innovation forecasting at H24, H48, and H72?"
    ),
    task=POST_EXPOSURE_RECOVERY_TASK,
    observation=PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    dynamics=CORRELATED_EXPOSURE_RESPONSE,
    horizons=POST_EXPOSURE_RECOVERY_TASK.horizons,
    outcomes=POST_EXPOSURE_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.SUPERSEDED,
    dataset_identity=IdentityReference(
        "correlated_exposure_recovery_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    parent_name="phase_consistent_post_exposure_recovery",
    disposition_note="Material correlated exposure-distribution change; later redesigned.",
)
