# RES-534 validation · 2026-10-19

The verified visitor journey is question → documented branching lineage → active synthetic experiment → original numerical explorer → mathematical lab → evidence and limitations. This extends RES-533; all original numerical tests and all six original browser tests remain intact.

| Check | Result |
| --- | --- |
| `npm test` | 6/6: four unchanged numerical tests plus two source-contract/graph checks |
| `npm run typecheck` | Passed: strict TypeScript, no emit |
| `npm run build` | Passed: production static export; original fixture checksum unchanged |
| `npm run test:ui` | 9/9 passed in 34.6 s, including all six original regressions |
| Numerical UI | All 96 model × root × horizon × outcome combinations match the source |
| Scientific lineage | Eight exact questions/statuses; five source-defined edges; proposed/active fork; unresolved retired ancestry; no invented dates |
| Interaction | Tab/Enter, click, mobile touch, parent selection, inline mobile details, active-study and lab links |
| Story | Question and lineage precede the explorer; chapter navigation follows scroll and direct explorer navigation; model definitions disclose on demand |
| Results | Four displayed aggregate bars match receipts to six decimals; ridge/constant relative difference rounds to 28.9%; no unsupported paired interval |
| Evidence semantics | Generation-plus-result chain is separate from scientific status; six historical evidence-only and two not-reproducible numeric-result statuses |
| Accessibility | Zero axe violations in tested WCAG 2 A/AA + 2.1 AA rules, desktop/mobile and expanded mobile evidence; keyboard controls checked |
| Responsive layout | No page overflow at 320, 375, 390, 768, 1024, 1440 px; original wide numerical tables retain local scrolling |
| Motion/graphics | Reduced motion disables result-bar reveal and preserves 2D hero fallback; original WebGL, time scrub and lab regressions pass |
| Visual review | Desktop question/lineage/experiment and mobile lineage inspected; updated full-page desktop/mobile and focused lineage screenshots retained |
| Scope | Only this showcase changed; no scientific repo, PR #8, package metadata, citation, release or deployment changes |

## Scientific verification

Public GitHub contract files were fetched read-only at `3dc4c82f0c948add6e4a9ebdebfd227933c823d3`. Seven verbatim files define eight formulations. Their paths and SHA-256 values are in `source/lineage/manifest.json`. Tests check exact questions, statuses, parents, all checksums, edge count, the fork, missing ancestry and cycle freedom. Audience-facing summaries distinguish a sample/query-surface revision, observation-law repair, exposure-distribution change, proposed threshold alternate and fixed mathematical modes with bounded discrepancy.

Reconstruction milestones and historical evidence statuses come from the preserved M8 matrix. New retired raw-progress and active NRMSE studies remain separate. Story scores are calculated from the same immutable fixture as the explorer, not copied into a second result table. Original fixture SHA-256 remains `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca`.

The reproduction CTA was checked against the pinned upstream `README.rst`; it gives the public qualification module's `--matrix-only` command and links installation/fresh-run instructions. No upstream simulation, fitting or replay was run.

## Screenshots and environment

- `desktop.png`: full desktop page, 1440 px wide, Chromium/WebGL.
- `mobile.png`: full mobile page, 390 px wide, reduced motion/2D fallback.
- `lineage-desktop.png`: branching families, unresolved retired branch and selected detail panel.
- `lineage-mobile.png`: selected inline mobile detail with expanded evidence.

This host lacks Chromium's NSPR/NSS/ALSA libraries. Ubuntu packages `libnspr4`, `libnss3`, `libasound2t64` were downloaded and unpacked under `/tmp/cmj-browser-libs`, with no system or project dependency changes. Browser checks run using:

```sh
LD_LIBRARY_PATH=/tmp/cmj-browser-libs/extracted/usr/lib/x86_64-linux-gnu npm run test:ui
```

The first browser attempt could not launch until these host libraries were present. Subsequent checks caught and fixed an inline source-link distinction and 320 px header overflow. No original assertions were removed or relaxed.

Safari, Firefox, physical devices and live screen-reader sessions were not tested. Automated accessibility checks do not establish full conformance. No preview was deployed; existing deployment-access restrictions remain in place. Synthetic results do not establish athlete efficacy, OOD generalization, exact historical replay or production calibrated scoring.
