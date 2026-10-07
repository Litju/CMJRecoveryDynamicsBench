"""Evidence-backed evaluation definitions; research and qualification stay separate."""

from __future__ import annotations

from cmj_recovery_dynamics.contracts import (
    AggregationLevel,
    CalibrationReferenceStatus,
    EvaluationDefinition,
    EvaluationImplementation,
    ForecastHorizon,
    MetricCategory,
    MetricUnits,
    MissingCellPolicy,
    NormalizationRule,
    OptimizationDirection,
    OutcomeVariable,
    ProductionAcceptance,
    TargetCell,
    WeightedOutcome,
    WeightedTargetCell,
    WeightingRule,
)
from cmj_recovery_dynamics.metrics.scoring import (
    INITIAL_CAMP_CELLS,
    POST_EXPOSURE_RESEARCH_CELLS,
    RICH_HISTORY_CELL_MIN_ROWS,
    RICH_HISTORY_CELLS,
    THRESHOLD_RESPONSE_CELLS,
)

_CAMP_HORIZONS = (ForecastHorizon.H72, ForecastHorizon.D7)
_POST_HORIZONS = (ForecastHorizon.H24, ForecastHorizon.H48, ForecastHorizon.H72)
_T01_BENCHMARKS = (
    "initial_preseason_camp_recovery",
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
)
_POST_EXPOSURE_RESEARCH_BENCHMARKS = (
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "fixed_mode_discrepancy_recovery",
)
_NO_NONFINITE = "reject every non-finite target, prediction, scale, and computed result"


def _equal_cell_weights(cells: tuple[TargetCell, ...]) -> tuple[WeightedTargetCell, ...]:
    return tuple(WeightedTargetCell(cell, 1.0) for cell in cells)


def _camp_score(
    *, name: str, benchmark: str, floor: float, unit_interpretation: str
) -> EvaluationDefinition:
    return EvaluationDefinition(
        name=name,
        category=MetricCategory.BENCHMARK_SCORE,
        implementation_status=EvaluationImplementation.IMPLEMENTED,
        production_acceptance=ProductionAcceptance.ACCEPTED_HISTORICAL,
        formula=(
            "For each of four outcome × horizon cells: r=RMSE(prediction, truth)/"
            "population_sd(truth, ddof=0), with raw-unit RMSE when SD=0; "
            "u=clip((floor-r)/floor, 0, 1); aggregate the four u values with "
            "equal weights; return the task-locked piecewise-linear map through "
            "(0,0), (reference_progress,0.5), (1,1)."
        ),
        optimization_direction=OptimizationDirection.HIGHER_IS_BETTER,
        raw_metric_direction=OptimizationDirection.LOWER_IS_BETTER,
        units=MetricUnits.DIMENSIONLESS,
        target_variables=tuple(OutcomeVariable),
        horizons=_CAMP_HORIZONS,
        scoring_cells=INITIAL_CAMP_CELLS,
        cell_definition=(
            "Four cells: two outcomes × {H72,D7}; one selected "
            "origin contributes to each horizon-specific outcome "
            "cell."
        ),
        normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
        normalization_reference=(
            "The scoring sample truth for the same outcome × horizon cell; population SD, ddof=0."
        ),
        aggregation_order=(
            AggregationLevel.ORIGIN,
            AggregationLevel.SCORING_CELL,
            AggregationLevel.OUTCOME,
            AggregationLevel.BENCHMARK,
        ),
        scoring_unit=AggregationLevel.ORIGIN,
        weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
        cell_weights=_equal_cell_weights(INITIAL_CAMP_CELLS),
        missing_cell_policy=MissingCellPolicy.REJECT,
        non_finite_policy=_NO_NONFINITE,
        minimum_rows_per_cell=1,
        normalization_floor=floor,
        perfect_metric_value=0.0,
        score_bounds=(0.0, 1.0),
        calibration_reference=(
            "Author-locked reference predictor aggregate progress; "
            "x_ref is not present in the public M1 evidence."
        ),
        calibration_reference_status=CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC,
        final_score_interpretation=(
            f"Dimensionless calibrated score in [0,1], higher is better; {unit_interpretation} "
            "The reference predictor maps to 0.5 and a perfect forecast maps to 1.0."
        ),
        implementation_id="calibrated_benchmark_score",
        raw_metric_units=MetricUnits.DIMENSIONLESS_WITH_TARGET_UNIT_FALLBACK,
        compatible_benchmarks=(benchmark,),
        comparable_result_families=(
            (
                "Only results with the same dataset, selected origins, "
                "four target cells, floor, and locked curve."
            ),
        ),
    )


INITIAL_PRESEASON_CAMP_EVALUATION = _camp_score(
    name="initial_camp_population_normalized_rmse_score",
    benchmark="initial_preseason_camp_recovery",
    floor=1.01,
    unit_interpretation=(
        "The 1.01 finite-bank floor means a mean-predictor "
        "normalized error of 1 can receive small positive "
        "progress."
    ),
)

