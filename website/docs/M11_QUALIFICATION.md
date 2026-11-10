# M11 qualification record (RES-629)

Scope: the Recovery Observatory 2.0 renovation (RES-628) and its documentation base (RES-627). This record states what was checked, how, and what was **not** checked. It is not an owner acceptance, a production deployment or a Vercel promotion.

## 1. Scientific values

| Check | Method | Result |
| --- | --- | --- |
| Source identity | `prepare-manuscript.mjs` verifies the pinned `ARTIFACT_SHA256SUMS` digest `a83b7069…` and all 24 input digests on every build | pass |
| Receipt agreement | Public CSV summaries vs S01 receipt, strict equality: 24 cell rows (root A/B/C, mean, sample SD) and 6 bootstrap rows | pass |
| Aggregates unchanged | zero innovation 2.430659, training mean 1.036038, ridge 0.736270, structured 0.773316 (fixture, overview, results page, abstract) | pass |
| Arithmetic | NRMSE = RMSE ÷ population SD per root and cell; root score = equal-weight mean of six cells; across-root mean and ddof = 1 SD recomputed | pass (|Δ| < 1e-12) |
| Units | force cells N/kg, impulse cells m/s, never pooled; legacy key `relative_peak_mean_force_innovation` retained on force cells | pass |
| Grouping | 96/16/3×16 camps; 24,000/4,000/4,000 episodes; 72,000/12,000/12,000 rows; grouping keys and labels not predictors | pass |
| Uncertainty | 6 stored within-root intervals, 5,000 replicates, seed 49,505,000, camp clustering; no ridge-vs-structured interval exists or is shown | pass |
| Caption claims | ridge lower in all 18 root-cells (0.025–0.047); failing elements 88–443; rich-history −48/+4; Fig. 5 values 14.79 N/kg, 24.09 N/kg, 2.74 m/s | pass |
| Interpretation prose | Every interpretive sentence beside a figure is asserted against the data in `tests/manuscript.test.mjs` | pass |
| No conflation | Synthetic six-cell results and native H72/D7 contract are labelled separately on every relevant page; route qualification never combined with NRMSE | pass |
| No private artifact | Fixture inputs are confined to `docs/manuscript/v3/`; no checkpoint, weight, private path or `state_dict` text | pass |

One defect was found by review rather than by a test. The first draft of the Fig. 9 interpretation named prior history as the largest ablation effect, but the record shows current exposure (+0.1315 vs +0.0834). The text is now generated from the fixture and covered by a test.

## 2. Browser, accessibility and responsive QA

Executed locally with Playwright 1.64.1 against the static export (Chromium headless shell, SwiftShader):

- `tests/ui/qualification.spec.ts`: 10/10 pass.
  - axe-core 4.14 with tags wcag2a/aa, wcag21a/aa and wcag22aa on all six routes, at 1440 px and 390 px, with every disclosure expanded: **0 violations**.
  - Five viewports (1440×1000, 834×1112, 1112×834, 390×844, 844×390): all routes return 200, navigation is visible, and there is no page overflow.
  - Keyboard: skip link, area navigation and figure controls are reachable, with a visible focus outline.
  - Reduced motion and no WebGL (`getContext("webgl*")` returns null): every figure renders an SVG and a data table, with no page errors.
  - Data tables have captions, column headers and focusable scroll regions.
- `tests/ui/publication.spec.ts`: 7/7 pass.
  - Navigation and `aria-current`.
  - PDF byte counts and `%PDF-` headers.
  - All ten figure contracts.
  - CSV, JSON and SVG exports, with values checked.
  - Deep links.
  - Keyboard inspection.
  - Draft-status wording.
  - Mobile overflow.
- Legacy specs that the renovation broke were fixed and rerun locally: context:5, exhibition:17, exhibition:301 and gate7.
  - exhibition:301 axe found a real `link-name` defect; gate7 found a real 320 px overflow. Both are fixed.
  - The complete 50-test suite, including all 96 benchmark views, runs in GitHub CI on each PR head; see the PR checks.

axe defects found and fixed in this gate:
- wordmark label-in-name (pre-existing)
- Paper PDF label-in-name
- nested-interactive SVGs
- 24 px targets for legacy atlas links (pre-existing)
- unfocusable scrollable code block

**Not performed:**
- manual NVDA/JAWS/VoiceOver testing; `docs/GATE7_NVDA_ACCEPTANCE_V1.md` remains pending
- Safari or Firefox
- physical phones or tablets (viewports are emulated)
- forced-colours mode beyond a CSS fallback
- WebGL context-loss on the new pages (they contain no WebGL; the existing context-loss tests cover the story)

## 3. Screenshots

Fresh captures from `scripts/capture-m11.mjs`, with reduced motion and viewport-only frames:
- `docs/m11/before/`: the original `main` export (`96b4314`), overview only, because the other routes did not exist.
- `docs/m11/after/`: this head, six routes × five viewports.

Each folder's `capture-log.json` records HTTP status, horizontal overflow and console errors. All 35 records show status 200, 0 px overflow and no console errors. Historical screenshots elsewhere in `docs/` are not used as evidence for this version.

## 4. Performance (measured from the static export, gzip, no field data)

| Route | Initial JS | CSS | HTML |
| --- | ---: | ---: | ---: |
| `/` before | 340.7 KB | 24.7 KB | 210.5 KB |
| `/` after | 341.2 KB | 27.5 KB | 250.9 KB |
| `/paper/` | 171.0 KB | 27.5 KB | 71.2 KB |
| `/results/` | 204.9 KB | 27.5 KB | 163.8 KB |
| `/models/` | 202.1 KB | 27.5 KB | 97.0 KB |
| `/methods/` | 204.7 KB | 27.5 KB | 114.6 KB |
| `/evidence/` | 199.6 KB | 27.5 KB | 99.9 KB |

Export size grows from 2.7 MB to 4.8 MB, mainly from the three PDFs (0.7 MB) and the new routes' prerendered payloads. Figures are SVG and need no WebGL. The overview's initial JS is essentially unchanged because the new overview chart is server-rendered. The legacy stylesheets lost 92 lines of obsolete or duplicate rules; tokens now live in `tokens.css`. No Core Web Vitals, Lighthouse score or field data is claimed.

## 5. Deployment boundary

No production promotion, alias change, new Vercel project, custom domain or `noindex` change was made. The site metadata still sets `robots: noindex, nofollow`. Vercel preview deployments for the PRs are created by the existing Git integration and are SSO-protected; check the PR checks for their status. Production remains tied to merges into `main`, which require owner approval.
