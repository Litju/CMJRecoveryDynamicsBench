"""Guard the RES-783 LinkedIn carousel against the pinned receipts and the claim boundary."""

from __future__ import annotations

import csv
import hashlib
import html
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CAROUSEL = REPOSITORY_ROOT / "docs" / "linkedin_carousel"
HTML_PATH = CAROUSEL / "output" / "carousel.html"
LEDGER_PATH = CAROUSEL / "ledger" / "figure_source_ledger.csv"
RESULTS = json.loads(
    (REPOSITORY_ROOT / "docs" / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text()
)
HEADLINE = {
    "zero_innovation": "2.430659",
    "training_constant": "1.036038",
    "ridge_full": "0.736270",
    "structured_full": "0.773316",
}
LINKS = {
    "https://recovery-observatory.vercel.app/",
    "https://github.com/Litju/CMJRecoveryDynamicsBench",
    "https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf",
}
RESULT_NUMBER = re.compile(r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+\.\d{3,})(?![\w.])")
FORBIDDEN = (
    "peak mean force",
    "leaderboard",
    "significant",
    "p-value",
    "time constant",
    "timescale",
    "state-of-the-art",
    "breakthrough",
    "revolutionary",
    "game-chang",
    "independent datasets",
)


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "carousel_builder", CAROUSEL / "tools" / "build_carousel.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


def _ledger() -> list[dict[str, str]]:
    with LEDGER_PATH.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _pages() -> dict[int, str]:
    source = HTML_PATH.read_text(encoding="utf-8")
    pages = re.findall(r'<section class="page[^"]*" data-page="(\d)".*?</section>', source, re.S)
    blocks = re.findall(r'(<section class="page[^"]*" data-page="\d".*?</section>)', source, re.S)
    return {int(n): block for n, block in zip(pages, blocks, strict=True)}


def _visible(fragment: str) -> str:
    fragment = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S)
    fragment = re.sub(r'<span class="tex[^"]*">.*?</span>', " ", fragment, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def _numbers(text: str) -> set[str]:
    return set(RESULT_NUMBER.findall(text.replace("−", "-")))


def _ledger_numbers() -> set[str]:
    found: set[str] = set()
    for row in _ledger():
        found |= _numbers(row["displayed"])
    return found


def test_manifest_matches_tracked_files_and_hashes() -> None:
    lines = (CAROUSEL / "ARTIFACT_SHA256SUMS").read_text().splitlines()
    listed = {name: digest for digest, name in (line.split("  ", 1) for line in lines)}
    tracked = subprocess.run(
        ["git", "ls-files", "docs/linkedin_carousel"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    expected = {f"docs/linkedin_carousel/{name}" for name in listed}
    assert set(tracked) == expected | {"docs/linkedin_carousel/ARTIFACT_SHA256SUMS"}
    for name, digest in listed.items():
        assert hashlib.sha256((CAROUSEL / name).read_bytes()).hexdigest() == digest, name


def test_build_reproduces_the_committed_html_and_ledger() -> None:
    builder: Any = _builder()
    rendered, registry = builder.render()
    assert rendered == HTML_PATH.read_text(encoding="utf-8")
    assert builder.write_ledger(registry) == LEDGER_PATH.read_text(encoding="utf-8")


def test_ledger_values_and_digests_match_their_sources() -> None:
    rows = _ledger()
    by_token = {row["token"]: row for row in rows}
    for model, text in HEADLINE.items():
        assert f"{RESULTS['across_root_variability'][model]['root_mean_nrmse']:.6f}" == text
        assert by_token[f"{model}.mean"]["displayed"] == text
        assert by_token[f"{model}.mean"]["page"] == "6"
    for row in rows:
        source = REPOSITORY_ROOT / row["source"]
        if source.is_file():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            assert row["source_sha256"] == digest, row["token"]
        else:
            assert row["evidence_class"] == "link" and row["source_sha256"] == "", row["token"]
    assert {row["page"] for row in rows} == {str(n) for n in range(1, 9)} - {"1"}


def test_every_displayed_result_number_is_in_the_ledger() -> None:
    allowed = _ledger_numbers()
    for number, block in _pages().items():
        missing = _numbers(_visible(block)) - allowed
        assert not missing, (number, sorted(missing))


def test_original_architectures_never_carry_a_score() -> None:
    pages = _pages()
    page4 = _visible(pages[4])
    assert "Not scored." in page4 and "No NRMSE exists for them" in page4
    assert not re.search(r"\d\.\d{3,}", page4)
    assert all(row["unit"] != "NRMSE" for row in _ledger() if row["page"] == "4")
    for block in pages.values():
        for element in re.findall(r"<(?:text|li|p|div)\b[^>]*>(.*?)</(?:text|li|p|div)>", block):
            words = _visible(element)
            if re.search(r"\bM[0-8]\b", words):
                assert not re.search(r"\d\.\d{4,}", words), words


def test_wording_respects_the_terminology_contract() -> None:
    pages = _pages()
    for number, block in pages.items():
        words = " ".join(_visible(block).split())
        lowered = words.lower()
        for phrase in FORBIDDEN:
            assert phrase not in lowered, (number, phrase)
        for match in re.finditer(r"accuracy", lowered):
            assert lowered[: match.start()].endswith("not athlete "), number
        assert "SYNTHETIC DATA" in words.upper(), number
    assert "not measured human recovery constants" in _visible(pages[3])
    assert "Peak force" in _visible(pages[2]) and "not a modeled target" in _visible(pages[2])


def test_pages_use_scientific_labels_not_internal_identifiers() -> None:
    internal = (
        r"\b[MAENRV]-\d{2}\b",  # claims-register ids
        r"\bRES-\d+",  # issue ids
        r"\w\.(?:py|csv|json|md)\b",  # file names
        r"\b\w+_\w+\b",  # code keys such as across_root_variability
        r"\b[0-9a-f]{8,}\b",  # digests
        r"(?i)gate ?7|receipt|ledger|token",
    )
    for number, block in _pages().items():
        words = " ".join(_visible(block).split())
        for pattern in internal:
            assert re.search(pattern, words) is None, (number, pattern, re.search(pattern, words))


def test_links_are_the_verified_public_destinations() -> None:
    source = HTML_PATH.read_text(encoding="utf-8")
    assert set(re.findall(r'<a [^>]*href="([^"]+)"', source)) == LINKS
    title = re.search(r"<title>(.*?)</title>", source)
    assert title is not None
    assert title.group(1) == (
        "From Force Plate to Forecast: Modeling CMJ Performance Changes Following Training"
    )
