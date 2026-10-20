# Continuous scientific exhibition · 2026-10-20

This is the journey implementation's original validation report. Its test count and captures are historical; the current release-grade run is recorded in [the final validation report](../VALIDATION.md).

The complete website now uses one persistent, chapter-aware 3D stage. The stage remains beside the scientific content on desktop and above it on mobile. Native scrolling continuously changes the camera and the schematic posture or elapsed-hour slice. It does not intercept wheel events, lock scrolling or require a scripted tour. Direct chapter links, pause and explicit rotation remain available.

The four spatial subjects have different scientific roles:

- **Measurement:** a schematic force plate, articulated figure and ground-reaction-force arrow. Its geometry and movement are illustrative; they are not motion-capture data or a biomechanical simulation.
- **World, limits and lab:** the existing 24 h / 84 h mathematical modes and their combined response. Depth separates curves; scroll selects illustrative elapsed hours. These are not fitted forecasts or athlete measurements.
- **History and evidence:** eight source-defined formulations with exactly five documented parent edges. Unresolved ancestry stays disconnected. Selecting a block opens the corresponding existing contract.
- **Experiment and comparison:** four source-backed NRMSE bars, from zero, for 24 h force averaged across three same-generator roots. Selecting a bar opens that exact model, root, horizon, and outcome/metric configuration in the original Explorer, including after changing its filters. It does not introduce a new result or uncertainty interval.

All chart surfaces, controls, SVG axes, WebGL backgrounds, labels, tooltips and mathematical figures share the light paper theme. Selection uses a restrained cobalt tint. The focused 24-cell 3D benchmark, exact matrices and original 2D comparison remain available.

## Validation

The complete Chromium suite has 29 cases; the scientific Node suite has 15. Strict TypeScript and the production build also pass. Original numerical fixture SHA-256 remains `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca`.

The four journey browser tests cover all nine chapter transitions, actual rendered-pixel changes under scroll, paused rendering, opt-in rotation and restored touch scrolling, sourced fallback values, light surfaces, axe accessibility, mobile chapter anchors, portrait/landscape layout bounds and actual 3D picking after changing the benchmark filters. The complete suite also retains the original 96 numerical views and the existing scientific, interaction, provenance and graphics-context-loss checks.

Motion preferences produce a static SVG/native alternative. Missing WebGL and lost contexts retain the content and existing numerical tools. Graphics rendering is on demand, and the focused figures keep viewport loading/disposal.

## Complete viewport captures

These images retain the real sticky header and persistent stage. Desktop is 1440 × 1000; mobile is 390 × 844 with touch and normal WebGL. Reduced-motion alternatives are separate. Capture metadata and uncaught errors are in [captures.json](captures.json). The [52 detailed scientific chapter/state images](../SCREENSHOTS.md) complement these 20 viewport captures.

| Chapter | Desktop | Mobile |
| --- | --- | --- |
| Opening | [View](desktop-intro.png) | [View](mobile-intro.png) |
| Measurement and setting | [View](desktop-question.png) | [View](mobile-question.png) |
| Synthetic world | [View](desktop-world.png) | [View](mobile-world.png) |
| Research history | [View](desktop-lineage.png) | [View](mobile-lineage.png) |
| Experimental design | [View](desktop-experiment.png) | [View](mobile-experiment.png) |
| Model comparison | [View](desktop-explorer.png) | [View](mobile-explorer.png) |
| Scientific limitations | [View](desktop-remaining.png) | [View](mobile-remaining.png) |
| Recovery mathematics | [View](desktop-lab.png) | [View](mobile-lab.png) |
| Evidence and open questions | [View](desktop-evidence.png) | [View](mobile-evidence.png) |
| Reduced motion | [View](desktop-reduced-motion.png) | [View](mobile-reduced-motion.png) |

## Limits

Chromium with software WebGL was exercised here. Safari, Firefox, real phones, hardware GPU performance and live screen-reader use were not checked. Automated accessibility checks are not a complete conformance assessment. Orthographic 3D can still obscure geometry; labelled native data and 2D figures remain available. The scientific Python repository, PR #8, package identity, release artifacts and numerical receipts remain unchanged.
