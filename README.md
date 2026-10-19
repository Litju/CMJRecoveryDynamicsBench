# Recovery Observatory · RES-533

A separate, static-first Next.js/TypeScript showcase of public CMJ recovery research. Configurable provisional branding, an on-demand React Three Fiber hero, interactive Recharts explorer, and a two-term mathematical decay lab. Tailwind 4 and custom editorial styling; fonts are served locally. No account, database, runtime API, inference, or simulation.

## Run

Requires Node.js 22+ and npm. Python 3 is used only by the local static-preview / browser-test server.

```sh
npm ci
npm run dev
```

Open <http://localhost:3000>. For the production static export:

```sh
npm run build
python3 -m http.server 4173 --directory out
```

Open <http://localhost:4173>. `out/` can be served by any static host.

## Validate

```sh
npm test
npm run typecheck
npm run build
npx playwright install --with-deps chromium
npm run test:ui
```

The four Node tests verify deterministic fixtures, immutable source checksums, every displayed cell, six-cell aggregation, sample root SD, paired differences, frozen alpha selection, and the illustrative equation. Six Playwright tests cover 96 model/root/horizon/outcome combinations, comparison and metric controls, ledger selection, root intervals, keyboard operation, downloads, lab play/pause/reset, 3D scrubbing, reduced motion, WebGL fallback, responsive overflow, and axe WCAG 2.1 AA checks. See [validation evidence](docs/VALIDATION.md), [desktop](docs/desktop.png), and [mobile](docs/mobile.png).

## Scientific provenance

Source repository: [Litju/CMJRecoveryDynamicsBench](https://github.com/Litju/CMJRecoveryDynamicsBench), pinned to **`3dc4c82f0c948add6e4a9ebdebfd227933c823d3`**, the immutable revision specified in RES-533. The Python repository is read-only and is outside this Git project.

- Original public receipts and documents are preserved byte-for-byte in `source/`; `source/manifest.json` maps each path to its SHA-256.
- `scripts/prepare-data.mjs` verifies every source checksum and transforms four reference models into the compact `src/data/results.json` and identical downloadable `public/data/results.json`. Run `npm run data` to regenerate. The build fails on checksum or fixture drift. Builds require no source-network access.
- Original result-file SHA-256: `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9`.
- Generated fixture SHA-256: `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca`.
- Scientific-results hash, study-code revision, selection lock, source SHA, root seeds, and row-stream hashes are retained in the fixture. They describe distinct identities and are not interchangeable.

Cell NRMSE is `RMSE / truth population SD` (`ddof=0`). The primary score is the equal-weight mean over six outcome/horizon cells. The across-root view is the arithmetic mean of three root-specific metrics: **mean RMSE / mean SD is not used**. Cross-root sample SD uses `ddof=1`; per-root camp-bootstrap intervals are copied without pooling or rebasing. RMSE units are force N/kg and net impulse m/s; they are never combined. The comparison selector changes the selected-minus-comparator contrast; reported bootstrap differences remain explicitly relative to zero.

The formulation status list is extracted from the public reference study; its older model-adapter availability is not used to describe the newer active study. Reproduction-chain status comes from the frozen reproduction matrix. Retired rich-history results are kept outside the active leaderboard. Release-audit evidence is linked without asserting publication authorization.

The lab uses `y(t) = a exp(-t/24) + b exp(-t/84)` with arbitrary unitless amplitudes and time in hours. It is not an athlete prediction, generator oracle, or reproduction of fitted predictions. The hero uses the same illustrative decay to modulate a spatial particle field; its geometry and rotation are decorative.

## Main files

| File | Purpose |
| --- | --- |
| `src/lib/brand.ts` | Provisional name and metadata; independent of scientific identity |
| `src/app/page.tsx`, `globals.css` | One-page composition and responsive visual design |
| `src/components/hero-instrument.tsx`, `instrument-scene.tsx` | Deferred 3D, scrub control, reduced-motion / WebGL / error fallback |
| `src/components/explorer.tsx`, `src/lib/science.ts` | Connected controls, real metrics, comparison chart, ledger and uncertainty |
| `src/components/recovery-lab.tsx`, `src/lib/decay.mjs` | Interactive mathematical illustration |
| `src/components/evidence.tsx` | Eight formulations, limitations and inspectable provenance |
| `scripts/prepare-data.mjs`, `source/manifest.json` | Deterministic source-to-fixture transformation |
| `tests/science.test.mjs`, `tests/ui/observatory.spec.ts` | Numerical and browser verification |

Geist font is distributed with Next.js and included under the SIL Open Font License in `public/fonts/OFL.txt`. Source research software is Apache-2.0, as preserved in `source/LICENSE`; that scope excludes external datasets and third-party materials. Creator credit follows the unchanged upstream CFF: Julio Rodriguez.

## Vercel preview

Deployment is authorized only as a **preview** to the connected `julitocrztuga-2084s-projects` team, under the neutral project name `cmj-research-showcase`. No domain or brand registration, production launch, Git connection to the scientific repository, or release action is required. `vercel.json` declares the static build.

The connector can list the team, but creation of this new project returned **403 forbidden**. The local Vercel CLI is logged out. No deployment or preview URL was created. After the owner supplies working Vercel access, create/link this separate project, verify its resolved team/project, and deploy the validated source as a preview. The existing scientific repository and PR #8 must remain untouched.
