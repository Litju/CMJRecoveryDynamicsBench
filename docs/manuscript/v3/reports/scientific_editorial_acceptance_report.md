# M10 V3 scientific and editorial acceptance report

**Disposition: ready for owner review.** This is a qualified, reviewable research article package. It is not a journal submission, accepted paper, preprint, or replacement of the public manuscript.

## Article identity and architecture

**Title:** *Recovering reproducibility in scientific machine learning: Reconstruction and numerical qualification of countermovement-jump recovery models*

The primary structure follows a full-length PLOS ONE **Research Article**: title/front matter, abstract, Introduction, Related work, Materials and methods, Results, Discussion, Limitations and threats to validity, Reproducibility and availability, Conclusions, declarations, and References. The article has a case-specific research gap and three research questions. Its argument connects formulation and model reconstruction, measurement contracts, numerical qualification, the distinct public synthetic experiment, and the limits of the available evidence.

PLOS is the best primary structural model for this full-length computational reconstruction. PLOS allows articles of any length and permits the appropriate organization of a sound methodological study; its criteria do not require positive results. The PLOS ONE submission guide, LaTeX instructions, figure guide, and data-availability policy were checked against official pages on 5 November 2026: [submission guidelines](https://journals.plos.org/plosone/s/submission-guidelines), [LaTeX instructions](https://journals.plos.org/plosone/s/latex), [figure guidelines](https://journals.plos.org/plosone/s/figures), [data-availability policy](https://journals.plos.org/plosone/s/data-availability), [publication criteria](https://journals.plos.org/plosone/s/criteria-for-publication), and [AI-use policy](https://journals.plos.org/plosone/s/ethical-publishing-practice). The review PDF follows the verified single-column, double-spaced, continuous line-number, Vancouver-reference, figure-caption, and table-placement conventions and uses the current PLOS LaTeX template's `plos2025.bst`. It uses an unbranded `article` class rather than claiming journal affiliation; a submission must still be rebuilt from PLOS's official template and completed in its submission system.

The assessment separately distinguishes Elsevier SoftwareX's short Original Software Publication format from this full-length article; its current OSP template specifies a 4,000-word, six-page main text and up to six figures. JMLR Research Articles and the four-page MLOSS software track are treated as different categories. JSS software-article conventions, TMLR, and JOSS are also assessed in [`journal_formatting_assessment.md`](journal_formatting_assessment.md). The SoftwareX Guide for Authors returned HTTP 403; no inaccessible guide-only requirement is asserted.

## Outputs and source of truth

- [`manuscript.tex`](../manuscript.tex) is the single authoritative article source. The review and reading wrappers select publication-review or inline-figure presentation without duplicating manuscript prose.
- [`academic_review_manuscript.pdf`](../academic_review_manuscript.pdf): 23 pages, single column, double spaced, continuously line numbered, with figures supplied separately.
- [`integrated_scientific_reading_edition.pdf`](../integrated_scientific_reading_edition.pdf): 20 pages, with vector figures integrated near their first substantive discussion.
- [`technical_supplement.pdf`](../technical_supplement.pdf) and [`technical_supplement.tex`](../supplement/technical_supplement.tex): 4 pages of detailed evidence tables, public study protocol, native measurement/analysis contract, and interpretation boundaries.

The review and reading PDFs are built from the same article source. The reading edition is for editorial review; it does not claim journal branding or replace the submission-style review PDF.

## Figure and table inventory

Ten figure families are supplied as PDF, SVG, PNG, and 600-dpi TIFF. Their evidence question, source, method, metric/units, and limitation were documented before plotting in [`figure_evidence_plan.csv`](figure_evidence_plan.csv); the generated [`figure_provenance_ledger.csv`](figure_provenance_ledger.csv) links each figure to source snapshots and hashes.

1. Formulation genealogy with only authenticated parent edges and unresolved ancestry left open.
2. Reconstruction and verification workflow, with computational qualification separate from scientific validity.
3. M0–M8 architecture schematics and parameter-count comparison.
4. Eighteen-route exact-CPU/saved-CUDA qualification matrix, discrepancy magnitudes, and recorded failing-element counts.
5. Native assessment/baseline/H72/D7 chronology separated from synthetic H24/H48/H72 queries.
6. Analytical vertical force-time illustration with concentric onset, takeoff, gross force area, body-weight reference, and signed net-impulse area.
7. Six-cell public synthetic benchmark showing all four reference models, all three evaluation roots, and stored root means.
8. Stored within-root paired camp-bootstrap intervals for model-versus-zero comparisons.
9. Recorded ablations and nested training-camp comparisons, separated by diagnostic family.
10. Categorical reproducibility-scope diagram with public, private, failed/partial, and unestablished evidence boundaries.

The main article has three tables: M0–M8 architecture and parameters; six-cell NRMSE with root sample SD; and overall model means, root SDs, and model scope. The supplement contains six numbered tables covering formulations, architecture, 18 routes, all 24 cell/root rows, six recorded uncertainty rows, and ablation/nested-camp results, plus an unnumbered public protocol table.

## Scientific source and numerical verification

The scientific software remains release `v1.1.0` at immutable source commit `401f87aad1e4ef4108011fa0c1d769a24f1ad329`. The original public synthetic-study receipts retain their separate identities. V3 includes 35 release-linked source snapshots, each hash-checked against its manifest.

The package validator compared the existing receipt arithmetic and sanitized route records without running training, fitting, checkpoint inference, athlete scoring, bootstrap resampling, or historical GPU replay. It checked all 24 six-cell/root rows and their aggregates, all six stored bootstrap records, and all 18 route records. The recorded summary is exact original-source CPU output equality for all 18 routes; saved historical CUDA comparisons pass for eight M0–M3 routes and fail for ten M4–M8 routes under the unchanged `|a-b| <= 10^-5 + 10^-4 |b|` rule. The CUDA outcomes are historical array comparisons, not original-GPU replay. Their cause remains unknown. Private checkpoint arrays and fitted preprocessing values are not in this package, so their route qualification is presented as a privately checked, sanitized record rather than a public re-execution.

The public synthetic study remains separate from the original neural-model native evaluation. Its three roots are from one generator; NRMSE is normalized within each of six H24/H48/H72 × force/impulse cells before equal-weight aggregation. Mean six-cell NRMSE is 0.736270 for ridge, 0.773316 for the structured comparator, 1.036038 for training mean, and 2.430659 for zero innovation. Root sample SD is descriptive. The six recorded bootstrap intervals compare each supported model with zero within each root; no ridge-versus-structured interval is inferred. Native mechanics/evaluation remain H72/D7 and four physical-unit force/impulse cells. The two result programs are never combined.

The documented rich-history materialization differences remain: 48 fewer training rows and four more validation rows in the clean-room materialization relative to the historical record. The manuscript retains this and the CUDA failures as negative findings.

## Mathematics and literature

The article natively typesets the force and gravity-adjusted impulse definitions, assessment baseline and innovation, cellwise RMSE/NRMSE, six-cell aggregation, and the historical saved-array tolerance. The public synthetic score uses population standard deviation within each cell; root SD and conditional camp-bootstrap intervals are explicitly distinct. Force (`N/kg`) and impulse (`m/s`) are never pooled in raw physical units. Event windows, three-trial assessment construction, and the baseline interval are defined, with native H72/D7 contracts distinguished from synthetic horizons.

The machine-readable bibliography contains 13 verified references. All in-text citation keys match the bibliography; authors, years, titles, publication venues, and DOI/URL status were cross-checked against stored authoritative bibliographic metadata. No new citation was added to pad the reference list. The 13-row result is in [`bibliography_verification.csv`](bibliography_verification.csv).

## Typesetting, rendered inspection, and reproducibility

All 47 final PDF pages were individually rendered and inspected at 144 dpi and A4 reading size (1191 × 1684 pixels): 23 review pages, 20 reading pages, and 4 supplement pages. There are no text blocks outside page bounds, unresolved cross-references, clipped elements, or missing bibliography entries. Figures remain legible at page size; the formerly detached visuals are now substantive evidence graphics placed with their discussions. The full inspection record is [`rendered_page_inspection.md`](rendered_page_inspection.md) and its page-level JSON.

The reproducibility package records CPython 3.12.13, pinned Python package versions, Tectonic 0.17.0 and its archive/binary hashes, the TeX bundle identity, `SOURCE_DATE_EPOCH`, source manifests, build script, figure/table generators, and exact commands. The build ran in a fresh `/tmp` virtual environment after synchronizing `requirements.lock`. A second complete build produced byte-for-byte identical SHA-256 entries for all 199 deliverable files present at that time. The build validates all PDF outputs, figure exports, rendered page sets, evidence arithmetic, bibliography, privacy boundary, and V2 preservation.

Remaining TeX notices are nonvisual: one invalid-UTF-8 warning originates in bundled `lineno.sty`, which substitutes U+FFFD while line numbers render correctly, and a few underfull-box spacing warnings. No overfull boxes remain. These are recorded in the rendered-page report.

## Unresolved items before any submission

- Owner/authors must complete names, affiliations, corresponding-author contact, ORCID, CRediT roles, funding, competing-interest, and final ethics/data-availability statements. The current text deliberately marks these items for confirmation.
- PLOS requires the official template for an actual submission, and the final submission-system fields must be completed. The truthful restriction on private checkpoints and records is not a guarantee that a journal will accept the data-availability statement.
- No athlete predictive validity, clinical utility, out-of-distribution transportability, causal feature attribution, or production readiness is established.
- Saved historical CUDA comparisons still fail for M4–M8; their cause is unresolved. Rich-history row-count differences remain unexplained. No new model replay, training, resampling, or empirical scoring was authorized or performed.

## Repository and owner-review boundary

The public repository's local HEAD remains `dac56cec866883ac64575e5b264eca86662b97ca` on `codex/res-584-research-atlas`; its worktree is clean. The immutable `v1.1.0` tag still resolves to `401f87aad1e4ef4108011fa0c1d769a24f1ad329`. PR #37 remains the merged public manuscript; this V3 package does not modify or replace it. Linear `RES-585` remains In Progress; no issue update was made. The V3 package is private under `/home/litju/cmj-open-source-recovery/RES-546-private-verification/M10_SCIENTIFIC_MANUSCRIPT_V3_20261105/`. No new Git branch, pull request, software release, submission, preprint, or DOI record was created before owner review.

