"""M3 bindings to the clean, typed evaluation registry."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from cmj_recovery_dynamics.contracts import EvaluationDefinition, MetricCategory
from cmj_recovery_dynamics.lineage.evaluations import EVALUATION_BINDINGS
from cmj_recovery_dynamics.lineage.experiments import EXPERIMENTS
from cmj_recovery_dynamics.registry import EVALUATION_REGISTRY

from .contracts import EvaluationReproduction, EvaluationRole


def _role(definition: EvaluationDefinition) -> EvaluationRole:
    if definition.category is MetricCategory.BENCHMARK_SCORE:
        if definition.is_accepted_production_scorer:
            return EvaluationRole.ACCEPTED_PRODUCTION_SCORER
        if definition.is_proposed_scorer:
            return EvaluationRole.PROPOSED_SCORER
        return EvaluationRole.UNIMPLEMENTED
    if definition.category is MetricCategory.RESEARCH_DIAGNOSTIC:
        return EvaluationRole.RESEARCH_DIAGNOSTIC
    if definition.category is MetricCategory.QUALIFICATION_STATISTIC:
        return EvaluationRole.QUALIFICATION_STATISTIC
    if definition.category is MetricCategory.MODEL_SELECTION_METRIC:
        return EvaluationRole.MODEL_SELECTION_METRIC
    if definition.category is MetricCategory.COMPATIBILITY_TRANSFORM:
        return EvaluationRole.COMPATIBILITY_TRANSFORM
    return EvaluationRole.UNIMPLEMENTED


_BENCHMARKS = {
    "initial_preseason_camp_recovery",
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
}
_USED_EVALUATIONS = {
    name
    for experiment in EXPERIMENTS
    if experiment.benchmark_name in _BENCHMARKS
    for name in experiment.evaluation_names
}
_USED_EVALUATIONS.update(
    {
        "four_cell_training_scale_normalized_rmse_selection_metric",
        "initial_camp_population_normalized_rmse_score",
        "canonical_camp_population_normalized_rmse_score",
        "rich_history_24_cell_normalized_rmse_score",
        "rich_history_raw_progress_diagnostic",
        "threshold_response_12_cell_normalized_rmse_score",
        "six_cell_mean_cellwise_normalized_rmse",
        "predictive_progress_over_cell_mean_baseline",
        "predictive_progress_ratio",
        "relative_progress_loss_from_model_component",
        "relative_progress_gain_over_reference",
        "piecewise_linear_historical_score_reanchoring",
    }
)


def _contract(definition: EvaluationDefinition) -> EvaluationReproduction:
    return EvaluationReproduction(
        name=definition.name,
        role=_role(definition),
        category=definition.category,
        production_acceptance=definition.production_acceptance,
        definition=definition,
        formula=definition.formula,
        implementation_id=definition.implementation_id,
        compatible_benchmarks=definition.compatible_benchmarks,
        evidence=("RES-367: clean evaluation catalog and scorer implementation",),
        missing_authority=(
            ("historical M2 dataset byte identity is not EXACT",)
            if definition.name
            in {
                "initial_camp_population_normalized_rmse_score",
                "canonical_camp_population_normalized_rmse_score",
                "rich_history_24_cell_normalized_rmse_score",
                "threshold_response_12_cell_normalized_rmse_score",
            }
            else ()
        ),
    )


_contracts = {
    name: _contract(definition)
    for name, definition in EVALUATION_REGISTRY.items()
    if name in _USED_EVALUATIONS
}

# The raw headroom diagnostic uses the recovered 24-cell progress aggregation and stops before
# the unavailable final score calibration reference.
_contracts["rich_history_raw_progress_diagnostic"] = EvaluationReproduction(
    name="rich_history_raw_progress_diagnostic",
    role=EvaluationRole.RESEARCH_DIAGNOSTIC,
    category=MetricCategory.RESEARCH_DIAGNOSTIC,
    production_acceptance=None,
    definition=None,
    formula=(
        "For each outcome, average the 12 strata's normalized RMSE, map it to clipped "
        "progress max(0, min(1, 1 - error)), then equally average the two outcomes. "
        "Do not apply the final benchmark calibration curve."
    ),
    implementation_id="rich_history_raw_progress",
    compatible_benchmarks=("rich_history_camp_recovery",),
    evidence=(
        "RES-366: rich-history raw-progress result binding",
        "RES-367: 24-cell rich-history aggregation semantics",
    ),
    missing_authority=("historical dataset hash is not EXACT under M2",),
)

for _binding in EVALUATION_BINDINGS:
    if _binding.name not in _USED_EVALUATIONS:
        continue
    if _binding.name not in _contracts:
        _contracts[_binding.name] = EvaluationReproduction(
            name=_binding.name,
            role=(
                EvaluationRole.UNIMPLEMENTED
                if _binding.category is None
                or _binding.category is MetricCategory.UNIMPLEMENTED_EVALUATION
                else EvaluationRole.RESEARCH_DIAGNOSTIC
                if _binding.category is MetricCategory.RESEARCH_DIAGNOSTIC
                else EvaluationRole.QUALIFICATION_STATISTIC
            ),
            category=_binding.category,
            production_acceptance=None,
            definition=None,
            formula=None,
            implementation_id=None,
            compatible_benchmarks=_binding.compatible_benchmarks,
            evidence=("RES-366: M1 evaluation binding",),
            missing_authority=(_binding.description,),
        )

EVALUATION_REPRODUCTIONS: Mapping[str, EvaluationReproduction] = MappingProxyType(_contracts)


def get_evaluation_reproduction(name: str) -> EvaluationReproduction:
    return EVALUATION_REPRODUCTIONS[name]


def require_production_scorer(name: str) -> EvaluationDefinition:
    contract = get_evaluation_reproduction(name)
    if (
        contract.role is not EvaluationRole.ACCEPTED_PRODUCTION_SCORER
        or contract.definition is None
    ):
        raise ValueError(f"{name} is not an accepted production scorer")
    return contract.definition


__all__ = [
    "EVALUATION_REPRODUCTIONS",
    "get_evaluation_reproduction",
    "require_production_scorer",
]
