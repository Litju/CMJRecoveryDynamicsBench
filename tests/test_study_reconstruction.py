from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from cmj_recovery_dynamics import (
    EXPERIMENT_RECONSTRUCTIONS,
    STUDY_RECONSTRUCTIONS,
    get_experiment_reconstruction,
    get_study_reconstruction,
)
from cmj_recovery_dynamics.contracts import ComparabilityStatus, StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    DatasetKind,
    ExperimentStatus,
    ResultDefinition,
    ScientificDisposition,
)
from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY
from cmj_recovery_dynamics.metrics import progress_ratio
from cmj_recovery_dynamics.study_reconstruction import (
    HISTORICAL_RULES,
    HistoricalGateState,
    ProtocolCompleteness,
    ResultAuthority,
    RuleDirection,
    RuleRole,
    StudyClassification,
    StudyDecisionOutcome,
)

M4_EXPERIMENTS = {
    "rich_history_headroom_reconstruction",
    "rich_history_gpu_frontier_reconstruction",
    "rich_history_final_expert_frontier_protocol",
    "phase_consistent_adversarial_survivability",
    "correlated_exposure_corrected_survivability",
    "threshold_response_proposed_protocol",
    "threshold_response_implementation_reference_attempt",
    "fixed_mode_public_dataset_qualification",
    "fixed_mode_partial_headroom_attempt",
    "fixed_mode_stopped_replay",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "fixed_mode_production_scorer_status",
    "fixed_mode_expert_reference_qualification",
    "fixed_mode_owner_pivot_adjudication",
    "manufactured_parameter_system_identification",
    "white_waveform_feasibility_boundary",
    "white_recovery_grounding_crosswalk",
}


def _results(name: str) -> dict[str, ResultDefinition]:
    return {result.name: result for result in get_experiment_reconstruction(name).results}


def _value(
    result: ResultDefinition,
    measure: str | None = None,
    stratum: str | None = None,
) -> float:
    for item in result.values:
        if (measure is None or item.measure == measure) and item.stratum == stratum:
            assert item.value is not None
            return item.value
    raise AssertionError(f"no value for {result.name}: {measure}/{stratum}")


def test_m4_inventory_is_closed_over_the_eight_existing_benchmarks() -> None:
    assert set(EXPERIMENT_RECONSTRUCTIONS) == M4_EXPERIMENTS
    assert set(STUDY_RECONSTRUCTIONS) == {
        "predictive_headroom",
        "observability",
        "reconstructability",
        "falsification",
        "system_identification",
        "real_data_grounding",
    }
    assert set(EXPERIMENT_RECONSTRUCTIONS).issubset(LINEAGE_REGISTRY.experiments)
    assert len(LINEAGE_REGISTRY.benchmarks) == 8
    assert all(
        reconstruction.classification is not StudyClassification.BENCHMARK_CHANGE
        for reconstruction in EXPERIMENT_RECONSTRUCTIONS.values()
    )
    assert get_study_reconstruction("observability").experiment_names
    assert get_study_reconstruction("falsification").study_type is None
    assert all(
        name in EXPERIMENT_RECONSTRUCTIONS
        for study in STUDY_RECONSTRUCTIONS.values()
        for name in study.experiment_names
    )
    with pytest.raises(TypeError):
        cast(MutableMapping[str, object], EXPERIMENT_RECONSTRUCTIONS)[
            "not_a_lineage_experiment"
        ] = None
    reconstruction = get_experiment_reconstruction("rich_history_headroom_reconstruction")
    frozen_field = "classification"
    with pytest.raises(FrozenInstanceError):
        setattr(reconstruction, frozen_field, StudyClassification.BENCHMARK_CHANGE)

    for name in (
        "manufactured_parameter_system_identification",
        "white_waveform_feasibility_boundary",
        "white_recovery_grounding_crosswalk",
    ):
        reconstruction = get_experiment_reconstruction(name)
        assert reconstruction.benchmark_name is None
        assert reconstruction.dataset.benchmark_names == ()


