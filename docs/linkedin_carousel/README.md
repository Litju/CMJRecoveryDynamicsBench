# Scientific LinkedIn carousel: From Force Plate to Forecast (RES-783)

A 10-page, 4:5 portrait (1080 × 1350 px) carousel that narrates the controlled synthetic CMJ
study behind the M12 flagship manuscript ([`docs/manuscript/v4`](../manuscript/v4/README.md)).
Status: **owner-review draft. Not posted to LinkedIn, not deployed.**

No athlete was measured. Every displayed value is derived at build time from a pinned public
receipt or from the synthetic generator's own routines and is listed in the
[figure-to-source ledger](ledger/figure_source_ledger.csv).

## Deliverables

| File | What it is |
|---|---|
| [`output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf`](output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf) | LinkedIn-ready flattened vector PDF, 10 pages, document title set, three clickable links |
| [`output/pages/page-01.png`](output/pages/) … `page-10.png` | Individual pages, exactly 1080 × 1350 px |
| [`output/previews/contact_sheet.png`](output/previews/contact_sheet.png) | All ten pages on one sheet |
| [`output/previews/phone/`](output/previews/phone/), [`phone-natural/`](output/previews/phone-natural/) | Each page at phone width: 390 CSS px at 3× density (phone pixels) and at 1× (natural size) |
| [`output/carousel.html`](output/carousel.html) | Rendered, diffable HTML of all pages (open after `npm ci`) |
| [`ledger/figure_source_ledger.csv`](ledger/figure_source_ledger.csv) | Every displayed value: page, token, unit, evidence class, claim id, source file, key, source SHA-256 |
| [`post/LINKEDIN_POST.md`](post/LINKEDIN_POST.md) | Draft post text with verified URLs |
| [`qa/QA_RES-783.md`](qa/QA_RES-783.md) | Content, numeric and visual QA record |
| [`ARTIFACT_SHA256SUMS`](ARTIFACT_SHA256SUMS) | Integrity manifest of every tracked file in this package |

## Narrative

| Page | Chapter | Dominant figure | Evidence |
|---|---|---|---|
| 1 | Cover: From Force Plate to Forecast | Measure → model → forecast strip | descriptor, nonclaim |
| 2 | Biomechanics | Generator force–time trace; mean force vs peak force vs net impulse | M-01–M-04, manuscript Fig 2 |
| 3 | Forecast target | Three-trial baseline → criterion; ΔF and ΔJ | M-05–M-06, Fig 3 |
| 4 | Mathematical model | r(τ) with fixed 24 h / 84 h modes, amplitude envelope, H24/H48/H72 | A-01–A-04, Fig 4 |
| 5 | Nine original architecture families M0–M8 | Component matrix with exact parameter counts; 18 recorded inference routes; not evaluated in the four-model experiment | N-01–N-04, Fig 5 |
| 6 | The experiment | Camp waffle (96 / 16 / 3 × 16), four reference models × six cells | E-01–E-04, Fig 6 |
| 7 | Results | Six-cell mean NRMSE; per-cell table | R-01–R-04, Fig 7–8 |
| 8 | Uncertainty | Recorded per-root 95% intervals with the limitation directly beneath | R-12–R-18, Fig 9 |
| 9 | Diagnostics | Ablations, nested training camps, penalty at grid edge | R-05–R-11, R-19, Fig 10 |
| 10 | Explore and verify | Observatory, manuscript and repository links; supports / does not support | V-02, nonclaims |

The nine original families and the four evaluated reference models stay separate: no NRMSE
appears on page 5 or next to any M0–M8 label (checked by `tests/test_linkedin_carousel.py`).

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
is clipped, if any figure label falls outside its figure or overlaps another label, or if any
text renders below 26 px (9.4 px when a page is shown 390 px wide; figure labels are 28 px or
larger). The build reads only the pinned
receipts and the generator's trial and response routines; it performs no training, fitting,
inference or scoring. Two consecutive builds produce identical bytes (PDF creation dates are
fixed by `tools/finalize.py`). After editing only Markdown files here, refresh the manifest
with `python tools/finalize.py --manifest-only`.

Independent PDF check (QA, not part of the build; needs `pip install pymupdf==1.24.10 pillow`):
`python tools/check_pdf_render.py OUT_DIR` rasterizes the final PDF with MuPDF, writes one PNG
per page plus a contact sheet to OUT_DIR, and fails if a page cannot be read or differs
visibly from its exported PNG.

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
