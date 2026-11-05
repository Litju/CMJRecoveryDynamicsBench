# Final rendered-page inspection

Inspection date: 5 November 2026. All PDFs were regenerated from `manuscript.tex` or the technical supplement source after the last editorial change, rendered page by page at 144 dpi, and visually inspected at full page size.

## Coverage

| PDF | Pages inspected | Page image size | Text outside page | Lowest page text count |
|---|---:|---:|---:|---:|
| Academic review manuscript | 23/23 | 1191 × 1684 px | 0 blocks | 1,045 characters |
| Integrated reading edition | 20/20 | 1191 × 1684 px | 0 blocks | 1,068 characters |
| Technical supplement | 4/4 | 1191 × 1684 px | 0 blocks | 3,295 characters |

Machine-readable page measurements and image paths are in [`rendered_page_inspection.json`](rendered_page_inspection.json). Every page has a corresponding PNG in `renders/`; contact sheets are additional navigation aids and were not used in place of full-size inspection.

## Findings

- The academic review copy is single column, double spaced, continuously line numbered, and paginated. Its equations, headings, table captions, figure captions, declarations, and Vancouver bibliography remain legible at the rendered size.
- The reading edition places figures beside their first substantive discussion. The formulation genealogy and verification workflow occupy figure pages with captions; the architecture, route matrix, chronology, force-time illustration, performance panels, uncertainty intervals, ablation chart, and evidence-scope diagram are readable without clipped labels or legends.
- The route matrix distinguishes all 18 saved-CUDA comparisons and the separate exact-CPU record. The six-cell performance plot labels its dimensionless NRMSE axis and separates force and impulse targets. The mechanics plot labels force, time, body-weight baseline, event boundaries, and the analytical-only status.
- The technical supplement tables fit within the page. Long tables repeat headers across pages. The full cellwise table and nested-camp table continue cleanly; the protocol and native measurement contracts remain readable.
- Float-only pages start at the top margin in the reading edition. Its orphan supporting-information caption page was removed; the PLOS-style review copy retains the supporting-information caption section after references.
- No text, equation, table, figure, caption, reference, or page number was visibly clipped. There are no missing glyphs or unresolved cross-reference markers in the rendered outputs.

## Build notices

Tectonic reports an invalid-UTF-8 byte in its bundled `lineno.sty`; it substitutes U+FFFD while processing that dependency. The line-numbered output was visually checked and is intact. The remaining `Underfull \hbox` notices occur in a table row and bibliography spacing; no corresponding visible defect was found. No overfull boxes, undefined references, or missing citations remain in the final build logs.

