"""Render every V3 PDF page at reading resolution and build review contact sheets."""

from __future__ import annotations

import json
from pathlib import Path

import fitz
from PIL import Image, ImageOps, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DPI = 144
SCALE = DPI / 72
PDFS = {
    "academic_review": ROOT / "academic_review_manuscript.pdf",
    "reading_edition": ROOT / "integrated_scientific_reading_edition.pdf",
    "technical_supplement": ROOT / "technical_supplement.pdf",
}


def render_one(name: str, path: Path):
    folder = ROOT / "renders" / name
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("page-*.png"):
        stale.unlink()
    for stale in folder.glob("contact-*.png"):
        stale.unlink()

    doc = fitz.open(path)
    pages = []
    thumbs = []
    for index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
        image_path = folder / f"page-{index:03d}.png"
        pix.save(image_path)
        text = page.get_text("text")
        blocks = [b for b in page.get_text("blocks") if len(b) > 4 and isinstance(b[4], str) and b[4].strip()]
        outside = [
            b[:4]
            for b in blocks
            if b[0] < -0.5 or b[1] < -0.5 or b[2] > page.rect.width + 0.5 or b[3] > page.rect.height + 0.5
        ]
        pages.append(
            {
                "page": index,
                "image": image_path.relative_to(ROOT).as_posix(),
                "image_size_px": [pix.width, pix.height],
                "page_size_points": [round(page.rect.width, 2), round(page.rect.height, 2)],
                "text_characters": len(text),
                "text_blocks": len(blocks),
                "embedded_images": len(page.get_images(full=True)),
                "vector_drawings": len(page.get_drawings()),
                "text_blocks_outside_page": outside,
            }
        )
        im = Image.open(image_path).convert("RGB")
        im.thumbnail((420, 594), Image.Resampling.LANCZOS)
        im = ImageOps.expand(im, border=1, fill=(185, 192, 198))
        thumbs.append((index, im.copy()))

    for start in range(0, len(thumbs), 4):
        batch = thumbs[start : start + 4]
        cell_w, cell_h = 424, 598
        canvas = Image.new("RGB", (cell_w * 2, cell_h * 2), "white")
        draw = ImageDraw.Draw(canvas)
        for pos, (page_number, im) in enumerate(batch):
            x = (pos % 2) * cell_w + (cell_w - im.width) // 2
            y = (pos // 2) * cell_h + 4
            canvas.paste(im, (x, y + 18))
            draw.text((x + 2, y + 2), f"Page {page_number}", fill=(35, 42, 48))
        first = batch[0][0]
        last = batch[-1][0]
        canvas.save(folder / f"contact-{first:03d}-{last:03d}.png", optimize=True)

    doc.close()
    return {
        "pdf": path.name,
        "pages": len(pages),
        "render_dpi": DPI,
        "inspection": "Every page exported at 144 dpi; page image contact sheets are provided for navigation.",
        "page_records": pages,
    }


def main():
    results = {}
    for name, pdf in PDFS.items():
        if not pdf.is_file():
            raise FileNotFoundError(pdf)
        results[name] = render_one(name, pdf)
    for name, result in results.items():
        assert result["pages"] > 0
        assert all(record["text_characters"] > 20 for record in result["page_records"]), f"Low-text page in {name}"
        assert all(not record["text_blocks_outside_page"] for record in result["page_records"]), f"Text outside page in {name}"
    target = ROOT / "reports" / "rendered_page_inspection.json"
    target.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: result["pages"] for name, result in results.items()}, indent=2))


if __name__ == "__main__":
    main()
