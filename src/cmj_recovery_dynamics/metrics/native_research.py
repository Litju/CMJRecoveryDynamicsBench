"""Versioned native research contract; it does not establish dataset authority.

This source-contract schema is distinct from generic outcomes and historical
calibrated scoring. Final historical split materialization remains unresolved.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from cmj_recovery_dynamics.metrics.evaluation_readiness import validate_participant_splits
from cmj_recovery_dynamics.metrics.scoring import MetricInputError, _rmse  # pyright: ignore[reportPrivateUsage]


class NativeTarget(StrEnum):
    FORCE = "relative_mean_concentric_force"
    IMPULSE = "relative_concentric_net_impulse"


class NativeHorizon(StrEnum):
    H72 = "H72"
    D7 = "D7"


@dataclass(frozen=True, slots=True)
class NativeSourceContract:
    version: str
    target_order: tuple[NativeTarget, NativeTarget]
    units: tuple[str, str]
    force_measurement: str
    impulse_measurement: str
    criterion: str
    baseline: str
    windows: tuple[tuple[NativeHorizon, int, int, int], ...]
    scope: str


NATIVE_SOURCE_V1: Final = NativeSourceContract(
    version="gate7_native_evaluation_v1",
    target_order=(NativeTarget.FORCE, NativeTarget.IMPULSE),
    units=("N/kg", "m/s"),
    force_measurement="concentric time-mean gross vertical force / explicit system mass",
    impulse_measurement=(
        "concentric integral of (vertical force - system mass * gravity) / system mass"
    ),
    criterion="arithmetic mean of three valid trials",
    baseline="arithmetic mean of two latest valid qualifying assessments 24–240 hours pre-origin",
    windows=((NativeHorizon.H72, 72, 66, 78), (NativeHorizon.D7, 168, 156, 180)),
    scope="authenticated source contract; final historical split materialization unresolved",
)


def _identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value


@dataclass(frozen=True, slots=True)
class NativeAuthority:
    """Operator-supplied source identity; matching a pin is not proof of permission."""

    reference: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class NativeQuery:
    dataset: str
    participant: str
    origin: str
    query: str
    input_identity: str
    horizon: NativeHorizon
    baseline_assessment_ids: tuple[str, str]
    baseline_offsets_hours: tuple[float, float]
    baseline_valid_trial_counts: tuple[int, int]


@dataclass(frozen=True, slots=True)
class NativePrediction:
    query: NativeQuery
    target: NativeTarget
    unit: str
    value: float


@dataclass(frozen=True, slots=True)
class NativeObservation:
    query: NativeQuery
    target: NativeTarget
    unit: str
    value: float
    observed_at_hours: float
    valid_trial_count: int
    assessment_identity: str


@dataclass(frozen=True, slots=True)
class NativeCellRMSE:
    target: NativeTarget
    horizon: NativeHorizon
    unit: str
    row_count: int
    rmse: float


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _query(query: NativeQuery) -> None:
    if type(query) is not NativeQuery or not all(
        _identifier(item)
        for item in (
            query.dataset,
            query.participant,
            query.origin,
            query.query,
            query.input_identity,
        )
    ):
        raise ValueError("invalid native query identity")
    if type(query.horizon) is not NativeHorizon:
        raise ValueError("invalid native horizon")
    ids = query.baseline_assessment_ids
    offsets = query.baseline_offsets_hours
    if (
        type(ids) is not tuple
        or len(ids) != 2
        or not all(_identifier(item) for item in ids)
        or len(set(ids)) != 2
        or type(offsets) is not tuple
        or len(offsets) != 2
        or not all(_finite(item) and -240 <= item <= -24 for item in offsets)
        or len(set(offsets)) != 2
        or query.baseline_valid_trial_counts != (3, 3)
        or any(type(count) is not int for count in query.baseline_valid_trial_counts)
    ):
        raise ValueError(
            "native baseline requires two distinct pre-origin assessments in 24–240 hours"
        )


def synthetic_native_rmse_v1(
    predictions: Sequence[NativePrediction],
    observations: Sequence[NativeObservation],
    *,
    source_contract: NativeSourceContract,
    source_authority: NativeAuthority,
    expected_authority: NativeAuthority,
    participant_splits: Mapping[str, Sequence[object]],
    dataset_kind: str,
) -> tuple[NativeCellRMSE, ...]:
    """Calculate native-unit RMSE for explicitly synthetic test data only.

    The caller must independently authenticate the source pins and synthetic
    data: this structural check cannot prove either or authorize empirical use.
    It is not a historical calibrated benchmark score.
    """
    if dataset_kind != "synthetic":
        raise ValueError("only synthetic test data are supported")
    if (
        type(source_contract) is not NativeSourceContract
        or source_contract != NATIVE_SOURCE_V1
        or any(type(target) is not NativeTarget for target in source_contract.target_order)
        or any(type(window[0]) is not NativeHorizon for window in source_contract.windows)
    ):
        raise ValueError("native source contract mismatch")
    if (
        type(source_authority) is not NativeAuthority
        or type(expected_authority) is not NativeAuthority
        or source_authority != expected_authority
        or not _identifier(source_authority.reference)
        or type(source_authority.source_sha256) is not str
        or re.fullmatch(r"[a-f0-9]{64}", source_authority.source_sha256) is None
    ):
        raise ValueError("independently pinned source authority required")
    validate_participant_splits(participant_splits)
    test_participants = set(participant_splits["test"])
    units = dict(zip(NATIVE_SOURCE_V1.target_order, NATIVE_SOURCE_V1.units, strict=True))
    windows = {h: (lo, hi) for h, _, lo, hi in NATIVE_SOURCE_V1.windows}
    pred: dict[tuple[str, NativeTarget], NativePrediction] = {}
    obs: dict[tuple[str, NativeTarget], NativeObservation] = {}
    query_by_id: dict[str, NativeQuery] = {}
    query_by_origin_horizon: dict[tuple[str, str, NativeHorizon], str] = {}
    participant_by_origin: dict[tuple[str, str], str] = {}

    def record_key(row: NativePrediction | NativeObservation) -> tuple[str, NativeTarget]:
        _query(row.query)
        if row.query.participant not in test_participants:
            raise ValueError("query participant is not in the test split")
        if type(row.target) is not NativeTarget or row.unit != units[row.target]:
            raise ValueError("native target or unit mismatch")
        if not _finite(row.value):
            raise ValueError("native values must be finite numbers")
        prior = query_by_id.setdefault(row.query.query, row.query)
        if prior != row.query:
            raise ValueError("query identity or input pairing mismatch")
        origin_key = (row.query.dataset, row.query.origin)
        if (
            participant_by_origin.setdefault(origin_key, row.query.participant)
            != row.query.participant
        ):
            raise ValueError("origin participant identity mismatch")
        horizon_key = (*origin_key, row.query.horizon)
        if query_by_origin_horizon.setdefault(horizon_key, row.query.query) != row.query.query:
            raise ValueError("duplicate origin and horizon query")
        return row.query.query, row.target

    for row in predictions:
        if type(row) is not NativePrediction:
            raise ValueError("wrong native record type")
        key = record_key(row)
        if key in pred:
            raise ValueError("duplicate native query target")
        pred[key] = row
    for row in observations:
        if type(row) is not NativeObservation:
            raise ValueError("wrong native record type")
        key = record_key(row)
        if key in obs:
            raise ValueError("duplicate native query target")
        obs[key] = row
    if not pred or set(pred) != set(obs):
        raise ValueError("prediction and observation query targets must pair exactly")
    for query in query_by_id.values():
        if any((query.query, target) not in pred for target in NATIVE_SOURCE_V1.target_order):
            raise ValueError("each query requires both native targets")
        times = {
            obs[(query.query, target)].observed_at_hours for target in NATIVE_SOURCE_V1.target_order
        }
        assessments = {
            obs[(query.query, target)].assessment_identity
            for target in NATIVE_SOURCE_V1.target_order
        }
        if len(times) != 1 or len(assessments) != 1 or not all(map(_identifier, assessments)):
            raise ValueError("native target measurements must share an assessment")
    for row in obs.values():
        lo, hi = windows[row.query.horizon]
        if not _finite(row.observed_at_hours) or not lo <= row.observed_at_hours <= hi:
            raise ValueError("native observation falls outside its target window")
        if type(row.valid_trial_count) is not int or row.valid_trial_count != 3:
            raise ValueError("native criterion requires three valid trials")
    if len({q.dataset for q in query_by_id.values()}) != 1:
        raise ValueError("native evaluation requires one authenticated dataset identity")
    result: list[NativeCellRMSE] = []
    for horizon in NativeHorizon:
        for target in NATIVE_SOURCE_V1.target_order:
            keys = sorted(
                k
                for k, row in pred.items()
                if row.query.horizon is horizon and row.target is target
            )
            if not keys:
                raise ValueError("all four native target/horizon cells are required")
            try:
                error = _rmse(tuple(pred[k].value for k in keys), tuple(obs[k].value for k in keys))
            except MetricInputError as exc:
                raise ValueError("native RMSE is outside its finite range") from exc
            result.append(NativeCellRMSE(target, horizon, units[target], len(keys), error))
    return tuple(result)
