# Fixed-mode public reference-model study

## Scope and claim boundary

This is a new synthetic research study for the active-candidate
`fixed_mode_discrepancy_recovery` formulation, based on public `main` at
`ecdf93091517` (12-character commit abbreviation). It is not a replay of historical
private scores, an empirical athlete study, or a production benchmark score.
The registered production scorer remains unimplemented. This work does not
qualify or authorize v1.0.

## Frozen public contract

The runner obtains rows through `PublicDatasetInterface` for
`fixed_mode_recovery_candidate_sample`; the underlying public generator is
`fixed_mode_discrepancy_world`. Training and development use the registered
public source roots. Each of three test roots is a fixed caller-supplied public
seed using the public-validation split geometry:

| Role | Split | Root |
|---|---|---|
| Training | `training` | `cmj-v2-oss-clean-room-root`; registered clean-room default |
| Development | `public_validation` | `cmj-v2-oss-clean-room-root`; registered clean-room default, development mixture |
| Independent test 1 | `public_validation` | `res-526-public-eval-root-a-2026-10-18` |
| Independent test 2 | `public_validation` | `res-526-public-eval-root-b-2026-10-18` |
| Independent test 3 | `public_validation` | `res-526-public-eval-root-c-2026-10-18` |

The source geometry is 96 training camps (24,000 episodes; 72,000 horizon rows)
and 16 public-validation camps (4,000 episodes; 12,000 rows). Each test root
uses the same 16-camp/4,000-episode/12,000-row validation geometry. Three
queries from an episode are kept together at H24, H48, and H72. The runner
validates participant, episode, and query key separation between training and
development and between the independent roots. Camp-unit identities use the
public keyed RNG namespace, root seed, split, and camp index; the evaluator
checks those identities are disjoint across train, development, and test.
Camp clustering for uncertainty uses the public generator's camp-major member
order and keeps all rows from a camp together.

Each row has the registered 82 public predictors: one known forecast horizon,
three current baseline fields, two declared participant-context fields, eight
current-exposure fields, and four observed prior episodes with 17 fields each.
The model encoding one-hot encodes the known horizon, producing 84 numeric
columns. Labels, participant/episode/query keys, target-time realizations,
current post-query outcomes, generator effects, RNG state, and oracle state are
not predictors. Feature means and population SDs are fitted on training rows
only; zero feature scales are set to one. Public predictors and observed labels
must be finite, except that a missing label is skipped for its target alone.

The two outputs are baseline-relative force innovations (N/kg) and net-impulse
innovations (m/s). The primary score is the registered
`six_cell_mean_cellwise_normalized_rmse`: for each of two outcomes at H24, H48,
and H72, compute RMSE divided by that cell's truth population SD (`ddof=0`),
then take the equal-weight mean over six cells. Every cell needs at least two
observations and a nonzero truth SD. The reported research progress is
`1 - six-cell mean NRMSE`, unclipped; it is not a production score.

## Deterministic pilot receipt

The 4-camp training / 2-camp development pilot passed before any independent
test root was generated. It produced 3,000 training rows and 1,500 development
rows; all six cells had 500 labels and nonzero truth SD. Participant, episode,
and query key overlaps across those splits were all zero. The registered zero
baseline development mean six-cell NRMSE was `2.4418910756879324` (unclipped
research progress `-1.4418910756879324`). Ordered row-stream SHA-256 values:

| Split | SHA-256 |
|---|---|
| Pilot training | `48a985dd24d396deb3e820db394bc43b5d1837028b9dd6a45c907e246226b867` |
| Pilot development | `e898eb92ab100ab8e877e3381e1d093692ea9ec9578b22d3a3c078846533014f` |

The committed pilot runner on study-code SHA abbreviation `b0bd5e11bca2` took
63.984 seconds on the recorded host. It used only the public source roots and
did not generate or score any evaluation test root.

## Models and locked selection

The predeclared comparators are:

1. Zero innovation, equivalent to persistence on the innovation scale.
2. One training-fitted outcome-by-horizon constant. Validation-cell means are
   never used as predictors.
3. Cellwise ridge on the public 82-field schema. Training-only feature scaling
   and target standardization are used; the intercept is unpenalized. Alpha is
   selected from `[0.01, 0.1, 1, 10, 100]` by development six-cell NRMSE, with
   ties resolved toward the lower alpha.
4. A structured fixed-mode comparator with public normalized current-exposure
   primitives multiplied by the fixed 24-hour and 84-hour decay bases, plus
   current public baselines, participant context, and observed prior-episode
   innovations. Its coefficients are estimated from training data. The fixed
   time constants are mathematical anchors; the fit does not use generator
   participant/camp effects, latent states, oracle states, or generator
   amplitude values. Its alpha uses the same training/development-only grid.

