# RES-536 chapter captures

Refreshed after the whole-site scroll-driven redesign from the production static export using Chromium, desktop 1440 × 1000 and mobile 390 × 844 with touch/reduced motion. Every scientific figure and the experimental cover share a light paper surface. Default mobile chapter captures respect reduced motion; explicit normal-mode mobile 3D views and reduced-motion fallbacks are captured separately. Both the benchmark and response-model chapter use real WebGL with exact numerical alternatives. Each file captures one chapter or focused scientific state; full-page regression captures remain in `desktop.png` and `mobile.png`.

Focused chapter captures suppress the persistent stage, sticky navigation and offscreen skip link so they do not cover tall scientific figures. The [20 complete viewport captures](journey/VALIDATION.md) retain the actual stage, header and controls on desktop and mobile. Scientific content and user-visible state are not replaced. The capture script selects expanded states through real controls. Run `node scripts/capture-exhibition.mjs` against the production preview to refresh; this host needs the browser-library prefix documented in the README.

| Chapter / state | Desktop | Mobile |
| --- | --- | --- |
| Force-plate hero | [View](screenshots/desktop-hero.png) | [View](screenshots/mobile-hero.png) |
| 90-second route | [View](screenshots/desktop-quick-route.png) | [View](screenshots/mobile-quick-route.png) |
| Research question | [View](screenshots/desktop-question.png) | [View](screenshots/mobile-question.png) |
| Apparatus and mean-force explanation | [View](screenshots/desktop-apparatus.png) | [View](screenshots/mobile-apparatus.png) |
| Net-impulse area | [View](screenshots/desktop-impulse.png) | [View](screenshots/mobile-impulse.png) |
| Baseline-relative innovation | [View](screenshots/desktop-innovation.png) | [View](screenshots/mobile-innovation.png) |
| Public exposure context | [View](screenshots/desktop-exposure.png) | [View](screenshots/mobile-exposure.png) |
| Scientific history reader | [View](screenshots/desktop-history.png) | [View](screenshots/mobile-history.png) |
| Synthetic Episode Theater | [View](screenshots/desktop-world.png) | [View](screenshots/mobile-world.png) |
| Later observer + revealed illustrative world | [View](screenshots/desktop-world-revealed.png) | [View](screenshots/mobile-world-revealed.png) |
| Shared measurement identity | [View](screenshots/desktop-measurement.png) | [View](screenshots/mobile-measurement.png) |
| Eight-formulation branching lineage | [View](screenshots/desktop-lineage.png) | [View](screenshots/mobile-lineage.png) |
| Expanded active formulation + reconstruction evidence | [View](screenshots/desktop-formulation-methods.png) | [View](screenshots/mobile-formulation-methods.png) |
| Actual experiment, metric lesson and diagnostics | [View](screenshots/desktop-experiment.png) | [View](screenshots/mobile-experiment.png) |
| Expanded split design and selection results | [View](screenshots/desktop-selection.png) | [View](screenshots/mobile-selection.png) |
| Original 96-view explorer + aggregate intervals | [View](screenshots/desktop-explorer.png) | [View](screenshots/mobile-explorer.png) |
| Mathematical assumptions introduction | [View](screenshots/desktop-remaining.png) | [View](screenshots/mobile-remaining.png) |
| Interactive mathematical lab | [View](screenshots/desktop-lab.png) | [View](screenshots/mobile-lab.png) |
| Signed area + expanded mathematical methods | [View](screenshots/desktop-lab-methods.png) | [View](screenshots/mobile-lab-methods.png) |
| Negative findings, evidence ladder and open questions | [View](screenshots/desktop-evidence.png) | [View](screenshots/mobile-evidence.png) |

Capture metadata, runtime errors, network script sizes and local interaction measurements are recorded in [browser-evidence.json](browser-evidence.json). Measurements describe this host and browser run; they are not field Core Web Vitals.

The [four before screenshots and audit notes](editorial/AUDIT.md) preserve the starting point for this redesign. Background literature is cited in the setting chapter, separately from the benchmark’s own synthetic evidence.

## Unified plotting and 3D views

| Figure / state | Desktop | Mobile |
| --- | --- | --- |
| Updated uncertainty intervals | [View](screenshots/desktop-plot-uncertainty.png) | [View](screenshots/mobile-plot-uncertainty.png) |
| Updated signed-area lab plot | [View](screenshots/desktop-plot-lab.png) | [View](screenshots/mobile-plot-lab.png) |
| Linked 3D benchmark | [View](screenshots/desktop-benchmark-3d.png) | [View](screenshots/mobile-benchmark-3d.png) |
| Front camera | [View](screenshots/desktop-benchmark-front.png) | Native camera presets are also touch-operated in browser tests |
| Exact 24-cell matrix / fallback | [View](screenshots/desktop-benchmark-matrix.png) | [View](screenshots/mobile-benchmark-fallback.png) |
| 3D response curves | [View](screenshots/desktop-response-3d.png) | [View](screenshots/mobile-response-3d.png) |
| Response mathematical fallback | Included in reduced-motion chapter captures | [View](screenshots/mobile-response-fallback.png) |

[Plot review, scientific interpretation and validation](plots/VALIDATION.md). The full capture run now contains 52 chapter/state images. Four additional [before figures](plots/before/) preserve the plotting mismatches addressed in this iteration.
