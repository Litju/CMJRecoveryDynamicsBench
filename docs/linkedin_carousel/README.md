# Scientific LinkedIn carousel: From Force Plate to Forecast (RES-783)

An 8-page, 4:5 portrait (1080 × 1350 px) carousel that narrates the controlled synthetic CMJ
study behind the M12 flagship manuscript ([`docs/manuscript/v4`](../manuscript/v4/README.md)).
Status: **owner-review draft. Not posted to LinkedIn, not deployed.**

No athlete was measured. Every displayed value is derived at build time from a pinned public
receipt or from the synthetic generator's own routines and is listed in the
[figure-to-source ledger](ledger/figure_source_ledger.csv).

## Deliverables

| File | What it is |
|---|---|
| [`output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf`](output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf) | LinkedIn-ready flattened vector PDF, 8 pages, document title set, three clickable links |
| [`output/pages/page-01.png`](output/pages/) … `page-08.png` | Individual pages, exactly 1080 × 1350 px |
| [`output/previews/contact_sheet.png`](output/previews/contact_sheet.png) | All eight pages on one sheet |
| [`output/previews/phone/`](output/previews/phone/) | Each page at phone width (390 CSS px, 3× density) |
| [`output/carousel.html`](output/carousel.html) | Rendered, diffable HTML of all pages (open after `npm ci`) |
| [`ledger/figure_source_ledger.csv`](ledger/figure_source_ledger.csv) | Every displayed value: page, token, unit, evidence class, claim id, source file, key, source SHA-256 |
| [`post/LINKEDIN_POST.md`](post/LINKEDIN_POST.md) | Draft post text with verified URLs |
| [`qa/QA_RES-783.md`](qa/QA_RES-783.md) | Content, numeric and visual QA record |
| [`ARTIFACT_SHA256SUMS`](ARTIFACT_SHA256SUMS) | Integrity manifest of every tracked file in this package |

## Narrative

| Page | Chapter | Dominant figure | Evidence |
|---|---|---|---|
| 1 | Cover: From Force Plate to Forecast | Measure → model → forecast strip | descriptor, nonclaim |
| 2 | Biomechanics | Generator force–time trace; mean force vs peak force vs net impulse; three-trial baseline → criterion | M-01–M-06, manuscript Fig 2–3 |
| 3 | Mathematical model | r(τ) with fixed 24 h / 84 h modes, amplitude envelope, H24/H48/H72 | A-01–A-04, Fig 4 |
| 4 | Nine original families M0–M8 | Component matrix with exact parameter counts; "not scored" boundary | N-01–N-04, Fig 5 |
| 5 | The experiment | Camp waffle (96 / 16 / 3 × 16), four reference models × six cells | E-01–E-04, Fig 6 |
| 6 | Results | Six-cell mean NRMSE with per-root values; per-cell table | R-01–R-04, Fig 7–8 |
| 7 | Interpretation | Recorded intervals, ablations, nested training camps; what is not shown | R-05–R-19, Fig 9–10 |
| 8 | Explore and verify | Observatory, manuscript and repository links; supports / does not support | V-02, nonclaims |

The nine original families and the four evaluated reference models stay separate: no NRMSE
appears on page 4 or next to any M0–M8 label (checked by `tests/test_linkedin_carousel.py`).

## Edit and rebuild

Words live in [`source/carousel.template.html`](source/carousel.template.html); styles in
[`source/carousel.css`](source/carousel.css) (Recovery Observatory tokens: warm paper, ink,
cobalt, vermilion). Numbers are `{{token}}` placeholders and figures are `{{fig:name}}` slots
drawn by [`tools/build_carousel.py`](tools/build_carousel.py); never type a result by hand.

```sh
# once: Python 3.12 venv with the repository installed (numpy), Node 22
python -m venv .venv && .venv/bin/pip install -e .          # from the repository root
cd docs/linkedin_carousel && npm ci
npx playwright-core install chromium-headless-shell          # Chromium build pinned by playwright-core 1.64.1

bash tools/build.sh      # receipts -> HTML + ledger -> PDF, PNGs, previews -> fixed dates + manifest
```

`tools/export.mjs` fails the build if any block runs into the footer, leaves the side gutter,
is clipped, or if any figure label falls outside its figure. The build reads only the pinned
receipts and the generator's trial and response routines; it performs no training, fitting,
inference or scoring. Two consecutive builds produce identical bytes (PDF creation dates are
fixed by `tools/finalize.py`). After editing only Markdown files here, refresh the manifest
with `python tools/finalize.py --manifest-only`.

## Sources

- `docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json` (SHA-256 `cd991366…`, scientific SHA-256
  `25032133…`): all results, study design and feature counts.
- `docs/manuscript/supplement/architecture_qualification.csv` (SHA-256 `ff1ae117…`): M0–M8
  structure and parameter counts.
- `src/cmj_recovery_dynamics/…/phase_consistent_force_impulse.py`, `episode_summary.py`,
  `fixed_mode_discrepancy_response.py`: the illustrative trace, trials and response curves,
  identical to manuscript Fig 2–4 (input 20 N/kg, 2.7 m/s; a_f 0.04, a_s 0.03).
- `docs/science/claims_evidence_register.csv`: claim ids and permitted wording.

## Licences

Text and source: Apache-2.0 (repository licence). Fonts: Geist and Geist Mono (Vercel) and
Source Serif 4 (Adobe), SIL Open Font License 1.1; licence texts in `source/fonts/`.