def test_execution_and_scientific_dispositions_remain_separate() -> None:
    correlated = get_experiment_reconstruction("correlated_exposure_corrected_survivability")
    assert correlated.execution_status is ExperimentStatus.COMPLETED
    assert correlated.scientific_disposition is ScientificDisposition.COMPLETED_MIXED
    assert correlated.decision is not None
    assert correlated.decision.outcome is StudyDecisionOutcome.RUNTIME_SCORER_REPAIR_REQUIRED

    partial = get_experiment_reconstruction("fixed_mode_partial_headroom_attempt")
    assert partial.execution_status is ExperimentStatus.OPERATIONAL_FAILURE
    assert partial.scientific_disposition is ScientificDisposition.NOT_ESTABLISHED
    assert partial.result_authority is ResultAuthority.PARTIAL_OUTPUT_EXCLUDED
    assert partial.result_identities == ()
    assert partial.historical_gate_outcomes == ()

    stopped = get_experiment_reconstruction("fixed_mode_stopped_replay")
    assert stopped.execution_status is ExperimentStatus.CANCELED
    assert stopped.scientific_disposition is ScientificDisposition.CANCELED
    assert stopped.result_authority is ResultAuthority.PARTIAL_OUTPUT_EXCLUDED
    assert stopped.historical_gate_outcomes == ()

    qualification = get_experiment_reconstruction("fixed_mode_public_dataset_qualification")
    assert qualification.scientific_disposition is ScientificDisposition.COMPLETED_POSITIVE
    assert qualification.classification is StudyClassification.AUDIT
    assert qualification.decision is not None
    assert qualification.decision.outcome is StudyDecisionOutcome.SOURCE_DATA_QUALIFIED
    assert qualification.decision.benchmark_disposition is None

    pivot = get_experiment_reconstruction("fixed_mode_owner_pivot_adjudication")
    assert pivot.scientific_disposition is ScientificDisposition.PROGRAM_PIVOT
    assert pivot.decision is not None
    assert pivot.decision.outcome is StudyDecisionOutcome.PROGRAM_PIVOT
    assert pivot.decision.benchmark_disposition is ScientificDisposition.ACTIVE_CANDIDATE

    for name in (
        "rich_history_final_expert_frontier_protocol",
        "threshold_response_proposed_protocol",
        "fixed_mode_expert_reference_qualification",
    ):
        proposed = get_experiment_reconstruction(name)
        assert proposed.execution_status is ExperimentStatus.PROPOSED_NOT_RUN
        assert proposed.result_authority is ResultAuthority.PROTOCOL_ONLY
        assert proposed.results == ()
        assert proposed.decision is None
    assert (
        get_experiment_reconstruction("threshold_response_proposed_protocol").scientific_disposition
        is ScientificDisposition.PROPOSED_ALTERNATE
    )
    assert (
        get_experiment_reconstruction(
            "rich_history_final_expert_frontier_protocol"
        ).scientific_disposition
        is ScientificDisposition.NOT_ESTABLISHED
    )

    threshold_attempt = get_experiment_reconstruction(
        "threshold_response_implementation_reference_attempt"
    )
    assert threshold_attempt.execution_status is ExperimentStatus.COMPLETED
    assert threshold_attempt.scientific_disposition is ScientificDisposition.NOT_ESTABLISHED
    assert threshold_attempt.results == ()
    assert threshold_attempt.decision is None

    scorer = get_experiment_reconstruction("fixed_mode_production_scorer_status")
    assert scorer.execution_status is ExperimentStatus.BLOCKED
    assert scorer.scientific_disposition is ScientificDisposition.NOT_ESTABLISHED
    assert scorer.result_authority is ResultAuthority.PROTOCOL_ONLY

    unknown = get_experiment_reconstruction("white_recovery_grounding_crosswalk")
    assert unknown.execution_status is ExperimentStatus.UNKNOWN
    assert unknown.scientific_disposition is ScientificDisposition.UNKNOWN
    assert unknown.result_authority is ResultAuthority.UNKNOWN
    assert unknown.decision is None


