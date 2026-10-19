# RES-533 validation · 2026-10-19

The story verified is: committed public receipts → deterministic compact fixture → explorer controls → exact metric/chart/table rendering. The mathematical lab is verified separately against its stated equation.

| Check | Result |
| --- | --- |
| `npm test` | 4/4 passed: pinned SHA/checksums, deterministic exports, every selected model/cell, aggregate and root sample SD, alpha selection, decay math |
| `npm run typecheck` | Passed, strict TypeScript |
| `npm run build` | Passed; statically prerendered `/` and not-found route; no runtime backend |
| `npm run test:ui` | 6/6 Playwright Chromium tests passed; final run 20.0 s |
| Numerical UI combinations | 96/96 model × root × horizon × outcome combinations matched the receipt to displayed precision |
| Accessibility | Zero axe violations for tested WCAG 2 A/AA + 2.1 AA rules at desktop and mobile; keyboard controls verified |
| Responsive widths | No page overflow at 320, 375, 390, 768, 1024, 1440 px; wide uncertainty tables scroll in labeled, keyboard-focusable regions |
| Visual review | Desktop hero/explorer and mobile hero/explorer inspected; full-page screenshots retained |
| Motion and graphics | On-demand WebGL rendering; time scrub updates scene; reduced motion and unavailable WebGL render 2D fallback |
| Lab | Amplitude and time changes match equation; keyboard increment, play/pause and reset pass |
| Data download | HTTP 200; immutable scientific revision and checksums retained |
| Production dependency audit | `npm audit --omit=dev --audit-level=high`: zero vulnerabilities |
| Browser runtime | No uncaught errors in the tested 3D/default desktop flow |
| Scientific repository | Clean working tree; local HEAD remains `878ba71cb741242f5b81b9f7da1cbe96501211b9` |
| Scientific PR #8 | Read-only GitHub check: OPEN, `mergedAt: null`; no changes made |
| Vercel preview | Blocked: new project creation returned 403; local CLI has no credentials. No preview URL exists |

Source commit: `3dc4c82f0c948add6e4a9ebdebfd227933c823d3`. Original result-file SHA-256: `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9`.

The test host lacked three Chromium library packages. They were downloaded and unpacked to `/tmp/cmj-browser-libs` without system installation; browser tests ran with `LD_LIBRARY_PATH=/tmp/cmj-browser-libs/extracted/usr/lib/x86_64-linux-gnu`. Standard machines can use Playwright's documented dependency installation command from the README.

Automated accessibility does not establish complete accessibility conformance. Physical mobile devices, screen-reader sessions, Safari and Firefox were not tested. No expensive upstream simulation, model refitting, historical replay, or empirical validation was run. Intentional design tradeoffs: discrete evaluation points are joined by straight lines with an explicit non-trajectory label; no invented pooled CI; user-initiated lab playback is allowed with reduced motion, while hero animation is disabled. Branding remains provisional and configured in `src/lib/brand.ts`.
