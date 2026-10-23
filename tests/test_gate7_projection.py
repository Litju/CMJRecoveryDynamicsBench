"""Golden and boundary checks for the recovered Gate7 feature projection."""

import hashlib
import json
from dataclasses import replace

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import ExposureComponent
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_AVAILABLE_FEATURE_INDICES,
    GATE7_AVAILABLE_FEATURE_NAMES,
    GATE7_CAMP_ROW_GAPS,
    GATE7_FEATURE_CONTRACT,
    GATE7_FEATURE_NAMES,
    GATE7_FEATURE_UNITS,
    Gate7AvailableFeatureProjection,
    Gate7CampPredictionInput,
    Gate7ExposureFeature,
    Gate7FeatureConstruction,
    Gate7FeatureUnit,
    Gate7HistoryAssessment,
    Gate7MissingAuthorityCode,
    Gate7PlanFeature,
    Gate7ProjectionAttempt,
    Gate7ProjectionInputCode,
    Gate7ProjectionInputError,
    Gate7ProjectionStatus,
    Gate7PublicFeatureRow,
    Gate7RoutineAssessment,
    Gate7RoutineSource,
    Gate7RoutineState,
    Gate7RoutineTemporalAuthority,
    project_gate7_available_fields_v1,
    project_gate7_historical_v1,
    project_gate7_v1,
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    AssessmentAvailability,
    AssessmentObservation,
    BaselineSummary,
    CampExposure,
    CampPredictionRow,
    CriterionTrial,
    InformationLeakageError,
    PlannedExposure,
    generate_canonical_camp_sample,
)

_EXPECTED_NAMES = (
    "baseline.relative_mean_concentric_force",
    "baseline.relative_concentric_net_impulse",
    "horizon.H72",
    "horizon.D7",
    "target_time_hours",
    "target_window_hours.low",
    "target_window_hours.high",
    "public_features.history_assessments[0].time_from_origin_hours",
    "public_features.history_assessments[0].relative_mean_concentric_force",
    "public_features.history_assessments[0].relative_concentric_net_impulse",
    "public_features.history_assessments[0].depth_m",
    "public_features.history_assessments[1].time_from_origin_hours",
    "public_features.history_assessments[1].relative_mean_concentric_force",
    "public_features.history_assessments[1].relative_concentric_net_impulse",
    "public_features.history_assessments[1].depth_m",
    "public_features.history_assessments[2].time_from_origin_hours",
    "public_features.history_assessments[2].relative_mean_concentric_force",
    "public_features.history_assessments[2].relative_concentric_net_impulse",
    "public_features.history_assessments[2].depth_m",
    "public_features.history_assessments[3].time_from_origin_hours",
    "public_features.history_assessments[3].relative_mean_concentric_force",
    "public_features.history_assessments[3].relative_concentric_net_impulse",
    "public_features.history_assessments[3].depth_m",
    "public_features.history_exposures[0].time_from_origin_hours",
    "public_features.history_exposures[0].duration_minutes",
    "public_features.index_exposure.time_from_origin_hours",
    "public_features.index_exposure.duration_minutes",
    "public_features.known_plan[0].time_from_origin_hours",
    "public_features.known_plan[0].duration_minutes",
    "public_features.known_plan[1].time_from_origin_hours",
    "public_features.known_plan[1].duration_minutes",
    "public_features.known_plan[2].time_from_origin_hours",
    "public_features.known_plan[2].duration_minutes",
    "public_features.routine_assessment.scheduled",
    "public_features.routine_assessment.availability_state.FIELD_STRUCTURALLY_ABSENT",
    "public_features.routine_assessment.availability_state.OBSERVED_MASKED",
    "public_features.routine_assessment.availability_state.SCHEDULED_UNAVAILABLE",
    "public_features.routine_assessment.availability_state.TRIAL_INVALID",
    "public_features.routine_assessment.availability_state.UNSCHEDULED",
)
_EXPECTED_UNITS = (
    Gate7FeatureUnit.NEWTON_PER_KILOGRAM,
    Gate7FeatureUnit.METER_PER_SECOND,
    Gate7FeatureUnit.DIMENSIONLESS,
    Gate7FeatureUnit.DIMENSIONLESS,
    Gate7FeatureUnit.HOUR,
    Gate7FeatureUnit.HOUR,
    Gate7FeatureUnit.HOUR,
    *(
        unit
        for _ in range(4)
        for unit in (
            Gate7FeatureUnit.HOUR,
            Gate7FeatureUnit.NEWTON_PER_KILOGRAM,
            Gate7FeatureUnit.METER_PER_SECOND,
            Gate7FeatureUnit.METER,
        )
    ),
    Gate7FeatureUnit.HOUR,
    Gate7FeatureUnit.MINUTE,
    Gate7FeatureUnit.HOUR,
    Gate7FeatureUnit.MINUTE,
    *(unit for _ in range(3) for unit in (Gate7FeatureUnit.HOUR, Gate7FeatureUnit.MINUTE)),
    *(Gate7FeatureUnit.DIMENSIONLESS for _ in range(6)),
)
# Golden vectors captured by differential execution of the recovered feature_vector on these
# independent synthetic rows; the restricted original source is not copied into this package.
_GOLDEN_H72 = np.asarray(
    (
        23.5,
        2.625,
        1.0,
        0.0,
        72.0,
        66.0,
        78.0,
        -240.0,
        20.0,
        2.0,
        0.25,
        -72.0,
        22.0,
        2.25,
        0.25,
        -48.0,
        23.0,
        2.5,
        0.375,
        -24.0,
        24.0,
        2.75,
        0.5,
        -96.0,
        123.5,
        0.0,
        80.0,
        0.0,
        80.0,
        48.0,
        95.25,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    ),
    dtype=np.float64,
)
_GOLDEN_D7 = np.asarray(
    (
        23.5,
        2.625,
        0.0,
        1.0,
        168.0,
        156.0,
        180.0,
        -240.0,
        20.0,
        2.0,
        0.25,
        -72.0,
        22.0,
        2.25,
        0.25,
        -48.0,
        23.0,
        2.5,
        0.375,
        -24.0,
        24.0,
        2.75,
        0.5,
        -96.0,
        123.5,
        0.0,
        80.0,
        0.0,
        80.0,
        48.0,
        95.25,
        120.0,
        110.75,
        1.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
    ),
    dtype=np.float64,
)