def test_rich_history_keeps_public_hidden_and_compatibility_results_separate() -> None:
    public = _results("rich_history_headroom_reconstruction")
    assert _value(public["rich_history_zero_baseline_result"], "raw progress") == 0.0
    assert _value(public["rich_history_empirical_bayes_public_result"], "raw progress") == (
        0.7165342249074321
    )
    assert _value(public["rich_history_boosted_residual_public_result"], "raw progress") == (
        0.7184639474288889
    )
    assert _value(public["rich_history_headroom_public_result"], "raw progress") == (
        0.7216319938969343
    )
    assert _value(public["rich_history_headroom_hidden_result"], "raw progress") == (
        0.6822285834382722
    )
    assert _value(public["rich_history_reference_hidden_result"], "raw progress") == (
        0.6441322434740403
    )
    assert (
        public["rich_history_headroom_public_result"].split_name == "rich_history_public_validation"
    )
    assert (
        public["rich_history_headroom_hidden_result"].split_name
        == "rich_history_original_hidden_bank"
    )
    assert (
        public["rich_history_headroom_public_result"].comparability
        is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
    )
    assert (
        public["rich_history_headroom_hidden_result"].comparability
        is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
    )
    assert (
        "must not be pooled"
        in get_experiment_reconstruction("rich_history_headroom_reconstruction").conclusion
    )

    gpu = get_experiment_reconstruction("rich_history_gpu_frontier_reconstruction")
    assert gpu.result_authority is ResultAuthority.RECONSTRUCTED_ARITHMETIC
    assert gpu.results[0].evaluation_name == "piecewise_linear_historical_score_reanchoring"
    assert not gpu.results[0].production_result
    assert gpu.protocol_completeness is ProtocolCompleteness.PARTIAL

    expert = get_experiment_reconstruction("rich_history_final_expert_frontier_protocol")
    assert expert.execution_status is ExperimentStatus.PROPOSED_NOT_RUN
    assert expert.scientific_disposition is ScientificDisposition.NOT_ESTABLISHED


def test_phase_and_correlated_results_remain_specimen_bound() -> None:
    phase = get_experiment_reconstruction("phase_consistent_adversarial_survivability")
    assert phase.study_type is StudyType.RECONSTRUCTABILITY
    assert phase.scientific_disposition is ScientificDisposition.COMPLETED_NEGATIVE
    phase_results = _results("phase_consistent_adversarial_survivability")
    assert {result.dataset_name for result in phase_results.values()} == {
        "phase_consistent_episode_sample"
    }
    assert {result.split_name for result in phase_results.values()} == {
        "phase_consistent_episode_public_validation"
    }
    assert _value(phase_results["phase_consistent_ridge_research_result"]) == 0.727472
    assert _value(phase_results["phase_consistent_restricted_frontier_research_result"]) == (
        0.786234
    )
    assert all(not result.production_result for result in phase_results.values())
    assert "unknown" in phase.conclusion

    correlated = get_experiment_reconstruction("correlated_exposure_corrected_survivability")
    correlated_results = _results("correlated_exposure_corrected_survivability")
    assert {result.dataset_name for result in correlated_results.values()} == {
        "correlated_exposure_recovery_sample"
    }
    assert {result.split_name for result in correlated_results.values()} == {
        "correlated_exposure_public_validation"
    }
    assert _value(correlated_results["correlated_exposure_local_frontier_ratio"]) == (
        0.9977002240012199
    )
    assert correlated_results["correlated_exposure_local_frontier_paired_sre_difference"].values[
        0
    ].interval == (-0.0014055337702137793, 0.002354712208178295)
    assert _value(correlated_results["correlated_exposure_scalar_progress_loss"]) == (
        0.031238600840498513
    )

    corr_fixed = next(
        item
        for item in correlated.comparability
        if item.name == "correlated_exposure_vs_fixed_mode_research_results"
    )
    assert corr_fixed.status is ComparabilityStatus.NON_COMPARABLE
    assert [rule.role for rule in correlated.historical_decision_rules] == [
        RuleRole.HISTORICAL_PROGRAM_RULE,
        RuleRole.HISTORICAL_PROGRAM_RULE,
    ]
    assert all(not rule.scientific_requirement for rule in correlated.historical_decision_rules)

    ratio_rule, scalar_rule = correlated.historical_decision_rules
    assert ratio_rule.threshold == 0.90
    assert ratio_rule.applied and ratio_rule.caused_historical_decision
    assert not ratio_rule.is_satisfied_by(0.9977002240012199)
    assert scalar_rule.threshold == 0.05
    assert scalar_rule.applied and scalar_rule.caused_historical_decision
    assert not scalar_rule.is_satisfied_by(0.031238600840498513)
    purpose = scalar_rule.historical_purpose.lower()
    assert "multidimensional" in purpose and "exposure" in purpose
    assert "history over the best scalar" not in purpose
    assert "history" not in purpose
    assert "best scalar" in scalar_rule.quantity


