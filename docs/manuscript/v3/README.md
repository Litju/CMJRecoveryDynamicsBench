# CMJ recovery research manuscript package

This owner-review package contains one authoritative LaTeX manuscript, a secondary separate-figure review edition, a technical supplement, and ten source-bound scientific figures. It preserves the original V2 evidence and the public repository manuscript.

## Article title

Retrospective reconstruction and numerical qualification of historical countermovement-jump recovery research: An evidence-bounded case study

## Main outputs

- full_illustrated_research_manuscript.pdf: primary owner-review artifact; single-column academic article layout with vector figures embedded near the corresponding Methods or Results discussion.
- academic_review_manuscript.pdf: secondary separate-figure review edition; single-column, double-spaced, continuously line-numbered, with figure captions in first-citation order and figure files supplied separately.
- technical_supplement.pdf: route-level qualification, formulation, full cell result, bootstrap, and protocol tables.

The manuscript uses an established single-column research-article format with academic typography. The separate-figure edition is secondary to the illustrated manuscript. Names, affiliations, author roles, funding, conflicts, and final publication declarations remain for human confirmation.

## Regenerate

The figure program reads only the bundled public source files, the published synthetic-study results, and the public route summaries. It performs no training, model fitting, checkpoint inference, athlete-data acquisition, or empirical scoring.

Use Python 3.12.13 with the exact packages in reproducibility/requirements.lock, and Tectonic 0.17.0. Run these commands from this directory:

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

reproducibility/build.sh regenerates figures, per-figure quantitative receipts and numerical checks, supplement tables, both manuscript editions, page images, validation records, and SHA-256 checksums. Rendered page images are under renders/.

Each quantitative figure has a separate JSON receipt in `reproducibility/figure_receipts/` with exact release-source and local-input SHA-256 digests, the full manuscript caption, population, metric, units, grouping, sample size, uncertainty interpretation, and a passing numerical check.

## Evidence boundary

The release evidence identity is v1.1.0 at 401f87aad1e4ef4108011fa0c1d769a24f1ad329. The public synthetic-study results retain their own experiment and package identities. The route table is a public summary of private qualification; its figure is reproducible from the summary, while the original weights and inference arrays are not public. No clinical, athlete-validity, transportability, or production-readiness claim is made.

## Review boundary

This repair continues the existing Draft PR #38 branch. The qualification reports preserve the earlier private-workspace status at the time of inspection. This package remains an unsubmitted owner-review draft. It has not been uploaded as a preprint, journal submission, DOI record, or software release. It does not replace the V1, V2, or merged public manuscript. Owner visual and editorial review is the next gate; no owner acceptance is recorded here.
