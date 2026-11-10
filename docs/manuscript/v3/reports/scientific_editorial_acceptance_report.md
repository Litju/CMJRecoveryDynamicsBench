# V3 scientific and editorial owner-review report (RES-585 redesign)

**Disposition: ready for owner review as an unsubmitted case study.** PLOS ONE is not currently qualified as a submission destination; no journal decision, submission, preprint, DOI, peer review, or acceptance is implied.

**Internal visual disposition: `RES-585_FIGURE_RICH_MANUSCRIPT_READY_FOR_OWNER_REVIEW`.** This is an agent-side disposition; owner visual acceptance remains pending and PR #38 stays Draft. The page-level evidence and before/after comparison are in [`visual_qa/README.md`](visual_qa/README.md).

## Article identity and scientific contribution

**Title:** *Retrospective reconstruction and numerical qualification of historical countermovement-jump recovery research: An evidence-bounded case study*

The article is positioned as a retrospective reconstruction and numerical qualification case study of one partially preserved scientific-ML program. It is not a new universal provenance framework, neural-network algorithm, athlete predictor, clinical validation study, or state-of-the-art comparison.

It answers three questions:

1. **Historical reconstructability:** Eight formulation identities and nine historical neural model families are represented in the authenticated release-linked record. Five parent links are explicit; three direct ancestry links remain unresolved. The public archive describes model topology and measurement contracts, but the fitted checkpoints, preprocessing values, and original route execution remain restricted. Rich-history training and validation row counts still differ by 48 and four, respectively.
2. **Numerical reproducibility:** The privately recorded qualification reports exact original-source CPU output equality for all 18 model-repeat routes. Comparisons with archived GPU outputs pass for eight M0–M3 routes and fail for ten M4–M8 routes under the unchanged elementwise tolerance. This is not a fresh public inference, an original-GPU replay, or an explanation of the failures.
3. **Scientific comparability:** The existing public synthetic study compares four reference models at H24/H48/H72 across six separately normalized force/impulse cells and three fixed roots from one generator. Mean six-cell NRMSE is 2.430659 for zero innovation, 1.036038 for training mean, 0.736270 for ridge, and 0.773316 for the structured comparator. The ranking is descriptive, is conditional on that generator, and says nothing about historical model accuracy or athlete validity.

The contribution is the evidence-bounded reconstruction of this archive and the lesson that software identity, source-level computation, historical runtime compatibility, measurement authority, public reproducibility, and predictive validity require separate evidence. Transferability of this approach has not been experimentally tested.

## Prior-work differentiation

The related-work section now treats the cited systems and standards as complementary prior work, without capability claims that were not tested:

- Pineau et al. describe the NeurIPS code policy, community reproducibility challenge, and reporting checklist; Goodman et al. discuss inconsistent terminology. This study applies those concerns retrospectively and reports operational evidence states.
- MLflow Tracking documents run logging; DVC documents experiment management and data/model versioning. Their functionality is not benchmarked here, and the paper does not claim they cannot support retrospective recovery.
- W3C PROV-O supplies a provenance vocabulary; RO-Crate specifies research-object packaging; FAIR4RS states research-software FAIR goals. The V3 export does not claim PROV-O or RO-Crate conformance.
- ACM Artifact Review and Badging v1.1 separates artifact evaluation, availability, and results validation. This manuscript has not received an ACM artifact review or badge; the original-model results are private qualification summaries, not public artifact reproduction.
- Morris, White, and Crowther's ADEMP structure is used to report the existing synthetic study. The study was not rerun for V3.

The 17-entry bibliography is checked against stored bibliographic metadata and the versioned/current official pages. The ACM policy is cited as v1.1 (24 August 2020); RO-Crate is cited as specification 1.3 (22 June 2026); MLflow and DVC documentation are cited with access date 6 November 2026.

## Claim audit and evidence authority