Four prespecified ablations are also selected using development only: ridge
without prior history, without current exposure fields, and without participant
context; and the structured comparator without prior history. Sample-efficiency
subsets use a deterministic nested permutation of 24, 48, and 96 training
camps. They keep the full-data selected alpha fixed and refit preprocessing and
coefficients on each training subset.

The CLI separates `pilot`, `select`, and `evaluate`. `select` writes a
content-addressed selection lock containing only the training/development
choices, fitted coefficients, full code SHA, and a package-source digest.
`evaluate` requires that lock and refuses a changed protocol, code SHA, or
package source digest before generating any independent test root.
The three root strings, scoring rule, bootstrap settings, ablations, and sample
subset seed are frozen in the runner and in the lock protocol digest.

## Results

Study code: `7421f02f39d7` (12-character Git SHA abbreviation); base public
main: `ecdf93091517`. The package-source SHA-256 is
`12e9e192accefb867707765098a4dd9eeabfd735097646fa4d4bcae5db60d0c3`. The
selection-lock SHA-256 is
`07ce6ed56c292e2f56d306eb38b2ff8ea574f4cf0cc3f0644b94fa2db872cb21`.

The public training stream contained 72,000 rows and the development stream
12,000. Both targets were complete: 72,000/72,000 training and 12,000/12,000
development observations. The source predictor-name SHA-256 is
`3ff19dcc79ef24338bfb807467c558fbec63e44c9c338846b1770fff12573e54`; the
84-column encoded feature-name SHA-256 is
`4a5e26c6e1776ab3395bce979ef2a2da7a52b15d044fecac59908642e852097a`. Ordered
row-stream SHA-256 values were:

| Split | SHA-256 |
|---|---|
| Training | `b3b6a3d523b8c46813c28d3cb3cfac15965b0c5b42881e81915da8c1b81c33cb` |
| Development | `d267bffdd3e039fbbd17966958f168d51cb191307a3fbc45a646bd788e1fe479` |

The three independent test row-stream SHA-256 values are:

| Root | SHA-256 |
|---|---|
| A | `82aec8d430dab054536caab0f8adb9020927bddf77d8a64cacc63e7f48ece353` |
| B | `cbe0e60590f0e76d08f11ffd87d07db7bca9cfd25a458cb57548e1dc401c3877` |
| C | `85c52a1ce56a9e4f2939a3b80ab13bfaddc8ac8110ff1d83c8b7c90574f3051a` |

All six ridge/structured configurations selected alpha `0.01`, the lower edge
of the frozen grid, using development only. Their development mean six-cell
NRMSEs were `0.735642` (full ridge), `0.771452` (full structured), `0.822267`
(ridge without prior history), `0.860150` (ridge without current exposure),
`0.735725` (ridge without participant context), and `0.822412` (structured
without prior history).

Across the three independently seeded test roots, mean six-cell NRMSE and
sample SD across roots were:

| Model | Mean NRMSE | Root-to-root SD |
|---|---:|---:|
| Zero innovation | 2.430659 | 0.008127 |
| Training constant | 1.036038 | 0.007308 |
| Ridge, full 82-field schema | 0.736270 | 0.003349 |
| Fixed-mode structured comparator | 0.773316 | 0.005490 |
| Ridge without prior history | 0.819681 | 0.005899 |
| Ridge without current exposure | 0.867735 | 0.006220 |
| Ridge without participant context | 0.736346 | 0.003327 |
| Structured without prior history | 0.820342 | 0.005741 |

Per-cell mean NRMSE averaged over the three roots was:

| Cell | Zero | Train constant | Ridge full | Structured full |
|---|---:|---:|---:|---:|
| H24 force | 3.0335 | 1.0477 | 0.6244 | 0.6575 |
| H24 net impulse | 2.7618 | 1.0451 | 0.6522 | 0.6960 |
| H48 force | 2.5420 | 1.0395 | 0.7319 | 0.7610 |
| H48 net impulse | 2.2644 | 1.0318 | 0.7598 | 0.8046 |
| H72 force | 2.1090 | 1.0274 | 0.8157 | 0.8429 |
| H72 net impulse | 1.8732 | 1.0248 | 0.8336 | 0.8779 |

The full ridge and structured model had 5,000/5,000 valid paired camp-bootstrap
replicates in every root. The intervals below are for each model's aggregate
six-cell NRMSE and its paired NRMSE difference from zero (negative favors the
model):

| Root | Ridge NRMSE 95% interval | Ridge minus zero | Structured NRMSE 95% interval | Structured minus zero |
|---|---:|---:|---:|---:|
| A | [0.7280, 0.7462] | [-1.7522, -1.6450] | [0.7638, 0.7843] | [-1.7147, -1.6081] |
| B | [0.7338, 0.7453] | [-1.7156, -1.6484] | [0.7735, 0.7846] | [-1.6766, -1.6092] |
| C | [0.7264, 0.7401] | [-1.7338, -1.6691] | [0.7612, 0.7751] | [-1.7005, -1.6325] |

