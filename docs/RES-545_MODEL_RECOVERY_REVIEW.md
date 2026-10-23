# RES-545 recovered-model review

## Scope and disposition

This review checked the private recovery inventory, original source/configuration
bindings, safe-loading records, and score evidence. It did not train models or
copy checkpoint payloads into this repository. The v1.0.0 release artifacts were
not changed.

No recovered model artifact currently has explicit public redistribution
authorization. The OLS JSON is a `PUBLIC_CANDIDATE`, which still requires the
separate rights review recorded by the authority registry. Neural checkpoints
remain private under `LICENSE_REVIEW`.

## Status by model

| Model | Recovered and inference-qualified | Historical score | Public redistribution | Review status |
|---|---|---|---|---|
| Gate7 M0-r0 and M0-r1 | Yes in the recovery record: safe weights-only loads and finite original-source forward smoke | The complete score objects were exactly reproduced from the preserved validation predictions. This review did not rerun full checkpoint inference. | No | Score replay complete; checkpoint inference was previously qualified |
| Gate7 M1-M8 repeats | Yes in the recovery record for the final states | Prediction digests and per-cell metrics reconcile; some aggregate fields have floating-point aggregation differences. | No | Within-family repeat comparison only |
| Gate5 OLS comparator | Yes: the original JSON model and source predictor produced finite two-target output on the shared evaluation rows; the JSON path did not call pickle loading | The Gate7 comparator is reproduced within `1e-12`. No native OLS result packet appears in the recovered result index, so its own historical validation score is unresolved. | No; `PUBLIC_CANDIDATE` is not clearance | External comparator replay complete |
| V2R-P8L6 S00-S02 | Yes in the recovery record: safe weights-only loads and finite original-source forward smoke | No validation score exists; the configs record no validation-data access. | No | Same candidate/data/schema, but training-contract hashes vary; no performance comparison |
| V3.1 R1-AKN and V3 HGB/MLP arrays | Partial: safe tensor/array parsing only; no complete forward or score replay | No; V3.1 validation was pooled into final fitting | No | Partial reproduction |
| SP07 C1 arrays | Partial: safe NPZ parsing; no accepted evaluation binding | No | No | Partial reproduction |
| R2I result packets | No fitted estimator or checkpoint was recovered for the nine result families | No independent replay | No | Results-only evidence |
| Pickle/joblib estimators and G4 checkpoints | No | No | No | Unresolved or unsafe; pickle/joblib stayed unopened and G4 safe loading was rejected without fallback |

## Integrity and source closure

- Full SHA-256 values for the Gate7 checkpoint inventory and all model records
  matched their private ledgers, including archive-contained entries. The
  recovery-bundle manifest verified. Only final Gate7 states were loaded for
  the recorded smoke; intermediate checkpoints were hash-checked only. Digests
  and private locators are intentionally omitted here.
- Gate7's exact source tree, run configurations, result packets, model
  definition, and public fixture identities reconcile with the private source
  index. Indexed run/configuration/result/manifest records and each final
  run's config/result links matched. Across final configs, the frozen
  contract, both split identities, feature order, and target order are
  identical.
- The Gate7 model contract is 39 raw features and two baseline-relative
  innovation outputs, ordered as relative mean concentric force and relative
  concentric net impulse, with H72/D7 evaluation cells. Raw, history, and basis
  mean/standard-deviation transforms and per-cell target scales are fitted from
  training data only. The frozen config records AdamW, batch size 64, learning
  rate 0.001, weight decay 0.0001, and a 200-epoch cap. M0 has 1,346
  parameters.
- The OLS model has the same 39-feature/two-output contract. Its stored affine
  feature scaling and intercept are read from JSON; no fit was run. The
  full feature and target order matches Gate7, and the serialized linear map
  contains 39 feature rows plus its intercept for each target.
- P8L6 is a separate input contract: 82 fields become 184 encoded channels
  (70 numeric values with missingness indicators and 12 categorical fields),
  with 37,318 parameters and two innovation outputs for relative force and net
  impulse. The three seed configs
  share their training-data identity and feature/target contracts, but not the
  Gate7 data identity. Their candidate, architecture, preprocessing, and
  feature-contract digests match; their training-contract digests do not all
  match. Their validation-access flags are false.
- All indexed OLS/P8 source and configuration files matched their private
  checksums. Original source code and raw result packets are not included in
  this report.
- Neural inference in this review: **NOT_RERUN**. The prior RES-545
  weights-only loads and smoke outputs remain recorded evidence, not a fresh
  checkpoint replay here.
- The current repository environment has no PyTorch. This review therefore
  relied on RES-545's recorded weights-only load and forward-smoke results,
  verified the original loader contract statically, and did not deserialize
  neural weights again.

## Inference parity

The recovery record documents finite `(16, 2)` outputs from Gate7 final states
using the original source. M0-r0 and M0-r1 also matched the public
NumPy predictor on those smoke inputs within a sub-micro absolute tolerance;
this is tolerance parity, not bitwise equality. The smoke ran under a different
CPU PyTorch runtime from the CUDA training runtime. P8L6's three seeds each
passed original-source finite-output smoke, but no second implementation or
shared output matrix is reported for an inter-seed parity check.

## Comparison boundaries

Gate7 repeats were compared within each candidate on the same public validation
split. M0-r0 and M0-r1 reproduce their complete stored score objects from the
saved predictions. The remaining family aggregates reconcile to floating-point
precision. Saved-prediction score replay is not a full checkpoint inference
replay; no new model selection was performed.

The OLS JSON was evaluated with its original source predictor on the Gate7
validation rows. This reproduces the campaign's OLS comparator, but the OLS
training data have a different identity from Gate7's training data. Treat it as
an external historical baseline on a common evaluation split, not as a
same-training experiment. The recovered index contains no native OLS result
packet, so scoring the OLS model on its own public validation split now would
produce a new evaluation, not an exact historical score replay.

P8L6 seeds were not compared against Gate7. Their encoded input schema and
training-data identity differ. They share one candidate, architecture,
preprocessing, feature contract, and training-data identity, but their
training-contract digests are not all equal. With no validation labels or score
packet, the recorded smoke tests qualify inference shape and finiteness only;
no performance or inter-seed output parity comparison is established.

## Current public boundary

The package's existing initial-preseason M0 identity is distinct from the
Gate7 candidate named M0. The current public projection also lacks the Gate7
39-feature input contract, as recorded in the [M8 reproducibility
matrix](M8_REPRODUCIBILITY_MATRIX.md). Do not alias the recovered candidate to
that existing M0 or auto-load its private checkpoint.

This document omits private checkpoint bytes, per-row data/predictions, full
hashes, machine paths, and source commit identifiers. No model, source file,
dataset, or checkpoint is cleared for redistribution by this review.
