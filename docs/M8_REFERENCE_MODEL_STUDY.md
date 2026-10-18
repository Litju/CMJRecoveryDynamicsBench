# M8 rich-history public reference-model study

## Selection

All eight benchmark contracts have public synthetic split generators. Only
`rich_history_camp_recovery` currently combines a registered executable public
baseline with an implemented evaluator and explicit target-cell and missing
label rules on the generated row schema. This makes it the first complete
public baseline comparison in the repository. The comparison is diagnostic
and formulation-specific; the benchmark contract itself remains retired.

| Benchmark contract | Status | Complete public baseline path? | Current limitation |
|---|---|---|---|
| `initial_preseason_camp_recovery` | Superseded | No | Linear and M0 adapters exist, but the current public rows lack the required 39-feature OLS projection; the M0 checkpoint remains external. |
| `canonical_preseason_camp_recovery` | Superseded | No | A score implementation exists, but no executable model adapter is bound to this row surface. |
| `rich_history_camp_recovery` | Retired | Yes, diagnostic only | Registered zero/persistence predictor, 24-cell raw-progress diagnostic, public train/validation generators, and explicit missing-label semantics. |
| `preliminary_post_exposure_recovery` | Superseded | No | No executable model adapter; production evaluator is unimplemented. |
| `phase_consistent_post_exposure_recovery` | Superseded | No | No executable model adapter; research metrics exist, but the production evaluator is unimplemented. |
| `correlated_exposure_recovery` | Superseded | No | No executable model adapter; the production evaluator is unimplemented. |
| `threshold_response_recovery` | Proposed | No | A 12-cell evaluation exists, but there is no executable public model adapter. |
| `fixed_mode_discrepancy_recovery` | Active candidate | No | Research metrics exist, but there is no executable model adapter and the production evaluator is unimplemented. |

Here “complete” means the public generator, predictor, target contract, and
native diagnostic can be executed end to end. It does not mean the retired
formulation is an accepted production benchmark or that its historical dataset
has been exactly reproduced.

## Protocol

This new experiment is based on public `main` at `16dac3f`. It uses the checked-in clean-room
generator `LCMJ-V3-monitored-multicycle-1.1` and its deterministic roots:

| Split | Root seed | M2 expected rows | Generated rows | Study input SHA-256 |
|---|---|---:|---:|---|
| Training | `cmj-v3-oss-train-root` | 15,182 | 15,134 | `950a2dde9d6bc24f38ad518c8099ad8a727caf0e1498be32d966be3474ada03f` |
| Public validation | `cmj-v3-oss-validation-root` | 3,795 | 3,799 | `241d6ae171cba9cdc36e39ee83020f6b5caebf7a2ecadb38eed86d2cae9ff95d` |

The row-count differences from M2 are preserved. These new generated splits are
not byte-identical replays of the historical dataset. Each target has 14,271
observed and 863 missing training labels, and 3,597 observed and 202 missing
validation labels.

The predictor schema is R02 `LCMJ-V3-CANONICAL-HORIZON-ROW-1.1`
(`ea8cd5c370c894b0b3175a2b263e405f490a46421517d4f3130cc8cc53d0b2ba`). The
study uses 134 of its 135 fields: 109 numeric and 25 categorical. It excludes
`target_time_hours`, the realized future query time. It does not use grouping
keys or labels as predictors. Numeric missing values are imputed from training
means and receive missingness indicators. Categories are one-hot encoded with
a training-only, sorted vocabulary and reserved missing/unknown levels. The
encoded input has 338 columns; its feature-name SHA-256 is
`d843479d76449fd703ecd0b36ec327734fc16efac08a7be2d722f7d138539aa8`.
Scaling statistics are fitted on training features only.

Targets are the two declared baseline-relative innovations—force (N/kg) and
net impulse (m/s)—at H72 and D7. Ridge fits are separate by outcome and
horizon, with the six registered history strata pooled. A missing target is
omitted only from that target’s fit and score; non-finite labels fail the run.
The registered zero model predicts zero innovation, equivalent to carrying the
pre-index baseline forward on the innovation scale.

The primary model is closed-form ridge with `alpha=1`, standardized targets,
and an unpenalized intercept. It uses four deterministic fits over the full
public training split, with no validation-based selection. `alpha=0.1` and
`alpha=10` are declared sensitivity fits, for 12 ridge fits total. Training
uses no random initialization.

Evaluation reports cell RMSE, RMSE divided by each validation cell’s
population standard deviation, and the registered
`rich_history_raw_progress_diagnostic`. For each outcome, that diagnostic
averages normalized RMSE over 12 cells (six strata across H72 and D7), clips
`1 - mean normalized RMSE` to `[0, 1]`, then equally averages the two outcomes.
It does not apply the unavailable final historical calibration.
Every one of the 24 target cells must have at least two observed labels.

The uncertainty interval resamples the 128 represented validation camps as
clusters, keeping dependent rows from the same camp together. It uses 500
paired replicates with seed `20261017`. The interval is conditional on the
single fixed training split and the fitted models; it does not include model
refitting or split variation.