def test_completed_fixed_mode_preserves_all_frozen_gate_outcomes_and_rules() -> None:
    completed = get_experiment_reconstruction(
        "fixed_mode_completed_headroom_and_reconstruction_study"
    )
    outcomes = {item.gate_name: item for item in completed.historical_gate_outcomes}
    assert len(outcomes) == 12
    assert all(
        item.experiment_name == "fixed_mode_completed_headroom_and_reconstruction_study"
        for item in outcomes.values()
    )
    assert set(outcomes) == {
        "PUBLIC_LEARNABILITY",
        "HISTORY_LOAD_BEARING",
        "POPULATION_LEARNING_LOAD_BEARING",
        "VALIDATION_SUBSTITUTION",
        "GENERIC_ML_HEADROOM",
        "KNOWN_LAW_LOCAL_RECONSTRUCTABILITY",
        "STRUCTURED_BASELINE_HEADROOM",
        "MULTIDIMENSIONAL_LOAD_BEARING",
        "SHORTCUT_LEAKAGE",
        "SHIFT_SUPPORT",
        "STATISTICAL_ADEQUACY",
        "RUNTIME_SEAL",
    }
    assert sum(item.state is HistoricalGateState.PASS for item in outcomes.values()) == 8
    assert sum(item.state is HistoricalGateState.FAIL for item in outcomes.values()) == 4
    failed_gates = {
        name for name, item in outcomes.items() if item.state is HistoricalGateState.FAIL
    }
    assert failed_gates == {
        "POPULATION_LEARNING_LOAD_BEARING",
        "KNOWN_LAW_LOCAL_RECONSTRUCTABILITY",
        "STRUCTURED_BASELINE_HEADROOM",
        "MULTIDIMENSIONAL_LOAD_BEARING",
    }
    assert outcomes["PUBLIC_LEARNABILITY"].state is HistoricalGateState.PASS

    expected_rules = {
        "fixed_mode_history_loss_minimum": (0.05, RuleDirection.GREATER_THAN_OR_EQUAL),
        "fixed_mode_population_learning_minimum": (0.05, RuleDirection.GREATER_THAN_OR_EQUAL),
        "fixed_mode_local_ratio_maximum": (0.90, RuleDirection.LESS_THAN_OR_EQUAL),
        "fixed_mode_generic_headroom_minimum": (0.02, RuleDirection.GREATER_THAN_OR_EQUAL),
        "fixed_mode_structured_baseline_headroom_minimum": (
            0.05,
            RuleDirection.GREATER_THAN_OR_EQUAL,
        ),
        "fixed_mode_multidimensional_advantage_minimum": (
            0.05,
            RuleDirection.GREATER_THAN_OR_EQUAL,
        ),
        "fixed_mode_validation_substitution_maximum": (0.10, RuleDirection.LESS_THAN),
    }
    rules = {rule.name: rule for rule in completed.historical_decision_rules}
    assert set(rules) == set(expected_rules)
    for name, (threshold, direction) in expected_rules.items():
        rule = rules[name]
        assert rule.threshold == threshold
        assert rule.direction is direction
        assert rule.role is RuleRole.HISTORICAL_PROGRAM_RULE
        assert not rule.scientific_requirement
        assert rule.source
    for gate_name, rule_name in (
        ("HISTORY_LOAD_BEARING", "fixed_mode_history_loss_minimum"),
        ("POPULATION_LEARNING_LOAD_BEARING", "fixed_mode_population_learning_minimum"),
        ("VALIDATION_SUBSTITUTION", "fixed_mode_validation_substitution_maximum"),
        ("GENERIC_ML_HEADROOM", "fixed_mode_generic_headroom_minimum"),
        ("KNOWN_LAW_LOCAL_RECONSTRUCTABILITY", "fixed_mode_local_ratio_maximum"),
        (
            "STRUCTURED_BASELINE_HEADROOM",
            "fixed_mode_structured_baseline_headroom_minimum",
        ),
        (
            "MULTIDIMENSIONAL_LOAD_BEARING",
            "fixed_mode_multidimensional_advantage_minimum",
        ),
    ):
        assert outcomes[gate_name].rule_names == (rule_name,)
    for name, contrast in (
        ("fixed_mode_history_loss_minimum", "paired uncertainty check"),
        ("fixed_mode_population_learning_minimum", "paired uncertainty check"),
        ("fixed_mode_local_ratio_maximum", "paired-CI check"),
        ("fixed_mode_generic_headroom_minimum", "BEST_GENERIC_MINUS_O1"),
        ("fixed_mode_structured_baseline_headroom_minimum", "wholly negative"),
        ("fixed_mode_multidimensional_advantage_minimum", "paired-CI direction check"),
    ):
        requirement = rules[name].paired_uncertainty_requirement
        assert requirement is not None and contrast in requirement

    observed_evidence = {
        "HISTORY_LOAD_BEARING": ("0.326100", "[0.071064, 0.084184]"),
        "POPULATION_LEARNING_LOAD_BEARING": (
            "-0.508897",
            "[-0.126576, -0.114962]",
        ),
        "GENERIC_ML_HEADROOM": (
            "0.109476",
            "BEST_GENERIC_MINUS_O1",
            "[0.102289, 0.116044]",
        ),
        "KNOWN_LAW_LOCAL_RECONSTRUCTABILITY": (
            "0.999835",
            "[0.998542, 1.001165]",
        ),
        "STRUCTURED_BASELINE_HEADROOM": (
            "-0.509146",
            "[-0.126593, -0.115126]",
            "[1.475162, 1.545666]",
        ),
        "MULTIDIMENSIONAL_LOAD_BEARING": (
            "-0.114598",
            "[-0.034592, -0.020563]",
            "[1.086457, 1.145019]",
        ),
        "VALIDATION_SUBSTITUTION": (
            "0.006677",
            "train-minus-pooled CI [0.001775, 0.002447]",
        ),
    }
    for gate_name, evidence in observed_evidence.items():
        for value in evidence:
            assert value in outcomes[gate_name].evidence_summary


