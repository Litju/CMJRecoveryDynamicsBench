# RES-529 independent synthetic release audit

## Disposition and reviewed identity

**Frozen commit: NO-GO** until the packaging/documentation blockers below are
applied. **Corrected candidate: GO_WITH_LIMITATIONS**, limited to public synthetic
research software. [PR #7](https://github.com/Litju/CMJRecoveryDynamicsBench/pull/7)
contains the scoped fixes and this evidence. Merge and owner acceptance of this
scope are required before a separately authorized version/publication step.
This report concerns a public synthetic research-software candidate, not exact
historical reproduction, human athlete validation, or a production scorer.
No release, tag, version bump, or DOI publication is authorized by this audit.
RES-291 remains in progress until publication actually occurs.

The audit used a fresh isolated HTTPS clone of
`https://github.com/Litju/CMJRecoveryDynamicsBench`, detached at `cd13f69f82f8`.
GitHub main matched that commit when frozen. The original tree was clean and
contained 116 tracked files, 80 package Python modules, 21 test modules, nine
reviewed documents/receipts, and root metadata. The full immutable commit and
tree IDs, complete per-file SHA-256 inventory, source archive, commands, logs,
built distributions, independent outputs and assertion scripts are retained in
the attached RES-529 evidence bundle. Full Git SHA-1 identifiers and host paths
stay outside this report under the existing public-tree boundary policy.

The frozen Git source archive SHA-256 is
`f050462283d2d4376dada166a518b40fb0a757721703efe4a56b4888c6741973`.
The frozen package-source SHA-256 is
`12e9e192accefb867707765098a4dd9eeabfd735097646fa4d4bcae5db60d0c3`.
An actual `git diff 7421f02f39d7 cd13f69f82f8 -- src` was empty. The full
resolved study commit was therefore supplied to `--git-sha`; the merge SHA was
not inferred to be the original experiment identity. Documentation and packaging
fixes below do not change any package Python bytes or original result receipts.

## Engineering evidence

CPython 3.12.13 and 3.13.13, NumPy 2.5.3, Linux x86_64; isolated environments
for development, direct wheel, direct sdist install, extracted-sdist rebuilt
wheel, and Python 3.13. Tools: pytest 9.1.1, Ruff 0.17.1, Pyright 1.1.414,
setuptools 84.0.0, uv 0.12.2, cffconvert 2.0.0.

| Check | Independent result |
|---|---|
| Frozen Python 3.12 pytest | 320 passed |
| Python 3.13 installed-package suite | 320 passed with source layout retained for repository checks, source import path disabled |
| Corrected candidate pytest | 321 passed on both Python 3.12 and 3.13 |
| Ruff lint and format | Pass |
| Strict Pyright | Zero errors, warnings or informations |
| CFF 1.2.0 schema validation | Pass |
| Direct wheel install and import outside checkout | Pass; site-packages origin |
| Direct sdist install outside checkout | Pass |
| Extracted sdist build and separate wheel install | Pass; matching package-source digest |
| Installed-sdist representative study/reproduction tests | 18 passed |
| All CLI routes | Matrix, qualification, rich-history study, fixed-mode pilot/select/evaluate exercised |

The frozen wheel has **85 entries**, including 80 Python modules and five
metadata/license entries; older 81/82/83-entry inventories describe earlier
builds. All required runtime assets are Python modules: no local data files,
private weights, checkpoint, service or historical platform is required.
The wheel deliberately omits source documentation; obtain its matching sdist.
The original sdist omitted both documentation and citation metadata; the scoped
packaging fix includes them and supplies README package metadata.

Exploratory attempts to relocate every test file into a flat external directory
failed repository-layout assertions; the extracted archive also lacks Git
metadata needed by repository-boundary checks. These are not passing runs.
The complete Python 3.13 replay retained source layout and Git metadata, used
`-o pythonpath= --import-mode=importlib`, and passed all 320 tests against the
installed package. The independent sdist smoke suite is explicitly limited to
its 18 scientific tests. The evidence bundle preserves these distinctions. No hosted CI workflow exists
in the frozen tree; these are independently executed local checks, not a claim
of GitHub CI qualification.

## Independent scientific reproduction

The fixed-mode deterministic pilot ran before full selection. Its 3,000 training
and 1,500 development rows matched the published ordered-stream hashes exactly:

- Training: `48a985dd24d396deb3e820db394bc43b5d1837028b9dd6a45c907e246226b867`.
- Development: `e898eb92ab100ab8e877e3381e1d093692ea9ec9578b22d3a3c078846533014f`.
- Zero six-cell NRMSE: `2.4418910756879324`.

Source, direct wheel, and extracted-sdist rebuilt wheel produced identical pilot
scientific records after removing only `pilot_seconds`. The full runs are monitored independently; no original receipt is overwritten
and no test-root tuning occurs. Actual stage costs are recorded in the bundle. The broader all-benchmark sweep
was extended from an initial 20-minute budget to 45 minutes after the reference
studies had completed; no scientific output was adjusted to meet a time limit.

The full fixed-mode selection lock matched exactly:
`07ce6ed56c292e2f56d306eb38b2ff8ea574f4cf0cc3f0644b94fa2db872cb21`.
Both direct-wheel and extracted-sdist rebuilt-wheel evaluations independently
matched published scientific-results SHA-256
`25032133d6f3293f722d06d3a618ec1aecec7cef35d2d35524c7431620e4bc71`.
This comparison includes all 17 models, all three test data hashes, development
selection, per-cell/per-root metrics, paired intervals and root variability;
only compute costs and the digest field itself are excluded by the declared
recipe. Mean six-cell NRMSE is 0.7362702602 (ridge), 0.7733155793
(structured), 1.0360383571 (training constant), and 2.4306587300
(zero). All six selected configurations use alpha 0.01, the declared grid floor.
Training generation took 497.07 seconds, development 71.80, and selection/fitting
10.03. Independent evaluations took 280.94 and 286.09 seconds with concurrent
qualification; runtime/file hashes differ legitimately.

The complete eight-benchmark qualification ran from the independently installed
sdist in 2370.43 seconds
(39.51 minutes). All **16 ordered row-stream
SHA-256 values match** the original immutable qualification receipt exactly.
All run specifications, numerical values, source/configuration/output provenance,
numerical checks, row schemas, label summaries and deterministic probe hashes
also match; the registered rich-history zero diagnostic is again 0.0. The current
matrix matches the independent frozen-wheel matrix. Runtime timestamps and
elapsed times are excluded from numerical comparisons. All eight historical
chains remain PARTIALLY_REPRODUCIBLE; fresh deterministic identity does not
establish exact historical replay. Full stream hashes and counts are in the
machine receipt, alongside the independently preserved raw output.

The fresh rich-history wheel study independently matched both documented input
hashes and the 338-column feature hash. All 24 table cells, row counts, RMSEs and
NRMSEs match the published four-decimal rounding. Primary alpha=1 raw progress is
`0.1759249656954272`, with 500/500 valid paired camp-bootstrap replicates and
95% interval `[0.15311580277079448, 0.18898828288735567]`. All 24 cells improve.
The independent raw rich-history JSON and comparison assertions are in the
bundle; no original rich-history machine result was committed, so numerical
comparison is to the published table rather than an invented historical digest.

## Method and claim review

- **Predictor admissibility:** fixed-mode projection exposes exactly 82 public
  fields, encoded to 84 columns. Current labels, grouping keys, hidden effects,
  discrepancy values and RNG state never enter the predictor matrix. Four prior
  episodes include their completed observed H24/H48/H72 outcomes; those are
  prior-episode observations, not current future labels. The current exposure
  and baseline precede the forecast. Rich-history encoding excludes realized
  `target_time_hours`, keeps only observed history and declared known plans,
  fits imputation/categories/scaling on training, and separates labels/grouping.
- **Selection:** six cell-specific ridge fits use training-only feature and
  target scaling, an unpenalized intercept, and mean-loss ridge penalty. Alpha
  is selected on development only from the declared grid. Evaluation verifies
  the code/package/protocol/lock digests before generating test roots. Five
  independently mutated lock fields were rejected before any test read.
  Content hashes establish integrity, not signed authenticity; the audit's Git
  and source-byte checks establish the supplied provenance.
- **Root and RNG independence:** camp streams include namespace, caller root,
  native split and camp; participant, episode, observation and discrepancy
  channels are keyed separately. Sharing the default root across training and
  development does not reuse streams because split is part of the identity.
  Test roots are frozen, exclude source roots, and use disjoint camp/key
  identities. Three seeds sample the same world and validation mixture;
  they do not prove independent-world or real-world OOD robustness.
- **Metrics and units:** innovations are force N/kg and net impulse m/s. The
  active diagnostic computes RMSE/truth population SD separately for two
  targets at each of H24/H48/H72, then equally averages six cells. It requires
  at least two labels and nonzero SD per cell. Missing labels are excluded per
  target; present non-finite labels/predictors fail. Progress is unclipped
  `1 - NRMSE`. The retired 24-cell metric averages 12 normalized errors per
  outcome and clips each outcome's progress before averaging; its zero-SD
  fallback is raw RMSE and is not used by these nondegenerate generated cells.
- **Uncertainty:** fixed-mode bootstrap shares 5,000 camp draws across models
  per root, preserves all 250 episodes and their horizons, recomputes the SD
  denominator after resampling, and pairs model-minus-zero differences.
  An independent literal whole-camp row-resampling calculation matched the
  optimized sufficient-statistic implementation over 100 toy replicates to
  relative tolerance `1e-12`. Rich-history uses 500 draws over 128 camps.
  Intervals condition on fitted models and do not include training refits;
  16 camps per active test root limits precision. Pairing is within roots.
- **Ablations and sample efficiency:** predefined feature removals are selected
  using development only. Nested 24/48/96-camp subsets refit preprocessing and
  coefficients while holding full-data selected alpha fixed. These are
  conditional learning-curve diagnostics, not independently tuned small-data
  optima. The structured comparator is fitted on public normalized loads and
  fixed 24h/84h mathematical bases, without true generator amplitudes. Because
  fits are horizon-specific, those decay multipliers are constant within each
  fit; they do not establish identified recovery time constants or a jointly
  constrained mechanistic trajectory.
- **Scientific claims:** all eight public historical generation chains remain
  partially reproducible for exact replay. Registry historical result values
  remain evidence records; this audit does not independently re-execute every
  M1 result or promote them to fresh outputs. Active production scoring is
  unimplemented. Alpha reaching 0.01 is a lower-grid limitation, not an optimum
  claim; structured regression losing to full ridge and negligible context
  ablation/sample-size differences remain reported. No empirical claim follows.

## Rights and current release safety

LICENSE contains Apache-2.0, metadata declares its SPDX expression, and both
wheel and sdist carry it. CFF author, repository and version match package
metadata. Sole-author ownership of original source/docs is an owner attestation,
not an independent legal clearance of outside materials. No upstream NOTICE
file or vendored third-party source was identified; NumPy remains an external
dependency with its own notices. No DOI or archive target is established.

The current tracked tree, Git source export, and built wheel/sdist members were
inspected. Project secret/private-path rules found no matches. Independent detect-secrets
1.5.0 final scanning produced 578 unverified hex-entropy candidates across duplicate
frozen/current/extracted views: 564 public SHA-256/test digests and 14 abbreviated
Git references. Every hit was
adjudicated; there were zero confirmed credentials. Raw results and executable
triage assertions are retained, rather than suppressing all entropy findings. No row-level datasets, checkpoint
or restricted empirical payloads ship in these bundles. This is a heuristic
current-tree/artifact assessment, not a universal credential guarantee or an
exact-byte comparison to private holdings. Restricted empirical source records
remain PROHIBITED; reproducibly generated public synthetic data plus lightweight
receipts suffice. No private data or historical checkpoints were accessed.

The accepted stale-PR-ref exception remains acknowledged. No old refs, M7 history
remediation, GitHub Support process, history rewrite or erasure work was reopened.

## Findings and minimal corrections

| ID | Severity | Evidence and reproduction | Disposition |
|---|---|---|---|
| F1 | Release blocker | Frozen `uv build`; list sdist members: no `docs/` or `CITATION.cff`, so archive users lack scientific protocols and citation. | Fixed in `ec124b7` and `24e7b5e`: MANIFEST includes only explicitly reviewed docs and CFF; README added as package metadata. Rebuilt and independently installed. |
| F2 | Release blocker | Published qualification/evaluation examples redirect output onto original immutable receipt paths. | Fixed in `cc53cec`: distinct rerun filenames; original receipts unchanged. |
| F3 | Medium | M7 report begins with superseded blocked status; original rich-history selection table obscures the subsequently added active study. | Fixed in `cc53cec`: current administrative addendum, active-study cross-links, candidate release notes and exact hash recipe. Historical audit evidence retained. |
| F4 | Limitation | Package and CFF remain `0.1.0`; no tag, DOI, empirical validation, implemented active production scorer or exact historical replay. | Intentional scope; owner publication/version decision remains outstanding. |
| F5 | Limitation | Archive testing cannot run repository/Git checks without the repository layout and Git metadata. | Representative installed-sdist tests pass; full installed-package Python 3.13 suite passes in matching source layout. |
| F6 | Limitation | Structured decay features are scaled separately within each horizon fit. | Interpret as a public-feature comparator; no identified kinetic/mechanistic claim. No retrospective protocol change. |

See [machine receipt](M8_V1_RELEASE_AUDIT_RECEIPT.json) for checks, hashes,
independent scientific comparisons and the exact candidate scope. Original
scientific receipt files are unchanged byte for byte. Final report/receipt hashes
are recorded in the external evidence manifest to avoid self-hash circularity.

## Reproduction commands

Use a fresh clone and resolve the frozen abbreviations to full SHAs locally.
Choose separate writable directories for every run; retain all stdout and
stderr. The evidence bundle supplies the exact executions and assertion scripts.
A compact replay from the repository root is:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[dev]' build cffconvert
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pyright
.venv/bin/cffconvert --validate
uv build --out-dir "$AUDIT_DIR/dist"
uv venv --python 3.12 "$AUDIT_DIR/wheel-env"
uv pip install --python "$AUDIT_DIR/wheel-env/bin/python" "$AUDIT_DIR"/dist/*.whl
STUDY_SHA=$(git rev-parse 7421f02f39d7)
cd "$AUDIT_DIR"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
wheel-env/bin/python -m cmj_recovery_dynamics.reproducibility.qualification --matrix-only > matrix.json
wheel-env/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study pilot --git-sha "$STUDY_SHA" --output pilot.json
wheel-env/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study select --git-sha "$STUDY_SHA" --output selection.json
wheel-env/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study evaluate --git-sha "$STUDY_SHA" --lock selection.json --output fixed-results.json
wheel-env/bin/python -m cmj_recovery_dynamics.studies.reference_model_study > rich-results.json
wheel-env/bin/python -m cmj_recovery_dynamics.reproducibility.qualification > qualification.json
```

Extract the sdist into another directory, run `uv build --wheel` there, install
that wheel in another fresh environment and repeat the pilot/evaluation outside
both source directories. Verify `module.__file__` resolves to site-packages and
compare package-source hashes before accepting any numerical parity claim.