def _routine_source(origin: str = "origin") -> Gate7RoutineSource:
    payload = json.dumps([[origin, True, "TRIAL_INVALID", 0.0]]).encode()
    return Gate7RoutineSource(payload, hashlib.sha256(payload).hexdigest())


def _source_row(
    horizon: ForecastHorizon = ForecastHorizon.H72,
    *,
    routine_state: Gate7RoutineState = Gate7RoutineState.TRIAL_INVALID,
    routine_temporal: Gate7RoutineTemporalAuthority = (
        Gate7RoutineTemporalAuthority.ORIGIN_KEYED_PUBLIC_STATE
    ),
) -> Gate7PublicFeatureRow:
    h72 = horizon is ForecastHorizon.H72
    assessments = (
        Gate7HistoryAssessment(-24.0, 24.0, 2.75, 0.5, "valid"),
        Gate7HistoryAssessment(-240.0, 20.0, 2.0, 0.25, "valid"),
        Gate7HistoryAssessment(-72.0, 22.0, 2.25, 0.25, "valid"),
        Gate7HistoryAssessment(-48.0, 23.0, 2.5, 0.375, "valid"),
    )
    plan = (
        Gate7PlanFeature(48.0, 95.25),
        Gate7PlanFeature(0.0, 80.0),
    )
    if not h72:
        plan += (Gate7PlanFeature(120.0, 110.75),)
    return Gate7PublicFeatureRow(
        baseline_relative_mean_concentric_force=23.5,
        baseline_relative_concentric_net_impulse=2.625,
        horizon=horizon,
        target_time_hours=72.0 if h72 else 168.0,
        target_window_hours=(66.0, 78.0) if h72 else (156.0, 180.0),
        history_assessments=assessments,
        history_exposures=(Gate7ExposureFeature(-96.0, 123.5),),
        index_exposure=Gate7ExposureFeature(0.0, 80.0),
        known_plan=plan,
        routine_assessment=Gate7RoutineAssessment(
            routine_state is not Gate7RoutineState.UNSCHEDULED,
            routine_state,
            routine_temporal,
            "origin",
            _routine_source().expected_sha256,
            0.0,
        ),
    )


