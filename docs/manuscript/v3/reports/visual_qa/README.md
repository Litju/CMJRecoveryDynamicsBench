# Visual qualification record (RES-585)

Agent-side review of the redesigned manuscript. It is **not** human peer review and **not** owner acceptance; the owner's visual review is the next gate and PR #38 stays Draft.

## Before and after

| | Before (`9b674ba`) | After (this package) |
|---|---|---|
| Layout | Single column, 11 pt, 20 mm margins, generic technical-report look | Two-column A4, 9 pt Palatino-style body, sans headings, 87 mm columns / 180 mm figures, running heads and folios |
| Primary PDF length | 19 pages | 12 pages |
| Figures | 10, mostly 6.3 in wide with large blank margins; Fig. 2 was a three-row text table; Figs. 5 and 6 were separate small plots | 10 multi-panel figures at 180 mm, scale 1.0; Fig. 2 is a camp-level study design, Figs. 5a–c merge the force-time curve, three-quantity ledger and scaled chronology; new Fig. 7 heatmap |
| Tables | Left-aligned text values | siunitx decimal-aligned columns, `table*` at full width |
| Equations | Two-column `align` blocks inside a single column | Stacked, numbered, cross-referenced equations |
| Figure type | STIX serif at ~6–7 pt after scaling | DejaVu Sans, ≥ 5.4 pt printed (smallest math subscript 4.6 pt) |

Contact sheets: [`before_9b674ba_contact_sheet.png`](before_9b674ba_contact_sheet.png) and [`after_contact_sheet.png`](after_contact_sheet.png). Grayscale rendering of all figures: [`figures_grayscale_check.png`](figures_grayscale_check.png).

## Visual problems and where they were corrected

Page numbers refer to `full_illustrated_research_manuscript.pdf` (after) and the pre-RES-585 PDF (before).

| Problem found | Before | After |
|---|---|---|
| Figures small, surrounded by blank margins, one per ~½ page (e.g. Fig. 1 p. 4, Fig. 2 p. 5, Fig. 10 p. 16) | Pages 4–16 | Figs. 1–2 share p. 3; Fig. 3 and Table 1 p. 5; Fig. 4 p. 6; Fig. 5 p. 7; Fig. 6 p. 8; Fig. 7 and Table 2 p. 9; Figs. 8–9 p. 10; Fig. 10 top of p. 11 |
| Fig. 2 was only a three-row text table; Fig. 3 panels A–C were text lists | Pp. 5–6 | Fig. 2 waffle of 160 camps with row counts and leakage rules (p. 3); Fig. 3 computational graph, component matrix and parameter bars (p. 5) |
| Force-time figure and chronology split into two small plots; no peak-force or mean-force contrast | Pp. 8–9 | Fig. 5 (p. 7) separates gross mean force 14.79 N/kg, peak 24.09 N/kg and net impulse 2.74 m/s |
| Heavy numbers hidden in Table 2/3 only; no model-by-cell view | p. 13 | Fig. 7 heatmap and per-root structured-minus-ridge panel (p. 9) |
| Tables with left-aligned values | p. 5, 13 | Decimal-aligned (Table 1 p. 5, Tables 2–3 p. 9) |

Defects found *during* this redesign and fixed before the final build (each re-checked on the rendered page or figure PNG):

- Table 2 printed decimals with thousands separators ("3.033,5"): siunitx grouped fractional digits. Fixed with `group-digits=integer`; verified on p. 9.
- Fig. 5 x-axis label collided with the panel-c heading; panel a was shortened and re-spaced; verified p. 7.
- Fig. 2 panel text overlapped the waffle note and was clipped at the right edge; Fig. 3 matrix markers were distorted ellipses; Fig. 4 footnotes overprinted the axis labels; Fig. 7 six-cell means were oriented as a column although rows are cells (now a bottom "Mean" row); Fig. 8 header and axis label were truncated; Fig. 10 labels overlapped data. All corrected in the generator and re-rendered.
- Fig. 10 originally sat alone on a mostly empty float page (FloatBarrier before the Discussion); the barrier was removed and floats now top-align (p. 11).
- Run-in headings lacked a space ("Aims.The"); the "at a glance" panel wrapped mid-word; review edition had nine overfull lines. All fixed; the final build has zero overfull boxes in all three PDFs.

## What was inspected, and how

- All 12 pages of the primary PDF were rendered and viewed as page pairs (75 dpi) after the final layout change, with pages 1, 3, 7, 8, 9, 11 and the figure pages re-viewed at larger size; each of the ten figures was also opened individually at 300 dpi. The review edition's first page was opened; the supplement was only machine-checked (zero overfull boxes, tables compile).
- Automated checks (`reproducibility/qa_visual_report.py`, outputs `figure_legibility.csv` and `page_layout_checks.csv`): all figures print at 180 mm wide, minimum plain text 5.4 pt, no text outside the page margins, every page's columns filled to the bottom margin.
- Grayscale: models are separated by position and printed labels as well as colour; roots by marker shape; the heatmap prints every value. Cobalt/vermilion and slate/ochre are close in gray, so no figure relies on colour alone.
- Not done: no human reviewer, no screen-reader (NVDA) pass, no print proof.

## Remaining visual judgement calls for the owner

- Whether the 150 mm-tall six-cell small-multiple figure (Fig. 6) should be compressed to share a page with more text.
- Whether the title-page "recorded results at a glance" panel is welcome or should be reduced to the abstract alone.
- Sans (DejaVu) figure type versus a serif to match the body.