The V2 553-entry claim ledger is preserved unchanged at SHA-256 `a83f261ab4881794576c959526a56eb51ac4016101f36c5c85fc97e629351187`. The V3 differential audit now contains 510 current units (485 substantive claims and 25 declaration records) plus three removed V2 statements; statuses are 128 retained, 312 modified, 45 new, 3 removed and 25 administrative. The RES-585 reconciliation (145 changed or new units, 0 numeric-check failures against the pinned corpus) is in `claims_differential_audit.md` and `claims_differential_changes_RES-585.csv`. The audit is agent-only internal source review, not human scientific validation or peer review; owner-confirmation items (authorship, funding/conflicts, the no-human-study statement, AI-use details, human review) remain open.

All 35 release-linked source snapshots verify against their v1.1.0 identities. Receipt arithmetic checks cover 24 six-cell/root values, six stored bootstrap records, and 18 route summaries. The V2 preservation check confirms the unchanged 139-file inventory. The original v1.1.0 software identity remains commit `401f87aad1e4ef4108011fa0c1d769a24f1ad329`.

Publicly reproducible work includes release-linked software records, public synthetic-study protocols and receipts, source-hash verification, receipt arithmetic, and figure regeneration from public inputs. Historical model-route qualification is privately recorded and summarized with public summaries; a reader cannot rerun it from the public package. The original checkpoints, fitted preprocessing values, saved inference arrays, and restricted observation/reconciliation records are not redistributed.

## Figures and academic editions

The ten figures were redesigned as multi-panel quantitative graphics (details in [`visual_qa/figure_program.md`](visual_qa/figure_program.md)): (1) formulation genealogy with eight cards, five parent links and three unresolved ancestries; (2) camp-level study design; (3) M8 computational graph with component matrix and parameter counts; (4) 18-route qualification matrix with discrepancy and failing-element panels; (5) analytical force-time curve contrasting gross mean force, peak force and net impulse, with the scaled assessment chronology; (6) six-cell small multiples; (7) model-by-cell heatmap with per-root structured-minus-ridge differences; (8) forest plot of the recorded bootstrap intervals; (9) ablations and nested-camp results; (10) rich-history row-count differences and the evidence-boundary matrix. The force-time curve is analytical, not athlete data. Each quantitative figure has an input-digest receipt and numerical checks.

The primary `full_illustrated_research_manuscript.pdf` is a 12-page two-column article. The secondary `academic_review_manuscript.pdf` is single-column, double-spaced and line-numbered (26 pages). The technical supplement is 4 pages. Rendering, legibility measurements, the grayscale check and the page-by-page inspection record are under `reports/visual_qa/`. PLOS-format TIFFs remain flattened RGB, 600 dpi, LZW-compressed and under 10 MB; the review copy and sources are owner-review materials, not a submission package.

Repeated generic AI-use sentences were removed from scientific captions. The consolidated AI-use statement remains in the integrity/declarations section and discloses manuscript and plotting-code assistance; authors must verify it before any submission.

## Data availability and venue status

The public software release and synthetic study materials are available; original fitted checkpoints and restricted records are not. The package documents no approved controlled-access mechanism or independent institutional contact, so no access-on-request statement is made. The public synthetic study answers RQ3 only and does not validate private RQ1/RQ2 route claims.

PLOS ONE is used only as a structural reference. Its current data policy requires public availability by default and specifies conditions for restricted data. Since the underlying route results cannot be reproduced from the public package and no permitted access route is documented, PLOS ONE eligibility is unresolved and the journal is not currently qualified as a submission destination. No alternative venue is designated submission-ready. The accompanying [`data_software_availability.md`](data_software_availability.md) provides the claim-by-claim access table and a conditional venue strategy.

## Outstanding owner decisions

- Confirm author names, affiliations, corresponding-author details, ORCID, CRediT roles, funding, competing interests, and final ethics/data statements.
- Review the 488 substantive claim units (plus 12 author/AI disclosure records) and confirm the historical artifact-rights and access description.
- Decide whether any legitimate controlled-access mechanism can be documented; do not add an “available upon request” promise without one.
- Perform the visual owner acceptance of the two-column layout (and manual NVDA acceptance if required). Do not merge PR #38 before explicit owner visual approval.
- Choose a venue only after the access and scope questions are resolved. No submission, preprint, DOI, release, or researcher outreach is authorized by this owner-review package.