CANONICAL_PRESEASON_CAMP_EVALUATION = _camp_score(
    name="canonical_camp_population_normalized_rmse_score",
    benchmark="canonical_preseason_camp_recovery",
    floor=1.0,
    unit_interpretation=(
        "the canonical task uses the exact within-cell population-mean predictor floor of 1.0."
    ),
)

RICH_HISTORY_EVALUATION = EvaluationDefinition(
    name="rich_history_24_cell_normalized_rmse_score",
    category=MetricCategory.BENCHMARK_SCORE,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.ACCEPTED_HISTORICAL,
    formula=(
        "For each outcome, average RMSE_s/population_sd_s(truth, ddof=0) equally over "
        "12 cells: six history strata × {H72,D7}; a zero-SD stratum contributes raw RMSE. "
        "Map each outcome mean r to clip((1-r)/1,0,1), average the two outcomes equally, "
        "then apply the task-locked curve through (0,0), (reference_progress,0.5), (1,1)."
    ),
    optimization_direction=OptimizationDirection.HIGHER_IS_BETTER,
    raw_metric_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_CAMP_HORIZONS,
    scoring_cells=RICH_HISTORY_CELLS,
    cell_definition=(
        "24 equal-weight terms: two outcomes × {H72,D7} × six strata. F2 is the count of valid "
        "assessments strictly after the latest prior exposure (0→L0, 1→L1, >=2→L2). "
        "F3 is clean iff at least six assessments are valid and the minimum trial count among "
        "valid assessments is >=2; otherwise degraded."
    ),
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "Within each outcome × horizon × history-stratum row set; population SD, ddof=0."
    ),
    aggregation_order=(
        AggregationLevel.PREDICTION_ROW,
        AggregationLevel.SCORING_CELL,
        AggregationLevel.OUTCOME,
        AggregationLevel.BENCHMARK,
    ),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(RICH_HISTORY_CELLS),
    target_weights=tuple(WeightedOutcome(outcome, 1.0) for outcome in OutcomeVariable),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=RICH_HISTORY_CELL_MIN_ROWS,
    normalization_floor=1.0,
    perfect_metric_value=0.0,
    score_bounds=(0.0, 1.0),
    calibration_reference=(
        "Author-locked reference predictor aggregate progress; "
        "x_ref is not present in the public M1 evidence."
    ),
    calibration_reference_status=CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC,
    final_score_interpretation=(
        "Dimensionless calibrated score in [0,1], higher is "
        "better. Each outcome's 12 strata are averaged "
        "before clipping its progress; the two outcome progresses are then equally averaged."
    ),
    implementation_id="rich_history_target_metrics_then_calibrated_benchmark_score",
    raw_metric_units=MetricUnits.DIMENSIONLESS_WITH_TARGET_UNIT_FALLBACK,
    compatible_benchmarks=("rich_history_camp_recovery",),
    comparable_result_families=(
        (
            "Same rich-history formulation and 24 cells; "
            "public-validation and original hidden-bank results "
            "retain a split caveat."
        ),
    ),
)

THRESHOLD_RESPONSE_PROPOSED_EVALUATION = EvaluationDefinition(
    name="threshold_response_12_cell_normalized_rmse_score",
    category=MetricCategory.BENCHMARK_SCORE,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.PROPOSED_UNRESOLVED,
    formula=(
        "Score each of 12 cells independently: outcome × horizon {H24,H48,H72} × "
        "current-load regime {low,high}; each cell is RMSE/population_sd(truth, ddof=0), "
        "with raw-unit RMSE if SD=0. Map each cell with clip((1-r)/1,0,1), average all "
        "12 progresses equally, and apply the task-locked curve through (0,0), "
        "(reference_progress,0.5), (1,1). The regime is high iff the mean of the seven "
        "support-scaled, [0,1]-clipped current-exposure primitives is >=0.5."
    ),
    optimization_direction=OptimizationDirection.HIGHER_IS_BETTER,
    raw_metric_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=THRESHOLD_RESPONSE_CELLS,
    cell_definition=(
        "12 cells: two outcomes × {H24,H48,H72} × {low,high}. Each current-exposure primitive "
        "is scaled by its public support, clipped to [0,1], and averaged equally: duration "
        "45–120 min; distance 3,000–13,000 m; high-speed distance 0–2,000 m; sprint distance "
        "0–600 m; acceleration/deceleration counts 0–150 each; session RPE 2–10. High is >=0.5."
    ),
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "Within each horizon × current-load-regime × outcome cell; population SD, ddof=0."
    ),
    aggregation_order=(
        AggregationLevel.PREDICTION_ROW,
        AggregationLevel.SCORING_CELL,
        AggregationLevel.BENCHMARK,
    ),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(THRESHOLD_RESPONSE_CELLS),
    missing_cell_policy=MissingCellPolicy.MASK_ROWS_OUTSIDE_CELL,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    normalization_floor=1.0,
    perfect_metric_value=0.0,
    score_bounds=(0.0, 1.0),
    calibration_reference=(
        "Author-locked reference predictor aggregate progress; "
        "x_ref is not present in the public M1 evidence."
    ),
    calibration_reference_status=CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC,
    final_score_interpretation=(
        "Implemented proposed score contract only. It is not an "
        "accepted production scorer; higher calibrated score is "
        "better."
    ),
    implementation_id="cellwise_normalized_rmse_then_calibrated_benchmark_score",
    raw_metric_units=MetricUnits.DIMENSIONLESS_WITH_TARGET_UNIT_FALLBACK,
    compatible_benchmarks=("threshold_response_recovery",),
    comparable_result_families=("UNKNOWN: no accepted result family is preserved.",),
)


