"""Minimal clean-room provenance mappings and repaired historical comparisons."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from cmj_recovery_dynamics.contracts import ComparabilityStatus, HistoricalComparison
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    INITIAL_PRESEASON_CAMP_EVALUATION,
    PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    POSTERIOR_ENERGY_RESEARCH_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    RICH_HISTORY_EVALUATION,
)

# Historical labels live here only; equations and public APIs use scientific names.
HISTORICAL_ALIASES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "initial_camp_population_normalized_rmse_score": ("SP01", "E01"),
        "canonical_camp_population_normalized_rmse_score": ("SP02", "E01"),
        "rich_history_24_cell_normalized_rmse_score": ("SP03", "E02", "V3"),
        "threshold_response_12_cell_normalized_rmse_score": ("SP07", "C1"),
        "six_cell_mean_cellwise_normalized_rmse": ("SRE", "SRE6"),
        "piecewise_linear_historical_score_reanchoring": ("PWL", "historical score reanchor"),
        "four_cell_training_scale_normalized_rmse_selection_metric": (
            "Gate5",
            "Gate7",
            "E01 selection",
        ),
        "prior_whitened_posterior_energy_score": ("SYSID-P0", "ALI-522"),
    }
)


# These two scalar anchors define a source-specific score transform, not a benchmark.
HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE = 0.6441322434740403
HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE = 0.6822285834382722


HISTORICAL_COMPARISONS = (
    HistoricalComparison(
        comparison_name="initial_vs_canonical_camp_public_results",
        status=ComparabilityStatus.NON_COMPARABLE,
        left_result_family="initial camp public sample",
        right_result_family="canonical camp public sample",
        identity_basis="task, split, target cells, and dataset identity",
        rationale=(
            "The datasets differ, and the scorer contracts use "
            "different null floors (1.01 vs 1.00); "
            "the task-locked calibration values are also unavailable for numeric alignment."
        ),
        provenance_aliases=("SP01/D02", "SP02/D03"),
        left_evaluation_name=INITIAL_PRESEASON_CAMP_EVALUATION.name,
        right_evaluation_name=CANONICAL_PRESEASON_CAMP_EVALUATION.name,
    ),
    HistoricalComparison(
        comparison_name="rich_history_public_vs_hidden_bank_results",
        status=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        left_result_family="rich-history public validation",
        right_result_family="rich-history original hidden bank",
        identity_basis="same formulation, 24 cells, target definitions, and raw progress equation",
        rationale=(
            "The target bank and split differ; report them as "
            "bank-specific results and do not pool them."
        ),
        provenance_aliases=("SP03 public", "SP03 hidden"),
        left_evaluation_name=RICH_HISTORY_EVALUATION.name,
        right_evaluation_name=RICH_HISTORY_EVALUATION.name,
    ),
    HistoricalComparison(
        comparison_name="managed_vs_authored_gpu_results_after_reanchoring",
        status=ComparabilityStatus.NON_COMPARABLE,
        left_result_family="managed-GPU camp formulation",
        right_result_family="authored-GPU rich-history formulation",
        identity_basis="different benchmark formulations, worlds, datasets, and target banks",
        rationale=(
            "The compatibility transform changes score scale only; "
            "it does not align the underlying benchmark worlds or "
            "data."
        ),
        provenance_aliases=("V26 GPU", "V39 GPU"),
        left_evaluation_name=CANONICAL_PRESEASON_CAMP_EVALUATION.name,
        right_evaluation_name=RICH_HISTORY_EVALUATION.name,
        compatibility_transform_name=PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.name,
    ),
    HistoricalComparison(
        comparison_name="authored_gpu_lane_internal_results",
        status=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        left_result_family="authored-GPU lane earlier attempt",
        right_result_family="authored-GPU lane later attempt",
        identity_basis="same named lane and compatibility transform",
        rationale=(
            "Per-attempt target-bank and seed receipts are "
            "incomplete; use descriptive within-lane comparisons "
            "only."
        ),
        provenance_aliases=("V39 GPU lane",),
        left_evaluation_name=RICH_HISTORY_EVALUATION.name,
        right_evaluation_name=RICH_HISTORY_EVALUATION.name,
        compatibility_transform_name=PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.name,
    ),
    HistoricalComparison(
        comparison_name="correlated_exposure_vs_fixed_mode_research_results",
        status=ComparabilityStatus.NON_COMPARABLE,
        left_result_family="correlated-exposure research study",
        right_result_family="fixed-mode discrepancy research study",
        identity_basis=(
            "different response world and dataset despite the shared six-cell research equation"
        ),
        rationale=(
            "The world and data changed; the common diagnostic "
            "equation does not make the results a paired comparison."
        ),
        provenance_aliases=("SP06/D07", "SP08/D09", "ALI-507", "ALI-518"),
        left_evaluation_name=POST_EXPOSURE_RESEARCH_EVALUATION.name,
        right_evaluation_name=POST_EXPOSURE_RESEARCH_EVALUATION.name,
    ),
    HistoricalComparison(
        comparison_name="fixed_mode_models_within_completed_study",
        status=ComparabilityStatus.DIRECTLY_COMPARABLE,
        left_result_family="fixed-mode completed-study model set",
        right_result_family="fixed-mode completed-study model set",
        identity_basis=(
            "same D09 validation rows, six cells, research metric, and paired camp bootstrap"
        ),
        rationale=(
            "All models use the same 16 validation camps, 5,000 "
            "paired camp resamples, and shared resample matrix."
        ),
        provenance_aliases=("ALI-518 attempt 002",),
        left_evaluation_name=POST_EXPOSURE_RESEARCH_EVALUATION.name,
        right_evaluation_name=POST_EXPOSURE_RESEARCH_EVALUATION.name,
    ),
    HistoricalComparison(
        comparison_name="public_baseline_vs_reference_selection",
        status=ComparabilityStatus.DIRECTLY_COMPARABLE,
        left_result_family="public linear baseline",
        right_result_family="two-seed selected public reference",
        identity_basis=(
            "same D02 public validation, four cells, training-scale "
            "normalization, and arithmetic score definition"
        ),
        rationale=(
            "The comparison uses the model-selection metric, not the "
            "calibrated hidden benchmark score."
        ),
        provenance_aliases=("Gate5", "Gate7"),
        left_evaluation_name=PUBLIC_REFERENCE_SELECTION_EVALUATION.name,
        right_evaluation_name=PUBLIC_REFERENCE_SELECTION_EVALUATION.name,
    ),
    HistoricalComparison(
        comparison_name="posterior_identification_vs_point_forecast",
        status=ComparabilityStatus.NON_COMPARABLE,
        left_result_family="manufactured posterior identification study",
        right_result_family="recovery point-forecast benchmarks",
        identity_basis=(
            "posterior distribution over four sensitivities vs force/impulse point forecasts"
        ),
        rationale="The estimands, output dimensions, laws, and scoring rules differ.",
        provenance_aliases=("SYSID-P0", "T01/T02"),
        left_evaluation_name=POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        right_evaluation_name="UNKNOWN",
    ),
)

COMPARABILITY_REGISTRY: Mapping[str, HistoricalComparison] = MappingProxyType(
    {item.comparison_name: item for item in HISTORICAL_COMPARISONS}
)


def get_historical_comparison(name: str) -> HistoricalComparison:
    """Return a repaired RES-366 comparison conclusion by its clean name."""
    return COMPARABILITY_REGISTRY[name]


__all__ = [
    "COMPARABILITY_REGISTRY",
    "HISTORICAL_ALIASES",
    "HISTORICAL_COMPARISONS",
    "HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE",
    "HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE",
    "get_historical_comparison",
]