def _duration(value: float) -> tuple[ExposureComponent, ...]:
    return (ExposureComponent("duration_minutes", value, "minutes", 100.0),)


def _camp_row(horizon: ForecastHorizon) -> CampPredictionRow:
    histories = (
        (-240.0, 20.0, 2.0, 0.25, "a-240"),
        (-72.0, 22.0, 2.25, 0.25, "a-72"),
        (-48.0, 23.0, 2.5, 0.375, "a-48"),
        (-24.0, 24.0, 2.75, 0.5, "a-24"),
    )
    assessments = tuple(
        AssessmentObservation(
            assessment_id,
            time,
            AssessmentAvailability.VALID,
            (CriterionTrial(force, impulse, depth),) * 3,
        )
        for time, force, impulse, depth, assessment_id in histories
    )
    index = CampExposure("index", 0.0, "training", _duration(80.0))
    known_plan = (PlannedExposure("plan-48", 48.0, "training", _duration(95.25)),)
    target_time = 72.0 if horizon is ForecastHorizon.H72 else 168.0
    if horizon is ForecastHorizon.D7:
        known_plan += (PlannedExposure("plan-120", 120.0, "training", _duration(110.75)),)
    return CampPredictionRow(
        "participant",
        "origin",
        horizon.label,
        horizon,
        target_time,
        BaselineSummary(23.5, 2.625, 0.4375, ("a-48", "a-24")),
        assessments,
        (CampExposure("history", -96.0, "training", _duration(123.5)),),
        index,
        known_plan,
    )


def test_contract_records_exact_order_width_units_and_distinct_m0_identity() -> None:
    assert GATE7_FEATURE_CONTRACT.version == "gate7_feature_projection_v1"
    assert GATE7_FEATURE_CONTRACT.model_identity == "gate7_m0_candidate"
    assert GATE7_FEATURE_CONTRACT.model_identity != "initial_public_reference_artifact"
    assert GATE7_FEATURE_CONTRACT.feature_count == 39
    assert GATE7_FEATURE_CONTRACT.expected_shape(5) == (5, 39)
    assert GATE7_FEATURE_NAMES == _EXPECTED_NAMES
    assert GATE7_FEATURE_UNITS == _EXPECTED_UNITS
    assert tuple(feature.index for feature in GATE7_FEATURE_CONTRACT.features) == tuple(range(39))
    assert {feature.dtype for feature in GATE7_FEATURE_CONTRACT.features} == {"float64"}
    assert tuple(feature.construction for feature in GATE7_FEATURE_CONTRACT.features) == tuple(
        Gate7FeatureConstruction.CAMP_ROW_DIRECT
        if index in (*range(7), 25)
        else Gate7FeatureConstruction.GATE7_PUBLIC_ROW
        for index in range(39)
    )


def test_source_preprocessing_missingness_and_duration_rules_are_exact() -> None:
    preprocessing = GATE7_FEATURE_CONTRACT.model_input_preprocessing
    assert "sample standard deviations (ddof=1)" in preprocessing
    assert "replaces zero scales with 1.0" in preprocessing
    assert "casts model tensors to float32" in preprocessing
    assert "fitted means and scales are not included" in preprocessing
    assert "Stable sort" in GATE7_FEATURE_CONTRACT.features[7].derivation
    assert "exactly four" in GATE7_FEATURE_CONTRACT.features[7].derivation
    assert (
        "does not inspect validity_state" in GATE7_FEATURE_CONTRACT.features[7].missingness_handling
    )
    assert "exactly one" in GATE7_FEATURE_CONTRACT.features[23].derivation
    assert "no unit conversion" in GATE7_FEATURE_CONTRACT.features[26].derivation
    assert "pad only slot 2" in GATE7_FEATURE_CONTRACT.features[31].missingness_handling
    assert "origin-keyed" in GATE7_FEATURE_CONTRACT.features[33].temporal_availability


def test_original_source_golden_matches_order_sort_padding_and_horizons() -> None:
    rows = (
        _source_row(),
        _source_row(ForecastHorizon.D7, routine_state=Gate7RoutineState.OBSERVED_MASKED),
    )
    matrix = project_gate7_historical_v1(rows)

    assert matrix.shape == (2, 39)
    assert matrix.dtype == np.dtype(np.float64)
    assert np.isfinite(matrix).all()
    np.testing.assert_array_equal(matrix[0], _GOLDEN_H72)
    np.testing.assert_array_equal(matrix[1], _GOLDEN_D7)
    assert matrix[0, 24] == 123.5
    assert matrix[0, 28] == 80.0
    assert matrix[0, 31:33].tolist() == [0.0, 0.0]