def _unimplemented_post_exposure(name: str, benchmark: str) -> EvaluationDefinition:
    return EvaluationDefinition(
        name=name,
        category=MetricCategory.UNIMPLEMENTED_EVALUATION,
        implementation_status=EvaluationImplementation.NOT_IMPLEMENTED,
        production_acceptance=ProductionAcceptance.NONE,
        formula="UNKNOWN",
        optimization_direction=OptimizationDirection.UNKNOWN,
        units=MetricUnits.UNKNOWN,
        target_variables=tuple(OutcomeVariable),
        horizons=_POST_HORIZONS,
        scoring_cells=(),
        normalization_rule=NormalizationRule.UNKNOWN,
        normalization_reference="UNKNOWN",
        aggregation_order=(),
        scoring_unit=AggregationLevel.UNKNOWN,
        weighting_rule=WeightingRule.UNKNOWN,
        cell_weights=(),
        missing_cell_policy=MissingCellPolicy.UNKNOWN,
        non_finite_policy="UNKNOWN",
        minimum_rows_per_cell=None,
        final_score_interpretation="UNKNOWN: no accepted production evaluation is implemented.",
        compatible_benchmarks=(benchmark,),
        comparable_result_families=(),
    )


PRELIMINARY_POST_EXPOSURE_EVALUATION = _unimplemented_post_exposure(
    "preliminary_post_exposure_production_evaluation",
    "preliminary_post_exposure_recovery",
)
PHASE_CONSISTENT_POST_EXPOSURE_EVALUATION = _unimplemented_post_exposure(
    "phase_consistent_post_exposure_production_evaluation",
    "phase_consistent_post_exposure_recovery",
)
CORRELATED_EXPOSURE_EVALUATION = _unimplemented_post_exposure(
    "correlated_exposure_production_evaluation",
    "correlated_exposure_recovery",
)
FIXED_MODE_DISCREPANCY_EVALUATION = _unimplemented_post_exposure(
    "fixed_mode_discrepancy_production_evaluation",
    "fixed_mode_discrepancy_recovery",
)

