# Recovery Observatory · RES-534

A separate, static-first Next.js/TypeScript scientific story about public CMJ recovery research. Configurable provisional branding, an on-demand React Three Fiber hero, interactive Recharts explorer, and a two-term mathematical decay lab. Tailwind 4 and custom editorial styling; fonts are served locally. No account, database, runtime API, inference, or simulation.

## Visitor story

Four acts extend the existing observatory without replacing its numerical explorer:

1. **The question:** CMJ assessments are moments; the synthetic forecast asks about later force and net-impulse innovations. An explicitly illustrative origin/horizon strip explains the task before any NRMSE.
2. **The evolution:** eight selectable formulations form two documented families and a separate unresolved retired branch. Five parent edges come from pinned GitHub contracts. Threshold response remains a proposed alternate; fixed-mode remains an active candidate. Desktop details stay beside the tree; mobile details open directly below the selected node. Tab/Enter, click and tap work.
3. **The experiment:** disclose the four model definitions, inspect receipt-derived aggregate bars and the 28.9% recorded ridge/constant difference, then use the original model/root/horizon/outcome controls.
4. **What remains:** explore the unchanged 24 h / 84 h equation, distinguish mathematical anchors from biological compartments, and inspect the evidence ladder, limitations and reproducibility instructions.

Sticky chapter navigation follows scrolling, including direct visits to the explorer/lab/evidence. Recorded result bars reveal on entering Act III. Reduced motion disables the reveal; all figures and text remain available without animation. No dates or cross-formulation ranking are implied.

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

Six Node tests verify the four original numerical checks plus exact contract questions/statuses/parentage, checksums and graph integrity. Nine Chromium browser tests retain all 96 numerical combinations and add story ordering, progressive navigation, receipt-derived bars, lineage Tab/Enter/click/tap selection, parent navigation, scientific/evidence status separation, expanded evidence accessibility, and active-study navigation. See [validation evidence](docs/VALIDATION.md), [desktop](docs/desktop.png), [mobile](docs/mobile.png), and focused [desktop lineage](docs/lineage-desktop.png) / [mobile detail](docs/lineage-mobile.png).

## Scientific provenance

Source repository: [Litju/CMJRecoveryDynamicsBench](https://github.com/Litju/CMJRecoveryDynamicsBench), pinned to **`3dc4c82f0c948add6e4a9ebdebfd227933c823d3`**, the immutable revision specified in RES-533. The Python repository is read-only and is outside this Git project.

- The seven benchmark contract files are preserved byte-for-byte under `source/lineage/`; its separate checksum manifest pins their GitHub paths and revision. `src/data/lineage.json` retains exact source questions, statuses and direct parents; `src/lib/story.ts` separates scientific metadata, M1–M8 reconstruction evidence and new study descriptions. The lineage tests compare those fields back to every contract.
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
| `src/components/lineage.tsx`, `src/lib/story.ts`, `src/data/lineage.json` | Branching scientific contracts, independent reconstruction evidence and study context |
| `src/components/research-story.tsx`, `story-progress.tsx` | Four-act narrative, sourced result bars and progressive chapter navigation |
| `src/components/evidence.tsx` | Evidence ladder, limitations, reproducibility instructions and inspectable provenance |
| `scripts/prepare-data.mjs`, `source/manifest.json` | Deterministic source-to-fixture transformation |
| `tests/science.test.mjs`, `tests/lineage.test.mjs`, `tests/ui/*.spec.ts` | Preserved numerical verification plus lineage/story/browser/accessibility regression |

Geist font is distributed with Next.js and included under the SIL Open Font License in `public/fonts/OFL.txt`. Source research software is Apache-2.0, as preserved in `source/LICENSE`; that scope excludes external datasets and third-party materials. Creator credit follows the unchanged upstream CFF: Julio Rodriguez.

## Vercel preview

Deployment is authorized only as a **preview** to the connected `julitocrztuga-2084s-projects` team, under the neutral project name `cmj-research-showcase`. No domain or brand registration, production launch, Git connection to the scientific repository, or release action is required. `vercel.json` declares the static build.

The connector can list the team, but creation of this new project returned **403 forbidden**. The local Vercel CLI is logged out. No deployment or preview URL was created. After the owner supplies working Vercel access, create/link this separate project, verify its resolved team/project, and deploy the validated source as a preview. The existing scientific repository and PR #8 must remain untouched.
