# Final rendered-page and figure inspection

Inspection date: 6 November 2026. Both article editions and the technical supplement were built from the V3 source, rendered at 144 dpi, and inspected after the final pagination and caption changes.

## PDF coverage

| PDF | Pages | Page image size | Text blocks outside page | Lowest extracted text count |
|---|---:|---:|---:|---:|
| Academic review manuscript | 24 | 1191 × 1684 px | 0 | 1,669 characters |
| Integrated scientific reading edition | 21 | 1191 × 1684 px | 0 | 1,210 characters |
| Technical supplement | 4 | 1191 × 1684 px | 0 | 3,330 characters |

Every page has an individual PNG in `renders/`; the final contact sheets cover all 49 pages. Figure-bearing pages were also inspected at full page size, and all four supplement pages were checked individually. The academic review copy is single-column, double-spaced, continuously line-numbered, and paginated. It carries captions in first-citation order and supplies figure files separately. The integrated edition uses the same manuscript text with vector figures placed in the argument; the short supplementary-information caption remains with the review copy without creating an additional page.

## Figure and table inspection

- Fig. 1 genealogy shows only recorded links and marks unresolved ancestry. Fig. 2 separates computational checks from scientific validity. Both are legible in the reading edition.
- Fig. 3 architecture atlas labels the input branches and parameter counts. Fig. 4 preserves all 18 CPU/CUDA route records, with status words, marks, discrepancy units, and failure counts readable.
- Fig. 5 keeps the native H72/D7 windows separate from synthetic H24/H48/H72 queries. Fig. 6 labels force, time, body-weight baseline, boundaries, and the analytical-only status.
- Fig. 7 reports the six synthetic cells with three roots, model labels, units, and dimensionless NRMSE. Fig. 8 describes conditional whole-camp bootstrap intervals. Fig. 9 separates feature ablations from nested-camp diagnostics. Fig. 10 is categorical and does not display a quantitative readiness score.
- A grayscale preview of all figure-bearing reading pages preserved distinctions through text labels, marker shapes, line styles, and hatching; color alone does not carry status or model identity.
- Tables remain within page bounds. The supplement's long tables repeat headers, and the full route, cell, bootstrap, ablation, protocol, and native-contract values remain legible at page size.

## Figure-file checks

The ten TIFF exports are flattened 8-bit RGB with no alpha channel, LZW compressed, and tagged at 600 dpi. Their physical widths/heights satisfy the current PLOS ONE figure dimensions, and every file is below 10 MB. PDF and SVG exports remain vector. The build validator checks TIFF mode, dimensions, compression, resolution, and file size for every figure.

## Rendering checks and notices

The page-level measurements and image paths are in [`rendered_page_inspection.json`](rendered_page_inspection.json). The validator found no text blocks outside page bounds, missing pages, or unresolved cross-reference markers. The final build log reports an invalid UTF-8 byte in the bundled `lineno.sty`; Tectonic replaces it while compiling. The line-numbered review copy shows no visible substitution or clipping. Remaining font-resolution and underfull-box notices did not produce a visible defect. No overfull boxes or missing citations remain.
