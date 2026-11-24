# RES-783 QA record: scientific LinkedIn carousel

Scope: `docs/linkedin_carousel/` at the commit that adds this file. Base: `main` at
`de9bc47` (M12 flagship manuscript, `docs/manuscript/v4`). No scientific record, receipt,
release tag, website route or production deployment was changed. Nothing was posted.

This record is the author's own QA (Claude Code, on behalf of the owner). An independent
human or agent review of content and visuals is still to be done on the pull request.

## 1. Numbers and sources

| Check | Method | Result |
|---|---|---|
| Receipt identity | `build_carousel.py` refuses to build unless the results file SHA-256 is `cd991366…`, its scientific SHA-256 is `25032133…`, and the architecture table is `ff1ae117…` | pass |
| Headline values | zero 2.430659, training mean 1.036038, ridge 0.736270, structured 0.773316 re-read from `across_root_variability.*.root_mean_nrmse`; equal to claims R-01–R-04 and `tables/overall.tex` | pass |
| Every displayed number is sourced | `test_every_displayed_result_number_is_in_the_ledger`: each value with ≥ 3 decimals or a thousands separator on any page is a ledger row (120 uses across pages 2–8) | pass |
| Ledger digests | `test_ledger_values_and_digests_match_their_sources` recomputes each source SHA-256 | pass |
| Re-derivation | `test_build_reproduces_the_committed_html_and_ledger` rebuilds the HTML and ledger from the receipts and compares byte for byte | pass |
| Descriptive statements guarded | Build fails if ridge stops being lower than structured in any root, if a paired difference from zero is no longer entirely below 0, if a ridge-versus-structured interval appears, or if any selected alpha differs from 0.01 | pass |
| Illustrations | Trace, trials and response curves call the generator's `realize_concentric_trial`, `assessment_trials` (stream `manuscript-illustration`) and `fixed_mode_response` with the manuscript's Fig 2–4 inputs; values match the manuscript figures (25.82 N/kg peak, 0.265 s, 20.05 → 19.22 N/kg, −0.84 N/kg) | pass |

## 2. Equations and units (checked against `docs/science/CONTRACT_AND_TERMINOLOGY.md`)

- Gross mean concentric force F̄ = (1/(mT)) ∫ F_z dt, N/kg; gravity not subtracted.
- Net concentric impulse J = (1/m) ∫ (F_z − mg) dt = (F̄ − g)T, m/s; g = 9.80665 m/s².
- Peak force max F_z/m is shown as a different quantity, "not a modeled target".
- Assessment = mean of three trials; target = additive criterion − baseline change (ΔF in
  N/kg, ΔJ in m/s), never a percentage, never pooled.
- r(τ) = −a_f e^(−τ/24 h) − a_s e^(−τ/84 h); A_criterion = A_baseline (1 + r(τ) + e);
  a_f 0.01–0.08, a_s 0–0.08. The 24 h / 84 h modes are labelled generator assumptions; the
  architecture basis constants (36 h / 120 h) are named separately on page 4.
- NRMSE = RMSE ÷ population SD of the truth per cell; score = equal-weight mean of 6 cells.

## 3. Two bodies of work kept apart

`test_original_architectures_never_carry_a_score`: page 4 carries no decimal result and no
NRMSE ledger row; no text element anywhere pairs an M0–M8 label with a 4-decimal value.
Page 4 states "Not scored … No NRMSE exists for them, and they are not ranked"; page 5
states that none of the four reference models is one of the nine networks.

## 4. Wording and naming

- Terminology contract: no "peak mean force", "leaderboard", "significant", "p-value",
  "time constant", "timescale", "independent datasets" or promotional superlatives;
  "accuracy" appears only as "not athlete accuracy" (`test_wording_respects_…`).
- Scientific labels only on the pages (`test_pages_use_scientific_labels_not_internal_identifiers`):
  no claim-register ids, issue ids, file names, code keys, digests, "Gate7", "receipt",
  "ledger" or "token". Footers cite manuscript figure numbers; the technical identifiers
  live in the ledger and this record.
- Every page carries the "Synthetic data" label.

## 5. Layout and readability

- Format: 1080 × 1350 px pages (4:5), 64 px side gutters, PDF MediaBox 810 × 1013 pt.
- Type sizes: headline 62 px (cover 104 px), statements 27–30 px, figure labels 22–27 px,
  smallest text 21 px (footers, axis captions) ≈ 7.6 CSS px on a 390 px-wide phone.
- `tools/export.mjs` fails the build if any block reaches within 12 px of the footer,
  breaks the side gutter, is clipped, if any SVG label leaves its figure, or if a font
  fails to load. Final build: no findings.
- Units never break from their values in footers (non-breaking spaces).

## 6. Visual inspection (every page, full size and phone preview)

| Page | Inspected | Issues found and fixed during review |
|---|---|---|
| 1 Cover | yes | panel label overflowed into the next panel; redundant baseline label removed |
| 2 Biomechanics | yes | labels collided with the trace; trials strip clipped the innovation value; footer split "2.7 / m/s" |
| 3 Model | yes | legend crossed the H72 line; envelope label moved into the legend; subscripts set properly |
| 4 Architectures | yes | caption overlapped the M8 row; column headers crowded; footer overflow |
| 5 Experiment | yes | evaluation roots drew 14 squares instead of 16 camps; right column overflowed |
| 6 Results | yes | root markers overlapped at bar ends (replaced by per-root values); axis caption collided with ticks; statements reached the footer |
| 7 Interpretation | yes | ablation rows overlapped panel c |
| 8 Links | yes | nested sections truncated the page in the parser (now divs; build guard added) |

A styling defect was also fixed globally: CSS class fills overrode SVG `fill` attributes, so
coloured labels rendered in ink; labels now use inline styles and a paper-coloured halo.

## 7. Output integrity

- PDF: 8 pages, title "From Force Plate to Forecast: Modeling CMJ Performance Changes
  Following Training", link annotations to exactly the three URLs below, no forms or
  scripts, fixed creation/modification dates.
- Two consecutive `tools/build.sh` runs produced identical `ARTIFACT_SHA256SUMS`.
- URLs returned HTTP 200 on 2026-11-24: https://recovery-observatory.vercel.app/ ,
  https://github.com/Litju/CMJRecoveryDynamicsBench ,
  https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf

## 8. Environment notes and open items

- Chromium: playwright-core 1.64.1 headless shell (build 1248). On a host without
  `libnss3`, `libnspr4` and `libasound2`, install them (`npx playwright-core install-deps`)
  before exporting.
- Not done here, by design: exact-head CI (runs on the pull request), independent review,
  owner approval, LinkedIn posting, optional MP4 (only after carousel acceptance).
