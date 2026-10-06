"""Eight scientifically named recovered benchmark states."""

from cmj_recovery_dynamics.benchmarks.correlated_exposure_recovery import (
    CORRELATED_EXPOSURE_RECOVERY,
)
from cmj_recovery_dynamics.benchmarks.fixed_mode_discrepancy_recovery import (
    FIXED_MODE_DISCREPANCY_RECOVERY,
)
from cmj_recovery_dynamics.benchmarks.phase_consistent_post_exposure_recovery import (
    PHASE_CONSISTENT_POST_EXPOSURE_RECOVERY,
)
from cmj_recovery_dynamics.benchmarks.preliminary_post_exposure_recovery import (
    PRELIMINARY_POST_EXPOSURE_RECOVERY,
)
from cmj_recovery_dynamics.benchmarks.preseason_camp_recovery import (
    CANONICAL_PRESEASON_CAMP_RECOVERY,
    INITIAL_PRESEASON_CAMP_RECOVERY,
)
from cmj_recovery_dynamics.benchmarks.rich_history_recovery import RICH_HISTORY_RECOVERY
from cmj_recovery_dynamics.benchmarks.threshold_response_recovery import (
    THRESHOLD_RESPONSE_RECOVERY,
)

BENCHMARK_DEFINITIONS = (
    INITIAL_PRESEASON_CAMP_RECOVERY,
    CANONICAL_PRESEASON_CAMP_RECOVERY,
    RICH_HISTORY_RECOVERY,
    PRELIMINARY_POST_EXPOSURE_RECOVERY,
    PHASE_CONSISTENT_POST_EXPOSURE_RECOVERY,
    CORRELATED_EXPOSURE_RECOVERY,
    THRESHOLD_RESPONSE_RECOVERY,
    FIXED_MODE_DISCREPANCY_RECOVERY,
)

__all__ = [
    "BENCHMARK_DEFINITIONS",
    "CANONICAL_PRESEASON_CAMP_RECOVERY",
    "CORRELATED_EXPOSURE_RECOVERY",
    "FIXED_MODE_DISCREPANCY_RECOVERY",
    "INITIAL_PRESEASON_CAMP_RECOVERY",
    "PHASE_CONSISTENT_POST_EXPOSURE_RECOVERY",
    "PRELIMINARY_POST_EXPOSURE_RECOVERY",
    "RICH_HISTORY_RECOVERY",
    "THRESHOLD_RESPONSE_RECOVERY",
]