POST_EXPOSURE_RESEARCH_EVALUATION = EvaluationDefinition(
    name="six_cell_mean_cellwise_normalized_rmse",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "For each of six outcome × horizon cells, compute RMSE/population_sd(truth, ddof=0); "
        "reject zero-SD cells; report the equal-weight mean of the six cell errors."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=POST_EXPOSURE_RESEARCH_CELLS,
    cell_definition="Six cells: two outcomes × {H24,H48,H72}; no further stratification.",
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference="Within each validation outcome × horizon cell; population SD, ddof=0.",
    aggregation_order=(AggregationLevel.PREDICTION_ROW, AggregationLevel.SCORING_CELL),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(POST_EXPOSURE_RESEARCH_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=2,
    uncertainty_unit=AggregationLevel.CAMP,
    uncertainty_protocol=(
        "Paired intervals use the same 5,000 PCG64 resamples (seed 49,505,000) "
        "of all rows from 16 validation camps for every model; "
        "the point metric remains row-weighted within each of six cells."
    ),
    final_score_interpretation=(
        "Dimensionless, nonnegative with no finite upper bound; lower is better; 1 corresponds to "
        "the per-cell held-out-mean constant baseline. "
        "It is not a production benchmark score."
    ),
    implementation_id="mean_cellwise_normalized_rmse",
    compatible_benchmarks=_POST_EXPOSURE_RESEARCH_BENCHMARKS,
    comparable_result_families=(
        (
            "Direct comparison is limited to models from the same "
            "formulation, data, six cells, and paired "
            "camp-resampling protocol."
        ),
    ),
)

PREDICTIVE_PROGRESS_EVALUATION = EvaluationDefinition(
    name="predictive_progress_over_cell_mean_baseline",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="progress = 1 - six_cell_mean_cellwise_normalized_rmse",
    optimization_direction=OptimizationDirection.HIGHER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=POST_EXPOSURE_RESEARCH_CELLS,
    cell_definition="Six cells: two outcomes × {H24,H48,H72}; no further stratification.",
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "A normalized error of 1 is the cell-mean constant predictor; progress is not clipped."
    ),
    aggregation_order=(AggregationLevel.PREDICTION_ROW, AggregationLevel.SCORING_CELL),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(POST_EXPOSURE_RESEARCH_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=2,
    final_score_interpretation=(
        "Dimensionless progress with upper bound 1 and no finite lower bound; "
        "positive beats the reference, "
        "zero ties it, negative underperforms it."
    ),
    implementation_id="predictive_progress",
    compatible_benchmarks=_POST_EXPOSURE_RESEARCH_BENCHMARKS,
)

PROGRESS_RATIO_EVALUATION = EvaluationDefinition(
    name="predictive_progress_ratio",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="(1 - numerator_error) / (1 - denominator_reference_error)",
    optimization_direction=OptimizationDirection.HIGHER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=POST_EXPOSURE_RESEARCH_CELLS,
    cell_definition="Six cells: two outcomes × {H24,H48,H72}; no further stratification.",
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "Both progress terms use the normalized-error-1 cell-mean constant baseline."
    ),
    aggregation_order=(AggregationLevel.PREDICTION_ROW, AggregationLevel.SCORING_CELL),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(POST_EXPOSURE_RESEARCH_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=(
        "reject non-finite values and denominator progress with absolute value <= 1e-12"
    ),
    minimum_rows_per_cell=2,
    final_score_interpretation=(
        "Ratio above 1 means the numerator model makes more "
        "progress than the explicit denominator reference; it has no universal finite range; "
        "no universal threshold is implied."
    ),
    implementation_id="progress_ratio",
    compatible_benchmarks=("correlated_exposure_recovery", "fixed_mode_discrepancy_recovery"),
    comparable_result_families=(
        (
            "For local reconstruction, numerator is the best local "
            "structured predictor and denominator is the best "
            "legitimate empirical frontier on the same validation "
            "cells."
        ),
    ),
)

RELATIVE_PROGRESS_LOSS_EVALUATION = EvaluationDefinition(
    name="relative_progress_loss_from_model_component",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="(progress(full_model) - progress(comparator)) / progress(full_model)",
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=POST_EXPOSURE_RESEARCH_CELLS,
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "Each progress term is 1 - six-cell normalized RMSE, relative to the cell-mean constant."
    ),
    aggregation_order=(AggregationLevel.PREDICTION_ROW, AggregationLevel.SCORING_CELL),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(POST_EXPOSURE_RESEARCH_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy="reject non-finite values and full-model progress <= 0",
    minimum_rows_per_cell=2,
    final_score_interpretation=(
        "Positive loss means the comparator removes some "
        "full-model progress; historical 5%/10% gates are "
        "protocol thresholds, not universal constants."
    ),
    implementation_id="relative_progress_loss",
    compatible_benchmarks=("correlated_exposure_recovery", "fixed_mode_discrepancy_recovery"),
)

RELATIVE_PROGRESS_GAIN_EVALUATION = EvaluationDefinition(
    name="relative_progress_gain_over_reference",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="(progress(candidate) - progress(reference)) / progress(reference)",
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_POST_HORIZONS,
    scoring_cells=POST_EXPOSURE_RESEARCH_CELLS,
    cell_definition="Six cells: two outcomes × {H24,H48,H72}; no further stratification.",
    normalization_rule=NormalizationRule.POPULATION_STANDARD_DEVIATION,
    normalization_reference=(
        "Each progress term is 1 - six-cell normalized RMSE, relative to the cell-mean constant."
    ),
    aggregation_order=(AggregationLevel.PREDICTION_ROW, AggregationLevel.SCORING_CELL),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(POST_EXPOSURE_RESEARCH_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy="reject non-finite values and reference progress <= 0",
    minimum_rows_per_cell=2,
    final_score_interpretation=(
        "Positive gain means the candidate makes more progress than the reference; "
        "historical validation cutoffs are protocol-specific, not universal constants."
    ),
    implementation_id="relative_progress_gain",
    compatible_benchmarks=("fixed_mode_discrepancy_recovery",),
)

PUBLIC_REFERENCE_SELECTION_EVALUATION = EvaluationDefinition(
    name="four_cell_training_scale_normalized_rmse_selection_metric",
    category=MetricCategory.MODEL_SELECTION_METRIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "For each of four H72/D7 × outcome cells, validation RMSE is divided by the "
        "same cell's public-training sample SD (ddof=1); average the four values equally. "
        "Across a candidate's two complete seeds, use their arithmetic mean; lower is better."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_CAMP_HORIZONS,
    scoring_cells=INITIAL_CAMP_CELLS,
    cell_definition=(
        "Four cells: two outcomes × {H72,D7}; horizon-specific "
        "validation rows are not pooled before cell RMSE."
    ),
    normalization_rule=NormalizationRule.TRAINING_SAMPLE_STANDARD_DEVIATION,
    normalization_reference="Public TRAIN target SD within outcome × horizon; sample SD, ddof=1.",
    aggregation_order=(
        AggregationLevel.PREDICTION_ROW,
        AggregationLevel.SCORING_CELL,
        AggregationLevel.REPEATED_RUN,
    ),
    scoring_unit=AggregationLevel.PREDICTION_ROW,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=_equal_cell_weights(INITIAL_CAMP_CELLS),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative dimensionless error with no finite upper bound; public reference "
        "selection metric only. Candidate "
        "eligibility and tie-break thresholds remain "
        "protocol-specific; this is not the hidden benchmark "
        "score."
    ),
    implementation_id="mean_training_scale_normalized_rmse_and_two_seed_mean",
    compatible_benchmarks=("initial_preseason_camp_recovery",),
    comparable_result_families=(
        (
            "The public linear baseline and the later two-seed "
            "reference selection use this same validation metric and "
            "split."
        ),
    ),
)

STANDARDIZED_EUCLIDEAN_QUALIFICATION_EVALUATION = EvaluationDefinition(
    name="mean_standardized_euclidean_prediction_error",
    category=MetricCategory.QUALIFICATION_STATISTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="mean_origin ||(prediction - truth) / public_train_axis_sd||₂",
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=_CAMP_HORIZONS,
    scoring_cells=INITIAL_CAMP_CELLS,
    cell_definition=(
        "Four horizon × outcome validation cells; each origin has both horizons and both outcomes."
    ),
    normalization_rule=NormalizationRule.EXPLICIT_AXIS_SCALES,
    normalization_reference=(
        "Four target-axis scales are public-TRAIN sample SDs (ddof=1), floored at 1e-9."
    ),
    aggregation_order=(AggregationLevel.ORIGIN, AggregationLevel.BENCHMARK),
    scoring_unit=AggregationLevel.ORIGIN,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative dimensionless residual with no finite upper bound; lower is a "
        "qualification signal-vs-constant diagnostic; "
        "it is not the "
        "point-forecast benchmark score or the proper ensemble "
        "energy score."
    ),
    implementation_id="mean_standardized_euclidean_error",
    compatible_benchmarks=("initial_preseason_camp_recovery",),
)

