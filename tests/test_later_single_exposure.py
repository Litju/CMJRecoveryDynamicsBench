from __future__ import annotations

import math

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import (
    BenchmarkStatus,
    CalibrationReferenceStatus,
    EvaluationImplementation,
    ForecastHorizon,
    MetricCategory,
    NormalizationRule,
    OutcomeVariable,
    ProductionAcceptance,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
    CORRELATED_EXPOSURE_PARAMETERS,
    LATENT_FACTOR_AXES,
    normalized_load_vector,
)
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    AMPLITUDE_FAST_SUPPORT,
    AMPLITUDE_SLOW_SUPPORT,
    CAMP_AMPLITUDE_LOGIT_SD,
    DISCREPANCY_FACTOR_MODE_PROBABILITIES,
    EPISODE_DISCREPANCY_NOMINAL_FRACTION,
    EPISODE_DISCREPANCY_SUPPORT,
    FAST_MODE_HOURS,
    PARTICIPANT_CONTEXT_MEAN_MATRIX,
    PARTICIPANT_MODULATION_SCALE,
    PARTICIPANT_SENSITIVITY_RESIDUAL_SD,
    RESPONSE_BASIS_INTERACTIONS,
    RESPONSE_BASIS_WEIGHTS,
    SHARED_DISCREPANCY_AMPLITUDE_FRACTION,
    SHARED_DISCREPANCY_FEATURE_COUNT,
    SHARED_DISCREPANCY_LENGTH_SCALE,
    SLOW_MODE_HOURS,
    FixedModeCampEffects,
    fixed_mode_component_score,
    fixed_mode_response,
    fixed_mode_response_fraction,
    response_axes,
    sample_fixed_mode_camp_effects,
    sample_fixed_mode_response_effects,
    shared_discrepancy_component,
    shared_discrepancy_fraction,
)
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    response_parameters_for_exposure as fixed_mode_parameters,
)
from cmj_recovery_dynamics.dynamics.threshold_response import (
    CAMP_AMPLITUDE_LOGIT_SD as THRESHOLD_CAMP_AMPLITUDE_LOGIT_SD,
)
from cmj_recovery_dynamics.dynamics.threshold_response import (
    FAST_BASE_WEIGHTS,
    FAST_INTERACTIONS,
    FAST_TIME_CONSTANT_SUPPORT_HOURS,
    HINGE_OFFSET,
    PRIOR_HIGH_LOAD_PROBABILITY,
    SLOW_BASE_WEIGHTS,
    SLOW_INTERACTIONS,
    SLOW_TIME_CONSTANT_SUPPORT_HOURS,
    SOFTPLUS_SCALE,
    SOFTPLUS_TEMPERATURE,
    THRESHOLD_RANGE,
    THRESHOLD_RESPONSE,
    ThresholdResponseParameters,
    participant_load,
    sample_threshold_camp_effects,
    sample_threshold_response_parameters,
    softplus_threshold_hinge,
    threshold_response_fraction,
    threshold_response_score,
)
from cmj_recovery_dynamics.dynamics.threshold_response import (
    response_parameters_for_exposure as threshold_parameters,
)
from cmj_recovery_dynamics.lineage.evaluations import EVALUATION_BINDINGS
from cmj_recovery_dynamics.metrics.catalog import (
    FIXED_MODE_DISCREPANCY_EVALUATION,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    THRESHOLD_RESPONSE_PROPOSED_EVALUATION,
)
from cmj_recovery_dynamics.metrics.scoring import (
    THRESHOLD_RESPONSE_CELLS,
    CellValues,
    cellwise_normalized_rmse,
    population_normalized_rmse,
    threshold_load_index,
    threshold_load_regime,
)
from cmj_recovery_dynamics.provenance.historical_aliases import HISTORICAL_ALIASES
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY
from cmj_recovery_dynamics.reproduction.contracts import (
    MaterializationState,
    ProductionScorerStatus,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionDimension as D,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionStatus as S,
)
from cmj_recovery_dynamics.reproduction.later_single_exposure import (
    LATER_SOURCE_CLOSURES,
    draw_episode_discrepancy,
    generate_later_episode,
    project_later_episode,
)
from cmj_recovery_dynamics.reproduction.registry import get_reproduction_contract
from cmj_recovery_dynamics.reproduction.single_exposure import (
    BASELINE_PRE_EXPOSURE_HOURS,
    CURRENT_EXPOSURE_TIME_HOURS,
    EXPOSURE_SUPPORTS,
    HORIZONS,
    NO_ADDITIONAL_EXPOSURE_THROUGH_H72,
    PREDICTOR_FIELDS,
    PRIOR_COMPLETE_EPISODES,
    ROW_KEY_FIELDS,
    SPLIT_GEOMETRY,
    TARGET_FIELDS,
    KeyedRandomStreams,
    PublicExposure,
)


