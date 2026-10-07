"""Cross-registry lineage integrity and scientific-boundary tests."""

import ast
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Protocol

import pytest

from cmj_recovery_dynamics.contracts import ComparabilityStatus, StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    ArtifactAvailability,
    ArtifactReference,
    ChangeClass,
    ConfigurationStatus,
    ConflictStatus,
    CoordinateBasis,
    ExperimentStatus,
    RedistributionStatus,
    ScientificDisposition,
    classify_posterior_rmse_trace,
)
from cmj_recovery_dynamics.lineage.datasets import (
    BENCHMARK_LINEAGE,
    BENCHMARK_TRANSITIONS,
    DATASETS,
    SPLITS,
)
from cmj_recovery_dynamics.lineage.experiments import EXPERIMENTS
from cmj_recovery_dynamics.lineage.models import MODEL_FAMILIES
from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY, LineageRegistry
from cmj_recovery_dynamics.lineage.results import (
    COMPARABILITY_CONCLUSIONS,
    POSTERIOR_RMSE_CONFLICT,
    POSTERIOR_RMSE_TRACE,
    RESULTS,
)
from cmj_recovery_dynamics.registry import (
    BENCHMARK_REGISTRY,
    get_benchmark_lineage,
    get_experiment,
    get_experiment_lineage,
    get_model_family,
    get_model_lineage,
    get_result,
)

EXPECTED_BENCHMARKS = {
    "initial_preseason_camp_recovery",
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
}


class _Named(Protocol):
    @property
    def name(self) -> str: ...


def _replacement[T: _Named](items: tuple[T, ...], replacement: T) -> tuple[T, ...]:
    return tuple(replacement if item.name == replacement.name else item for item in items)


def test_all_eight_benchmarks_have_explicit_dataset_and_training_validation_splits() -> None:
    assert set(BENCHMARK_REGISTRY) == EXPECTED_BENCHMARKS
    assert {lineage.benchmark_name for lineage in BENCHMARK_LINEAGE} == EXPECTED_BENCHMARKS
    for name in EXPECTED_BENCHMARKS:
        view = get_benchmark_lineage(name)
        assert view.dataset.name == BENCHMARK_REGISTRY[name].dataset_identity.scientific_name
        assert view.lineage.generator_identity
        assert view.lineage.observation_identity
        assert view.lineage.representation_name
        assert view.evaluation.name == BENCHMARK_REGISTRY[name].evaluation_identity.name
        assert {split.role.value for split in view.splits} >= {"TRAINING", "PUBLIC_VALIDATION"}


def test_dataset_row_counts_do_not_conflate_rows_and_participants() -> None:
    splits = {split.name: split for split in SPLITS}
    assert splits["initial_camp_training"].rows == 4096
    assert splits["initial_camp_training"].participants == 1024
    assert splits["initial_camp_public_validation"].rows == 512
    assert splits["initial_camp_public_validation"].participants == 128
    assert splits["rich_history_training"].rows == 15182
    assert splits["rich_history_training"].participants == 4096
    active = next(item for item in DATASETS if item.name == "fixed_mode_recovery_candidate_sample")
    assert "older README" in active.evidence.note


def test_every_lineage_reference_resolves_and_scientific_names_are_unique() -> None:
    registry = LINEAGE_REGISTRY
    assert len(registry.benchmarks) == 8
    assert len(registry.datasets) == len(DATASETS)
    assert len(registry.model_families) == len(MODEL_FAMILIES)
    assert len(registry.experiments) == len(EXPERIMENTS)
    assert len(registry.results) == len(RESULTS)
    for result in registry.results.values():
        assert result.experiment_name in registry.experiments
        assert result.dataset_name in registry.datasets
        assert result.split_name in registry.splits
        assert (
            result.evaluation_name in registry.evaluations
            or result.evaluation_name in registry.custom_evaluations
        )
        assert set(result.model_names) <= set(registry.model_families)


def test_model_only_changes_do_not_create_benchmark_states() -> None:
    extra_model = replace(
        MODEL_FAMILIES[0],
        name="additional_linear_research_model",
        architecture="linear regression",
        introduction_change=ChangeClass.MODEL_ONLY_CHANGE,
    )
    registry = LineageRegistry(model_families=MODEL_FAMILIES + (extra_model,))
    assert set(registry.benchmarks) == EXPECTED_BENCHMARKS
    assert extra_model.name in registry.model_families
    assert all(
        transition.target_benchmark in EXPECTED_BENCHMARKS for transition in BENCHMARK_TRANSITIONS
    )


