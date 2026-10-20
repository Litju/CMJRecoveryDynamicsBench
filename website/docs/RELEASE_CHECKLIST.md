# Release checklist and decision

**Assessment date:** 2026-10-20

**Candidate:** Recovery Observatory in the canonical scientific repository

**Scientific source:** `Litju/CMJRecoveryDynamicsBench@3dc4c82f0c948add6e4a9ebdebfd227933c823d3`
**Local website source HEAD:** 4e08777 (docs/screenshots: refresh full-page regression captures)

## Decision

| Release surface | Decision | Reason |
| --- | --- | --- |
| Local showcase release candidate | **GO_WITH_LIMITATIONS** | Static build, scientific fixture checks, full automated suite and local responsive/accessibility/WebGL evidence pass on the recorded candidate. Firefox, Safari, physical devices, hardware GPU performance and live screen-reader review remain untested. |
| Public showcase source | **GO for review PR** | The target is the already-public Litju/CMJRecoveryDynamicsBench repository at website/. The owner approved Apache-2.0 for Julio Rodriguez-authored website source and authorized publication of the branch; approval is recorded in RES-538. website/LICENSE applies to the original website source. Third-party licenses remain separate. The showcase title/brand remains provisional. |
| Vercel preview or production deployment | **NO-GO now** | No linked project or hostname; the prior handoff records a 403, and the local CLI shim is broken. Owner/Vercel project access and explicit deployment approval are required. Vercel root directory for the monorepo is website/. |
| Scientific Python `v1.0.0` release | **NO-GO / out of scope** | This showcase does not satisfy or replace the Python release gate. PR #8 remains a separate scientific-repository decision and was not changed or merged. |

“GO_WITH_LIMITATIONS” describes the validated local candidate. The owner separately approved website-source licensing and publication for review. This does not authorize a merge, deployment, domain, release, or tag.

## Verified repository checks

- [x] Node.js 22.23.2 and npm 10.9.8 recorded; clean `npm ci` completed from `package-lock.json`.
- [x] Source, license, citation, lineage and exhibition manifests retained under `source/`.
- [x] Deterministic fixture SHA-256 checked against the pinned source receipt.
- [x] All scientific tests, TypeScript check, production build and complete Chromium suite run after the hero SVG hydration fix; exact results and commands are in [validation evidence](VALIDATION.md).
- [x] Desktop/mobile screenshots captured from the production static export and reviewed. The screenshot index is [here](SCREENSHOTS.md); the scroll-stage evidence is [here](journey/VALIDATION.md).
- [x] `npm audit` and `npm audit --omit=dev` reported no known vulnerabilities at assessment time.
- [x] The local website history has 27 single-parent commits, all by Julio Rodriguez. Its 504 reachable blobs were scanned for common credential patterns with no matches; a 5 KB dangling release-checklist blob was excluded. The largest tracked historical blob is 2.73 MB.
- [x] The website history is imported without squash under website/. The local source repository remains intact. The untracked 34 MB walkthrough, .next/, node_modules/, out/, and test artifacts are excluded.
- [x] Root .gitignore has narrow website exceptions for reviewed package files, fixtures, and documentation; .env*, dependencies, build output, videos, and private-data patterns remain excluded.
- [x] source/LICENSE applies only to upstream scientific software. website/LICENSE covers Julio Rodriguez-authored website source under Apache-2.0. The Geist font's OFL and npm package licenses remain separate.
- [x] The clean scientific checkout is on RES-526 at 878ba71. Refreshed origin/main is 3dc4c82; PR #8 remains open at 618a56b with seven commits ahead and zero behind. This integration branch starts at origin/main; PR #8 was not changed.

## Owner decision and remaining launch actions

The owner approved Apache-2.0 for Julio Rodriguez-authored website source and authorized publication of this branch for review on 2026-10-20. That approval is recorded in RES-538. Third-party licenses remain separate.

1. Confirm the provisional Recovery Observatory name, final public title/brand and an approved canonical hostname before deployment.
2. Review the published source PR before any merge. The 34 MB local walkthrough remains excluded because it is not revision-anchored or revalidated.
3. Restore authorized Vercel CLI/account access, link the approved project and authorize a preview deployment. The Vercel project root directory is website/.
4. Independently review scientific PR #8 and the Python v1.0.0 gate. This website integration does not change either.

## CI and external environments

The root .github/workflows/website-ci.yml runs the independent website npm checks, static build, and Chromium suite from website/. Its hosted results will be recorded after publication. The scientific Python package and its tests remain separate. Automated axe coverage and local Chromium/SwiftShader testing do not establish complete WCAG conformance or real-device graphics performance. Firefox, WebKit, physical phones, hardware GPU profiling and live assistive-technology sessions remain untested.
