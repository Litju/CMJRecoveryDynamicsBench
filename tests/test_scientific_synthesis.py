"""Semantic checks for the evidence-bounded M6 synthesis registry."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cmj_recovery_dynamics.contracts import ComparabilityStatus
from cmj_recovery_dynamics.lineage.contracts import ScientificDisposition
from cmj_recovery_dynamics.lineage.registry import (
    LINEAGE_REGISTRY,
    get_result,
)
from cmj_recovery_dynamics.model_reproduction.contracts import ResultReproductionStatus
from cmj_recovery_dynamics.model_reproduction.registry import get_result_reproduction
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY
from cmj_recovery_dynamics.reproducibility.registry import (
    ReproducibilityProfile,
    get_reproducibility_profile,
)
from cmj_recovery_dynamics.reproduction.audit import FormulationReproducibility
from cmj_recovery_dynamics.reproduction.contracts import MaterializationState
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    HistoricalGateState,
    ProtocolCompleteness,
    ResultAuthority,
    StudyDecisionOutcome,
)
from cmj_recovery_dynamics.study_reconstruction.registry import (
    HISTORICAL_RULES,
    get_experiment_reconstruction,
)
from cmj_recovery_dynamics.synthesis import (
    BENCHMARK_CHARACTERIZATIONS,
    PROGRAM_SYNTHESIS,
    STUDY_CHARACTERIZATIONS,
    SYNTHESIS_CLAIMS,
    ComparativeEvidence,
    ConclusionStatus,
    ModelRoleEvidence,
    SynthesisAxis,
    SynthesisScope,
    build_comparative_evidence,
    get_benchmark_characterization,
    get_program_synthesis,
    get_study_characterization,
    get_synthesis_claim,
    get_synthesis_claims,
    validate_synthesis_claim,
)


def _scalar(result_name: str) -> float:
    values = [value.value for value in get_result(result_name).values if value.value is not None]
    assert len(values) == 1
    return values[0]


def test_inventory_is_exactly_eight_benchmarks_plus_two_studies() -> None:
    assert len(BENCHMARK_CHARACTERIZATIONS) == 8
    assert tuple(BENCHMARK_CHARACTERIZATIONS) == tuple(BENCHMARK_REGISTRY)
    assert set(STUDY_CHARACTERIZATIONS) == {"system_identification", "real_data_grounding"}
    assert not {
        "system_identification",
        "white_waveform",
        "predictive_headroom",
        "observability",
        "reconstructability",
        "falsification",
    }.intersection(BENCHMARK_CHARACTERIZATIONS)
    assert get_program_synthesis() is PROGRAM_SYNTHESIS
    assert PROGRAM_SYNTHESIS.benchmark_names == tuple(BENCHMARK_REGISTRY)
    assert PROGRAM_SYNTHESIS.study_names == ("system_identification", "real_data_grounding")
    assert len(SYNTHESIS_CLAIMS) == len(PROGRAM_SYNTHESIS.claims)

    for study in STUDY_CHARACTERIZATIONS.values():
        assert study.experiment_reconstructions
        assert all(
            item.experiment.benchmark_name is None for item in study.experiment_reconstructions
        )

    with pytest.raises(FrozenInstanceError):
        PROGRAM_SYNTHESIS.study_names = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        BENCHMARK_CHARACTERIZATIONS["new_benchmark"] = object()  # type: ignore[index]
    with pytest.raises(KeyError):
        get_study_characterization("white_waveform")


def test_claims_are_typed_unique_explicit_and_validated() -> None:
    names = tuple(claim.name for claim in PROGRAM_SYNTHESIS.claims)
    assert len(names) == len(set(names))
    assert all(isinstance(claim.status, ConclusionStatus) for claim in PROGRAM_SYNTHESIS.claims)
    assert all(claim.statement.strip() for claim in PROGRAM_SYNTHESIS.claims)
    for claim in PROGRAM_SYNTHESIS.claims:
        validate_synthesis_claim(claim)

    bad_reference = replace(
        get_synthesis_claim("initial_public_model_selection"),
        result_names=("not_a_registered_result",),
        comparative_evidence=(),
    )
    with pytest.raises(ValueError, match="unknown result"):
        validate_synthesis_claim(bad_reference)

    with pytest.raises(TypeError, match="immutable tuple"):
        ComparativeEvidence(
            result_names=["left", "right"],  # type: ignore[arg-type]
            status=ComparabilityStatus.DIRECTLY_COMPARABLE,
            shared_identity=("experiment", "dataset", "split", "evaluation"),
        )


def test_benchmark_model_roles_require_registered_benchmark_applicability() -> None:
    family = LINEAGE_REGISTRY.model_families["fixed_mode_nonlinear_mixed_effects_predictor"]
    claim = replace(
        get_synthesis_claim("initial_public_model_selection"),
        model_roles=(ModelRoleEvidence(family.name, family.roles),),
    )
    with pytest.raises(ValueError, match="model.*benchmark.*applicability"):
        validate_synthesis_claim(claim)


@pytest.mark.parametrize(
    ("claim_name", "model_name", "study_names"),
    (
        (
            "sysid_history_improves_manufactured_inference",
            "linear_public_baseline",
            ("system_identification",),
        ),
        (
            "white_waveform_rank_is_unstable",
            "identification_exact_analytic_posterior",
            ("real_data_grounding",),
        ),
        (
            "sysid_history_improves_manufactured_inference",
            "identification_exact_analytic_posterior",
            ("system_identification", "real_data_grounding"),
        ),
    ),
)
def test_study_model_roles_require_applicability_to_every_named_study(
    claim_name: str, model_name: str, study_names: tuple[str, ...]
) -> None:
    family = LINEAGE_REGISTRY.model_families[model_name]
    claim = replace(
        get_synthesis_claim(claim_name),
        study_names=study_names,
        model_roles=(ModelRoleEvidence(family.name, family.roles),),
    )
    with pytest.raises(ValueError, match="model.*study.*applicability"):
        validate_synthesis_claim(claim)


def test_experiment_model_roles_require_explicit_experiment_membership() -> None:
    family = LINEAGE_REGISTRY.model_families["initial_public_reference_model"]
    experiment = LINEAGE_REGISTRY.experiments["initial_linear_public_baseline_evaluation"]
    assert experiment.benchmark_name in family.applicability.benchmark_names
    assert family.name not in experiment.model_names
    claim = replace(
        get_synthesis_claim("initial_public_model_selection"),
        scope=SynthesisScope.EXPERIMENT,
        result_names=(),
        experiment_names=(experiment.name,),
        comparative_evidence=(),
        model_roles=(ModelRoleEvidence(family.name, family.roles),),
    )
    with pytest.raises(ValueError, match="model.*bound experiment"):
        validate_synthesis_claim(claim)

    validate_synthesis_claim(
        replace(
            claim,
            experiment_names=(experiment.name, "initial_public_reference_selection"),
        )
    )


def test_non_comparable_result_families_fail_closed() -> None:
    comparisons = (
        (
            ("initial_camp_negative_result_family", "canonical_camp_public_campaign_result_family"),
            "initial_vs_canonical_camp_results",
        ),
        (
            ("correlated_exposure_sre6_result_family", "fixed_mode_local_predictor_sre6"),
            "correlated_exposure_vs_fixed_mode_research_results",
        ),
        (
            ("manufactured_exact_posterior_energy_scores", "fixed_mode_local_predictor_sre6"),
            "system_identification_vs_recovery_point_forecast",
        ),
        (
            ("white_waveform_classical_validation_rmse", "fixed_mode_local_predictor_sre6"),
            "white_waveform_vs_recovery_benchmark",
        ),
    )
    for result_names, comparison_name in comparisons:
        with pytest.raises(ValueError):
            build_comparative_evidence(result_names, comparison_name=comparison_name)
        with pytest.raises(ValueError):
            build_comparative_evidence(result_names)

    with pytest.raises(ValueError, match="cannot support a quantitative comparison"):
        ComparativeEvidence(
            result_names=("left", "right"),
            status=ComparabilityStatus.NON_COMPARABLE,
            comparison_name="registered_non_comparable_pair",
        )


def test_initial_model_selection_is_direct_and_not_historical_replay() -> None:
    claim = get_synthesis_claim("initial_public_model_selection")
    linear = get_result("initial_linear_public_baseline_result")
    reference = get_result("initial_public_reference_selection_result")
    assert linear.values[0].value == 0.40366749638706456
    assert reference.values[0].value == 0.35930952854248116
    assert _scalar(reference.name) < _scalar(linear.name)
    assert claim.comparison_names == ("initial_public_baseline_vs_reference_selection",)
    assert claim.comparative_evidence[0].status is ComparabilityStatus.DIRECTLY_COMPARABLE
    assert "not an exact historical benchmark-score replay" in claim.statement

    negative = get_result("initial_camp_negative_result_family")
    replay = get_result_reproduction(negative.name)
    assert negative.disposition is ScientificDisposition.COMPLETED_NEGATIVE
    assert negative.values[0].value_range == (0.59, 0.60)
    assert replay.status is ResultReproductionStatus.RESULT_EVIDENCE_ONLY
    assert not replay.numerically_replayed
    assert (
        "M3 replay status" in get_synthesis_claim("initial_historical_attempts_negative").statement
    )

    qualification = get_result("initial_confirmatory_qualification_result")
    assert qualification.disposition is ScientificDisposition.COMPLETED_NEGATIVE
    assert (
        "not a benchmark-failure verdict"
        in get_synthesis_claim("initial_confirmatory_qualification_not_failure_verdict").statement
    )


def test_canonical_range_does_not_establish_seed_robustness() -> None:
    campaign = get_result("canonical_camp_public_campaign_result_family")
    assert campaign.values[0].value_range == (0.5176, 0.5266)
    assert campaign.values[0].sample_count == 5
    claim = get_synthesis_claim("canonical_campaign_range_identity_unresolved")
    assert "UNKNOWN" in claim.statement
    assert (
        get_synthesis_claim("canonical_run_robustness_not_established").status
        is ConclusionStatus.UNRESOLVED
    )
    assert claim.comparative_evidence == ()


def test_rich_history_public_lane_and_hidden_bank_remain_separate() -> None:
    names = (
        "rich_history_zero_baseline_result",
        "rich_history_empirical_bayes_public_result",
        "rich_history_boosted_residual_public_result",
        "rich_history_headroom_public_result",
    )
    records = tuple(get_result(name) for name in names)
    assert {item.experiment_name for item in records} == {"rich_history_headroom_reconstruction"}
    assert {item.dataset_name for item in records} == {"rich_history_camp_sample"}
    assert {item.split_name for item in records} == {"rich_history_public_validation"}
    assert {item.evaluation_name for item in records} == {"rich_history_raw_progress_diagnostic"}
    assert tuple(item.values[0].value for item in records) == (
        0.0,
        0.7165342249074321,
        0.7184639474288889,
        0.7216319938969343,
    )
    public = get_synthesis_claim("rich_history_public_headroom")
    assert public.comparative_evidence[0].status is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
    assert "captured most observed public headroom" in public.statement
    assert "small point gain" in public.statement
    for result in records[1:]:
        assert f"{_scalar(result.name):.16f}" in public.statement

    hidden_headroom = get_result("rich_history_headroom_hidden_result")
    hidden_reference = get_result("rich_history_reference_hidden_result")
    assert hidden_headroom.values[0].value == 0.6822285834382722
    assert hidden_reference.values[0].value == 0.6441322434740403
    separation = get_synthesis_claim("rich_history_public_hidden_bank_separation")
    assert separation.comparison_names == ("rich_history_public_vs_hidden_bank",)
    assert separation.comparative_evidence == ()
    hidden_split = next(
        item
        for item in get_benchmark_characterization(
            "rich_history_camp_recovery"
        ).reproducibility_profile.reproduction_contract.splits
        if item.role.value == "hidden_test"
    )
    assert hidden_split.materialization_state is MaterializationState.NOT_RECOVERED
    assert "not pooled" in separation.statement
    assert f"{_scalar(hidden_headroom.name):.16f}" in separation.statement
    assert f"{_scalar(hidden_reference.name):.16f}" in separation.statement


def test_phase_result_is_a_within_study_negative_result() -> None:
    ridge = get_result("phase_consistent_ridge_research_result")
    frontier = get_result("phase_consistent_restricted_frontier_research_result")
    assert ridge.values[0].value == 0.727472
    assert frontier.values[0].value == 0.786234
    assert _scalar(ridge.name) < _scalar(frontier.name)
    claim = get_synthesis_claim("phase_consistent_ridge_beats_restricted_frontier")
    assert claim.comparative_evidence[0].status is ComparabilityStatus.DIRECTLY_COMPARABLE
    assert "does not adjudicate correlated-exposure or fixed-mode" in " ".join(claim.limitations)


def test_correlated_reconstructability_and_historical_scalar_rule_are_preserved() -> None:
    ratio = get_result("correlated_exposure_local_frontier_ratio")
    interval = get_result("correlated_exposure_local_frontier_paired_sre_difference")
    loss = get_result("correlated_exposure_scalar_progress_loss")
    assert ratio.values[0].value == 0.9977002240012199
    assert interval.values[0].interval == (-0.0014055337702137793, 0.002354712208178295)
    assert loss.values[0].value == 0.031238600840498513
    reconstruction = get_synthesis_claim("correlated_exposure_local_reconstructability")
    assert "not evidence that a biological state was observable" in reconstruction.statement

    scalar_claim = get_synthesis_claim("correlated_scalar_loss_below_historical_rule")
    rule = next(
        item
        for item in get_experiment_reconstruction(
            "correlated_exposure_corrected_survivability"
        ).historical_decision_rules
        if item.name == "correlated_scalar_progress_minimum"
    )
    assert rule.threshold == 0.05
    assert not rule.scientific_requirement
    assert scalar_claim.historical_rule_names == (rule.name,)
    assert "not a universal scientific requirement" in scalar_claim.statement
    assert f"{loss.values[0].value:.18f}" in scalar_claim.statement

    terminal = get_experiment_reconstruction("correlated_exposure_corrected_survivability")
    assert terminal.decision is not None
    assert terminal.decision.outcome is StudyDecisionOutcome.RUNTIME_SCORER_REPAIR_REQUIRED
    assert (
        "not converted into benchmark PASS or FAIL"
        in get_synthesis_claim("correlated_terminal_runtime_repair_required").statement
    )


def test_threshold_response_remains_proposed_and_unadjudicated() -> None:
    protocol = LINEAGE_REGISTRY.experiments["threshold_response_proposed_protocol"]
    attempt = LINEAGE_REGISTRY.experiments["threshold_response_implementation_reference_attempt"]
    protocol_reconstruction = get_experiment_reconstruction(protocol.name)
    attempt_reconstruction = get_experiment_reconstruction(attempt.name)
    assert protocol.status.value == "PROPOSED_NOT_RUN"
    assert protocol.disposition is ScientificDisposition.PROPOSED_ALTERNATE
    assert protocol_reconstruction.result_authority is ResultAuthority.PROTOCOL_ONLY
    assert attempt.status.value == "COMPLETED"
    assert attempt.disposition is ScientificDisposition.NOT_ESTABLISHED
    assert attempt_reconstruction.result_authority is ResultAuthority.PROTOCOL_ONLY

    claim = get_synthesis_claim("threshold_response_proposed_unadjudicated")
    assert claim.status is ConclusionStatus.UNRESOLVED
    assert claim.axis is SynthesisAxis.NEGATIVE_RESULTS
    assert claim.result_names == ()
    assert all(
        item.scope is not SynthesisScope.BENCHMARK
        for item in get_synthesis_claims(
            SynthesisAxis.PREDICTIVE_PERFORMANCE,
            benchmark_name="threshold_response_recovery",
        )
    )
    assert "not a validated or rejected" in claim.statement
    assert "NOT_ESTABLISHED is not a negative" in " ".join(claim.limitations)


def test_fixed_mode_values_gates_and_pivot_are_not_benchmark_failure() -> None:
    expected = {
        "fixed_mode_local_predictor_sre6": 0.641366,
        "fixed_mode_nonlinear_mixed_effects_sre6": 0.641307,
        "fixed_mode_best_one_dimensional_sre6": 0.735083,
        "fixed_mode_generic_mlp_sre6": 0.762320,
        "fixed_mode_principal_component_diagnostic": 0.750521,
    }
    for name, value in expected.items():
        assert _scalar(name) == value
    comparison = get_synthesis_claim("fixed_mode_within_study_model_behavior")
    assert comparison.comparative_evidence[0].status is ComparabilityStatus.DIRECTLY_COMPARABLE
    for value in expected.values():
        assert f"{value:.6f}" in comparison.statement

    qualification = get_synthesis_claim("fixed_mode_public_data_qualification")
    assert "96 camps, 24000 participants, 72000 rows" in qualification.statement
    assert "16 camps, 4000 participants, 12000 rows" in qualification.statement

    study = get_experiment_reconstruction("fixed_mode_completed_headroom_and_reconstruction_study")
    assert study.result_authority is ResultAuthority.DIRECT_RESULT
    assert study.protocol_completeness is ProtocolCompleteness.PARTIAL
    assert len(study.historical_gate_outcomes) == 12
    passed = {
        item.gate_name
        for item in study.historical_gate_outcomes
        if item.state is HistoricalGateState.PASS
    }
    failed = {
        item.gate_name
        for item in study.historical_gate_outcomes
        if item.state is HistoricalGateState.FAIL
    }
    assert len(passed) == 8
    assert "PUBLIC_LEARNABILITY" in passed
    assert failed == {
        "POPULATION_LEARNING_LOAD_BEARING",
        "KNOWN_LAW_LOCAL_RECONSTRUCTABILITY",
        "STRUCTURED_BASELINE_HEADROOM",
        "MULTIDIMENSIONAL_LOAD_BEARING",
    }
    claim = get_synthesis_claim("fixed_mode_frontier_and_historical_gate_pivot")
    assert set(claim.gate_names) == passed | failed
    assert "PROGRAM_PIVOT" in claim.statement
    assert "ACTIVE_CANDIDATE" in claim.statement
    assert "not a benchmark-failure verdict" in claim.statement
    ratio = get_result("fixed_mode_local_to_frontier_ratio").values[0]
    assert f"{ratio.value:.6f}" in claim.statement
    assert str(ratio.interval) in claim.statement

    pivot = get_experiment_reconstruction("fixed_mode_owner_pivot_adjudication")
    assert pivot.result_authority is ResultAuthority.DIRECT_RESULT
    assert pivot.decision is not None
    assert pivot.decision.outcome is StudyDecisionOutcome.PROGRAM_PIVOT
    assert pivot.decision.benchmark_disposition is ScientificDisposition.ACTIVE_CANDIDATE
    fixed = get_benchmark_characterization("fixed_mode_discrepancy_recovery")
    assert (
        fixed.reproducibility_profile.reproduction_contract.evaluation.production_status.value
        == "unimplemented"
    )
    assert (
        get_synthesis_claim("fixed_mode_scorer_and_expert_qualification_unresolved").status
        is ConclusionStatus.UNRESOLVED
    )


def test_sysid_history_and_inference_stay_inside_adjacent_manufactured_study() -> None:
    study = get_study_characterization("system_identification")
    assert len(study.experiment_reconstructions) == 1
    assert (
        study.experiment_reconstructions[0].experiment.name
        == "manufactured_parameter_system_identification"
    )
    assert study.experiment_reconstructions[0].experiment.benchmark_name is None

    score_results = (
        "manufactured_prior_energy_scores",
        "manufactured_map_energy_scores",
        "manufactured_exact_posterior_energy_scores",
        "manufactured_empirical_bayes_energy_scores",
        "manufactured_neural_posterior_energy_scores",
    )
    expected = (
        (1.322, 1.323, 1.323),
        (1.269, 0.971, 0.713),
        (0.897, 0.687, 0.504),
        (0.902, 0.690, 0.506),
        (0.925, 0.728, 0.550),
    )
    for name, values in zip(score_results, expected, strict=True):
        assert tuple(item.value for item in get_result(name).values) == values

    rmse = get_result("manufactured_exact_posterior_raw_coordinate_rmse")
    assert tuple(item.value for item in rmse.values) == (0.372, 0.284, 0.207)
    assert {item.unit for item in rmse.values} == {"raw sensitivity-coordinate units"}
    history = get_synthesis_claim("sysid_history_improves_manufactured_inference")
    assert "energy" in history.statement
    assert "RMSE" in history.statement
    assert "concentration" not in history.statement.lower()
    assert history.result_names == (
        "manufactured_exact_posterior_energy_scores",
        "manufactured_exact_posterior_raw_coordinate_rmse",
    )
    differences = get_result("manufactured_neural_vs_exact_posterior_energy_difference")
    assert tuple((item.value, item.interval) for item in differences.values) == (
        (0.0279, (0.0244, 0.0319)),
        (0.0401, (0.0358, 0.0442)),
        (0.0462, (0.0422, 0.0502)),
    )
    claim = get_synthesis_claim("sysid_classical_inference_beats_neural_amortization")
    assert claim.comparative_evidence[0].status is ComparabilityStatus.DIRECTLY_COMPARABLE
    for values in expected:
        for value in values:
            assert f"{value:.3f}" in claim.statement
    terminal = get_experiment_reconstruction("manufactured_parameter_system_identification")
    assert terminal.decision is not None
    assert terminal.decision.outcome is StudyDecisionOutcome.NOT_ML_TASK
    assert (
        "does not establish that recovery forecasting is impossible"
        in get_synthesis_claim("sysid_terminal_not_ml_task_boundary").statement
    )


def test_white_waveform_is_not_recovery_validation_or_a_stable_model_ranking() -> None:
    classical = get_result("white_waveform_classical_validation_rmse")
    tcn = get_result("white_waveform_temporal_convolution_validation_rmse")
    assert classical.values[0].value == 0.4088
    assert tcn.values[0].value == 0.4117
    assert classical.values[0].sample_count == tcn.values[0].sample_count == 9
    claim = get_synthesis_claim("white_waveform_rank_is_unstable")
    assert claim.scope is SynthesisScope.STUDY
    assert claim.comparative_evidence[0].status is ComparabilityStatus.DIRECTLY_COMPARABLE
    assert "no stable classical-versus-TCN superiority" in claim.statement
    assert (
        get_result("white_recovery_crosswalk_unresolved_result").comparability
        is ComparabilityStatus.NON_COMPARABLE
    )
    with pytest.raises(ValueError):
        build_comparative_evidence(
            (classical.name, "fixed_mode_local_predictor_sre6"),
            comparison_name="white_waveform_vs_recovery_benchmark",
        )


def test_sample_and_compute_efficiency_are_unresolved_without_proxy_estimates() -> None:
    sample = get_synthesis_claim("program_sample_efficiency_unresolved")
    assert sample.status is ConclusionStatus.UNRESOLVED
    assert set(sample.benchmark_names) == set(BENCHMARK_REGISTRY)
    assert "not sample-efficiency estimates" in sample.statement
    assert not any(token in sample.statement for token in ("72000", "24000", "4000"))

    history = get_synthesis_claim("program_sample_efficiency_sysid_boundary")
    assert history.scope is SynthesisScope.STUDY
    assert history.study_names == ("system_identification",)
    assert history.benchmark_names == ()

    compute = get_synthesis_claim("program_compute_efficiency_unresolved")
    assert compute.status is ConclusionStatus.UNRESOLVED
    assert compute.comparative_evidence == ()
    assert "GPU/CPU labels" in compute.statement
    assert "future reproducibility tooling" in compute.statement


def test_structured_vs_learned_and_task_design_claims_are_caveated() -> None:
    structured = get_synthesis_claim("program_structured_and_analytic_methods_no_universal_winner")
    assert structured.status is ConclusionStatus.SUPPORTED_WITH_CAVEAT
    assert "does not support a universal structured-over-learned rule" in structured.statement
    assert len(structured.comparative_evidence) == 4
    assert all(
        item.status
        in {
            ComparabilityStatus.DIRECTLY_COMPARABLE,
            ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        }
        for item in structured.comparative_evidence
    )
    assert any(
        item.roles and any(role.value == "LOCAL_STRUCTURED_PREDICTOR" for role in item.roles)
        for item in structured.model_roles
    )
    assert any(
        item.roles and any(role.value == "GENERIC_HIGH_CAPACITY_PREDICTOR" for role in item.roles)
        for item in structured.model_roles
    )

    task_design = get_synthesis_claim("program_task_design_sensitivity")
    assert task_design.status is ConclusionStatus.SUPPORTED_WITH_CAVEAT
    assert task_design.comparative_evidence == ()
    assert "does not define a monotonic performance trajectory" in task_design.statement


def test_benchmark_quality_reuses_exact_m5_profiles_and_does_not_upgrade_status() -> None:
    expected = {
        "initial_preseason_camp_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
        "canonical_preseason_camp_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
        "rich_history_camp_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
        "preliminary_post_exposure_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
        "phase_consistent_post_exposure_recovery": (
            FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
        ),
        "correlated_exposure_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
        "threshold_response_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
        "fixed_mode_discrepancy_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
    }
    for name, status in expected.items():
        characterization = get_benchmark_characterization(name)
        profile = characterization.reproducibility_profile
        assert isinstance(profile, ReproducibilityProfile)
        assert profile == get_reproducibility_profile(name)
        assert profile.final_reproduction_audit.overall_status is status
        assert characterization.model_ladder.benchmark_name == name
        assert all(item.benchmark_name == name for item in characterization.result_reproductions)
    assert all(status is not FormulationReproducibility.EXACT for status in expected.values())

    rich_hidden = next(
        item
        for item in get_benchmark_characterization(
            "rich_history_camp_recovery"
        ).reproducibility_profile.reproduction_contract.splits
        if item.role.value == "hidden_test"
    )
    fixed_hidden = next(
        item
        for item in get_benchmark_characterization(
            "fixed_mode_discrepancy_recovery"
        ).reproducibility_profile.reproduction_contract.splits
        if item.role.value == "hidden_test"
    )
    threshold_hidden = next(
        item
        for item in get_benchmark_characterization(
            "threshold_response_recovery"
        ).reproducibility_profile.reproduction_contract.splits
        if item.role.value == "hidden_test"
    )
    assert rich_hidden.materialization_state is MaterializationState.NOT_RECOVERED
    assert fixed_hidden.materialization_state is MaterializationState.NOT_MATERIALIZED
    assert threshold_hidden.materialization_state is MaterializationState.UNKNOWN


def test_robustness_and_negative_result_statuses_keep_their_scope() -> None:
    robustness = get_synthesis_claim("program_robustness_is_study_specific")
    assert robustness.status is ConclusionStatus.SUPPORTED_WITH_CAVEAT
    assert set(robustness.gate_names) == {
        "SHORTCUT_LEAKAGE",
        "SHIFT_SUPPORT",
        "STATISTICAL_ADEQUACY",
        "RUNTIME_SEAL",
        "VALIDATION_SUBSTITUTION",
    }
    assert "no universal robustness score" in robustness.statement

    negative = get_synthesis_claim("program_negative_results_preserved")
    assert negative.status is ConclusionStatus.SUPPORTED_WITH_CAVEAT
    assert "NOT_ESTABLISHED attempt is unresolved evidence" in negative.statement
    assert "fixed's pivot is not benchmark failure" in negative.statement
    assert (
        get_synthesis_claim("threshold_response_proposed_unadjudicated").status
        is ConclusionStatus.UNRESOLVED
    )
    assert (
        get_synthesis_claim("fixed_mode_frontier_and_historical_gate_pivot").status
        is ConclusionStatus.SUPPORTED_WITH_CAVEAT
    )

    for claim in PROGRAM_SYNTHESIS.claims:
        for rule_name in claim.historical_rule_names:
            rule = next(item for item in HISTORICAL_RULES if item.name == rule_name)
            assert not rule.scientific_requirement
