#!/usr/bin/env bash
# Deterministic build of the RES-783 carousel.
#   1. tools/build_carousel.py  receipts + generator routines -> output/carousel.html, ledger
#   2. tools/export.mjs         Chromium (playwright-core 1.64.1) -> PDF, page PNGs, previews
#   3. tools/finalize.py        fixed PDF dates, structural checks, SHA256SUMS
# Requirements: Python 3.12 with the repository installed (numpy), Node 22, `npm ci` here,
# and `npx playwright-core install chromium-headless-shell`.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$REPO/.venv/bin/python}"
[[ -x "$PYTHON_BIN" ]] || PYTHON_BIN="$(command -v python3)"
cd "$HERE"
[[ -d node_modules/playwright-core && -d node_modules/katex ]] || npm ci
export TZ=UTC
"$PYTHON_BIN" tools/build_carousel.py
node tools/export.mjs
"$PYTHON_BIN" tools/finalize.py
