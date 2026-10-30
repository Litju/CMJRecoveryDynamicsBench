"""Protect the clean scientific namespace and repository artifact boundary."""

import ast
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from cmj_recovery_dynamics.provenance.historical_aliases import HISTORICAL_ALIASES
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_IDENTIFIER = re.compile(
    r"\b(?:SP\d{2}|[WODT]\d{2}|ALI-\d+|Gate\s*\d+|Candidate H|V[123])\b",
    re.IGNORECASE,
)
PUBLIC_HISTORICAL_LABELS = frozenset(
    label.casefold()
    for label in (
        "SP01",
        "SP02",
        "SP03",
        "SP04",
        "SP05",
        "SP06",
        "SP07",
        "SP08",
        "W01",
        "W02",
        "W03",
        "W04",
        "W05",
        "W06",
        "O01",
        "O02",
        "O03",
        "O04",
        "D02",
        "D03",
        "D04",
        "D05",
        "D06",
        "D07",
        "D08",
        "D09",
        "T01",
        "T02",
        "ALI-400",
        "ALI-488",
        "ALI-490",
        "ALI-494",
        "ALI-506",
        "ALI-507",
        "ALI-517",
        "ALI-518",
        "ALI-522",
        "Gate 0",
        "Gate 3",
        "Gate 5",
        "Gate 6",
        "Gate 7",
        "Gate0",
        "Gate3",
        "Gate5",
        "Gate6",
        "Gate7",
        "Candidate H",
        "V1",
        "V2",
        "V3",
    )
)
HISTORICAL_PATH_ALLOWLIST = {
    "src/cmj_recovery_dynamics/reproduction/d04_membership.py",
    "src/cmj_recovery_dynamics/model_reproduction/gate7_projection.py",
    "tests/test_d04_membership.py",
    "tests/test_gate7_projection.py",
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
    "MANIFEST.in",
}
PUBLIC_DIRECTORY_ALLOWLIST = {"src", "tests", "docs", "website", ".github"}
PUBLIC_RECONCILIATION_COMMITS = {
    "3dc4c82f0c948add6e4a9ebdebfd2279" + "33c823d3",
    "618a56bbcc8de6fb1cd3a5d4d8f71bf" + "7fcb61529",
    "4e08777bc7c7f7ce4fa541ea3776b4cb" + "2e2dda3b",
    "582a8c3f86fad7e20ebb6a5d907a1965" + "7ee0d8c2",
}
PUBLIC_DOCUMENT_ALLOWLIST = {
    "docs/GATE7_TARGET_AUTHORITY_AND_DATA_READINESS_V1.md",
    "docs/RESEARCH_LAB.md",
    "docs/GATE7_SCIENTIFIC_EVALUATION_PROTOCOL_V1.md",
    "docs/M8_RELEASE_NOTES.md",
    "docs/M8_V1_RELEASE_AUDIT.md",
    "docs/M7_PUBLIC_TREE_REDACTION.md",
    "docs/M7_OCCURRENCE_CLASSIFICATION.md",
    "docs/M7_QUALIFICATION.md",
    "docs/M8_REPRODUCIBILITY_MATRIX.md",
    "docs/M8_REPRODUCTION_RESULTS.md",
    "docs/M8_PUBLIC_REPRODUCTION_RECEIPTS.json",
    "docs/M8_REFERENCE_MODEL_STUDY.md",
    "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md",
    "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json",
    "docs/M8_V1_RELEASE_AUDIT_RECEIPT.json",
    "docs/M8_V1_PUBLICATION_RECEIPT.json",
    "docs/RES-545_MODEL_RECOVERY_REVIEW.md",
    "docs/RES-546_EXECUTION_PLAN.md",
    "docs/RES-546_GATE7_M8_RECOVERY.md",
    "docs/RES-546_INFERENCE_VERIFICATION.md",
    "docs/RES-546_CPU_SOURCE_INTEGRATION_POLICY.md",
    "docs/RES-546_M4_HISTORICAL_FINDINGS.md",
    "docs/RES-546_M5_HISTORICAL_FINDINGS.md",
    "docs/RES-546_M6_HISTORICAL_FINDINGS.md",
    "docs/RES-546_M7_HISTORICAL_FINDINGS.md",
}
PUBLIC_MACHINE_RECEIPT_ALLOWLIST = {
    "docs/M8_PUBLIC_REPRODUCTION_RECEIPTS.json",
    "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json",
    "docs/M8_V1_RELEASE_AUDIT_RECEIPT.json",
    "docs/M8_V1_PUBLICATION_RECEIPT.json",
}
PROTECTED_SUFFIXES = (
    ".bundle",
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.xz",
    ".7z",
    ".parquet",
    ".pkl",
    ".pickle",
    ".joblib",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".safetensors",
    ".bin",
    ".npy",
    ".npz",
    ".h5",
    ".hdf5",
    ".feather",
    ".arrow",
    ".jsonl",
    ".json",
    ".csv",
    ".tsv",
    ".mmd",
    ".md",
)
PROTECTED_DIRECTORY_NAMES = {
    "recovery-corpus",
    "recovery-archive",
    "private-evidence",
    "evidence-archive",
    "private-evaluation",
    "private-evaluations",
    "private-results",
    "historical-git",
    "git-database",
    "evaluation-artifacts",
    "evaluation-results",
    "model-checkpoints",
    "license_review",
    "data",
    "datasets",
    "artifacts",
    "raw-data",
}
PRIVATE_MACHINE_PATH = re.compile(
    "/"
    + r"(?:home|users|root|mnt|tmp|var/tmp)/"
    + r"[^\s'\"<>]+"
    + "|"
    + r"[A-Z]:\\"
    + "Users"
    + r"\\[^\s'\"<>]+",
    re.IGNORECASE,
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?" + "PRIVATE KEY" + r"-----")
SECRET_PATTERNS = (
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
SHA1_OBJECT_REFERENCE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", re.IGNORECASE)


def test_historical_identifiers_are_exactly_allowlisted_and_imports_are_restricted() -> None:
    expected = set(BENCHMARK_REGISTRY)
    assert set(HISTORICAL_ALIASES) == expected
    source_root = REPOSITORY_ROOT / "src" / "cmj_recovery_dynamics"
    for source_path in source_root.rglob("*.py"):
        relative = source_path.relative_to(source_root)
        source = source_path.read_text(encoding="utf-8")
        syntax_tree = ast.parse(source)
        for node in ast.walk(syntax_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert all(
                    identifier.casefold() in PUBLIC_HISTORICAL_LABELS
                    for identifier in HISTORICAL_IDENTIFIER.findall(node.value)
                ), relative
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("cmj_recovery_dynamics.provenance"):
                        assert relative == Path("reproducibility/execution.py")
                        assert alias.name == "cmj_recovery_dynamics.provenance.public_roots"
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("cmj_recovery_dynamics.provenance"):
                    if relative == Path("provenance/__init__.py"):
                        assert module in {
                            "cmj_recovery_dynamics.provenance.historical_aliases",
                            "cmj_recovery_dynamics.provenance.public_roots",
                        }
                    else:
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
        _assert_public_path(tracked_path)


def _assert_public_path(tracked_path: str) -> None:
    path = Path(tracked_path)
    if len(path.parts) == 1:
        assert path.name in ROOT_FILE_ALLOWLIST, tracked_path
    else:
        assert path.parts[0] in PUBLIC_DIRECTORY_ALLOWLIST, tracked_path
        if path.parts[0] == "docs":
            assert tracked_path in PUBLIC_DOCUMENT_ALLOWLIST, tracked_path
    assert not path.name.startswith(".env"), tracked_path
    protected = any(tracked_path.endswith(suffix) for suffix in PROTECTED_SUFFIXES)
    public_report = tracked_path in PUBLIC_DOCUMENT_ALLOWLIST and path.suffix == ".md"
    public_receipt = tracked_path in PUBLIC_MACHINE_RECEIPT_ALLOWLIST and path.suffix == ".json"
    public_website_source = path.parts[0] == "website" and path.suffix in {".md", ".json"}
    assert not protected or public_report or public_receipt or public_website_source, tracked_path
    protected_directories = PROTECTED_DIRECTORY_NAMES.intersection(
        part.lower() for part in path.parts
    )
    public_fixture_directory = path.parts[:3] in {
        ("website", "src", "data"),
        ("website", "public", "data"),
    }
    assert not protected_directories or (
        protected_directories == {"data"} and public_fixture_directory
    ), tracked_path


@pytest.mark.parametrize(
    "tracked_path",
    (
        "src/export.csv",
        "tests/export.tsv",
        "src/checkpoint.safetensors",
        "tests/checkpoint.bin",
        "src/archive.tgz",
        "tests/archive.tar.xz",
        "src/history.mmd",
        "src/historical-git/object.py",
        "tests/git-database/object.py",
        "src/private-results/result.py",
        "tests/private-evaluation/scorer.py",
        "docs/unreviewed.md",
        "docs/unreviewed.json",
    ),
)
def test_public_boundary_rejects_protected_artifact_paths(tracked_path: str) -> None:
    with pytest.raises(AssertionError):
        _assert_public_path(tracked_path)


def test_tracked_text_has_no_machine_paths_or_secret_markers() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = REPOSITORY_ROOT / raw_path.decode("utf-8")
        content = path.read_bytes()
        if b"\0" in content:
            continue
        source = content.decode("utf-8")
        relative = path.relative_to(REPOSITORY_ROOT)
        assert PRIVATE_MACHINE_PATH.search(source) is None, relative
        assert PRIVATE_KEY.search(source) is None, relative
        assert all(pattern.search(source) is None for pattern in SECRET_PATTERNS), relative
        for public_reference in (
            PUBLIC_RECONCILIATION_COMMITS if relative.parts[0] == "website" else ()
        ):
            source = source.replace(public_reference, "")
        assert SHA1_OBJECT_REFERENCE.search(source) is None, relative


def test_public_github_identity_is_allowed_but_private_markers_are_rejected() -> None:
    public_url = "https://github.com/Litju/CMJRecoveryDynamicsBench"
    private_path = "/" + "home" + "/" + "operator" + "/" + "private-data"
    synthetic_secret = "gh" + "p_" + "x" * 36
    assert PRIVATE_MACHINE_PATH.search(public_url) is None
    assert PRIVATE_MACHINE_PATH.search(private_path) is not None
    assert not any(pattern.search(public_url) for pattern in SECRET_PATTERNS)
    assert any(pattern.search(synthetic_secret) for pattern in SECRET_PATTERNS)
    assert "litju" in public_url.casefold()
    assert "sp03" in PUBLIC_HISTORICAL_LABELS
    assert "ali-999" not in PUBLIC_HISTORICAL_LABELS


def test_v1_version_and_scientific_claim_boundary() -> None:
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())["project"]
    assert project["version"] == "1.0.0"
    readme = (REPOSITORY_ROOT / "README.rst").read_text().casefold()
    notes = (REPOSITORY_ROOT / "docs/M8_RELEASE_NOTES.md").read_text().casefold()
    assert "official github release" in readme
    assert "matching official github release/tag" in notes
    assert "its production scorer remains unimplemented" in readme
    assert "neither ood robustness nor human athlete performance" in readme
    assert "the fixed-mode production scorer is unimplemented" in notes
    assert "this is not exact historical replay" in notes


def test_license_and_citation_versions_match_package_metadata() -> None:
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())["project"]
    has_license_file = (REPOSITORY_ROOT / "LICENSE").is_file()
    assert bool(project.get("license")) == has_license_file
    citation = REPOSITORY_ROOT / "CITATION.cff"
    if citation.exists():
        match = re.search(r"(?m)^version:\s*['\"]?([^\s'\"]+)", citation.read_text())
        assert match is not None
        assert match.group(1) == project["version"]


def test_source_archive_manifest_includes_only_reviewed_public_documents() -> None:
    instructions = (REPOSITORY_ROOT / "MANIFEST.in").read_text().splitlines()
    assert set(instructions) == {
        "include CITATION.cff",
        *(f"include {path}" for path in PUBLIC_DOCUMENT_ALLOWLIST),
    }
