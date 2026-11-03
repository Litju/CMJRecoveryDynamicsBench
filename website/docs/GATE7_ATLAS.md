# Gate7 research atlas: developer and figure contract

The atlas extends the existing Next.js static export. It adds no hosted inference,
private evidence fetch, dependency or new scientific result. `gate7-atlas.tsx`
is a client component; `gate7.json` is the independently pinned public presentation
layer. The original M8 source files, manifests and `results.json` remain unchanged.

## Regenerate and verify

Use Node 22, then from `website/`:

```sh
npm ci
npm run data:gate7
npm test
npm run typecheck
npm run build
npm run test:ui
```

`prepare-gate7.mjs` reads an explicit allowlist of public source files authenticated against the manifest at
`08c31e0876edea14e0eb6132d08c1b2705c1cfc9`, records SHA-256 for each, and emits
stable JSON without dates or machine paths. The build rejects stale generated
bytes. No private evidence or Git history is required during the build.
Architecture descriptions are reviewed editorial summaries of the hashed Python
implementations, not automated architectural inference. Tests verify determinism,
18 routes, recorded CUDA categories and the separation from NRMSE.

## Figure ledger

| Figure | Experiment / population | Source and calculation | Accessible / export |
| --- | --- | --- | --- |
| Existing horizon comparison | Public M8 synthetic roots A/B/C | Historical `source/manifest.json`; per-cell receipts, H24/H48/H72 | Existing exact tables and exports |
| Existing six-cell heatmap | Public M8 synthetic | RMSE / truth population SD; force and impulse normalized separately | Existing exact matrix |
| Existing independent roots | Public M8 synthetic | Root means are separate experimental roots, not participant CIs | Existing explorer values |
| Existing method/sample-efficiency comparisons | Public M8 synthetic | Pinned study variants only | Existing methods exhibit |
| G1 route matrix | Gate7 engineering qualification; r0/r1 | `RES-546_INFERENCE_VERIFICATION.md`, CPU policy and family findings | Native buttons and status text; source links |
| Architecture | Gate7 engineering contract | Hashed checkpoint implementations; selected family summary | SVG title, full text contract, SVG export |
| G2 force-time | Analytical illustration, no measured population | `native-mechanics.mjs`: F(t)=75(g+8−4t/T); 41 linear samples, trapezoid sum. g=9.80665 m/s². Mean=15.80665 N/kg; impulse=6T m/s | Exact sample table, scalar values, SVG export |
| G3 timeline | Native source assessment contract | Baseline −240…−24 h; H72 66…78 h; D7 156…180 h | Text windows and exact table, SVG export |
| G4 inference flow | Gate7 authority boundaries | Public source → authenticated artifacts → loader → smoke → preflight → separately authorized study | Semantic ordered list; no quantitative score |

The complete source hashes are inspectable in the atlas and generated JSON.
Native four-cell errors are never added to the public six-cell NRMSE dataset.
No uncertainty is inferred from parity categories or analytical signals.

## Interaction and accessibility

`?architecture=additive-basis-model&run=2#model-atlas` restores a route; selection updates the URL. Older model/repeat links remain supported.
All 18 routes are native buttons with `aria-pressed`; detail updates use a polite
live region. Duration is a labeled keyboard-operable range control. The concise
seven-chapter tour advances manually with native buttons and chapter links; it
has no forced autoplay. Existing scroll progress, WebGL alternatives, benchmark
explorer and Recovery Lab remain available. Every new diagram works without WebGL.
Manual Windows/NVDA acceptance remains pending.

## Deployment boundary

Use the existing Git-linked Vercel preview and inspect its exact Git SHA. No
production alias promotion, merge, release publication or v1.1 tag is authorized
by this implementation. Follow [deployment and rollback](DEPLOYMENT.md).
Rollback means redeploying the previously verified production deployment after
owner approval; a preview can simply be discarded without changing production.

## Presentation style and public language

The model atlas follows the Observatory's existing field-journal design: warm
paper, ink, cobalt, vermilion, serif headings and square controls. SVG exports use
the same shared `plotTheme` as the benchmark figures. Public navigation and copy
use descriptive research and architecture names. Internal project/milestone labels
are excluded; original model identifiers remain in the expandable technical
reference, with the existing source filenames and shared links preserved.