EMPIRICAL_ENERGY_QUALIFICATION_EVALUATION = EvaluationDefinition(
    name="finite_ensemble_empirical_energy_score",
    category=MetricCategory.QUALIFICATION_STATISTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "mean_i ||(X_i-y)/s||₂ - (1/(2n²)) sum_{i,j} ||(X_i-X_j)/s||₂; "
        "the V-statistic includes zero diagonal pairs and members have equal weight."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=(),
    scoring_cells=(),
    cell_definition=(
        "One two-outcome forecast vector per scored observation; "
        "one horizon per call, with no cross-horizon aggregation."
    ),
    normalization_rule=NormalizationRule.EXPLICIT_AXIS_SCALES,
    normalization_reference="Caller-supplied positive force and impulse scales in native units.",
    aggregation_order=(AggregationLevel.ENSEMBLE_MEMBER,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ENSEMBLE_MEMBERS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative dimensionless proper score with no finite upper bound; "
        "qualification-only for a two-outcome "
        "predictive sample; never attached to the point-forecast "
        "benchmark definitions."
    ),
    implementation_id="empirical_energy_score",
    compatible_benchmarks=("initial_preseason_camp_recovery",),
)

POSTERIOR_ENERGY_RESEARCH_EVALUATION = EvaluationDefinition(
    name="prior_whitened_posterior_energy_score",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "After z=L⁻¹(x−μ₀), Σ₀=LLᵀ: mean_i ||z_i-z_y||₂ - "
        "(1/(n(n−1))) sum_{i<j} ||z_i-z_j||₂; the unbiased U-statistic omits self-pairs."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference=(
        "Context-conditioned public prior mean and covariance "
        "over four statistical sensitivity coordinates."
    ),
    aggregation_order=(AggregationLevel.ENSEMBLE_MEMBER, AggregationLevel.POSTERIOR_CASE),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ENSEMBLE_MEMBERS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Dimensionless finite-sample proper score; lower is better and the unbiased "
        "estimate may be negative. It is from a separate manufactured identification "
        "study and does not measure point-forecast benchmark "
        "performance."
    ),
    implementation_id="mean_prior_whitened_energy_score",
    target_names=(
        "volume_sensitivity",
        "speed_sensitivity",
        "change_of_speed_sensitivity",
        "internal_load_sensitivity",
    ),
)