def _exposure(unit: tuple[float, ...]) -> PublicExposure:
    values = {
        name: low + fraction * (high - low)
        for (name, (low, high)), fraction in zip(EXPOSURE_SUPPORTS, unit, strict=True)
    }
    duration = float(values["duration_min"])
    total_distance = float(values["total_distance_m"])
    high_speed = float(values["high_speed_distance_m"])
    sprint = min(float(values["sprint_distance_m"]), high_speed)
    accel = round(float(values["high_intensity_accel_count"]))
    decel = round(float(values["high_intensity_decel_count"]))
    rpe = float(values["session_rpe_cr10"])
    assert total_distance >= high_speed >= sprint
    return PublicExposure(
        duration,
        total_distance,
        high_speed,
        sprint,
        accel,
        decel,
        rpe,
        duration * rpe,
    )


def _public_primitives(exposure: PublicExposure) -> dict[str, float | int]:
    values = exposure.as_dict()
    return {name: values[name] for name, _bounds in EXPOSURE_SUPPORTS}


def test_exact_m1_source_closures_bind_all_executable_and_schema_inputs() -> None:
    assert set(LATER_SOURCE_CLOSURES) == {
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    }
    expected = {
        "threshold_response_recovery": (
            "2.1.0",
            "059f42ebc7396662dba04f0b0021d834e4e1aa79",
            "d6758ab6f75262121bc6b6df1eb995cb32567386",
        ),
        "fixed_mode_discrepancy_recovery": (
            "1.0.0",
            "984a9c740f7fab11d5ae10c5eee3c99f53f43537",
            "96dd5450512aca55d42c90c7c1a845ebbb2887bd",
        ),
    }
    required_files = (
        "params.py",
        "response.py",
        "exposure.py",
        "generator.py",
        "rng.py",
        "splits.py",
        "measurement.py",
        "projection.py",
        "generate_public.py",
    )
    for name, closure in LATER_SOURCE_CLOSURES.items():
        version, commit, tree = expected[name]
        assert closure.parameter_authority_version == version
        assert closure.parameter_authority_metadata_key == f"{name}.historical_labels"
        assert closure.public_root_metadata_key == f"{name}.historical_labels"
        assert closure.source_commit == commit
        assert closure.task_tree == tree
        assert closure.repository_task_path == "problems/preseason-exposure-cmj-recovery-forecast"
        assert all(
            any(
                path.endswith(filename)
                for path in (
                    closure.params_path,
                    closure.response_path,
                    closure.exposure_path,
                    closure.generator_path,
                    closure.rng_path,
                    closure.split_path,
                    closure.measurement_path,
                    closure.projection_path,
                    closure.public_generator_path,
                )
            )
            for filename in required_files
        )
        assert closure.schema_path == "data/canonical_v2.py"
        assert closure.manifest_path == "data/public/manifest.json"
        assert closure.scorer_path == "scorer/compute_score.py"
        assert closure.test_paths
        assert all(path.startswith("data_generation/tests/") for path in closure.test_paths)
        labels = HISTORICAL_ALIASES[name].historical_labels
        if name == "threshold_response_recovery":
            assert "LCMJ-V2-PARAMETERS-C1-2.1.0" in labels
            assert "LCMJ-C1-PUBLIC-003-e88b767181cf4e1c" in labels
        else:
            assert "LCMJ-CANDIDATE-H-PARAMETERS-ALI-517-1.0.0" in labels
            assert "ALI-517-CANDIDATE-H-PUBLIC-001" in labels
    assert (
        LATER_SOURCE_CLOSURES["threshold_response_recovery"].cell_definition_path
        == "scorer/cells.py"
    )
    assert LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].cell_definition_path is None
    assert (
        LATER_SOURCE_CLOSURES["threshold_response_recovery"].public_data_qualification_status
        is None
    )
    assert (
        LATER_SOURCE_CLOSURES["threshold_response_recovery"].scientific_adjudication_status is None
    )
    assert (
        LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].public_data_qualification_status
        == "PASS"
    )
    assert (
        LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].scientific_adjudication_status
        == "NOT_COMPLETED"
    )


