# Recovery Observatory · RES-536

A static-first scientific field journal built on the RES-533/534 observatory and RES-536 exhibition. Warm paper and dark ink, cobalt, vermilion and ochre; solid surfaces without decorative gradients. Next.js / TypeScript, React Three Fiber, Recharts, locally served Geist and system serif typography. No backend, login, model training, benchmark generation or inference. Package and scientific identities remain unchanged.

## Experience

The **whole exhibition is a continuous scroll-driven journey**. A persistent 3D stage follows nine chapters, with scrolling controlling the camera, schematic movement and mathematical time slice. Select a 3D model bar to open its exact benchmark view, or a formulation block to inspect that contract. Native scrolling, direct chapter links, pause and opt-in rotation keep navigation predictable. The stage becomes a compact pinned panel on phones, with a separate landscape layout. Reduced motion and unavailable graphics preserve native explanations and exact SVG values.

All scientific figures use the same light paper surface, dark axes and consistent cobalt / terracotta / ochre palette. See the [complete journey captures](docs/journey/VALIDATION.md) and [detailed scientific chapter gallery](docs/SCREENSHOTS.md).

A four-point **Understand in 90 seconds** route shares its evidence with five chapters and progressive **Methods & evidence** sheets:

- **Setting & signal:** the real sports-science motivation and the actual synthetic setting are distinguished before the models. A four-dimension exposure glossary explains all eight public load descriptors. An interactive apparatus/measurement exhibit switches among mean force, net-impulse area and baseline-relative innovation, with explicit units, construction and purpose. Cited primary background studies motivate the question; the pinned source defines this benchmark’s own observation law.
- **The world:** six-event Episode Theater with playback, keyboard/touch scrubbing, reset, model-at-origin and later-observer perspectives. World / observation / predictor / scorer layers; 82-field feature budget; an interactive mean-force/net-impulse schematic; conceptual world cards linked to the correct formulation.
- **The evolution:** a focus-preserving, interactive history reader connects each of eight source-defined formulations to its scientific issue, design decision and consequence. The exact graph retains two families and an unresolved retired branch. Exact research questions and statuses, five documented parent edges, world/observation/task/metric/model evidence sheets, URL selection and browser-history restoration. A separate reconstruction strand preserves the distinction between fresh public generation and historical replay.
- **The experiment:** four principal recorded scores, model knowledge cards, 72 real teaching cells, frozen train/development/test design and all six selection configurations. Interactive ablations and 24/48/96-camp sample efficiency use a separate receipt-derived fixture. The original **96 numerical filter combinations** remain intact. Aggregate bootstrap interval plots accompany exact root tables; comparisons never invent direct ridge-versus-structured intervals.
- **What remains:** signed 24h/84h amplitude lab with scenarios, response / derivative / signed integral charts, exact contributions, playback/reset, half-life and assumption explanations. Five evidence levels, negative findings, separately proposed falsification questions, reproducibility and citation.

Scientific figures share one palette and tooltip treatment across SVG, Recharts and WebGL. The original 2D plots stay available; the benchmark also offers **3D comparison**, showing all 24 model/outcome/horizon cell scores for the selected root. Bar picking and the exact matrix update the same model/horizon/outcome controls. Height is NRMSE from zero; model depth is categorical. Orthographic camera presets, opt-in drag rotation and scene scale work alongside exact values.

The response-model chapter now plots the combined mathematical response and its two components as three real 3D curves, with named axes, a moving time slice and curve picking to scrub elapsed hours. It replaces the decorative spatial field. Both scenes load near their viewport only, render on demand and release when leaving. Reduced motion, missing WebGL or context loss retain 2D curves / exact data. Touch scrolling is preserved until rotation is explicitly enabled.


## Run

Node.js 22+:

```sh
npm ci
npm run dev
```

Development: <http://localhost:3000>. Production static preview:

```sh
npm run build
python3 -m http.server 4173 --directory out
```

Preview: <http://localhost:4173>. The existing preview process is left running after validation. Any static host can serve `out/`.

## Validate and capture

```sh
npm test
npm run typecheck
npm run build
npx playwright install --with-deps chromium
npm run test:ui
node scripts/capture-exhibition.mjs
```

This host uses extracted browser libraries; prefix browser commands with:

```sh
LD_LIBRARY_PATH=/tmp/cmj-browser-libs/extracted/usr/lib/x86_64-linux-gnu
```

