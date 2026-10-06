"""The two recovered recovery-forecasting estimands."""

from cmj_recovery_dynamics.tasks.post_exposure_recovery import POST_EXPOSURE_RECOVERY_TASK
from cmj_recovery_dynamics.tasks.preseason_camp_recovery import PRESEASON_CAMP_RECOVERY_TASK

TASKS = (PRESEASON_CAMP_RECOVERY_TASK, POST_EXPOSURE_RECOVERY_TASK)

__all__ = [
    "POST_EXPOSURE_RECOVERY_TASK",
    "PRESEASON_CAMP_RECOVERY_TASK",
    "TASKS",
]
