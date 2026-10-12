"""Protect the clean scientific namespace and repository artifact boundary."""

import ast
import re
import subprocess
import tomllib
from pathlib import Path

from cmj_recovery_dynamics.provenance.historical_aliases import HISTORICAL_ALIASES
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_IDENTIFIER = re.compile(
    r"\b(?:SP\d{2}|[WODT]\d{2}|ALI-\d+|Gate\s*\d+|Candidate H|V[123])\b",
    re.IGNORECASE,
)
HISTORICAL_PROVENANCE_PATHS = {
    "lineage/experiments.py",
    "lineage/results.py",
    "metrics/provenance.py",
    "model_reproduction/registry.py",
    "reproduction/camp_history.py",
    "reproduction/d04_membership.py",
    "reproduction/later_single_exposure.py",
    "reproduction/registry.py",
    "reproduction/rich_history.py",
    "reproduction/single_exposure.py",
    "study_reconstruction/decisions.py",
    "study_reconstruction/registry.py",
    "synthesis/registry.py",
}
HISTORICAL_PATH_ALLOWLIST = {
    "src/cmj_recovery_dynamics/reproduction/d04_membership.py",
    "tests/test_d04_membership.py",
}
HISTORICAL_PATH_IDENTIFIER = re.compile(
    r"(?:^|[/_.-])(?:SP\d{2}|[WODT]\d{2}|ALI-\d+|Gate\s*\d+|Candidate[ _-]*H|V[123])(?=$|[/_.-])",
    re.IGNORECASE,
)
ROOT_FILE_ALLOWLIST = {
    ".gitignore",
    ".python-version",
    "pyproject.toml",
    "README.rst",
    "LICENSE",
    "CITATION.cff",
    "NOTICE",
}
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
        # These exact files hold public lineage, reproduction, or study evidence metadata.
        if "provenance" in relative.parts or relative.as_posix() in HISTORICAL_PROVENANCE_PATHS:
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
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            normalized = relative.replace("_", "/")
            if HISTORICAL_PATH_IDENTIFIER.search(normalized):
                assert relative in HISTORICAL_PATH_ALLOWLIST


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
        if len(path.parts) == 1:
            assert path.name in ROOT_FILE_ALLOWLIST, tracked_path
        else:
            assert path.parts[0] in {"src", "tests"}, tracked_path
        assert not path.name.startswith(".env"), tracked_path
        assert not any(tracked_path.endswith(suffix) for suffix in PROTECTED_SUFFIXES), tracked_path
        assert not PROTECTED_DIRECTORY_NAMES.intersection(part.lower() for part in path.parts), (
            tracked_path
        )


def test_tracked_text_has_no_machine_paths_or_secret_markers() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    path_pattern = re.compile(
        "/"
        + r"(?:home|users|root|mnt|tmp|var/tmp)/"
        + r"[^\s'\"<>]+"
        + "|"
        + r"[A-Z]:\\"
        + "Users"
        + r"\\[^\s'\"<>]+",
        re.IGNORECASE,
    )
    private_key = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?" + "PRIVATE KEY" + r"-----")
    secret_patterns = (
        re.compile(r"\bA" + "KIA" + r"[0-9A-Z]{16}\b"),
        re.compile(r"\bgh[pousr]" + "_" + r"[A-Za-z0-9]{36,}\b"),
        re.compile(r"\bxox[baprs]" + "-" + r"[A-Za-z0-9-]{20,}\b"),
        re.compile(r"\bsk" + "-" + r"[A-Za-z0-9_-]{32,}\b"),
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
            r"\s*[:=]\s*['\"][A-Za-z0-9/+=._-]{16,}['\"]"
        ),
        re.compile(r"(?i)https?://[^/\s:@]+:[^/\s@]+@"),
        re.compile(r"(?i)https?://[^/\s]*(?:\.internal|\.local|\.corp|\.lan|localhost)"),
    )
    account_label = "lit" + "ju"
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = REPOSITORY_ROOT / raw_path.decode("utf-8")
        content = path.read_bytes()
        if b"\0" in content:
            continue
        source = content.decode("utf-8")
        relative = path.relative_to(REPOSITORY_ROOT)
        assert path_pattern.search(source) is None, relative
        assert private_key.search(source) is None, relative
        assert all(pattern.search(source) is None for pattern in secret_patterns), relative
        assert account_label not in source.casefold(), relative


def test_release_and_package_metadata_do_not_claim_m8_or_v1() -> None:
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())["project"]
    assert project["version"] != "1.0.0"
    for name in ("README.rst", "CITATION.cff"):
        path = REPOSITORY_ROOT / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            assert (
                re.search(
                    r"(?i)\b(?:released|published|complete|reproduced)\b[^\n]{0,60}\bv?1\.0(?:\.0)?\b",
                    text,
                )
                is None
            )


def test_license_and_citation_versions_match_package_metadata() -> None:
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())["project"]
    has_license_file = (REPOSITORY_ROOT / "LICENSE").is_file()
    assert bool(project.get("license")) == has_license_file
    citation = REPOSITORY_ROOT / "CITATION.cff"
    if citation.exists():
        match = re.search(r"(?m)^version:\s*['\"]?([^\s'\"]+)", citation.read_text())
        assert match is not None
        assert match.group(1) == project["version"]