def test_benchmark_changing_transitions_preserve_world_and_measurement_redesigns() -> None:
    transitions = {transition.name: transition for transition in BENCHMARK_TRANSITIONS}
    assert (
        ChangeClass.DATASET_SPLIT_CHANGE
        in transitions["initial_to_canonical_camp_sample"].change_classes
    )
    assert (
        ChangeClass.WORLD_CHANGE
        in transitions["phase_consistent_to_correlated_exposure_world"].change_classes
    )
    assert (
        ChangeClass.OBSERVATION_CHANGE
        in transitions["scalar_to_phase_consistent_measurement"].change_classes
    )
    assert not transitions["correlated_to_threshold_alternate"].accepted_successor
    assert (
        ChangeClass.WORLD_CHANGE in transitions["correlated_to_fixed_mode_candidate"].change_classes
    )


def test_unknown_model_configuration_and_checkpoint_stay_unresolved() -> None:
    model = get_model_family("generic_multilayer_perceptron_predictor")
    assert model.configuration is None
    assert model.configuration_status.value == "UNKNOWN"
    assert model.checkpoint is None
    assert model.checkpoint_status is ArtifactAvailability.UNKNOWN


def test_preserved_model_artifact_can_exist_without_an_accepted_result() -> None:
    model = get_model_family("threshold_response_reference_predictor")
    assert model.checkpoint_status is ArtifactAvailability.PRESERVED_PRIVATELY
    assert model.checkpoint is not None
    assert model.configuration_status.value == "UNKNOWN"
    assert not any(model.name in result.model_names for result in RESULTS)


def test_known_model_configuration_details_do_not_invent_missing_hyperparameters() -> None:
    exact = get_model_family("identification_exact_analytic_posterior")
    neural = get_model_family("identification_amortized_neural_posterior")
    assert exact.configuration is not None
    assert exact.configuration.status is ConfigurationStatus.IDENTIFIED
    assert neural.configuration is not None
    assert neural.configuration.status is ConfigurationStatus.PARTIALLY_SPECIFIED
    assert any("unresolved" in detail for detail in neural.configuration.known_details)


def test_operational_failure_is_not_a_scientific_negative() -> None:
    partial = get_experiment("fixed_mode_partial_headroom_attempt")
    assert partial.status is ExperimentStatus.OPERATIONAL_FAILURE
    assert partial.disposition is ScientificDisposition.NOT_ESTABLISHED
    assert not any(result.experiment_name == partial.name for result in RESULTS)
    negative = get_experiment("initial_camp_failure_certificate")
    assert negative.status is ExperimentStatus.COMPLETED
    assert negative.disposition is ScientificDisposition.COMPLETED_NEGATIVE
    assert (
        get_result("initial_camp_negative_result_family").disposition
        is ScientificDisposition.COMPLETED_NEGATIVE
    )
    assert negative.benchmark_name == "initial_preseason_camp_recovery"


def test_central_benchmark_query_exposes_adjacent_studies_and_conflicts() -> None:
    view = get_benchmark_lineage("fixed_mode_discrepancy_recovery")
    assert view.dataset.name == "fixed_mode_recovery_candidate_sample"
    assert view.models
    assert view.experiments
    assert view.results
    assert StudyType.SYSTEM_IDENTIFICATION in {item.study_type for item in view.adjacent_studies}
    assert any(
        item.name == "manufactured_parameter_system_identification"
        for item in view.adjacent_experiments
    )
    assert any(
        item.name == "manufactured_exact_posterior_raw_coordinate_rmse"
        for item in view.adjacent_results
    )
    assert view.conflicts == (POSTERIOR_RMSE_CONFLICT,)


def test_model_and_experiment_queries_return_resolved_result_associations() -> None:
    model_view = get_model_lineage("identification_exact_analytic_posterior")
    assert any(
        item.name == "manufactured_exact_posterior_raw_coordinate_rmse"
        for item in model_view.results
    )
    experiment_view = get_experiment_lineage(
        "fixed_mode_completed_headroom_and_reconstruction_study"
    )
    assert experiment_view.dataset.name == "fixed_mode_recovery_candidate_sample"
    assert experiment_view.splits[0].name == "fixed_mode_public_validation"
    assert experiment_view.models
    assert experiment_view.evaluations
    assert any(item.name == "fixed_mode_local_predictor_sre6" for item in experiment_view.results)


