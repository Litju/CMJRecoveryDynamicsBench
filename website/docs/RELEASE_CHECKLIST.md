# Recovery Observatory — release checklist and current decision

**Current assessment:** 2026-10-21, after the first public Vercel deployment. This supersedes the former **pre-publication** status in this document; it does not rewrite the historical qualification evidence.

## Current release surfaces

| Surface | Decision | Evidence and limits |
| --- | --- | --- |
| Original local showcase audit (2026-10-20) | **GO_WITH_LIMITATIONS** | Clean `npm ci`, typecheck, 15 Node science tests, 31 Chromium tests, provenance/static build and automated axe checks. Original source and screenshots remain described in [validation evidence](VALIDATION.md). |
| Canonical public GitHub repository | **GO — merged** | The owner approved Apache-2.0 for author-owned website source, excluding third-party materials. [PR #9](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/9) merged the audited website subtree; no separate repository was created. |
| Vercel production showcase | **GO_WITH_LIMITATIONS — reported READY** | Stable URL [recovery-observatory.vercel.app](https://recovery-observatory.vercel.app), deployment record [RES-539](https://linear.app/alignerr-cmj/issue/RES-539), final deployed Git SHA `582a8c3f86fad7e20ebb6a5d907a19657ee0d8c2`. The deployment executor reported HTTP 200 and production Chromium/live fixture checks. An independent reviewer could verify GitHub/CI/data but could not access the Vercel project through the connected API. |
| Python scientific package v1.0.0 | **Separate — not released** | [Scientific PR #8](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/8) remains open. This showcase's source/hosting qualification does not authorize a Python release. |

**Hosting settings:** the Vercel project builds the existing `Litju/CMJRecoveryDynamicsBench` repository with root `website/`, production branch `main`, Node 22.x, framework preset **Other**, install `npm ci`, build `npm run build`, and static output `out/`. The website still uses Next.js 16.4.2 and `output: "export"`. The original Next.js adapter failure was resolved by [PR #10](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/10); production status links were added in [PR #11](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/11).

## Source and scientific checks

- [x] Original website subtree imported with preserved audited ancestry; author-owned website code is Apache-2.0 and separate scientific/Geist/font/npm license notices remain.
- [x] Scientific Python source and packaging were preserved during website import. Original wheel and sdist smoke tests excluded website assets.
- [x] Frozen scientific source commit: `3dc4c82f0c948add6e4a9ebdebfd227933c823d3`.
- [x] Active fixed-mode public result receipt SHA-256: `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9`.
- [x] Scientific-results digest: `25032133d6f3293f722d06d3a618ec1aecec7cef35d2d35524c7431620e4bc71`.
- [x] Result data uses 3 independent seeds in one declared synthetic world. It does not establish out-of-distribution or real-athlete performance, an accepted production scorer or exact historical numeric replay.
- [x] Retired rich-history raw-progress scoring remains separate from the active six-cell NRMSE model comparison.
- [x] Final [PR #11 push CI](https://github.com/Litju/CMJRecoveryDynamicsBench/actions/runs/39541270704) and [PR CI](https://github.com/Litju/CMJRecoveryDynamicsBench/actions/runs/39541281041) completed successfully (Node unit tests, strict TypeScript, static build, Chromium UI tests).
- [x] RES-539 records 25 production Playwright tests and six core repeats after PR #11, including the 96 benchmark configurations, representative desktop/mobile interactions and fallback behavior.

## Launch and ongoing-qualification limits

- [ ] Independently verify current Vercel project/deployment metadata in an authorized dashboard or CLI. A reviewer connection returned 404 for the reported deployment despite RES-539's READY record; this is an access/verification gap, not proof of outage.
- [ ] Reconcile the **two different immutable Vercel hostnames** recorded for the same deployment ID. Use Vercel's authoritative deployment record, not guesses. The stable production alias is the public link.
- [ ] Test Safari/Firefox, actual mobile devices, hardware-accelerated WebGL and live screen readers. Chromium/headless SwiftShader and mobile emulation do not replace these.
- [ ] Decide public-discovery launch separately: the site intentionally still carries `noindex,nofollow`, with no custom domain, absolute canonical meta URL or image-based Open Graph preview. Do not change these without an owner decision.
- [ ] Review and forward-integrate separate scientific PR #8 against current main before any Python v1.0.0 release.

## Operational workflow

For subsequent website changes, open a small PR into `main`, require exact-head hosted Website CI, inspect production deployment state after merge and follow [the current deployment/rollback guide](DEPLOYMENT.md). Keep source-data checksums stable unless a reviewed scientific source/receipt revision is explicitly approved.

**Current verdict:** the static **portfolio/research exhibit** is shareable based on the recorded deployment and tests (**GO_WITH_LIMITATIONS**); the scientific Python library is not published as v1.0. The original 2026-10-20 local screenshots, test receipts and provenance remain accessible without being relabeled as new live production captures.