def test_feature_ordering_is_stable_for_ties_and_validity_state_is_not_a_feature() -> None:
    row = _source_row()
    tied = replace(
        row,
        history_assessments=(
            Gate7HistoryAssessment(-48.0, 31.0, 3.1, 0.31, "TRIAL_INVALID"),
            Gate7HistoryAssessment(-240.0, 20.0, 2.0, 0.20, "valid"),
            Gate7HistoryAssessment(-48.0, 32.0, 3.2, 0.32, "valid"),
            Gate7HistoryAssessment(-24.0, 24.0, 2.4, 0.24, "valid"),
        ),
    )
    values = project_gate7_historical_v1((tied,))[0]
    assert values[11] == -48.0
    assert values[12] == 31.0
    assert values[15] == -48.0
    assert values[16] == 32.0

    tied_plan = replace(
        _source_row(),
        known_plan=(
            Gate7PlanFeature(48.0, 80.0),
            Gate7PlanFeature(0.0, 70.0),
            Gate7PlanFeature(48.0, 90.0),
        ),
    )
    plan_values = project_gate7_historical_v1((tied_plan,))[0]
    np.testing.assert_array_equal(plan_values[27:33], (0.0, 70.0, 48.0, 80.0, 48.0, 90.0))


def test_source_missing_records_and_invalid_values_fail_without_filling() -> None:
    row = _source_row()
    cases = (
        (
            replace(row, history_assessments=row.history_assessments[:3]),
            Gate7ProjectionInputCode.ASSESSMENT_HISTORY_COUNT,
        ),
        (replace(row, history_exposures=()), Gate7ProjectionInputCode.HISTORY_EXPOSURE_COUNT),
        (
            replace(row, known_plan=(Gate7PlanFeature(0.0, 80.0),)),
            Gate7ProjectionInputCode.KNOWN_PLAN_COUNT,
        ),
        (
            replace(
                row,
                known_plan=(
                    *row.known_plan,
                    Gate7PlanFeature(120.0, 100.0),
                    Gate7PlanFeature(144.0, 90.0),
                ),
            ),
            Gate7ProjectionInputCode.KNOWN_PLAN_COUNT,
        ),
    )
    for malformed, code in cases:
        with pytest.raises(Gate7ProjectionInputError) as error:
            project_gate7_historical_v1((malformed,))
        assert error.value.code is code

    invalid = replace(
        row,
        history_assessments=(
            replace(row.history_assessments[0], relative_mean_concentric_force=None),
            *row.history_assessments[1:],
        ),
    )
    with pytest.raises(Gate7ProjectionInputError) as error:
        project_gate7_historical_v1((invalid,))
    assert error.value.code is Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE
    assert error.value.feature_names == (_EXPECTED_NAMES[20],)

    invalid_trial_state = replace(
        row,
        history_assessments=(
            replace(row.history_assessments[0], validity_state="TRIAL_INVALID"),
            *row.history_assessments[1:],
        ),
    )
    np.testing.assert_array_equal(
        project_gate7_historical_v1((invalid_trial_state,)),
        project_gate7_historical_v1((row,)),
    )


