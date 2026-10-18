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
choices and fitted coefficients. `evaluate` requires that lock and refuses a
changed protocol or code SHA before generating any independent test root.
The three root strings, scoring rule, bootstrap settings, ablations, and sample
subset seed are frozen in the runner and in the lock protocol digest.

## Uncertainty, costs, and reproduction

Each test root reports per-cell RMSE/NRMSE, the aggregate six-cell NRMSE, and
paired camp-bootstrap intervals for aggregate NRMSE and its difference from the
zero baseline. The bootstrap uses 5,000 PCG64 resamples of the 16 whole camps
with seed `49,505,000`, shared across models within each root. With only 16
clusters, the intervals are descriptive and can be coarse. Cross-root results
report each root, the mean, sample SD, and range across the three independently
seeded populations. Compute costs report generation, selection/fitting, and
evaluation wall time separately.

Run the three stages from the repository root, with the full SHA of the frozen
study-code commit:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study pilot --git-sha <study-code-sha>
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study select --git-sha <study-code-sha> --output selection-lock.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study evaluate --git-sha <study-code-sha> --lock selection-lock.json --output docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json
```

The small pilot uses four training camps and two development camps. Do not run
the full selection stage until the pilot has verified the public row contract,
key separation, six-cell coverage, and measured runtime. The final machine
receipt records source commit, protocol and selection-lock digests, ordered
row-stream SHA-256 values for every split, feature schema hashes, target
counts, fit choices, per-cell results, paired intervals, cross-root variability,
and compute costs. Row-level datasets are not committed.
