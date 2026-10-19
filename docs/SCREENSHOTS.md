# RES-536 chapter captures

Captured from the production static export using Chromium, desktop 1440 × 1000 and mobile 390 × 844 with touch/reduced motion. The hero uses WebGL on desktop and its 2D fallback on mobile. Each file captures one chapter or focused scientific state; full-page regression captures remain in `desktop.png` and `mobile.png`.

Sticky navigation and the offscreen skip link are suppressed only during chapter captures so neither covers the middle of tall images. Scientific content and user-visible state are not replaced. The capture script selects expanded states through real controls. Run `node scripts/capture-exhibition.mjs` against the production preview to refresh; this host needs the browser-library prefix documented in the README.

| Chapter / state | Desktop | Mobile |
| --- | --- | --- |
| Force-plate hero | [View](screenshots/desktop-hero.png) | [View](screenshots/mobile-hero.png) |
| 90-second route | [View](screenshots/desktop-quick-route.png) | [View](screenshots/mobile-quick-route.png) |
| Research question | [View](screenshots/desktop-question.png) | [View](screenshots/mobile-question.png) |
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