def test_origin_safe_projection_blocks_unresolved_or_post_origin_routine_state() -> None:
    h72 = Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), _source_row().routine_assessment)
    d7 = Gate7CampPredictionInput(
        _camp_row(ForecastHorizon.D7),
        _source_row(
            ForecastHorizon.D7,
        ).routine_assessment,
    )
    ready = project_gate7_v1((h72, d7), routine_source=_routine_source())
    assert ready.status is Gate7ProjectionStatus.READY_FOR_GATE7_FULL_PROJECTION_REVIEW
    assert ready.matrix is not None
    assert ready.matrix.shape == (2, 39)
    assert ready.matrix.dtype == np.dtype(np.float64)
    assert np.isfinite(ready.matrix).all()
    np.testing.assert_array_equal(ready.matrix[0], _GOLDEN_H72)
    expected_d7 = _GOLDEN_D7.copy()
    expected_d7[34:39] = (0, 0, 0, 1, 0)
    np.testing.assert_array_equal(ready.matrix[1], expected_d7)

    for authority, code in (
        (
            Gate7RoutineTemporalAuthority.UNRESOLVED,
            Gate7MissingAuthorityCode.ROUTINE_TEMPORAL_AUTHORITY_UNRESOLVED,
        ),
        (
            Gate7RoutineTemporalAuthority.POST_ORIGIN,
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_POST_ORIGIN,
        ),
    ):
        routine = replace(_source_row().routine_assessment, temporal_authority=authority)
        blocked = project_gate7_v1(
            (Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), routine),)
        )
        assert blocked.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
        assert blocked.matrix is None
        assert blocked.missing_authority[0].code is code


def test_historical_extractor_is_preserved_separately_from_prospective_checks() -> None:
    post_origin = _source_row(routine_temporal=Gate7RoutineTemporalAuthority.POST_ORIGIN)
    np.testing.assert_array_equal(project_gate7_historical_v1((post_origin,))[0], _GOLDEN_H72)

    blocked = project_gate7_v1(
        (Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), post_origin.routine_assessment),)
    )
    assert blocked.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
    assert blocked.matrix is None
    assert (
        blocked.missing_authority[0].code
        is Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_POST_ORIGIN
    )


def test_each_missingness_state_uses_its_frozen_one_hot_column() -> None:
    for index, state in enumerate(Gate7RoutineState):
        row = _source_row(routine_state=state)
        values = project_gate7_historical_v1((row,))[0]
        expected = np.zeros(6, dtype=np.float64)
        expected[0] = float(state is not Gate7RoutineState.UNSCHEDULED)
        expected[index + 1] = 1.0
        np.testing.assert_array_equal(values[33:39], expected)


def test_current_camp_row_gaps_are_machine_readable_and_no_routine_is_inferred() -> None:
    rows = generate_canonical_camp_sample(seed=19, participant_count=1).rows
    missing_routine = project_gate7_v1(tuple(Gate7CampPredictionInput(row) for row in rows))
    assert missing_routine.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
    assert missing_routine.matrix is None
    assert missing_routine.missing_authority[0].code is (
        Gate7MissingAuthorityCode.CAMP_ROW_ROUTINE_ASSESSMENT_ABSENT
    )

    with_routine = project_gate7_v1(
        tuple(
            Gate7CampPredictionInput(row, _routine_source(row.origin_id).records()[0])
            for row in rows
        ),
        routine_source=_routine_source(rows[0].origin_id),
    )
    assert with_routine.matrix is None
    assert with_routine.missing_authority[0].code is (
        Gate7MissingAuthorityCode.CAMP_ROW_ASSESSMENT_HISTORY_SHAPE
    )
    assert len(GATE7_CAMP_ROW_GAPS) == 3


def test_projection_excludes_grouping_keys_and_is_reproducible() -> None:
    row = _camp_row(ForecastHorizon.H72)
    routine = _source_row().routine_assessment
    first = project_gate7_v1(
        (Gate7CampPredictionInput(row, routine),), routine_source=_routine_source()
    )
    repeated = project_gate7_v1(
        (Gate7CampPredictionInput(row, routine),), routine_source=_routine_source()
    )
    changed_ids = replace(row, participant_key="p2", origin_id="o2", query_id="q2")
    changed_source = _routine_source("o2")
    changed = project_gate7_v1(
        (Gate7CampPredictionInput(changed_ids, changed_source.records()[0]),),
        routine_source=changed_source,
    )

    assert first.matrix is not None and repeated.matrix is not None and changed.matrix is not None
    np.testing.assert_array_equal(first.matrix, repeated.matrix)
    np.testing.assert_array_equal(first.matrix, changed.matrix)
    assert not any(
        key in name
        for name in GATE7_FEATURE_NAMES
        for key in ("participant_key", "origin_id", "query_id", "assessment_id", "event_id")
    )


