"""Guard the science-first evidence register against the pinned public receipts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCIENCE = REPOSITORY_ROOT / "docs" / "science"
RESULTS = json.loads(
    (REPOSITORY_ROOT / "docs" / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text()
)
VARIABILITY = RESULTS["across_root_variability"]
REFERENCE_MODELS = {
    "R-01": "zero_innovation",
    "R-02": "training_constant",
    "R-03": "ridge_full",
    "R-04": "structured_full",
}
EXPECTED_MEANS = {
    "zero_innovation": "2.430659",
    "training_constant": "1.036038",
    "ridge_full": "0.736270",
    "structured_full": "0.773316",
}
CLASSES = {"repository_result", "repository_definition", "synthetic_assumption", "nonclaim"}


def _register() -> list[dict[str, str]]:
    with (SCIENCE / "claims_evidence_register.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def _sha(relative: str) -> str:
    return hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest()


def test_manifest_matches_directory() -> None:
    lines = (SCIENCE / "SHA256SUMS").read_text().splitlines()
    listed = {name: digest for digest, name in (line.split("  ", 1) for line in lines)}
    on_disk = {p.name for p in SCIENCE.iterdir() if p.is_file() and p.name != "SHA256SUMS"}
    assert set(listed) == on_disk
    for name, digest in listed.items():
        assert hashlib.sha256((SCIENCE / name).read_bytes()).hexdigest() == digest, name


def test_every_manifest_file_is_tracked_by_git() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "docs/science"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    on_disk = {f"docs/science/{p.name}" for p in SCIENCE.iterdir() if p.is_file()}
    assert set(tracked) == on_disk


def test_source_digests_match_the_pinned_files() -> None:
    pinned = json.loads((SCIENCE / "source_digests.json").read_text())
    assert pinned["results_scientific_sha256"] == RESULTS["scientific_results_sha256"]
    assert pinned["selection_lock_sha256"] == RESULTS["selection_lock_sha256"]
    for key, entry in pinned["sources"].items():
        assert _sha(entry["path"]) == entry["sha256"], key


def test_register_rows_are_classified_and_traceable() -> None:
    rows = _register()
    assert len({row["claim_id"] for row in rows}) == len(rows)
    for row in rows:
        assert row["evidence_class"] in CLASSES, row["claim_id"]
        assert (REPOSITORY_ROOT / row["source"]).is_file(), row["claim_id"]
        assert _sha(row["source"]) == row["source_sha256"], row["claim_id"]


def test_reference_model_values_equal_the_receipt() -> None:
    rows = {row["claim_id"]: row for row in _register()}
    for claim_id, model in REFERENCE_MODELS.items():
        assert rows[claim_id]["value"] == EXPECTED_MEANS[model]
        assert f"{VARIABILITY[model]['root_mean_nrmse']:.6f}" == EXPECTED_MEANS[model]


def test_every_numeric_result_matches_the_receipt() -> None:
    for row in _register():
        locator = row["locator"]
        match = re.fullmatch(r"across_root_variability\.(\w+)\.root_mean_nrmse", locator)
        if match:
            assert row["value"] == f"{VARIABILITY[match.group(1)]['root_mean_nrmse']:.6f}"
    for index, root in enumerate(RESULTS["independent_test_roots"]):
        for model in ("ridge_full", "structured_full"):
            low, high = root["paired_camp_bootstrap"]["models"][model][
                "mean_six_cell_nrmse_95_percentile_interval"
            ]
            needle = f"[{low:.6f}, {high:.6f}]"
            suffix = f"[{index}].paired_camp_bootstrap.models.{model}"
            claims = [r["claim"] for r in _register() if r["locator"].endswith(suffix)]
            assert len(claims) == 1 and needle in claims[0]
            assert root["paired_camp_bootstrap"]["models"][model]["valid_replicates"] == 5000


def test_ridge_is_lower_than_structured_in_every_root_and_intervals_do_not_overlap() -> None:
    for root in RESULTS["independent_test_roots"]:
        models = root["paired_camp_bootstrap"]["models"]
        ridge = models["ridge_full"]["mean_six_cell_nrmse_95_percentile_interval"]
        structured = models["structured_full"]["mean_six_cell_nrmse_95_percentile_interval"]
        assert ridge[1] < structured[0]
        assert set(models["ridge_full"]) == {
            "mean_six_cell_nrmse_95_percentile_interval",
            "paired_nrmse_delta_vs_zero_95_percentile_interval",
            "valid_replicates",
        }


def test_original_architectures_are_never_given_a_score() -> None:
    for row in _register():
        if re.search(r"\bM[0-8]\b", row["claim"]) and "NRMSE" in row["unit"]:
            raise AssertionError(row["claim_id"])
        if row["claim_id"].startswith("N-"):
            assert not re.search(r"\d\.\d{6}", row["value"]), row["claim_id"]


def test_fixed_modes_are_labeled_as_synthetic_assumptions() -> None:
    rows = {row["claim_id"]: row for row in _register()}
    assert rows["A-01"]["evidence_class"] == "synthetic_assumption"
    assert "biological time constants" in rows["A-01"]["forbidden_wording"]
    source = (
        REPOSITORY_ROOT / "src/cmj_recovery_dynamics/dynamics/fixed_mode_discrepancy_response.py"
    ).read_text()
    assert "FAST_MODE_HOURS = 24.0" in source and "SLOW_MODE_HOURS = 84.0" in source


def test_register_formulas_match_the_generator() -> None:
    from math import pi

    from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
        GRAVITATIONAL_ACCELERATION_M_PER_S2 as g,
    )
    from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
        realize_concentric_trial,
    )

    force, impulse = 24.0, 2.6
    trial = realize_concentric_trial(force, impulse)
    assert abs(trial.mean_force_n_per_kg - force) < 1e-9
    assert abs(trial.net_impulse_m_per_s - impulse) < 1e-9
    assert abs(trial.net_impulse_m_per_s - (force - g) * trial.concentric_duration_seconds) < 1e-9
    peak = max(trial.vertical_force_n_per_kg)
    continuous_peak = g + (pi / 2.0) * (force - g)
    assert abs(peak - continuous_peak) < 0.01 * continuous_peak
    assert g == 9.80665


def test_references_are_external_and_verified() -> None:
    payload = json.loads((SCIENCE / "verified_references.json").read_text())
    for reference in payload["references"]:
        assert reference["verification"]
        assert reference["does_not_support"] is not None
    dois = {r["doi"] for r in payload["references"]}
    assert "10.1119/1.1397460" in dois and "10.1002/sim.8086" in dois
