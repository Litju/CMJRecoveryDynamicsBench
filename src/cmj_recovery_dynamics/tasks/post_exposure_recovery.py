"""Single-exposure recovery forecasting with no later material exposure through H72."""

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

POST_EXPOSURE_RECOVERY_TASK = TaskDefinition(
    name="post_exposure_recovery",
    task_type=TaskType.POST_EXPOSURE_RECOVERY,
    research_question=(
        "Can baseline-relative force and net-impulse innovations be forecast at H24, H48, "
        "and H72 from participant context, one current exposure, and four prior measured "
        "episodes when no additional material exposure occurs through H72?"
    ),
    estimand=Estimand(
        name="single_exposure_innovation",
        estimand_type=EstimandType.SINGLE_EXPOSURE_INNOVATION,
        target_semantics=(
            "Observed additive change from a dedicated pre-exposure baseline, including "
            "measurement and episode discrepancy."
        ),
    ),
    horizons=(
        ForecastHorizon.H24,
        ForecastHorizon.H48,
        ForecastHorizon.H72,
    ),
    horizon_windows=(
        ForecastWindow(ForecastHorizon.H24, 24, 24),
        ForecastWindow(ForecastHorizon.H48, 48, 48),
        ForecastWindow(ForecastHorizon.H72, 72, 72),
    ),
    outcomes=CANONICAL_OUTCOMES,
    exposure_policy=ExposurePolicy.ONE_CURRENT_EXPOSURE_THROUGH_H72,
    baseline_definition="Three-trial dedicated baseline about two hours before exposure at t=0.",
    prediction_time_information=(
        "Use the current baseline and exposure, participant context, and four prior episodes; "
        "future labels are unavailable. No additional material exposure occurs through H72."
    ),
)
