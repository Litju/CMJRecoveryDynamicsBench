"""Write a page-by-page inventory for the primary illustrated manuscript."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "full_illustrated_research_manuscript.pdf"
PLAN = ROOT / "reports" / "figure_evidence_plan.csv"
REPORT = ROOT / "reports" / "full_illustrated_page_figure_inventory.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    with PLAN.open(newline="", encoding="utf-8") as stream:
        claims = {int(row["figure"]): row["question"] for row in csv.DictReader(stream)}
    document = fitz.open(PDF)
    page_figures = {}
    for number, page in enumerate(document, start=1):
        text = page.get_text("text")
        matches = re.findall(r"(?m)^\s*Fig\.?\s*(\d+)\.\s+[A-Z]", text)
        for figure in matches:
            figure_number = int(figure)
            assert figure_number not in page_figures, f"Figure {figure_number} caption appears on multiple pages"
            page_figures[figure_number] = number
    assert set(page_figures) == set(range(1, 11)), f"Missing figure caption pages: {sorted(set(range(1, 11)) - set(page_figures))}"

    figures_by_page = {}
    for figure, page in page_figures.items():
        figures_by_page.setdefault(page, []).append(figure)
    lines = [
        "# Primary manuscript page-by-page figure inventory",
        "",
        f"PDF: `{PDF.name}`",
        f"SHA-256: `{sha256(PDF)}`",
        f"Pages: {len(document)}",
        "",
        "Each figure entry names the research question its chart or scientific illustration supports. Pages without an embedded figure are marked explicitly.",
        "",
    ]
    for page in range(1, len(document) + 1):
        figures = sorted(figures_by_page.get(page, []))
        if not figures:
            lines.append(f"- **Page {page}:** No embedded figure.")
            continue
        lines.append(f"- **Page {page}:**")
        for figure in figures:
            lines.append(f"  - **Fig. {figure}:** {claims[figure]}")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    document.close()
    print(f"Wrote {REPORT.name} for {len(page_figures)} figures across {page} pages.")


if __name__ == "__main__":
    main()