def test_threshold_source_support_weights_and_participant_distribution() -> None:
    exposure = _exposure((0.2, 0.4, 0.6, 0.8, 0.5, 0.3, 0.7))
    streams = KeyedRandomStreams("threshold-parameters", 12)
    params = sample_threshold_response_parameters(streams)
    replay = sample_threshold_response_parameters(KeyedRandomStreams("threshold-parameters", 12))
    assert len(params.participant_load_weights_fast) == 7
    assert len(params.participant_load_weights_slow) == 7
    assert all(
        weight > 0.0
        for weight in (*params.participant_load_weights_fast, *params.participant_load_weights_slow)
    )
    assert math.fsum(params.participant_load_weights_fast) == pytest.approx(1.0)
    assert math.fsum(params.participant_load_weights_slow) == pytest.approx(1.0)
    assert params == replay
    assert THRESHOLD_RANGE == (0.35, 0.75)
    assert THRESHOLD_RESPONSE.implementation_status.value == "complete_equation"
    assert PRIOR_HIGH_LOAD_PROBABILITY == 0.30
    assert len(normalized_load_vector(exposure)) == 7
    assert FAST_BASE_WEIGHTS == (0.14, 0.14, 0.16, 0.16, 0.14, 0.12, 0.14)
    assert SLOW_BASE_WEIGHTS == (0.18, 0.18, 0.13, 0.10, 0.12, 0.12, 0.17)
    assert FAST_INTERACTIONS == ((2, 3, 0.60), (4, 5, 0.35), (0, 6, 0.20))
    assert SLOW_INTERACTIONS == ((0, 1, 0.45), (6, 4, 0.25), (2, 5, 0.20))
    assert len(exposure.as_dict()) == 8
    vector = normalized_load_vector(exposure)
    load = participant_load(vector, params)
    interaction_score = math.fsum(
        coefficient * (vector[left] * vector[right] - 0.25)
        for left, right, coefficient in FAST_INTERACTIONS
    )
    assert threshold_response_score(vector, params) == pytest.approx(
        load - 0.5 + interaction_score + softplus_threshold_hinge(load, params.threshold)
    )


def test_threshold_hinge_zero_below_at_and_above_threshold() -> None:
    threshold = 0.5

    def expected(load: float) -> float:
        return (
            SOFTPLUS_SCALE
            * SOFTPLUS_TEMPERATURE
            * math.log1p(math.exp((load - threshold) / SOFTPLUS_TEMPERATURE))
            + HINGE_OFFSET
        )

    values = tuple(softplus_threshold_hinge(load, threshold) for load in (0.0, 0.4, 0.5, 0.6, 1.0))
    assert values == pytest.approx(tuple(expected(load) for load in (0.0, 0.4, 0.5, 0.6, 1.0)))
    assert values[0] < values[1] < values[2] < values[3] < values[4]
    assert HINGE_OFFSET == -0.30


