#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN=python3
if [[ -x "$ROOT_DIR/toolchain/tectonic" ]]; then
  TECTONIC_BIN="$ROOT_DIR/toolchain/tectonic"
else
  TECTONIC_BIN="$(command -v tectonic)"
fi
TEX_BUNDLE="https://relay.fullyjustified.net/default_bundle_v33.tar"

mkdir -p build/academic_review build/full_illustrated build/technical_supplement
for BUILD_DIR in build/academic_review build/full_illustrated; do
  cp plos2025.bst "$BUILD_DIR/plos2025.bst"
  mkdir -p "$BUILD_DIR/bibliography"
  cp bibliography/references.bib "$BUILD_DIR/bibliography/references.bib"
done
"$PYTHON_BIN" reproducibility/refresh_claims_audit.py
"$PYTHON_BIN" reproducibility/verify_package.py --pre-build
"$PYTHON_BIN" figure_source/generate_figures.py
"$PYTHON_BIN" reproducibility/verify_quantitative_figures.py
"$PYTHON_BIN" reproducibility/generate_supplement_tables.py

export SOURCE_DATE_EPOCH=1793836800
export TZ=UTC
if [[ "$("$TECTONIC_BIN" --version)" != "Tectonic 0.17.0" ]]; then
  echo "Tectonic 0.17.0 is required." >&2
  exit 1
fi
"$TECTONIC_BIN" -X compile --bundle "$TEX_BUNDLE" --keep-intermediates --keep-logs --outdir build/academic_review manuscript-review.tex
"$TECTONIC_BIN" -X compile --bundle "$TEX_BUNDLE" --keep-intermediates --keep-logs --outdir build/full_illustrated manuscript.tex
"$TECTONIC_BIN" -X compile --bundle "$TEX_BUNDLE" --keep-intermediates --keep-logs --outdir build/technical_supplement supplement/technical_supplement.tex

cp build/academic_review/manuscript-review.pdf academic_review_manuscript.pdf
cp build/full_illustrated/manuscript.pdf full_illustrated_research_manuscript.pdf
cp build/technical_supplement/technical_supplement.pdf technical_supplement.pdf

"$PYTHON_BIN" reproducibility/render_pdfs.py
"$PYTHON_BIN" reproducibility/write_page_inventory.py
"$PYTHON_BIN" reproducibility/qa_visual_report.py
"$PYTHON_BIN" reproducibility/verify_package.py --post-build
"$PYTHON_BIN" reproducibility/write_checksums.py