def test_fixed_mode_qualification_attempts_completed_study_and_owner_boundary() -> None:
    completed = get_experiment_reconstruction(
        "fixed_mode_completed_headroom_and_reconstruction_study"
    )
    assert completed.protocol_completeness is ProtocolCompleteness.COMPLETE
    assert completed.dataset.name == "fixed_mode_recovery_candidate_sample"
    assert tuple(split.name for split in completed.splits) == ("fixed_mode_public_validation",)
    assert completed.source_closure.protocol_source[-1] == (
        "ALI-518-002: D09 public validation; 16 validation camps"
    )
    assert completed.protocol_unit.value == "CAMP"
    assert completed.repetitions == 3
    assert completed.bootstrap is not None
    assert completed.bootstrap.unit.value == "CAMP"
    assert completed.bootstrap.resamples == 5000
    assert completed.bootstrap.seed == 49505000
    assert completed.bootstrap.paired
    assert completed.bootstrap.shared_sample_matrix
    validation = completed.splits[0]
    assert validation.camps == 16

    results = _results("fixed_mode_completed_headroom_and_reconstruction_study")
    assert _value(results["fixed_mode_local_predictor_sre6"]) == 0.641366
    assert _value(results["fixed_mode_nonlinear_mixed_effects_sre6"]) == 0.641307
    ratio = results["fixed_mode_local_to_frontier_ratio"].values[0]
    assert ratio.value == 0.999835
    assert ratio.interval == (0.998542, 1.001165)
    assert _value(results["fixed_mode_best_one_dimensional_sre6"]) == 0.735083
    assert _value(results["fixed_mode_generic_mlp_sre6"]) == 0.762320
    assert _value(results["fixed_mode_principal_component_diagnostic"]) == 0.750521
    assert all(
        binding.authority is ResultAuthority.DIRECT_RESULT
        for binding in completed.result_authorities
    )
    assert progress_ratio(0.641366, 0.641307) == pytest.approx(0.999835)

    partial = get_experiment_reconstruction("fixed_mode_partial_headroom_attempt")
    stopped = get_experiment_reconstruction("fixed_mode_stopped_replay")
    assert not set(partial.result_identities).intersection(completed.result_identities)
    assert not set(stopped.result_identities).intersection(completed.result_identities)

    scorer = get_experiment_reconstruction("fixed_mode_production_scorer_status")
    assert "unimplemented" in scorer.conclusion
    expert = get_experiment_reconstruction("fixed_mode_expert_reference_qualification")
    assert expert.execution_status is ExperimentStatus.PROPOSED_NOT_RUN

    owner = get_experiment_reconstruction("fixed_mode_owner_pivot_adjudication")
    assert owner.scientific_disposition is ScientificDisposition.PROGRAM_PIVOT
    assert owner.decision is not None
    assert owner.decision.benchmark_disposition is ScientificDisposition.ACTIVE_CANDIDATE
    assert set(owner.decision.historical_rule_names) == {
        "fixed_mode_population_learning_minimum",
        "fixed_mode_local_ratio_maximum",
        "fixed_mode_structured_baseline_headroom_minimum",
        "fixed_mode_multidimensional_advantage_minimum",
    }
    failed_rules = {
        rule_name
        for gate in completed.historical_gate_outcomes
        if gate.state is HistoricalGateState.FAIL
        for rule_name in gate.rule_names
    }
    assert set(owner.decision.historical_rule_names) == failed_rules
    observation = owner.decision.scientific_observation.lower()
    assert "public learnability passed" in observation
    for phrase in (
        "population learning load-bearing",
        "known-law local reconstructability",
        "structured baseline headroom",
        "multidimensional load-bearing",
    ):
        assert phrase in observation
    assert "PIVOT_TO_SYSTEM_IDENTIFICATION" in owner.decision.downstream_program_action
    assert "FORWARD_SYNTHETIC_RECOVERY_REDESIGN=STOP" in (owner.decision.downstream_program_action)
    assert "not benchmark failure" in owner.conclusion
    assert not all(rule.scientific_requirement for rule in HISTORICAL_RULES)


