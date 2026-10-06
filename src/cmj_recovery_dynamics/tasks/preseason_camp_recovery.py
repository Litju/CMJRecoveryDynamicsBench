"""Longitudinal camp-state forecasting after a multi-exposure trajectory."""

from cmj_recovery_dynamics.contracts import (
    CANONICAL_OUTCOMES,
    Estimand,
    EstimandType,
    ExposurePolicy,
    ForecastHorizon,
    ForecastWindow,
    TaskDefinition,
    TaskType,
)

PRESEASON_CAMP_RECOVERY_TASK = TaskDefinition(
    name="preseason_camp_recovery",
    task_type=TaskType.PRESEASON_CAMP_RECOVERY,
    research_question=(
        "Can baseline-relative force and net-impulse innovations be forecast at H72 and D7 "
        "from pre-origin monitoring, exposure history, and plans known at origin in a "
        "synthetic camp trajectory?"
    ),
    estimand=Estimand(
        name="multi_exposure_camp_state_innovation",
        estimand_type=EstimandType.CAMP_STATE_INNOVATION,
        target_semantics=(
            "Observed additive change from the pre-index reference after the camp exposure "
            "trajectory, including exposures through each query horizon."
        ),
    ),
    horizons=(ForecastHorizon.H72, ForecastHorizon.D7),
    horizon_windows=(
        ForecastWindow(ForecastHorizon.H72, 66, 78),
        ForecastWindow(ForecastHorizon.D7, 156, 180),
    ),
    outcomes=CANONICAL_OUTCOMES,
    exposure_policy=ExposurePolicy.CAMP_TRAJECTORY_THROUGH_HORIZON,
    baseline_definition=(
        "Two latest valid qualifying pre-index assessment summaries, 24–240 hours before origin."
    ),
    prediction_time_information=(
        "Use only history available before origin and plans known at origin; realized future "
        "camp exposure and target labels are unavailable."
    ),
)
