"""Write ARTIFACT_SHA256SUMS for every packaged file (excludes build outputs and toolchain)."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"build", "toolchain", ".venv", "__pycache__"}
files = sorted(
    p for p in ROOT.rglob("*") if p.is_file() and not SKIP.intersection(p.relative_to(ROOT).parts) and p.name != "ARTIFACT_SHA256SUMS"
)
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}" for p in files]
(ROOT / "ARTIFACT_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(lines), "files")
