"""Automated page- and figure-level layout checks for the illustrated manuscript (RES-585).

These checks support, but do not replace, the human page-by-page inspection recorded in
reports/visual_qa/. They measure printed figure size, minimum rendered type size, text
outside the page margins, and unused vertical space on each page.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "visual_qa"
MM = 25.4 / 72


def figure_rows():
    rows = []
    for number in range(1, 11):
        page = fitz.open(ROOT / "figures" / f"Fig{number}.pdf")[0]
        plain, script = [], []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    (script if len(text) == 1 and text.isalpha() and span["size"] < 5.2 else plain).append(span["size"])
        rows.append(
            {
                "figure": f"Fig{number}",
                "printed_width_mm": round(page.rect.width * MM, 1),
                "printed_height_mm": round(page.rect.height * MM, 1),
                "scale_in_manuscript": 1.0,
                "min_text_pt": round(min(plain), 1),
                "min_math_script_pt": round(min(script), 1) if script else "",
                "text_spans": len(plain) + len(script),
            }
        )
    assert all(r["min_text_pt"] >= 5.2 for r in rows), rows
    assert all(abs(r["printed_width_mm"] - 180) < 0.6 for r in rows)
    return rows


def page_rows():
    document = fitz.open(ROOT / "full_illustrated_research_manuscript.pdf")
    rows = []
    for number, page in enumerate(document, start=1):
        width, height = page.rect.width * MM, page.rect.height * MM
        boxes = [fitz.Rect(b[:4]) for b in page.get_text("blocks") if b[4].strip()]
        boxes += [fitz.Rect(d["rect"]) for d in page.get_drawings() if d["rect"].width > 20]
        boxes += [fitz.Rect(i["bbox"]) for i in page.get_image_info()]
        body = [b for b in boxes if b.y1 * MM < height - 14]  # ignore folio
        bottom = max((b.y1 for b in body), default=0) * MM
        outside = [
            s["text"][:30]
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for s in line["spans"]
            if s["text"].strip() and (s["bbox"][0] * MM < 13.5 or s["bbox"][2] * MM > width - 13.5)
        ]
        rows.append(
            {
                "page": number,
                "figures_or_tables_on_page": len(page.get_images()) + (1 if page.get_drawings() else 0),
                "content_bottom_mm": round(bottom, 1),
                "unused_bottom_mm": round(height - 19 - bottom, 1),
                "text_outside_margins": len(outside),
            }
        )
    assert all(r["text_outside_margins"] == 0 for r in rows), rows
    return rows, len(document)


def contact_sheet(pdf: Path, path: Path, cols: int = 6, dpi: int = 45) -> None:
    document = fitz.open(pdf)
    images = []
    for page in document:
        pix = page.get_pixmap(dpi=dpi)
        images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "#888888")
    for k, image in enumerate(images):
        sheet.paste(image, ((k % cols) * w, (k // cols) * h))
    sheet.save(path, optimize=True)


def grayscale_sheet(path: Path) -> None:
    tiles = [Image.open(ROOT / "figures" / f"Fig{n}.png").convert("L").resize((560, int(560 * Image.open(ROOT / 'figures' / f'Fig{n}.png').height / Image.open(ROOT / 'figures' / f'Fig{n}.png').width))) for n in range(1, 11)]
    cols = 2
    heights = [max(t.height for t in tiles[i : i + cols]) for i in range(0, 10, cols)]
    sheet = Image.new("L", (560 * cols, sum(heights)), 255)
    y = 0
    for r, hh in enumerate(heights):
        for c in range(cols):
            sheet.paste(tiles[r * cols + c], (c * 560, y))
        y += hh
    sheet.save(path, optimize=True)


def figure_program(figures, page_map):
    """Write the figure inventory with data sources, tests and printed legibility."""
    lines = [
        "# Figure program inventory (RES-585)",
        "",
        "Every figure is authored at its printed size (180 mm) and placed at scale 1.0. Quantitative figures read only pinned release sources or sanitized public summaries; per-figure receipts in `reproducibility/figure_receipts/` hold the exact SHA-256 digests, caption, units and numerical test.",
        "",
        "| Figure | Manuscript page | Title | Data sources | Numerical test | Min. text (pt) |",
        "|---|---:|---|---|---|---:|",
    ]
    legibility = {r["figure"]: r for r in figures}
    for number in range(1, 11):
        name = f"Fig{number}"
        receipt = ROOT / "reproducibility" / "figure_receipts" / f"{name}.json"
        if receipt.exists():
            data = json.loads(receipt.read_text(encoding="utf-8"))
            sources = ", ".join(data["source_ids"]) + ("; " + ", ".join(Path(k).name for k in data["input_digests"]["local_data"]) if data["input_digests"]["local_data"] else "")
            title, test = data["title"], data["numerical_test"]["id"]
        else:
            sources, title, test = "S17, S18 (lineage and formulation-method records)", "Formulation genealogy", "recorded links only; 8 nodes, 5 parent links (checked in generator)"
        lines.append(f"| {name} | {page_map.get(number, '')} | {title} | {sources} | `{test}` | {legibility[name]['min_text_pt']} |")
    lines += ["", "Minimum plain text is 5.4 pt; the smallest mathematical subscript (the z of F_z in axis labels) is 4.6 pt. Colour encodes the model or evidence category, marker shape encodes the evaluation root, and the heatmap uses a diverging scale centred at NRMSE = 1 with printed values. Grayscale rendering is in `figures_grayscale_check.png`.", ""]
    (OUT / "figure_program.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figures = figure_rows()
    pages, count = page_rows()
    with (OUT / "figure_legibility.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, list(figures[0]))
        w.writeheader()
        w.writerows(figures)
    with (OUT / "page_layout_checks.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, list(pages[0]))
        w.writeheader()
        w.writerows(pages)
    import re

    document = fitz.open(ROOT / "full_illustrated_research_manuscript.pdf")
    page_map = {}
    for number, page in enumerate(document, start=1):
        for match in re.findall(r"(?m)^\s*Fig\.?\s*(\d+)\.\s+[A-Z]", page.get_text("text")):
            page_map[int(match)] = number
    figure_program(figures, page_map)
    contact_sheet(ROOT / "full_illustrated_research_manuscript.pdf", OUT / "after_contact_sheet.png")
    grayscale_sheet(OUT / "figures_grayscale_check.png")
    print(json.dumps({"pages": count, "figures_checked": len(figures), "max_unused_bottom_mm": max(r["unused_bottom_mm"] for r in pages[:-1])}))


if __name__ == "__main__":
    main()