def test_public_row_rejects_future_history_and_future_plan_injection() -> None:
    row = _camp_row(ForecastHorizon.H72)
    future_assessment = AssessmentObservation("future", 1.0, AssessmentAvailability.UNSCHEDULED)
    with pytest.raises(InformationLeakageError, match="assessment history must stop before"):
        replace(row, assessment_history=(*row.assessment_history[:-1], future_assessment))

    future_plan = PlannedExposure("future", 73.0, "training", _duration(100.0))
    with pytest.raises(InformationLeakageError, match="post-query event"):
        replace(row, known_plan=(*row.known_plan, future_plan))


def test_available_camp_fields_and_projection_result_contracts_remain_valid() -> None:
    rows = generate_canonical_camp_sample(seed=19, participant_count=1).rows
    available = project_gate7_available_fields_v1(rows)
    assert GATE7_AVAILABLE_FEATURE_INDICES == (0, 1, 2, 3, 4, 5, 6, 25)
    assert GATE7_AVAILABLE_FEATURE_NAMES == tuple(
        GATE7_FEATURE_NAMES[index] for index in (0, 1, 2, 3, 4, 5, 6, 25)
    )
    assert available.values.shape == (len(rows), 8)
    assert available.values.dtype == np.dtype(np.float64)
    assert np.isfinite(available.values).all()
    assert not available.values.flags.writeable
    with pytest.raises(ValueError, match="non-negative"):
        GATE7_FEATURE_CONTRACT.expected_shape(-1)


def test_projection_matrix_validation_rejects_wrong_width_dtype_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="shape"):
        Gate7AvailableFeatureProjection(
            GATE7_AVAILABLE_FEATURE_NAMES,
            np.zeros((1, 7), dtype=np.float64),
        )
    with pytest.raises(TypeError, match="float64"):
        Gate7AvailableFeatureProjection(
            GATE7_AVAILABLE_FEATURE_NAMES,
            np.zeros((1, 8), dtype=np.float32),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="finite"):
        Gate7AvailableFeatureProjection(
            GATE7_AVAILABLE_FEATURE_NAMES,
            np.full((1, 8), np.nan, dtype=np.float64),
        )
    with pytest.raises(ValueError, match="shape"):
        Gate7ProjectionAttempt(
            Gate7ProjectionStatus.READY_FOR_GATE7_FULL_PROJECTION_REVIEW,
            1,
            np.zeros((1, 38), dtype=np.float64),
            (),
        )


@pytest.mark.parametrize(
    "change,code",
    [
        ({"origin_id": "another"}, Gate7MissingAuthorityCode.ROUTINE_ORIGIN_MISMATCH),
        ({"source_sha256": "unverified"}, Gate7MissingAuthorityCode.ROUTINE_SOURCE_MISMATCH),
        (
            {"available_at_origin_hours": 1.0},
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_POST_ORIGIN,
        ),
        (
            {"availability_state": Gate7RoutineState.OBSERVED_MASKED},
            Gate7MissingAuthorityCode.ROUTINE_SOURCE_MISMATCH,
        ),
    ],
)
def test_origin_source_rejects_adversarial_metadata(
    change: dict[str, object],
    code: Gate7MissingAuthorityCode,
) -> None:
    source = _routine_source()
    routine = replace(source.records()[0], **change)
    inputs = (
        Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), source.records()[0]),
        Gate7CampPredictionInput(_camp_row(ForecastHorizon.D7), routine),
    )
    for batch in (inputs, inputs[1:]):
        result = project_gate7_v1(batch, routine_source=source)
        assert result.matrix is None
        assert result.missing_authority[0].code is code


def test_enum_alone_and_unpinned_source_never_grant_authority() -> None:
    routine = _source_row().routine_assessment
    result = project_gate7_v1((Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), routine),))
    assert result.matrix is None
    assert result.missing_authority[0].code is Gate7MissingAuthorityCode.ROUTINE_SOURCE_MISMATCH
    with pytest.raises(ValueError, match="SHA-256"):
        Gate7RoutineSource(_routine_source().payload, "untrusted")


@pytest.mark.parametrize(
    "records",
    [
        [["origin", True, "TRIAL_INVALID", 0], ["origin", True, "OBSERVED_MASKED", 0]],
        [["origin", True, "TRIAL_INVALID", float("nan")]],
        [["origin", True, "TRIAL_INVALID", "0"]],
        [["origin", 1, "TRIAL_INVALID", 0]],
        [["", True, "TRIAL_INVALID", 0]],
        [["origin", True, "unknown", 0]],
        {"origin": "invalid shape"},
        [["origin"]],
    ],
)
def test_source_rejects_ambiguous_or_malformed_records(records: object) -> None:
    payload = json.dumps(records).encode()
    with pytest.raises(ValueError):
        Gate7RoutineSource(payload, hashlib.sha256(payload).hexdigest())