def test_threshold_participant_load_is_distinct_from_equal_public_load_regime() -> None:
    exposure = _exposure((0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    participant = ThresholdResponseParameters(
        (0.01, 0.94, 0.01, 0.01, 0.01, 0.01, 0.01),
        (0.10, 0.60, 0.06, 0.06, 0.06, 0.06, 0.06),
        threshold=0.5,
    )
    primitives = _public_primitives(exposure)
    equal_public_load = threshold_load_index(primitives)
    assert equal_public_load == pytest.approx(1.0 / 7.0)
    assert threshold_load_regime(primitives) == "low"
    assert participant_load((0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0), participant) == pytest.approx(0.94)
    midpoint = _exposure((0.5,) * 7)
    assert threshold_load_index(_public_primitives(midpoint)) == pytest.approx(0.5)
    assert threshold_load_regime(_public_primitives(midpoint)) == "high"


def test_threshold_response_mapping_supports_outcomes_horizons_and_rejects_bad_support() -> None:
    exposure = _exposure((0.65,) * 7)
    participant = sample_threshold_response_parameters(KeyedRandomStreams("threshold-response", 3))
    camp = sample_threshold_camp_effects(KeyedRandomStreams("threshold-camp", 3))
    assert THRESHOLD_CAMP_AMPLITUDE_LOGIT_SD == 0.12
    for metric in ("force", "impulse"):
        fast_amp, fast_tau, slow_amp, slow_tau = threshold_parameters(
            exposure, participant, camp, metric
        )
        assert (
            FAST_TIME_CONSTANT_SUPPORT_HOURS[0] <= fast_tau <= FAST_TIME_CONSTANT_SUPPORT_HOURS[1]
        )
        assert (
            SLOW_TIME_CONSTANT_SUPPORT_HOURS[0] <= slow_tau <= SLOW_TIME_CONSTANT_SUPPORT_HOURS[1]
        )
        assert 0.01 < fast_amp < 0.08
        assert 0.0 < slow_amp < 0.08
        at_zero = threshold_response_fraction(exposure, 0.0, participant, camp, metric)
        at_24 = threshold_response_fraction(exposure, 24.0, participant, camp, metric)
        at_72 = threshold_response_fraction(exposure, 72.0, participant, camp, metric)
        assert at_zero == pytest.approx(-fast_amp - slow_amp)
        assert at_zero < at_24 < at_72 < 0.0
    invalid = exposure.as_dict()
    invalid["duration_min"] = 121.0
    with pytest.raises(ValueError, match="outside its frozen supports"):
        from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
            normalized_load_vector,
        )

        normalized_load_vector(invalid)


def test_threshold_evaluation_has_exactly_twelve_equal_cells_and_unresolved_calibration() -> None:
    assert len(THRESHOLD_RESPONSE_CELLS) == 12
    assert {cell.outcome for cell in THRESHOLD_RESPONSE_CELLS} == set(OutcomeVariable)
    assert {cell.horizon for cell in THRESHOLD_RESPONSE_CELLS} == {
        ForecastHorizon.H24,
        ForecastHorizon.H48,
        ForecastHorizon.H72,
    }
    assert {cell.stratum for cell in THRESHOLD_RESPONSE_CELLS} == {"high", "low"}
    values = tuple(
        CellValues(cell, (index / 10.0, 2.0 + index / 10.0), (0.0, 2.0))
        for index, cell in enumerate(THRESHOLD_RESPONSE_CELLS)
    )
    metrics = cellwise_normalized_rmse(values, THRESHOLD_RESPONSE_CELLS)
    progress = math.fsum(min(1.0, max(0.0, 1.0 - item.normalized_error)) for item in metrics) / 12
    expected = math.fsum(min(1.0, max(0.0, 1.0 - index / 10.0)) for index in range(12)) / 12
    assert progress == pytest.approx(expected)
    assert population_normalized_rmse((1, 1), (0, 2)) == pytest.approx(1.0)
    assert population_normalized_rmse((3, 3), (2, 2)) == pytest.approx(1.0)
    evaluation = THRESHOLD_RESPONSE_PROPOSED_EVALUATION
    assert evaluation.implementation_status is EvaluationImplementation.IMPLEMENTED
    assert evaluation.production_acceptance is ProductionAcceptance.PROPOSED_UNRESOLVED
    assert evaluation.normalization_rule is NormalizationRule.POPULATION_STANDARD_DEVIATION
    assert (
        evaluation.calibration_reference_status
        is CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
    )
    assert evaluation.calibration_reference_value is None
    assert evaluation.is_proposed_scorer and not evaluation.is_accepted_production_scorer
    contract = get_reproduction_contract("threshold_response_recovery")
    assert contract.evaluation.production_status is ProductionScorerStatus.PROPOSED
    assert contract.claim(D.EVALUATION).status is S.PARTIAL


def test_threshold_hidden_design_has_no_materialization_or_hash() -> None:
    hidden = get_reproduction_contract("threshold_response_recovery").splits[-1]
    assert hidden.assignment_status is S.PARTIAL
    assert hidden.materialization_state is MaterializationState.UNKNOWN
    assert hidden.rows is None
    assert hidden.planned_rows == 15_750
    assert hidden.reference_hash is None
    assert LATER_SOURCE_CLOSURES["threshold_response_recovery"].hidden_design == (
        21,
        5250,
        15_750,
    )
    assert LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].hidden_design is None


