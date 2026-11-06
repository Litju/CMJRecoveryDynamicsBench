# CMJRecoveryDynamicsBench M10 V3 owner-review package

This V3 owner-review package contains one LaTeX manuscript source, two editions of that article, a technical supplement, and ten source-bound scientific figures. It preserves the V2 package and the public repository manuscript.

## Article title

Recovering reproducibility in scientific machine learning: Reconstruction and numerical qualification of countermovement-jump recovery models

## Main outputs

- academic_review_manuscript.pdf: single-column, double-spaced, continuously line-numbered review copy. Captions and tables follow first citation; figure files remain separate.
- integrated_scientific_reading_edition.pdf: same manuscript source and tables with vector figures placed next to the relevant discussion.
- technical_supplement.pdf: route-level qualification, formulation, full cell result, bootstrap, and protocol tables.

The publication structure follows a PLOS ONE full-length Research Article, with a journal-neutral review appearance. The reading edition is an internal editorial version, not a journal submission PDF. Names, affiliations, author roles, funding, conflicts, and final publication declarations remain for human confirmation.

## Regenerate

The figure program reads only the bundled release-linked public source snapshots, the published synthetic receipts, and the sanitized route tables. It performs no training, model fitting, checkpoint inference, athlete-data acquisition, or empirical scoring.

Use Python 3.12.13 with the exact packages in reproducibility/requirements.lock, and Tectonic 0.17.0. Run these commands from this directory:

```sh
uv python install 3.12.13
uv venv .venv-v3 --python 3.12.13
uv pip sync --python .venv-v3/bin/python reproducibility/requirements.lock
source .venv-v3/bin/activate
BUILD_TMP="${BUILD_TMP:-.build-tools}"
export PATH="$PWD/$BUILD_TMP/tectonic:$PATH"
bash reproducibility/build.sh
```

The local virtual environment and tool directory are ignored build outputs. Set `BUILD_TMP` to choose another relative tool directory if needed.

The Tectonic binary was built from the official 0.17.0 x86_64 Linux release. Its archive URL and SHA-256, the Python build versions, and figure input hashes are recorded in reports/build_instructions.md and the final checksum manifest. The first LaTeX build downloads Tectonic's TeX support bundle; its resolved identity is recorded in the build report.

reproducibility/build.sh regenerates figures, supplement tables, both PDFs, page images, validation records, and SHA-256 checksums. Rendered page images are under renders/.

## Evidence boundary

The release evidence identity is v1.1.0 at 401f87aad1e4ef4108011fa0c1d769a24f1ad329. The M8 public synthetic receipts retain their own experiment and package identities. The route table is a sanitized summary of private qualification; its figure is reproducible from the summary, while the original weights and inference arrays are not public. No clinical, athlete-validity, transportability, or production-readiness claim is made.

## Review boundary

The owner authorized committing and pushing this package on a separate Git review branch. The qualification reports preserve the earlier private-workspace status at the time of inspection. This package remains an unsubmitted owner-review draft. It has not been uploaded as a preprint, journal submission, DOI record, or software release. It does not replace the V1, V2, or merged public manuscript. Owner visual and editorial review is the next gate.