See [editorial audit and brief](docs/editorial/AUDIT.md), [validation](docs/VALIDATION.md), [browser measurements](docs/browser-evidence.json), [chapter screenshots](docs/SCREENSHOTS.md) and [implementation map](docs/IMPLEMENTATION.md). Screenshots are individual desktop/mobile chapters and selected expanded states, in addition to full-page regression captures. The capture script disables sticky positioning only while taking chapter images, preventing navigation from covering the middle of a tall capture.

## Scientific provenance

Source: [Litju/CMJRecoveryDynamicsBench](https://github.com/Litju/CMJRecoveryDynamicsBench), immutable audited commit **`3dc4c82f0c948add6e4a9ebdebfd227933c823d3`**.

- `source/manifest.json`: original receipts, study documents, citation and license with checksums.
- `source/lineage/manifest.json`: seven verbatim benchmark files defining eight formulations; tests compare exact questions, statuses, parentage and world/observation symbols.
- `source/exhibition/manifest.json`: verbatim observation, fixed-mode dynamics, correlated-exposure dynamics and reference-study implementation, fetched read-only at the same commit.
- `scripts/prepare-data.mjs`: verifies authority checksums and deterministically exports `results.json` and the separate `methods.json` fixture, to both `src/data/` and downloadable `public/data/`. Production builds reject stale fixtures. Builds need no network.
- Original result receipt SHA-256: `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9`.
- Original numerical fixture remains byte-identical: SHA-256 `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca`.

Cell NRMSE is RMSE / truth **population** SD (`ddof=0`); six cells receive equal weight. Across-root values average root-specific ratios, never mean RMSE / mean SD. Cross-root sample SD uses `ddof=1`. Force and impulse RMSE remain in their separate units. Bootstrap intervals are per-root, conditional on a fixed fit, using 5,000 whole-camp resamples of 16 camps; reported paired contrasts are against **zero**. No pooled interval or new between-model interval is computed.

The retired rich-history 24-cell raw-progress specimen stays outside the active six-cell leaderboard. Scientific status, reconstruction evidence, new public-study execution, production score implementation and empirical validity are distinct. Mathematical figures are explicitly illustrations; they are not raw generated trials, model outputs or athlete data.

## Main files

| File | Purpose |
| --- | --- |
| `scroll-journey.tsx`, `journey-scene.tsx`, `src/lib/journey.ts` | Whole-site chapter tracking, continuous scroll-controlled 3D, linked model/formulation selection and native fallbacks |
| `src/lib/brand.ts` | Configurable provisional branding |
| `src/app/page.tsx`, `globals.css` | Exhibition composition, typography and responsive design |
| `measurement-exhibit.tsx`, `src/data/context.json` | Setting, public exposure descriptors, force/impulse/innovation and primary background citations |
| `src/app/editorial.css`, `src/data/research-history.json` | Editorial design and eight source-grounded scientific decision narratives |
| `episode-theater.tsx`, `src/data/exhibition.json` | Timeline, information boundary, measurement lens and world cards |
| `lineage.tsx`, `src/lib/story.ts`, `src/data/formulation-methods.json` | Scientific ancestry, reconstruction and formulation methods |
| `experiment-methods.tsx`, `explorer.tsx`, `src/lib/science.ts` | Metric teaching, study design, diagnostics and original numerical explorer |
| `recovery-lab.tsx`, `src/lib/decay.mjs` | Signed mathematical response, analytic slope/integral and assumption drilldowns |
| `hero-instrument.tsx`, `instrument-scene.tsx`, `src/lib/response-geometry.mjs` | 3D response curves, mode isolation, curve picking and exact mathematical fallback |
| `benchmark-3d.tsx`, `benchmark-scene.tsx` | Linked 24-cell WebGL comparison and exact source-backed matrix |
| `scene-availability.tsx`, `scene-primitives.tsx`, `camera-controls.tsx`, `src/lib/plot-theme.mjs` | Shared plotting colours, camera controls, viewport loading, disposal and context-loss fallback |
| `evidence.tsx` | Negative results, evidence ladder, proposed roadmap and provenance |
| `tests/`, `scripts/capture-exhibition.mjs` | Scientific, interaction, accessibility, responsive and capture verification |

Component filenames above are under `src/components/` unless otherwise specified. Geist is distributed under the SIL Open Font License in `public/fonts/OFL.txt`. Upstream research software is Apache-2.0, excluding external datasets and third-party materials; unchanged CFF credit is Julio Rodriguez, version 0.1.0.

## Scope and preview hosting

Only this showcase is modified. The scientific Python repository, PR #8, package metadata, CFF and release artifacts are untouched. No production release, tag, domain, publication or historical replay is claimed.

The prior Vercel connector attempt returned 403 and the CLI was logged out. This implementation does not retry or bypass those restrictions. No remote deployment was created; use the running local preview above.
