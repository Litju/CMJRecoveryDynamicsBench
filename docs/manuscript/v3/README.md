# CMJ recovery research manuscript package

This owner-review package contains one authoritative LaTeX manuscript, a secondary separate-figure review edition, a technical supplement, and ten source-bound scientific figures. It preserves the original V2 evidence and the public repository manuscript.

## Article title

Retrospective reconstruction and numerical qualification of historical countermovement-jump recovery research: An evidence-bounded case study

## Start here

**Read [`full_illustrated_research_manuscript.pdf`](full_illustrated_research_manuscript.pdf)** — the primary owner-review document: a 12-page, two-column A4 research article with ten full-width quantitative figures (180 mm design width, placed at scale 1.0) and three decimal-aligned tables beside the argument they support. Everything else in this folder supports it.

| File | Purpose |
|---|---|
| `full_illustrated_research_manuscript.pdf` | Primary figure-rich article (two columns, editorial layout). |
| `academic_review_manuscript.pdf` | Same source as a single-column, double-spaced, line-numbered review copy; figure captions in citation order, figure files supplied separately. |
| `technical_supplement.pdf` | Route-level, formulation, cell-level, bootstrap and protocol tables. |
| `figures/Fig1`–`Fig10` (`.pdf`, `.svg`, `.png`, `.tif`) | Independently exportable figures: vector PDF, editable SVG, 300 dpi PNG preview, flattened 600 dpi LZW TIFF. |
| `reports/visual_qa/` | Before/after comparison, page-level inspection record, figure legibility and layout checks. |
| `reports/force_target_provenance_note.md` | Why the force outcome is *mean concentric-force innovation* and what the legacy registered identifier means. |
| `reports/claims_differential_audit.*` | Claim-by-claim audit and the RES-585 reconciliation ledger. |
| `ARTIFACT_SHA256SUMS` | SHA-256 inventory of every deliverable. |

There is one authoritative LaTeX source, `manuscript.tex`; `manuscript-review.tex` only defines the review-edition switch and inputs it. The figures come from `figure_source/generate_figures.py` and the style module `figure_source/figstyle.py`.

## Force-target terminology

The registered evaluation cell `relative_peak_mean_force_innovation` scores the generated target `label.relative_mean_concentric_force_innovation`: the baseline-relative change in **gross mean concentric force per unit mass (N/kg)**, i.e. the criterion-assessment mean minus the baseline-assessment mean of three simulated concentric-force trials. It is not peak force and not net impulse. The article therefore says "mean concentric-force innovation"; the legacy identifier is kept unchanged in frozen results and explained in the Methods and the provenance note. `tests/test_force_target_semantics.py` checks the mapping.

The manuscript uses an established academic layout: Palatino-style serif body, sans-serif headings, numbered equations, booktabs tables and one consistent figure typeface (DejaVu Sans, bundled with Matplotlib). Names, affiliations, author roles, funding, conflicts and final publication declarations remain for human confirmation.

## Regenerate

The figure program reads only the bundled public source files, the published synthetic-study results, and the public route summaries. It performs no training, model fitting, checkpoint inference, athlete-data acquisition, or empirical scoring.

Use Python 3.12.13 with the exact packages in reproducibility/requirements.lock, and Tectonic 0.17.0 (a XeTeX engine; TeX Gyre Pagella-style body and TeX Gyre Heros headings come from the pinned support bundle). Run these commands from this directory:

```sh
uv python install 3.12.13
uv venv .venv --python 3.12.13
uv pip sync --python .venv/bin/python reproducibility/requirements.lock
source .venv/bin/activate
BUILD_TMP="${BUILD_TMP:-toolchain}"
export PATH="$PWD/$BUILD_TMP:$PATH"
bash reproducibility/build.sh
```

The local virtual environment and `toolchain/` directory are ignored build outputs. Set `BUILD_TMP` to choose another relative tool directory if needed.

The Tectonic binary was built from the official 0.17.0 x86_64 Linux release. Its archive URL and SHA-256, the Python build versions, and figure input hashes are recorded in reports/build_instructions.md and the final checksum manifest. The first LaTeX build downloads Tectonic's TeX support bundle; its resolved identity is recorded in the build report.

reproducibility/build.sh reconciles the claims audit with the manuscript source, regenerates the figures (about two minutes, mainly the 600 dpi TIFFs), per-figure quantitative receipts and numerical checks, supplement tables, all three PDFs, page images, the visual-QA measurements, validation records and SHA-256 checksums. Rendered page images are under renders/.

Each quantitative figure has a separate JSON receipt in `reproducibility/figure_receipts/` with exact release-source and local-input SHA-256 digests, the full manuscript caption, population, metric, units, grouping, sample size, uncertainty interpretation, and a passing numerical check.

## Evidence boundary

The release evidence identity is v1.1.0 at 401f87aad1e4ef4108011fa0c1d769a24f1ad329. The public synthetic-study results retain their own experiment and package identities. The route table is a public summary of private qualification; its figure is reproducible from the summary, while the original weights and inference arrays are not public. No clinical, athlete-validity, transportability, or production-readiness claim is made.

## Review boundary

This repair continues the existing Draft PR #38 branch. The qualification reports preserve the earlier private-workspace status at the time of inspection. This package remains an unsubmitted owner-review draft. It has not been uploaded as a preprint, journal submission, DOI record, or software release. It does not replace the V1, V2, or merged public manuscript. Owner visual and editorial review is the next gate; no owner acceptance is recorded here.
