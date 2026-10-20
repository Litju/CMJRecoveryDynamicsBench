# RES-538 repository reconciliation

Assessment date: 2026-10-20

## Canonical repository and branch

Canonical destination: public GitHub repository Litju/CMJRecoveryDynamicsBench.
The repository default branch is main at 3dc4c82f0c948add6e4a9ebdebfd227933c823d3.
The integration branch res-538-showcase-reconciliation was created directly
from that commit in a separate worktree. The branch was 30 commits ahead of origin/main before this manifest commit.
The manifest is the 31st branch-only commit; a later trailing-space-only cleanup
in the bundled font license makes the final branch 32 commits ahead. No commit
was made to main.

Scientific PR #8 remains open against main. Its branch is
res-291-v1-publication-candidate at
618a56bbcc8de6fb1cd3a5d4d8f71bf7fcb61529, seven commits ahead and zero behind
main at the audit. It was not merged, rebased, or changed.

The GitHub account Litju has admin permission on the canonical repository. On 2026-10-20, the owner approved Apache-2.0 for Julio Rodriguez-authored website source and authorized public branch publication; the approval is recorded in RES-538.
The destination is public, so this branch publishes the website source and its reviewed history.
The owner authorized publication. PR #9 is open against main at https://github.com/Litju/CMJRecoveryDynamicsBench/pull/9.

## Publication and hosted checks

The approved website license was added in c4e68ac. Approval for Apache-2.0 and public branch publication was recorded in Linear. The current PR is https://github.com/Litju/CMJRecoveryDynamicsBench/pull/9. The branch was 34 commits ahead of origin/main immediately before this documentation commit; this commit adds one.
The initial push run 39517286430 and pull_request run 39517302876 passed on application head 4acd4cf. This final documentation commit triggers new hosted runs; see PR #9 for their results. The PR remains open and unmerged.

## Local repository inventory

The scientific checkout is the sibling CMJRecoveryDynamicsBench worktree. Its
active RES-526 branch at 878ba71 is clean and matches its upstream. The local
main ref is stale and divergent: 36 commits ahead of and 71 behind refreshed
origin/main. Other local refs were left untouched: res-288-m7-remediation is
46 ahead and 71 behind origin/main with no upstream configured;
res-291-m8-reference-study is equal to its remote ref and 11 behind main;
res-291-m8-reproduction is equal to its remote ref, 48 ahead and 71 behind
main. The website source checkout remains clean on main at
4e08777bc7c7f7ce4fa541ea3776b4cb2e2dda3b and has no configured remote.

The website source history contains 27 single-parent commits, all authored by
Julio Rodriguez, with no merge commits, tags, or additional branches. Its
reachable history contains 504 blobs and occupies 59,100 KiB in the source
object database. The largest historical blob is a 2,730,656-byte generated
screenshot. A scan of all reachable text blobs found no common private-key,
GitHub, OpenAI, AWS, Slack, or credential-assignment markers. The one dangling
5,147-byte release-checklist blob was also scanned and was not transferred to
the integration repository.

The full reachable website history is preserved through an unsquashed subtree
merge under website/. The original website repository remains intact. No
nested .git directory or submodule was added. The integrated website has 210
tracked files, including the source manifests, JSON fixtures, lockfile,
documentation, screenshots, and font license.

Ignored local material remains excluded: the 34 MB walkthrough recording,
Next build output, node_modules, static export output, test results, build
caches, and the ignored recording script. Root .gitignore has scoped
exceptions for the website package, its JSON fixtures, and its documentation.
Environment files, generated outputs, dependencies, videos, and private-data
patterns remain ignored. No tracked website file is effectively ignored.

## Source, packaging, and licensing

The website’s source manifests pin scientific authority to
3dc4c82f0c948add6e4a9ebdebfd227933c823d3. The build verified the source and
fixture hashes, including SHA-256
cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9 for the
public fixed-mode results receipt. The upstream source/LICENSE applies only to
that scientific source.

All 80 pre-existing Python modules under src/cmj_recovery_dynamics are
byte-identical to origin/main. The Python package metadata, MANIFEST.in,
LICENSE, and CITATION.cff are unchanged. One existing repository-boundary test
was narrowly updated to recognize the audited website and root workflow and
the three reviewed public provenance commits. The other 20 existing Python
test files are unchanged; the Python suite has no npm dependency.

Wheel and source-distribution builds both succeeded. A wheel import smoke test
found all eight benchmark registrations. The wheel contained 85 entries and
the source distribution 144 entries; neither contains website files.

website/LICENSE applies Apache-2.0 to original website source authored by Julio Rodriguez; the owner approved this license and publication in RES-538.
Third-party licenses remain separate: the local Geist font carries OFL 1.1; all 164 locked npm packages declare license metadata. The lock includes optional Sharp/libvips packages with LGPL-3.0-or-later metadata and caniuse-lite with CC-BY-4.0 metadata. These dependencies are not vendored in the repository; the static site does not use next/image or bundle Sharp.

The website presents pinned synthetic evidence and states that it contains no
human records. Screenshots are project captures. No credentials, private
datasets, private evidence, or third-party image/font files without an
accompanying license were found in the reviewed website tree.

## Integration changes

- Website CI now runs from .github/workflows/website-ci.yml with working
  directory website/ and path filters for website changes. It runs npm ci,
  typecheck, unit tests, static build, and Chromium tests only.
- Root README.rst links to the website package. Scientific Python packaging
  and its tests remain separate from the website workflow.
- Website release and deployment notes point to the canonical monorepo and
  identify website/ as the Vercel project root. No deployment was attempted.
- The original site workflow was removed from website/.github/workflows/.

Reconciliation commits:

- 71bd814: subtree merge preserving the complete website history.
- d9d18b9: root workflow, scoped ignore rules, and monorepo navigation.
- 160db66: public-boundary test adjustment and machine-path cleanup.
- This manifest is committed separately after validation.
- 0bc0ec7: one trailing space trimmed from the bundled OFL copy; license wording is unchanged.

## Validation results

- npm ci: passed; 118 packages installed and npm reported zero known
  vulnerabilities.
- npm run typecheck: passed.
- npm test: 15/15 passed.
- npm run build: passed; Next.js emitted the static export.
- npm run test:ui: 31/31 passed in Chromium, including all 96 sourced
  model, root, horizon, and outcome views, desktop and mobile states, accessibility,
  reduced motion, and WebGL fallback cases.
- Python pytest: 321 passed.
- Ruff lint and format checks: passed; 137 files checked.
- Strict Pyright: 0 errors, 0 warnings.
- Wheel and source distribution builds and wheel import smoke test: passed.

Chromium and the required runtime libraries were available only after extracting the missing libraries locally. The workflow’s npx playwright install --with-deps command could not install system packages because this environment has no sudo password. This did not prevent the full 31-test local browser run. The initial push and pull_request Website CI runs passed on head 4acd4cf; this document update triggers fresh runs.

## Decision and remaining launch limits

Local reconciliation is GO_WITH_LIMITATIONS. The owner approved website-source Apache-2.0 licensing and authorized public branch publication. PR #9 is open; initial hosted Website CI passed on the published head. No merge, tag, deployment, or production release was performed. PR #8 remains independent and open.
