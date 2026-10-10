"""Protect the clean scientific namespace and repository artifact boundary."""

import ast
import re
import subprocess
from pathlib import Path

from cmj_recovery_dynamics.provenance.historical_aliases import HISTORICAL_ALIASES
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_IDENTIFIER = re.compile(
    r"\b(?:SP\d{2}|[WODT]\d{2}|" + "ALI" + r"-\d+|Gate\s*\d+|" + "Candidate" + " H|V[123])\b",
    re.IGNORECASE,
)
PROTECTED_SUFFIXES = (
    ".bundle",
    ".zip",
    ".tar",
    ".tar.gz",
    ".7z",
    ".parquet",
    ".pkl",
    ".pickle",
    ".joblib",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".npy",
    ".npz",
    ".h5",
    ".hdf5",
    ".feather",
    ".arrow",
    ".jsonl",
    ".json",
    ".md",
)
PROTECTED_DIRECTORY_NAMES = {
    "recovery-corpus",
    "recovery-archive",
    "private-evidence",
    "evidence-archive",
    "private-evaluations",
    "evaluation-artifacts",
    "evaluation-results",
    "model-checkpoints",
    "license_review",
    "data",
    "datasets",
    "artifacts",
    "raw-data",
}


def test_historical_alias_values_are_confined_to_the_provenance_mapping() -> None:
    expected = set(BENCHMARK_REGISTRY)
    assert set(HISTORICAL_ALIASES) == expected
    source_root = REPOSITORY_ROOT / "src" / "cmj_recovery_dynamics"
    for source_path in source_root.rglob("*.py"):
        relative = source_path.relative_to(source_root)
        if "provenance" in relative.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        assert HISTORICAL_IDENTIFIER.search(source) is None, relative
        syntax_tree = ast.parse(source)
        for node in ast.walk(syntax_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("cmj_recovery_dynamics.provenance"):
                        assert relative == Path("reproducibility/execution.py")
                        assert alias.name == "cmj_recovery_dynamics.provenance.public_roots"
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("cmj_recovery_dynamics.provenance"):
                    assert relative == Path("reproducibility/execution.py")
                    assert module == "cmj_recovery_dynamics.provenance.public_roots"


def test_scientific_source_and_test_paths_use_no_historical_identifiers() -> None:
    for folder in ("src", "tests"):
        for path in (REPOSITORY_ROOT / folder).rglob("*.py"):
            assert (
                HISTORICAL_IDENTIFIER.search(path.relative_to(REPOSITORY_ROOT).as_posix()) is None
            )


def test_git_tracks_no_protected_artifact_class() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    tracked_paths = tuple(path.decode("utf-8") for path in completed.stdout.split(b"\0") if path)
    for tracked_path in tracked_paths:
        path = Path(tracked_path)
        assert not path.name.startswith(".env"), tracked_path
        assert not any(tracked_path.endswith(suffix) for suffix in PROTECTED_SUFFIXES), tracked_path
        assert not PROTECTED_DIRECTORY_NAMES.intersection(part.lower() for part in path.parts), (
            tracked_path
        )
