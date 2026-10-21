# Recovery Observatory — build, deployment and operations

## Current website deployment (recorded 2026-10-21)

The public Recovery Observatory research exhibit is served at **https://recovery-observatory.vercel.app**. It is an independent static website inside the canonical scientific repository, not a release of the Python research package.

| Authority | Recorded value |
| --- | --- |
| GitHub repository | [Litju/CMJRecoveryDynamicsBench](https://github.com/Litju/CMJRecoveryDynamicsBench) |
| Website source directory | `website/` |
| Production branch | `main` |
| GitHub deployed commit | `582a8c3f86fad7e20ebb6a5d907a19657ee0d8c2` |
| Vercel project | `recovery-observatory` |
| Vercel team | `julitocrztuga-2084s-projects` |
| Recorded project ID | `prj_aJ0zAG4b0YQHnq15YbnW5WlrVgH5` |
| Recorded deployment ID | `dpl_EopioesVCbzn65MCd9fEufjy5ESB` |
| Production alias | https://recovery-observatory.vercel.app |
| Status | **READY and HTTP 200**, as recorded by the deployment executor in [RES-539](https://linear.app/alignerr-cmj/issue/RES-539) |
| Deployment protection | Public production URL; preview deployments protected, per RES-539 |
| Search indexing | `noindex,nofollow`; no custom domain or canonical meta URL |

The executor recorded live Chromium validation, including the 96 benchmark configurations and the scientific fixture hashes. The deployed commit is also the canonical GitHub `main` commit after merged [PR #11](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/11). The [PR #11 hosted Website CI run](https://github.com/Litju/CMJRecoveryDynamicsBench/actions/runs/39541281041) passed.

**Verification boundary:** a separate reviewer on 2026-10-21 could verify the GitHub tree, committed scientific receipt and hosted CI, but the connected Vercel API returned `404 Project not found` for the reported team/project/deployment, and that reviewer could not fetch the public URL. This is a connector/access limitation, not a demonstrated deployment outage. If verifying operational state afresh, use the authenticated [Vercel project dashboard](https://vercel.com/julitocrztuga-2084s-projects/recovery-observatory) or an authorized CLI session.

**Immutable URL reconciliation pending:** RES-539 and a separate user handoff reported different immutable `*.vercel.app` deployment hostnames for the same deployment ID. Neither hostname is endorsed here without a direct Vercel deployment lookup. Confirm deployment `url`, `id`, aliases and Git SHA in the authenticated dashboard/CLI, then correct RES-539. The stable production alias above is the intended public link.

## Build and test from the canonical repository

Use Node.js 22 and the committed lockfile, from the website directory:

```sh
cd website
npm ci
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
npm run test:ui
```

The static build checks `source/` against the pinned manifests and regenerates neither scientific model parameters nor private data. Its four exported pages/assets are emitted to `website/out/`. The Playwright suite starts an isolated static server on `127.0.0.1:4174`, rather than reusing any development server. To manually inspect the export from `website/`:

```sh
python3 -m http.server 4173 --directory out
```

No runtime environment variables, API keys, database, Python process, private datasets or server-side inference are required.

## Vercel configuration

The production project is Git-linked to the **existing canonical repository**, root directory **`website/`**, production branch **`main`**. Use these settings:

| Setting | Value |
| --- | --- |
| Framework preset | **Other / static** (`"framework": null` in [`vercel.json`](../vercel.json)) |
| Application build tool | Next.js 16.4.2 with `output: "export"` |
| Node version | 22.x |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Output directory | `out` (relative to `website/`) |
| Git production branch | `main` |
| Environment variables | None |

**Why the Other preset?** The original Vercel Next.js framework adapter attempted to read a missing `out/routes-manifest.json` from a fully generated Next.js static export and failed with `NEXT_NO_ROUTES_MANIFEST`. Merged [PR #10](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/10) changed only the Vercel framework preset to Other. Next.js continues to compile and typecheck the site; Vercel serves the generated `out/` as static files. Do not revert to the Next.js framework adapter without qualifying a changed output contract.

## Normal change and rollback procedure

1. Make changes on a scoped branch and open a PR into canonical `main`. Require successful hosted Website CI: clean npm install, typecheck, 15+ scientific fixture/unit tests, static build and Chromium browser tests.
2. Merge only after review. Vercel's Git integration should build from the new `main` SHA. Confirm the exact deployed SHA, project settings, build logs, READY state and production alias before declaring the release complete.
3. Recheck the live story, Episode Theater, eight-formulation lineage, 96-view benchmark data, Recovery Lab, WebGL/2D fallback, mobile tables, fonts, console and network requests. Verify `/data/results.json` against the pinned source and its hashes. The latest [RES-539 report](https://linear.app/alignerr-cmj/issue/RES-539) records the first live campaign; it does not substitute for testing future deployments.
4. If production regresses, use the authorized Vercel dashboard to roll back the production alias to the last known READY deployment, and record both source SHAs/deployment IDs. Do not rewrite the Git history or silently repoint the scientific citation.
5. Keep preview access protection, `noindex,nofollow` and provisional display branding unless the owner separately approves changing them. A public website does **not** imply empirical human validity, historical score replay or Python package v1.0 publication.

Browser checks currently cover Chromium and emulated mobile. Safari, Firefox, physical device GPUs and live screen readers have not been independently qualified.