def test_system_identification_is_manufactured_and_distinct_from_recovery_forecasting() -> None:
    reconstruction = get_experiment_reconstruction("manufactured_parameter_system_identification")
    assert reconstruction.benchmark_name is None
    assert reconstruction.dataset.kind is DatasetKind.MANUFACTURED
    assert reconstruction.study_type is StudyType.SYSTEM_IDENTIFICATION
    assert reconstruction.protocol_unit.value == "SYNTHETIC_HISTORY"
    assert reconstruction.seed_values == (522,)
    assert reconstruction.fold_count == 4
    assert reconstruction.repetitions == 1
    assert {split.name for split in reconstruction.splits} == {
        "identification_training_histories",
        "identification_heldout_history_regimes",
    }

    results = _results("manufactured_parameter_system_identification")
    expected = {
        "manufactured_prior_energy_scores": (1.322, 1.323, 1.323),
        "manufactured_map_energy_scores": (1.269, 0.971, 0.713),
        "manufactured_exact_posterior_energy_scores": (0.897, 0.687, 0.504),
        "manufactured_empirical_bayes_energy_scores": (0.902, 0.690, 0.506),
        "manufactured_neural_posterior_energy_scores": (0.925, 0.728, 0.550),
    }
    for result_name, expected_values in expected.items():
        assert (
            tuple(
                _value(results[result_name], stratum=f"history_count_{count}")
                for count in (2, 4, 8)
            )
            == expected_values
        )

    rmse = results["manufactured_exact_posterior_raw_coordinate_rmse"]
    assert tuple(_value(rmse, stratum=f"history_count_{count}") for count in (2, 4, 8)) == (
        0.372,
        0.284,
        0.207,
    )
    assert "raw-coordinate" in rmse.evidence.note
    assert "prior-whitened" in rmse.evidence.note
    assert {value.unit for value in rmse.values} == {"raw sensitivity-coordinate units"}

    differences = results["manufactured_neural_vs_exact_posterior_energy_difference"]
    assert tuple((value.value, value.interval) for value in differences.values) == (
        (0.0279, (0.0244, 0.0319)),
        (0.0401, (0.0358, 0.0442)),
        (0.0462, (0.0422, 0.0502)),
    )
    assert reconstruction.scientific_disposition is ScientificDisposition.NOT_ML_TASK
    assert reconstruction.decision is not None
    assert reconstruction.decision.outcome is StudyDecisionOutcome.NOT_ML_TASK
    comparison = next(
        item
        for item in reconstruction.comparability
        if item.name == "system_identification_vs_recovery_point_forecast"
    )
    assert comparison.status is ComparabilityStatus.NON_COMPARABLE


