"""Regression checks for metric roles, benchmark bindings, and comparability."""

from cmj_recovery_dynamics.contracts import (
    ComparabilityStatus,
    MetricCategory,
    ProductionAcceptance,
)
from cmj_recovery_dynamics.metrics import (
    COMPARABILITY_REGISTRY,
    HISTORICAL_COMPARISONS,
    get_historical_comparison,
    reanchor_historical_score,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    INITIAL_PRESEASON_CAMP_EVALUATION,
    PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    RICH_HISTORY_EVALUATION,
)
from cmj_recovery_dynamics.registry import (
    BENCHMARK_REGISTRY,
    EVALUATION_REGISTRY,
    get_evaluation,
)


def test_comparability_repairs_preserve_evidence_bound_conclusions() -> None:
    expected = {
        "initial_vs_canonical_camp_public_results": ComparabilityStatus.NON_COMPARABLE,
        "rich_history_public_vs_hidden_bank_results": ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        "managed_vs_authored_gpu_results_after_reanchoring": ComparabilityStatus.NON_COMPARABLE,
        "correlated_exposure_vs_fixed_mode_research_results": ComparabilityStatus.NON_COMPARABLE,
        "fixed_mode_models_within_completed_study": ComparabilityStatus.DIRECTLY_COMPARABLE,
        "authored_gpu_lane_internal_results": ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        "public_baseline_vs_reference_selection": ComparabilityStatus.DIRECTLY_COMPARABLE,
        "posterior_identification_vs_point_forecast": ComparabilityStatus.NON_COMPARABLE,
    }
    assert len(HISTORICAL_COMPARISONS) == len(expected)
    for name, status in expected.items():
        assert get_historical_comparison(name).status is status
        assert COMPARABILITY_REGISTRY[name].rationale
    camp_comparison = get_historical_comparison("initial_vs_canonical_camp_public_results")
    assert camp_comparison.left_evaluation_name == INITIAL_PRESEASON_CAMP_EVALUATION.name
    assert camp_comparison.right_evaluation_name == CANONICAL_PRESEASON_CAMP_EVALUATION.name


def test_all_benchmarks_resolve_to_their_typed_evaluation_definition() -> None:
    assert len(EVALUATION_REGISTRY) == 29
    for benchmark in BENCHMARK_REGISTRY.values():
        evaluation = get_evaluation(benchmark.evaluation_identity.name)
        assert evaluation == benchmark.evaluation_identity
        assert benchmark.name in evaluation.compatible_benchmarks


def test_research_selection_and_compatibility_metrics_do_not_bind_as_benchmark_scores() -> None:
    bound = {benchmark.evaluation_identity.name for benchmark in BENCHMARK_REGISTRY.values()}
    assert POST_EXPOSURE_RESEARCH_EVALUATION.name not in bound
    assert PUBLIC_REFERENCE_SELECTION_EVALUATION.name not in bound
    assert PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.name not in bound
    assert POST_EXPOSURE_RESEARCH_EVALUATION.category is MetricCategory.RESEARCH_DIAGNOSTIC
    assert PUBLIC_REFERENCE_SELECTION_EVALUATION.category is MetricCategory.MODEL_SELECTION_METRIC
    assert (
        PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.category is MetricCategory.COMPATIBILITY_TRANSFORM
    )
    assert PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.compatible_benchmarks == ()


def test_rich_history_weights_are_uniform_across_cells_and_outcomes() -> None:
    assert len(RICH_HISTORY_EVALUATION.cell_weights) == 24
    assert {weight.weight for weight in RICH_HISTORY_EVALUATION.cell_weights} == {1.0}
    assert len(RICH_HISTORY_EVALUATION.target_weights) == 2
    assert {weight.weight for weight in RICH_HISTORY_EVALUATION.target_weights} == {1.0}


def test_proposed_threshold_score_is_not_an_accepted_production_scorer() -> None:
    evaluation = BENCHMARK_REGISTRY["threshold_response_recovery"].evaluation_identity
    assert evaluation.category is MetricCategory.BENCHMARK_SCORE
    assert evaluation.production_acceptance is ProductionAcceptance.PROPOSED_UNRESOLVED
    assert evaluation.is_proposed_scorer
    assert not evaluation.is_accepted_production_scorer


def test_auxiliary_evaluations_are_queryable_without_becoming_production_scores() -> None:
    initial = BENCHMARK_REGISTRY["initial_preseason_camp_recovery"]
    assert {item.category for item in initial.qualification_evaluations} == {
        MetricCategory.QUALIFICATION_STATISTIC
    }
    assert len(initial.model_selection_evaluations) == 1
    assert initial.model_selection_evaluations[0].category is MetricCategory.MODEL_SELECTION_METRIC

    for name in (
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "fixed_mode_discrepancy_recovery",
    ):
        benchmark = BENCHMARK_REGISTRY[name]
        assert benchmark.evaluation_identity.category is MetricCategory.UNIMPLEMENTED_EVALUATION
        assert benchmark.research_evaluations
        assert all(
            item.category is MetricCategory.RESEARCH_DIAGNOSTIC
            for item in benchmark.research_evaluations
        )


def test_historical_reanchor_is_callable_only_as_an_explicit_compatibility_step() -> None:
    assert reanchor_historical_score(0.0) == 0.0
    assert reanchor_historical_score(1.0) == 1.0
    assert all(
        benchmark.evaluation_identity.implementation_id != "reanchor_historical_score"
        for benchmark in BENCHMARK_REGISTRY.values()
    )
