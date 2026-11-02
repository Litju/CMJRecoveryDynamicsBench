"""Offline, explicitly authorized native study execution; no network or artifact discovery.

Trusted pins come from the responsible institutional operator, independently of
incoming records. Software checks bindings, not signatures, consent or scientific truth.
"""

from __future__ import annotations

import copy
import hashlib
import math
import platform
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from cmj_recovery_dynamics.metrics.native_analysis import (
    AnalysisPlan,
    CandidatePredictions,
    _digest,  # pyright: ignore[reportPrivateUsage]
    _native_analysis_v1,  # pyright: ignore[reportPrivateUsage]
    validate_analysis_plan,
)
from cmj_recovery_dynamics.metrics.native_research import (
    NativeAuthority,
    NativeHorizon,
    NativeObservation,
    NativePrediction,
    NativeQuery,
    NativeTarget,
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import project_gate7_historical_v1
from cmj_recovery_dynamics.observations.native_mechanics import gate7_basis_v1
from cmj_recovery_dynamics.observations.native_preflight import (
    _assessment_values,  # pyright: ignore[reportPrivateUsage]
    _canonical,  # pyright: ignore[reportPrivateUsage]
    _public_row,  # pyright: ignore[reportPrivateUsage]
    validate_native_dataset,
)
from cmj_recovery_dynamics.research_lab import ModelGrant, _original  # pyright: ignore[reportPrivateUsage]

AUTHORIZATION_SCOPES = (
    "investigator_plan_and_native_addendum",
    "measurement_and_origin_availability",
    "participant_linkage_and_separation",
    "data_use_and_outcome_access",
    "ethics_determination",
    "checkpoint_execution",
    "result_generation_and_disclosure",
)


def study_runtime_identity() -> dict[str, Any]:
    """Bind authorization to installed Python source and the actual CPU runtime."""
    root = Path(__file__).parent
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "device": "cpu",
        "source_sha256": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*.py"))
        },
    }


def model_identities(grants: Sequence[ModelGrant]) -> list[dict[str, Any]]:
    """Restricted association identities, excluding local artifact paths."""
    return [
        {
            "candidate": grant.candidate,
            "repeat": grant.repeat,
            "config_sha256": grant.config_sha256,
            "checkpoint_sha256": grant.checkpoint_sha256,
            "source_authority": grant.source_authority,
            "association_authority": grant.association_authority,
        }
        for grant in sorted(grants, key=lambda g: (g.candidate, g.repeat))
    ]


