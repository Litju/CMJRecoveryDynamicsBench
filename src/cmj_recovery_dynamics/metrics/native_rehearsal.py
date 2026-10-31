"""Inspectable all-nine synthetic rehearsal; never loads weights or empirical records."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from cmj_recovery_dynamics.metrics.native_analysis import (
    CELLS,
    AnalysisPlan,
    CandidatePredictions,
    CellRule,
    fit_synthetic_constant_baseline,
    synthetic_native_analysis_v1,
)
from cmj_recovery_dynamics.metrics.native_research import (
    NativeAuthority,
    NativeHorizon,
    NativeObservation,
    NativePrediction,
    NativeQuery,
    NativeTarget,
)
from cmj_recovery_dynamics.observations.native_preflight import (
    synthetic_preflight_fixture,
    synthetic_trusted_reviews,
    validate_native_dataset,
)


def rehearsal_plan() -> AnalysisPlan:
    """Hypothetical numerical thresholds exercise decisions; no clinical meaning."""
    return AnalysisPlan(
        "invented-engineering-plan-v1",
        "M0",
        tuple(
            CellRule(h, t, "N/kg" if t is NativeTarget.FORCE else "m/s", 0.001, 1.0, 1.0, 1.0, 6)
            for h, t in CELLS
        ),
        "query_weighted_participant_cluster",
        "percentile_linear_95",
        tuple(f"{h.value}/{t.value}" for h, t in CELLS),
        "participant_sign_flip_squared_error",
        "independent_participant_clusters_symmetric_paired_loss_null",
        10_000,
        20261031,
        0.05,
        True,
        (),
        True,
    )


def rehearsal_inputs(
    payload: Mapping[str, Any],
) -> tuple[list[CandidatePredictions], list[NativeObservation], list[NativeObservation]]:
    """Create invented predictions and native record identities from the admitted fixture."""
    assessments = {row["id"]: row for row in payload["assessments"]}
    observations: list[NativeObservation] = []
    training: list[NativeObservation] = []
    for row in payload["queries"]:
        if row["participant"] in payload["participant_splits"]["validation"]:
            continue
        baseline_ids = row["baseline_assessment_ids"]
        query = NativeQuery(
            payload["dataset_id"],
            row["participant"],
            row["origin_id"],
            row["id"],
            row["input_id"],
            NativeHorizon(row["horizon"]),
            (baseline_ids[0], baseline_ids[1]),
            (
                assessments[baseline_ids[0]]["time_h"] - row["origin_h"],
                assessments[baseline_ids[1]]["time_h"] - row["origin_h"],
            ),
            (3, 3),
        )
        target = assessments[row["target_assessment_id"]]
        destination = (
            training
            if row["participant"] in payload["participant_splits"]["train"]
            else observations
        )
        for target_name in NativeTarget:
            destination.append(
                NativeObservation(
                    query,
                    target_name,
                    row["units"][target_name.value],
                    row["targets"][target_name.value],
                    target["time_h"] - row["origin_h"],
                    3,
                    target["id"],
                )
            )
    # Deliberately label-derived invented predictions exercise analysis, never predictive validity.
    candidates = [
        CandidatePredictions(
            f"M{index}",
            repeat,
            tuple(
                NativePrediction(
                    row.query,
                    row.target,
                    row.unit,
                    row.value
                    + (index + 1 + repeat / 4)
                    * (0.003 if row.target is NativeTarget.FORCE else 0.0003)
                    * (1 + int(row.query.participant.rsplit("-", 1)[-1]) / 10),
                )
                for row in observations
            ),
        )
        for index in range(9)
        for repeat in (0, 1)
    ]
    return candidates, observations, training


def synthetic_rehearsal_v1() -> dict[str, Any]:
    """Construct, admit, pair and analyze the new deterministic engineering fixture."""
    payload = synthetic_preflight_fixture(6)
    admission = validate_native_dataset(payload, trusted_reviews=synthetic_trusted_reviews())
    if not admission.eligible:
        raise ValueError("synthetic rehearsal failed admission")
    admission_sha = hashlib.sha256(
        json.dumps(asdict(admission), sort_keys=True).encode()
    ).hexdigest()
    candidates, observations, training = rehearsal_inputs(payload)
    authority = NativeAuthority(
        payload["source_authority"]["reference"], payload["source_authority"]["sha256"]
    )

    def digest(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()

    admission_receipt = {
        "version": "gate7_analysis_admission_v1",
        "dataset_kind": "synthetic",
        "stages": admission.stages,
        "source_authority": asdict(authority),
        "dataset_identity": payload["dataset_id"],
        "participant_splits_sha256": digest(payload["participant_splits"]),
        "observations_sha256": digest([asdict(row) for row in observations]),
        "preflight_payload_sha256": digest(payload),
    }
    admission_sha = digest(admission_receipt)
    baseline = fit_synthetic_constant_baseline(
        training,
        source_authority=authority,
        expected_authority=authority,
        participant_splits=payload["participant_splits"],
        dataset_kind="synthetic",
    )
    analysis = synthetic_native_analysis_v1(
        candidates,
        observations,
        plan=rehearsal_plan(),
        admission_stages=admission.stages,
        admission_receipt_sha256=admission_sha,
        admission_receipt=admission_receipt,
        source_authority=authority,
        expected_authority=authority,
        participant_splits=payload["participant_splits"],
        dataset_kind="synthetic",
        constant_baseline=baseline,
    )
    negatives: dict[str, list[str]] = {}
    corruptions: dict[str, tuple[str, object]] = {
        "wrong_units": (
            "units",
            {"relative_mean_concentric_force": "m/s", "relative_concentric_net_impulse": "m/s"},
        ),
        "wrong_targets": ("targets", {"generic_peak_force": 0.2}),
        "wrong_participant_links": ("participant", "invented-unknown"),
        "missing_basis_authority": ("basis_source_sha256", "f" * 64),
    }
    for name, (field, value) in corruptions.items():
        altered = deepcopy(payload)
        altered["queries"][0][field] = value
        failure = validate_native_dataset(altered, trusted_reviews=synthetic_trusted_reviews())
        if failure.eligible:
            raise AssertionError(f"negative control unexpectedly admitted: {name}")
        negatives[name] = [issue.code for issue in failure.issues]
    for name in (
        "future_observation",
        "incomplete_cells",
        "invalid_trial_criterion",
        "invalid_data_use_authorization",
        "repeated_query_identity",
        "mismatched_query_identity",
    ):
        altered = deepcopy(payload)
        if name == "future_observation":
            altered["assessments"][0]["available_at_h"] = 1.0
        elif name == "incomplete_cells":
            altered["queries"].pop()
        elif name == "invalid_trial_criterion":
            altered["assessments"][0]["trials"].pop()
        elif name == "invalid_data_use_authorization":
            altered["reviews"]["data_use_authorization"]["decision"] = "denied"
        elif name == "repeated_query_identity":
            altered["queries"].append(deepcopy(altered["queries"][0]))
        else:
            altered["queries"][1]["input_id"] = altered["queries"][0]["input_id"]
        failure = validate_native_dataset(altered, trusted_reviews=synthetic_trusted_reviews())
        if failure.eligible:
            raise AssertionError(f"negative control unexpectedly admitted: {name}")
        negatives[name] = [issue.code for issue in failure.issues]
    from dataclasses import replace

    try:
        synthetic_native_analysis_v1(
            candidates,
            observations,
            plan=replace(rehearsal_plan(), locked=False),
            admission_stages=admission.stages,
            admission_receipt_sha256=admission_sha,
            admission_receipt=admission_receipt,
            source_authority=authority,
            expected_authority=authority,
            participant_splits=payload["participant_splits"],
            dataset_kind="synthetic",
        )
    except ValueError as exc:
        negatives["unlocked_thresholds"] = [str(exc)]
    else:
        raise AssertionError("unlocked plan unexpectedly accepted")
    return {
        "version": "gate7_synthetic_rehearsal_v1",
        "dataset_kind": "synthetic",
        "fixture_scope": "new invented labeled engineering dataset; not historical Gate7",
        "fixture_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "admission": asdict(admission),
        "analysis": analysis,
        "negative_controls": negatives,
        "candidate_repeat_combinations": len(candidates),
        "empirical_execution_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-rehearsal", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(synthetic_rehearsal_v1(), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
