"""Fail-closed native dataset inspection and aggregate-only steward assessment.

Evidence declarations and separately pinned review records are not proof of
provenance, consent or independence. Empirical execution remains unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    Gate7ExposureFeature,
    Gate7HistoryAssessment,
    Gate7PlanFeature,
    Gate7PublicFeatureRow,
    Gate7RoutineAssessment,
    Gate7RoutineState,
    Gate7RoutineTemporalAuthority,
    project_gate7_historical_v1,
)

PREFLIGHT_VERSION = "native_dataset_preflight_v1"
REVIEW_STAGES = (
    "measurement_authority",
    "participant_independence",
    "data_use_authorization",
    "result_generation_authorization",
    "result_disclosure_authorization",
)
MECHANICS = {
    "force": "time_mean_gross_concentric_force_per_system_mass",
    "impulse": "concentric_net_impulse_per_system_mass",
    "events": "source_supplied_onset_and_takeoff",
    "integration": "interpolated_boundaries_in_contact_trapezoid",
    "criterion": "mean_three_valid_trials",
}
TARGETS = {"relative_mean_concentric_force": "N/kg", "relative_concentric_net_impulse": "m/s"}
WINDOWS = {"H72": (72.0, 66.0, 78.0), "D7": (168.0, 156.0, 180.0)}


@dataclass(frozen=True)
class AdmissionIssue:
    code: str
    explanation: str


@dataclass(frozen=True)
class PreflightResult:
    version: str
    stages: dict[str, bool]
    issues: tuple[AdmissionIssue, ...]
    eligible: bool


class AdmissionError(ValueError):
    def __init__(self, code: str, explanation: str) -> None:
        super().__init__(explanation)
        self.issue = AdmissionIssue(code, explanation)


def _require(condition: bool, code: str, explanation: str) -> None:
    if not condition:
        raise AdmissionError(code, explanation)


def _id(value: object) -> str:
    _require(
        isinstance(value, str) and bool(value) and value.strip() == value,
        "IDENTITY_INVALID",
        "Identities must be nonempty canonical strings.",
    )
    return cast(str, value)


def _number(value: object) -> float:
    _require(
        type(value) in (int, float) and math.isfinite(cast(float, value)),
        "VALUE_INVALID",
        "Numeric values must be finite; boolean values are not measurements.",
    )
    return float(cast(float, value))


def _pin(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _canonical(identity: object, aliases: Mapping[str, Any]) -> str:
    current = _id(identity)
    visited: set[str] = set()
    while current in aliases:
        _require(current not in visited, "ALIAS_CYCLE", "Participant alias graph contains a cycle.")
        visited.add(current)
        current = _id(aliases[current])
    return current


def _assessment_values(assessment: Mapping[str, Any]) -> tuple[float, float, float]:
    _require(assessment["valid"] is True, "TRIAL_CRITERION", "A selected assessment must be valid.")
    trials = assessment["trials"]
    _require(
        len(trials) == 3 and all(t["valid"] is True for t in trials),
        "TRIAL_CRITERION",
        "Exactly three selected trials, all valid, are required.",
    )
    _require(
        len({_id(trial["id"]) for trial in assessment["trials"]}) == len(assessment["trials"]),
        "DUPLICATE_TRIAL",
        "Trial identities must be distinct within an assessment.",
    )
    _require(
        _number(assessment["system_mass_kg"]) > 0,
        "SYSTEM_MASS",
        "A positive explicit accelerated system mass is required.",
    )
    _require(
        assessment["mechanics"] == MECHANICS and _pin(assessment["provenance_sha256"]),
        "MECHANICS_AUTHORITY",
        "Frozen native mechanics and pinned assessment provenance are required.",
    )
    from cmj_recovery_dynamics.observations.native_mechanics import native_force_metrics_v1

    for trial in trials:
        signal = trial["force_time"]
        _require(
            _pin(signal["sop_sha256"]) and _pin(signal["calibration_sha256"]),
            "MECHANICS_AUTHORITY",
            "Pinned empirical SOP and calibration evidence are required.",
        )
        try:
            metrics = native_force_metrics_v1(
                signal["timestamps_s"],
                signal["force_n"],
                system_mass_kg=_number(assessment["system_mass_kg"]),
                gravity_m_s2=_number(signal["gravity_m_s2"]),
                concentric_onset_s=_number(signal["concentric_onset_s"]),
                takeoff_s=_number(signal["takeoff_s"]),
            )
        except ValueError as exc:
            raise AdmissionError(
                "FORCE_TIME_EVENTS", "Force/time support, event ordering or gravity is invalid."
            ) from exc
        _require(
            math.isclose(
                _number(trial["force_n_per_kg"]),
                metrics.force_n_per_kg,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
            and math.isclose(
                _number(trial["impulse_m_per_s"]),
                metrics.net_impulse_m_per_s,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
            "FORCE_TIME_LINEAGE",
            "Trial native metrics do not match the supplied calibrated force-time evidence.",
        )
    return cast(
        tuple[float, float, float],
        tuple(
            math.fsum(_number(trial[field]) for trial in trials) / 3
            for field in ("force_n_per_kg", "impulse_m_per_s", "depth_m")
        ),
    )


def _public_row(
    query: Mapping[str, Any], assessments: Mapping[str, Mapping[str, Any]]
) -> Gate7PublicFeatureRow:
    origin = _number(query["origin_h"])
    horizon = query["horizon"]
    nominal, low, high = WINDOWS[horizon]
    baseline = [assessments[x] for x in query["baseline_assessment_ids"]]
    values = [_assessment_values(x) for x in baseline]
    routine = query["routine"]
    return Gate7PublicFeatureRow(
        (values[0][0] + values[1][0]) / 2,
        (values[0][1] + values[1][1]) / 2,
        ForecastHorizon.H72 if horizon == "H72" else ForecastHorizon.D7,
        nominal,
        (low, high),
        tuple(
            Gate7HistoryAssessment(
                _number(assessments[x]["time_h"]) - origin, *_assessment_values(assessments[x])
            )
            for x in query["history_assessment_ids"]
        ),
        tuple(
            Gate7ExposureFeature(_number(x["time_h"]) - origin, _number(x["duration_minutes"]))
            for x in query["history_exposures"]
        ),
        Gate7ExposureFeature(0.0, _number(query["index_exposure"]["duration_minutes"])),
        tuple(
            Gate7PlanFeature(_number(x["time_h"]) - origin, _number(x["duration_minutes"]), True)
            for x in query["plans"]
        ),
        Gate7RoutineAssessment(
            routine["scheduled"],
            Gate7RoutineState(routine["state"]),
            Gate7RoutineTemporalAuthority.ORIGIN_KEYED_PUBLIC_STATE,
            query["origin_id"],
            routine["source_sha256"],
            _number(routine["available_at_h"]) - origin,
        ),
    )


def _structural(payload: Mapping[str, Any]) -> None:
    _id(payload["dataset_id"])
    _require(payload["version"] == PREFLIGHT_VERSION, "VERSION", "Unsupported dataset schema.")
    aliases = payload["aliases"]
    for alias in aliases:
        _canonical(alias, aliases)
    splits = payload["participant_splits"]
    _require(set(splits) == {"train", "validation", "test"}, "SPLIT_KEYS", "Three splits required.")
    seen: set[str] = set()
    for group in splits.values():
        canonical = [_canonical(x, aliases) for x in group]
        _require(bool(canonical), "EMPTY_SPLIT", "Each participant split must be nonempty.")
        _require(
            len(set(canonical)) == len(canonical),
            "DUPLICATE_PARTICIPANT",
            "Duplicate linked groups.",
        )
        _require(
            not seen.intersection(canonical),
            "PARTICIPANT_OVERLAP",
            "Linked participant splits overlap.",
        )
        seen.update(canonical)
    preprocessing = payload["preprocessing"]
    _require(
        preprocessing["frozen"] is True
        and preprocessing["training_only"] is True
        and _pin(preprocessing["sha256"])
        and bool(_id(preprocessing["reference"])),
        "PREPROCESSING",
        "Run-bound frozen training-only preprocessing must be identified.",
    )
    _require(
        payload["missingness"] == [] and payload["support_mismatches"] == [],
        "SUPPORT_MISSINGNESS",
        "Unresolved missingness/support mismatches require refusal.",
    )
    assessment_rows = payload["assessments"]
    assessments: dict[str, Mapping[str, Any]] = {}
    trial_ids: set[str] = set()
    for assessment in assessment_rows:
        identity = _id(assessment["id"])
        _require(
            identity not in assessments, "DUPLICATE_ASSESSMENT", "Repeated assessment identity."
        )
        assessments[identity] = assessment
        _require(
            _canonical(assessment["participant"], aliases) in seen,
            "PARTICIPANT_LINK",
            "Assessment participant absent from declared groups.",
        )
        _number(assessment["time_h"])
        _number(assessment["available_at_h"])
        _require(
            _number(assessment["available_at_h"]) >= _number(assessment["time_h"]),
            "AVAILABILITY_ORDER",
            "Assessment cannot be available before it was measured.",
        )
        _require(
            type(assessment["valid"]) is bool
            and all(type(trial["valid"]) is bool for trial in assessment["trials"]),
            "TRIAL_CRITERION",
            "Assessment and trial validity must be explicit booleans.",
        )
        for trial in assessment["trials"]:
            trial_id = _id(trial["id"])
            _require(
                trial_id not in trial_ids,
                "DUPLICATE_TRIAL",
                "A trial cannot be reused across assessments.",
            )
            trial_ids.add(trial_id)
        if assessment["valid"] is True:
            _assessment_values(assessment)
    queries = payload["queries"]
    _require(bool(queries), "EMPTY_DATASET", "At least one complete origin is required.")
    query_ids: set[str] = set()
    input_ids: set[str] = set()
    origin_owners: dict[str, str] = {}
    origins: dict[tuple[str, str], dict[str, Any]] = {}
    fingerprints: list[tuple[str, str, np.ndarray[Any, Any]]] = []
    for query in queries:
        qid, iid, oid = (_id(query[k]) for k in ("id", "input_id", "origin_id"))
        participant = _canonical(query["participant"], aliases)
        _require(
            participant in seen,
            "PARTICIPANT_LINK",
            "Query participant absent from declared groups.",
        )
        _require(
            qid not in query_ids and iid not in input_ids,
            "DUPLICATE_QUERY",
            "Repeated query or input identity.",
        )
        query_ids.add(qid)
        input_ids.add(iid)
        _require(
            origin_owners.setdefault(oid, participant) == participant,
            "ORIGIN_LINK",
            "Origin linked to inconsistent participants.",
        )
        origin = _number(query["origin_h"])
        horizon = query["horizon"]
        _require(horizon in WINDOWS, "HORIZON", "Only H72 and D7 are supported.")
        nominal, low, high = WINDOWS[horizon]
        group = origins.setdefault((participant, oid), {})
        _require(horizon not in group, "DUPLICATE_QUERY", "Repeated origin/horizon query.")
        group[horizon] = query
        _require(
            query["units"] == TARGETS,
            "TARGET_UNITS",
            "Native target keys and units must match exactly.",
        )
        ids = query["history_assessment_ids"]
        _require(
            len(ids) == len(set(ids)) == 4,
            "HISTORY_COUNT",
            "Four distinct history assessments required.",
        )
        selected_ids = [*ids, *query["baseline_assessment_ids"], query["target_assessment_id"]]
        _require(
            all(x in assessments for x in selected_ids),
            "ASSESSMENT_LINK",
            "Selected assessment does not exist.",
        )
        _require(
            all(
                _canonical(assessments[x]["participant"], aliases) == participant
                for x in selected_ids
            ),
            "PARTICIPANT_LINK",
            "Assessment/query participant mismatch.",
        )
        history_times = [_number(assessments[x]["time_h"]) for x in ids]
        _require(
            history_times == sorted(set(history_times)) and all(x < origin for x in history_times),
            "FUTURE_HISTORY",
            "History must be chronological, distinct and strictly pre-origin.",
        )
        _require(
            all(_number(assessments[x]["available_at_h"]) <= origin for x in ids),
            "FUTURE_AVAILABILITY",
            "History was not available at prediction origin.",
        )
        _require(
            _number(payload["history_complete_through_h"][participant]) >= origin,
            "INCOMPLETE_HISTORY",
            "Full qualifying assessment history must be declared through origin.",
        )
        qualifying = sorted(
            (
                a
                for a in assessments.values()
                if _canonical(a["participant"], aliases) == participant
                and a["valid"] is True
                and 24 <= origin - _number(a["time_h"]) <= 240
            ),
            key=lambda a: _number(a["time_h"]),
        )
        _require(
            len({_number(a["time_h"]) for a in qualifying}) == len(qualifying),
            "BASELINE_TIME_TIE",
            "Qualifying assessment timestamps are ambiguous; adjudicate tied records.",
        )
        _require(
            len(qualifying) >= 2
            and query["baseline_assessment_ids"] == [a["id"] for a in qualifying[-2:]],
            "BASELINE_LATEST",
            "Baseline must identify the two latest qualifying 24–240h assessments.",
        )
        _require(
            all(_number(a["available_at_h"]) <= origin for a in qualifying[-2:]),
            "FUTURE_AVAILABILITY",
            "Baseline unavailable at origin.",
        )
        target = assessments[query["target_assessment_id"]]
        _require(
            target["id"] not in query["baseline_assessment_ids"]
            and low <= _number(target["time_h"]) - origin <= high,
            "TARGET_WINDOW",
            "Target assessment must lie in its native window and differ from baseline.",
        )
        _require(
            _number(query["target_time_hours"]) == nominal,
            "HORIZON",
            "Nominal query time must match horizon.",
        )
        for exposure in [*query["history_exposures"], query["index_exposure"], *query["plans"]]:
            _require(
                _number(exposure["known_at_h"]) <= origin
                and _number(exposure["duration_minutes"]) >= 0,
                "FUTURE_PLAN",
                "Exposure durations/plans must be available at origin.",
            )
        _require(
            len(query["history_exposures"]) == 1
            and _number(query["history_exposures"][0]["time_h"]) < origin,
            "EXPOSURE_HISTORY",
            "One strictly pre-origin historical exposure required.",
        )
        _require(
            _number(query["index_exposure"]["time_h"]) == origin,
            "INDEX_EXPOSURE",
            "Index exposure time must match origin.",
        )
        _require(
            len(query["plans"]) in (2, 3)
            and all(origin <= _number(x["time_h"]) <= origin + nominal for x in query["plans"]),
            "PLAN_SHAPE",
            "Two or three origin-known query-specific plans required.",
        )
        routine = query["routine"]
        _require(
            type(routine["scheduled"]) is bool
            and routine["origin_id"] == oid
            and _number(routine["available_at_h"]) <= origin
            and routine["source_sha256"] == payload["routine_source_sha256"]
            and _pin(routine["source_sha256"]),
            "ROUTINE_AUTHORITY",
            "Routine state must match an origin-keyed, pinned pre-origin record.",
        )
        row = _public_row(query, assessments)
        raw = np.asarray(query["raw_features"], dtype=np.float64)
        tokens = np.asarray(query["history_tokens"], dtype=np.float64)
        _require(
            raw.shape == (39,) and bool(np.isfinite(raw).all()),
            "RAW_FEATURES",
            "All 39 raw input components must be finite.",
        )
        for value in query["raw_features"]:
            _number(value)
        _require(
            tokens.shape == (4, 4) and np.array_equal(tokens.ravel(), raw[7:23]),
            "HISTORY_PAIRING",
            "Four history tokens must match raw columns and chronological order.",
        )
        _require(
            np.array_equal(raw, project_gate7_historical_v1((row,))[0]),
            "RAW_PAIRING",
            "Raw feature projection differs from authenticated source records.",
        )
        target_values = _assessment_values(target)
        baseline_values = [
            _assessment_values(assessments[x]) for x in query["baseline_assessment_ids"]
        ]
        expected_targets = [
            target_values[i] - (baseline_values[0][i] + baseline_values[1][i]) / 2 for i in range(2)
        ]
        _require(
            set(query["targets"]) == set(TARGETS),
            "TARGET_KEYS",
            "Both exact native target keys are required.",
        )
        _require(
            all(
                math.isclose(
                    _number(query["targets"][name]), expected_targets[i], rel_tol=0.0, abs_tol=1e-12
                )
                for i, name in enumerate(TARGETS)
            ),
            "TARGET_LINEAGE",
            "Native target arithmetic lineage differs from supplied assessment summaries.",
        )
        if any(index >= 6 for index in payload["candidate_indices"]):
            from cmj_recovery_dynamics.observations.native_mechanics import gate7_basis_v1

            basis = np.asarray(query["basis"], dtype=np.float64)
            _require(
                query["basis_source_sha256"] == payload["basis_source_sha256"]
                and _pin(query["basis_source_sha256"]),
                "BASIS_AUTHORITY",
                "Original basis construction authority must be pinned.",
            )
            _require(
                basis.shape == (5,)
                and bool(np.isfinite(basis).all())
                and np.allclose(basis, gate7_basis_v1(row), rtol=1e-12, atol=1e-12),
                "BASIS_PAIRING",
                "Five source-defined basis components must reproduce the same row.",
            )
        for prior_oid, prior_horizon, prior_raw in fingerprints:
            if (
                prior_oid != oid
                and prior_horizon == horizon
                and np.allclose(raw, prior_raw, rtol=0.0, atol=1e-8)
            ):
                raise AdmissionError(
                    "NEAR_DUPLICATE",
                    "Copied or near-duplicate query vectors need independent adjudication.",
                )
        fingerprints.append((oid, horizon, raw))
    for group in origins.values():
        _require(
            set(group) == set(WINDOWS),
            "INCOMPLETE_CELLS",
            "Each origin requires both horizons and both targets.",
        )
        a, b = group["H72"], group["D7"]
        _require(
            a["origin_h"] == b["origin_h"]
            and a["baseline_assessment_ids"] == b["baseline_assessment_ids"]
            and a["history_assessment_ids"] == b["history_assessment_ids"]
            and a["routine"] == b["routine"]
            and a["history_exposures"] == b["history_exposures"]
            and a["index_exposure"] == b["index_exposure"]
            and sorted(a["plans"], key=lambda x: x["time_h"])
            == sorted(
                (x for x in b["plans"] if x["time_h"] <= a["origin_h"] + 72),
                key=lambda x: x["time_h"],
            ),
            "ORIGIN_PAIRING",
            "Horizon queries must share origin, baseline, history and routine identities.",
        )


def dataset_manifest_sha256(payload: Mapping[str, object]) -> str:
    """Bind review decisions to every source, identity and value except reviews."""
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in payload.items() if k != "reviews"},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def validate_native_dataset(
    payload: object,
    *,
    metadata_only: bool = False,
    trusted_reviews: Mapping[str, str] | None = None,
) -> PreflightResult:
    """Inspect supplied records without scoring or authenticating real-world claims.

    Trusted review pins must be supplied independently of the dataset. They
    identify reviewed decisions, not automatic permission derived from fields.
    Empirical datasets can be inspected but never receive executable admission.
    """
    stages: dict[str, bool] = dict.fromkeys(("metadata", "structural", *REVIEW_STAGES), False)
    issues: list[AdmissionIssue] = []
    if not isinstance(payload, Mapping):
        return PreflightResult(
            PREFLIGHT_VERSION,
            stages,
            (AdmissionIssue("SCHEMA_INVALID", "Dataset must be an object."),),
            False,
        )
    data = cast(Mapping[str, Any], payload)
    try:
        _id(data["dataset_id"])
        _require(data["version"] == PREFLIGHT_VERSION, "VERSION", "Unsupported dataset schema.")
        _require(
            data["dataset_kind"] in ("synthetic", "empirical"),
            "DATASET_KIND",
            "Explicit dataset kind required.",
        )
        _require(
            bool(data["candidate_indices"])
            and all(type(x) is int and 0 <= x <= 8 for x in data["candidate_indices"]),
            "CANDIDATE",
            "Explicit candidate coverage from 0 through 8 required.",
        )
        _require(
            _pin(data["source_authority"]["sha256"])
            and bool(_id(data["source_authority"]["reference"])),
            "SOURCE_AUTHORITY",
            "Versioned native source identity and SHA-256 pin required.",
        )
        stages["metadata"] = True
        if metadata_only:
            return PreflightResult(PREFLIGHT_VERSION, stages, (), False)
        _structural(data)
        stages["structural"] = True
    except AdmissionError as exc:
        issues.append(exc.issue)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        issues.append(
            AdmissionIssue("SCHEMA_INVALID", "Required fields, types or dimensions are invalid.")
        )
    reviews = data.get("reviews", {})
    if not isinstance(reviews, Mapping):
        reviews = {}
    try:
        manifest_hash = dataset_manifest_sha256(data)
    except (TypeError, ValueError, OverflowError):
        manifest_hash = ""
    for stage in REVIEW_STAGES:
        review = cast(Mapping[str, Any], reviews).get(stage, {})
        if not isinstance(review, Mapping):
            review = {}
        review = cast(Mapping[str, Any], review)
        try:
            digest = hashlib.sha256(
                json.dumps(review, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
        except (TypeError, ValueError, OverflowError):
            digest = ""
        accepted = (
            bool(manifest_hash)
            and bool(digest)
            and review.get("decision") == "approved"
            and review.get("scope") == stage
            and review.get("dataset_sha256") == manifest_hash
            and isinstance(review.get("reference"), str)
            and bool(review.get("reference"))
            and isinstance(review.get("reviewer"), str)
            and bool(review.get("reviewer"))
            and trusted_reviews is not None
            and trusted_reviews.get(stage) == digest
        )
        stages[stage] = accepted
        if not accepted:
            issues.append(
                AdmissionIssue(
                    stage.upper(), "A separately pinned approved review decision is required."
                )
            )
    if data.get("dataset_kind") != "synthetic":
        issues.append(
            AdmissionIssue(
                "EMPIRICAL_EXECUTION_BLOCKED",
                "Preflight does not authorize empirical scoring or disclosure.",
            )
        )
    return PreflightResult(
        PREFLIGHT_VERSION, stages, tuple(issues), not issues and all(stages.values())
    )


def _query_coverage(data: Mapping[str, Any], query: Mapping[str, Any]) -> dict[str, bool]:
    """Conservative component counts; no authority decision follows from them."""
    result: dict[str, bool] = dict.fromkeys(
        ("history", "baseline", "H72", "D7", "native_targets", "M0_M5_inputs", "M6_M8_basis"), False
    )
    try:
        assessments = {a["id"]: a for a in data["assessments"]}
        origin = _number(query["origin_h"])
        canonical = _canonical(query["participant"], data["aliases"])
        ids = query["history_assessment_ids"]
        selected = [assessments[x] for x in ids]
        result["history"] = (
            len(ids) == len(set(ids)) == 4
            and [_number(a["time_h"]) for a in selected]
            == sorted({_number(a["time_h"]) for a in selected})
            and all(
                _canonical(a["participant"], data["aliases"]) == canonical
                and _number(a["time_h"]) < origin
                and _number(a["available_at_h"]) <= origin
                and bool(_assessment_values(a))
                for a in selected
            )
        )
        qualifying = sorted(
            (
                a
                for a in assessments.values()
                if _canonical(a["participant"], data["aliases"]) == canonical
                and a["valid"] is True
                and 24 <= origin - _number(a["time_h"]) <= 240
            ),
            key=lambda a: _number(a["time_h"]),
        )
        result["baseline"] = (
            len(qualifying) >= 2
            and len({_number(a["time_h"]) for a in qualifying}) == len(qualifying)
            and query["baseline_assessment_ids"] == [a["id"] for a in qualifying[-2:]]
            and all(
                _number(a["available_at_h"]) <= origin and bool(_assessment_values(a))
                for a in qualifying[-2:]
            )
            and _number(data["history_complete_through_h"][canonical]) >= origin
        )
        target = assessments[query["target_assessment_id"]]
        for horizon, (_, low, high) in WINDOWS.items():
            result[horizon] = (
                query["horizon"] == horizon
                and low <= _number(target["time_h"]) - origin <= high
                and _canonical(target["participant"], data["aliases"]) == canonical
            )
        values = _assessment_values(target)
        baselines = [_assessment_values(assessments[x]) for x in query["baseline_assessment_ids"]]
        result["native_targets"] = (
            set(query["targets"]) == set(TARGETS)
            and query["units"] == TARGETS
            and all(
                math.isclose(
                    _number(query["targets"][name]),
                    values[i] - (baselines[0][i] + baselines[1][i]) / 2,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                for i, name in enumerate(TARGETS)
            )
            and any(result[h] for h in WINDOWS)
        )
        row = _public_row(query, assessments)
        raw = np.asarray(query["raw_features"], dtype=np.float64)
        result["M0_M5_inputs"] = (
            result["history"]
            and result["baseline"]
            and raw.shape == (39,)
            and np.array_equal(raw, project_gate7_historical_v1((row,))[0])
            and np.array_equal(np.asarray(query["history_tokens"]).reshape(16), raw[7:23])
            and len(query["history_exposures"]) == 1
            and _number(query["history_exposures"][0]["time_h"]) < origin
            and _number(query["index_exposure"]["time_h"]) == origin
            and len(query["plans"]) in (2, 3)
            and all(
                origin <= _number(x["time_h"]) <= origin + WINDOWS[query["horizon"]][0]
                for x in query["plans"]
            )
            and query["routine"]["origin_id"] == query["origin_id"]
            and _number(query["routine"]["available_at_h"]) <= origin
            and query["routine"]["source_sha256"] == data["routine_source_sha256"]
            and all(
                _number(x["known_at_h"]) <= origin
                for x in [*query["history_exposures"], query["index_exposure"], *query["plans"]]
            )
            and data["preprocessing"]["frozen"] is True
            and data["preprocessing"]["training_only"] is True
        )
        from cmj_recovery_dynamics.observations.native_mechanics import gate7_basis_v1

        basis = np.asarray(query["basis"], dtype=np.float64)
        result["M6_M8_basis"] = (
            result["M0_M5_inputs"]
            and basis.shape == (5,)
            and _pin(query["basis_source_sha256"])
            and query["basis_source_sha256"] == data["basis_source_sha256"]
            and bool(np.allclose(basis, gate7_basis_v1(row), rtol=1e-12, atol=1e-12))
        )
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        pass
    return result


def aggregate_steward_assessment(
    payload: Mapping[str, object], *, minimum_cell_size: int = 5
) -> dict[str, object]:
    """Return aggregate component counts; no identities, labels or refusals.

    The whole count vector is suppressed if any nonzero count or complement is
    small. Repeated/adaptive releases still need steward disclosure review;
    a local function cannot prevent cross-run differencing attacks.
    """
    if type(minimum_cell_size) is not int or minimum_cell_size < 5:
        raise ValueError("minimum suppression threshold must be at least five")
    data = cast(Mapping[str, Any], payload)
    try:
        test_groups = {_canonical(x, data["aliases"]) for x in data["participant_splits"]["test"]}
        queries = [
            q
            for q in data["queries"]
            if _canonical(q["participant"], data["aliases"]) in test_groups
        ]
        participants = {_canonical(q["participant"], data["aliases"]) for q in queries}
        history: set[str] = set()
        baseline: set[str] = set()
        potential: set[str] = set()
        counts: dict[str, int] = dict.fromkeys(
            (
                "queries_H72",
                "queries_D7",
                "queries_native_targets",
                "queries_M0_M5_inputs",
                "queries_M6_M8_basis",
            ),
            0,
        )
        for query in queries:
            participant = _canonical(query["participant"], data["aliases"])
            coverage = _query_coverage(data, query)
            if coverage["history"]:
                history.add(participant)
            if coverage["baseline"]:
                baseline.add(participant)
            for name in counts:
                counts[name] += int(coverage[name.removeprefix("queries_")])
        global_result = validate_native_dataset(payload)
        if global_result.stages["structural"]:
            potential = participants
        counts.update(
            participants_with_history=len(history),
            participants_with_baseline=len(baseline),
            potentially_eligible_participant_groups=len(potential),
        )
        small = any(
            0 < n < minimum_cell_size
            or 0
            < (
                len(test_groups)
                if name.startswith("participants_")
                or name == "potentially_eligible_participant_groups"
                else len(queries)
            )
            - n
            < minimum_cell_size
            for name, n in counts.items()
        )
        return {
            "version": PREFLIGHT_VERSION,
            "scope": "declared test groups only; counts grant no scientific or use authority",
            "suppressed": small,
            "counts": None if small else counts,
            "disclosure_review_required": True,
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return {
            "version": PREFLIGHT_VERSION,
            "suppressed": True,
            "counts": None,
            "status": "invalid_or_unassessed",
            "disclosure_review_required": True,
        }


def synthetic_trusted_reviews(payload: Mapping[str, object] | None = None) -> dict[str, str]:
    """Invented review pins solely for qualifying the engineering fixture."""
    reviews = cast(
        Mapping[str, Any], synthetic_preflight_fixture() if payload is None else payload
    )["reviews"]
    return {
        stage: hashlib.sha256(
            json.dumps(
                reviews[stage],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        for stage in REVIEW_STAGES
    }


def synthetic_preflight_fixture(participants: int = 6) -> dict[str, Any]:
    """Invent explicitly synthetic signals/identities; not a historical experiment.

    Values are not fitted, sampled from participants, or predictions from
    recovered checkpoints. A synthetic label remains an operator assertion.
    """
    from cmj_recovery_dynamics.observations.native_mechanics import gate7_basis_v1

    if type(participants) is not int or participants < 1:
        raise ValueError("positive synthetic test participant count required")
    test = [f"invented-test-{i}" for i in range(participants)]
    people = ["invented-train", "invented-validation", *test]
    payload: dict[str, Any] = {
        "version": PREFLIGHT_VERSION,
        "dataset_kind": "synthetic",
        "dataset_id": "invented-native-engineering-cohort",
        "candidate_indices": list(range(9)),
        "source_authority": {"reference": "synthetic-native-v1", "sha256": "a" * 64},
        "basis_source_sha256": "b" * 64,
        "routine_source_sha256": "c" * 64,
        "participant_splits": {"train": people[:1], "validation": people[1:2], "test": test},
        "aliases": {},
        "preprocessing": {
            "reference": "invented-frozen-training-preprocessing",
            "sha256": "d" * 64,
            "frozen": True,
            "training_only": True,
        },
        "missingness": [],
        "support_mismatches": [],
        "history_complete_through_h": dict.fromkeys(people, 0.0),
        "reviews": {},
        "assessments": [],
        "queries": [],
    }
    for pindex, participant in enumerate(people):
        history_ids: list[str] = []
        for aindex, time in enumerate((-240.0, -168.0, -72.0, -24.0, 72.0, 168.0)):
            aid = f"{participant}-assessment-{aindex}"
            if time < 0:
                history_ids.append(aid)
            trials: list[dict[str, Any]] = [
                {
                    "id": f"{aid}-trial-{i}",
                    "valid": True,
                    "force_n_per_kg": 18.0 + pindex / 5 + aindex / 10 + i / 100,
                    "impulse_m_per_s": 2.0 + pindex / 50 + aindex / 100 + i / 1000,
                    "depth_m": 0.3 + pindex / 1000 + i / 10000,
                }
                for i in range(3)
            ]
            for trial in trials:
                gravity = 9.80665
                duration = trial["impulse_m_per_s"] / (trial["force_n_per_kg"] - gravity)
                peak_force = (70.0 + pindex) * trial["force_n_per_kg"] / 0.75
                trial["force_time"] = {
                    "timestamps_s": [0.0, 0.2, 0.2 + duration / 2, 0.2 + duration, 0.3 + duration],
                    "force_n": [peak_force, peak_force, peak_force, 0.0, 0.0],
                    "gravity_m_s2": gravity,
                    "concentric_onset_s": 0.2,
                    "takeoff_s": 0.2 + duration,
                    "sop_sha256": "f" * 64,
                    "calibration_sha256": "9" * 64,
                }
            payload["assessments"].append(
                {
                    "id": aid,
                    "participant": participant,
                    "time_h": time,
                    "available_at_h": time,
                    "valid": True,
                    "system_mass_kg": 70.0 + pindex,
                    "mechanics": dict(MECHANICS),
                    "provenance_sha256": "e" * 64,
                    "trials": trials,
                }
            )
        assessments = {a["id"]: a for a in payload["assessments"]}
        for hindex, (horizon, (nominal, _, _)) in enumerate(WINDOWS.items()):
            oid = f"{participant}-origin"
            query: dict[str, Any] = {
                "id": f"{oid}-{horizon}",
                "input_id": f"{oid}-{horizon}-input",
                "participant": participant,
                "origin_id": oid,
                "origin_h": 0.0,
                "horizon": horizon,
                "target_time_hours": nominal,
                "baseline_assessment_ids": history_ids[-2:],
                "history_assessment_ids": history_ids.copy(),
                "target_assessment_id": f"{participant}-assessment-{4 + hindex}",
                "units": dict(TARGETS),
                "history_exposures": [
                    {"time_h": -48.0, "duration_minutes": 45.0 + pindex, "known_at_h": -48.0}
                ],
                "index_exposure": {
                    "time_h": 0.0,
                    "duration_minutes": 40.0 + pindex,
                    "known_at_h": 0.0,
                },
                "plans": [
                    {"time_h": t, "duration_minutes": 40.0 + pindex, "known_at_h": 0.0}
                    for t in (0.0, 24.0, 48.0)
                ],
                "routine": {
                    "scheduled": False,
                    "state": "UNSCHEDULED",
                    "origin_id": oid,
                    "available_at_h": 0.0,
                    "source_sha256": "c" * 64,
                },
                "basis_source_sha256": "b" * 64,
            }
            row = _public_row(query, assessments)
            query["raw_features"] = project_gate7_historical_v1((row,))[0].tolist()
            query["history_tokens"] = np.asarray(query["raw_features"][7:23]).reshape(4, 4).tolist()
            query["basis"] = list(gate7_basis_v1(row))
            tv = _assessment_values(assessments[query["target_assessment_id"]])
            bv = [_assessment_values(assessments[x]) for x in query["baseline_assessment_ids"]]
            query["targets"] = {
                name: tv[i] - (bv[0][i] + bv[1][i]) / 2 for i, name in enumerate(TARGETS)
            }
            payload["queries"].append(query)
    manifest_hash = dataset_manifest_sha256(payload)
    payload["reviews"] = {
        stage: {
            "decision": "approved",
            "reference": "invented-engineering-review",
            "reviewer": "synthetic-reviewer",
            "scope": stage,
            "dataset_sha256": manifest_hash,
        }
        for stage in REVIEW_STAGES
    }
    return payload


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON object key")
        result[name] = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local aggregate-only native dataset assessment; no network access."
    )
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        payload: object = json.loads(args.input.read_text(), object_pairs_hook=_unique_json_object)
        if not isinstance(payload, dict):
            raise ValueError("invalid input")
        result = aggregate_steward_assessment(cast(dict[str, object], payload))
    except (OSError, ValueError):
        result = {
            "version": PREFLIGHT_VERSION,
            "suppressed": True,
            "counts": None,
            "status": "invalid_or_unassessed",
        }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
