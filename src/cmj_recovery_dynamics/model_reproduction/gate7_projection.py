"""Versioned public feature authority for the recovered Gate7 input schema."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

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
    CAMP_ROW = "constructible_from_camp_prediction_row"
    MISSING_AUTHORITY = "blocked_on_exact_feature_authority"


class Gate7ProjectionStatus(StrEnum):
    BLOCKED_ON_EXACT_FEATURE_AUTHORITY = "BLOCKED_ON_EXACT_FEATURE_AUTHORITY"


class Gate7MissingAuthorityCode(StrEnum):
    ASSESSMENT_SLOT_POLICY_UNRESOLVED = "assessment_slot_policy_unresolved"
    ASSESSMENT_MISSINGNESS_RULE_UNRESOLVED = "assessment_missingness_rule_unresolved"
    HISTORY_EXPOSURE_SLOT_POLICY_UNRESOLVED = "history_exposure_slot_policy_unresolved"
    EXPOSURE_DURATION_MAPPING_UNRESOLVED = "exposure_duration_mapping_unresolved"
    KNOWN_PLAN_SLOT_POLICY_UNRESOLVED = "known_plan_slot_policy_unresolved"
    ROUTINE_ASSESSMENT_INPUT_ABSENT = "routine_assessment_input_absent"
    ROUTINE_ASSESSMENT_TEMPORAL_AUTHORITY_UNRESOLVED = (
        "routine_assessment_temporal_authority_unresolved"
    )


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
    missing_authority_codes: tuple[Gate7MissingAuthorityCode, ...] = ()

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
        if (self.construction is Gate7FeatureConstruction.MISSING_AUTHORITY) != bool(
            self.missing_authority_codes
        ):
            raise ValueError("blocked features must identify their missing authority")


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
        if self.status is not Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY:
            raise ValueError("the current projector only represents a blocked projection")
        if self.matrix is not None:
            raise ValueError("a blocked projection must not return a feature matrix")
        if not self.missing_authority:
            raise ValueError("a blocked projection must return missing authority")


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
    construction = Gate7FeatureConstruction.MISSING_AUTHORITY
    authority_codes: tuple[Gate7MissingAuthorityCode, ...] = ()
    if index <= 6 or index == 25:
        construction = Gate7FeatureConstruction.CAMP_ROW

    if index == 0:
        input_field = "row.baseline.force_n_per_kg"
        derivation = "Copy the finite public baseline mean force in N/kg."
        temporal = "Baseline is measured before the prediction origin."
        missingness = "Required; CampPredictionRow rejects non-finite baseline values."
    elif index == 1:
        input_field = "row.baseline.net_impulse_m_s"
        derivation = "Copy the finite public baseline net impulse in m/s."
        temporal = "Baseline is measured before the prediction origin."
        missingness = "Required; CampPredictionRow rejects non-finite baseline values."
    elif index in (2, 3):
        horizon = "H72" if index == 2 else "D7"
        input_field = "row.horizon"
        derivation = f"One-hot indicator: 1.0 when the horizon is {horizon}, else 0.0."
        temporal = "Forecast horizon is fixed at the prediction origin."
        missingness = "Required enum value; exactly one registered horizon indicator is 1.0."
    elif index == 4:
        input_field = "row.target_time_hours"
        derivation = "Copy the finite forecast query time in hours."
        temporal = "Query time is registered at the prediction origin."
        missingness = "Required; CampPredictionRow rejects non-finite or out-of-window times."
    elif index in (5, 6):
        edge = "start_offset_hours" if index == 5 else "end_offset_hours"
        input_field = f"PRESEASON_CAMP_RECOVERY_TASK.horizon_windows.{edge}"
        derivation = f"Read the registered {edge} for row.horizon, in hours."
        temporal = "Forecast window is part of the task contract at the prediction origin."
        missingness = "Required registered task value; no imputation."
    elif 7 <= index <= 22:
        input_field = "row.assessment_history"
        derivation = "Read the named field from its recovered ordered history-assessment slot."
        temporal = "CampPredictionRow permits pre-origin assessment history only."
        missingness = (
            "Slot selection, trial aggregation, padding, and invalid-value handling unresolved."
        )
        authority_codes = (
            Gate7MissingAuthorityCode.ASSESSMENT_SLOT_POLICY_UNRESOLVED,
            Gate7MissingAuthorityCode.ASSESSMENT_MISSINGNESS_RULE_UNRESOLVED,
        )
    elif index in (23, 24):
        input_field = "row.exposure_history"
        derivation = "Read the named field from recovered history-exposure slot 0."
        temporal = "CampPredictionRow permits pre-origin exposure history only."
        missingness = "Slot ordering, selection, and duration mapping unresolved."
        authority_codes = (Gate7MissingAuthorityCode.HISTORY_EXPOSURE_SLOT_POLICY_UNRESOLVED,)
        if index == 24:
            authority_codes += (Gate7MissingAuthorityCode.EXPOSURE_DURATION_MAPPING_UNRESOLVED,)
    elif index == 25:
        input_field = "row.index_exposure.time_from_origin_hours"
        derivation = "Copy the index exposure time; the public row contract requires 0 hours."
        temporal = "Index exposure is timestamped at the prediction origin."
        missingness = "Required; CampPredictionRow enforces a zero-hour index exposure."
    elif index == 26:
        input_field = "row.index_exposure.components"
        derivation = "Read the duration_minutes component using the original source rule."
        temporal = "Index exposure is timestamped at the prediction origin."
        missingness = (
            "Exact duration component selection and unavailable-value handling unresolved."
        )
        authority_codes = (Gate7MissingAuthorityCode.EXPOSURE_DURATION_MAPPING_UNRESOLVED,)
    elif 27 <= index <= 32:
        input_field = "row.known_plan"
        derivation = "Read the named field from its recovered known-plan slot."
        temporal = "Plan must be known at origin and occur no later than the query time."
        missingness = "Slot ordering, selection, padding, and duration mapping unresolved."
        authority_codes = (Gate7MissingAuthorityCode.KNOWN_PLAN_SLOT_POLICY_UNRESOLVED,)
        if index in (28, 30, 32):
            authority_codes += (Gate7MissingAuthorityCode.EXPOSURE_DURATION_MAPPING_UNRESOLVED,)
    elif index == 33:
        input_field = "not represented by CampPredictionRow"
        derivation = "Encode the routine assessment scheduled flag as 1.0 or 0.0."
        temporal = "Availability at the prediction origin is not established."
        missingness = "Required source field is absent; do not infer from future assessment rows."
        authority_codes = (
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_INPUT_ABSENT,
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_TEMPORAL_AUTHORITY_UNRESOLVED,
        )
    else:
        state = _ROUTINE_STATES[index - 34]
        input_field = "not represented by CampPredictionRow"
        derivation = f"One-hot indicator for routine assessment state {state}."
        temporal = "Availability-state cutoff is unresolved and may be after the origin."
        missingness = "Required source field is absent; no state may be inferred or defaulted."
        authority_codes = (
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_INPUT_ABSENT,
            Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_TEMPORAL_AUTHORITY_UNRESOLVED,
        )

    if not authority_codes and construction is Gate7FeatureConstruction.MISSING_AUTHORITY:
        raise AssertionError(f"missing Gate7 authority code for feature {name}")
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
        missing_authority_codes=authority_codes,
    )


GATE7_FEATURE_CONTRACT = Gate7FeatureContract(
    version="gate7_feature_projection_v1",
    model_identity="gate7_m0_candidate",
    source_evidence=(
        "Recovered Gate7 M0 run configuration feature order and raw transform.",
        "Recovered Gate7 model-family and public data manifests.",
        "Public CampPredictionRow and preseason camp task contracts.",
    ),
    features=tuple(
        _feature_definition(index, name) for index, name in enumerate(GATE7_FEATURE_NAMES)
    ),
    model_input_preprocessing=(
        "The recovered model configuration records train-only mean/std standardization after "
        "raw feature construction. Fitted means and scales are not part of this public contract."
    ),
)


GATE7_MISSING_AUTHORITY = (
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.ASSESSMENT_SLOT_POLICY_UNRESOLVED,
        GATE7_FEATURE_NAMES[7:23],
        "Recover the source extractor rule for slot direction, selection to four records, "
        "trial aggregation, padding, and invalid or absent assessment values.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.ASSESSMENT_MISSINGNESS_RULE_UNRESOLVED,
        GATE7_FEATURE_NAMES[7:23],
        "Recover the exact missing-value and preprocessing behavior for each history field.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.HISTORY_EXPOSURE_SLOT_POLICY_UNRESOLVED,
        GATE7_FEATURE_NAMES[23:25],
        "Recover the source rule for ordering and selecting history exposure slot 0.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.EXPOSURE_DURATION_MAPPING_UNRESOLVED,
        (
            GATE7_FEATURE_NAMES[24],
            GATE7_FEATURE_NAMES[26],
            GATE7_FEATURE_NAMES[28],
            GATE7_FEATURE_NAMES[30],
            GATE7_FEATURE_NAMES[32],
        ),
        "Recover the exact duration component name, unit validation, and unavailable-value rule.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.KNOWN_PLAN_SLOT_POLICY_UNRESOLVED,
        GATE7_FEATURE_NAMES[27:33],
        "Recover the source rule for sorting, slot assignment, truncation, padding, and missing "
        "duration handling for the three known-plan records.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_INPUT_ABSENT,
        GATE7_FEATURE_NAMES[33:39],
        "Provide a public versioned prediction-row field for scheduled and availability state.",
    ),
    Gate7MissingAuthority(
        Gate7MissingAuthorityCode.ROUTINE_ASSESSMENT_TEMPORAL_AUTHORITY_UNRESOLVED,
        GATE7_FEATURE_NAMES[33:39],
        "Provide source evidence that schedule and state are known at the prediction origin and "
        "do not depend on future measurements or target labels.",
    ),
)


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


def project_gate7_v1(rows: Iterable[CampPredictionRow]) -> Gate7ProjectionAttempt:
    """Fail closed until every feature has exact extraction and temporal authority."""
    row_values = _collect_rows(rows)
    return Gate7ProjectionAttempt(
        status=Gate7ProjectionStatus.BLOCKED_ON_EXACT_FEATURE_AUTHORITY,
        row_count=len(row_values),
        matrix=None,
        missing_authority=GATE7_MISSING_AUTHORITY,
    )


__all__ = [
    "GATE7_AVAILABLE_FEATURE_INDICES",
    "GATE7_AVAILABLE_FEATURE_NAMES",
    "GATE7_FEATURE_CONTRACT",
    "GATE7_FEATURE_NAMES",
    "GATE7_FEATURE_UNITS",
    "GATE7_MISSING_AUTHORITY",
    "Gate7AvailableFeatureProjection",
    "Gate7FeatureConstruction",
    "Gate7FeatureContract",
    "Gate7FeatureDefinition",
    "Gate7FeatureUnit",
    "Gate7MissingAuthority",
    "Gate7MissingAuthorityCode",
    "Gate7ProjectionAttempt",
    "Gate7ProjectionStatus",
    "project_gate7_available_fields_v1",
    "project_gate7_v1",
]
