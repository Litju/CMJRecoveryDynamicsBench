"""Versioned public feature authority for the recovered Gate7 input schema."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.reproduction.camp_history import CampPredictionRow
from cmj_recovery_dynamics.tasks.preseason_camp_recovery import PRESEASON_CAMP_RECOVERY_TASK

Float64Matrix = NDArray[np.float64]


class Gate7FeatureUnit(StrEnum):
    NEWTON_PER_KILOGRAM = "N/kg"
    METER_PER_SECOND = "m/s"
    METER = "m"
    HOUR = "h"
    MINUTE = "min"
    DIMENSIONLESS = "dimensionless"


class Gate7FeatureConstruction(StrEnum):
    CAMP_ROW_DIRECT = "constructible_from_camp_prediction_row"
    GATE7_PUBLIC_ROW = "constructible_from_gate7_public_feature_row"


class Gate7ProjectionStatus(StrEnum):
    READY_FOR_GATE7_FULL_PROJECTION_REVIEW = "READY_FOR_GATE7_FULL_PROJECTION_REVIEW"
    BLOCKED_ON_EXACT_FEATURE_AUTHORITY = "BLOCKED_ON_EXACT_FEATURE_AUTHORITY"


class Gate7MissingAuthorityCode(StrEnum):
    CAMP_ROW_ASSESSMENT_HISTORY_SHAPE = "camp_row_assessment_history_shape_incompatible"
    CAMP_ROW_HISTORY_EXPOSURE_SHAPE = "camp_row_history_exposure_shape_incompatible"
    CAMP_ROW_KNOWN_PLAN_SHAPE = "camp_row_known_plan_shape_incompatible"
    CAMP_ROW_ROUTINE_ASSESSMENT_ABSENT = "camp_row_routine_assessment_absent"
    CAMP_ROW_VALUE_INVALID = "camp_row_value_invalid"
    ROUTINE_TEMPORAL_AUTHORITY_UNRESOLVED = "routine_temporal_authority_unresolved"
    ROUTINE_ASSESSMENT_POST_ORIGIN = "routine_assessment_post_origin"
    ROUTINE_ORIGIN_MISMATCH = "routine_origin_mismatch"
    ROUTINE_SOURCE_MISMATCH = "routine_source_mismatch"


class Gate7ProjectionInputCode(StrEnum):
    ASSESSMENT_HISTORY_COUNT = "assessment_history_count"
    HISTORY_EXPOSURE_COUNT = "history_exposure_count"
    KNOWN_PLAN_COUNT = "known_plan_count"
    INVALID_OR_MISSING_FEATURE = "invalid_or_missing_feature"
    DURATION_COMPONENT_INVALID = "duration_component_invalid"
    FUTURE_ASSESSMENT_HISTORY = "future_assessment_history"
    FUTURE_EXPOSURE_HISTORY = "future_exposure_history"
    INVALID_INDEX_EXPOSURE_TIME = "invalid_index_exposure_time"
    UNKNOWN_OR_FUTURE_PLAN = "unknown_or_future_plan"
    ROUTINE_TEMPORAL_AUTHORITY = "routine_temporal_authority"


class Gate7RoutineState(StrEnum):
    FIELD_STRUCTURALLY_ABSENT = "FIELD_STRUCTURALLY_ABSENT"
    OBSERVED_MASKED = "OBSERVED_MASKED"
    SCHEDULED_UNAVAILABLE = "SCHEDULED_UNAVAILABLE"
    TRIAL_INVALID = "TRIAL_INVALID"
    UNSCHEDULED = "UNSCHEDULED"


class Gate7RoutineTemporalAuthority(StrEnum):
    ORIGIN_KEYED_PUBLIC_STATE = "origin_keyed_public_state"
    UNRESOLVED = "unresolved"
    POST_ORIGIN = "post_origin"


@dataclass(frozen=True, slots=True)
class Gate7FeatureDefinition:
    index: int
    name: str
    dtype: str
    unit: Gate7FeatureUnit
    input_field: str
    derivation: str
    temporal_availability: str
    missingness_handling: str
    construction: Gate7FeatureConstruction

    def __post_init__(self) -> None:
        if self.index < 0 or not all(
            (
                self.name,
                self.dtype,
                self.input_field,
                self.derivation,
                self.temporal_availability,
                self.missingness_handling,
            )
        ):
            raise ValueError("Gate7 feature definitions require complete non-empty metadata")
        if self.dtype != "float64":
            raise ValueError("the public Gate7 projection matrix uses float64 columns")


@dataclass(frozen=True, slots=True)
class Gate7FeatureContract:
    version: str
    model_identity: str
    source_evidence: tuple[str, ...]
    features: tuple[Gate7FeatureDefinition, ...]
    model_input_preprocessing: str

    def __post_init__(self) -> None:
        if not self.version or not self.model_identity or not self.source_evidence:
            raise ValueError("Gate7 contract needs a version, model identity, and evidence")
        if not self.features or any(not source for source in self.source_evidence):
            raise ValueError("Gate7 contract needs features and non-empty source evidence")
        if tuple(feature.index for feature in self.features) != tuple(range(len(self.features))):
            raise ValueError("Gate7 feature indices must be contiguous and ordered")
        if len({feature.name for feature in self.features}) != len(self.features):
            raise ValueError("Gate7 feature names must be unique")
        if not self.model_input_preprocessing:
            raise ValueError("Gate7 preprocessing authority must be recorded")

    @property
    def feature_count(self) -> int:
        return len(self.features)

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(feature.name for feature in self.features)

    def expected_shape(self, row_count: int) -> tuple[int, int]:
        if row_count < 0:
            raise ValueError("row count must be non-negative")
        return row_count, self.feature_count


@dataclass(frozen=True, slots=True)
class Gate7MissingAuthority:
    code: Gate7MissingAuthorityCode
    feature_names: tuple[str, ...]
    evidence_required: str

    def __post_init__(self) -> None:
        if not self.feature_names or not self.evidence_required:
            raise ValueError("missing-authority records need features and required evidence")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("missing-authority feature names must be unique")


class Gate7ProjectionInputError(ValueError):
    def __init__(
        self,
        code: Gate7ProjectionInputCode,
        message: str,
        feature_names: tuple[str, ...] = (),
    ) -> None:
        self.code = code
        self.feature_names = feature_names
        super().__init__(f"{code.value}: {message}")


@dataclass(frozen=True, slots=True)
class Gate7HistoryAssessment:
    time_from_origin_hours: float
    relative_mean_concentric_force: float | None
    relative_concentric_net_impulse: float | None
    depth_m: float | None
    validity_state: str | None = None


@dataclass(frozen=True, slots=True)
class Gate7ExposureFeature:
    time_from_origin_hours: float
    duration_minutes: float | None


@dataclass(frozen=True, slots=True)
class Gate7PlanFeature:
    time_from_origin_hours: float
    duration_minutes: float | None
    known_at_origin: bool = True

    def __post_init__(self) -> None:
        if type(self.known_at_origin) is not bool:
            raise TypeError("known_plan.known_at_origin must be boolean")


@dataclass(frozen=True, slots=True)
class Gate7RoutineAssessment:
    scheduled: bool
    availability_state: Gate7RoutineState
    temporal_authority: Gate7RoutineTemporalAuthority
    origin_id: str | None = None
    source_sha256: str | None = None
    available_at_origin_hours: float | None = None

    def __post_init__(self) -> None:
        if type(self.scheduled) is not bool:
            raise TypeError("routine assessment scheduled must be boolean")
        state: object = self.availability_state
        if type(state) is not Gate7RoutineState:
            raise TypeError("routine assessment availability_state is not registered")
        temporal_authority: object = self.temporal_authority
        if type(temporal_authority) is not Gate7RoutineTemporalAuthority:
            raise TypeError("routine assessment temporal authority is not registered")
        if self.scheduled is (self.availability_state is Gate7RoutineState.UNSCHEDULED):
            raise ValueError("scheduled must be false exactly for UNSCHEDULED routine states")


@dataclass(frozen=True, slots=True)
class Gate7RoutineSource:
    """Immutable origin records verified against an externally trusted SHA-256.

    The application must pin the digest from its authoritative ingestion process,
    independently of prediction requests, and reuse this source across calls.
    A matching digest proves byte identity, not that a caller's data are truthful.
    """

    payload: bytes
    expected_sha256: str

    def __post_init__(self) -> None:
        if type(self.payload) is not bytes:
            raise TypeError("routine source payload must be immutable bytes")
        if hashlib.sha256(self.payload).hexdigest() != self.expected_sha256:
            raise ValueError("routine source SHA-256 mismatch")
        self.records()

    def records(self) -> tuple[Gate7RoutineAssessment, ...]:
        # Array records avoid ambiguous duplicate JSON object keys.
        data: object = json.loads(self.payload)
        if not isinstance(data, list):
            raise ValueError("routine source must be an array of origin records")
        records: list[Gate7RoutineAssessment] = []
        for raw in cast(list[object], data):
            if not isinstance(raw, list) or len(cast(list[object], raw)) != 4:
                raise ValueError("routine source records require origin, scheduled, state, time")
            origin, scheduled, state, time = cast(list[object], raw)
            if not isinstance(origin, str) or not origin.strip():
                raise ValueError("routine source requires a non-empty origin_id")
            if type(scheduled) is not bool or not isinstance(state, str):
                raise ValueError("routine source requires boolean scheduled and registered state")
            if type(time) not in (int, float) or not np.isfinite(cast(float, time)):
                raise ValueError("routine source availability time must be finite numeric hours")
            records.append(
                Gate7RoutineAssessment(
                    scheduled,
                    Gate7RoutineState(state),
                    Gate7RoutineTemporalAuthority.ORIGIN_KEYED_PUBLIC_STATE,
                    origin,
                    self.expected_sha256,
                    float(cast(float, time)),
                )
            )
        if len({record.origin_id for record in records}) != len(records):
            raise ValueError("routine source requires exactly one record per origin")
        return tuple(records)


@dataclass(frozen=True, slots=True)
class Gate7PublicFeatureRow:
    """Exact public input surface consumed by the recovered Gate7 extractor."""

    baseline_relative_mean_concentric_force: float
    baseline_relative_concentric_net_impulse: float
    horizon: ForecastHorizon
    target_time_hours: float
    target_window_hours: tuple[float, float]
    history_assessments: tuple[Gate7HistoryAssessment, ...]
    history_exposures: tuple[Gate7ExposureFeature, ...]
    index_exposure: Gate7ExposureFeature
    known_plan: tuple[Gate7PlanFeature, ...]
    routine_assessment: Gate7RoutineAssessment


@dataclass(frozen=True, slots=True)
class Gate7CampPredictionInput:
    row: CampPredictionRow
    routine_assessment: Gate7RoutineAssessment | None = None

    def __post_init__(self) -> None:
        row: object = self.row
        if type(row) is not CampPredictionRow:
            raise TypeError("row must be a CampPredictionRow")
        routine_assessment: object = self.routine_assessment
        if (
            routine_assessment is not None
            and type(routine_assessment) is not Gate7RoutineAssessment
        ):
            raise TypeError("routine_assessment must be a Gate7RoutineAssessment")


@dataclass(frozen=True, slots=True)
class Gate7AvailableFeatureProjection:
    """The source-closed columns only; this is not a model-ready 39-column matrix."""

    feature_names: tuple[str, ...]
    values: Float64Matrix

    def __post_init__(self) -> None:
        if self.feature_names != GATE7_AVAILABLE_FEATURE_NAMES:
            raise ValueError("available Gate7 feature names must follow their source order")
        if self.values.ndim != 2:
            raise ValueError("Gate7 projection matrix must be two-dimensional")
        object.__setattr__(
            self,
            "values",
            _validate_matrix(
                self.values, row_count=self.values.shape[0], column_count=len(self.feature_names)
            ),
        )


@dataclass(frozen=True, slots=True)
class Gate7ProjectionAttempt:
    status: Gate7ProjectionStatus
    row_count: int
    matrix: Float64Matrix | None
    missing_authority: tuple[Gate7MissingAuthority, ...]

    def __post_init__(self) -> None:
        if self.row_count < 0:
            raise ValueError("row count must be non-negative")
        if self.status is Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY:
            if self.matrix is not None or not self.missing_authority:
                raise ValueError("a blocked projection must return authority gaps and no matrix")
        elif self.matrix is None or self.missing_authority:
            raise ValueError("a ready projection needs a matrix and no authority gaps")
        else:
            object.__setattr__(
                self,
                "matrix",
                _validate_matrix(
                    self.matrix,
                    row_count=self.row_count,
                    column_count=GATE7_FEATURE_CONTRACT.feature_count,
                ),
            )


def _unit(name: str) -> Gate7FeatureUnit:
    if name.endswith("relative_mean_concentric_force"):
        return Gate7FeatureUnit.NEWTON_PER_KILOGRAM
    if name.endswith("relative_concentric_net_impulse"):
        return Gate7FeatureUnit.METER_PER_SECOND
    if name.endswith("depth_m"):
        return Gate7FeatureUnit.METER
    if "hours" in name or name.endswith("time_from_origin_hours"):
        return Gate7FeatureUnit.HOUR
    if name.endswith("duration_minutes"):
        return Gate7FeatureUnit.MINUTE
    return Gate7FeatureUnit.DIMENSIONLESS


_HISTORY_ASSESSMENT_NAMES = tuple(
    f"public_features.history_assessments[{slot}].{field}"
    for slot in range(4)
    for field in (
        "time_from_origin_hours",
        "relative_mean_concentric_force",
        "relative_concentric_net_impulse",
        "depth_m",
    )
)
_KNOWN_PLAN_NAMES = tuple(
    f"public_features.known_plan[{slot}].{field}"
    for slot in range(3)
    for field in ("time_from_origin_hours", "duration_minutes")
)

GATE7_FEATURE_NAMES = (
    "baseline.relative_mean_concentric_force",
    "baseline.relative_concentric_net_impulse",
    "horizon.H72",
    "horizon.D7",
    "target_time_hours",
    "target_window_hours.low",
    "target_window_hours.high",
    *_HISTORY_ASSESSMENT_NAMES,
    "public_features.history_exposures[0].time_from_origin_hours",
    "public_features.history_exposures[0].duration_minutes",
    "public_features.index_exposure.time_from_origin_hours",
    "public_features.index_exposure.duration_minutes",
    *_KNOWN_PLAN_NAMES,
    "public_features.routine_assessment.scheduled",
    "public_features.routine_assessment.availability_state.FIELD_STRUCTURALLY_ABSENT",
    "public_features.routine_assessment.availability_state.OBSERVED_MASKED",
    "public_features.routine_assessment.availability_state.SCHEDULED_UNAVAILABLE",
    "public_features.routine_assessment.availability_state.TRIAL_INVALID",
    "public_features.routine_assessment.availability_state.UNSCHEDULED",
)
GATE7_FEATURE_UNITS = tuple(_unit(name) for name in GATE7_FEATURE_NAMES)
GATE7_AVAILABLE_FEATURE_INDICES = (0, 1, 2, 3, 4, 5, 6, 25)
GATE7_AVAILABLE_FEATURE_NAMES = tuple(
    GATE7_FEATURE_NAMES[index] for index in GATE7_AVAILABLE_FEATURE_INDICES
)
_HORIZON_WINDOWS = {
    window.horizon: (float(window.start_offset_hours), float(window.end_offset_hours))
    for window in PRESEASON_CAMP_RECOVERY_TASK.horizon_windows
}
_ROUTINE_STATES = (
    "FIELD_STRUCTURALLY_ABSENT",
    "OBSERVED_MASKED",
    "SCHEDULED_UNAVAILABLE",
    "TRIAL_INVALID",
    "UNSCHEDULED",
)


def _feature_definition(index: int, name: str) -> Gate7FeatureDefinition:
    construction = (
        Gate7FeatureConstruction.CAMP_ROW_DIRECT
        if index in (*range(7), 25)
        else Gate7FeatureConstruction.GATE7_PUBLIC_ROW
    )
    if index == 0:
        input_field = "baseline.relative_mean_concentric_force"
        derivation = "Copy the finite baseline relative mean concentric force in N/kg."
        temporal = "Baseline is measured before the prediction origin."
        missingness = "Required finite numeric value; no imputation."
    elif index == 1:
        input_field = "baseline.relative_concentric_net_impulse"
        derivation = "Copy the finite baseline relative concentric net impulse in m/s."
        temporal = "Baseline is measured before the prediction origin."
        missingness = "Required finite numeric value; no imputation."
    elif index in (2, 3):
        horizon = "H72" if index == 2 else "D7"
        input_field = "horizon"
        derivation = f"One-hot indicator: 1.0 when horizon is {horizon}, else 0.0."
        temporal = "Forecast horizon is fixed at the prediction origin."
        missingness = "Required registered enum; exactly one horizon indicator is 1.0."
    elif index == 4:
        input_field = "target_time_hours"
        derivation = "Copy the finite forecast query time in hours."
        temporal = "Query time is registered at the prediction origin."
        missingness = "Required finite numeric value; no imputation."
    elif index in (5, 6):
        edge = "low" if index == 5 else "high"
        input_field = f"target_window_hours.{edge}"
        derivation = f"Copy the registered {edge} boundary in hours."
        temporal = "Forecast window is fixed at the prediction origin."
        missingness = "Required finite task-contract value; no imputation."
    elif 7 <= index <= 22:
        input_field = name
        derivation = (
            "Stable sort all history assessments by ascending time_from_origin_hours; require "
            "exactly four; copy the named finite field from its slot."
        )
        temporal = "History assessments are pre-origin records."
        missingness = (
            "No padding or imputation. The extractor does not inspect validity_state; absent, "
            "null, or non-finite values fail numeric conversion."
        )
    elif 23 <= index <= 24:
        input_field = name
        derivation = (
            "Stable sort history exposures by ascending time_from_origin_hours; require exactly "
            "one; copy the named finite field."
        )
        temporal = "History exposure is a pre-origin record."
        missingness = "No padding or imputation; duration is copied in minutes."
    elif index == 25:
        input_field = name
        derivation = "Copy the index exposure time; the public row contract requires 0 hours."
        temporal = "Index exposure occurs at the prediction origin."
        missingness = "Required finite numeric value; no imputation."
    elif index == 26:
        input_field = name
        derivation = "Copy duration_minutes directly in minutes; no unit conversion."
        temporal = "Index exposure occurs at the prediction origin."
        missingness = "Required finite numeric value; no imputation."
    elif 27 <= index <= 32:
        input_field = name
        derivation = (
            "Stable sort the query-specific known plan by ascending time_from_origin_hours; "
            "require two or three records; copy finite fields by slot."
        )
        temporal = "Plan events are known at origin and do not exceed the query time."
        missingness = (
            "If there are two records, pad only slot 2 time and duration with 0.0; other missing "
            "or non-finite values fail. Durations are copied in minutes."
        )
    elif index == 33:
        input_field = name
        derivation = "Copy the source scheduled boolean as a float64 1.0 or 0.0."
        temporal = (
            "L05-R01 public generation assigns one origin-keyed state and copies it unchanged to "
            "the horizon queries; the state is independent of future targets."
        )
        missingness = "Required boolean value; no default or inference from assessment rows."
    else:
        state = _ROUTINE_STATES[index - 34]
        input_field = name.rsplit(".", maxsplit=1)[0]
        derivation = f"One-hot indicator for availability_state == {state}."
        temporal = (
            "L05-R01 public generation assigns one origin-keyed state and copies it unchanged to "
            "the horizon queries; the state is independent of future targets."
        )
        missingness = "State must be one of the five registered categories."

    return Gate7FeatureDefinition(
        index=index,
        name=name,
        dtype="float64",
        unit=GATE7_FEATURE_UNITS[index],
        input_field=input_field,
        derivation=derivation,
        temporal_availability=temporal,
        missingness_handling=missingness,
        construction=construction,
    )


GATE7_FEATURE_CONTRACT = Gate7FeatureContract(
    version="gate7_feature_projection_v1",
    model_identity="gate7_m0_candidate",
    source_evidence=(
        "Recovered Gate7 common.feature_vector and feature_matrix call chain.",
        "Recovered Gate7 M0 model Preprocessor and train-only preprocessing rules.",
        "L05-R01 final public generator and Gate6 public surface and target contracts.",
        "Public CampPredictionRow and preseason camp task contracts.",
    ),
    features=tuple(
        _feature_definition(index, name) for index, name in enumerate(GATE7_FEATURE_NAMES)
    ),
    model_input_preprocessing=(
        "The original M0 fits raw feature means and sample standard deviations (ddof=1) on "
        "training rows only, replaces zero scales with 1.0, applies (x - mean) / scale, then "
        "casts model tensors to float32. This projection returns raw float64 values; fitted "
        "means and scales are not included."
    ),
)


GATE7_CAMP_ROW_GAPS = (
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.CAMP_ROW_ASSESSMENT_HISTORY_SHAPE,
        GATE7_FEATURE_NAMES[7:23],
        "Supply exactly four finite pre-origin assessment summaries in the Gate7 public field "
        "shape; current CampPredictionRow permits variable-length trial observations.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.CAMP_ROW_HISTORY_EXPOSURE_SHAPE,
        GATE7_FEATURE_NAMES[23:25],
        "Supply exactly one finite pre-origin history exposure with a public duration_minutes "
        "component; current CampPredictionRow permits zero or multiple events.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.CAMP_ROW_ROUTINE_ASSESSMENT_ABSENT,
        GATE7_FEATURE_NAMES[33:39],
        "Supply the source scheduled boolean and five-state availability value as an explicit "
        "origin-keyed public input; do not derive it from assessment_history.",
    ),
)

GATE7_MISSING_AUTHORITY = GATE7_CAMP_ROW_GAPS


def _collect_rows(rows: Iterable[object]) -> tuple[CampPredictionRow, ...]:
    try:
        values = tuple(rows)
    except TypeError as error:
        raise TypeError("rows must be an iterable of CampPredictionRow values") from error
    row_values: list[CampPredictionRow] = []
    for index, row in enumerate(values):
        if not isinstance(row, CampPredictionRow):
            raise TypeError(f"row {index} must be a CampPredictionRow")
        row_values.append(row)
    return tuple(row_values)


def _collect_public_rows(rows: Iterable[object]) -> tuple[Gate7PublicFeatureRow, ...]:
    try:
        values = tuple(rows)
    except TypeError as error:
        raise TypeError("rows must be an iterable of Gate7PublicFeatureRow values") from error
    row_values: list[Gate7PublicFeatureRow] = []
    for index, row in enumerate(values):
        if not isinstance(row, Gate7PublicFeatureRow):
            raise TypeError(f"row {index} must be a Gate7PublicFeatureRow")
        row_values.append(row)
    return tuple(row_values)


def _validate_matrix(values: object, *, row_count: int, column_count: int) -> Float64Matrix:
    if not isinstance(values, np.ndarray):
        raise TypeError("Gate7 projection values must be a float64 NumPy matrix")
    matrix = cast(Float64Matrix, values)
    if matrix.dtype != np.dtype(np.float64):
        raise TypeError("Gate7 projection values must be a float64 NumPy matrix")
    if matrix.shape != (row_count, column_count):
        raise ValueError(f"Gate7 projection matrix must have shape {(row_count, column_count)}")
    if not np.isfinite(matrix).all():
        raise ValueError("Gate7 projection matrix values must all be finite")
    frozen = matrix.copy()
    frozen.setflags(write=False)
    return frozen


def _feature_float(value: object, feature_name: str) -> float:
    try:
        result = float(cast(Any, value))
    except (TypeError, ValueError, OverflowError) as error:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE,
            f"{feature_name} is missing or non-numeric",
            (feature_name,),
        ) from error
    if not np.isfinite(result):
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE,
            f"{feature_name} is non-finite",
            (feature_name,),
        )
    return result


def _source_feature_vector(row: Gate7PublicFeatureRow) -> Float64Matrix:
    horizon: object = row.horizon
    if type(horizon) is not ForecastHorizon:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE,
            "horizon is not registered",
            GATE7_FEATURE_NAMES[2:4],
        )
    values: list[float] = []
    names: list[str] = []

    def add(name: str, value: object) -> None:
        names.append(name)
        values.append(_feature_float(value, name))

    add(GATE7_FEATURE_NAMES[0], row.baseline_relative_mean_concentric_force)
    add(GATE7_FEATURE_NAMES[1], row.baseline_relative_concentric_net_impulse)
    add(GATE7_FEATURE_NAMES[2], row.horizon is ForecastHorizon.H72)
    add(GATE7_FEATURE_NAMES[3], row.horizon is ForecastHorizon.D7)
    add(GATE7_FEATURE_NAMES[4], row.target_time_hours)
    if len(row.target_window_hours) != 2:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE,
            "target_window_hours must contain low and high values",
            GATE7_FEATURE_NAMES[5:7],
        )
    add(GATE7_FEATURE_NAMES[5], row.target_window_hours[0])
    add(GATE7_FEATURE_NAMES[6], row.target_window_hours[1])

    history = sorted(
        row.history_assessments,
        key=lambda item: _feature_float(item.time_from_origin_hours, GATE7_FEATURE_NAMES[7]),
    )
    if len(history) != 4:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.ASSESSMENT_HISTORY_COUNT,
            "the original extractor requires exactly four history assessments",
            GATE7_FEATURE_NAMES[7:23],
        )
    for index, item in enumerate(history):
        start = 7 + index * 4
        add(GATE7_FEATURE_NAMES[start], item.time_from_origin_hours)
        add(GATE7_FEATURE_NAMES[start + 1], item.relative_mean_concentric_force)
        add(GATE7_FEATURE_NAMES[start + 2], item.relative_concentric_net_impulse)
        add(GATE7_FEATURE_NAMES[start + 3], item.depth_m)

    exposures = sorted(
        row.history_exposures,
        key=lambda item: _feature_float(item.time_from_origin_hours, GATE7_FEATURE_NAMES[23]),
    )
    if len(exposures) != 1:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.HISTORY_EXPOSURE_COUNT,
            "the original extractor requires exactly one history exposure",
            GATE7_FEATURE_NAMES[23:25],
        )
    add(GATE7_FEATURE_NAMES[23], exposures[0].time_from_origin_hours)
    add(GATE7_FEATURE_NAMES[24], exposures[0].duration_minutes)
    add(GATE7_FEATURE_NAMES[25], row.index_exposure.time_from_origin_hours)
    add(GATE7_FEATURE_NAMES[26], row.index_exposure.duration_minutes)

    plan = sorted(
        row.known_plan,
        key=lambda item: _feature_float(item.time_from_origin_hours, GATE7_FEATURE_NAMES[27]),
    )
    if len(plan) not in (2, 3):
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.KNOWN_PLAN_COUNT,
            "the original extractor requires two or three query-specific plan records",
            GATE7_FEATURE_NAMES[27:33],
        )
    for index in range(3):
        item = plan[index] if index < len(plan) else None
        start = 27 + index * 2
        add(GATE7_FEATURE_NAMES[start], 0.0 if item is None else item.time_from_origin_hours)
        add(GATE7_FEATURE_NAMES[start + 1], 0.0 if item is None else item.duration_minutes)

    routine = row.routine_assessment
    routine_state: object = routine.availability_state
    if type(routine_state) is not Gate7RoutineState:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.INVALID_OR_MISSING_FEATURE,
            "routine assessment state is outside the frozen five-state category set",
            GATE7_FEATURE_NAMES[33:39],
        )
    add(GATE7_FEATURE_NAMES[33], routine.scheduled)
    for offset, state in enumerate(_ROUTINE_STATES):
        add(GATE7_FEATURE_NAMES[34 + offset], routine.availability_state.value == state)

    if tuple(names) != GATE7_FEATURE_NAMES:
        raise AssertionError("Gate7 source feature order drifted")
    return np.asarray(values, dtype=np.float64)


def _duration_minutes(components: tuple[object, ...], feature_name: str) -> float:
    """Prospective components must be usable; historical rows already carry raw minutes."""
    matches = tuple(
        component
        for component in components
        if getattr(component, "name", None) == "duration_minutes"
    )
    if len(matches) != 1:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.DURATION_COMPONENT_INVALID,
            f"{feature_name} requires exactly one duration_minutes component",
            (feature_name,),
        )
    component = matches[0]
    if (
        getattr(component, "units", None) != "minutes"
        or getattr(component, "observed", None) is not True
        or getattr(component, "day_mask", None) is not True
        or getattr(component, "event_mask", None) is not True
    ):
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.DURATION_COMPONENT_INVALID,
            f"{feature_name} requires an observed, unmasked minutes component",
            (feature_name,),
        )
    return _feature_float(getattr(component, "value", None), feature_name)


def _public_row_from_camp_input(value: Gate7CampPredictionInput) -> Gate7PublicFeatureRow:
    row = value.row
    if value.routine_assessment is None:
        raise Gate7ProjectionInputError(
            Gate7ProjectionInputCode.ROUTINE_TEMPORAL_AUTHORITY,
            "CampPredictionRow has no routine_assessment; supply the source public state",
            GATE7_FEATURE_NAMES[33:39],
        )
    assessments = tuple(
        Gate7HistoryAssessment(
            item.time_from_origin_hours,
            item.force_summary_n_per_kg,
            item.impulse_summary_m_s,
            item.depth_summary_m,
            item.availability.value,
        )
        for item in row.assessment_history
    )
    exposures = tuple(
        Gate7ExposureFeature(
            item.time_from_origin_hours,
            _duration_minutes(item.components, GATE7_FEATURE_NAMES[24]),
        )
        for item in row.exposure_history
    )
    index = Gate7ExposureFeature(
        row.index_exposure.time_from_origin_hours,
        _duration_minutes(row.index_exposure.components, GATE7_FEATURE_NAMES[26]),
    )
    plan = (
        Gate7PlanFeature(index.time_from_origin_hours, index.duration_minutes),
        *(
            Gate7PlanFeature(
                item.time_from_origin_hours,
                _duration_minutes(item.components, GATE7_FEATURE_NAMES[28]),
                item.known_at_origin,
            )
            for item in row.known_plan
        ),
    )
    return Gate7PublicFeatureRow(
        baseline_relative_mean_concentric_force=row.baseline.force_n_per_kg,
        baseline_relative_concentric_net_impulse=row.baseline.net_impulse_m_s,
        horizon=row.horizon,
        target_time_hours=row.target_time_hours,
        target_window_hours=_HORIZON_WINDOWS[row.horizon],
        history_assessments=assessments,
        history_exposures=exposures,
        index_exposure=index,
        known_plan=plan,
        routine_assessment=value.routine_assessment,
    )


def _prospective_row_authority(row: Gate7PublicFeatureRow) -> tuple[Gate7MissingAuthority, ...]:
    gaps: list[Gate7MissingAuthority] = []
    horizon: object = row.horizon
    if type(horizon) is not ForecastHorizon or horizon not in _HORIZON_WINDOWS:
        gaps.append(
            Gate7MissingAuthority(
                Gate7MissingAuthorityCode.CAMP_ROW_VALUE_INVALID,
                GATE7_FEATURE_NAMES[2:7],
                "Gate7 rows require a registered H72 or D7 horizon and its forecast window.",
            )
        )
    else:
        low, high = _HORIZON_WINDOWS[row.horizon]
        if row.target_window_hours != (low, high) or not low <= row.target_time_hours <= high:
            gaps.append(
                Gate7MissingAuthority(
                    Gate7MissingAuthorityCode.CAMP_ROW_VALUE_INVALID,
                    GATE7_FEATURE_NAMES[2:7],
                    "Horizon, target time, and target window must match the registered "
                    "task contract.",
                )
            )
    if any(item.time_from_origin_hours >= 0 for item in row.history_assessments):
        gaps.append(
            Gate7MissingAuthority(
                Gate7MissingAuthorityCode.CAMP_ROW_ASSESSMENT_HISTORY_SHAPE,
                GATE7_FEATURE_NAMES[7:23],
                "Assessment history must end before the prediction origin.",
            )
        )
    if any(item.time_from_origin_hours >= 0 for item in row.history_exposures):
        gaps.append(
            Gate7MissingAuthority(
                Gate7MissingAuthorityCode.CAMP_ROW_HISTORY_EXPOSURE_SHAPE,
                GATE7_FEATURE_NAMES[23:25],
                "History exposures must end before the prediction origin.",
            )
        )
    if row.index_exposure.time_from_origin_hours != 0.0:
        gaps.append(
            Gate7MissingAuthority(
                Gate7MissingAuthorityCode.CAMP_ROW_VALUE_INVALID,
                GATE7_FEATURE_NAMES[25:27],
                "Index exposure must occur at the prediction origin.",
            )
        )
    if any(
        not item.known_at_origin
        or item.time_from_origin_hours < 0
        or item.time_from_origin_hours > row.target_time_hours
        for item in row.known_plan
    ):
        gaps.append(
            Gate7MissingAuthority(
                Gate7MissingAuthorityCode.CAMP_ROW_KNOWN_PLAN_SHAPE,
                GATE7_FEATURE_NAMES[27:33],
                "Every plan feature must have been known at origin and occur no later than "
                "the query.",
            )
        )
    return tuple(gaps)


def _camp_row_gap(error: Gate7ProjectionInputError) -> Gate7MissingAuthority:
    if error.code is Gate7ProjectionInputCode.ASSESSMENT_HISTORY_COUNT:
        code = Gate7MissingAuthorityCode.CAMP_ROW_ASSESSMENT_HISTORY_SHAPE
        names = GATE7_FEATURE_NAMES[7:23]
    elif error.code is Gate7ProjectionInputCode.HISTORY_EXPOSURE_COUNT:
        code = Gate7MissingAuthorityCode.CAMP_ROW_HISTORY_EXPOSURE_SHAPE
        names = GATE7_FEATURE_NAMES[23:25]
    elif error.code is Gate7ProjectionInputCode.KNOWN_PLAN_COUNT:
        code = Gate7MissingAuthorityCode.CAMP_ROW_KNOWN_PLAN_SHAPE
        names = GATE7_FEATURE_NAMES[27:33]
    elif error.code is Gate7ProjectionInputCode.ROUTINE_TEMPORAL_AUTHORITY:
        code = Gate7MissingAuthorityCode.CAMP_ROW_ROUTINE_ASSESSMENT_ABSENT
        names = GATE7_FEATURE_NAMES[33:39]
    else:
        code = Gate7MissingAuthorityCode.CAMP_ROW_VALUE_INVALID
        names = error.feature_names or GATE7_FEATURE_NAMES
    return Gate7MissingAuthority(code, names, str(error))


def project_gate7_available_fields_v1(
    rows: Iterable[CampPredictionRow],
) -> Gate7AvailableFeatureProjection:
    """Project only the eight source-closed fields; never use grouping keys."""
    row_values = _collect_rows(rows)
    projected = tuple(
        (
            row.baseline.force_n_per_kg,
            row.baseline.net_impulse_m_s,
            float(row.horizon is ForecastHorizon.H72),
            float(row.horizon is ForecastHorizon.D7),
            row.target_time_hours,
            *_HORIZON_WINDOWS[row.horizon],
            row.index_exposure.time_from_origin_hours,
        )
        for row in row_values
    )
    matrix = np.asarray(projected, dtype=np.float64).reshape(
        len(row_values), len(GATE7_AVAILABLE_FEATURE_NAMES)
    )
    return Gate7AvailableFeatureProjection(GATE7_AVAILABLE_FEATURE_NAMES, matrix)


def project_gate7_v1(
    inputs: Iterable[object],
    *,
    routine_source: Gate7RoutineSource | None = None,
) -> Gate7ProjectionAttempt:
    """Project with an application-pinned origin source, shared across calls.

    No global registry is inferred: replacing the trusted source is an application
    authority decision. Request-supplied enums or hashes alone grant no authority.
    """
    try:
        input_values = tuple(inputs)
    except TypeError as error:
        raise TypeError("inputs must be an iterable of Gate7CampPredictionInput values") from error
    camp_inputs: list[Gate7CampPredictionInput] = []
    for index, item in enumerate(input_values):
        if not isinstance(item, Gate7CampPredictionInput):
            raise TypeError(f"input {index} must be a Gate7CampPredictionInput")
        camp_inputs.append(item)

    records = (
        {}
        if routine_source is None
        else {record.origin_id: record for record in routine_source.records()}
    )
    vectors: list[Float64Matrix] = []
    for item in camp_inputs:
        try:
            row = _public_row_from_camp_input(item)
        except Gate7ProjectionInputError as error:
            missing = (_camp_row_gap(error),)
            return Gate7ProjectionAttempt(
                Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY,
                len(input_values),
                None,
                missing,
            )
        routine = item.routine_assessment
        assert routine is not None
        authority_code: Gate7MissingAuthorityCode | None = None
        if routine.temporal_authority is Gate7RoutineTemporalAuthority.POST_ORIGIN or (
            routine.available_at_origin_hours is not None and routine.available_at_origin_hours > 0
        ):
            authority_code = Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_POST_ORIGIN
        elif routine.origin_id != item.row.origin_id:
            authority_code = Gate7MissingAuthorityCode.ROUTINE_ORIGIN_MISMATCH
        elif routine.temporal_authority is Gate7RoutineTemporalAuthority.UNRESOLVED:
            authority_code = Gate7MissingAuthorityCode.ROUTINE_TEMPORAL_AUTHORITY_UNRESOLVED
        elif routine_source is None or records.get(item.row.origin_id) != routine:
            authority_code = Gate7MissingAuthorityCode.ROUTINE_SOURCE_MISMATCH
        if authority_code is not None:
            return Gate7ProjectionAttempt(
                Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY,
                len(input_values),
                None,
                (
                    Gate7MissingAuthority(
                        authority_code,
                        GATE7_FEATURE_NAMES[33:39],
                        "Routine metadata must match the prediction origin and its unique record "
                        "in the application-pinned source, available no later than origin.",
                    ),
                ),
            )
        temporal_gaps = _prospective_row_authority(row)
        if temporal_gaps:
            return Gate7ProjectionAttempt(
                Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY,
                len(input_values),
                None,
                temporal_gaps,
            )
        try:
            vectors.append(_source_feature_vector(row))
        except Gate7ProjectionInputError as error:
            missing = (_camp_row_gap(error),)
            return Gate7ProjectionAttempt(
                Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY,
                len(input_values),
                None,
                missing,
            )

    matrix = (
        np.asarray(vectors, dtype=np.float64)
        if vectors
        else np.empty((0, GATE7_FEATURE_CONTRACT.feature_count), dtype=np.float64)
    )
    matrix = _validate_matrix(
        matrix,
        row_count=len(input_values),
        column_count=GATE7_FEATURE_CONTRACT.feature_count,
    )
    return Gate7ProjectionAttempt(
        Gate7ProjectionStatus.READY_FOR_GATE7_FULL_PROJECTION_REVIEW,
        len(input_values),
        matrix,
        (),
    )


def project_gate7_historical_v1(
    rows: Iterable[Gate7PublicFeatureRow],
) -> Float64Matrix:
    """Faithfully reproduce the recovered raw extractor, with no temporal filtering."""
    row_values = _collect_public_rows(rows)
    vectors = tuple(_source_feature_vector(row) for row in row_values)
    matrix = (
        np.asarray(vectors, dtype=np.float64)
        if vectors
        else np.empty((0, GATE7_FEATURE_CONTRACT.feature_count), dtype=np.float64)
    )
    return _validate_matrix(
        matrix,
        row_count=len(row_values),
        column_count=GATE7_FEATURE_CONTRACT.feature_count,
    )


# Source identities are bound privately to this opaque authority, never published.
GATE7_HISTORY_SOURCE_AUTHORITY_V1 = "RES-546-M3-INPUT-AUTHORITY-01"
GATE7_HISTORY_SCHEMA_V1 = "gate7_history_projection_v1"
GATE7_HISTORY_FEATURE_NAMES = (
    "time_from_origin_hours",
    "relative_mean_concentric_force",
    "relative_concentric_net_impulse",
    "depth_m",
)


def project_gate7_history_v1(rows: Iterable[CampPredictionRow]) -> Float64Matrix:
    """Unscaled float64 (N,4,4) history from authorized typed observations.

    Columns are hours, N/kg, m/s, m; tokens sort oldest to latest. All four
    assessments must be valid and strictly pre-origin. There is no mask, padding
    or imputation. Fitted train-only statistics belong to the pinned predictor.
    This reads observations directly, never reconstructs history from raw features.
    """
    values = _collect_rows(rows)
    histories: list[list[list[float]]] = []
    for row in values:
        history = sorted(row.assessment_history, key=lambda item: item.time_from_origin_hours)
        if len(history) != 4 or any(not item.is_valid for item in history):
            raise ValueError("Gate7 history requires four valid assessments; no masks or padding")
        if any(item.time_from_origin_hours >= 0 for item in history):
            raise ValueError("Gate7 history assessments must precede origin")
        histories.append(
            [
                [
                    _feature_float(value, name)
                    for name, value in zip(
                        GATE7_HISTORY_FEATURE_NAMES,
                        (
                            item.time_from_origin_hours,
                            item.force_summary_n_per_kg,
                            item.impulse_summary_m_s,
                            item.depth_summary_m,
                        ),
                        strict=True,
                    )
                ]
                for item in history
            ]
        )
    result = np.asarray(histories, dtype=np.float64).reshape(len(values), 4, 4)
    result.setflags(write=False)
    return result


__all__ = [
    "GATE7_HISTORY_SOURCE_AUTHORITY_V1",
    "GATE7_HISTORY_SCHEMA_V1",
    "GATE7_HISTORY_FEATURE_NAMES",
    "project_gate7_history_v1",
    "GATE7_AVAILABLE_FEATURE_INDICES",
    "GATE7_AVAILABLE_FEATURE_NAMES",
    "GATE7_CAMP_ROW_GAPS",
    "GATE7_FEATURE_CONTRACT",
    "GATE7_FEATURE_NAMES",
    "GATE7_FEATURE_UNITS",
    "GATE7_MISSING_AUTHORITY",
    "Gate7AvailableFeatureProjection",
    "Gate7FeatureConstruction",
    "Gate7FeatureContract",
    "Gate7FeatureDefinition",
    "Gate7FeatureUnit",
    "Gate7CampPredictionInput",
    "Gate7ExposureFeature",
    "Gate7HistoryAssessment",
    "Gate7MissingAuthority",
    "Gate7MissingAuthorityCode",
    "Gate7PlanFeature",
    "Gate7ProjectionInputCode",
    "Gate7ProjectionInputError",
    "Gate7ProjectionAttempt",
    "Gate7ProjectionStatus",
    "Gate7PublicFeatureRow",
    "Gate7RoutineAssessment",
    "Gate7RoutineSource",
    "Gate7RoutineState",
    "Gate7RoutineTemporalAuthority",
    "project_gate7_available_fields_v1",
    "project_gate7_historical_v1",
    "project_gate7_v1",
]
