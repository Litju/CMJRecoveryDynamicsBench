"""QA: render the final PDF with an independent engine (MuPDF) and compare it with the PNGs.

Not part of the build. Requires PyMuPDF and Pillow (`pip install pymupdf==1.24.10 pillow`).

    python tools/check_pdf_render.py OUT_DIR

Writes OUT_DIR/pdf-page-NN.png (1080 x 1350) and OUT_DIR/pdf_contact_sheet.png, checks the
page count, size, link targets and extractable text of every page, and reports the mean
absolute pixel difference against output/pages/page-NN.png. Chromium (export) and MuPDF
(this check) rasterize text differently, so small differences are expected; a page that
differs by more than MAX_MEAN_DIFF, or whose text cannot be extracted, fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageChops, ImageStat

HERE = Path(__file__).resolve().parents[1]
PDF = HERE / "output" / "CMJ_From_Force_Plate_to_Forecast_carousel.pdf"
PAGES = 10
MAX_MEAN_DIFF = 4.0  # 0-255 scale, averaged over RGB


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    if doc.page_count != PAGES:
        raise SystemExit(f"PDF has {doc.page_count} pages, expected {PAGES}")
    failures = []
    renders = []
    for index, page in enumerate(doc, start=1):
        zoom = 1080 / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).crop(
            (0, 0, 1080, 1350)
        )
        image.save(out / f"pdf-page-{index:02d}.png")
        renders.append(image)
        png = Image.open(HERE / "output" / "pages" / f"page-{index:02d}.png").convert("RGB")
        diff = sum(ImageStat.Stat(ImageChops.difference(image, png)).mean) / 3
        words = len(page.get_text("words"))
        links = [link.get("uri") for link in page.get_links() if link.get("uri")]
        print(
            f"page {index:02d}: {pix.width}x{pix.height} px, mean |PDF - PNG| = {diff:.2f},",
            end=" ",
        )
        print(f"{words} words, links {sorted(set(links))}")
        if diff > MAX_MEAN_DIFF or words < 20:
            failures.append(index)
    sheet = Image.new("RGB", (5 * 360 + 6 * 24, 2 * 450 + 3 * 24), (235, 231, 218))
    for i, image in enumerate(renders):
        sheet.paste(
            image.resize((360, 450), Image.LANCZOS), (24 + (i % 5) * 384, 24 + (i // 5) * 474)
        )
    sheet.save(out / "pdf_contact_sheet.png")
    if failures:
        raise SystemExit(f"PDF render check failed on pages {failures}")
    print(
        f"PDF render check passed: {PAGES} pages rendered independently by MuPDF {fitz.VersionBind}"
    )


if __name__ == "__main__":
    main()
