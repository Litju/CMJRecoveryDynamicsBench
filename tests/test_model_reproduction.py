"""M3 model, evaluation, and historical-result authority boundaries."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from math import erf, sqrt

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import (
    CalibrationReferenceStatus,
    ComparabilityStatus,
    MetricCategory,
)
from cmj_recovery_dynamics.lineage.contracts import ExperimentStatus, ScientificDisposition
from cmj_recovery_dynamics.lineage.experiments import EXPERIMENTS
from cmj_recovery_dynamics.lineage.models import MODEL_FAMILIES
from cmj_recovery_dynamics.lineage.results import COMPARABILITY_CONCLUSIONS, RESULTS
from cmj_recovery_dynamics.metrics import RICH_HISTORY_CELLS, CellValues, rich_history_raw_progress
from cmj_recovery_dynamics.metrics.catalog import PUBLIC_REFERENCE_SELECTION_EVALUATION
from cmj_recovery_dynamics.model_reproduction import (
    BENCHMARK_NAMES,
    EVALUATION_REPRODUCTIONS,
    MODEL_REPRODUCTIONS,
    RESULT_REPRODUCTIONS,
    SPECIMEN_MODEL_LADDERS,
    CheckpointState,
    EvaluationRole,
    ModelConfigurationStatus,
    ModelInputError,
    ModelReproductionStatus,
    ReferenceM0Parameters,
    ResultReproductionStatus,
    SpecimenModelStatus,
    directly_comparable,
    fit_linear_public_baseline,
    get_evaluation_reproduction,
    get_model_reproduction,
    get_model_use_reproduction,
    get_result_reproduction,
    get_specimen_model_ladder,
    predict_linear_public_baseline,
    predict_reference_m0,
    require_production_scorer,
    zero_innovation_prediction,
)


def test_every_benchmark_linked_m1_model_has_an_explicit_m3_family_contract() -> None:
    expected = {
        family.name
        for family in MODEL_FAMILIES
        if set(family.applicability.benchmark_names).intersection(BENCHMARK_NAMES)
    }
    assert set(MODEL_REPRODUCTIONS) == expected
    assert all(
        contract.status in ModelReproductionStatus for contract in MODEL_REPRODUCTIONS.values()
    )
    assert get_model_reproduction("rich_history_zero_baseline").status is (
        ModelReproductionStatus.EXACT_IMPLEMENTATION
    )
    assert set(SPECIMEN_MODEL_LADDERS) == set(BENCHMARK_NAMES)
    assert EVALUATION_REPRODUCTIONS["six_cell_mean_cellwise_normalized_rmse"].role is (
        EvaluationRole.RESEARCH_DIAGNOSTIC
    )
    assert not any("posterior" in name or "waveform" in name for name in EVALUATION_REPRODUCTIONS)


def test_each_benchmark_result_keeps_its_m1_model_experiment_data_split_and_metric_binding() -> (
    None
):
    expected_results = {
        result.name
        for result in RESULTS
        if result.model_names and any(name in MODEL_REPRODUCTIONS for name in result.model_names)
    }
    assert set(RESULT_REPRODUCTIONS) == expected_results
    experiments = {experiment.name: experiment for experiment in EXPERIMENTS}
    for name, contract in RESULT_REPRODUCTIONS.items():
        result = contract.result
        experiment = experiments[result.experiment_name]
        assert result.model_names
        assert all(model in MODEL_REPRODUCTIONS for model in result.model_names)
        assert contract.benchmark_name == experiment.benchmark_name
        assert result.dataset_name == experiment.dataset_name
        assert result.split_name in experiment.split_names
        assert result.evaluation_name in experiment.evaluation_names
        assert contract.experiment_status is experiment.status
        assert contract.experiment == experiment
        assert name == result.name

    reference = get_result_reproduction("initial_public_reference_selection_result")
    assert reference.seed_identities is not None
    assert len(reference.seed_identities) == 2
    assert reference.fold_grouping is not None
    assert len(reference.runtime_details) == 1
    assert "RTX 5090" in reference.runtime_details[0]


def test_direct_comparability_fails_closed_at_specimen_dataset_split_and_metric_boundaries() -> (
    None
):
    assert not directly_comparable(
        get_result_reproduction("initial_linear_public_baseline_result"),
        get_result_reproduction("canonical_camp_public_campaign_result_family"),
    )
    assert not directly_comparable(
        get_result_reproduction("initial_linear_public_baseline_result"),
        get_result_reproduction("initial_camp_negative_result_family"),
    )
    assert not directly_comparable(
        get_result_reproduction("rich_history_headroom_public_result"),
        get_result_reproduction("rich_history_headroom_hidden_result"),
    )
    assert not directly_comparable(
        get_result_reproduction("correlated_exposure_local_frontier_ratio"),
        get_result_reproduction("fixed_mode_local_to_frontier_ratio"),
    )
    assert directly_comparable(
        get_result_reproduction("fixed_mode_local_predictor_sre6"),
        get_result_reproduction("fixed_mode_nonlinear_mixed_effects_sre6"),
    )

    required_m1 = {
        "initial_vs_canonical_camp_results": ComparabilityStatus.NON_COMPARABLE,
        "rich_history_public_vs_hidden_bank": ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        "correlated_exposure_vs_fixed_mode_research_results": ComparabilityStatus.NON_COMPARABLE,
        "fixed_mode_local_vs_empirical_frontier": ComparabilityStatus.DIRECTLY_COMPARABLE,
        "system_identification_vs_recovery_point_forecast": ComparabilityStatus.NON_COMPARABLE,
        "white_waveform_vs_recovery_benchmark": ComparabilityStatus.NON_COMPARABLE,
    }
    observed = {item.name: item.status for item in COMPARABILITY_CONCLUSIONS}
    for name, status in required_m1.items():
        assert observed[name] is status


def test_historical_scores_cannot_be_exact_replays_without_exact_m2_data_identity() -> None:
    assert all(
        result.status
        not in {
            ResultReproductionStatus.EXACT_REPLAYABLE,
            ResultReproductionStatus.SEMANTICALLY_REPLAYABLE,
        }
        for result in RESULT_REPRODUCTIONS.values()
    )
    for result in RESULT_REPRODUCTIONS.values():
        assert not result.replay_authority.historical_dataset_hash_exact
        assert not result.replay_authority.exact_replay_ready
        assert not result.numerically_replayed
    with pytest.raises(ValueError, match="exact replay requires complete authority"):
        replace(
            get_result_reproduction("initial_public_reference_selection_result"),
            status=ResultReproductionStatus.EXACT_REPLAYABLE,
            numerically_replayed=True,
        )
    assert (
        get_result_reproduction("initial_linear_public_baseline_result").status
        is ResultReproductionStatus.SOURCE_REPRODUCIBLE
    )
    assert (
        get_result_reproduction("initial_public_reference_selection_result").status
        is ResultReproductionStatus.SOURCE_REPRODUCIBLE
    )


def test_result_replay_calibration_comes_from_bound_evaluation_authority() -> None:
    canonical = get_result_reproduction("canonical_camp_public_campaign_result_family")
    canonical_evaluation = get_evaluation_reproduction(canonical.result.evaluation_name)
    assert canonical_evaluation.definition is not None
    assert (
        canonical_evaluation.definition.calibration_reference_status
        is CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
    )
    assert canonical_evaluation.definition.calibration_reference_value is None
    assert canonical.replay_authority.evaluation_implementation_exact
    assert not canonical.replay_authority.calibration_available
    assert not canonical.replay_authority.semantic_replay_ready
    assert not canonical.replay_authority.exact_replay_ready
    assert not canonical.numerically_replayed
    assert canonical.status not in {
        ResultReproductionStatus.EXACT_REPLAYABLE,
        ResultReproductionStatus.SEMANTICALLY_REPLAYABLE,
    }
    with pytest.raises(
        ValueError,
        match="semantic replay requires semantic evaluation authority and a numerical replay",
    ):
        replace(
            canonical,
            status=ResultReproductionStatus.SEMANTICALLY_REPLAYABLE,
            numerically_replayed=True,
        )
    unknown_calibration = replace(
        canonical_evaluation,
        definition=replace(
            canonical_evaluation.definition,
            calibration_reference_status=CalibrationReferenceStatus.UNKNOWN,
        ),
    )
    assert unknown_calibration.implementation_exact
    assert not unknown_calibration.calibration_available
    unimplemented = get_evaluation_reproduction("unresolved_initial_camp_platform_metric")
    assert not unimplemented.implementation_exact
    assert not unimplemented.calibration_available

    raw_progress = get_result_reproduction("rich_history_headroom_public_result")
    raw_evaluation = get_evaluation_reproduction(raw_progress.result.evaluation_name)
    assert raw_evaluation.name == "rich_history_raw_progress_diagnostic"
    assert raw_evaluation.implementation_exact
    assert raw_evaluation.calibration_available
    assert raw_progress.replay_authority.evaluation_implementation_exact
    assert raw_progress.replay_authority.target_semantics_exact
    assert raw_progress.replay_authority.calibration_available
    assert raw_progress.replay_authority.semantic_replay_ready
    assert not raw_progress.replay_authority.historical_dataset_hash_exact
    assert not raw_progress.numerically_replayed
    assert raw_progress.status is not ResultReproductionStatus.SEMANTICALLY_REPLAYABLE
    assert "Do not apply" in (raw_evaluation.formula or "")

    selection = get_result_reproduction("initial_public_reference_selection_result")
    selection_evaluation = get_evaluation_reproduction(selection.result.evaluation_name)
    assert selection_evaluation.role is EvaluationRole.MODEL_SELECTION_METRIC
    assert selection_evaluation.calibration_available
    assert selection.replay_authority.calibration_available
    assert not selection.numerically_replayed
    assert selection.status is ResultReproductionStatus.SOURCE_REPRODUCIBLE


def test_missing_hyperparameters_stay_unknown_and_private_weights_do_not_fill_config_gaps() -> None:
    ridge = get_model_use_reproduction(
        "post_exposure_ridge_baseline",
        "phase_consistent_post_exposure_recovery",
        "phase_consistent_adversarial_survivability",
    )
    assert ridge.configuration_status is ModelConfigurationStatus.UNKNOWN
    assert ridge.hyperparameters == ()
    assert ridge.checkpoint_state is CheckpointState.UNKNOWN

    threshold = get_model_use_reproduction(
        "threshold_response_reference_predictor",
        "threshold_response_recovery",
        "threshold_response_implementation_reference_attempt",
    )
    assert threshold.checkpoint_state is CheckpointState.PRESERVED_PRIVATELY
    assert threshold.configuration_status is ModelConfigurationStatus.UNKNOWN
    assert threshold.implementation_status is ModelReproductionStatus.UNRESOLVED
    assert not threshold.result_names

    reference = get_model_use_reproduction(
        "initial_public_reference_model",
        "initial_preseason_camp_recovery",
        "initial_public_reference_selection",
    )
    assert reference.configuration_status is ModelConfigurationStatus.EXACT
    assert reference.checkpoint_state is CheckpointState.PRESERVED_PRIVATELY
    assert reference.checkpoint_identity_sha256 == (
        "c8b72aa46a52fbc25a9f27330c3f62f54c67adbc5d64c5d5d0b91680a6a0842e"
    )
    assert reference.seed_metrics == (
        ("M0 repeat=0", 0.36102172987192604),
        ("M0 repeat=1", 0.3575973272130363),
    )
    with pytest.raises(FrozenInstanceError):
        reference.architecture = "inferred architecture"  # type: ignore[misc]


def test_recovered_linear_baseline_fits_and_predicts_the_source_defined_ols_surface() -> None:
    features = np.zeros((4, 39))
    features[:, 0] = (0.0, 1.0, 2.0, 3.0)
    targets = np.column_stack((2.0 + 4.0 * features[:, 0], -1.0 + 3.0 * features[:, 0]))
    model = fit_linear_public_baseline(features, targets)
    np.testing.assert_allclose(predict_linear_public_baseline(features, model), targets, atol=1e-12)
    assert model.feature_scale[0] == pytest.approx(sqrt(5.0 / 3.0))
    assert model.feature_scale[1:] == (1.0,) * 38

    with pytest.raises(ModelInputError, match="39 columns"):
        fit_linear_public_baseline(np.zeros((2, 3)), np.zeros((2, 2)))


def test_recovered_reference_m0_forward_matches_its_exact_gelu_architecture() -> None:
    input_weights = np.zeros((39, 32))
    input_weights[0, 0] = 1.0
    output_weights = np.zeros((32, 2))
    output_weights[0] = (2.0, -1.0)
    parameters = ReferenceM0Parameters(
        feature_mean=(0.0,) * 39,
        feature_scale=(1.0,) * 39,
        input_weights=tuple(map(tuple, input_weights)),
        input_bias=(0.0,) * 32,
        output_weights=tuple(map(tuple, output_weights)),
        output_bias=(0.0, 0.0),
    )
    features = np.zeros((2, 39))
    features[1, 0] = 1.0
    prediction = predict_reference_m0(features, parameters)
    gelu_one = 0.5 * (1.0 + erf(1.0 / sqrt(2.0)))
    np.testing.assert_allclose(prediction, ((0.0, 0.0), (2.0 * gelu_one, -gelu_one)))


def test_zero_innovation_baseline_is_exact_and_executable() -> None:
    zero = get_model_use_reproduction(
        "rich_history_zero_baseline",
        "rich_history_camp_recovery",
        "rich_history_headroom_reconstruction",
    )
    assert zero.implementation_status is ModelReproductionStatus.EXACT_IMPLEMENTATION
    assert zero.configuration_status is ModelConfigurationStatus.NOT_APPLICABLE
    assert zero_innovation_prediction(5, 2).shape == (5, 2)
    assert not bool(zero_innovation_prediction(5, 2).any())
    with pytest.raises(ModelInputError, match="positive integers"):
        zero_innovation_prediction(0)


def test_rich_history_raw_progress_reproduces_hand_calculation_without_calibration() -> None:
    cells = tuple(CellValues(cell, (0.0, 1.0), (0.0, 2.0)) for cell in RICH_HISTORY_CELLS)
    assert rich_history_raw_progress(cells) == pytest.approx(1.0 - 1.0 / sqrt(2.0))
    evaluation = get_evaluation_reproduction("rich_history_raw_progress_diagnostic")
    assert evaluation.role is EvaluationRole.RESEARCH_DIAGNOSTIC
    assert evaluation.implementation_id == "rich_history_raw_progress"
    assert "Do not apply" in (evaluation.formula or "")
    assert evaluation.definition is None


def test_selection_research_and_compatibility_metrics_cannot_be_production_scorers() -> None:
    selection = get_evaluation_reproduction(PUBLIC_REFERENCE_SELECTION_EVALUATION.name)
    research = get_evaluation_reproduction("six_cell_mean_cellwise_normalized_rmse")
    progress_ratio = get_evaluation_reproduction("predictive_progress_ratio")
    compatibility = get_evaluation_reproduction("piecewise_linear_historical_score_reanchoring")
    threshold = get_evaluation_reproduction("threshold_response_12_cell_normalized_rmse_score")

    assert selection.category is MetricCategory.MODEL_SELECTION_METRIC
    assert selection.role is EvaluationRole.MODEL_SELECTION_METRIC
    assert research.role is EvaluationRole.RESEARCH_DIAGNOSTIC
    assert progress_ratio.role is EvaluationRole.RESEARCH_DIAGNOSTIC
    assert compatibility.role is EvaluationRole.COMPATIBILITY_TRANSFORM
    assert threshold.role is EvaluationRole.PROPOSED_SCORER
    assert threshold.definition is not None
    assert threshold.definition.calibration_reference_value is None
    assert get_evaluation_reproduction("initial_camp_population_normalized_rmse_score").role is (
        EvaluationRole.ACCEPTED_PRODUCTION_SCORER
    )
    assert get_evaluation_reproduction("canonical_camp_population_normalized_rmse_score").role is (
        EvaluationRole.ACCEPTED_PRODUCTION_SCORER
    )
    for name in (
        PUBLIC_REFERENCE_SELECTION_EVALUATION.name,
        "six_cell_mean_cellwise_normalized_rmse",
        "predictive_progress_ratio",
        "piecewise_linear_historical_score_reanchoring",
        "threshold_response_12_cell_normalized_rmse_score",
    ):
        with pytest.raises(ValueError, match="not an accepted production scorer"):
            require_production_scorer(name)


def test_negative_operational_canceled_and_proposed_results_remain_distinct() -> None:
    initial_failure = get_result_reproduction("initial_camp_negative_result_family")
    assert initial_failure.experiment_status is ExperimentStatus.COMPLETED
    assert initial_failure.experiment_disposition is ScientificDisposition.COMPLETED_NEGATIVE
    assert initial_failure.status is ResultReproductionStatus.RESULT_EVIDENCE_ONLY

    incomplete = get_model_use_reproduction(
        "generic_multilayer_perceptron_predictor",
        "fixed_mode_discrepancy_recovery",
        "fixed_mode_partial_headroom_attempt",
    )
    completed = get_model_use_reproduction(
        "generic_multilayer_perceptron_predictor",
        "fixed_mode_discrepancy_recovery",
        "fixed_mode_completed_headroom_and_reconstruction_study",
    )
    canceled = get_model_use_reproduction(
        "generic_multilayer_perceptron_predictor",
        "fixed_mode_discrepancy_recovery",
        "fixed_mode_stopped_replay",
    )
    assert incomplete.experiment_status is ExperimentStatus.OPERATIONAL_FAILURE
    assert incomplete.scientific_disposition is ScientificDisposition.NOT_ESTABLISHED
    assert completed.experiment_status is ExperimentStatus.COMPLETED
    assert completed.scientific_disposition is ScientificDisposition.COMPLETED_MIXED
    assert canceled.experiment_status is ExperimentStatus.CANCELED
    assert canceled.scientific_disposition is ScientificDisposition.CANCELED


def test_preliminary_and_threshold_ladders_have_no_accepted_model_results() -> None:
    preliminary = get_specimen_model_ladder("preliminary_post_exposure_recovery")
    threshold = get_specimen_model_ladder("threshold_response_recovery")
    assert preliminary.status is SpecimenModelStatus.NOT_ESTABLISHED
    assert preliminary.model_names == preliminary.result_names == ()
    assert threshold.status is SpecimenModelStatus.PROPOSED
    assert threshold.result_names == ()
    assert "no accepted result exists" in threshold.note


def test_adjacent_sysid_and_white_results_stay_outside_benchmark_model_reproductions() -> None:
    assert all(
        "manufactured_parameter_identification" not in result.result.dataset_name
        and "waveform" not in result.result.dataset_name
        for result in RESULT_REPRODUCTIONS.values()
    )
    m1 = {item.name: item.status for item in COMPARABILITY_CONCLUSIONS}
    assert m1["system_identification_vs_recovery_point_forecast"] is (
        ComparabilityStatus.NON_COMPARABLE
    )
    assert m1["white_waveform_vs_recovery_benchmark"] is ComparabilityStatus.NON_COMPARABLE
