> **Superseded for the illustrated edition by RES-585.** The page-level record for the redesigned two-column article is `visual_qa/README.md`. The text below is the earlier V3 record and is kept for provenance.

# Final page-by-page visual review

**Final nomenclature pass: 7 November 2026.** Reader-facing manuscript and figure labels were checked against the pinned model inventory, public synthetic-study protocol, route qualification summary, and measurement definitions. No new labels, observations, metrics, uncertainty estimates, or model results were introduced.

| Reader-facing text found | Final scientific wording | Traceability retained |
|---|---|---|
| Project codename in model descriptions | Historical neural model families | Original family IDs M0–M8 remain in architecture and route contexts. |
| Source inventory codes and local file/key names in captions | Descriptive lineage, protocol, qualification, and results records | Exact source IDs, paths, and hashes remain in machine-readable evidence and figure receipts. |
| “Zero”, “Train mean”, “Ridge”, and “Structured” plot shorthand | Zero-innovation baseline, training-mean baseline, ridge regression, and structured comparator | Original model configuration IDs remain only in reproducibility records. |
| Internal tolerance abbreviations and CUDA-array wording | Absolute tolerance, relative tolerance, reference CPU output, and archived GPU output | Numerical values, M0–M8/r0–r1 route IDs, and the unchanged tolerance are preserved. |
| “Clean-room” and “caller-supplied” labels | Public reconstruction and fixed evaluation roots | Evaluation-root IDs A–C remain where they identify the three recorded roots. |
| Bootstrap table labels `ridge_full` and `structured_full` | Ridge regression and structured comparator | Original keys remain in the figure receipt. |

An initial post-edit visual pass found two further defects: the revised bootstrap-panel x-axis label wrapped into the legend, and the expanded route-table headings left the table 1.2 pt overfull. The x-axis label was shortened to “Δ NRMSE (model − zero innovation)” and rechecked on page 14. The route-ID column was narrowed by 0.04 in; the final supplement table now fits, remains readable, and the final build has no overfull boxes. The final render was then inspected at 144 dpi page size, one image per page.

**Visual disposition: `M10_VISUAL_REVIEW_READY`.** This is an internal visual-review disposition; owner acceptance remains pending.

## Pages reviewed

All three final PDFs were rendered to one 1191 × 1684 px PNG per page at 144 dpi. Every page image was opened and inspected individually at its full rendered size; contact sheets were used only to navigate.

| PDF | Pages | Individually inspected |
|---|---:|---|
| `full_illustrated_research_manuscript.pdf` — primary | 19 | 19 |
| `academic_review_manuscript.pdf` — secondary, separate figures | 24 | 24 |
| `technical_supplement.pdf` | 4 | 4 |
| **Total** | **47** | **47** |

The primary manuscript has no figure-only pages. Figures 1–6 appear in Methods on pages 4–9; the six-cell performance plot is on page 12, bootstrap intervals on page 14, ablations and nested-camp results on page 15, and the rich-history row-count comparison on page 16. The full page-by-page figure-to-claim mapping is in [`full_illustrated_page_figure_inventory.md`](full_illustrated_page_figure_inventory.md).

## Defects found and corrections made

- **Architecture figure:** the M0–M2 node labels overlapped their boxes, and the feature panels were crowded. Replaced the box atlas with aligned architecture summaries and a parameter-count plot. The final panel fits on page 6 with readable row labels and counts.
- **Evidence workflow graphic:** the former workflow cards contained no observations or sample counts. Replaced them with the recorded training, development, and evaluation-root counts, including the three grouped horizon queries per episode (Fig. 2, page 5).
- **Evidence-scope graphic:** the former four-card summary repeated conclusions from the Discussion and displayed no measurement. Replaced it with the signed rich-history training and validation row-count differences from the preserved split records (Fig. 10, page 16).
- **Route matrix:** the first regenerated draft had overlapping summary and column headings. Separated the summary line from the headers and increased route/status text. The final 18-route matrix is legible on page 7; its mixed-unit maximum differences remain explicitly identified as non-comparable.
- **Timeline and mechanics:** the timeline annotations and force-plot legend were too small at manuscript scale, while formula callouts covered the force curve. Increased annotation type and removed the redundant in-plot formula boxes and banner; the equations and analytical-only limitation remain in the Methods text and caption (pages 8–9).
- **Six-cell comparison:** diagonal model labels and close root symbols impeded comparison. Used horizontal model labels and small horizontal root offsets, with the caption stating that offsets only separate symbols and do not change group membership (page 12).
- **Six-cell table:** six-decimal mean/SD pairs crowded the four result columns. Displayed four decimals with the rounding stated in the caption; full stored precision remains in the bundled CSV and supplement (page 13).
- **Supplement route table:** its narrow column widths left excessive unused page width and made the route fields harder to scan. Expanded the columns and type size while retaining every route and value (page 2).
- **Separate-figure review copy:** two full-precision M8 discrepancy values forced an overfull line at the RQ2 paragraph. The main text now uses compact scientific notation; the complete values remain in the public route summary, which has a per-figure input digest, and the supplement table retains additional precision. The final build logs contain no overfull boxes.

## Final-page checks

The final visual pass found no clipped figure labels, overlapping captions, figure-only pages, or missing figures in the primary manuscript. The Results subsection prominently states the 18/18 exact CPU-output equality and the 8/18 pass, 10/18 fail comparison with archived GPU outputs. The six-cell means, three-root variation, recorded bootstrap intervals, ablations, and nested-camp results are shown or tabulated in Results. The last reference page has ordinary end-of-document white space; text and references are within page bounds.

The separate-figure edition remains double-spaced and line-numbered, with captions at first citation and the standalone figure files available. The technical supplement retains repeated headers and full-precision numerical tables. Tectonic still reports the known invalid UTF-8 byte in bundled `lineno.sty` and font-resolution/underfull-box notices; the final individually inspected pages showed no corresponding visual defect.

No new model inference, training, bootstrap, empirical scoring, athlete-data collection, GPU replay, or external-data campaign was performed for this repair. The immutable v1.1.0 release was not changed.
