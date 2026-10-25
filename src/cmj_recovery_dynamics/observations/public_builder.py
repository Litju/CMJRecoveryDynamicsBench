"""Origin-pinned Gate7 observations and a distinct clean-room integration fixture.

An ingestion authority pins both digests outside prediction requests. Hashes prove
identity, not truth or permission; callers remain responsible for authorization.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import cast

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import ExposureComponent
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_FEATURE_NAMES,
    GATE7_FEATURE_UNITS,
    Gate7CampPredictionInput,
    Gate7RoutineSource,
    Gate7RoutineState,
    project_gate7_v1,
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    HORIZON_TIMES_HOURS,
    AssessmentAvailability,
    AssessmentObservation,
    CampExposure,
    CampPredictionRow,
    CriterionTrial,
    InformationLeakageError,
    PlannedExposure,
    select_camp_baseline,
    validate_target_time,
)

GATE7_OBSERVATION_SCHEMA_V1 = "gate7_public_observation_v1"
GATE7_FIXTURE_GENERATOR_V1 = "oss_gate7_observation_fixture_v1"
GATE7_FIXTURE_DATASET_V1 = "oss_gate7_observation_integration_v1"
GATE7_FIXTURE_SEED_V1 = 20261024
_ORIGIN_FIELDS: frozenset[str] = frozenset(
    (
        "participant_key",
        "origin_id",
        "available_at_origin_hours",
        "assessment_history",
        "exposure_history",
        "index_exposure",
        "known_plan",
    )
)


def _finite(value: object) -> float:
    if type(value) not in (float, int) or not math.isfinite(cast(float, value)):
        raise ValueError("observation values must be finite numbers, never booleans")
    return float(cast(float, value))


def _duration(event: CampExposure | PlannedExposure) -> None:
    if type(event.components) is not tuple or len(event.components) != 1:
        raise ValueError("observation v1 requires exactly one duration component per event")
    component = event.components[0]
    if type(component) is not ExposureComponent or (
        component.name != "duration_minutes"
        or component.units != "minutes"
        or component.observed is not True
        or component.day_mask is not True
        or component.event_mask is not True
        or component.source != "public"
    ):
        raise ValueError("duration must be observed, unmasked public minutes")
    if _finite(component.value) < 0:
        raise ValueError("duration minutes must be nonnegative")


@dataclass(frozen=True, slots=True)
class Gate7OriginObservation:
    """Complete public snapshot; availability is when its last datum became known.

    Every assessment contains three valid criterion trials in N/kg, m/s and m.
    Summaries are arithmetic means; baseline uses the two latest qualifying means.
    No labels, realized future events or target assessments belong in this schema.
    """

    participant_key: str
    origin_id: str
    available_at_origin_hours: float
    assessment_history: tuple[AssessmentObservation, ...]
    exposure_history: tuple[CampExposure, ...]
    index_exposure: CampExposure
    known_plan: tuple[PlannedExposure, ...]

    def __post_init__(self) -> None:
        if any(
            type(key) is not str or not key.strip()
            for key in (self.participant_key, self.origin_id)
        ):
            raise ValueError("nonempty participant and origin keys are required")
        if _finite(self.available_at_origin_hours) > 0:
            raise InformationLeakageError("the complete snapshot must be available at origin")
        if type(self.assessment_history) is not tuple or len(self.assessment_history) != 4:
            raise ValueError("exactly four assessments are required; no padding")
        for item in self.assessment_history:
            if type(item) is not AssessmentObservation:
                raise TypeError("assessment history requires AssessmentObservation values")
            if _finite(item.time_from_origin_hours) >= 0:
                raise InformationLeakageError("assessments must precede origin")
            if item.time_from_origin_hours > self.available_at_origin_hours:
                raise InformationLeakageError("assessment occurs after snapshot availability")
            if item.availability is not AssessmentAvailability.VALID:
                raise ValueError("all four assessments must be valid")
            if type(item.trials) is not tuple or len(item.trials) != 3:
                raise ValueError("each assessment requires exactly three valid trials")
            for trial in item.trials:
                if type(trial) is not CriterionTrial:
                    raise TypeError("assessment trials must be CriterionTrial values")
                if any(
                    _finite(value) <= 0
                    for value in (trial.force_n_per_kg, trial.net_impulse_m_s, trial.depth_m)
                ):
                    raise ValueError("criterion force, impulse and depth must be positive")
        if (
            len({item.assessment_id for item in self.assessment_history}) != 4
            or len({item.time_from_origin_hours for item in self.assessment_history}) != 4
        ):
            raise ValueError("assessment ids and times must be distinct")
        if type(self.exposure_history) is not tuple or len(self.exposure_history) != 1:
            raise ValueError("exactly one prior exposure is required")
        prior = self.exposure_history[0]
        if type(prior) is not CampExposure or type(self.index_exposure) is not CampExposure:
            raise TypeError("prior and index exposures must be CampExposure values")
        if _finite(prior.time_from_origin_hours) >= 0:
            raise InformationLeakageError("prior exposure must precede origin")
        if prior.time_from_origin_hours > self.available_at_origin_hours:
            raise InformationLeakageError("prior exposure occurs after snapshot availability")
        if _finite(self.index_exposure.time_from_origin_hours) != 0:
            raise ValueError("index exposure must occur at zero hours")
        if type(self.known_plan) is not tuple or len(self.known_plan) != 2:
            raise ValueError("complete origin plan requires the 48 and 120 hour events")
        if any(type(event) is not PlannedExposure for event in self.known_plan):
            raise TypeError("known plans require PlannedExposure values")
        if sorted(_finite(event.time_from_origin_hours) for event in self.known_plan) != [48, 120]:
            raise ValueError("known plan times must be 48 and 120 hours")
        if any(event.known_at_origin is not True for event in self.known_plan):
            raise InformationLeakageError("plans must be known at origin")
        events = (prior, self.index_exposure, *self.known_plan)
        if len({event.event_id for event in events}) != 4:
            raise ValueError("event ids must be distinct within an origin")
        for event in events:
            _duration(event)
        select_camp_baseline(self.assessment_history)


def gate7_origin_from_mapping(values: Mapping[str, object]) -> Gate7OriginObservation:
    """Ingest typed public fields only, with a closed schema like CampPredictionRow."""
    if frozenset(values) != _ORIGIN_FIELDS:
        raise InformationLeakageError("origin fields must match the label-free observation schema")
    return Gate7OriginObservation(
        cast(str, values["participant_key"]),
        cast(str, values["origin_id"]),
        _finite(values["available_at_origin_hours"]),
        cast(tuple[AssessmentObservation, ...], values["assessment_history"]),
        cast(tuple[CampExposure, ...], values["exposure_history"]),
        cast(CampExposure, values["index_exposure"]),
        cast(tuple[PlannedExposure, ...], values["known_plan"]),
    )


def gate7_observation_payload_v1(
    source_identity: str, origins: tuple[Gate7OriginObservation, ...]
) -> bytes:
    """Canonical UTF-8 JSON: schema, identity, origin-id order; no NaN or whitespace."""
    return json.dumps(
        [
            GATE7_OBSERVATION_SCHEMA_V1,
            source_identity,
            [asdict(origin) for origin in sorted(origins, key=lambda origin: origin.origin_id)],
        ],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class Gate7ObservationBuilderV1:
    """Application-owned authority, reused unchanged across horizons and calls.

    Configure from independently authorized public observations. Prediction calls
    select an existing origin; they cannot submit replacement observations/sources.
    The routine source remains separately pinned, never derived from a query.
    """

    source_identity: str
    origins: tuple[Gate7OriginObservation, ...]
    expected_observations_sha256: str
    routine_source: Gate7RoutineSource

    def __post_init__(self) -> None:
        if type(self.source_identity) is not str or not self.source_identity.strip():
            raise ValueError("an independent observation source identity is required")
        if type(self.origins) is not tuple or not self.origins:
            raise ValueError("a nonempty immutable origin collection is required")
        if any(type(origin) is not Gate7OriginObservation for origin in self.origins):
            raise TypeError("source requires Gate7OriginObservation values")
        if len({origin.origin_id for origin in self.origins}) != len(self.origins):
            raise ValueError("origin ids must be unique across participants")
        payload = gate7_observation_payload_v1(self.source_identity, self.origins)
        if sha256(payload).hexdigest() != self.expected_observations_sha256:
            raise ValueError("observation source SHA-256 mismatch")
        if type(self.routine_source) is not Gate7RoutineSource:
            raise TypeError("a separately pinned Gate7RoutineSource is required")
        records = {record.origin_id: record for record in self.routine_source.records()}
        if set(records) != {origin.origin_id for origin in self.origins}:
            raise ValueError("routine source must match exactly the observation origins")
        if any(
            record.available_at_origin_hours is None or record.available_at_origin_hours > 0
            for record in records.values()
        ):
            raise InformationLeakageError("routine metadata must be available at origin")

    def build(
        self,
        origin_id: str,
        horizon: ForecastHorizon,
        target_time_hours: float | None = None,
    ) -> Gate7CampPredictionInput:
        if type(horizon) is not ForecastHorizon or horizon not in HORIZON_TIMES_HOURS:
            raise ValueError("Gate7 accepts only H72 and D7 queries")
        target = (
            HORIZON_TIMES_HOURS[horizon]
            if target_time_hours is None
            else _finite(target_time_hours)
        )
        validate_target_time(horizon, target)
        origin = next((item for item in self.origins if item.origin_id == origin_id), None)
        if origin is None:
            raise ValueError("origin is absent from the pinned observation source")
        routine = next(
            item for item in self.routine_source.records() if item.origin_id == origin_id
        )
        row = CampPredictionRow(
            origin.participant_key,
            origin.origin_id,
            f"{origin_id}/{horizon.label}/{target:g}",
            horizon,
            target,
            select_camp_baseline(origin.assessment_history),
            tuple(sorted(origin.assessment_history, key=lambda item: item.time_from_origin_hours)),
            origin.exposure_history,
            origin.index_exposure,
            tuple(
                sorted(
                    (item for item in origin.known_plan if item.time_from_origin_hours <= target),
                    key=lambda item: item.time_from_origin_hours,
                )
            ),
        )
        return Gate7CampPredictionInput(row, routine)

    def inputs(self) -> tuple[Gate7CampPredictionInput, ...]:
        """Frozen order: origin id ascending, then H72, D7."""
        return tuple(
            self.build(origin.origin_id, horizon)
            for origin in sorted(self.origins, key=lambda item: item.origin_id)
            for horizon in (ForecastHorizon.H72, ForecastHorizon.D7)
        )

    def matrix(self) -> NDArray[np.float64]:
        attempt = project_gate7_v1(self.inputs(), routine_source=self.routine_source)
        if attempt.matrix is None:
            raise ValueError(f"source cannot project to Gate7: {attempt.missing_authority}")
        return attempt.matrix


def _draw(key: str, low: float, high: float) -> float:
    digest = sha256(f"{GATE7_FIXTURE_GENERATOR_V1}/{GATE7_FIXTURE_SEED_V1}/{key}".encode()).digest()
    return round(low + (high - low) * (int.from_bytes(digest[:8], "big") / 2**64), 9)


def generate_gate7_fixture_v1(split: str = "training") -> Gate7ObservationBuilderV1:
    """New predictor-only fixture, never historical data or a biological simulation.

    Four training/two validation participants, two origins each. Semantic SHA-256
    draws isolate split, participant, origin, session and trial. Group keys are
    opaque and disjoint across splits; no targets or model/scaler fitting occurs.
    """
    if split not in ("training", "public_validation"):
        raise ValueError("fixture split must be training or public_validation")
    origins: list[Gate7OriginObservation] = []
    routine_records: list[list[object]] = []
    for participant in range(4 if split == "training" else 2):
        key = f"{split}/{participant}"
        participant_key = sha256(f"{GATE7_FIXTURE_DATASET_V1}/{key}".encode()).hexdigest()[:24]
        force, impulse, depth = (
            _draw(f"{key}/{name}", low, high)
            for name, low, high in (("force", 20, 28), ("impulse", 2.2, 3.2), ("depth", 0.25, 0.45))
        )
        for index in range(2):
            origin_key = f"{key}/{index}"
            origin_id = sha256(f"{GATE7_FIXTURE_DATASET_V1}/{origin_key}".encode()).hexdigest()[:24]
            assessments: list[AssessmentObservation] = []
            for time in (-240.0, -72.0, -48.0, -24.0):
                session_key = f"{origin_key}/{time}"
                session_force = force + _draw(f"{session_key}/session-force", -0.3, 0.3)
                session_impulse = impulse + _draw(f"{session_key}/session-impulse", -0.03, 0.03)
                trials = tuple(
                    CriterionTrial(
                        session_force + _draw(f"{session_key}/{trial}/force", -0.1, 0.1),
                        session_impulse + _draw(f"{session_key}/{trial}/impulse", -0.01, 0.01),
                        depth,
                    )
                    for trial in range(3)
                )
                assessments.append(
                    AssessmentObservation(
                        f"{origin_id}/assessment/{time:g}",
                        time,
                        AssessmentAvailability.VALID,
                        trials,
                    )
                )
            components = tuple(
                (
                    ExposureComponent(
                        "duration_minutes",
                        _draw(f"{origin_key}/duration/{time}", 40, 120),
                        "minutes",
                        100.0,
                    ),
                )
                for time in (-96, 0, 48, 120)
            )
            origins.append(
                Gate7OriginObservation(
                    participant_key,
                    origin_id,
                    0.0,
                    tuple(assessments),
                    (CampExposure(f"{origin_id}/prior", -96, "training", components[0]),),
                    CampExposure(f"{origin_id}/index", 0, "match", components[1]),
                    tuple(
                        PlannedExposure(f"{origin_id}/plan/{time}", time, "training", component)
                        for time, component in zip((48, 120), components[2:], strict=True)
                    ),
                )
            )
            states = tuple(Gate7RoutineState)
            state = states[int(_draw(f"{origin_key}/routine", 0, 5)) % len(states)]
            routine_records.append(
                [origin_id, state is not Gate7RoutineState.UNSCHEDULED, state.value, 0.0]
            )
    payload = json.dumps(sorted(routine_records), separators=(",", ":")).encode()
    routine_source = Gate7RoutineSource(payload, sha256(payload).hexdigest())
    identity = f"{GATE7_FIXTURE_DATASET_V1}/{split}"
    observations = tuple(sorted(origins, key=lambda origin: origin.origin_id))
    return Gate7ObservationBuilderV1(
        identity,
        observations,
        sha256(gate7_observation_payload_v1(identity, observations)).hexdigest(),
        routine_source,
    )


def fixture_receipt_v1(split: str) -> dict[str, object]:
    builder = generate_gate7_fixture_v1(split)
    matrix = builder.matrix()
    return {
        "generator": GATE7_FIXTURE_GENERATOR_V1,
        "seed": GATE7_FIXTURE_SEED_V1,
        "schema": GATE7_OBSERVATION_SCHEMA_V1,
        "source_identity": builder.source_identity,
        "historical_replay": False,
        "observation_sha256": builder.expected_observations_sha256,
        "routine_sha256": builder.routine_source.expected_sha256,
        "matrix_sha256": sha256(matrix.astype("<f8").tobytes(order="C")).hexdigest(),
        "shape": list(matrix.shape),
        "dtype": str(matrix.dtype),
        "feature_names": GATE7_FEATURE_NAMES,
        "feature_units": tuple(unit.value for unit in GATE7_FEATURE_UNITS),
        "ordering": "origin_id ascending; H72 then D7; matrix little-endian float64 C order",
    }


if __name__ == "__main__":
    print(
        json.dumps(
            [fixture_receipt_v1(split) for split in ("training", "public_validation")],
            sort_keys=True,
            indent=2,
        )
    )