def test_threshold_keyed_public_episode_replay_and_shared_projection() -> None:
    first = generate_later_episode(
        benchmark_name="threshold_response_recovery",
        split="validation",
        camp_index=2,
        participant_index=7,
        root_seed="threshold-public-smoke",
    )
    second = generate_later_episode(
        benchmark_name="threshold_response_recovery",
        split="validation",
        camp_index=2,
        participant_index=7,
        root_seed="threshold-public-smoke",
    )
    assert first == second
    assert len(first.prior_episodes) == 4
    assert CURRENT_EXPOSURE_TIME_HOURS == 0.0
    assert BASELINE_PRE_EXPOSURE_HOURS == 2.0
    assert NO_ADDITIONAL_EXPOSURE_THROUGH_H72 is True
    assert PRIOR_COMPLETE_EPISODES == 4
    assert len(PREDICTOR_FIELDS) == 82
    assert len(ROW_KEY_FIELDS) == 3
    assert len(TARGET_FIELDS) == 2
    rows = project_later_episode(first)
    assert len(rows) == 3
    assert all(len(row) == 87 for row in rows)
    assert all(len([key for key in row if key.startswith("prior_episode[")]) == 68 for row in rows)


def test_fixed_mode_response_uses_exact_mathematical_modes_and_full_rank_basis() -> None:
    assert FAST_MODE_HOURS == 24.0
    assert SLOW_MODE_HOURS == 84.0
    assert fixed_mode_response(0.0, 0.03, 0.02) == pytest.approx(-0.05)
    assert abs(fixed_mode_response(24.0, 0.03, 0.02)) > abs(fixed_mode_response(48.0, 0.03, 0.02))
    assert abs(fixed_mode_response(48.0, 0.03, 0.02)) > abs(fixed_mode_response(72.0, 0.03, 0.02))
    assert np.linalg.matrix_rank(np.asarray(RESPONSE_BASIS_WEIGHTS)) == 4
    assert RESPONSE_BASIS_INTERACTIONS == (
        (1, 2, 0.25),
        (0, 3, 0.25),
        (2, 3, 0.25),
        (0, 2, 0.25),
    )
    values = (0.2, 0.4, 0.6, 0.8, 0.3, 0.5, 0.7)
    assert response_axes(values) == pytest.approx((0.3, 0.7, 0.4, 0.7))


def test_fixed_mode_four_sensitivities_use_context_conditioned_source_distribution() -> None:
    context = (-0.3, 0.1, 0.2, -0.1)
    streams = KeyedRandomStreams("fixed-sensitivity", 4)
    first = sample_fixed_mode_response_effects(streams, context)
    replay = sample_fixed_mode_response_effects(KeyedRandomStreams("fixed-sensitivity", 4), context)
    shifted = sample_fixed_mode_response_effects(streams, (0.2, 0.1, 0.2, -0.1))
    assert first == replay
    assert len(first.sensitivity) == 4
    assert all(-1.0 < value < 1.0 for value in first.sensitivity)
    assert first != shifted
    assert PARTICIPANT_CONTEXT_MEAN_MATRIX == (
        (0.35, 0.20, 0.15, 0.05),
        (-0.10, 0.40, 0.05, 0.15),
        (0.05, 0.30, -0.10, 0.20),
        (0.25, -0.05, 0.10, 0.35),
    )
    assert PARTICIPANT_SENSITIVITY_RESIDUAL_SD == 0.45
    assert LATENT_FACTOR_AXES == ("volume", "speed", "change", "internal")
    assert CAMP_AMPLITUDE_LOGIT_SD == 0.12
    assert sample_fixed_mode_camp_effects(
        KeyedRandomStreams("fixed-camp", 4)
    ) == sample_fixed_mode_camp_effects(KeyedRandomStreams("fixed-camp", 4))


