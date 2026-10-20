# Release checklist and decision

**Assessment date:** 2026-10-20

**Candidate:** local Recovery Observatory showcase

**Scientific source:** `Litju/CMJRecoveryDynamicsBench@3dc4c82f0c948add6e4a9ebdebfd227933c823d3`
**Current website Git HEAD before the RES-537 commits:** `cb0eab2` (`test(exhibition): verify continuous 3D journey and refresh 72 chapter captures`)

## Decision

| Release surface | Decision | Reason |
| --- | --- | --- |
| Local showcase release candidate | **GO_WITH_LIMITATIONS** | Static build, scientific fixture checks, full automated suite and local responsive/accessibility/WebGL evidence pass on the recorded candidate. Firefox, Safari, physical devices, hardware GPU performance and live screen-reader review remain untested. |
| Public showcase source repository | **NO-GO for publication now** | No Git remote or confirmed destination exists. The original website code has no root license, so a public repository would grant no clear reuse license. The showcase title/brand is provisional. Owner must select a website-source license, confirm attribution/brand and approve repository creation/visibility before publishing. |
| Vercel preview or production deployment | **NO-GO now** | No linked project or hostname; the prior handoff records a 403, and the local CLI shim is broken. Owner/Vercel project access and explicit deployment approval are required. |
| Scientific Python `v1.0.0` release | **NO-GO / out of scope** | This showcase does not satisfy or replace the Python release gate. PR #8 remains a separate scientific-repository decision and was not changed or merged. |

“GO_WITH_LIMITATIONS” describes the locally validated website candidate only. It is not approval to publish, deploy, change visibility, select a commercial identity, register a domain or release scientific Python software.

## Verified repository checks

- [x] Node.js 22.23.2 and npm 10.9.8 recorded; clean `npm ci` completed from `package-lock.json`.
- [x] Source, license, citation, lineage and exhibition manifests retained under `source/`.
- [x] Deterministic fixture SHA-256 checked against the pinned source receipt.
- [x] All scientific tests, TypeScript check, production build and complete Chromium suite run after the hero SVG hydration fix; exact results and commands are in [validation evidence](VALIDATION.md).
- [x] Desktop/mobile screenshots captured from the production static export and reviewed. The screenshot index is [here](SCREENSHOTS.md); the scroll-stage evidence is [here](journey/VALIDATION.md).
- [x] `npm audit` and `npm audit --omit=dev` reported no known vulnerabilities at assessment time.
- [x] `git remote -v` is empty; read-only GitHub search for `cmj-research-showcase` returned no results. No push, PR, repository creation or visibility change occurred.
- [x] `.gitignore` covers dependencies, generated Next/build output, Vercel local state, test results and environment files. No environment file or secret is tracked.
- [x] The exact website source is not licensed by `source/LICENSE`. The upstream scientific software attribution and font OFL notice remain explicit; see [README attribution](../README.md#attribution-and-licensing).
- [x] Static Vercel build/output configuration matches the successful local export. Vercel account/project access is still blocked/unverified; see [deployment notes](DEPLOYMENT.md).
- [x] A read-only check of the scientific clone at `878ba71` showed a clean worktree. GitHub confirms [PR #8](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/8) remains open and unmerged; no files or PR state were changed.

## Owner actions before any public launch

1. Select the license, if any, for this showcase's original website code and confirm its attribution. Do not reuse the scientific Python license by default.
2. Confirm the provisional Recovery Observatory name, final public title/brand and approved canonical hostname.
3. Approve creation of the intended GitHub repository and its visibility. Inspect the final source tree before the first push; do not publish the existing local recording as a demo because it is a 34 MB machine capture without an embedded source revision and was not revalidated against this candidate.
4. Restore authorized Vercel CLI/account access, link the approved project and authorize a preview deployment. Update the canonical URL, robots/indexing and image-based social metadata only after a hostname is approved.
5. Independently review scientific PR #8 and the Python `v1.0.0` gate. This website decision does not change either.

## CI and external environments

`.github/workflows/ci.yml` defines `npm ci`, typecheck, science tests, static build and Chromium tests for future pushes and pull requests. Since there is no remote, this workflow has not run on GitHub. Automated axe coverage and local Chromium/SwiftShader testing do not establish complete WCAG conformance or real-device graphics performance. A Chromium mobile viewport at device scale factor 2 was checked; Firefox, WebKit, physical phones, hardware GPU profiling and live assistive-technology sessions are not release evidence from this environment.