POSTERIOR_ENERGY_DIFFERENCE_EVALUATION = EvaluationDefinition(
    name="paired_prior_whitened_energy_score_difference",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="mean_case(energy_score_first - energy_score_second) on paired held-out histories",
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference="Both scores use the same case-specific public prior whitening.",
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Positive first-minus-second difference means the first posterior scores worse; "
        "comparisons require paired held-out histories."
    ),
    implementation_id="paired_score_difference",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

POSTERIOR_ENERGY_REGRET_EVALUATION = EvaluationDefinition(
    name="prior_whitened_energy_score_regret",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="E||X−Y|| - 0.5 E||X−X'|| - 0.5 E||Y−Y'|| in prior-whitened space",
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference=(
        "Forecast and exact-reference posterior samples use the same "
        "context-conditioned prior whitening."
    ),
    aggregation_order=(AggregationLevel.ENSEMBLE_MEMBER, AggregationLevel.POSTERIOR_CASE),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ENSEMBLE_MEMBERS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=2,
    final_score_interpretation=(
        "Finite-sample posterior energy-regret estimate; negative estimates can occur "
        "while its expectation is "
        "non-negative, with no finite upper bound."
    ),
    implementation_id="prior_whitened_energy_score_regret",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

VARIOGRAM_RESEARCH_EVALUATION = EvaluationDefinition(
    name="prior_whitened_variogram_score_order_half",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Equal-pair mean of (mean_sample |zᵢ-zⱼ|^0.5 - |z_truth,ᵢ-z_truth,ⱼ|^0.5)^2 "
        "over all unordered coordinate pairs in prior-whitened space."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference=(
        "Same context-conditioned public prior whitening as the separate posterior study."
    ),
    aggregation_order=(AggregationLevel.ENSEMBLE_MEMBER, AggregationLevel.POSTERIOR_CASE),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative dependence diagnostic with no finite upper bound; "
        "no score blend or benchmark use is defined."
    ),
    implementation_id="mean_prior_whitened_variogram_score",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

VARIOGRAM_REGRET_RESEARCH_EVALUATION = EvaluationDefinition(
    name="prior_whitened_variogram_score_regret_order_half",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Equal-pair mean of (mean_forecast |Xᵢ−Xⱼ|^0.5 - "
        "mean_reference |Yᵢ−Yⱼ|^0.5)^2 in prior-whitened space."
    ),
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference=(
        "Same context-conditioned public prior whitening for forecast and reference samples."
    ),
    aggregation_order=(AggregationLevel.ENSEMBLE_MEMBER, AggregationLevel.POSTERIOR_CASE),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_SCORING_CELLS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative separate dependence diagnostic with no finite upper bound; "
        "no blend with the proper primary score is defined."
    ),
    implementation_id="prior_whitened_variogram_score_regret",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

PARAMETER_RMSE_RESEARCH_EVALUATION = EvaluationDefinition(
    name="posterior_parameter_root_mean_square_error",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="sqrt(mean_{case,coordinate} (posterior_mean - true_parameter)^2)",
    optimization_direction=OptimizationDirection.LOWER_IS_BETTER,
    units=MetricUnits.PARAMETER_UNITS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.NONE,
    normalization_reference=(
        "The preserved posterior summary computes RMSE on the "
        "four statistical sensitivity coordinates without "
        "whitening; the result registry's 'prior-whitened' unit "
        "label conflicts with that code."
    ),
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Research-only parameter recovery diagnostic; it is not forecast accuracy."
    ),
    implementation_id="parameter_root_mean_square_error",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
    comparable_result_families=("Different history lengths are distinct comparison strata.",),
)

GAUSSIAN_KL_RESEARCH_EVALUATION = EvaluationDefinition(
    name="posterior_to_prior_gaussian_kl_divergence",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=("0.5 × [tr(Σ₀⁻¹Σ₁) + (μ₀−μ₁)ᵀΣ₀⁻¹(μ₀−μ₁) − d + ln(detΣ₀/detΣ₁)]"),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.NATS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.NONE,
    normalization_reference=(
        "Context-conditioned prior Gaussian for the same four sensitivity coordinates."
    ),
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative information-gain diagnostic in nats; "
        "not a predictive score or universal optimization target."
    ),
    implementation_id="gaussian_kl_divergence",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

POSTERIOR_COVERAGE_QUALIFICATION_EVALUATION = EvaluationDefinition(
    name="posterior_marginal_and_joint_coverage",
    category=MetricCategory.QUALIFICATION_STATISTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Marginal coverage is the per-coordinate fraction with lower≤truth≤upper; "
        "joint ellipsoid coverage is the fraction with (truth−mean)ᵀΣ⁻¹(truth−mean)≤χ² cutoff."
    ),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    score_bounds=(0.0, 1.0),
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.EXPLICIT_AXIS_SCALES,
    normalization_reference=(
        "Intervals and chi-square ellipsoid cutoffs are supplied "
        "at the declared nominal coverage levels."
    ),
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Marginal and joint coverage values lie in [0,1]; calibration qualification only, "
        "not a forecast ranking score."
    ),
    implementation_id="marginal_interval_coverage_and_joint_ellipsoid_coverage",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