def test_known_comparability_conclusions_are_preserved() -> None:
    comparisons = {item.name: item for item in COMPARABILITY_CONCLUSIONS}
    assert (
        comparisons["initial_vs_canonical_camp_results"].status
        is ComparabilityStatus.NON_COMPARABLE
    )
    assert (
        comparisons["rich_history_public_vs_hidden_bank"].status
        is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
    )
    assert (
        comparisons["correlated_exposure_vs_fixed_mode_research_results"].status
        is ComparabilityStatus.NON_COMPARABLE
    )
    assert (
        comparisons["fixed_mode_local_vs_empirical_frontier"].status
        is ComparabilityStatus.DIRECTLY_COMPARABLE
    )
    assert (
        comparisons["system_identification_vs_recovery_point_forecast"].status
        is ComparabilityStatus.NON_COMPARABLE
    )
    assert (
        comparisons["white_waveform_vs_recovery_benchmark"].status
        is ComparabilityStatus.NON_COMPARABLE
    )


def test_completed_fixed_mode_models_share_split_metric_and_bootstrap_protocol() -> None:
    left = get_result("fixed_mode_local_predictor_sre6")
    right = get_result("fixed_mode_nonlinear_mixed_effects_sre6")
    left_experiment = get_experiment(left.experiment_name)
    right_experiment = get_experiment(right.experiment_name)
    assert left.dataset_name == right.dataset_name
    assert left.split_name == right.split_name
    assert left.evaluation_name == right.evaluation_name
    assert left_experiment.bootstrap == right_experiment.bootstrap
    assert left_experiment.bootstrap is not None
    assert left_experiment.bootstrap.resamples == 5000
    assert left_experiment.bootstrap.seed == 49505000


def test_system_identification_is_adjacent_posterior_inference_not_point_forecasting() -> None:
    experiments = [
        item for item in EXPERIMENTS if item.study_type is StudyType.SYSTEM_IDENTIFICATION
    ]
    assert len(experiments) == 1
    experiment = experiments[0]
    assert experiment.benchmark_name is None
    assert LINEAGE_REGISTRY.datasets[experiment.dataset_name].kind.value == "MANUFACTURED"
    assert all(
        not LINEAGE_REGISTRY.model_families[name].applicability.benchmark_names
        for name in experiment.model_names
    )
    assert all(
        not result.production_result
        for result in LINEAGE_REGISTRY.results.values()
        if result.experiment_name == experiment.name
    )


def test_real_data_waveform_results_cannot_bind_as_recovery_benchmark_validation() -> None:
    experiment = get_experiment("white_waveform_feasibility_boundary")
    assert experiment.benchmark_name is None
    assert LINEAGE_REGISTRY.datasets[experiment.dataset_name].kind.value == "EMPIRICAL"
    for result_name in (
        "white_waveform_classical_validation_rmse",
        "white_waveform_temporal_convolution_validation_rmse",
    ):
        result = get_result(result_name)
        assert result.disposition is ScientificDisposition.NOT_BENCHMARK_VALIDATION
        assert result.comparability is ComparabilityStatus.DIRECTLY_COMPARABLE


def test_posterior_rmse_conflict_resolves_only_with_exact_result_source_and_config_evidence() -> (
    None
):
    assert POSTERIOR_RMSE_CONFLICT.status is ConflictStatus.RESOLVED_RAW_COORDINATE
    assert POSTERIOR_RMSE_TRACE.source_basis is CoordinateBasis.RAW_COORDINATE
    assert "sqrt(mean" in POSTERIOR_RMSE_TRACE.evaluator_reference
    assert "posterior.point_rmse" in POSTERIOR_RMSE_TRACE.source_output_reference
    assert POSTERIOR_RMSE_TRACE.configuration_identity

    incomplete = replace(POSTERIOR_RMSE_TRACE, same_result_binding=False)
    assert classify_posterior_rmse_trace(incomplete) is ConflictStatus.UNRESOLVED_CONFLICT
    with pytest.raises(ValueError, match="exact source evidence"):
        replace(
            POSTERIOR_RMSE_CONFLICT,
            status=ConflictStatus.UNRESOLVED_CONFLICT,
            trace=POSTERIOR_RMSE_TRACE,
        )
    distinct = replace(POSTERIOR_RMSE_TRACE, multiple_distinct_results=True)
    assert classify_posterior_rmse_trace(distinct) is ConflictStatus.MULTIPLE_DISTINCT_RESULTS


