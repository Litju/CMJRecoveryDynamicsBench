#!/usr/bin/env bash
# Rebuild figures, tables, supplement and the three PDFs. Requires Python 3.12 with
# reproducibility/requirements.lock and Tectonic 0.17.0 on PATH (or toolchain/tectonic).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT_DIR/toolchain/tectonic" ]]; then TECTONIC_BIN="$ROOT_DIR/toolchain/tectonic"; else TECTONIC_BIN="$(command -v tectonic)"; fi
BUNDLE="https://relay.fullyjustified.net/default_bundle_v33.tar"
[[ "$("$TECTONIC_BIN" --version)" == "Tectonic 0.17.0" ]] || { echo "Tectonic 0.17.0 required" >&2; exit 1; }
"$PYTHON_BIN" figure_source/generate_figures.py
"$PYTHON_BIN" figure_source/generate_tables.py
"$PYTHON_BIN" figure_source/generate_supplement.py
export SOURCE_DATE_EPOCH=1793836800 TZ=UTC
for target in full review supp; do
  mkdir -p "build/$target/bibliography"
  cp plos2025.bst "build/$target/"; cp bibliography/references.bib "build/$target/bibliography/"
done
"$TECTONIC_BIN" -X compile --bundle "$BUNDLE" --keep-intermediates --keep-logs --outdir build/full manuscript.tex
"$TECTONIC_BIN" -X compile --bundle "$BUNDLE" --keep-intermediates --keep-logs --outdir build/review manuscript-review.tex
"$TECTONIC_BIN" -X compile --bundle "$BUNDLE" --keep-intermediates --keep-logs --outdir build/supp supplement/technical_supplement.tex
cp build/full/manuscript.pdf full_illustrated_manuscript.pdf
cp build/review/manuscript-review.pdf academic_review_manuscript.pdf
cp build/supp/technical_supplement.pdf technical_supplement.pdf
