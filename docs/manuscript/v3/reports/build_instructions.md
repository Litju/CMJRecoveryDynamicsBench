# Reproducible V3 build instructions

## Build scope

The build consumes the public release-linked evidence snapshots in this package and the sanitized route-level qualification CSVs. It generates vector and raster figures, per-figure numerical receipts, formatted receipt tables, the fully illustrated primary manuscript, the separate-figure review edition, the technical supplement, and rendered page images. It does not load the research package, train or fit a model, deserialize a checkpoint, run inference, bootstrap outcomes, generate benchmark rows, or access athlete data.

## Exact environment recorded for this build

- Operating system: Ubuntu 24.04.3 LTS, x86_64.
- Python: CPython 3.12.13.
- Python packages: see reproducibility/requirements.lock. The resolved environment is also recorded in reports/build_environment.json.
- LaTeX engine: Tectonic 0.17.0, x86_64 GNU/Linux release archive SHA-256 1a715688baf591e650c8aeb160ae934e181685eecbb38b317de30b269ac5d606; extracted executable SHA-256 2b3a86250906c92ed0a3ae8aaa454ec55bd6cede8593b3e549640177f6aecaa3.
- Tectonic support bundle: https://relay.fullyjustified.net/default_bundle_v33.tar; the resolved bundle-content SHA-256 recorded in the local build is 6ffe055852f8faf66c0acbe1a7fb27f87b869a90bad1204f3bf4d9683f597c7c.
- Bibliography: BibTeX with the PLOS 2025 Vancouver style distributed in the current PLOS ONE LaTeX template (version 3.8, April 2026).
- PDF page rendering: PyMuPDF 1.26.7 at 144 dpi. Every PDF page is written as an individual PNG and grouped into contact sheets for navigation.
- Tectonic uses SOURCE_DATE_EPOCH=1793836800, corresponding to 2026-11-05 00:00:00 UTC.

## Clean environment setup

The V3 folder contains all public scientific inputs needed to regenerate its figures. The only network downloads are the pinned Python/LaTeX tools and Tectonic support bundle. The commands below use paths relative to the V3 package root; set `BUILD_TMP` to choose a different local tools directory.

```sh
BUILD_TMP="${BUILD_TMP:-toolchain}"
uv python install 3.12.13
uv venv .venv --python 3.12.13
uv pip sync --python .venv/bin/python reproducibility/requirements.lock
source .venv/bin/activate

mkdir -p "$BUILD_TMP"
curl -fLsS -o "$BUILD_TMP/tectonic-0.17.0.tar.gz" https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-unknown-linux-gnu.tar.gz
echo "1a715688baf591e650c8aeb160ae934e181685eecbb38b317de30b269ac5d606  $BUILD_TMP/tectonic-0.17.0.tar.gz" | sha256sum -c -
tar -xzf "$BUILD_TMP/tectonic-0.17.0.tar.gz" -C "$BUILD_TMP"
export PATH="$PWD/$BUILD_TMP:$PATH"

bash reproducibility/build.sh
```

The script regenerates Fig1–Fig10 in vector PDF/SVG and raster PNG/TIFF. TIFFs are flattened RGB, 600 dpi, and LZW-compressed. It writes one numerical receipt for each quantitative figure, including exact input and figure-PDF digests and calculation checks. It compiles `full_illustrated_research_manuscript.pdf` as the primary owner-review paper and `academic_review_manuscript.pdf` as a secondary double-spaced, line-numbered edition with separate figure files. The technical supplement compiles from `supplement/technical_supplement.tex`. The renderer writes one PNG per page at 144 dpi; contact sheets are navigation aids, and the page-by-page visual review findings are recorded separately. The build validates source and receipt links, checks PLOS TIFF dimensions/size/channel requirements, and writes `ARTIFACT_SHA256SUMS`.

## Evidence identities

All 35 public source snapshots are checked against their source_id, immutable release commit, and SHA-256 in evidence/release_sources/sources.json. The M8 synthetic study has a separate study-specific package source SHA-256, protocol hash, selection-lock hash, and scientific-results hash in reports/build_environment.json and S19_manifest.json. The script checks that the 24 six-cell values, root/cell summaries, six bootstrap rows, and 18 model-route records match their existing receipts. It performs arithmetic consistency checks on existing results only.

Sanitized route summaries are not a public re-execution of the original restricted checkpoints. The V3 package intentionally omits checkpoint payloads, fitted parameter values, private path names, and private artifact hashes. The separate V2 preservation record contains only an aggregate inventory digest. An optional local preservation check uses `M10_V2_WORKSPACE` to locate a V2 copy and reads it without writing any V2 files.

## Output and checksum boundaries

The three PDFs are written at the V3 root. Individual page images and contact sheets are in `renders/academic_review`, `renders/full_illustrated`, and `renders/technical_supplement`. `ARTIFACT_SHA256SUMS` covers the V3 manuscript, bibliography, figures, evidence snapshots, scripts, reports, and page images. It excludes build scratch, the optional local Tectonic executable, and the checksum file itself.