POSTERIOR_PREDICTIVE_RESIDUAL_QUALIFICATION_EVALUATION = EvaluationDefinition(
    name="posterior_predictive_standardized_residual_diagnostics",
    category=MetricCategory.QUALIFICATION_STATISTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "For z=(observed−predictive_mean)/predictive_sd, report mean |z| and "
        "mean I(|z|≤Φ⁻¹(0.95)) for central 90% normal predictive coverage."
    ),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.EXPLICIT_AXIS_SCALES,
    normalization_reference=(
        "Predictive standard deviation for each manufactured observation channel."
    ),
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Posterior predictive qualification only; coverage is marginal, not joint."
    ),
    implementation_id="normal_standardized_residual_diagnostics",
    target_names=("criterion_baseline_log_ratio",),
)

POSTERIOR_COVARIANCE_QUALIFICATION_EVALUATION = EvaluationDefinition(
    name="predictive_covariance_and_mahalanobis_residual",
    category=MetricCategory.QUALIFICATION_STATISTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Validate Σ as finite, exactly symmetric, positive "
        "definite and condition≤1e12; compute ||L⁻¹(y−ŷ)||₂² for "
        "Σ=LLᵀ."
    ),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=tuple(OutcomeVariable),
    horizons=(),
    scoring_cells=(),
    cell_definition="One two-target covariance matrix for a single forecast horizon.",
    normalization_rule=NormalizationRule.PRIOR_COVARIANCE_WHITENING,
    normalization_reference=(
        "Two-coordinate force/impulse residual and their declared covariance units."
    ),
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.UNKNOWN,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Forecast-object and whitening contract qualification; "
        "not attached to point-forecast definitions."
    ),
    implementation_id="validate_two_target_covariance_and_mahalanobis_squared",
    compatible_benchmarks=("initial_preseason_camp_recovery",),
)

POSTERIOR_TRACE_RESEARCH_EVALUATION = EvaluationDefinition(
    name="posterior_to_prior_covariance_trace_ratio",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula="mean_case tr(Σ_posterior) / tr(Σ_prior)",
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.NONE,
    normalization_reference="Trace of the same conditional prior covariance.",
    aggregation_order=(AggregationLevel.POSTERIOR_CASE,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EQUAL_ROWS,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "Nonnegative contraction ratio with no finite upper bound; "
        "smaller means less posterior trace, "
        "not necessarily a better calibrated posterior."
    ),
    implementation_id="posterior_trace_ratio",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

POSTERIOR_TWO_SAMPLE_AUC_EVALUATION = EvaluationDefinition(
    name="posterior_two_sample_classifier_mean_auc",
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Compute tie-corrected ROC AUC per grouped held-out "
        "fold; report the equal-fold arithmetic mean."
    ),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.AUC,
    score_bounds=(0.0, 1.0),
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.NONE,
    normalization_reference=(
        "Chance separability is AUC=0.5; this is a two-sample "
        "diagnostic, not a posterior quality score."
    ),
    aggregation_order=(AggregationLevel.REPEATED_RUN,),
    scoring_unit=AggregationLevel.POSTERIOR_CASE,
    weighting_rule=WeightingRule.EXPLICIT,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.REJECT,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=1,
    final_score_interpretation=(
        "AUC lies in [0,1]; distance from chance 0.5 indicates distinguishability, "
        "with neither direction universally better."
    ),
    implementation_id="binary_auc_and_mean_fold_auc",
    target_names=POSTERIOR_ENERGY_RESEARCH_EVALUATION.target_names,
)

PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY = EvaluationDefinition(
    name="piecewise_linear_historical_score_reanchoring",
    category=MetricCategory.COMPATIBILITY_TRANSFORM,
    implementation_status=EvaluationImplementation.IMPLEMENTED,
    production_acceptance=ProductionAcceptance.NONE,
    formula=(
        "Invert the old map through (0,0), (a_old,0.5), (1,1) to recover raw progress; "
        "apply the new map through (0,0), (a_new,0.5), (1,1)."
    ),
    optimization_direction=OptimizationDirection.DIAGNOSTIC_ONLY,
    units=MetricUnits.DIMENSIONLESS,
    score_bounds=(0.0, 1.0),
    target_variables=(),
    horizons=(),
    scoring_cells=(),
    normalization_rule=NormalizationRule.NONE,
    normalization_reference=(
        "Historical progress anchors are source-specific and are isolated in the provenance module."
    ),
    aggregation_order=(),
    scoring_unit=AggregationLevel.UNKNOWN,
    weighting_rule=WeightingRule.UNKNOWN,
    cell_weights=(),
    missing_cell_policy=MissingCellPolicy.UNKNOWN,
    non_finite_policy=_NO_NONFINITE,
    minimum_rows_per_cell=None,
    final_score_interpretation=(
        "Forensic compatibility transform only. It is never "
        "called by benchmark scoring and does not establish "
        "cross-benchmark comparability."
    ),
    implementation_id="compatibility_reanchor_score",
)