def execute_native_study(
    payload: Mapping[str, Any],
    *,
    plan: AnalysisPlan,
    grants: Sequence[ModelGrant],
    authorization: Mapping[str, Any],
    expected_authorization_sha256: str,
    trusted_reviews: Mapping[str, str],
) -> dict[str, Any]:
    """Execute all18 original identities only after a separately authenticated grant.

    No approvals exist by default. An independently supplied trusted pin is the
    operator trust boundary, not cryptographic verification of human authority.
    Synthetic fixtures may qualify this path without representing real approvals.
    The returned receipt contains restricted aggregates; nothing is published.
    """
    data = copy.deepcopy(dict(payload))
    approval = copy.deepcopy(dict(authorization))
    models = tuple(grants)
    reviews = dict(trusted_reviews)
    validate_analysis_plan(plan)
    if (
        type(expected_authorization_sha256) is not str
        or len(expected_authorization_sha256) != 64
        or any(c not in "0123456789abcdef" for c in expected_authorization_sha256)
        or _digest(approval) != expected_authorization_sha256
    ):
        raise ValueError("INDEPENDENT_STUDY_AUTHORIZATION_REQUIRED")
    if (
        len(models) != 18
        or any(type(grant) is not ModelGrant for grant in models)
        or {(g.candidate, g.repeat) for g in models}
        != {(f"M{i}", repeat) for i in range(9) for repeat in (0, 1)}
        or data.get("candidate_indices") != list(range(9))
        or plan.primary_candidate != "M0"
        or data.get("dataset_kind") not in ("synthetic", "empirical")
        or (data["dataset_kind"] == "empirical" and plan.hypothetical_thresholds)
    ):
        raise ValueError("COMPLETE_STUDY_IDENTITY_AND_SCIENTIFIC_PLAN_REQUIRED")
    try:
        approved_at = datetime.fromisoformat(approval["approved_at"])
        expires_at = datetime.fromisoformat(approval["expires_at"])
        now = datetime.now(UTC)
        times_valid = (
            approved_at.utcoffset() is not None
            and expires_at.utcoffset() is not None
            and approved_at <= now < expires_at
        )
        decisions = approval["decisions"]
        scopes_valid = set(decisions) == set(AUTHORIZATION_SCOPES) and all(
            decisions[scope]["decision"] == "approved"
            and all(
                type(decisions[scope][key]) is str and decisions[scope][key].strip()
                for key in ("authority", "reference")
            )
            for scope in AUTHORIZATION_SCOPES
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError("STUDY_AUTHORITY_RECORDS_REQUIRED") from None
    if (
        approval.get("version") != "gate7_offline_study_authorization_v1"
        or not times_valid
        or not scopes_valid
        or approval.get("dataset_sha256") != _digest(data)
        or approval.get("plan_sha256") != _digest(asdict(plan))
        or approval.get("models_sha256") != _digest(model_identities(models))
        or approval.get("trusted_reviews_sha256") != _digest(reviews)
        or approval.get("runtime_sha256") != _digest(study_runtime_identity())
    ):
        raise ValueError("STUDY_AUTHORIZATION_BINDING_FAILED")
    admission = validate_native_dataset(data, trusted_reviews=reviews)
    if not all(admission.stages.values()) or any(
        issue.code != "EMPIRICAL_EXECUTION_BLOCKED" for issue in admission.issues
    ):
        raise ValueError("STUDY_SOURCE_ADMISSION_FAILED")
    aliases = data["aliases"]
    splits = {
        name: [_canonical(p, aliases) for p in group]
        for name, group in data["participant_splits"].items()
    }
    test_groups = set(splits["test"])
    queries = sorted(
        (q for q in data["queries"] if _canonical(q["participant"], aliases) in test_groups),
        key=lambda q: q["id"],
    )
    participants = {_canonical(q["participant"], aliases) for q in queries}
    origins = {q["origin_id"] for q in queries}
    registered_groups = approval.get("registered_participants")
    registered_origins = approval.get("registered_origins")
    retention = approval.get("minimum_retention_fraction")
    if (
        type(registered_groups) is not int
        or registered_groups < len(participants)
        or type(registered_origins) is not int
        or registered_origins < len(origins)
        or not isinstance(retention, (int, float))
        or isinstance(retention, bool)
        or not 0 < retention <= 1
        or not math.isfinite(retention)
        or not participants
        or not origins
        or len(participants) / registered_groups < retention
        or len(origins) / registered_origins < retention
        or any(len(participants) < rule.minimum_participants for rule in plan.rules)
    ):
        raise ValueError("STUDY_COVERAGE_FAILED")
    assessments = {a["id"]: a for a in data["assessments"]}
    rows = [_public_row(q, assessments) for q in queries]
    raw = project_gate7_historical_v1(rows)
    history = raw[:, 7:23].reshape(len(queries), 4, 4)
    horizons = np.asarray([0 if q["horizon"] == "H72" else 1 for q in queries], dtype=np.int64)
    basis = np.asarray([gate7_basis_v1(row) for row in rows], dtype=np.float64)
    observations: list[NativeObservation] = []
    for query in queries:
        baseline = [assessments[x] for x in query["baseline_assessment_ids"]]
        identity = NativeQuery(
            data["dataset_id"],
            _canonical(query["participant"], aliases),
            query["origin_id"],
            query["id"],
            query["input_id"],
            NativeHorizon(query["horizon"]),
            (baseline[0]["id"], baseline[1]["id"]),
            (baseline[0]["time_h"] - query["origin_h"], baseline[1]["time_h"] - query["origin_h"]),
            (3, 3),
        )
        target = assessments[query["target_assessment_id"]]
        values = _assessment_values(target)
        before = [_assessment_values(a) for a in baseline]
        for i, kind in enumerate(NativeTarget):
            observations.append(
                NativeObservation(
                    identity,
                    kind,
                    query["units"][kind.value],
                    values[i] - (before[0][i] + before[1][i]) / 2,
                    target["time_h"] - query["origin_h"],
                    3,
                    target["id"],
                )
            )
    candidates: list[CandidatePredictions] = []
    for grant in sorted(models, key=lambda g: (g.candidate, g.repeat)):
        try:
            predictor = _original(grant)
            index = int(grant.candidate[1:])
            args: list[Any] = [raw]
            if index >= 3:
                args.append(history)
            if index >= 5:
                args.append(horizons)
            if index >= 6:
                args.append(basis)
            values = predictor.predict(*args)
            if values.shape != (len(queries), 2) or not np.isfinite(values).all():
                raise ValueError("invalid prediction")
        except Exception:
            raise ValueError("STUDY_MODEL_EXECUTION_FAILED: no partial analysis") from None
        candidates.append(
            CandidatePredictions(
                grant.candidate,
                grant.repeat,
                tuple(
                    NativePrediction(
                        observation.query,
                        observation.target,
                        observation.unit,
                        float(values[i // 2, i % 2]),
                    )
                    for i, observation in enumerate(observations)
                ),
            )
        )
    source = NativeAuthority(
        data["source_authority"]["reference"], data["source_authority"]["sha256"]
    )
    admission_record = {
        "version": "gate7_analysis_admission_v1",
        "dataset_kind": data["dataset_kind"],
        "stages": admission.stages,
        "source_authority": asdict(source),
        "participant_splits_sha256": _digest(splits),
        "observations_sha256": _digest([asdict(o) for o in observations]),
        "dataset_identity": data["dataset_id"],
        "preflight_payload_sha256": _digest(data),
    }
    result = _native_analysis_v1(
        candidates,
        observations,
        plan=plan,
        admission_stages=admission.stages,
        admission_receipt_sha256=_digest(admission_record),
        admission_receipt=admission_record,
        source_authority=source,
        expected_authority=source,
        participant_splits=splits,
        dataset_kind=data["dataset_kind"],
    )
    result.pop("receipt_sha256")
    result["offline_study"] = {
        "authorization_sha256": expected_authorization_sha256,
        "models": model_identities(models),
        "runtime_sha256": approval["runtime_sha256"],
        "registered_participants": registered_groups,
        "registered_origins": registered_origins,
        "analyzed_origins": len(origins),
        "minimum_retention_fraction": retention,
        "authority_limit": "Operator independently authenticates grants; hashes only bind bytes.",
        "disclosure": "Restricted aggregates; no automatic publication or individual predictions.",
    }
    result["empirical_execution_authorized"] = data["dataset_kind"] == "empirical"
    result["receipt_sha256"] = _digest(result)
    return result
