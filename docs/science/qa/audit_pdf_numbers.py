# pyright: basic, reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false
"""Independent audit: every 4+-decimal number in the flagship PDFs must come from the receipt.

Reads the rendered PDFs (not the LaTeX), so it checks what a reader sees. Requires PyMuPDF.
usage: python audit_pdf_numbers.py <repo-root>
"""

import json
import re
import sys
from pathlib import Path

import fitz

root = Path(sys.argv[1])
receipt = json.loads((root / "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text())
values: list[float] = []


def walk(node: object) -> None:
    if isinstance(node, dict):
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)
    elif isinstance(node, float):
        values.append(node)


walk(receipt["across_root_variability"])
walk(receipt["independent_test_roots"])
av = receipt["across_root_variability"]
derived = [
    av[k]["root_mean_nrmse"] - av[b]["root_mean_nrmse"]
    for k, b in (
        ("ridge_no_prior_history", "ridge_full"),
        ("ridge_no_current_exposure", "ridge_full"),
        ("ridge_no_participant_context", "ridge_full"),
        ("structured_no_prior_history", "structured_full"),
    )
]
values += derived
CONSTANTS = {
    "9.80665",
    "0.0025",
    "0.0035",
    "0.0060",
    "0.0090",
    "0.0030",
    "0.0080",
    "0.0055",
    "0.006",
}
FORBIDDEN = ("leaderboard", "peak mean force", "physiological time constant")
bad = 0
for name in (
    "full_illustrated_manuscript.pdf",
    "academic_review_manuscript.pdf",
    "technical_supplement.pdf",
):
    text = "\n".join(page.get_text() for page in fitz.open(root / "docs/manuscript/v4" / name))
    text = text.replace("−", "-")
    cut = text.rfind("References")  # DOIs and arXiv identifiers are not results
    if name != "technical_supplement.pdf" and cut > 0:
        text = text[:cut]
    found = set(re.findall(r"[+-]?\d+\.\d{4,}", text))
    unmatched = []
    for token in sorted(found):
        digits = len(token.split(".")[1])
        number = abs(float(token.lstrip("+")))
        if token.lstrip("+-") in CONSTANTS:
            continue
        if not any(
            round(abs(v), digits) == number or abs(abs(v) - number) < 0.5 * 10**-digits + 1e-12
            for v in values
        ):
            unmatched.append(token)
    hits = [f for f in FORBIDDEN if f in text.lower()]
    print(f"{name}: {len(found)} numbers, {len(unmatched)} unmatched {unmatched}, forbidden {hits}")
    bad += len(unmatched) + len(hits)
sys.exit(1 if bad else 0)
