"""Preliminary scalar-measurement formulation of single-exposure recovery forecasting."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    UNRESOLVED_EVALUATION_IDENTITY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    BIEXPONENTIAL_EPISODE_RESPONSE,
)
from cmj_recovery_dynamics.observations.episode_summary import EPISODE_SUMMARY_OBSERVATION
from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK

PRELIMINARY_POST_EXPOSURE_RECOVERY = BenchmarkDefinition(
    name="preliminary_post_exposure_recovery",
    research_question=(
        "Can participant baseline and context, one current exposure, and four prior episodes "
        "forecast measured force and impulse innovations at H24, H48, and H72 using scalar "
        "paired-trial measurements?"
    ),
    task=POST_EXPOSURE_RECOVERY_TASK,
    observation=EPISODE_SUMMARY_OBSERVATION,
    dynamics=BIEXPONENTIAL_EPISODE_RESPONSE,
    horizons=POST_EXPOSURE_RECOVERY_TASK.horizons,
    outcomes=POST_EXPOSURE_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.SUPERSEDED,
    dataset_identity=IdentityReference(
        "preliminary_episode_measurement_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    disposition_note=(
        "Direct parent is unresolved; preliminary measurement contract without a frozen "
        "force–impulse identity."
    ),
)