def test_fixed_mode_interaction_and_participant_modulation_are_applied() -> None:
    axes = (0.4, 0.6, 0.2, 0.8)
    participant = sample_fixed_mode_response_effects(
        KeyedRandomStreams("fixed-score"), (0.0, 0.0, 0.0, 0.0)
    )
    score = fixed_mode_component_score(axes, "force", "fast", participant)
    weights = RESPONSE_BASIS_WEIGHTS[0]
    interaction = RESPONSE_BASIS_INTERACTIONS[0]
    expected = math.fsum(
        weight * (value - 0.5) for weight, value in zip(weights, axes, strict=True)
    )
    expected += interaction[2] * (axes[interaction[0]] * axes[interaction[1]] - 0.25)
    expected += PARTICIPANT_MODULATION_SCALE * math.fsum(
        weight * sensitivity * value
        for weight, sensitivity, value in zip(weights, participant.sensitivity, axes, strict=True)
    )
    assert score == pytest.approx(expected)
    assert PARTICIPANT_MODULATION_SCALE == 3.20


def test_fixed_mode_amplitudes_and_correlated_exposure_reuse() -> None:
    exposure = _exposure((0.6,) * 7)
    participant = sample_fixed_mode_response_effects(
        KeyedRandomStreams("fixed-params"), (0.0, 0.0, 0.0, 0.0)
    )
    camp = FixedModeCampEffects(((0.0, 0.0), (0.0, 0.0)))
    for metric in ("force", "impulse"):
        fast_amp, fast_tau, slow_amp, slow_tau = fixed_mode_parameters(
            exposure, participant, camp, metric
        )
        assert AMPLITUDE_FAST_SUPPORT[0] < fast_amp < AMPLITUDE_FAST_SUPPORT[1]
        assert AMPLITUDE_SLOW_SUPPORT[0] < slow_amp < AMPLITUDE_SLOW_SUPPORT[1]
        assert fast_tau == FAST_MODE_HOURS and slow_tau == SLOW_MODE_HOURS
    record = generate_later_episode(
        benchmark_name="fixed_mode_discrepancy_recovery",
        split="train",
        camp_index=0,
        participant_index=0,
        root_seed="fixed-public-smoke",
    )
    assert record.current.exposure.archetype_index is not None
    assert len(record.prior_episodes) == PRIOR_COMPLETE_EPISODES == 4
    assert len(project_later_episode(record)) == len(HORIZONS) == 3
    assert len(CORRELATED_EXPOSURE_PARAMETERS.train_probabilities) == 4


def test_fixed_mode_shared_discrepancy_is_replayed_bounded_and_horizon_decayed() -> None:
    exposure = _exposure((0.55,) * 7)
    context = (0.25, 0.50, 0.75, 0.40)
    assert SHARED_DISCREPANCY_FEATURE_COUNT == 32
    assert SHARED_DISCREPANCY_LENGTH_SCALE == 0.65
    for metric in ("force", "impulse"):
        for component in ("fast", "slow"):
            value = shared_discrepancy_component(exposure, context, metric, component)
            assert value == shared_discrepancy_component(exposure, context, metric, component)
            assert abs(value) <= SHARED_DISCREPANCY_AMPLITUDE_FRACTION
        for lag in (24.0, 48.0, 72.0):
            bound = SHARED_DISCREPANCY_AMPLITUDE_FRACTION * (
                math.exp(-lag / FAST_MODE_HOURS) + math.exp(-lag / SLOW_MODE_HOURS)
            )
            assert abs(shared_discrepancy_fraction(exposure, context, lag, metric)) <= bound + 1e-15
    participant = sample_fixed_mode_response_effects(
        KeyedRandomStreams("fixed-frac"), (0.0, 0.0, 0.0, 0.0)
    )
    camp = sample_fixed_mode_camp_effects(KeyedRandomStreams("fixed-frac-camp"))
    with_discrepancy = fixed_mode_response_fraction(
        exposure, 24.0, participant, camp, "force", context
    )
    nominal = fixed_mode_response_fraction(exposure, 24.0, participant, camp, "force")
    assert abs(with_discrepancy - nominal) <= 2 * SHARED_DISCREPANCY_AMPLITUDE_FRACTION


