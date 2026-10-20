# Scientific plots and 3D upgrade · 2026-10-20

This report records the plot implementation iteration. Its browser-test count and capture set are historical; use [the final validation report](../VALIDATION.md) for the current release candidate.

The existing editorial exhibition is preserved. Every figure now uses a light paper surface with dark ink, cobalt, terracotta and ochre across Recharts, SVG and WebGL, with consistent square tooltips, grid lines, model legends and selection states.

## What changed

| Figure | Previous mismatch | Completed behaviour |
| --- | --- | --- |
| [Benchmark before](before/benchmark.png) | Old tooltip, grid, point and comparison-panel colours | Shared plotting tokens; original 2D horizon view plus optional genuine 3D model/cell comparison |
| [Uncertainty before](before/uncertainty.png) | Mint intervals unrelated to the selected model | Model-coloured intervals, consistent axis typography and native per-root exact-value titles; original tables retained |
| [Lab before](before/lab.png) | Old grid, tooltip and slow-slider colouring | Consistent blue/terracotta components, neutral combined curve, shared tooltip and chart surfaces; signed response/slope/integral controls retained |
| [Response before](before/response.png) | Decorative spatial field with a fixed camera | Three real response curves with mathematical coordinates, categorical mode lanes, a time slice, curve picking and camera controls |

The 3D benchmark has 24 solid bars: four models × force/impulse at H24/H48/H72. Height is the exact source-backed cell NRMSE from zero. Depth only separates model categories. Root A/B/C/mean changes the same source values as the original explorer. Clicking a bar or matrix cell selects the existing model, horizon and outcome; the original score cards and ledger update together. The matrix exposes all 24 exact values without requiring WebGL.

The response figure uses 169 hourly samples of the existing two-exponential equation. Its total, fast and slow lanes share one response scale. The moving slice marks elapsed hours. Clicking a curve selects the nearest displayed hour, with exact equation readouts. It is a mathematical illustration, not an athlete trace, generator sample or fitted forecast.

The two focused scenes have orthographic camera presets, opt-in pointer/touch rotation and native keyboard-operable scene scale. Zoom preserves manual rotation; view presets reset orientation and scale. Page scrolling remains available until rotation is explicitly enabled. Rendering is on demand, viewport loading is deferred and scenes are released when leaving. Shared cleanup disposes controls, labels and geometry. Missing WebGL, reduced motion and actual graphics-context loss preserve exact data / 2D curves.

## Validation

- **15 Node tests pass**, including all original source/metric tests and exact time, component sum, amplitude and lane checks for the new response geometry.
- **29 Chromium browser tests pass** on the production static build, including all original 96 numerical combinations and the new matrix's 96 root/model/cell values.
- Real 3D ray picking is exercised against independently projected world coordinates, proving bar selection updates the existing controls and curve picking selects 84 h correctly.
- Camera preset and pointer-drag changes are checked against actual rendered canvas images. Scene scale is checked through keyboard input.
- Live `WEBGL_lose_context` is exercised: the 3D canvas is removed, the exact matrix opens and the application remains usable without uncaught errors.
- Reduced motion, unavailable WebGL, actual mobile WebGL rendering and native touch selection are checked. No page overflow at 320, 375, 390, 768, 1024 and 1440 px.
- Zero violations in tested axe WCAG 2 A/AA and 2.1 AA checks, including expanded exact matrices and mobile WebGL/fallback states. These checks do not establish complete accessibility conformance.
- Strict TypeScript and the production static build pass. The original numerical fixture SHA-256 remains `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca`.
- The scientific Python repository, source authorities, package identity, lockfile, citation, original result fixtures and release artifacts are unchanged. No new dependency, training, simulation, inference or deployment is introduced.

The screenshot scripts refresh 52 detailed exhibition chapter/state views plus 20 complete viewport views of the persistent scroll-driven stage, including desktop/mobile 3D figures, camera views, exact matrix and fallback captures. Tall desktop 3D captures use a taller viewport so the compositor paints the complete figure. See [the gallery](../SCREENSHOTS.md) and [raw capture/performance evidence](../browser-evidence.json). Existing browser libraries are used as documented in the root README.

## Scientific and testing limits

Orthographic projection avoids perspective-dependent size scaling, but rotation can still obscure bars or foreshorten their heights. This is disclosed in the interface; the exact matrix and 2D plot remain the direct numerical comparison tools. The 3D figures introduce no per-cell confidence intervals, direct ridge-versus-structured interval or new scientific result. Reported aggregate and paired-versus-zero intervals retain their original identities.

Safari, Firefox, physical touch devices, hardware GPU profiling and live screen readers were not tested. Browser measurements use this host's software WebGL and are not field INP or physical-device performance guarantees. Same-generator synthetic evidence still does not establish athlete validity or a production recovery score.

The whole-site upgrade is recorded in `9acc1b4` (light figures), `2e42684` (continuous 3D journey), `5eb7a6e` (exact selection and landscape) and `70e53e7` (readable native axis key). See [the journey validation and captures](../journey/VALIDATION.md).
