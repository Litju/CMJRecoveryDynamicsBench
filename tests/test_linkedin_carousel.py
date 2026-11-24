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
PAGE_COUNT = 10
MEASURE_PAGE, TARGET_PAGE, MODEL_PAGE, ARCH_PAGE, RESULTS_PAGE, UNCERTAINTY_PAGE = 2, 3, 4, 5, 7, 8
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
    pages = re.findall(r'<section class="page[^"]*" data-page="(\d+)".*?</section>', source, re.S)
    blocks = re.findall(r'(<section class="page[^"]*" data-page="\d+".*?</section>)', source, re.S)
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
        assert by_token[f"{model}.mean"]["page"] == str(RESULTS_PAGE)
    for row in rows:
        source = REPOSITORY_ROOT / row["source"]
        if source.is_file():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            assert row["source_sha256"] == digest, row["token"]
        else:
            assert row["evidence_class"] == "link" and row["source_sha256"] == "", row["token"]
    assert {row["page"] for row in rows} == {str(n) for n in range(2, PAGE_COUNT + 1)}


def test_every_displayed_result_number_is_in_the_ledger() -> None:
    allowed = _ledger_numbers()
    for number, block in _pages().items():
        missing = _numbers(_visible(block)) - allowed
        assert not missing, (number, sorted(missing))


def test_original_architectures_never_carry_a_score() -> None:
    pages = _pages()
    assert len(pages) == PAGE_COUNT
    architectures = " ".join(_visible(pages[ARCH_PAGE]).split())
    assert "18 recorded inference routes" in architectures
    assert "Not evaluated here." in architectures
    assert "not part of the public four-reference-model experiment" in architectures
    assert "no comparative NRMSE is reported for them" in architectures
    everything = " ".join(_visible(block) for block in pages.values()).lower()
    for overreach in ("no nrmse exists", "networks in total", "not scored"):
        assert overreach not in everything, overreach
    assert not re.search(r"\d\.\d{3,}", architectures)
    assert all(row["unit"] != "NRMSE" for row in _ledger() if row["page"] == str(ARCH_PAGE))
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
    assert "not measured human recovery constants" in _visible(pages[MODEL_PAGE])
    measure = _visible(pages[MEASURE_PAGE])
    assert "Peak force" in measure and "not a modeled target" in measure


def test_displayed_change_equals_the_displayed_means() -> None:
    shown = {row["token"]: row["displayed"] for row in _ledger()}
    base, crit = float(shown["base.mean"]), float(shown["crit.mean"])
    change = float(shown["innovation"].replace("−", "-"))
    assert round(crit - base, 3) == change
    assert all(len(shown[k].split(".")[1]) == 3 for k in ("base.mean", "crit.mean", "innovation"))
    assert "computed from the unrounded means" in _visible(_pages()[TARGET_PAGE])


def test_interval_limitation_sits_directly_under_the_bootstrap_figure() -> None:
    block = _pages()[UNCERTAINTY_PAGE]
    figure_end = block.index("</figure>")
    note = re.search(r'<p class="fig-note">(.*?)</p>', block, re.S)
    assert note is not None and block[figure_end + len("</figure>") : note.start()].strip() == ""
    text = " ".join(_visible(note.group(1)).split())
    assert "Per-model uncertainty within each evaluation root." in text
    assert "not a paired ridge-versus-structured comparison" in text
    assert "no direct ridge-versus-structured interval or significance result was recorded" in text


def test_type_scale_keeps_phone_readable_minimums() -> None:
    css = (CAROUSEL / "source" / "carousel.css").read_text(encoding="utf-8")
    sizes = [int(n) for n in re.findall(r"(?:font-size:\s*|font:[^;]*?\s)(\d+)px", css)]
    assert sizes and min(sizes) >= 26, sorted(sizes)[:5]
    svg_rules = dict(re.findall(r"svg \.([\w-]+) \{\s*font: \d+ (\d+)px", css))
    labels = {k: int(v) for k, v in svg_rules.items() if k not in {"dot-n"}}
    assert labels and min(labels.values()) >= 28, labels


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


PDF_PATH = CAROUSEL / "output" / "CMJ_From_Force_Plate_to_Forecast_carousel.pdf"


def _png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path.name
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def test_pdf_is_a_flat_ten_page_portrait_document_with_title_and_links() -> None:
    data = PDF_PATH.read_bytes()
    assert len(re.findall(rb"/Type\s*/Page(?!s)", data)) == PAGE_COUNT
    title = "From Force Plate to Forecast: Modeling CMJ Performance Changes Following Training"
    assert f"/Title ({title})".encode() in data
    assert {m.decode() for m in re.findall(rb"/URI \(([^)]*)\)", data)} == LINKS
    boxes = re.findall(rb"/MediaBox\s*\[([^\]]*)\]", data)
    assert len(boxes) == PAGE_COUNT
    for box in boxes:
        width, height = (float(v) for v in box.split()[2:4])
        assert abs(width / height - 0.8) < 0.002
    assert b"/AcroForm" not in data and b"/JavaScript" not in data
    assert (
        re.findall(rb"/(?:CreationDate|ModDate) \(([^)]*)\)", data)
        == [b"D:20261124000000+00'00'"] * 2
    )


def test_page_images_and_previews_are_complete() -> None:
    pages = sorted((CAROUSEL / "output" / "pages").glob("*.png"))
    assert [p.name for p in pages] == [f"page-{n:02d}.png" for n in range(1, PAGE_COUNT + 1)]
    assert all(_png_size(p) == (1080, 1350) for p in pages)
    for folder, size in (("phone", (1170, 1464)), ("phone-natural", (390, 488))):
        phones = sorted((CAROUSEL / "output" / "previews" / folder).glob("*.png"))
        expected = [f"phone-{n:02d}.png" for n in range(1, PAGE_COUNT + 1)]
        assert [p.name for p in phones] == expected, folder
        assert all(_png_size(p) == size for p in phones), folder
    width, height = _png_size(CAROUSEL / "output" / "previews" / "contact_sheet.png")
    assert width > height > 1000


def test_post_draft_uses_only_sourced_numbers_and_verified_links() -> None:
    builder: Any = _builder()
    registry, _geometry = builder.build_registry()
    sourced: set[str] = set()
    for token in registry.tokens.values():
        sourced |= _numbers(token.text)
    post = (CAROUSEL / "post" / "LINKEDIN_POST.md").read_text(encoding="utf-8")
    body = post.split("\n---\n", 1)[1]
    assert not _numbers(body) - sourced, sorted(_numbers(body) - sourced)
    assert set(re.findall(r"https://\S+", body)) == LINKS
    lowered = body.lower()
    for phrase in FORBIDDEN:
        assert phrase not in lowered, phrase
    assert "no athlete was measured" in lowered and "not peer reviewed" in lowered
    words = re.sub(r"https://\S+", " ", body).split()
    assert 120 <= len(words) <= 180, len(words)
    for phrase in (
        "nine original neural architecture families",
        "were not part of the benchmark",
        "four reference models",
        "ridge regression had lower descriptive nrmse",
        "simulator's own response modes",
        "no paired test of that difference was recorded",
    ):
        assert phrase in lowered, phrase
    assert not re.search("[\U0001f000-\U0001faff\u2600-\u27bf]", body), "no emoji"
    assert "#" not in body