def test_episode_residual_and_shared_feature_amplitudes_are_distinct_authorities() -> None:
    assert PARTICIPANT_MODULATION_SCALE == 3.20
    assert SHARED_DISCREPANCY_AMPLITUDE_FRACTION == 0.006
    assert EPISODE_DISCREPANCY_SUPPORT == (0.0030, 0.0080)
    assert EPISODE_DISCREPANCY_NOMINAL_FRACTION == 0.0055
    assert (
        EPISODE_DISCREPANCY_SUPPORT[0]
        <= EPISODE_DISCREPANCY_NOMINAL_FRACTION
        <= EPISODE_DISCREPANCY_SUPPORT[1]
    )
    assert SHARED_DISCREPANCY_AMPLITUDE_FRACTION != EPISODE_DISCREPANCY_NOMINAL_FRACTION
    assert DISCREPANCY_FACTOR_MODE_PROBABILITIES == (0.50, 0.20, 0.20, 0.10)
    streams = KeyedRandomStreams("episode-discrepancy", 5)
    first = draw_episode_discrepancy(
        streams,
        "current",
        channel="current_discrepancy",
        support=EPISODE_DISCREPANCY_SUPPORT,
        factor_probabilities=DISCREPANCY_FACTOR_MODE_PROBABILITIES,
    )
    replay = draw_episode_discrepancy(
        KeyedRandomStreams("episode-discrepancy", 5),
        "current",
        channel="current_discrepancy",
        support=EPISODE_DISCREPANCY_SUPPORT,
        factor_probabilities=DISCREPANCY_FACTOR_MODE_PROBABILITIES,
    )
    assert first == replay
    assert all(
        EPISODE_DISCREPANCY_SUPPORT[0] <= abs(value) <= EPISODE_DISCREPANCY_SUPPORT[1]
        for cell in first.values()
        for value in cell.values()
    )


def test_public_geometry_and_train_validation_group_keys() -> None:
    train = SPLIT_GEOMETRY["train"]
    validation = SPLIT_GEOMETRY["validation"]
    assert (train.camps, train.participants, train.rows) == (96, 24_000, 72_000)
    assert (validation.camps, validation.participants, validation.rows) == (16, 4_000, 12_000)
    assert train.participants == train.camps * 250
    assert validation.participants == validation.camps * 250
    assert train.rows == train.participants * 3
    assert validation.rows == validation.participants * 3
    for benchmark_name in (
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    ):
        public_splits = get_reproduction_contract(benchmark_name).splits[:2]
        assert tuple(split.rows for split in public_splits) == (72_000, 12_000)
    generated = [
        generate_later_episode(
            benchmark_name="fixed_mode_discrepancy_recovery",
            split=split,
            camp_index=0,
            participant_index=0,
            root_seed="fixed-disjoint-smoke",
        )
        for split in ("train", "validation")
    ]
    assert generated[0].camp_identity != generated[1].camp_identity
    assert generated[0].participant_key != generated[1].participant_key
    assert generated[0].episode_key != generated[1].episode_key
    assert set(dict(generated[0].query_keys).values()).isdisjoint(
        dict(generated[1].query_keys).values()
    )
    with pytest.raises(ValueError, match="only public train and validation"):
        generate_later_episode(
            benchmark_name="fixed_mode_discrepancy_recovery",
            split="test",
            camp_index=0,
            participant_index=0,
            root_seed="no-hidden-generation",
        )


def test_fixed_hidden_challenge_is_not_materialized() -> None:
    hidden = get_reproduction_contract("fixed_mode_discrepancy_recovery").splits[-1]
    assert hidden.materialization_state is MaterializationState.NOT_MATERIALIZED
    assert hidden.assignment_status is S.NOT_APPLICABLE
    assert hidden.rows is None
    assert hidden.reference_hash is None


