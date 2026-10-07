"""Deterministic clean-room samples for the initial and canonical camp task."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from hashlib import sha256
from typing import cast

from cmj_recovery_dynamics.contracts import (
    ForecastHorizon,
    OutcomeVariable,
    TargetCell,
)
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import (
    CampResponseState,
    EventTimeParameters,
    ExposureComponent,
    ExposureEvent,
    simulate_camp_response,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    INITIAL_PRESEASON_CAMP_EVALUATION,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    CalibrationReferenceStatus,
    ReferenceHash,
    ReproductionClaim,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionDimension as Dimension,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionStatus as Status,
)
from cmj_recovery_dynamics.reproduction.registry import get_reproduction_contract
from cmj_recovery_dynamics.tasks.preseason_camp_recovery import PRESEASON_CAMP_RECOVERY_TASK

OSS_REPRODUCTION_ID = "oss_event_time_camp_history_v1"
OSS_SEED = 20261007  # New reproduction authority; never a recovered D02/D03 root seed.
OSS_BASELINE_TRIAL_COUNT = 3  # Open-source convention; the historical count remains unresolved.
OSS_TARGET_TRIAL_COUNT = 3
ORIGINS_PER_PARTICIPANT = 2
HORIZON_TIMES_HOURS = {
    ForecastHorizon.H72: 72.0,
    ForecastHorizon.D7: 168.0,
}
HORIZON_WINDOWS_HOURS = {
    window.horizon: (float(window.start_offset_hours), float(window.end_offset_hours))
    for window in PRESEASON_CAMP_RECOVERY_TASK.horizon_windows
}
_SPLITS = {
    "training": ("public_train", 1024),
    "public_validation": ("public_validation", 128),
}
_MISSINGNESS_STATES = (
    "UNSCHEDULED",
    "SCHEDULED_UNAVAILABLE",
    "TRIAL_INVALID",
    "FIELD_STRUCTURALLY_ABSENT",
    "OBSERVED_MASKED",
)
_PREDICTION_FIELDS = frozenset(
    {
        "participant_key",
        "origin_id",
        "query_id",
        "horizon",
        "target_time_hours",
        "baseline",
        "assessment_history",
        "exposure_history",
        "index_exposure",
        "known_plan",
    }
)
_PROHIBITED_PREDICTION_FIELDS = frozenset(
    {
        "target",
        "label",
        "observed_target",
        "future_realized_exposures",
        "realized_future_exposures",
        "target_assessment",
        "scorer",
        "random_state",
    }
)


class InformationLeakageError(ValueError):
    """A public prediction record contains target-time or hidden information."""


class AssessmentAvailability(StrEnum):
    VALID = "valid"
    UNSCHEDULED = "UNSCHEDULED"
    SCHEDULED_UNAVAILABLE = "SCHEDULED_UNAVAILABLE"
    TRIAL_INVALID = "TRIAL_INVALID"
    FIELD_STRUCTURALLY_ABSENT = "FIELD_STRUCTURALLY_ABSENT"
    OBSERVED_MASKED = "OBSERVED_MASKED"


@dataclass(frozen=True, slots=True)
class CampReproductionConfig:
    reproduction_id: str
    seed: int
    seed_authority: str
    rng_algorithm: str
    stream_construction: str
    draw_order: str
    substream_strategy: str
    rng_namespaces: tuple[str, ...]
    baseline_trial_count: int
    baseline_trial_count_authority: str
    historical_baseline_trial_count: int | None
    pre_index_exposure_history_convention: str


OSS_CAMP_REPRODUCTION = CampReproductionConfig(
    reproduction_id=OSS_REPRODUCTION_ID,
    seed=OSS_SEED,
    seed_authority="new_reproduction_authority",
    rng_algorithm="CPython random.Random version 2",
    stream_construction="SHA-256 of canonical JSON semantic keys; first 16 bytes as unsigned seed",
    draw_order="one random() draw per keyed uniform value; decimal rounding to nine places",
    substream_strategy="independent semantic-keyed streams",
    rng_namespaces=(
        "athlete",
        "event",
        "measurement",
        "assessment",
        "missingness.public.state",
        "public_dataset.row",
    ),
    baseline_trial_count=OSS_BASELINE_TRIAL_COUNT,
    baseline_trial_count_authority="open_source_reproduction_convention",
    historical_baseline_trial_count=None,
    pre_index_exposure_history_convention=(
        "empty_in_clean_room_schedule; no historical pre-index events are asserted"
    ),
)


@dataclass(frozen=True, slots=True)
class CriterionTrial:
    force_n_per_kg: float
    net_impulse_m_s: float
    depth_m: float

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value)
            for value in (self.force_n_per_kg, self.net_impulse_m_s, self.depth_m)
        ):
            raise ValueError("criterion-trial measurements must be finite")


@dataclass(frozen=True, slots=True)
class AssessmentObservation:
    assessment_id: str
    time_from_origin_hours: float
    availability: AssessmentAvailability
    trials: tuple[CriterionTrial, ...] = ()

    def __post_init__(self) -> None:
        if not self.assessment_id:
            raise ValueError("assessment id is required")
        if not math.isfinite(self.time_from_origin_hours):
            raise ValueError("assessment timestamp must be finite")
        if (self.availability is AssessmentAvailability.VALID) != bool(self.trials):
            raise ValueError("valid assessments need trials; unavailable assessments must not")

    @property
    def is_valid(self) -> bool:
        return self.availability is AssessmentAvailability.VALID

    @property
    def force_summary_n_per_kg(self) -> float | None:
        return (
            math.fsum(trial.force_n_per_kg for trial in self.trials) / len(self.trials)
            if self.is_valid
            else None
        )

    @property
    def impulse_summary_m_s(self) -> float | None:
        return (
            math.fsum(trial.net_impulse_m_s for trial in self.trials) / len(self.trials)
            if self.is_valid
            else None
        )

    @property
    def depth_summary_m(self) -> float | None:
        return (
            math.fsum(trial.depth_m for trial in self.trials) / len(self.trials)
            if self.is_valid
            else None
        )


@dataclass(frozen=True, slots=True)
class BaselineSummary:
    force_n_per_kg: float
    net_impulse_m_s: float
    depth_m: float
    selected_assessment_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value)
            for value in (self.force_n_per_kg, self.net_impulse_m_s, self.depth_m)
        ):
            raise ValueError("baseline summaries must be finite")
        if len(self.selected_assessment_ids) != 2:
            raise ValueError("camp baseline requires the two latest qualifying assessments")


@dataclass(frozen=True, slots=True)
class CampExposure:
    event_id: str
    time_from_origin_hours: float
    kind: str
    components: tuple[ExposureComponent, ...]

    def __post_init__(self) -> None:
        if not self.event_id or not self.kind:
            raise ValueError("exposure id and kind are required")
        if not math.isfinite(self.time_from_origin_hours):
            raise ValueError("exposure timestamp must be finite")
        if not self.components:
            raise ValueError("camp exposures need public dose components")

    def as_dynamics_event(self) -> ExposureEvent:
        return ExposureEvent(
            event_id=self.event_id,
            timestamp_hours=self.time_from_origin_hours,
            kind=self.kind,
            components=self.components,
        )


@dataclass(frozen=True, slots=True)
class PlannedExposure:
    event_id: str
    time_from_origin_hours: float
    kind: str
    components: tuple[ExposureComponent, ...]
    known_at_origin: bool = True

    def __post_init__(self) -> None:
        if not self.event_id or not self.kind:
            raise ValueError("planned exposure id and kind are required")
        if not math.isfinite(self.time_from_origin_hours) or self.time_from_origin_hours <= 0:
            raise ValueError("planned exposures must occur after the index origin")
        if not self.known_at_origin:
            raise ValueError("only plans known at the origin are public predictors")


@dataclass(frozen=True, slots=True)
class CampPredictionRow:
    participant_key: str
    origin_id: str
    query_id: str
    horizon: ForecastHorizon
    target_time_hours: float
    baseline: BaselineSummary
    assessment_history: tuple[AssessmentObservation, ...]
    exposure_history: tuple[CampExposure, ...]
    index_exposure: CampExposure
    known_plan: tuple[PlannedExposure, ...]

    def __post_init__(self) -> None:
        if not self.participant_key or not self.origin_id or not self.query_id:
            raise ValueError("prediction-row grouping and query keys are required")
        validate_target_time(self.horizon, self.target_time_hours)
        if any(item.time_from_origin_hours >= 0 for item in self.assessment_history):
            raise InformationLeakageError("assessment history must stop before the index origin")
        if any(item.time_from_origin_hours >= 0 for item in self.exposure_history):
            raise InformationLeakageError("exposure history must stop before the index origin")
        if self.index_exposure.time_from_origin_hours != 0:
            raise ValueError("index exposure must be timestamped at the prediction origin")
        if any(
            not item.known_at_origin or item.time_from_origin_hours > self.target_time_hours
            for item in self.known_plan
        ):
            raise InformationLeakageError("known plan contains an unavailable or post-query event")
        history_ids = {item.assessment_id for item in self.assessment_history}
        if not set(self.baseline.selected_assessment_ids).issubset(history_ids):
            raise ValueError("selected baseline assessments must be present in public history")

    def predictor_features(self) -> dict[str, object]:
        """Return predictors only; grouping keys and observed outcomes stay separate."""
        return {
            "horizon": self.horizon.label,
            "target_time_hours": self.target_time_hours,
            "baseline": {
                "force_n_per_kg": self.baseline.force_n_per_kg,
                "net_impulse_m_s": self.baseline.net_impulse_m_s,
                "depth_m": self.baseline.depth_m,
                "selected_assessment_ids": self.baseline.selected_assessment_ids,
            },
            "assessment_history": tuple(
                _assessment_record(item) for item in self.assessment_history
            ),
            "exposure_history": tuple(_exposure_record(item) for item in self.exposure_history),
            "index_exposure": _exposure_record(self.index_exposure),
            "known_plan": tuple(_plan_record(item) for item in self.known_plan),
        }


def validate_target_time(horizon: ForecastHorizon, target_time_hours: float) -> float:
    if not math.isfinite(target_time_hours):
        raise ValueError("target time must be finite")
    lower, upper = HORIZON_WINDOWS_HOURS[horizon]
    if not lower <= target_time_hours <= upper:
        raise ValueError(f"{horizon.label} time must lie in [{lower}, {upper}] hours")
    return target_time_hours


def select_camp_baseline(
    assessments: tuple[AssessmentObservation, ...],
) -> BaselineSummary:
    """Average the two latest valid assessments in the inclusive 24–240 h window."""
    qualifying = tuple(
        sorted(
            (
                item
                for item in assessments
                if item.is_valid and 24.0 <= -item.time_from_origin_hours <= 240.0
            ),
            key=lambda item: item.time_from_origin_hours,
            reverse=True,
        )
    )
    if len(qualifying) < 2:
        raise ValueError("two qualifying valid pre-index assessments are required")
    selected = qualifying[:2]
    forces = tuple(item.force_summary_n_per_kg for item in selected)
    impulses = tuple(item.impulse_summary_m_s for item in selected)
    depths = tuple(item.depth_summary_m for item in selected)
    assert all(value is not None for value in (*forces, *impulses, *depths))
    return BaselineSummary(
        math.fsum(value for value in forces if value is not None) / 2,
        math.fsum(value for value in impulses if value is not None) / 2,
        math.fsum(value for value in depths if value is not None) / 2,
        tuple(item.assessment_id for item in selected),
    )


def prediction_row_from_mapping(values: Mapping[str, object]) -> CampPredictionRow:
    """Build the public row from typed fields and reject future labels or outcomes."""
    prohibited = set(values).intersection(_PROHIBITED_PREDICTION_FIELDS)
    if prohibited:
        raise InformationLeakageError(
            f"prediction input includes prohibited fields: {sorted(prohibited)}"
        )
    unknown = set(values).difference(_PREDICTION_FIELDS)
    if unknown:
        raise ValueError(f"unknown prediction fields: {sorted(unknown)}")
    if frozenset(values) != _PREDICTION_FIELDS:
        raise ValueError("prediction row is missing required public fields")
    participant_key = values["participant_key"]
    origin_id = values["origin_id"]
    query_id = values["query_id"]
    horizon = values["horizon"]
    target_time = values["target_time_hours"]
    baseline = values["baseline"]
    assessments = values["assessment_history"]
    exposures = values["exposure_history"]
    index_exposure = values["index_exposure"]
    known_plan = values["known_plan"]
    if not isinstance(participant_key, str) or not isinstance(origin_id, str):
        raise TypeError("prediction grouping keys must be strings")
    if not isinstance(query_id, str) or not isinstance(horizon, ForecastHorizon):
        raise TypeError("query id and horizon have invalid types")
    if isinstance(target_time, bool) or not isinstance(target_time, int | float):
        raise TypeError("target time must be numeric")
    if not isinstance(baseline, BaselineSummary):
        raise TypeError("baseline must be a BaselineSummary")
    if not isinstance(assessments, tuple):
        raise TypeError("assessment history must be a tuple of AssessmentObservation values")
    assessment_items = cast(tuple[object, ...], assessments)
    if any(not isinstance(item, AssessmentObservation) for item in assessment_items):
        raise TypeError("assessment history must be a tuple of AssessmentObservation values")
    if not isinstance(exposures, tuple):
        raise TypeError("exposure history must be a tuple of CampExposure values")
    exposure_items = cast(tuple[object, ...], exposures)
    if any(not isinstance(item, CampExposure) for item in exposure_items):
        raise TypeError("exposure history must be a tuple of CampExposure values")
    if not isinstance(index_exposure, CampExposure):
        raise TypeError("index exposure must be a CampExposure")
    if not isinstance(known_plan, tuple):
        raise TypeError("known plan must be a tuple of PlannedExposure values")
    plan_items = cast(tuple[object, ...], known_plan)
    if any(not isinstance(item, PlannedExposure) for item in plan_items):
        raise TypeError("known plan must be a tuple of PlannedExposure values")
    return CampPredictionRow(
        participant_key,
        origin_id,
        query_id,
        horizon,
        float(target_time),
        baseline,
        cast(tuple[AssessmentObservation, ...], assessments),
        cast(tuple[CampExposure, ...], exposures),
        index_exposure,
        cast(tuple[PlannedExposure, ...], known_plan),
    )


@dataclass(frozen=True, slots=True)
class CampTarget:
    query_id: str
    horizon: ForecastHorizon
    target_time_hours: float
    observed_force_n_per_kg: float
    observed_net_impulse_m_s: float
    force_innovation_n_per_kg: float
    net_impulse_innovation_m_s: float
    criterion_trials: tuple[CriterionTrial, ...]

    def __post_init__(self) -> None:
        validate_target_time(self.horizon, self.target_time_hours)
        values = (
            self.observed_force_n_per_kg,
            self.observed_net_impulse_m_s,
            self.force_innovation_n_per_kg,
            self.net_impulse_innovation_m_s,
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("observed camp targets must be finite")
        if len(self.criterion_trials) != OSS_TARGET_TRIAL_COUNT:
            raise ValueError("camp targets aggregate exactly three criterion trials")
        mean_force = math.fsum(item.force_n_per_kg for item in self.criterion_trials) / len(
            self.criterion_trials
        )
        mean_impulse = math.fsum(item.net_impulse_m_s for item in self.criterion_trials) / len(
            self.criterion_trials
        )
        if not math.isclose(mean_force, self.observed_force_n_per_kg, abs_tol=1e-9):
            raise ValueError("observed force must equal the three-trial criterion mean")
        if not math.isclose(mean_impulse, self.observed_net_impulse_m_s, abs_tol=1e-9):
            raise ValueError("observed impulse must equal the three-trial criterion mean")

    def value(self, outcome: OutcomeVariable) -> float:
        if outcome is OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION:
            return self.force_innovation_n_per_kg
        if outcome is OutcomeVariable.NET_IMPULSE_INNOVATION:
            return self.net_impulse_innovation_m_s
        raise ValueError(f"unsupported camp outcome: {outcome}")


def camp_target_cell(row: CampPredictionRow, outcome: OutcomeVariable) -> TargetCell:
    return TargetCell(outcome, row.horizon)


@dataclass(frozen=True, slots=True)
class CampSampleGeometry:
    participants: int
    origins_per_participant: int = ORIGINS_PER_PARTICIPANT
    horizons_per_origin: int = 2

    def __post_init__(self) -> None:
        if type(self.participants) is not int:
            raise TypeError("participant count must be an integer")
        if self.participants < 1:
            raise ValueError("participant count must be positive")
        if self.origins_per_participant != ORIGINS_PER_PARTICIPANT:
            raise ValueError("camp reproduction uses two origins per participant")
        if self.horizons_per_origin != 2:
            raise ValueError("camp reproduction uses the H72 and D7 horizons")

    @property
    def origins(self) -> int:
        return self.participants * self.origins_per_participant

    @property
    def query_rows(self) -> int:
        return self.origins * self.horizons_per_origin


@dataclass(frozen=True, slots=True)
class CampSampleIdentity:
    reproduction_id: str
    artifact_id: str
    generated_dataset_identity: str
    artifact_kind: str
    benchmark_name: str
    historical_reference_dataset: str
    evaluation_name: str
    normalization_floor: float
    seed: int
    seed_authority: str
    historical_claims: tuple[ReproductionClaim, ...]
    calibration_reference_status: CalibrationReferenceStatus
    calibration_reference_value: float | None
    historical_reference_hashes: tuple[ReferenceHash, ...]
    baseline_trial_count: int
    baseline_trial_count_authority: str
    historical_baseline_trial_count: int | None
    pre_index_exposure_history_convention: str

    def __post_init__(self) -> None:
        dimensions = tuple(claim.dimension for claim in self.historical_claims)
        if len(set(dimensions)) != len(dimensions) or set(dimensions) != set(Dimension):
            raise ValueError("sample identity must retain every distinct historical claim")

    def historical_status(self, dimension: Dimension) -> Status:
        for claim in self.historical_claims:
            if claim.dimension is dimension:
                return claim.status
        raise ValueError(f"historical claim is missing: {dimension.value}")

    def authority_snapshot(self) -> dict[str, object]:
        """Return explicit identity/status metadata; hashes are historical references only."""
        reproduction = get_camp_reproduction_config(self.seed)
        return {
            "artifact_kind": self.artifact_kind,
            "artifact_id": self.artifact_id,
            "generated_dataset_identity": self.generated_dataset_identity,
            "reproduction_id": self.reproduction_id,
            "new_reproduction_seed": self.seed,
            "seed_authority": self.seed_authority,
            "new_reproduction_rng": {
                "algorithm": reproduction.rng_algorithm,
                "stream_construction": reproduction.stream_construction,
                "draw_order": reproduction.draw_order,
                "substream_strategy": reproduction.substream_strategy,
                "namespaces": reproduction.rng_namespaces,
            },
            "benchmark_name": self.benchmark_name,
            "historical_reference_dataset": self.historical_reference_dataset,
            "evaluation_name": self.evaluation_name,
            "normalization_floor": self.normalization_floor,
            "historical_authority": {
                claim.dimension.value: claim.status.value for claim in self.historical_claims
            },
            "evaluation_authority": {
                "calibration_reference": self.calibration_reference_status.value,
                "calibration_reference_value": self.calibration_reference_value,
            },
            "historical_reference_hashes_only": tuple(
                {"split": item.split_name, "sha256": item.digest, "authority": item.authority}
                for item in self.historical_reference_hashes
            ),
            "open_source_baseline_trial_convention": {
                "trial_count": self.baseline_trial_count,
                "authority": self.baseline_trial_count_authority,
                "historical_trial_count": self.historical_baseline_trial_count,
            },
            "open_source_pre_index_exposure_convention": self.pre_index_exposure_history_convention,
        }


@dataclass(frozen=True, slots=True)
class CampSample:
    identity: CampSampleIdentity
    split_name: str
    geometry: CampSampleGeometry
    rows: tuple[CampPredictionRow, ...]
    targets: tuple[CampTarget, ...]

    def __post_init__(self) -> None:
        if len(self.rows) != self.geometry.query_rows or len(self.targets) != len(self.rows):
            raise ValueError("sample rows and target labels must match the declared geometry")
        if tuple(row.query_id for row in self.rows) != tuple(
            target.query_id for target in self.targets
        ):
            raise ValueError("prediction rows and observed target labels must align")
        origins = {row.origin_id for row in self.rows}
        participants = {row.participant_key for row in self.rows}
        if len(origins) != self.geometry.origins or len(participants) != self.geometry.participants:
            raise ValueError("sample identity counts do not match its geometry")
        rows_per_origin: dict[str, int] = {}
        for row in self.rows:
            rows_per_origin[row.origin_id] = rows_per_origin.get(row.origin_id, 0) + 1
        if any(count != 2 for count in rows_per_origin.values()):
            raise ValueError("clean-room camp rows use one row for each of two horizons per origin")

    def to_jsonl(self) -> str:
        """Serialize this new sample; historical byte serialization remains unresolved."""
        lines: list[str] = []
        for row, target in zip(self.rows, self.targets, strict=True):
            record = {
                "artifact_kind": self.identity.artifact_kind,
                "artifact_id": self.identity.artifact_id,
                "reproduction_id": self.identity.reproduction_id,
                "reproduction_seed": self.identity.seed,
                "benchmark_identity": self.identity.benchmark_name,
                "evaluation_identity": self.identity.evaluation_name,
                "split": self.split_name,
                "query_id": row.query_id,
                "grouping": {"participant_key": row.participant_key, "origin_id": row.origin_id},
                "features": row.predictor_features(),
                "label": {
                    OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value: (
                        target.force_innovation_n_per_kg
                    ),
                    OutcomeVariable.NET_IMPULSE_INNOVATION.value: target.net_impulse_innovation_m_s,
                },
                "label_units": {
                    OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value: "N/kg",
                    OutcomeVariable.NET_IMPULSE_INNOVATION.value: "m/s",
                },
            }
            lines.append(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
        return "\n".join(lines) + "\n"


def _contract_identity(benchmark_name: str, seed: int) -> CampSampleIdentity:
    contract = get_reproduction_contract(benchmark_name)
    if benchmark_name == "initial_preseason_camp_recovery":
        dataset = "initial_preseason_camp_public_sample"
        evaluation = INITIAL_PRESEASON_CAMP_EVALUATION
    elif benchmark_name == "canonical_preseason_camp_recovery":
        dataset = "canonical_preseason_camp_horizon_sample"
        evaluation = CANONICAL_PRESEASON_CAMP_EVALUATION
    else:
        raise ValueError(f"unsupported camp benchmark identity: {benchmark_name}")
    sample_name = "initial" if benchmark_name.startswith("initial_") else "canonical"
    artifact_id = f"{OSS_REPRODUCTION_ID}:{sample_name}:{seed}"
    if evaluation.normalization_floor is None:
        raise ValueError("camp scorer normalization floor is unavailable")
    reproduction = get_camp_reproduction_config(seed)
    return CampSampleIdentity(
        reproduction_id=OSS_REPRODUCTION_ID,
        artifact_id=artifact_id,
        generated_dataset_identity=f"oss_{sample_name}_camp_history_sample_seed_{seed}",
        artifact_kind="clean_room_reproduction",
        benchmark_name=benchmark_name,
        historical_reference_dataset=dataset,
        evaluation_name=evaluation.name,
        normalization_floor=evaluation.normalization_floor,
        seed=seed,
        seed_authority="new_reproduction_authority",
        historical_claims=contract.claims,
        calibration_reference_status=contract.evaluation.calibration_reference_status,
        calibration_reference_value=contract.evaluation.calibration_reference_value,
        historical_reference_hashes=contract.reference_hashes,
        baseline_trial_count=OSS_BASELINE_TRIAL_COUNT,
        baseline_trial_count_authority="open_source_reproduction_convention",
        historical_baseline_trial_count=None,
        pre_index_exposure_history_convention=reproduction.pre_index_exposure_history_convention,
    )


def get_camp_reproduction_config(seed: int = OSS_SEED) -> CampReproductionConfig:
    if type(seed) is not int:
        raise TypeError("clean-room seed must be an integer")
    return replace(OSS_CAMP_REPRODUCTION, seed=seed)


def _semantic_seed(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str | None,
    cluster_id: str | None,
    entity_id: str | None,
    event_or_assessment_id: str | None,
    purpose_namespace: str,
) -> int:
    material = {
        "project_id": "CMJRecoveryDynamicsBench",
        "contract_version": OSS_REPRODUCTION_ID,
        "root_seed": seed,
        "split": split,
        "world_id": world_id,
        "origin_id": origin_id,
        "cluster_id": cluster_id,
        "entity_id": entity_id,
        "event_or_assessment_id": event_or_assessment_id,
        "purpose_namespace": purpose_namespace,
    }
    digest = sha256(
        json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:16], "big", signed=False)


def _rng(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str | None,
    cluster_id: str | None,
    entity_id: str | None,
    event_or_assessment_id: str | None,
    purpose_namespace: str,
) -> random.Random:
    derived = _semantic_seed(
        seed=seed,
        split=split,
        world_id=world_id,
        origin_id=origin_id,
        cluster_id=cluster_id,
        entity_id=entity_id,
        event_or_assessment_id=event_or_assessment_id,
        purpose_namespace=purpose_namespace,
    )
    result = random.Random()
    result.seed(derived, version=2)
    return result


def _draw_uniform(
    lower: float,
    upper: float,
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str | None,
    cluster_id: str | None,
    entity_id: str | None,
    event_id: str | None,
    purpose: str,
) -> float:
    rng = _rng(
        seed=seed,
        split=split,
        world_id=world_id,
        origin_id=origin_id,
        cluster_id=cluster_id,
        entity_id=entity_id,
        event_or_assessment_id=event_id,
        purpose_namespace=purpose,
    )
    value = lower + (upper - lower) * rng.random()
    rounded = round(value, 9)
    return 0.0 if rounded == 0.0 else rounded


def _participant_parameters(
    *, seed: int, split: str, world_id: str, cluster_id: str, participant_key: str
) -> tuple[float, float, EventTimeParameters, float]:
    # Draw ranges and response bounds follow the M1 camp world-generator authority.
    def draw(purpose: str, lower: float, upper: float) -> float:
        return _draw_uniform(
            lower,
            upper,
            seed=seed,
            split=split,
            world_id=world_id,
            origin_id=None,
            cluster_id=cluster_id,
            entity_id=participant_key,
            event_id=None,
            purpose=purpose,
        )

    depth = draw("athlete.depth", 0.16, 0.42)
    baseline_force = draw("athlete.baseline.force", 18.0, 32.0)
    baseline_impulse = draw("athlete.baseline.impulse", 0.8, 3.2)
    parameters = EventTimeParameters(
        dose_response_ceiling_kappa=10.0,
        dose_half_saturation_delta=1.0,
        dose_exponent_gamma=1.0,
        fast_fatigue_time_constant_hours=draw("athlete.tau.fast", 6.0, 120.0),
        slow_adaptation_time_constant_hours=draw("athlete.tau.slow", 72.0, 504.0),
        memory_shape_beta=draw("athlete.beta", 0.5, 1.5),
        fatigue_force_amplitude_n_per_kg=draw("athlete.fatigue.force", 0.0, 3.0),
        adaptation_force_amplitude_n_per_kg=draw("athlete.adaptation.force", 0.0, 3.0),
        fatigue_impulse_amplitude_m_per_s=draw("athlete.fatigue.impulse", 0.0, 0.6),
        adaptation_impulse_amplitude_m_per_s=draw("athlete.adaptation.impulse", 0.0, 0.6),
    )
    return depth, baseline_force, parameters, baseline_impulse


def _make_exposure(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str,
    cluster_id: str,
    event_id: str,
    timestamp: float,
    kind: str,
) -> CampExposure:
    duration = _draw_uniform(
        60.0,
        140.0,
        seed=seed,
        split=split,
        world_id=world_id,
        origin_id=origin_id,
        cluster_id=cluster_id,
        entity_id=origin_id,
        event_id=event_id,
        purpose="event.duration",
    )
    return CampExposure(
        event_id,
        timestamp,
        kind,
        (ExposureComponent("duration_minutes", duration, "minutes", 100.0),),
    )


def _measurement_error(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str,
    cluster_id: str,
    assessment_id: str,
    trial_index: int,
) -> tuple[float, float, float, float]:
    def draw(namespace: str, entity_id: str, lower: float, upper: float) -> float:
        return _draw_uniform(
            lower,
            upper,
            seed=seed,
            split=split,
            world_id=world_id,
            origin_id=origin_id,
            cluster_id=cluster_id,
            entity_id=entity_id,
            event_id=assessment_id,
            purpose=namespace,
        )

    return (
        draw("measurement.between.force", assessment_id, -0.25, 0.25),
        draw("measurement.within.force", f"{assessment_id}-{trial_index}", -0.08, 0.08),
        draw("measurement.between.impulse", assessment_id, -0.06, 0.06),
        draw("measurement.within.impulse", f"{assessment_id}-{trial_index}", -0.02, 0.02),
    )


def _baseline_assessment(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str,
    cluster_id: str,
    assessment_id: str,
    time_hours: float,
    force: float,
    impulse: float,
    depth: float,
) -> AssessmentObservation:
    trials: list[CriterionTrial] = []
    for index in range(OSS_BASELINE_TRIAL_COUNT):
        between_force, within_force, between_impulse, within_impulse = _measurement_error(
            seed=seed,
            split=split,
            world_id=world_id,
            origin_id=origin_id,
            cluster_id=cluster_id,
            assessment_id=assessment_id,
            trial_index=index,
        )
        trials.append(
            CriterionTrial(
                force + between_force + within_force,
                impulse + between_impulse + within_impulse,
                depth,
            )
        )
    return AssessmentObservation(
        assessment_id,
        time_hours,
        AssessmentAvailability.VALID,
        tuple(trials),
    )


def _missingness_assessment(
    *, seed: int, split: str, world_id: str, origin_id: str, cluster_id: str
) -> AssessmentObservation:
    assessment_id = f"assessment-{origin_id}-routine"
    state = _semantic_seed(
        seed=seed,
        split=split,
        world_id=world_id,
        origin_id=origin_id,
        cluster_id=cluster_id,
        entity_id=assessment_id,
        event_or_assessment_id=assessment_id,
        purpose_namespace="missingness.public.state",
    ) % len(_MISSINGNESS_STATES)
    return AssessmentObservation(
        assessment_id,
        -120.0,
        AssessmentAvailability(_MISSINGNESS_STATES[state]),
    )


def _target_assessment(
    *,
    seed: int,
    split: str,
    world_id: str,
    origin_id: str,
    cluster_id: str,
    assessment_id: str,
    query_id: str,
    target_time: float,
    baseline: BaselineSummary,
    state: CampResponseState,
    depth: float,
) -> CampTarget:
    between_force, within_force, between_impulse, within_impulse = _measurement_error(
        seed=seed,
        split=split,
        world_id=world_id,
        origin_id=origin_id,
        cluster_id=cluster_id,
        assessment_id=assessment_id,
        trial_index=0,
    )
    innovation_force = state.net_force_innovation_n_per_kg + between_force + within_force
    innovation_impulse = state.net_impulse_innovation_m_per_s + between_impulse + within_impulse
    observed_force = baseline.force_n_per_kg + innovation_force
    observed_impulse = baseline.net_impulse_m_s + innovation_impulse
    trials = (
        CriterionTrial(observed_force - 0.03, observed_impulse - 0.01, depth),
        CriterionTrial(observed_force, observed_impulse, depth),
        CriterionTrial(observed_force + 0.03, observed_impulse + 0.01, depth),
    )
    return CampTarget(
        query_id,
        ForecastHorizon.H72 if target_time == 72.0 else ForecastHorizon.D7,
        target_time,
        observed_force,
        observed_impulse,
        observed_force - baseline.force_n_per_kg,
        observed_impulse - baseline.net_impulse_m_s,
        trials,
    )


def _build_prediction_row(
    *,
    participant_key: str,
    origin_id: str,
    horizon: ForecastHorizon,
    target_time: float,
    assessments: tuple[AssessmentObservation, ...],
    exposure_history: tuple[CampExposure, ...],
    index_exposure: CampExposure,
    plan: tuple[PlannedExposure, ...],
) -> CampPredictionRow:
    before_origin_assessments = tuple(
        item for item in assessments if item.time_from_origin_hours < 0
    )
    before_origin_exposures = tuple(
        item for item in exposure_history if item.time_from_origin_hours < 0
    )
    baseline = select_camp_baseline(before_origin_assessments)
    known_plan = tuple(
        item for item in plan if item.known_at_origin and item.time_from_origin_hours <= target_time
    )
    return prediction_row_from_mapping(
        {
            "participant_key": participant_key,
            "origin_id": origin_id,
            "query_id": f"query-{origin_id}-{horizon.label}",
            "horizon": horizon,
            "target_time_hours": target_time,
            "baseline": baseline,
            "assessment_history": before_origin_assessments,
            "exposure_history": before_origin_exposures,
            "index_exposure": index_exposure,
            "known_plan": known_plan,
        }
    )


def generate_camp_sample(
    benchmark_name: str,
    *,
    split_name: str = "training",
    seed: int = OSS_SEED,
    participant_count: int | None = None,
) -> CampSample:
    """Generate a deterministic clean-room camp sample under a new seed identity."""
    if split_name not in _SPLITS:
        raise ValueError("camp split must be 'training' or 'public_validation'")
    if type(seed) is not int:
        raise TypeError("clean-room seed must be an integer")
    split_key, default_participants = _SPLITS[split_name]
    participants = default_participants if participant_count is None else participant_count
    geometry = CampSampleGeometry(participants)
    identity = _contract_identity(benchmark_name, seed)
    rows: list[CampPredictionRow] = []
    targets: list[CampTarget] = []
    for participant_index in range(participants):
        participant_key = f"participant-{split_name}-{participant_index:04d}"
        world_id = (
            f"world-{identity.generated_dataset_identity}-{split_name}-{participant_index:04d}"
        )
        cluster_id = (
            f"cluster-{identity.generated_dataset_identity}-{split_name}-{participant_index:04d}"
        )
        depth, baseline_force, parameters, baseline_impulse = _participant_parameters(
            seed=seed,
            split=split_key,
            world_id=world_id,
            cluster_id=cluster_id,
            participant_key=participant_key,
        )
        for origin_index in range(ORIGINS_PER_PARTICIPANT):
            origin_id = f"origin-{split_name}-{participant_index:04d}-{origin_index}"
            # The recovered schedule starts at index; this OSS sample asserts no past events.
            index_exposure = _make_exposure(
                seed=seed,
                split=split_key,
                world_id=world_id,
                origin_id=origin_id,
                cluster_id=cluster_id,
                event_id=f"event-{origin_id}-index",
                timestamp=0.0,
                kind="match",
            )
            first_training = _make_exposure(
                seed=seed,
                split=split_key,
                world_id=world_id,
                origin_id=origin_id,
                cluster_id=cluster_id,
                event_id=f"event-{origin_id}-training-48",
                timestamp=48.0,
                kind="training",
            )
            second_training = _make_exposure(
                seed=seed,
                split=split_key,
                world_id=world_id,
                origin_id=origin_id,
                cluster_id=cluster_id,
                event_id=f"event-{origin_id}-training-120",
                timestamp=120.0,
                kind="training",
            )
            realized_events = (index_exposure, first_training, second_training)
            plan = tuple(
                PlannedExposure(
                    item.event_id,
                    item.time_from_origin_hours,
                    item.kind,
                    item.components,
                )
                for item in (first_training, second_training)
            )
            baseline_assessments = (
                _baseline_assessment(
                    seed=seed,
                    split=split_key,
                    world_id=world_id,
                    origin_id=origin_id,
                    cluster_id=cluster_id,
                    assessment_id=f"assessment-{origin_id}-pre-240",
                    time_hours=-240.0,
                    force=baseline_force,
                    impulse=baseline_impulse,
                    depth=depth,
                ),
                _baseline_assessment(
                    seed=seed,
                    split=split_key,
                    world_id=world_id,
                    origin_id=origin_id,
                    cluster_id=cluster_id,
                    assessment_id=f"assessment-{origin_id}-pre-48",
                    time_hours=-48.0,
                    force=baseline_force,
                    impulse=baseline_impulse,
                    depth=depth,
                ),
                _missingness_assessment(
                    seed=seed,
                    split=split_key,
                    world_id=world_id,
                    origin_id=origin_id,
                    cluster_id=cluster_id,
                ),
            )
            baseline = select_camp_baseline(baseline_assessments)
            query_times = tuple(HORIZON_TIMES_HOURS.values())
            response = simulate_camp_response(
                tuple(item.as_dynamics_event() for item in realized_events),
                query_times,
                parameters,
            )
            for horizon in (ForecastHorizon.H72, ForecastHorizon.D7):
                target_time = HORIZON_TIMES_HOURS[horizon]
                query_id = f"query-{origin_id}-{horizon.label}"
                row = _build_prediction_row(
                    participant_key=participant_key,
                    origin_id=origin_id,
                    horizon=horizon,
                    target_time=target_time,
                    assessments=baseline_assessments,
                    # The OSS schedule has no pre-index events; the row contract accepts
                    # caller-supplied history and enforces its origin cutoff.
                    exposure_history=(),
                    index_exposure=index_exposure,
                    plan=plan,
                )
                target = _target_assessment(
                    seed=seed,
                    split=split_key,
                    world_id=world_id,
                    origin_id=origin_id,
                    cluster_id=cluster_id,
                    assessment_id=f"assessment-{origin_id}-{horizon.label}",
                    query_id=query_id,
                    target_time=target_time,
                    baseline=baseline,
                    state=response.state_at(target_time),
                    depth=depth,
                )
                rows.append(row)
                targets.append(target)
    return CampSample(identity, split_name, geometry, tuple(rows), tuple(targets))


def generate_initial_camp_sample(
    *, split_name: str = "training", seed: int = OSS_SEED, participant_count: int | None = None
) -> CampSample:
    return generate_camp_sample(
        "initial_preseason_camp_recovery",
        split_name=split_name,
        seed=seed,
        participant_count=participant_count,
    )


def generate_canonical_camp_sample(
    *, split_name: str = "training", seed: int = OSS_SEED, participant_count: int | None = None
) -> CampSample:
    return generate_camp_sample(
        "canonical_preseason_camp_recovery",
        split_name=split_name,
        seed=seed,
        participant_count=participant_count,
    )


def _assessment_record(item: AssessmentObservation) -> dict[str, object]:
    return {
        "assessment_id": item.assessment_id,
        "time_from_origin_hours": item.time_from_origin_hours,
        "validity_state": item.availability.value,
        "trial_count": len(item.trials),
        "force_n_per_kg": item.force_summary_n_per_kg,
        "net_impulse_m_s": item.impulse_summary_m_s,
        "depth_m": item.depth_summary_m,
    }


def _component_record(item: ExposureComponent) -> dict[str, object]:
    return {
        "name": item.name,
        "value": item.value,
        "units": item.units,
        "normalization": item.normalization,
        "observed": item.observed,
        "day_mask": item.day_mask,
        "event_mask": item.event_mask,
        "normalized_contribution": item.contribution,
    }


def _exposure_record(item: CampExposure) -> dict[str, object]:
    return {
        "event_id": item.event_id,
        "time_from_origin_hours": item.time_from_origin_hours,
        "kind": item.kind,
        "components": tuple(_component_record(component) for component in item.components),
    }


def _plan_record(item: PlannedExposure) -> dict[str, object]:
    return {
        "event_id": item.event_id,
        "time_from_origin_hours": item.time_from_origin_hours,
        "kind": item.kind,
        "components": tuple(_component_record(component) for component in item.components),
        "known_at_origin": item.known_at_origin,
    }


__all__ = [
    "AssessmentAvailability",
    "AssessmentObservation",
    "BaselineSummary",
    "CampExposure",
    "CampPredictionRow",
    "CampReproductionConfig",
    "CampSample",
    "CampSampleGeometry",
    "CampSampleIdentity",
    "CampTarget",
    "CriterionTrial",
    "HORIZON_TIMES_HOURS",
    "HORIZON_WINDOWS_HOURS",
    "InformationLeakageError",
    "OSS_BASELINE_TRIAL_COUNT",
    "OSS_CAMP_REPRODUCTION",
    "OSS_REPRODUCTION_ID",
    "OSS_SEED",
    "PlannedExposure",
    "camp_target_cell",
    "generate_camp_sample",
    "generate_canonical_camp_sample",
    "generate_initial_camp_sample",
    "get_camp_reproduction_config",
    "prediction_row_from_mapping",
    "select_camp_baseline",
    "validate_target_time",
]