## Results

| Model | Raw progress | Mean cell NRMSE |
|---|---:|---:|
| Registered zero/persistence | 0.0000 | 1.1170 |
| Ridge, `alpha=0.1` (sensitivity) | 0.2240 | 0.7760 |
| Ridge, `alpha=1` (declared primary) | 0.1759 | 0.8241 |
| Ridge, `alpha=10` (sensitivity) | 0.0760 | 0.9240 |

For the declared primary, raw-progress improvement over zero/persistence was
`0.1759`; the paired camp-bootstrap 95% percentile interval was `[0.1531,
0.1890]` (500 of 500 valid replicates). The primary ridge had lower normalized
RMSE in all 24 cells. The sensitivity results show that performance depends on
regularization strength; `alpha=0.1` is reported as a sensitivity result and
was not selected after looking at validation.

| Outcome | Horizon | Stratum | n | Zero RMSE | Ridge RMSE | Zero NRMSE | Ridge NRMSE |
|---|---|---|---:|---:|---:|---:|---:|
| Force | H72 | L0 / clean | 260 | 2.4565 | 1.6124 | 1.2567 | 0.8249 |
| Force | H72 | L0 / degraded | 500 | 2.4153 | 1.6239 | 1.2547 | 0.8436 |
| Force | H72 | L1 / clean | 321 | 2.1091 | 1.5034 | 1.1820 | 0.8425 |
| Force | H72 | L1 / degraded | 354 | 2.1428 | 1.5163 | 1.1968 | 0.8469 |
| Force | H72 | L2 / clean | 252 | 1.7022 | 1.2646 | 1.1466 | 0.8518 |
| Force | H72 | L2 / degraded | 120 | 2.0916 | 1.4320 | 1.1972 | 0.8196 |
| Force | D7 | L0 / clean | 239 | 1.7998 | 1.3860 | 1.0536 | 0.8114 |
| Force | D7 | L0 / degraded | 499 | 1.7071 | 1.3341 | 1.0344 | 0.8084 |
| Force | D7 | L1 / clean | 317 | 1.9134 | 1.4646 | 1.0351 | 0.7923 |
| Force | D7 | L1 / degraded | 352 | 1.5396 | 1.2564 | 1.0091 | 0.8235 |
| Force | D7 | L2 / clean | 259 | 1.5711 | 1.1525 | 1.0294 | 0.7551 |
| Force | D7 | L2 / degraded | 124 | 2.0117 | 1.4487 | 1.0865 | 0.7824 |
| Net impulse | H72 | L0 / clean | 260 | 0.1983 | 0.1328 | 1.2435 | 0.8328 |
| Net impulse | H72 | L0 / degraded | 500 | 0.1974 | 0.1380 | 1.2250 | 0.8563 |
| Net impulse | H72 | L1 / clean | 321 | 0.1687 | 0.1237 | 1.1471 | 0.8410 |
| Net impulse | H72 | L1 / degraded | 354 | 0.1657 | 0.1195 | 1.1815 | 0.8524 |
| Net impulse | H72 | L2 / clean | 252 | 0.1299 | 0.1017 | 1.1352 | 0.8886 |
| Net impulse | H72 | L2 / degraded | 120 | 0.1730 | 0.1294 | 1.1544 | 0.8633 |
| Net impulse | D7 | L0 / clean | 239 | 0.1483 | 0.1169 | 1.0502 | 0.8283 |
| Net impulse | D7 | L0 / degraded | 499 | 0.1380 | 0.1083 | 1.0362 | 0.8132 |
| Net impulse | D7 | L1 / clean | 317 | 0.1425 | 0.1099 | 1.0268 | 0.7922 |
| Net impulse | D7 | L1 / degraded | 352 | 0.1241 | 0.1027 | 1.0078 | 0.8338 |
| Net impulse | D7 | L2 / clean | 259 | 0.1219 | 0.0908 | 1.0357 | 0.7713 |
| Net impulse | D7 | L2 / degraded | 124 | 0.1591 | 0.1178 | 1.0832 | 0.8021 |

## Limits and rerun

This is a new synthetic experiment on the current public generator, not a
historical model result. It does not use private checkpoints, hidden banks,
restricted measurements, or empirical athlete data. It describes one public
train/validation seed pair for a retired formulation; it does not establish
empirical recovery performance, exact M2 replay, or a production benchmark
score. The confidence interval is conditional on the fixed training split.
M8 remains in progress and no v1.0 release is authorized by this study.

From the repository root, rerun the full rich-history study with:

```text
python -m cmj_recovery_dynamics.studies.reference_model_study
```

The runner writes its machine-readable results to stdout. Keep that output
separate from the original
[`M8_PUBLIC_REPRODUCTION_RECEIPTS.json`](M8_PUBLIC_REPRODUCTION_RECEIPTS.json),
which remains unchanged.