def test_formulation_statuses_and_evaluation_fail_closed() -> None:
    threshold = BENCHMARK_REGISTRY["threshold_response_recovery"]
    fixed = BENCHMARK_REGISTRY["fixed_mode_discrepancy_recovery"]
    assert threshold.status is BenchmarkStatus.PROPOSED
    assert fixed.status is BenchmarkStatus.ACTIVE_CANDIDATE
    assert threshold.status.value != "accepted"
    assert fixed.status.value != "accepted"
    assert (
        FIXED_MODE_DISCREPANCY_EVALUATION.implementation_status
        is EvaluationImplementation.NOT_IMPLEMENTED
    )
    assert FIXED_MODE_DISCREPANCY_EVALUATION.production_acceptance is ProductionAcceptance.NONE
    assert POST_EXPOSURE_RESEARCH_EVALUATION.category is MetricCategory.RESEARCH_DIAGNOSTIC
    assert POST_EXPOSURE_RESEARCH_EVALUATION is not FIXED_MODE_DISCREPANCY_EVALUATION
    qualification = next(
        item
        for item in EVALUATION_BINDINGS
        if item.name == "public_synthetic_dataset_qualification"
    )
    assert qualification.category is MetricCategory.QUALIFICATION_STATISTIC
    assert qualification.production_scorer is False


def test_later_exactness_and_hash_claims_remain_fail_closed() -> None:
    threshold = get_reproduction_contract("threshold_response_recovery")
    fixed = get_reproduction_contract("fixed_mode_discrepancy_recovery")
    assert threshold.claim(D.WORLD_LAW).status is S.EXACT
    assert threshold.claim(D.COMPLETE_GENERATOR).status is S.SEMANTICALLY_EQUIVALENT
    assert threshold.claim(D.RNG_ALGORITHM).status is S.PARTIAL
    assert threshold.claim(D.RNG_STATE).status is S.PARTIAL
    assert threshold.claim(D.SEED_AUTHORITY).status is S.EXACT
    assert threshold.claim(D.RNG_STREAM_CONSTRUCTION).status is S.EXACT
    assert threshold.claim(D.RNG_DRAW_ORDER).status is S.EXACT
    assert threshold.claim(D.RNG_SUBSTREAM_STRATEGY).status is S.PARTIAL
    assert threshold.claim(D.ROW_ORDERING).status is S.UNKNOWN
    assert threshold.claim(D.DATASET_HASH).status is S.PARTIAL
    assert threshold.claim(D.EVALUATION).status is S.PARTIAL
    assert fixed.claim(D.WORLD_LAW).status is S.EXACT
    assert fixed.claim(D.COMPLETE_GENERATOR).status is S.SEMANTICALLY_EQUIVALENT
    assert fixed.claim(D.RNG_ALGORITHM).status is S.PARTIAL
    assert fixed.claim(D.RNG_STATE).status is S.PARTIAL
    assert fixed.claim(D.SEED_AUTHORITY).status is S.EXACT
    assert fixed.claim(D.RNG_STREAM_CONSTRUCTION).status is S.EXACT
    assert fixed.claim(D.RNG_DRAW_ORDER).status is S.EXACT
    assert fixed.claim(D.RNG_SUBSTREAM_STRATEGY).status is S.EXACT
    assert fixed.claim(D.ROW_ORDERING).status is S.UNKNOWN
    assert fixed.claim(D.DATASET_HASH).status is S.PARTIAL
    assert fixed.claim(D.EVALUATION).status is S.PARTIAL
    assert (
        threshold.reference_hashes[0].digest
        == "f5d691156b19854224db9cf9f05ca1be1c149631ca2b451ad38979640f94ab60"
    )
    assert (
        threshold.reference_hashes[1].digest
        == "0fd0b288b306950187e39def57200f362758996107516899d6096ea1bdf552c6"
    )
    assert (
        fixed.reference_hashes[0].digest
        == "7bcb327b3a391a1f6bcdf928b8f045edb8d4925e0b6d7d6e7261491766e0d5d3"
    )
    assert (
        fixed.reference_hashes[1].digest
        == "e2dbfc83b76ce240c013128582f58a34bd1d5b6e3092381a7223cf62ad10f00a"
    )
