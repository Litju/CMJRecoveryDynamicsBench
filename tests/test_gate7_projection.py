"""Source-closed checks for the Gate7 feature contract and blocked full projection."""

from dataclasses import replace

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_AVAILABLE_FEATURE_INDICES,
    GATE7_AVAILABLE_FEATURE_NAMES,
    GATE7_FEATURE_CONTRACT,
    GATE7_FEATURE_NAMES,
    GATE7_FEATURE_UNITS,
    GATE7_MISSING_AUTHORITY,
    Gate7FeatureConstruction,
    Gate7FeatureUnit,
    Gate7ProjectionStatus,
    project_gate7_available_fields_v1,
    project_gate7_v1,
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    AssessmentAvailability,
    AssessmentObservation,
    CampPredictionRow,
    InformationLeakageError,
    generate_canonical_camp_sample,
)


def _rows() -> tuple[CampPredictionRow, ...]:
    return generate_canonical_camp_sample(seed=19, participant_count=1).rows


def test_contract_records_exact_order_width_units_and_distinct_m0_identity() -> None:
    expected_names = (
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
    expected_units = (
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

    assert GATE7_FEATURE_CONTRACT.version == "gate7_feature_projection_v1"
    assert GATE7_FEATURE_CONTRACT.model_identity == "gate7_m0_candidate"
    assert GATE7_FEATURE_CONTRACT.model_identity != "initial_public_reference_artifact"
    assert GATE7_FEATURE_CONTRACT.feature_count == 39
    assert GATE7_FEATURE_CONTRACT.expected_shape(5) == (5, 39)
    assert GATE7_FEATURE_NAMES == expected_names
    assert GATE7_FEATURE_UNITS == expected_units
    assert tuple(feature.index for feature in GATE7_FEATURE_CONTRACT.features) == tuple(range(39))
    assert {feature.dtype for feature in GATE7_FEATURE_CONTRACT.features} == {"float64"}


def test_preprocessing_and_categorical_missingness_are_recorded_without_fitted_values() -> None:
    assert "train-only mean/std standardization" in (
        GATE7_FEATURE_CONTRACT.model_input_preprocessing
    )
    assert "means and scales are not part" in GATE7_FEATURE_CONTRACT.model_input_preprocessing
    assert GATE7_FEATURE_CONTRACT.features[2].derivation == (
        "One-hot indicator: 1.0 when the horizon is H72, else 0.0."
    )
    assert GATE7_FEATURE_CONTRACT.features[3].derivation == (
        "One-hot indicator: 1.0 when the horizon is D7, else 0.0."
    )
    assert "One-hot indicator" in GATE7_FEATURE_CONTRACT.features[34].derivation
    assert GATE7_FEATURE_CONTRACT.features[33].missingness_handling.startswith(
        "Required source field is absent"
    )
    assert "padding" in GATE7_FEATURE_CONTRACT.features[7].missingness_handling
    assert all(
        feature.construction is Gate7FeatureConstruction.CAMP_ROW
        for feature in GATE7_FEATURE_CONTRACT.features[:7]
    )


def test_available_projection_is_finite_float64_and_preserves_h72_d7_windows() -> None:
    rows = _rows()
    projection = project_gate7_available_fields_v1(rows)
    by_horizon = {row.horizon: (row, index) for index, row in enumerate(rows)}

    assert GATE7_AVAILABLE_FEATURE_INDICES == (0, 1, 2, 3, 4, 5, 6, 25)
    assert GATE7_AVAILABLE_FEATURE_NAMES == tuple(
        GATE7_FEATURE_NAMES[i] for i in (0, 1, 2, 3, 4, 5, 6, 25)
    )
    assert projection.values.shape == (len(rows), 8)
    assert projection.values.dtype == np.dtype(np.float64)
    assert np.isfinite(projection.values).all()

    for horizon, expected_indicator, expected_window in (
        (ForecastHorizon.H72, (1.0, 0.0), (66.0, 78.0)),
        (ForecastHorizon.D7, (0.0, 1.0), (156.0, 180.0)),
    ):
        row, index = by_horizon[horizon]
        np.testing.assert_array_equal(
            projection.values[index, 0:2],
            (row.baseline.force_n_per_kg, row.baseline.net_impulse_m_s),
        )
        np.testing.assert_array_equal(projection.values[index, 2:4], expected_indicator)
        assert projection.values[index, 4] == row.target_time_hours
        np.testing.assert_array_equal(projection.values[index, 5:7], expected_window)
        assert projection.values[index, 7] == 0.0


def test_grouping_keys_are_excluded_and_projection_is_reproducible() -> None:
    row = _rows()[0]
    changed_keys = replace(
        row,
        participant_key="different-participant",
        origin_id="different-origin",
        query_id="different-query",
    )
    first = project_gate7_available_fields_v1((row,))
    repeated = project_gate7_available_fields_v1((row,))
    changed = project_gate7_available_fields_v1((changed_keys,))

    assert not any(
        key in name
        for name in GATE7_FEATURE_NAMES
        for key in ("participant_key", "origin_id", "query_id", "assessment_id", "event_id")
    )
    np.testing.assert_array_equal(first.values, repeated.values)
    np.testing.assert_array_equal(first.values, changed.values)


def test_full_projection_fails_closed_with_specific_missing_authority() -> None:
    rows = _rows()
    attempt = project_gate7_v1(rows)
    blocked_features = {
        name for authority in attempt.missing_authority for name in authority.feature_names
    }
    returned_codes = {authority.code for authority in attempt.missing_authority}
    unavailable_features = {
        feature.name
        for feature in GATE7_FEATURE_CONTRACT.features
        if feature.construction is Gate7FeatureConstruction.MISSING_AUTHORITY
    }

    assert attempt.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
    assert attempt.row_count == len(rows)
    assert attempt.matrix is None
    assert attempt.missing_authority == GATE7_MISSING_AUTHORITY
    assert blocked_features == unavailable_features
    assert all(
        set(feature.missing_authority_codes).issubset(returned_codes)
        for feature in GATE7_FEATURE_CONTRACT.features
        if feature.construction is Gate7FeatureConstruction.MISSING_AUTHORITY
    )
    assert GATE7_FEATURE_NAMES[33] in blocked_features
    assert GATE7_FEATURE_NAMES[38] in blocked_features
    assert any(
        "future measurements" in item.evidence_required for item in attempt.missing_authority
    )


def test_invalid_rows_and_empty_batches_are_handled_deterministically() -> None:
    with pytest.raises(TypeError, match="row 0 must be a CampPredictionRow"):
        project_gate7_v1((object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="iterable of CampPredictionRow"):
        project_gate7_available_fields_v1(None)  # type: ignore[arg-type]

    empty = project_gate7_available_fields_v1(())
    blocked_empty = project_gate7_v1(())
    assert empty.values.shape == (0, 8)
    assert empty.values.dtype == np.dtype(np.float64)
    assert blocked_empty.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
    assert blocked_empty.row_count == 0


def test_public_row_rejects_future_history_instead_of_leaking_it() -> None:
    row = _rows()[0]
    future = AssessmentObservation(
        assessment_id="future-assessment",
        time_from_origin_hours=72.0,
        availability=AssessmentAvailability.UNSCHEDULED,
    )
    with pytest.raises(InformationLeakageError, match="must stop before the index origin"):
        replace(row, assessment_history=(*row.assessment_history, future))


def test_missing_history_values_are_not_imputed_into_a_full_projection() -> None:
    row = _rows()[0]
    unavailable = AssessmentObservation(
        assessment_id="unavailable-assessment",
        time_from_origin_hours=-12.0,
        availability=AssessmentAvailability.SCHEDULED_UNAVAILABLE,
    )
    row_with_missing_history = replace(
        row, assessment_history=(*row.assessment_history, unavailable)
    )
    original_available = project_gate7_available_fields_v1((row,))
    missing_available = project_gate7_available_fields_v1((row_with_missing_history,))
    attempt = project_gate7_v1((row_with_missing_history,))

    np.testing.assert_array_equal(original_available.values, missing_available.values)
    assert attempt.matrix is None
    assert attempt.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY
    assert GATE7_FEATURE_NAMES[7] in {
        name for authority in attempt.missing_authority for name in authority.feature_names
    }


def test_matrix_contract_rejects_invalid_values_and_versions_are_stable() -> None:
    from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
        Gate7AvailableFeatureProjection,
    )

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
    assert GATE7_FEATURE_CONTRACT.expected_shape(0) == (0, 39)
    with pytest.raises(ValueError, match="non-negative"):
        GATE7_FEATURE_CONTRACT.expected_shape(-1)
