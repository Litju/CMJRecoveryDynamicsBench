# Final validation · 2026-10-20

**Validated source/test revision:** `3ab3bc4` (`fix(metadata): separate scientific source attribution`). Documentation and capture evidence follow in the RES-537 documentation commit.

**Scientific authority:** [`Litju/CMJRecoveryDynamicsBench@3dc4c82f0c948add6e4a9ebdebfd227933c823d3`](https://github.com/Litju/CMJRecoveryDynamicsBench/tree/3dc4c82f0c948add6e4a9ebdebfd227933c823d3).

**Decision:** GO_WITH_LIMITATIONS for the local showcase candidate only; public source publication and Vercel deployment are NO-GO pending owner actions. See the [release checklist](RELEASE_CHECKLIST.md).

## Build and test results

| Check | Result |
| --- | --- |
| Clean `npm ci` | Passed with Node.js 22.23.2 / npm 10.9.8; 118 packages installed; no package or lockfile changes |
| `npm run typecheck` | Passed with strict TypeScript |
| `npm test` | **15/15 passed**, including deterministic source/fixture checks, all 17 reported model variants, six-cell selection minima, all eight lineage contracts and mathematical identities |
| `npm run build` | Passed; verifies all source manifests and static fixtures, then emits the Next.js 16.4.2 export to `out/` (2.7 MB) |
| `npm run test:ui` | **31/31 passed** in Chromium against the production static export in 2.0 minutes |
| `npm audit` | 0 known vulnerabilities in the lockfile at assessment time |
| `npm audit --omit=dev` | 0 known production-dependency vulnerabilities at assessment time |

The browser suite uses an isolated Python static server on `127.0.0.1:4174` with `reuseExistingServer: false`; it cannot silently attach to the Next development server on port 4173. Its `all 96 model/root/horizon/outcome combinations` test verifies exact sourced values. The 3D matrix separately checks all 96 root/model/cell values. Other cases cover the study, lineage/history, keyboard and touch interaction, chart picking, reduced motion, axe checks, unavailable WebGL, context loss, and responsive bounds.

On this host, Playwright's Chromium binary could not initially find `libnspr4.so` in the system library path. No test body ran in that attempt. Re-running with the host's already-extracted browser libraries passed all tests:

```sh
LD_LIBRARY_PATH=/tmp/cmj-browser-libs/extracted/usr/lib/x86_64-linux-gnu npm run test:ui
```

On a normal Linux host, install the browser and system dependencies first with `npx playwright install --with-deps chromium`; do not copy the `/tmp` path above to other machines.

## Fresh-browser and layout evidence

A separate production-export smoke opened fresh Chromium sessions at desktop `1440 × 1000`, mobile `390 × 844`, and mobile `390 × 844` at device scale factor 2. The desktop rendered its WebGL stage; the reduced-motion mobile modes correctly used the non-WebGL alternative. All three reported:

- zero browser console errors and uncaught page errors;
- zero failed requests or HTTP responses at status 400 or higher;
- no horizontal page overflow (scroll width equaled 1440 px or 390 px).

The browser suite checked responsive widths **320, 375, 390, 768, 1024 and 1440 px**, plus **844 × 390** landscape. Axe checks reported zero violations for the tested WCAG 2 A/AA and 2.1 AA rules/states. This is automated coverage, not a complete accessibility-conformance assessment.

No hydration warnings appeared in the fresh-browser console checks after the hero SVG coordinate-rounding fix. The current page title, `noindex,nofollow` robots policy, Open Graph text tags and Twitter summary card were confirmed in the emitted HTML. A canonical URL and image-based social card are still withheld because no public host or final brand is approved.

## Screenshots and local performance

The production export produced **52 chapter/state captures** in [`docs/screenshots/`](screenshots/) and **20 scroll-stage viewport captures** in [`docs/journey/`](journey/). Refreshed full-page views are [`docs/desktop.png`](desktop.png) at 1440 × 23,850 and [`docs/mobile.png`](mobile.png) at 390 × 33,184. The [gallery index](SCREENSHOTS.md) links the focused chapter states. Both screenshot scripts completed with zero page errors. The source, output URL, capture counts, script resources and local timings are recorded in [`docs/browser-evidence.json`](browser-evidence.json) and [`docs/journey/captures.json`](journey/captures.json).

The measured interaction samples use headless Chromium and SwiftShader (software WebGL), not a physical GPU. In the scripted chart-switch sample, median / p95 / max were 33.4 / 40.9 / 49.7 ms with the normal scene and 33.4 / 33.5 / 33.8 ms with reduced motion. They are local two-animation-frame observations, not field INP, Core Web Vitals or mobile-network timings.

## Scientific receipt verification

| File | SHA-256 |
| --- | --- |
| `source/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json` | `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9` |
| `src/data/results.json` and `public/data/results.json` | `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca` |
| `src/data/methods.json` and `public/data/methods.json` | `4d0e1302eb8a8d075d41f563d8b9c5e0e2d1341c3bccb74bd710308aff43b7fa` |
| `source/M8_V1_RELEASE_AUDIT_RECEIPT.json` | `60b17138deee66d22e766740847a344bede3f07ff794fe6ad524ea4a690151ba` |

`npm run build` verified the three pinned source manifests and both public fixture pairs. The synthetic scores, statuses, protocol, NRMSE and 24 h / 84 h mathematical illustration are documented in [Science and data](SCIENCE_AND_DATA.md). No Python generator, training run, historical replay or new score was produced for this website pass.

## Repository and launch checks

- The app has no server secrets, API, database or runtime environment variables. No `.env` file or video is tracked; generated build and test outputs are ignored.
- The public font carries its local OFL notice. The scientific source license is scoped to the upstream materials; this website has no root reuse license yet. See [attribution and licensing](../README.md#attribution-and-licensing).
- GitHub Actions configuration is present but no hosted run exists because the showcase has no Git remote and GitHub search found no matching repository.
- No Vercel project or deployment exists. The handoff records a previous 403; this environment's CLI shim fails to load its missing `dist/vc.js`. Static output is ready for an approved host, but Vercel access is not.
- A read-only check of the separate scientific clone at `878ba71` showed a clean worktree. GitHub currently reports [PR #8](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/8) open and unmerged. No scientific-repository file or PR was changed.
- The local 34 MB walkthrough recording is not included or linked: its capture timeline does not bind it to a source revision, and its video metadata could not be independently checked with `ffprobe` on this host. It remains local and ignored.

## Not tested

Only Chromium is installed. Firefox, WebKit/Safari, physical phones, hardware-GPU performance, Lighthouse/field metrics and live assistive-technology sessions were not tested. The current screenshots and SwiftShader checks do not replace those environments. No public domain, canonical URL, final commercial brand, root website license, GitHub destination or Vercel access is approved.
