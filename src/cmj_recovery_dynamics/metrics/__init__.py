"""Typed evaluation definitions and clean-room scientific metric implementations."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from cmj_recovery_dynamics.metrics.probabilistic import (
    binary_auc,
    empirical_energy_score,
    gaussian_kl_divergence,
    joint_ellipsoid_coverage,
    mahalanobis_squared,
    marginal_interval_coverage,
    mean_fold_auc,
    mean_prior_whitened_energy_score,
    mean_prior_whitened_variogram_score,
    mean_standardized_euclidean_error,
    normal_standardized_residual_diagnostics,
    paired_score_difference,
    parameter_root_mean_square_error,
    posterior_trace_ratio,
    prior_whitened_energy_score,
    prior_whitened_energy_score_regret,
    prior_whitened_variogram_score,
    prior_whitened_variogram_score_regret,
    sample_covariance,
    student_t_covariance_from_scale,
    student_t_scale_from_covariance,
    validate_two_target_covariance,
    variogram_score,
    whitened_vector,
)
from cmj_recovery_dynamics.metrics.scoring import (
    INITIAL_CAMP_CELLS,
    POST_EXPOSURE_RESEARCH_CELLS,
    RICH_HISTORY_CELLS,
    THRESHOLD_RESPONSE_CELLS,
    BenchmarkScoreResult,
    CellMetric,
    CellValues,
    MetricInputError,
    RichHistoryAssessment,
    TargetMetricValue,
    calibrated_benchmark_score,
    cellwise_normalized_rmse,
    mean_cellwise_normalized_rmse,
    mean_training_scale_normalized_rmse,
    piecewise_linear_calibration,
    point_benchmark_score,
    population_normalized_rmse,
    predictive_progress,
    progress_ratio,
    relative_progress_gain,
    relative_progress_loss,
    rich_history_benchmark_score,
    rich_history_stratum,
    rich_history_target_cell,
    rich_history_target_metrics,
    sample_standard_deviation,
    target_metrics_from_cells,
    threshold_load_index,
    threshold_load_regime,
    threshold_response_target_cell,
    training_axis_scales,
    two_seed_mean,
    weighted_cell_mean,
)

if TYPE_CHECKING:
    from cmj_recovery_dynamics.metrics.catalog import (
        ALL_EVALUATION_DEFINITIONS,
        BENCHMARK_EVALUATIONS,
        OTHER_EVALUATIONS,
    )
    from cmj_recovery_dynamics.metrics.compatibility import reanchor_historical_score
    from cmj_recovery_dynamics.metrics.provenance import (
        COMPARABILITY_REGISTRY,
        HISTORICAL_ALIASES,
        HISTORICAL_COMPARISONS,
        get_historical_comparison,
    )

_PROVENANCE_EXPORTS = frozenset(
    {
        "COMPARABILITY_REGISTRY",
        "HISTORICAL_ALIASES",
        "HISTORICAL_COMPARISONS",
        "get_historical_comparison",
    }
)
_CATALOG_EXPORTS = frozenset(
    {"ALL_EVALUATION_DEFINITIONS", "BENCHMARK_EVALUATIONS", "OTHER_EVALUATIONS"}
)


def __getattr__(name: str) -> Any:
    if name in _CATALOG_EXPORTS:
        return getattr(import_module("cmj_recovery_dynamics.metrics.catalog"), name)
    if name == "reanchor_historical_score":
        compatibility = import_module("cmj_recovery_dynamics.metrics.compatibility")
        return compatibility.reanchor_historical_score
    if name in _PROVENANCE_EXPORTS:
        return getattr(import_module("cmj_recovery_dynamics.metrics.provenance"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ALL_EVALUATION_DEFINITIONS",
    "BENCHMARK_EVALUATIONS",
    "BenchmarkScoreResult",
    "COMPARABILITY_REGISTRY",
    "CellMetric",
    "CellValues",
    "HISTORICAL_ALIASES",
    "HISTORICAL_COMPARISONS",
    "INITIAL_CAMP_CELLS",
    "MetricInputError",
    "OTHER_EVALUATIONS",
    "POST_EXPOSURE_RESEARCH_CELLS",
    "RICH_HISTORY_CELLS",
    "RichHistoryAssessment",
    "THRESHOLD_RESPONSE_CELLS",
    "TargetMetricValue",
    "binary_auc",
    "calibrated_benchmark_score",
    "cellwise_normalized_rmse",
    "empirical_energy_score",
    "gaussian_kl_divergence",
    "get_historical_comparison",
    "joint_ellipsoid_coverage",
    "mahalanobis_squared",
    "mean_cellwise_normalized_rmse",
    "mean_fold_auc",
    "mean_prior_whitened_energy_score",
    "mean_prior_whitened_variogram_score",
    "mean_standardized_euclidean_error",
    "normal_standardized_residual_diagnostics",
    "mean_training_scale_normalized_rmse",
    "marginal_interval_coverage",
    "parameter_root_mean_square_error",
    "paired_score_difference",
    "piecewise_linear_calibration",
    "point_benchmark_score",
    "population_normalized_rmse",
    "posterior_trace_ratio",
    "predictive_progress",
    "prior_whitened_energy_score",
    "prior_whitened_energy_score_regret",
    "prior_whitened_energy_score_regret",
    "prior_whitened_variogram_score",
    "prior_whitened_variogram_score_regret",
    "prior_whitened_variogram_score_regret",
    "progress_ratio",
    "reanchor_historical_score",
    "relative_progress_gain",
    "relative_progress_loss",
    "rich_history_stratum",
    "rich_history_target_cell",
    "rich_history_target_metrics",
    "rich_history_benchmark_score",
    "sample_standard_deviation",
    "sample_covariance",
    "student_t_covariance_from_scale",
    "student_t_scale_from_covariance",
    "target_metrics_from_cells",
    "threshold_load_index",
    "threshold_load_regime",
    "threshold_response_target_cell",
    "two_seed_mean",
    "training_axis_scales",
    "validate_two_target_covariance",
    "variogram_score",
    "weighted_cell_mean",
    "whitened_vector",
]