def test_post_origin_authoritative_source_is_blocked() -> None:
    payload = json.dumps([["origin", True, "TRIAL_INVALID", 1.0]]).encode()
    source = Gate7RoutineSource(payload, hashlib.sha256(payload).hexdigest())
    result = project_gate7_v1(
        (Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), source.records()[0]),),
        routine_source=source,
    )
    assert result.matrix is None
    assert result.missing_authority[0].code is (
        Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_POST_ORIGIN
    )


@pytest.mark.parametrize("horizon", (ForecastHorizon.H72, ForecastHorizon.D7))
def test_shared_origin_source_is_consistent_across_separate_calls(horizon: ForecastHorizon) -> None:
    source = _routine_source()
    result = project_gate7_v1(
        (Gate7CampPredictionInput(_camp_row(horizon), source.records()[0]),),
        routine_source=source,
    )
    assert result.matrix is not None
    np.testing.assert_array_equal(result.matrix[0, 33:39], (1, 0, 0, 0, 1, 0))


@pytest.mark.parametrize(
    "component",
    [
        ExposureComponent("duration_minutes", None, "minutes", 100, observed=False),
        ExposureComponent("duration_minutes", 80, "minutes", 100, day_mask=False),
        ExposureComponent("duration_minutes", 80, "minutes", 100, event_mask=False),
        ExposureComponent("duration_minutes", 80, "seconds", 100),
        ExposureComponent("other", 80, "minutes", 100),
    ],
)
@pytest.mark.parametrize("slot", ("history", "index", "plan"))
def test_prospective_duration_rejects_unobserved_masked_or_mislabelled(
    component: ExposureComponent,
    slot: str,
) -> None:
    # A separate observed component keeps the exposure valid at its own boundary.
    row = _camp_row(ForecastHorizon.H72)
    components = (component, ExposureComponent("load", 1, "dimensionless", 1))
    if slot == "index":
        row = replace(row, index_exposure=replace(row.index_exposure, components=components))
    elif slot == "history":
        row = replace(
            row, exposure_history=(replace(row.exposure_history[0], components=components),)
        )
    else:
        row = replace(row, known_plan=(replace(row.known_plan[0], components=components),))
    result = project_gate7_v1(
        (Gate7CampPredictionInput(row, _routine_source().records()[0]),),
        routine_source=_routine_source(),
    )
    assert result.matrix is None
    assert "duration_component_invalid" in result.missing_authority[0].evidence_required


def test_duration_validation_at_component_and_event_boundaries() -> None:
    for value in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite and non-negative"):
            ExposureComponent("duration_minutes", value, "minutes", 100)
    row = _camp_row(ForecastHorizon.H72)
    duplicate = replace(
        row, index_exposure=replace(row.index_exposure, components=_duration(80) * 2)
    )
    result = project_gate7_v1(
        (Gate7CampPredictionInput(duplicate, _routine_source().records()[0]),),
        routine_source=_routine_source(),
    )
    assert result.matrix is None
    assert "exactly one duration_minutes" in result.missing_authority[0].evidence_required
    component = _duration(80)[0]
    assert component.contribution == 0.8
    assert replace(component, day_mask=False).contribution is None
    # Historical rows contain raw minutes, with no component mask or normalization.
    assert project_gate7_historical_v1((_source_row(),))[0, 26] == 80


def test_originless_enum_only_metadata_is_blocked_even_with_a_trusted_source() -> None:
    routine = Gate7RoutineAssessment(
        True,
        Gate7RoutineState.TRIAL_INVALID,
        Gate7RoutineTemporalAuthority.ORIGIN_KEYED_PUBLIC_STATE,
    )
    result = project_gate7_v1(
        (Gate7CampPredictionInput(_camp_row(ForecastHorizon.H72), routine),),
        routine_source=_routine_source(),
    )
    assert result.matrix is None
    assert result.missing_authority[0].code is Gate7MissingAuthorityCode.ROUTINE_ORIGIN_MISMATCH
