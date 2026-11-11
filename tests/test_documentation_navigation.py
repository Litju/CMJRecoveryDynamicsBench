"""Guard the single documentation path from the repository to the current paper."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PAPER = "docs/manuscript/v3/full_illustrated_research_manuscript.pdf"
NAVIGATION_DOCUMENTS = (
    "README.rst",
    "docs/INDEX.md",
    "docs/manuscript/README.md",
    "website/README.md",
    "website/docs/SCIENCE_AND_DATA.md",
)
MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
RST_LINK = re.compile(r"`[^`<]*<([^>]+)>`_")


def _text(relative: str) -> str:
    return (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")


def _local_targets(relative: str) -> list[Path]:
    source = _text(relative)
    pattern = RST_LINK if relative.endswith(".rst") else MARKDOWN_LINK
    base = (REPOSITORY_ROOT / relative).parent
    targets: list[Path] = []
    for target in pattern.findall(source):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        targets.append((base / target.split("#", 1)[0]).resolve())
    return targets


@pytest.mark.parametrize("relative", NAVIGATION_DOCUMENTS)
def test_navigation_links_resolve_inside_repository(relative: str) -> None:
    targets = _local_targets(relative)
    assert targets, relative
    for target in targets:
        assert target.is_relative_to(REPOSITORY_ROOT), (relative, target)
        assert target.exists(), (relative, target)


@pytest.mark.parametrize("relative", NAVIGATION_DOCUMENTS)
def test_navigation_points_to_the_current_paper(relative: str) -> None:
    canonical = (REPOSITORY_ROOT / CANONICAL_PAPER).resolve()
    assert canonical in _local_targets(relative), relative


def test_current_paper_is_listed_before_historical_editions() -> None:
    index = _text("docs/INDEX.md")
    editions = _text("docs/manuscript/README.md")
    assert index.index("full_illustrated_research_manuscript.pdf") < index.index(
        "manuscript/README.md"
    )
    assert editions.index("v3/full_illustrated_research_manuscript.pdf") < editions.index(
        "(manuscript.pdf)"
    )
    assert "not the latest manuscript" in editions


@pytest.mark.parametrize("relative", NAVIGATION_DOCUMENTS)
def test_paper_is_described_as_an_unsubmitted_draft(relative: str) -> None:
    text = " ".join(_text(relative).casefold().split())
    assert "unsubmitted research draft" in text, relative
    for claim in ("peer-reviewed paper", "published in", "accepted paper", "doi:"):
        assert claim not in text, (relative, claim)


@pytest.mark.parametrize(
    "relative",
    ("README.rst", "docs/INDEX.md", "website/README.md", "website/docs/SCIENCE_AND_DATA.md"),
)
def test_force_outcome_terminology_keeps_the_registered_key(relative: str) -> None:
    text = " ".join(_text(relative).split())
    assert "mean concentric-force innovation" in text.casefold(), relative
    assert "relative_peak_mean_force_innovation" in text, relative
    assert "not peak force" in text.casefold(), relative


def test_current_and_historical_citations_are_distinguished() -> None:
    root_citation = _text("CITATION.cff")
    historical_citation = _text("website/source/CITATION.cff")
    assert re.search(r'(?m)^version:\s*"1\.1\.0"', root_citation)
    assert "1.1.0" not in historical_citation
    website_readme = _text("website/README.md")
    assert "](../CITATION.cff)" in website_readme
    assert "frozen historical copy" in website_readme
    assert "](../CITATION.cff)" in _text("docs/INDEX.md")


def test_flagship_paper_is_listed_before_the_retrospective_companion() -> None:
    index = _text("docs/INDEX.md")
    flagship = "manuscript/v4/full_illustrated_manuscript.pdf"
    assert (REPOSITORY_ROOT / "docs" / flagship).is_file()
    assert index.index(flagship) < index.index("full_illustrated_research_manuscript.pdf")
    assert "retrospective companion" in index
