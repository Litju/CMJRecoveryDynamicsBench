"""Finalize the exported carousel: fixed PDF dates, structural checks and checksums.

Chromium stamps the wall-clock time into the PDF Info dictionary. The stamp is
replaced in place by a fixed value of identical length, so cross-reference
offsets stay valid and the PDF is byte-reproducible for a given toolchain.
"""

# ruff: noqa: E501  (receipt URLs and messages are long literal strings)
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OUTPUT = HERE / "output"
PDF = OUTPUT / "CMJ_From_Force_Plate_to_Forecast_carousel.pdf"
TITLE = "From Force Plate to Forecast: Modeling CMJ Performance Changes Following Training"
FIXED_DATE = b"D:20261124000000+00'00'"
EXPECTED_LINKS = {
    "https://recovery-observatory.vercel.app/",
    "https://github.com/Litju/CMJRecoveryDynamicsBench",
    "https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf",
}
PAGES = 10
PAGE_PX = (1080, 1350)
MANIFEST = HERE / "ARTIFACT_SHA256SUMS"
UNTRACKED = {"node_modules", "__pycache__"}


def fix_pdf_dates(data: bytes) -> bytes:
    def stamp(match: re.Match[bytes]) -> bytes:
        if len(match.group(2)) != len(FIXED_DATE):
            raise SystemExit(f"unexpected PDF date format: {match.group(2)!r}")
        return match.group(1) + FIXED_DATE + b")"

    fixed, count = re.subn(rb"(/(?:CreationDate|ModDate) \()(D:[^)]*)\)", stamp, data)
    if count != 2:
        raise SystemExit(f"expected two PDF date stamps, found {count}")
    return fixed


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path.name} is not a PNG")
    return struct.unpack(">II", head[16:24])


def check_pdf(data: bytes) -> None:
    pages = len(re.findall(rb"/Type\s*/Page(?!s)", data))
    if pages != PAGES:
        raise SystemExit(f"PDF has {pages} pages, expected {PAGES}")
    if f"/Title ({TITLE})".encode() not in data:
        raise SystemExit("PDF title missing or changed")
    links = {m.decode() for m in re.findall(rb"/URI \(([^)]*)\)", data)}
    if links != EXPECTED_LINKS:
        raise SystemExit(f"PDF links {sorted(links)} differ from {sorted(EXPECTED_LINKS)}")
    for box in re.findall(rb"/MediaBox\s*\[([^\]]*)\]", data):
        w, h = (float(v) for v in box.split()[2:4])
        if abs(w / h - 0.8) > 0.002:
            raise SystemExit(f"page is not 4:5 portrait: {w} x {h} pt")
    if b"/AcroForm" in data or b"/JavaScript" in data:
        raise SystemExit("PDF must be flat: no forms or scripts")


def write_manifest() -> None:
    """Hash every package file (sources, tools, outputs, docs); node_modules is not tracked."""
    lines = []
    for path in sorted(HERE.rglob("*")):
        rel = path.relative_to(HERE)
        if path.is_file() and path != MANIFEST and not UNTRACKED.intersection(rel.parts):
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel.as_posix()}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if sys.argv[1:] == ["--manifest-only"]:
        write_manifest()
        print(f"wrote {MANIFEST.name}")
        return
    if not PDF.is_file():
        raise SystemExit("run tools/export.mjs first")
    data = fix_pdf_dates(PDF.read_bytes())
    check_pdf(data)
    PDF.write_bytes(data)
    pngs = sorted((OUTPUT / "pages").glob("page-*.png"))
    if [p.name for p in pngs] != [f"page-{i:02d}.png" for i in range(1, PAGES + 1)]:
        raise SystemExit("page PNGs missing")
    for png in pngs:
        if png_size(png) != PAGE_PX:
            raise SystemExit(f"{png.name} is {png_size(png)}, expected {PAGE_PX}")
    for folder, size in (("phone", (1170, 1464)), ("phone-natural", (390, 488))):
        phones = sorted((OUTPUT / "previews" / folder).glob("phone-*.png"))
        if len(phones) != PAGES or any(png_size(p) != size for p in phones):
            raise SystemExit(f"{folder} previews missing or mis-sized")
    if not (OUTPUT / "previews" / "contact_sheet.png").is_file():
        raise SystemExit("contact sheet missing")
    write_manifest()
    print(
        f"finalized {PDF.name}: {PAGES} pages, title and {len(EXPECTED_LINKS)} links verified; {MANIFEST.name} written"
    )


if __name__ == "__main__":
    main()