Sample-efficiency results used nested subsets of 24, 48, and 96 training camps
with alpha selected from the full training/development data held fixed:

| Camps | Ridge NRMSE | Structured NRMSE | Training-constant NRMSE |
|---:|---:|---:|---:|
| 24 | 0.736889 | 0.773624 | 1.038164 |
| 48 | 0.736602 | 0.773621 | 1.037354 |
| 96 | 0.736270 | 0.773316 | 1.036038 |

Feature ablations show that current-exposure fields and prior-history values
helped on these populations, while removing participant context changed mean
NRMSE by only `+0.000076`. The fixed-mode comparator outperformed zero and the
training constant but did not match full ridge. The 24-to-96-camp differences
were small within this synthetic setup; 24 camps still contain 6,000 episodes.
All selected alphas hit the lower bound of the frozen grid, so weaker
regularization is a question for a separately preregistered study, not a
post-test adjustment here.

Recorded isolated-wheel compute costs were:

| Stage | Wall time |
|---|---:|
| Training generation, 96 camps | 566.6 s |
| Development generation, 16 camps | 126.9 s |
| Selection and fitting after generation | 23.5 s |
| Test generation, roots A / B / C | 66.1 / 70.4 / 68.9 s |
| Scoring and bootstrap, roots A / B / C | 1.49 / 1.33 / 1.36 s |
| Evaluation stage total | 209.6 s |

The final isolated-wheel JSON has scientific-results SHA-256
`25032133d6f3293f722d06d3a618ec1aecec7cef35d2d35524c7431620e4bc71`; the file
SHA-256 is `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9`.
It contains exact root-specific RMSE, truth SD, and NRMSE for all 17 models,
all three test-row hashes, paired bootstrap summaries, and per-cell cross-root
variation. The source and isolated-wheel evaluations matched exactly on those
scientific fields.

## Uncertainty, costs, and reproduction

Each test root reports per-cell RMSE/NRMSE, the aggregate six-cell NRMSE, and
paired camp-bootstrap intervals for aggregate NRMSE and its difference from the
zero baseline. The bootstrap uses 5,000 PCG64 resamples of the 16 whole camps
with seed `49,505,000`, shared across models within each root. With only 16
clusters, the intervals are descriptive and can be coarse. Cross-root results
report each root, the mean, sample SD, and range across the three independently
seeded populations. Compute costs report generation, selection/fitting, and
evaluation wall time separately.

Run the three stages from an installed environment, with the full SHA of the
frozen study-code commit. Resolve `7421f02f39d7` with `git rev-parse` in the
matching source checkout; the release audit verifies its package source is
identical to frozen merge `cd13f69f82f8`. Do not substitute a merge SHA solely
because it contains the study. Use new output paths and preserve the committed
receipt:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study pilot --git-sha <study-code-sha>
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study select --git-sha <study-code-sha> --output selection-lock.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study evaluate --git-sha <study-code-sha> --lock selection-lock.json --output rerun-fixed-mode-results.json
```

The small pilot uses four training camps and two development camps. Do not run
the full selection stage until the pilot has verified the public row contract,
key separation, six-cell coverage, and measured runtime. The final machine
receipt records source commit, protocol and selection-lock digests, ordered
row-stream SHA-256 values for every split, feature schema hashes, target
counts, fit choices, per-cell results, paired intervals, cross-root variability,
and compute costs. Row-level datasets are not committed.


### Hash verification

The row-stream digest hashes ordered UTF-8 compact JSON objects with sorted
keys, `ensure_ascii=False`, `allow_nan=False`, and one newline after each row.
The selection-lock digest hashes compact sorted JSON without its own
`selection_lock_sha256` field. The package-source digest visits sorted package
`*.py` paths, adding the relative POSIX path, a NUL byte, original file bytes,
and a newline for each module.

The scientific digest hashes the entire result object except `compute_costs`
and `scientific_results_sha256`, using the same compact JSON encoding without
a trailing newline. It includes runtime versions and provenance: a different
Python version or study SHA can change it without changing numerical results.
For an exact comparison use the recorded Python/NumPy versions and verified
study-code identity; otherwise compare data hashes, feature contract, selection,
per-cell/per-root metrics and intervals separately, and report differences.
The file SHA-256 includes pretty-printing and runtime costs and is expected to
differ on rerun. No original receipt should be overwritten to make hashes match.


For exact replay of the receipt above, use its original 0.1.0 study snapshot.
The 1.0.0 publication candidate changes only version metadata in package Python,
which changes the package-source digest and invalidates older selection locks.
For runs from a 1.0.0 installation, resolve and verify the matching candidate
source commit for `--git-sha`; do not label that package with the original study
SHA or reuse its lock. The original numerical receipt remains unchanged.
