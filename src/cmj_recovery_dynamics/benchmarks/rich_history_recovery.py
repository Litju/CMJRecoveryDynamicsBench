"""Richer camp-history recovery-forecasting benchmark state."""

from cmj_recovery_dynamics.contracts import (
    PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    UNRESOLVED_EVALUATION_IDENTITY,
    BenchmarkDefinition,
    BenchmarkStatus,
    IdentityReference,
    ReferenceStatus,
)
from cmj_recovery_dynamics.dynamics.fitness_fatigue_impulse_response import (
    FITNESS_FATIGUE_IMPULSE_RESPONSE,
)
from cmj_recovery_dynamics.observations.rich_monitoring import RICH_MONITORING_OBSERVATION
from cmj_recovery_dynamics.tasks.preseason_camp_recovery import PRESEASON_CAMP_RECOVERY_TASK

RICH_HISTORY_RECOVERY = BenchmarkDefinition(
    name="rich_history_camp_recovery",
    research_question=(
        "Can richer monitoring, participant context, variable assessment histories, and "
        "known plans forecast camp-state force and impulse innovations at H72 and D7?"
    ),
    task=PRESEASON_CAMP_RECOVERY_TASK,
    observation=RICH_MONITORING_OBSERVATION,
    dynamics=FITNESS_FATIGUE_IMPULSE_RESPONSE,
    horizons=PRESEASON_CAMP_RECOVERY_TASK.horizons,
    outcomes=PRESEASON_CAMP_RECOVERY_TASK.outcomes,
    status=BenchmarkStatus.RETIRED,
    dataset_identity=IdentityReference(
        "rich_history_camp_sample",
        ReferenceStatus.IDENTIFIED,
        "Identity reference only; no dataset or private payload is included.",
    ),
    evaluation_identity=UNRESOLVED_EVALUATION_IDENTITY,
    claim_boundary=PERFORMANCE_ONLY_CLAIM_BOUNDARY,
    disposition_note="Retired formulation; its direct scientific parent is unresolved.",
)