BENCHMARK_EVALUATIONS = (
    INITIAL_PRESEASON_CAMP_EVALUATION,
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    RICH_HISTORY_EVALUATION,
    PRELIMINARY_POST_EXPOSURE_EVALUATION,
    PHASE_CONSISTENT_POST_EXPOSURE_EVALUATION,
    CORRELATED_EXPOSURE_EVALUATION,
    THRESHOLD_RESPONSE_PROPOSED_EVALUATION,
    FIXED_MODE_DISCREPANCY_EVALUATION,
)

OTHER_EVALUATIONS = (
    POST_EXPOSURE_RESEARCH_EVALUATION,
    PREDICTIVE_PROGRESS_EVALUATION,
    PROGRESS_RATIO_EVALUATION,
    RELATIVE_PROGRESS_LOSS_EVALUATION,
    RELATIVE_PROGRESS_GAIN_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    STANDARDIZED_EUCLIDEAN_QUALIFICATION_EVALUATION,
    EMPIRICAL_ENERGY_QUALIFICATION_EVALUATION,
    POSTERIOR_ENERGY_RESEARCH_EVALUATION,
    POSTERIOR_ENERGY_DIFFERENCE_EVALUATION,
    POSTERIOR_ENERGY_REGRET_EVALUATION,
    VARIOGRAM_RESEARCH_EVALUATION,
    VARIOGRAM_REGRET_RESEARCH_EVALUATION,
    PARAMETER_RMSE_RESEARCH_EVALUATION,
    GAUSSIAN_KL_RESEARCH_EVALUATION,
    POSTERIOR_COVERAGE_QUALIFICATION_EVALUATION,
    POSTERIOR_PREDICTIVE_RESIDUAL_QUALIFICATION_EVALUATION,
    POSTERIOR_COVARIANCE_QUALIFICATION_EVALUATION,
    POSTERIOR_TRACE_RESEARCH_EVALUATION,
    POSTERIOR_TWO_SAMPLE_AUC_EVALUATION,
    PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY,
)

ALL_EVALUATION_DEFINITIONS = BENCHMARK_EVALUATIONS + OTHER_EVALUATIONS

__all__ = [
    "ALL_EVALUATION_DEFINITIONS",
    "BENCHMARK_EVALUATIONS",
    "CANONICAL_PRESEASON_CAMP_EVALUATION",
    "CORRELATED_EXPOSURE_EVALUATION",
    "EMPIRICAL_ENERGY_QUALIFICATION_EVALUATION",
    "FIXED_MODE_DISCREPANCY_EVALUATION",
    "GAUSSIAN_KL_RESEARCH_EVALUATION",
    "INITIAL_PRESEASON_CAMP_EVALUATION",
    "OTHER_EVALUATIONS",
    "PARAMETER_RMSE_RESEARCH_EVALUATION",
    "PHASE_CONSISTENT_POST_EXPOSURE_EVALUATION",
    "POSTERIOR_COVARIANCE_QUALIFICATION_EVALUATION",
    "POSTERIOR_COVERAGE_QUALIFICATION_EVALUATION",
    "POSTERIOR_PREDICTIVE_RESIDUAL_QUALIFICATION_EVALUATION",
    "POSTERIOR_ENERGY_RESEARCH_EVALUATION",
    "POSTERIOR_ENERGY_DIFFERENCE_EVALUATION",
    "POSTERIOR_ENERGY_REGRET_EVALUATION",
    "POSTERIOR_TRACE_RESEARCH_EVALUATION",
    "POSTERIOR_TWO_SAMPLE_AUC_EVALUATION",
    "POST_EXPOSURE_RESEARCH_EVALUATION",
    "PRELIMINARY_POST_EXPOSURE_EVALUATION",
    "PROGRESS_RATIO_EVALUATION",
    "PREDICTIVE_PROGRESS_EVALUATION",
    "PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY",
    "PUBLIC_REFERENCE_SELECTION_EVALUATION",
    "RELATIVE_PROGRESS_LOSS_EVALUATION",
    "RELATIVE_PROGRESS_GAIN_EVALUATION",
    "RICH_HISTORY_EVALUATION",
    "STANDARDIZED_EUCLIDEAN_QUALIFICATION_EVALUATION",
    "THRESHOLD_RESPONSE_PROPOSED_EVALUATION",
    "VARIOGRAM_RESEARCH_EVALUATION",
    "VARIOGRAM_REGRET_RESEARCH_EVALUATION",
]
