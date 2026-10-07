"""Clean-room camp samples exercise the recovered world without upgrading history."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Callable

import pytest

from cmj_recovery_dynamics.contracts import (
    ForecastHorizon,
    OutcomeVariable,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    ExposureComponent,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    INITIAL_CAMP_CELLS,
    INITIAL_PRESEASON_CAMP_EVALUATION,
)
from cmj_recovery_dynamics.metrics.scoring import (
    CellValues,
    calibrated_benchmark_score,
    cellwise_normalized_rmse,
    target_metrics_from_cells,
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    HORIZON_TIMES_HOURS,
    OSS_BASELINE_TRIAL_COUNT,
    OSS_CAMP_REPRODUCTION,
    OSS_SEED,
    OSS_TARGET_TRIAL_COUNT,
    AssessmentAvailability,
    AssessmentObservation,
    CampExposure,
    CampSample,
    CriterionTrial,
    InformationLeakageError,
    PlannedExposure,
    camp_target_cell,
    generate_canonical_camp_sample,
    generate_initial_camp_sample,
    get_camp_reproduction_config,
    prediction_row_from_mapping,
    select_camp_baseline,
    validate_target_time,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    CalibrationReferenceStatus,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionDimension as Dimension,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionStatus as Status,
)


def _trial(force: float, impulse: float, depth: float = 0.25) -> CriterionTrial:
    return CriterionTrial(force, impulse, depth)


def _assessment(
    assessment_id: str,
    timestamp: float,
    force: float,
    *,
    availability: AssessmentAvailability = AssessmentAvailability.VALID,
) -> AssessmentObservation:
    trials = (_trial(force, 1.0),) if availability is AssessmentAvailability.VALID else ()
    return AssessmentObservation(assessment_id, timestamp, availability, trials)


def test_baseline_uses_two_latest_valid_assessments_in_inclusive_window() -> None:
    baseline = select_camp_baseline(
        (
            _assessment("too_old", -240.1, 10.0),
            _assessment("old", -240.0, 20.0),
            _assessment("middle", -72.0, 30.0),
            _assessment("newest", -24.0, 40.0),
            _assessment("invalid", -12.0, 50.0, availability=AssessmentAvailability.TRIAL_INVALID),
            _assessment("future", 8.0, 60.0),
        )
    )
    assert baseline.selected_assessment_ids == ("newest", "middle")
    assert baseline.force_n_per_kg == pytest.approx(35.0)
    assert baseline.net_impulse_m_s == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("horizon", "times", "outside"),
    (
        (ForecastHorizon.H72, (66.0, 72.0, 78.0), (65.99, 78.01)),
        (ForecastHorizon.D7, (156.0, 168.0, 180.0), (155.99, 180.01)),
    ),
)
def test_horizon_windows_accept_boundaries_and_reject_outside(
    horizon: ForecastHorizon, times: tuple[float, ...], outside: tuple[float, ...]
) -> None:
    for target_time in times:
        assert validate_target_time(horizon, target_time) == target_time
    for target_time in outside:
        with pytest.raises(ValueError, match="hours"):
            validate_target_time(horizon, target_time)


def test_prediction_representation_rejects_future_history_and_labels() -> None:
    valid_assessments = (_assessment("pre-240", -240.0, 20.0), _assessment("pre-48", -48.0, 21.0))
    baseline = select_camp_baseline(valid_assessments)
    index = CampExposure(
        "index",
        0.0,
        "match",
        (ExposureComponent("duration_minutes", 90.0, "minutes", 100.0),),
    )
    plan = PlannedExposure(
        "plan-48",
        48.0,
        "training",
        (ExposureComponent("duration_minutes", 80.0, "minutes", 100.0),),
    )
    fields: dict[str, object] = {
        "participant_key": "group-only",
        "origin_id": "origin-1",
        "query_id": "query-1",
        "horizon": ForecastHorizon.H72,
        "target_time_hours": 72.0,
        "baseline": baseline,
        "assessment_history": valid_assessments,
        "exposure_history": (),
        "index_exposure": index,
        "known_plan": (plan,),
    }
    row = prediction_row_from_mapping(fields)
    assert "participant_key" not in row.predictor_features()
    assert "target" not in row.predictor_features()
    past_exposure = CampExposure(
        "past",
        -72.0,
        "training",
        (ExposureComponent("duration_minutes", 90.0, "minutes", 100.0),),
    )
    with_history = prediction_row_from_mapping({**fields, "exposure_history": (past_exposure,)})
    assert with_history.exposure_history == (past_exposure,)
    with pytest.raises(InformationLeakageError, match="prohibited"):
        prediction_row_from_mapping({**fields, "label": {"force": 1.0}})
    with pytest.raises(InformationLeakageError, match="prohibited"):
        prediction_row_from_mapping({**fields, "future_realized_exposures": (plan,)})
    with pytest.raises(InformationLeakageError, match="assessment history"):
        prediction_row_from_mapping(
            {
                **fields,
                "assessment_history": (*valid_assessments, _assessment("future", 72.0, 20.0)),
            }
        )
    future_history = CampExposure(
        "future",
        8.0,
        "training",
        (ExposureComponent("duration_minutes", 90.0, "minutes", 100.0),),
    )
    with pytest.raises(InformationLeakageError, match="exposure history"):
        prediction_row_from_mapping({**fields, "exposure_history": (future_history,)})


def test_clean_room_seed_is_repeatable_and_seed_identity_is_new() -> None:
    config = get_camp_reproduction_config(811)
    assert config.reproduction_id == OSS_CAMP_REPRODUCTION.reproduction_id
    assert config.seed == 811
    assert config.seed_authority == "new_reproduction_authority"
    with pytest.raises(TypeError, match="integer"):
        get_camp_reproduction_config(True)  # type: ignore[arg-type]
    first = generate_initial_camp_sample(seed=OSS_SEED, participant_count=2)
    replay = generate_initial_camp_sample(seed=OSS_SEED, participant_count=2)
    other = generate_initial_camp_sample(seed=OSS_SEED + 1, participant_count=2)
    assert first.to_jsonl() == replay.to_jsonl()
    assert first.to_jsonl() != other.to_jsonl()
    assert first.identity.seed == OSS_SEED
    assert first.identity.seed_authority == "new_reproduction_authority"
    assert first.identity.historical_status(Dimension.WORLD_LAW) is Status.EXACT
    assert first.identity.historical_status(Dimension.RNG_ALGORITHM) is Status.EXACT
    assert first.identity.historical_status(Dimension.RNG_STREAM_CONSTRUCTION) is Status.EXACT
    assert first.identity.historical_status(Dimension.RNG_DRAW_ORDER) is Status.EXACT
    assert first.identity.historical_status(Dimension.RNG_SUBSTREAM_STRATEGY) is Status.EXACT
    assert first.identity.historical_status(Dimension.SEED_AUTHORITY) is Status.UNKNOWN
    assert first.identity.historical_status(Dimension.RNG_STATE) is Status.UNKNOWN
    assert first.identity.historical_status(Dimension.ROW_ORDERING) is Status.UNKNOWN
    assert first.identity.historical_status(Dimension.DATASET_HASH) is Status.PARTIAL
    assert first.identity.historical_status(Dimension.COMPLETE_GENERATOR) is Status.PARTIAL
    assert first.identity.historical_status(Dimension.OBSERVATION) is Status.PARTIAL
    assert first.identity.historical_status(Dimension.SPLIT_ASSIGNMENT) is Status.PARTIAL
    assert first.identity.historical_status(Dimension.EVALUATION) is Status.PARTIAL
    assert first.identity.artifact_kind == "clean_room_reproduction"
    assert "D02" not in first.identity.artifact_id
    assert "D03" not in first.identity.artifact_id
    assert first.identity.generated_dataset_identity != first.identity.historical_reference_dataset
    assert OSS_CAMP_REPRODUCTION.historical_baseline_trial_count is None
    assert OSS_CAMP_REPRODUCTION.baseline_trial_count == OSS_BASELINE_TRIAL_COUNT == 3
    assert OSS_CAMP_REPRODUCTION.rng_algorithm == "CPython random.Random version 2"
    assert "SHA-256" in OSS_CAMP_REPRODUCTION.stream_construction
    assert "measurement" in OSS_CAMP_REPRODUCTION.rng_namespaces
    assert OSS_CAMP_REPRODUCTION.baseline_trial_count_authority == (
        "open_source_reproduction_convention"
    )
    assert "no historical pre-index events are asserted" in (
        OSS_CAMP_REPRODUCTION.pre_index_exposure_history_convention
    )
    snapshot = first.identity.authority_snapshot()
    historical = snapshot["historical_authority"]
    assert isinstance(historical, dict)
    assert historical[Dimension.WORLD_LAW.value] == Status.EXACT.value
    assert historical[Dimension.SEED_AUTHORITY.value] == Status.UNKNOWN.value
    reproduction_rng = snapshot["new_reproduction_rng"]
    assert isinstance(reproduction_rng, dict)
    assert reproduction_rng["algorithm"] == OSS_CAMP_REPRODUCTION.rng_algorithm


def test_initial_and_canonical_authority_and_identities_stay_distinct() -> None:
    initial = generate_initial_camp_sample(seed=123, participant_count=1)
    canonical = generate_canonical_camp_sample(seed=123, participant_count=1)
    assert initial.identity.benchmark_name == "initial_preseason_camp_recovery"
    assert initial.identity.historical_reference_dataset == "initial_preseason_camp_public_sample"
    assert initial.identity.evaluation_name == "initial_camp_population_normalized_rmse_score"
    assert initial.identity.historical_status(Dimension.SCHEMA) is Status.PARTIAL
    assert initial.identity.historical_status(Dimension.SERIALIZATION) is Status.PARTIAL
    assert (
        initial.identity.normalization_floor
        == INITIAL_PRESEASON_CAMP_EVALUATION.normalization_floor
        == 1.01
    )
    assert canonical.identity.benchmark_name == "canonical_preseason_camp_recovery"
    assert (
        canonical.identity.historical_reference_dataset == "canonical_preseason_camp_horizon_sample"
    )
    assert canonical.identity.evaluation_name == "canonical_camp_population_normalized_rmse_score"
    assert canonical.identity.historical_status(Dimension.SCHEMA) is Status.EXACT
    assert (
        canonical.identity.historical_status(Dimension.SERIALIZATION)
        is Status.SEMANTICALLY_EQUIVALENT
    )
    assert (
        canonical.identity.normalization_floor
        == CANONICAL_PRESEASON_CAMP_EVALUATION.normalization_floor
        == 1.0
    )
    assert initial.identity.artifact_id != canonical.identity.artifact_id
    assert (
        initial.identity.generated_dataset_identity != canonical.identity.generated_dataset_identity
    )
    for identity in (initial.identity, canonical.identity):
        assert identity.historical_reference_hashes
        assert identity.historical_status(Dimension.SEED_AUTHORITY) is Status.UNKNOWN
        assert identity.historical_status(Dimension.ROW_ORDERING) is Status.UNKNOWN
        assert identity.historical_status(Dimension.DATASET_HASH) is Status.PARTIAL
        assert identity.calibration_reference_status is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
        assert identity.calibration_reference_value is None
        assert identity.historical_baseline_trial_count is None
        assert identity.baseline_trial_count_authority == "open_source_reproduction_convention"


def test_clean_room_jsonl_is_valid_and_cannot_claim_historical_hashes() -> None:
    sample = generate_canonical_camp_sample(seed=7, participant_count=1)
    records = tuple(json.loads(line) for line in sample.to_jsonl().splitlines())
    assert len(records) == 4
    assert all(record["artifact_kind"] == "clean_room_reproduction" for record in records)
    assert all(record["artifact_id"] == sample.identity.artifact_id for record in records)
    assert all(record["reproduction_seed"] == sample.identity.seed for record in records)
    assert all(record["benchmark_identity"] == sample.identity.benchmark_name for record in records)
    assert all("historical_reference_hashes" not in record for record in records)
    assert all("target" not in record["features"] for record in records)
    assert OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value in records[0]["label"]
    assert OutcomeVariable.NET_IMPULSE_INNOVATION.value in records[0]["label"]
    assert "label_units" in records[0]
    assert "latent_state" not in records[0]["label"]
    assert "percent_change" not in records[0]["label"]


def test_sample_has_participant_heterogeneity_and_supported_design_bounds() -> None:
    sample = generate_initial_camp_sample(seed=88, participant_count=4)
    participants = {
        row.participant_key: row for row in sample.rows if row.horizon is ForecastHorizon.H72
    }
    assert len({row.baseline.force_n_per_kg for row in participants.values()}) > 1
    assert len({row.baseline.net_impulse_m_s for row in participants.values()}) > 1
    assert all(0.16 <= row.baseline.depth_m <= 0.42 for row in participants.values())
    for row in sample.rows:
        components = tuple(
            component
            for plan in row.known_plan
            for component in plan.components
            if component.name == "duration_minutes"
        )
        assert all(
            component.value is not None and 60.0 <= component.value <= 140.0
            for component in components
        )


def test_query_specific_plan_history_and_d7_target_aggregation() -> None:
    sample = generate_canonical_camp_sample(seed=19, participant_count=1)
    by_horizon = {row.horizon: row for row in sample.rows}
    h72 = by_horizon[ForecastHorizon.H72]
    d7 = by_horizon[ForecastHorizon.D7]
    assert tuple(item.time_from_origin_hours for item in h72.known_plan) == (48.0,)
    assert tuple(item.time_from_origin_hours for item in d7.known_plan) == (48.0, 120.0)
    assert d7.exposure_history == ()
    assert h72.index_exposure.time_from_origin_hours == 0.0
    assert h72.target_time_hours == HORIZON_TIMES_HOURS[ForecastHorizon.H72]
    assert d7.target_time_hours == HORIZON_TIMES_HOURS[ForecastHorizon.D7]
    for row, target in zip(sample.rows, sample.targets, strict=True):
        assert target.force_innovation_n_per_kg == pytest.approx(
            target.observed_force_n_per_kg - row.baseline.force_n_per_kg
        )
        assert target.net_impulse_innovation_m_s == pytest.approx(
            target.observed_net_impulse_m_s - row.baseline.net_impulse_m_s
        )
        assert len(target.criterion_trials) == OSS_TARGET_TRIAL_COUNT
    cells = {camp_target_cell(row, outcome) for row in sample.rows for outcome in OutcomeVariable}
    assert cells == set(INITIAL_CAMP_CELLS)


def test_initial_and_canonical_training_validation_geometry() -> None:
    generators: tuple[Callable[..., CampSample], ...] = (
        generate_initial_camp_sample,
        generate_canonical_camp_sample,
    )
    for generate in generators:
        for split, participants, origins, rows in (
            ("training", 1024, 2048, 4096),
            ("public_validation", 128, 256, 512),
        ):
            sample = generate(split_name=split, seed=OSS_SEED)
            assert sample.geometry.participants == participants
            assert sample.geometry.origins == origins
            assert sample.geometry.query_rows == rows
            assert len(sample.rows) == rows
            assert len({row.participant_key for row in sample.rows}) == participants
            assert len({row.origin_id for row in sample.rows}) == origins
            assert sample.identity.artifact_kind == "clean_room_reproduction"
            per_origin = Counter(row.origin_id for row in sample.rows)
            assert set(per_origin.values()) == {2}


def test_camp_metric_cells_normalization_progress_and_aggregation() -> None:
    values = tuple(
        CellValues(cell, (0.0, 1.0, 2.0), (0.0, 2.0, 4.0)) for cell in INITIAL_CAMP_CELLS
    )
    metrics = cellwise_normalized_rmse(values, INITIAL_CAMP_CELLS)
    assert len(metrics) == 4
    for metric in metrics:
        assert metric.root_mean_square_error == pytest.approx(math.sqrt(5.0 / 3.0))
        assert metric.observation_standard_deviation == pytest.approx(math.sqrt(8.0 / 3.0))
        assert metric.normalized_error == pytest.approx(math.sqrt(5.0 / 8.0))
        assert metric.row_count == 3
    initial_targets = target_metrics_from_cells(
        metrics, INITIAL_CAMP_CELLS, floor=1.01, perfect=0.0
    )
    canonical_targets = target_metrics_from_cells(
        metrics, INITIAL_CAMP_CELLS, floor=1.0, perfect=0.0
    )
    assert {item.floor for item in initial_targets} == {1.01}
    assert {item.floor for item in canonical_targets} == {1.0}
    # Test-only calibration input exercises the generic score transform; no task reference is set.
    score = calibrated_benchmark_score(initial_targets, reference_progress=0.5)
    expected_cell_progress = (1.01 - math.sqrt(5.0 / 8.0)) / 1.01
    assert score.aggregate_progress == pytest.approx(expected_cell_progress)
    assert len(score.target_progress) == 4
    assert score.score == pytest.approx(expected_cell_progress)
    canonical_score = calibrated_benchmark_score(canonical_targets, reference_progress=0.5)
    canonical_progress = 1.0 - math.sqrt(5.0 / 8.0)
    assert canonical_score.aggregate_progress == pytest.approx(canonical_progress)
    assert len(canonical_score.target_progress) == 4
