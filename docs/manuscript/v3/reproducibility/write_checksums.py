"""Write SHA-256 checksums for the V3 deliverables, excluding build scratch."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ARTIFACT_SHA256SUMS"
EXCLUDED_DIRS = {"build", "__pycache__", ".venv", "toolchain"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        files.append((digest(path), relative.as_posix()))
    MANIFEST.write_text("".join(f"{sha}  {name}\n" for sha, name in files), encoding="utf-8")
    print(f"Wrote {MANIFEST.name} for {len(files)} deliverable files.")


if __name__ == "__main__":
    main()
