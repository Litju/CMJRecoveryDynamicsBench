# RES-783 QA record: scientific LinkedIn carousel

Scope: `docs/linkedin_carousel/` after the remediation of the independent review of
`f329148` (PR #46). Base: `main` at `de9bc47` (M12 flagship manuscript, `docs/manuscript/v4`).
No scientific record, receipt, manuscript, release tag, website route or production deployment
was changed. Nothing was posted.

Reviews so far: an independent **agent** review of `f329148` (PR #46) and this author QA
(Claude Code, on behalf of the owner). No independent human or domain-peer review has been
done; owner review is still required before posting.

## 1. Review findings and remediation

| Finding | Remediation | Guard |
|---|---|---|
| P1 M0–M8 claim too broad (p. 4, now p. 5) | "Two recorded repeats per family: 18 recorded inference routes." "Not evaluated here. M0–M8 were not part of the public four-reference-model experiment that follows, so no comparative NRMSE is reported for them." Parameter counts, components and the basis-constant distinction unchanged. | `test_original_architectures_never_carry_a_score` requires the bounded wording and rejects "no NRMSE exists", "networks in total", "not scored" |
| P1 phone readability | Type minimum 21 px → 26 px (footers only); figure labels ≥ 28 px; statements 31–32 px. Dense slides split: 8 → 10 pages (forecast target, uncertainty and diagnostics now stand alone). Per-root values moved from the results bar chart to the uncertainty page; axis ticks reduced. | Export gate fails on any text < 26 px (script-size equation parts and subscripts ≥ 20 px) and on overlapping figure labels; `test_type_scale_keeps_phone_readable_minimums` |
| P2 rounding on p. 2 (now p. 3) | Source values: baseline mean 20.053821, criterion mean 19.217941, change −0.835880 N/kg (generator stream `manuscript-illustration`, unchanged). Shown at three decimals: 20.054, 19.218, −0.836 (19.218 − 20.054 = −0.836). Page states the change is computed from unrounded means. | Build fails if the displayed means stop subtracting to the displayed change; `test_displayed_change_equals_the_displayed_means` |
| P2 interval interpretation (p. 7, now p. 8) | A note attached directly beneath the bootstrap figure: "Per-model uncertainty within each evaluation root. These intervals are not a paired ridge-versus-structured comparison: no direct ridge-versus-structured interval or significance result was recorded." Statement: "a descriptive pattern, not a tested difference." Intervals unchanged (4 decimals). | `test_interval_limitation_sits_directly_under_the_bootstrap_figure` |
| P2 post repeats the slides | Rewritten as a ~150-word introduction: biomechanics → response modes → nine architectures (18 inference routes) → four-model synthetic benchmark → ridge (0.736270) below the structured model on the simulator's own modes (0.773316), no paired test, no athlete. | `test_post_draft_uses_only_sourced_numbers_and_verified_links` (120–180 words, distinctions, no emoji or hashtags) |
| Scope note: PDF not rendered independently | `tools/check_pdf_render.py` rasterizes the final PDF with MuPDF 1.24.10 (independent of the Chromium export) and compares every page with its PNG. | see §6 |

## 2. Numbers and sources

| Check | Result |
|---|---|
| Receipt identity: results `cd991366…` (scientific `25032133…`), architecture table `ff1ae117…`; the build refuses any other digest | pass |
| Headline six-cell mean NRMSE: zero 2.430659, training mean 1.036038, ridge 0.736270, structured 0.773316 (`across_root_variability.*.root_mean_nrmse`) | pass |
| Every displayed value with ≥ 3 decimals or a thousands separator is a ledger row (113 uses on pages 2–10); ledger digests recomputed | pass |
| HTML and ledger re-derived from receipts byte for byte | pass |
| Descriptive guards: ridge < structured in every root; paired differences from zero entirely < 0; no ridge-versus-structured interval exists; all alphas 0.01 | pass |
| Illustrations call `realize_concentric_trial`, `assessment_trials`, `fixed_mode_response` with the manuscript's Fig 2–4 inputs (peak 25.82 N/kg, T 0.265 s) | pass |

## 3. Equations and units

Unchanged and re-checked against `docs/science/CONTRACT_AND_TERMINOLOGY.md`: gross mean concentric
force F̄ = (1/(mT))∫F_z dt [N/kg]; net impulse J = (1/m)∫(F_z − mg)dt [m/s], g = 9.80665;
peak force shown for contrast only; ΔF and ΔJ are additive criterion − baseline changes of
three-trial means [N/kg, m/s]; r(τ) = −a_f e^(−τ/24 h) − a_s e^(−τ/84 h) labelled as generator
assumptions; architecture basis constants (36 h / 120 h) named separately; NRMSE = RMSE ÷ SD
of the true change. KaTeX renders all equations; MuPDF renders them identically (§6).

## 4. Wording and naming

Terminology contract and scientific-label tests pass on all ten pages: no claim ids, file names,
code keys, digests or internal terms; "accuracy" only as "not athlete accuracy"; "Synthetic
data" on every page. Footers cite manuscript figures only.

## 5. Readability and layout

- Pages 1080 × 1350 px (4:5); PDF MediaBox 810 × 1013 pt.
- Measured sizes: headline 64 px (cover 104), statements 31–32 px, figure labels 28–33 px,
  footers 26 px. At 390 px width these are 23, 11–11.6, 10.1–11.9 and 9.4 px on screen.
- Export gate (final build): no block in the footer zone or outside the gutters, no clipping,
  no figure label outside its figure, no overlapping labels, nothing below 26 px.

## 6. Visual inspection

All ten pages were inspected at full resolution (PNG and MuPDF PDF render) and at natural phone
size (390 × 488 px, 1×), and the deck was read in order as one narrative.

| Page | Notes from inspection |
|---|---|
| 1 Cover | Footer wrapped "→" onto its own line in the PDF render; fixed with a shorter footer and a non-breaking space |
| 2 Biomechanics | Labels sit inside their regions; mean-force label split over two lines to clear the trace |
| 3 Forecast target | Means and change legible at phone size; arithmetic consistent at 3 decimals |
| 4 Response model | Legend moved below the amplitude envelope; subscripts render in both engines |
| 5 Architectures | Matrix readable at 1×; caption no longer collides with the M8 row |
| 6 Experiment | 16 squares per evaluation root; headers fit their columns |
| 7 Results | Axis title collided with a tick (gate finding), fixed |
| 8 Uncertainty | Interval labels above their bars; limitation note attached to the figure |
| 9 Diagnostics | Ablation values and nested-camp table readable at 1× |
| 10 Links | Three link cards; supports / does not support lists |

PDF render (MuPDF 1.24.10, `tools/check_pdf_render.py`): 10 pages; mean absolute difference from
the PNG exports 1.4–2.1 / 255 per page (anti-aliasing differences between engines); text
extractable on every page (97–207 words); page 10 carries exactly the three link annotations.

## 7. Output integrity and verification runs

- Two consecutive `tools/build.sh` runs produced identical `ARTIFACT_SHA256SUMS`, and the
  committed outputs reproduce byte for byte.
- PDF: 10 pages, title "From Force Plate to Forecast: Modeling CMJ Performance Changes Following
  Training", links to exactly the three URLs below, no forms or scripts, fixed dates.
- Links returned HTTP 200 on 2026-11-24: https://recovery-observatory.vercel.app/ ,
  https://github.com/Litju/CMJRecoveryDynamicsBench ,
  https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf
- Local: `ruff check`, `ruff format --check`, `pyright` on the carousel tests, full `pytest`
  (613 passed, 9 skipped); website `npm ci`, `npm run typecheck`, `npm test` (36 pass).
  Repository-wide `pyright` reports only pre-existing errors in torch-dependent modules (torch
  is not installed locally; CI installs it).
- Exact-head GitHub CI: recorded on PR #46.

## 8. Remaining limitations

- Browsers: pages were rendered with Chromium (playwright-core 1.64.1) and MuPDF only;
  LinkedIn's own document viewer was not tested and may resample pages.
- Accessibility: the PDF is tagged and text is extractable, but SVG figures are exposed as
  images with one-line descriptions; no screen-reader pass was done. Colour pairs follow the
  Observatory palette; no formal contrast audit of every label beyond visual inspection.
- Readability: figure labels reach about 10 px on a 390 px phone; readers with low vision may
  still need to zoom.
- Review: agent and author review only; independent human (domain) review and owner approval
  are outstanding. Posting and the optional MP4 remain owner decisions.
- Environment: on hosts without `libnss3`, `libnspr4` and `libasound2`, install them
  (`npx playwright-core install-deps`) before exporting.
