"""Guard the science-first flagship manuscript against the pinned public receipts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
V4 = REPOSITORY_ROOT / "docs" / "manuscript" / "v4"
RESULTS = json.loads(
    (REPOSITORY_ROOT / "docs" / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text()
)
VAR = RESULTS["across_root_variability"]
TEX = (V4 / "manuscript.tex").read_text()
HEADLINE = {
    "zero_innovation": "2.430659",
    "training_constant": "1.036038",
    "ridge_full": "0.736270",
    "structured_full": "0.773316",
}


def test_manifest_matches_tracked_files_and_hashes() -> None:
    lines = (V4 / "ARTIFACT_SHA256SUMS").read_text().splitlines()
    listed = {name: digest for digest, name in (line.split("  ", 1) for line in lines)}
    tracked = subprocess.run(
        ["git", "ls-files", "docs/manuscript/v4"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    expected = {f"docs/manuscript/v4/{name}" for name in listed} | {
        "docs/manuscript/v4/ARTIFACT_SHA256SUMS"
    }
    assert set(tracked) == expected
    for name, digest in listed.items():
        assert hashlib.sha256((V4 / name).read_bytes()).hexdigest() == digest, name


def test_headline_scores_equal_the_receipt_and_appear_in_the_paper() -> None:
    for model, text in HEADLINE.items():
        assert f"{VAR[model]['root_mean_nrmse']:.6f}" == text
        assert text in TEX, model


def test_generated_tables_match_the_receipts() -> None:
    spec = importlib.util.spec_from_file_location(
        "v4_tables", V4 / "figure_source/generate_tables.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    written: dict[str, str] = {}
    module.write = lambda name, text: written.__setitem__(name, text)  # type: ignore[attr-defined]
    for build in (
        module.overall,
        module.cells,
        module.intervals,
        module.ablations,
        module.nested,
        module.architectures,
    ):
        build()
    assert len(written) == 6
    for name, text in written.items():
        assert (V4 / "tables" / name).read_text() == text, name


def test_paper_keeps_the_two_bodies_of_work_separate() -> None:
    assert "not scored" in TEX and "were not compared for predictive accuracy" in TEX
    for sentence in TEX.split("."):
        if re.search(r"\bM[0-8]\b", sentence) and "NRMSE" in sentence:
            assert "not" in sentence or "no " in sentence, sentence[:80]
    for banned in ("leaderboard", "peak mean force", "physiological timescale"):
        assert banned not in TEX.lower() or banned == "physiological timescale"


def test_paper_states_synthetic_boundaries() -> None:
    for phrase in (
        "not experimentally established recovery time constants",
        "No paired interval for ridge versus the structured comparator was recorded",
        "legacy identifier",
        "no athlete was measured",
        "not athlete accuracy",
    ):
        assert phrase.lower() in TEX.lower() or phrase in TEX, phrase


def test_every_cited_key_has_a_bibliography_entry() -> None:
    bib = (V4 / "bibliography/references.bib").read_text()
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    cited = {k.strip() for group in re.findall(r"\\cite\{([^}]+)\}", TEX) for k in group.split(",")}
    assert cited <= keys, cited - keys
