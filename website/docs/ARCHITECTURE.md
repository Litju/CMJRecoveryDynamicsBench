# Architecture

The showcase is one statically exported Next.js App Router page. It has no API, database, authentication, analytics, model-serving service or runtime environment variables.

## Render and interaction flow

```text
Pinned scientific snapshots under source/
            │
            ▼
scripts/prepare-data.mjs ── SHA-256 checks ──► src/data/*.json
            │                                      │
            └── public/data/*.json                 ▼
                                     src/app/page.tsx + src/components/
                                                   │
                                                   ▼
                                        Next.js static export: out/
```

`npm run build` runs the fixture generator in check mode before `next build`. The build fails if a preserved source hash is wrong or a generated fixture differs from the expected deterministic serialization. The web application imports the checked JSON at build time; browsers do not fetch the source repository or run the Python benchmark.

## Application structure

- [`src/app/page.tsx`](../src/app/page.tsx) composes the site header, story, persistent chapter stage, research sections and footer.
- [`src/app/layout.tsx`](../src/app/layout.tsx) sets the document shell, metadata and temporary no-index policy. The site has no approved public hostname, so it does not claim a canonical URL.
- [`src/components/`](../src/components/) contains the narrative exhibits, filters, tables and charts. Interactive client components own local presentation state; the source-backed values remain immutable fixtures.
- [`src/lib/science.ts`](../src/lib/science.ts) provides the four displayed model definitions and selectors over the pinned receipt. It does not fit or score a model.
- [`src/lib/decay.mjs`](../src/lib/decay.mjs) and [`src/lib/response-geometry.mjs`](../src/lib/response-geometry.mjs) compute the explicitly illustrative two-mode response and chart geometry.
- [`src/lib/journey.ts`](../src/lib/journey.ts) and [`src/components/scroll-journey.tsx`](../src/components/scroll-journey.tsx) map native scroll position to the persistent stage. Scene selection dispatches to the existing model or formulation controls.
- [`src/components/scene-primitives.tsx`](../src/components/scene-primitives.tsx) owns shared Three.js camera controls, labels, lighting and context-loss handling. Focused scenes load near their chapter and provide source-backed 2D/text alternatives.

## Data and state boundaries

`source/` is a preserved, checksum-verified snapshot of selected upstream code, documentation, citation metadata and result receipts. `src/data/` contains build inputs. `public/data/` contains downloadable deterministic JSON copies. The scripts do not contact a server or execute a generator. User choices such as model, horizon, root and mathematical lab mode only select displayed values or illustrations; they do not change the underlying receipt.

The WebGL stage and focused Three.js scenes are optional presentation layers. Reduced motion, missing WebGL, a lost graphics context and narrow screens retain narrative text, exact-value matrices, 2D plots or SVG diagrams. See [scientific interpretation](SCIENCE_AND_DATA.md) before using a plotted value.

## Static output

The installed Next.js 16.4.2 configuration uses `output: "export"`, so `next build` writes a static site to `out/`. The host serves these HTML, JavaScript, CSS, font and data files; no Next.js server runtime is required. This implementation therefore avoids server-only Next.js features such as request-time handlers, cookies or image optimization.
