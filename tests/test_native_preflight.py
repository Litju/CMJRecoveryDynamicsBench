"""Invented cohort admission and aggregate disclosure controls only."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from cmj_recovery_dynamics.observations.native_preflight import (
    aggregate_steward_assessment,
    synthetic_preflight_fixture,
    synthetic_trusted_reviews,
    validate_native_dataset,
)


def codes(payload: dict[str, Any]) -> set[str]:
    return {
        issue.code
        for issue in validate_native_dataset(
            payload, trusted_reviews=synthetic_trusted_reviews()
        ).issues
    }


def test_synthetic_admission_has_separate_stages() -> None:
    payload = synthetic_preflight_fixture()
    result = validate_native_dataset(payload, trusted_reviews=synthetic_trusted_reviews())
    assert result.eligible and all(result.stages.values()) and not result.issues
    unreviewed = validate_native_dataset(payload)
    assert unreviewed.stages["structural"] and not unreviewed.eligible
    assert not unreviewed.stages["measurement_authority"]
    meta = validate_native_dataset(payload, metadata_only=True)
    assert meta.stages["metadata"] and not meta.stages["structural"] and not meta.eligible
    payload["dataset_kind"] = "empirical"
    assert "EMPIRICAL_EXECUTION_BLOCKED" in codes(payload)


@pytest.mark.parametrize(
    ("area", "field", "value", "code"),
    [
        (
            "query",
            "units",
            {"relative_mean_concentric_force": "N", "relative_concentric_net_impulse": "m/s"},
            "TARGET_UNITS",
        ),
        ("query", "targets", {"relative_peak_mean_force_innovation": 0.0}, "TARGET_KEYS"),
        ("query", "participant", "unlinked-person", "PARTICIPANT_LINK"),
        (
            "query",
            "baseline_assessment_ids",
            ["invented-train-assessment-0", "invented-train-assessment-1"],
            "BASELINE_LATEST",
        ),
        ("query", "raw_features", [0.0] * 38, "RAW_FEATURES"),
        ("query", "history_tokens", [[0.0] * 4] * 4, "HISTORY_PAIRING"),
        ("query", "basis", [0.0] * 5, "BASIS_PAIRING"),
        ("query", "basis_source_sha256", "", "BASIS_AUTHORITY"),
        ("query", "horizon", "H48", "HORIZON"),
        ("assessment", "system_mass_kg", 0.0, "SYSTEM_MASS"),
        ("assessment", "mechanics", {}, "MECHANICS_AUTHORITY"),
        ("preprocessing", "frozen", False, "PREPROCESSING"),
        ("preprocessing", "training_only", False, "PREPROCESSING"),
    ],
)
def test_corrupt_records_fail_with_explained_codes(
    area: str, field: str, value: object, code: str
) -> None:
    payload = synthetic_preflight_fixture()
    row = (
        payload["queries"][0]
        if area == "query"
        else payload["assessments"][0]
        if area == "assessment"
        else payload["preprocessing"]
    )
    row[field] = value
    assert code in codes(payload)


def test_aliases_are_resolved_before_split_separation() -> None:
    payload = synthetic_preflight_fixture()
    payload["aliases"]["invented-test-0"] = "invented-train"
    assert "PARTICIPANT_OVERLAP" in codes(payload)
    payload["aliases"] = {"a": "b", "b": "a"}
    assert "ALIAS_CYCLE" in codes(payload)


def test_identity_copies_and_repeated_origins_fail() -> None:
    payload = synthetic_preflight_fixture()
    payload["queries"].append(copy.deepcopy(payload["queries"][0]))
    assert "DUPLICATE_QUERY" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["queries"][1]["origin_id"] = payload["queries"][2]["origin_id"]
    payload["queries"][1]["routine"]["origin_id"] = payload["queries"][2]["origin_id"]
    assert "ORIGIN_LINK" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["assessments"].append(copy.deepcopy(payload["assessments"][0]))
    assert "DUPLICATE_ASSESSMENT" in codes(payload)


def test_missing_cells_and_wrong_links_are_not_silently_excluded() -> None:
    payload = synthetic_preflight_fixture()
    payload["queries"].pop()
    assert "INCOMPLETE_CELLS" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["queries"][0]["target_assessment_id"] = "invented-test-0-assessment-4"
    assert "PARTICIPANT_LINK" in codes(payload)


def test_future_data_and_plans_fail_even_with_valid_shapes() -> None:
    payload = synthetic_preflight_fixture()
    payload["assessments"][0]["available_at_h"] = 1.0
    assert "FUTURE_AVAILABILITY" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["queries"][0]["plans"][0]["known_at_h"] = 1.0
    assert "FUTURE_PLAN" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["queries"][0]["routine"]["available_at_h"] = 1.0
    assert "ROUTINE_AUTHORITY" in codes(payload)


def test_latest_baseline_requires_complete_history_and_valid_trials() -> None:
    payload = synthetic_preflight_fixture()
    extra = copy.deepcopy(payload["assessments"][0])
    extra.update(id="invented-extra-baseline", time_h=-25.0, available_at_h=-25.0)
    for index, trial in enumerate(extra["trials"]):
        trial["id"] = f"invented-extra-trial-{index}"
    payload["assessments"].append(extra)
    assert "BASELINE_LATEST" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["assessments"][2]["trials"].pop()
    assert "TRIAL_CRITERION" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["history_complete_through_h"]["invented-train"] = -24.0
    assert "INCOMPLETE_HISTORY" in codes(payload)


def test_target_windows_and_arithmetic_are_checked() -> None:
    payload = synthetic_preflight_fixture()
    payload["assessments"][4]["time_h"] = 79.0
    payload["assessments"][4]["available_at_h"] = 79.0
    assert "TARGET_WINDOW" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["queries"][0]["targets"]["relative_concentric_net_impulse"] = 5.0
    assert "TARGET_LINEAGE" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["support_mismatches"] = ["invented-support-gap"]
    assert "SUPPORT_MISSINGNESS" in codes(payload)


def test_near_duplicate_vectors_need_adjudication() -> None:
    payload = synthetic_preflight_fixture()
    query = copy.deepcopy(payload["queries"][0])
    query.update(
        id="invented-copy-query", input_id="invented-copy-input", origin_id="invented-copy-origin"
    )
    query["routine"]["origin_id"] = query["origin_id"]
    payload["queries"].append(query)
    assert "NEAR_DUPLICATE" in codes(payload)


def test_trial_identity_and_missing_source_pins_fail() -> None:
    payload = synthetic_preflight_fixture()
    payload["assessments"][1]["trials"][0]["id"] = payload["assessments"][0]["trials"][0]["id"]
    assert "DUPLICATE_TRIAL" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["source_authority"]["sha256"] = ""
    assert "SOURCE_AUTHORITY" in codes(payload)


def test_extra_invalid_trial_and_premeasurement_availability_fail() -> None:
    payload = synthetic_preflight_fixture()
    trial = copy.deepcopy(payload["assessments"][0]["trials"][0])
    trial.update(id="invented-extra-invalid-trial", valid=False)
    payload["assessments"][0]["trials"].append(trial)
    assert "TRIAL_CRITERION" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["assessments"][0]["available_at_h"] -= 100
    assert "AVAILABILITY_ORDER" in codes(payload)


def test_reviews_are_scope_and_entire_manifest_bound() -> None:
    payload = synthetic_preflight_fixture()
    pins = synthetic_trusted_reviews(payload)
    payload["dataset_id"] = "different-unreviewed-dataset"
    result = validate_native_dataset(payload, trusted_reviews=pins)
    assert result.stages["structural"] and not result.eligible
    assert not any(result.stages[stage] for stage in pins)
    payload = synthetic_preflight_fixture()
    payload["preprocessing"]["reference"] = "different-unreviewed-run"
    result = validate_native_dataset(payload, trusted_reviews=pins)
    assert not result.stages["measurement_authority"]
    payload = synthetic_preflight_fixture()
    payload["reviews"]["measurement_authority"] = payload["reviews"]["data_use_authorization"]
    assert not validate_native_dataset(payload, trusted_reviews=pins).stages[
        "measurement_authority"
    ]


def test_malformed_payload_and_nonserializable_review_fail_closed() -> None:
    from typing import cast

    assert not validate_native_dataset(cast(Any, [])).eligible
    payload = synthetic_preflight_fixture()
    payload["reviews"]["measurement_authority"]["extra"] = {"not-json"}
    assert not validate_native_dataset(
        payload, trusted_reviews=synthetic_trusted_reviews()
    ).eligible


def test_signal_events_and_trial_arithmetic_are_not_just_labels() -> None:
    payload = synthetic_preflight_fixture()
    payload["assessments"][0]["trials"][0]["force_time"]["takeoff_s"] = 99.0
    assert "FORCE_TIME_EVENTS" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["assessments"][0]["trials"][0]["force_n_per_kg"] += 1
    assert "FORCE_TIME_LINEAGE" in codes(payload)
    payload = synthetic_preflight_fixture()
    payload["assessments"][0]["trials"][0]["force_time"]["calibration_sha256"] = ""
    assert "MECHANICS_AUTHORITY" in codes(payload)


def test_tied_baseline_times_need_adjudication() -> None:
    payload = synthetic_preflight_fixture()
    assessment = copy.deepcopy(payload["assessments"][2])
    assessment["id"] = "invented-tied-assessment"
    for index, trial in enumerate(assessment["trials"]):
        trial["id"] = f"invented-tied-trial-{index}"
    payload["assessments"].append(assessment)
    assert "BASELINE_TIME_TIE" in codes(payload)


@pytest.mark.parametrize("reviews", [[], True, "approved", {"data_use_authorization": True}])
def test_malformed_authority_does_not_crash_or_authorize(reviews: object) -> None:
    payload = synthetic_preflight_fixture()
    payload["reviews"] = reviews
    result = validate_native_dataset(payload, trusted_reviews=synthetic_trusted_reviews())
    assert not result.eligible and not result.stages["data_use_authorization"]


def test_aggregate_counts_suppress_entire_vector_and_never_output_identifiers() -> None:
    payload = synthetic_preflight_fixture(6)
    result = aggregate_steward_assessment(payload)
    assert result["suppressed"] is False
    assert result["counts"] == {
        "participants_with_history": 6,
        "participants_with_baseline": 6,
        "queries_H72": 6,
        "queries_D7": 6,
        "queries_native_targets": 12,
        "queries_M0_M5_inputs": 12,
        "queries_M6_M8_basis": 12,
        "potentially_eligible_participant_groups": 6,
    }
    assert "invented-test" not in json.dumps(result)
    assert "test groups only" in str(result["scope"])
    assert aggregate_steward_assessment(synthetic_preflight_fixture(1))["counts"] is None
    payload["queries"][4]["basis"][0] += 1
    assert aggregate_steward_assessment(payload)["counts"] is None
    with pytest.raises(ValueError, match="at least five"):
        aggregate_steward_assessment(payload, minimum_cell_size=1)


def test_steward_cli_does_not_echo_input_errors_or_rows(tmp_path: Path) -> None:
    path = tmp_path / "invented.json"
    path.write_text(json.dumps(synthetic_preflight_fixture()))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "cmj_recovery_dynamics.observations.native_preflight", str(path)],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    assert not result.stderr and "invented-test" not in result.stdout
    assert json.loads(result.stdout)["counts"]["queries_H72"] == 6
    path.write_text("invalid secret-shaped content")
    result = subprocess.run(
        [sys.executable, "-m", "cmj_recovery_dynamics.observations.native_preflight", str(path)],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    assert "secret-shaped" not in result.stdout and not result.stderr
    assert json.loads(result.stdout)["counts"] is None