def test_duplicate_result_and_unknown_experiment_fail_loudly() -> None:
    with pytest.raises(ValueError, match="duplicate scientific result"):
        LineageRegistry(results=RESULTS + (RESULTS[0],))
    unknown = replace(RESULTS[0], experiment_name="missing_experiment")
    changed = _replacement(RESULTS, unknown)
    with pytest.raises(ValueError, match="unknown experiment"):
        LineageRegistry(results=changed)


def test_duplicate_model_identity_fails_loudly() -> None:
    with pytest.raises(ValueError, match="duplicate scientific model identity"):
        LineageRegistry(model_families=MODEL_FAMILIES + (MODEL_FAMILIES[0],))


def test_experiment_unknown_dataset_model_and_evaluation_fail_loudly() -> None:
    experiment = get_experiment("fixed_mode_completed_headroom_and_reconstruction_study")
    defects = (
        replace(experiment, dataset_name="unknown_dataset"),
        replace(experiment, model_names=("unknown_model",)),
        replace(experiment, evaluation_names=("unknown_evaluation",)),
    )
    expected_messages = ("unknown dataset", "unknown model", "unknown evaluation")
    for defect, expected in zip(defects, expected_messages, strict=True):
        changed = _replacement(EXPERIMENTS, defect)
        with pytest.raises(ValueError, match=expected):
            LineageRegistry(experiments=changed)


def test_experiment_with_incompatible_model_fails_loudly() -> None:
    experiment = get_experiment("fixed_mode_completed_headroom_and_reconstruction_study")
    incompatible = replace(experiment, model_names=("linear_public_baseline",))
    changed = _replacement(EXPERIMENTS, incompatible)
    with pytest.raises(ValueError, match="incompatible with benchmark"):
        LineageRegistry(experiments=changed)


def test_production_result_cannot_use_research_only_sre6() -> None:
    result = get_result("fixed_mode_local_predictor_sre6")
    changed_result = replace(result, production_result=True)
    changed = _replacement(RESULTS, changed_result)
    with pytest.raises(ValueError, match="research-only"):
        LineageRegistry(results=changed)


def test_direct_comparability_rejects_dataset_split_or_evaluation_mismatch() -> None:
    comparison = next(
        item
        for item in COMPARABILITY_CONCLUSIONS
        if item.name == "fixed_mode_local_vs_empirical_frontier"
    )
    invalid = replace(
        comparison,
        left_result_names=("initial_linear_public_baseline_result",),
        status=ComparabilityStatus.DIRECTLY_COMPARABLE,
    )
    changed = _replacement(COMPARABILITY_CONCLUSIONS, invalid)
    with pytest.raises(ValueError, match="identical dataset, split, and evaluation"):
        LineageRegistry(comparisons=changed)


def test_private_artifact_cannot_be_public_without_an_explicit_rights_decision() -> None:
    with pytest.raises(ValueError, match="explicit rights decision"):
        ArtifactReference(
            "private_checkpoint",
            "model checkpoint",
            ArtifactAvailability.PRESERVED_PRIVATELY,
            RedistributionStatus.ALLOWED,
        )


def test_lineage_source_has_no_private_absolute_paths_or_payloads() -> None:
    root = Path(__file__).resolve().parents[1]
    lineage_root = root / "src" / "cmj_recovery_dynamics" / "lineage"
    for path in lineage_root.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        assert "/home/" not in content
        assert "/Users/" not in content

    for path in (
        *lineage_root.rglob("*.py"),
        root / "src" / "cmj_recovery_dynamics" / "registry.py",
        root / "src" / "cmj_recovery_dynamics" / "__init__.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all("provenance" not in alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert "provenance" not in (node.module or "")

    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    names = tuple(item.decode("utf-8") for item in tracked.stdout.split(b"\0") if item)
    assert not any(
        name.endswith((".parquet", ".pt", ".pth", ".ckpt", ".npz", ".jsonl")) for name in names
    )
