# M8 scientific reproduction matrix

## Scope and status rules

This matrix joins the public M1 lineage, M2 reproduction contracts, M3 model and
evaluation authorities, M4 study reconstructions, M5 qualification views, and
M6 synthesis. It distinguishes a fresh public synthetic run from a replay of a
historical result. The M8 run uses only the public synthetic generators and
never uses the White dataset, private checkpoints, hidden test data, or a
private runtime.

`reproducibility_status` describes the benchmark's public generation and
historical result chain together. `historical_result_status` describes only
registered historical numeric results.

| Status | Meaning |
|---|---|
| `EXACTLY_REPRODUCIBLE` | Public data identity, model and configuration, evaluation, and numerical result all have exact authority and were replayed. |
| `PARTIALLY_REPRODUCIBLE` | A supported public synthetic path runs, but at least one historical data, model, evaluation, or result authority is incomplete. |
| `NOT_REPRODUCIBLE` | No registered numeric result is available for replay, and there is no complete public historical-result path. |
| `HISTORICAL_EVIDENCE_ONLY` | M1 records numeric results, but M3 does not report a numerical replay. |

## Per-benchmark matrix

| Benchmark | M2 status; registered training / public validation rows | M8 default clean-room seeds | Public model execution | Evaluation and historical expected-result authority |
|---|---|---|---|---|
| `initial_preseason_camp_recovery` | `PARTIALLY_REPRODUCIBLE`; 4,096 / 512 | integer `20261007` on both splits | Linear baseline adapter and M0 inference adapter exist. The 39-column task projection is absent from the public source; M0 checkpoint is preserved privately and is not auto-loaded. | Four-cell selection metric is implemented. The production calibration value and initial platform metric binding remain unavailable. M1 expected records: negative-result family, linear baseline, public reference selection. |
| `canonical_preseason_camp_recovery` | `PARTIALLY_REPRODUCIBLE`; 4,096 / 512 | integer `20261007` on both splits | Historical campaign model is result evidence only; no runnable M3 model use. | Native scorer code is present, but the calibration value and model/evaluation association are unresolved. M1 expected record: five-run campaign range. |
| `rich_history_camp_recovery` | `SEMANTICALLY_REPRODUCIBLE`; 15,182 / 3,795 | `cmj-v3-oss-train-root`; `cmj-v3-oss-validation-root` | Registered zero-innovation baseline is executable. Other model results are evidence only. | Raw-progress diagnostic and 24-cell scorer implementation exist. Final historical calibration is locked. M1 public-validation records cover zero baseline, empirical-Bayes, boosted residual, headroom reference, and score reanchoring. |
| `preliminary_post_exposure_recovery` | `PARTIALLY_REPRODUCIBLE`; 72,000 / 12,000 | `cmj-v2-oss-clean-room-root` on both splits | No M3 model implementation is registered. | Production evaluation is not implemented. No public M1 numeric result is registered; the historical numeric result is `NOT_REPRODUCIBLE`. |
| `phase_consistent_post_exposure_recovery` | `SEMANTICALLY_REPRODUCIBLE`; 72,000 / 12,000 | `cmj-v2-oss-clean-room-root` on both splits | Ridge result is evidence only; no executable M3 model adapter. | Six-cell diagnostic is implemented; production scorer is not. M1 expected result: ridge research result. |
| `correlated_exposure_recovery` | `SEMANTICALLY_REPRODUCIBLE`; 72,000 / 12,000 | `cmj-v2-oss-clean-room-root` on both splits | Registered predictor families are result evidence only. | Six-cell, progress-ratio, and progress-loss diagnostics are implemented; production scorer is not. M1 expected records include local/frontier ratio, paired SRE difference, and scalar progress loss. |
| `threshold_response_recovery` | `SEMANTICALLY_REPRODUCIBLE`; 72,000 / 12,000 | `cmj-v2-oss-clean-room-root` on both splits | Reference predictor configuration is unresolved; its checkpoint is not public. | Twelve-cell scorer implementation is proposed and requires an unavailable calibration reference. No public M1 numeric result is registered; the historical numeric result is `NOT_REPRODUCIBLE`. |
| `fixed_mode_discrepancy_recovery` | `SEMANTICALLY_REPRODUCIBLE`; 72,000 / 12,000 | `cmj-v2-oss-clean-room-root` on both splits | Historical local, generic, and structured predictors are result evidence only; no runnable M3 model adapter. | Six-cell and relative-progress diagnostics are implemented; production scorer is not. M1 expected records include six-cell diagnostics and local/frontier comparison results. |

All eight have `PARTIALLY_REPRODUCIBLE` as the M8 generation-plus-result-chain
status: each has a public train and public-validation generator, but none has an
exact historical result replay. No benchmark qualifies as
`EXACTLY_REPRODUCIBLE`. Historical-result status is
`HISTORICAL_EVIDENCE_ONLY` for initial, canonical, rich-history,
phase-consistent, correlated, and fixed-mode; it is `NOT_REPRODUCIBLE` for
preliminary and threshold-response because their public registries contain no
numeric M1 result to replay.

The machine-readable receipt contains the M1 expected values and ranges, M3
result-replay status, each split's row authority and materialization status,
all registered seed authorities, model uses, evaluation bindings, missing M2
dimensions, and the M6 claim identities. Restricted model result records are
excluded from this matrix output.

## M1–M6 synthesis and remaining gaps

- M1 binds scientific questions, synthetic datasets, splits, models, results,
  and comparability. M2 records generator, RNG, observation, schema, split,
  ordering, serialization, dataset-hash, evaluation, and historical-result
  claims separately.
- M3 distinguishes executable adapters from result-only evidence and keeps
  private checkpoints from auto-loading. M4 records reconstructed protocols
  and study evidence. M5 carries those authorities into benchmark qualification
  and model-ladder views. M6 validates synthesis claims against those bindings.
- M6 contains 34 public claims. It rejects a cross-specimen leaderboard because
  the benchmarks have different worlds, targets, and evaluation identities.
  It leaves empirical recovery grounding unresolved; synthetic runs do not
  establish empirical validation.
- Historical split hashes and some RNG roots/states remain unresolved. Several
  production scorers are absent, proposed, or blocked on a locked calibration
  value. Many historic model configurations, training procedures, and
  checkpoints are not public. These gaps prevent exact historical score replay.

Fresh row counts are compared with M2's historical counts for information only.
A different count under a clean-room root does not fail the new synthetic run
and does not imply an exact historical dataset match. The public validation
split count and observed clean-room count are both retained in each receipt.

See [M8 reproduction results](M8_REPRODUCTION_RESULTS.md) and the
[machine-readable receipts](M8_PUBLIC_REPRODUCTION_RECEIPTS.json).