def test_white_waveform_is_adjacent_evidence_with_unknown_recovery_crosswalk() -> None:
    waveform = get_experiment_reconstruction("white_waveform_feasibility_boundary")
    assert waveform.benchmark_name is None
    assert waveform.dataset.kind is DatasetKind.EMPIRICAL
    assert waveform.scientific_disposition is ScientificDisposition.NOT_BENCHMARK_VALIDATION
    results = _results("white_waveform_feasibility_boundary")
    assert _value(results["white_waveform_classical_validation_rmse"]) == 0.4088
    assert _value(results["white_waveform_temporal_convolution_validation_rmse"]) == 0.4117
    assert all(result.values[0].sample_count == 9 for result in results.values())
    comparison = next(
        item
        for item in waveform.comparability
        if item.name == "white_waveform_vs_recovery_benchmark"
    )
    assert comparison.status is ComparabilityStatus.NON_COMPARABLE

    crosswalk = get_experiment_reconstruction("white_recovery_grounding_crosswalk")
    assert crosswalk.benchmark_name is None
    assert crosswalk.scientific_disposition is ScientificDisposition.UNKNOWN
    assert crosswalk.results[0].comparability is ComparabilityStatus.NON_COMPARABLE
    assert crosswalk.decision is None
    assert "rights decision" in crosswalk.downstream_action


def test_source_closures_are_public_safe_and_historical_rules_are_not_universal() -> None:
    completed = get_experiment_reconstruction(
        "fixed_mode_completed_headroom_and_reconstruction_study"
    )
    assert completed.source_closure.source_commit == ("62eb1d7714a04721429a7f4f385caad745e51c66",)
    assert completed.source_closure.task_tree == ("d9a12bed9c1ca4bc686bbbab1a06ba125f8b4e6d",)
    source_values = tuple(
        source
        for reconstruction in EXPERIMENT_RECONSTRUCTIONS.values()
        for field in (
            "source_commit",
            "task_tree",
            "protocol_source",
            "runner_source",
            "model_source",
            "evaluation_source",
            "result_source",
            "decision_source",
            "bootstrap_source",
            "environment_runtime_source",
        )
        for source in getattr(reconstruction.source_closure, field)
    )
    assert source_values
    assert all(not source.startswith("/") for source in source_values)
    assert all(rule.role is RuleRole.HISTORICAL_PROGRAM_RULE for rule in HISTORICAL_RULES)
    assert all(not rule.scientific_requirement for rule in HISTORICAL_RULES)
    assert all(rule.source for rule in HISTORICAL_RULES)
    with pytest.raises(ValueError):
        replace(HISTORICAL_RULES[0], threshold=float("nan"))
    with pytest.raises(ValueError):
        HISTORICAL_RULES[0].is_satisfied_by(float("nan"))
