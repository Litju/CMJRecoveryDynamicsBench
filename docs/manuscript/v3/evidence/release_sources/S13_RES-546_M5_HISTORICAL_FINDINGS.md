# RES-546 Gate7 M0/M1/M2/M3/M5 inference verification

The current M5 findings appear under **Gate7 M5 recovery: CPU source qualified,
historical CUDA blocked** below. Earlier M0–M3 sections retain historical
qualification snapshots; their statuses and test totals describe those snapshots.

## Historical M0 qualification snapshot — 2026-10-25

**READY_FOR_PRIVATE_GATE7_M0_INFERENCE_REVIEW** — both recovered original M0
repeats executed on 2026-10-25 using safe weights-only loading. The public adapter
matched the unmodified preserved original-source predictor. This report supersedes
planning-only status for these two repeats; it does not alter rights or scores.

### Artifact and source verification

The private RES-545 bundle checksums verified before use. Each repeat's checkpoint,
configuration and result packet matched the recovery inventory and Gate7 checksum
ledger. The result's checkpoint hash, repeat, candidate, seed identity, data
contract and canonical configuration digest matched the corresponding run. The
checkpoint manifest independently identified each selected state. Original model,
training and feature-extractor source bytes matched the preserved source index.
Both fitted preprocessors have identical content, embedded in their independently
verified repeat configs. No preprocessing fit, retraining or model selection ran.

The private receipt retains full artifact/configuration/source identities, fixture
receipts, runtimes, numerical comparisons and private prediction arrays. These
materials remain outside public Git; no private source, fitted scalers, weights,
restricted rows, per-row predictions, machine locators or source commit IDs are
published here.

### Synthetic execution and independent source parity

Inputs were the existing public observation builder's frozen v1 fixture: 16 rows
from its `training` partition followed by 8 from its `public_validation` partition,
each in origin-id order, H72 then D7. These names identify new synthetic predictor
fixtures, not the historical training or evaluation split. There are no target
labels and this execution establishes no predictive accuracy.

An independent conversion of the source observations to original participant-visible
records passed the unmodified original extractor with exact equality to all 936
entries of the builder's `(24, 39)` raw float64 matrix. Original and adapter fitted
standardization produced identical `(24, 39)` float32 tensors. The adapter uses
only the raw-feature branch required by M0; the original predictor also executes
its preserved history/basis preprocessing. The network has 1,346 parameters:
Linear(39,32), exact GELU, Linear(32,2). Both final outputs were finite `(24, 2)`
arrays, float32 network values returned as float64.

Outputs are innovations ordered as relative mean concentric force (N/kg) and
relative concentric net impulse (m/s). The original output transform is identity:
train-only per-cell target scales belong to loss/evaluation and must not be
multiplied into predictions. Baseline addition is not part of this adapter.

Numerical tolerances were declared in the private runner before loading or
predicting: `abs(a-b) <= 1e-6 + 1e-5 * abs(b)`. Maximum relative error is
`abs(a-b) / max(abs(b), float64.tiny)`.

| Repeat | Max absolute error | Max relative error | Finite output | Repeated call |
|---|---:|---:|---|---|
| M0-r0 | 0 | 0 | (24, 2) | Exactly equal |
| M0-r1 | 0 | 0 | (24, 2) | Exactly equal |

Runtime: Linux x86_64, Python 3.12, NumPy 2.5.3, PyTorch 2.14.1+cpu,
one CPU inference thread, deterministic algorithms enabled. Single-call wall times
are execution evidence, not a throughput benchmark; imports are excluded.

| Repeat | Adapter load | Adapter forward | Original load + forward |
|---|---:|---:|---:|
| M0-r0 | 3.32 ms | 0.84 ms | 2.41 ms |
| M0-r1 | 1.54 ms | 0.28 ms | 2.98 ms |

### Separately identified historical prediction replay

The exact 512 historical validation rows were accessible from the run-bound source
and matched the configuration's split SHA-256. Query order, horizons and target
order matched the saved predictions. Their canonical innovation matrices matched
the original result/manifest prediction digests before comparison. No hidden split
or empirical athlete dataset was used.

Predeclared historical tolerance: `abs(a-b) <= 1e-5 + 1e-4 * abs(b)`.
Original-source versus adapter CPU predictions again had zero maximum absolute
and relative error for both repeats. Against saved training-runtime predictions:

| Repeat | Max absolute error | Max relative error | Tolerance | Adapter forward |
|---|---:|---:|---|---:|
| M0-r0 | 1.430511474609375e-6 | 6.355414324126131e-5 | Pass | 0.82 ms |
| M0-r1 | 1.430511474609375e-6 | 1.439026395855604e-4 | Pass | 0.62 ms |

The combined absolute/relative tolerance applies elementwise; the maximum relative
error alone need not be below `rtol`. Saved predictions came from PyTorch
2.11.0+cu128 on CUDA; this CPU replay is tolerance parity, not bitwise historical
reproduction. No scientific score was redefined or recomputed by this execution.

### Reusable implementation and verification

Install the optional `inference` extra to import
`cmj_recovery_dynamics.model_reproduction.checkpoint_inference`. Call
`load_gate7_m0(config_path, checkpoint_path, config_sha256=..., checkpoint_sha256=...,
repeat=...)`, then `.predict(builder.matrix())`. Supply the exact pair of hashes
from independently verified private run evidence. Hashes pin bytes; they do not
establish provenance or pair association by themselves. There is no artifact
discovery, downloading or automatic private loading.

The loader verifies hashes on the same bytes it deserializes, checks the repeat,
feature/target order, preprocessing and identity output transform, and accepts
only the four finite float32 tensors of the exact architecture. It always calls
`torch.load(..., map_location="cpu", weights_only=True)` without allowlisting or
unsafe fallback. The NumPy-only package import and initial-preseason public M0
remain independent. CI installs the optional CPU runtime to exercise the tests.

Synthetic tests cover exact nonzero forward execution, deterministic inference,
RNG preservation, malformed features, float32 overflow, invalid fitted scales,
wrong configuration/repeat/hash/tensor contracts, unsafe-global rejection and
one-call weights-only loading without fallback. Verification completed: **445 pytest tests passed** (including repository boundary
and eight inference tests); Ruff check and format check passed; strict Pyright
reported zero errors or warnings. The built wheel passed **119 tests** outside the
checkout, including inference, projection and observation-builder checks. Wheel
and source archive inspection found no private model/data/source artifacts.
PyTorch is optional at runtime; CI explicitly installs it so inference tests run.

### Scientific and publication limits

This qualifies the two private Gate7 M0 checkpoints for inference review. It does
not establish clinical validity, human athlete performance, out-of-distribution
robustness, production scorer readiness or checkpoint redistribution permission.
The frozen synthetic fixture is never a historical evaluation claim. Gate7 M0
remains distinct from the initial-preseason public M0. Rights declarations,
official v1.0.0 release artifacts and existing PRs are unchanged. No PR is merged.

## Historical M0 integration qualification — 2026-10-25

**READY_FOR_M0_STACK_INTEGRATION** after the remaining inference findings were
repaired. Positive synthetic tests now execute both repeat identities, compare
nonzero forward outputs exactly, check deterministic repeated calls, distinguish
repeat-specific checkpoint/configuration bytes and outputs, and reject the other
repeat's requested identity. The authoritative target order is a `Final` tuple;
validation still accepts the original JSON arrays in their exact order.

An independent private audit verified the existing execution receipt against its
verification receipt and original adapter commit. It checked the RES-545 bundle,
repeat-specific checkpoint/config/result records, canonical config digests,
embedded preprocessing identities and original source bytes. Both the saved
prediction files' byte checksums and their canonical innovation digests verified.
The 512 historical rows matched the run-bound split identity; query order,
horizons and target order matched the saved predictions. Fresh safe execution
reproduced every preserved synthetic and historical output array exactly.
Original-source parity remains zero for both repeats, and both historical
comparisons retain the tolerances and errors reported above. No score was
recomputed. Detailed audit records remain private.

Source-fingerprint handling is reconciled in PR #14 and propagated through #15
and #16. The current trees use `RES-546-EXTRACTOR-AUTHORITY-01`; the differential
harness verifies a reviewer-supplied private SHA-256 pin before source execution.
Its actual original-source replay passed all 780 synthetic column comparisons
with zero difference. Existing decisions did not establish public disclosure
permission for that fingerprint, so the public identifier was replaced without
reopening rights decisions or rewriting history. Previously published commits
are unchanged.

Final local checks: **449 pytest tests passed**, including **21 repository
boundary tests** and **11 inference tests**; Ruff lint/format and strict Pyright
passed. The installed wheel passed **122 projection, builder and inference tests**
outside the checkout. Wheel and sdist inspection found no private payloads or
private source fingerprint. The separately checked #13, #14 and #15 source scopes
passed 326, 373 and 438 tests respectively, plus Ruff and strict Pyright. PR #13
predates Python CI; its Python checks were executed locally rather than inferred
from its website CI status.

All four sequential integration simulations were conflict-free and yielded the
intended branch trees. Repairs were propagated as ordinary commits; no merge or
force-push was performed. Preserve ancestry with merge commits when integration
is authorized: #13 into main, retarget and integrate #14, then #15, then #16.
Refresh CI and review the incremental diff after each retarget. Draft/review and
merge authorization remain separate from this technical qualification. Existing
rights, scientific definitions and official release artifacts remain unchanged.

## Gate7 M1 recovered inference qualification — 2026-10-26

**READY_FOR_PRIVATE_GATE7_M1_INFERENCE_REVIEW** for both recovered final repeats,
M1-r0 and M1-r1. The recovery inventory, final-weight records, run registry and
checkpoint manifest agree on this complete final-repeat set. Intermediate epoch
and environment-qualification checkpoints are not final-repeat artifacts and were
not selected or executed. No training, fitting or model selection ran.

### Recovered contract and implementation

The independently verified original model source defines M1 as a raw-only
39→64→2 network with exact GELU between its two linear layers: **2,690 parameters**.
Its exact float32 state dictionary is:

| Tensor | Shape |
|---|---|
| `raw_wide.0.weight` | `(64, 39)` |
| `raw_wide.0.bias` | `(64,)` |
| `raw_wide.2.weight` | `(2, 64)` |
| `raw_wide.2.bias` | `(2,)` |

There is no dropout in this candidate's forward path. The original preprocessing
also constructs history `(N, 4, 4)`, horizon `(N,)` and basis `(N, 5)` inputs, but
M1's forward method uses only raw features. The adapter accepts the existing
finite float64 `(N, 39)` projection in `GATE7_FEATURE_NAMES` order. It applies the
M1 run's fitted `(raw - raw_mean) / raw_scale` in float64 and casts to float32.
The original fitting rule is training-only mean and sample standard deviation
(`ddof=1`), replacing zero scales with one. No fitted values are published or
refitted. Each repeat's own configuration supplies its preprocessing; equal
preprocessing content was verified rather than inferred from M0.

Outputs are `(N, 2)` innovations, ordered as relative mean concentric force
(N/kg), then relative concentric net impulse (m/s). Network float32 outputs are
returned as float64. The output transform is identity. Target scales used by the
original loss/evaluation are not applied to inference, and baseline addition is
not part of this adapter.

Install the optional `inference` extra and import `load_gate7_m1` from
`cmj_recovery_dynamics.model_reproduction.checkpoint_inference`. Its arguments
match the existing M0 loader: explicit config/checkpoint paths, independently
pinned `config_sha256`, `checkpoint_sha256`, and `repeat=0` or `repeat=1`; call the
returned `Gate7M1Predictor.predict(raw_features)`. No private files are discovered
or downloaded. The shared raw-network execution and validation are justified by
the recovered source; M1's width and tensor namespace remain distinct from M0.
M0's public API, configuration contract and inference behavior are preserved.

The loader pins the exact bytes it consumes and uses only
`torch.load(..., map_location="cpu", weights_only=True)`, with no unsafe fallback
or added allowlisted globals. It rejects wrong candidate/repeat/input/output
contracts, M1 width mismatches, invalid fitted scales, incompatible tensor keys,
shapes or dtypes, and nonfinite tensors, preprocessing or predictions. Digest
pins alone do not establish candidate/checkpoint association: the private
qualification independently verifies the inventory, run configuration, canonical
configuration digest, result, seed identity, source binding and final checkpoint.
A caller must supply the corresponding verified pair of pins.

### Frozen synthetic fixture execution

The fixture is unchanged: 16 `training` rows followed by 8 `public_validation`
rows, ordered by origin then H72/D7. These are synthetic fixture partition names,
not historical evaluation membership. Independent conversion of observations to
original-source records reproduced all 936 raw feature values exactly. The
original preprocessing and adapter produced exactly equal `(24, 39)` float32
inputs for both repeats. All outputs were finite and repeated calls were exactly
equal. The unmodified original M1 predictor used its own source-defined network
and complete preprocessing path.

Source-parity tolerance was declared before execution:
`abs(adapter - original) <= 1e-6 + 1e-5 * abs(original)`.

| Repeat | Max absolute error | Max relative error | Output | Deterministic |
|---|---:|---:|---|---|
| M1-r0 | 0 | 0 | Finite `(24, 2)` | Exact |
| M1-r1 | 0 | 0 | Finite `(24, 2)` | Exact |

### Separate historical prediction replay

For each repeat, the original validation bytes were retrieved from its verified
run-bound source and matched the split digest in its configuration. Both splits
contained exactly 512 rows. Before replay, saved prediction file byte checksums
matched the preserved ledger; canonical innovation digests matched the original
result, run registry and checkpoint manifest. Saved query ordering, horizons and
target order matched the validation rows exactly. Byte digests, canonical
prediction digests and query-order digests remain in the private receipt.

The historical tolerance was separately predeclared:
`abs(replayed - saved) <= 1e-5 + 1e-4 * abs(saved)`. Both adapter replays matched
the unmodified original CPU predictor exactly, including preprocessing. Against
the saved training-runtime predictions:

| Repeat | Max absolute error | Max relative error | Historical replay |
|---|---:|---:|---|
| M1-r0 | 1.430511474609375e-6 | 5.814875508801607e-5 | Pass, 512 rows |
| M1-r1 | 1.430511474609375e-6 | 4.9153575431076854e-5 | Pass, 512 rows |

Relative error is `abs(replayed - saved) / max(abs(saved), float64.tiny)`.
The elementwise combined tolerance defines acceptance. Runtime was Python 3.12,
NumPy 2.5.3 and PyTorch 2.14.1+cpu, one CPU thread, deterministic algorithms
enabled. Saved predictions originated on the preserved CUDA training runtime;
this is numerical prediction parity, not bitwise cross-device reproduction.
Historical scores were neither recomputed nor reinterpreted. The synthetic
fixture results establish execution parity only.

### Private evidence and review scope

The private execution receipt records repeat-specific artifact and configuration
identities, original source bindings, fitted preprocessing digests, tensor shapes,
fixture receipts, deterministic execution, errors, runtimes and historical
prediction/order digests. The private runner re-verifies preserved authorities
before loading; its own digest and adapter digest bind the execution. A separate
private verification receipt binds local checks, package inspection, installed
wheel tests, the draft PR head and hosted CI. These receipts and prediction
arrays remain outside Git. Only aggregate qualification findings are published.

Synthetic tests exercise both candidates and both repeat identities, nonzero
exact forward execution, RNG preservation, deterministic inference, wrong
candidate/checkpoint and pinned repeat associations, preprocessing failures,
tensor incompatibilities, invalid inputs, output overflow and weights-only
rejection without fallback. Original M0 synthetic and historical executions were
also rerun and compared exactly with their preserved private output arrays.
No rights declaration, scorer, scientific result, original v1.0.0 tag or release
artifact is changed. This qualification grants no checkpoint redistribution
permission and makes no new predictive-performance or production-readiness claim.

Local verification passed **508 pytest tests**, including **70 inference tests**
and **21 repository boundary tests**, plus Ruff lint/format and strict Pyright
with zero errors or warnings. A fresh environment installed the built wheel and
passed **181 projection, observation-builder and inference tests** outside the
checkout. Wheel and source archive entries were inspected against the public
file boundary and scanned for private artifact/source identities; both passed.
The existing Python CI workflow exercises these expanded inference tests in its
full suite and installed-wheel smoke; hosted results are bound to the PR head in
the private verification receipt.

## Final M1 integration qualification — 2026-10-27

An independent audit verified the original private M1 verification receipt, its
embedded execution receipt, all 55 bound evidence files and the checksum ledger.
Fresh execution rechecked the recovered source identity, complete final-repeat
set, checkpoint/config/result associations, repeat and seed identities, fitted
preprocessing, original validation splits, saved-prediction bytes and canonical
prediction bindings. Every preserved M1 synthetic and historical output array
was reproduced exactly. The original receipts and evidence were left unchanged;
the new audit and execution records remain private.

Both M1 repeats retain zero numerical difference from the original CPU source
on all 24 frozen synthetic observations and their separate 512-row historical
replays. The saved CUDA prediction comparisons retain the errors and predeclared
combined tolerances reported above; they are tolerance-based historical parity,
not bitwise cross-device reproduction. Query order, horizons and target order
were independently verified. No training, fitting, selection or scientific-score
recomputation ran.

M0's loader, predictor constructor and predict signatures match the base API.
Fresh M0 executions reproduced both repeats' original private synthetic and
historical arrays exactly. No M0 evidence, rights decision, scientific contract,
v1.0.0 tag or published release artifact was changed.

Final local qualification passed **508 pytest tests**, including **70 inference
tests** and **21 repository boundary tests**, Ruff lint/format and strict Pyright.
Fresh wheel/sdist inspection verified public payload boundaries and absence of
private source/artifact identities. The installed wheel passed **181 tests**
outside the checkout. Exact-head hosted results and release-identity checks are
recorded separately in the final private qualification receipt. Integration
readiness requires those checks to pass on the pushed documentation commit;
this historical report alone is not evidence of hosted status for a later head.

PR #17 remains subject to explicit merge approval. No merge, force-push,
checkpoint/scaler publication or release modification is authorized by this
qualification. Existing production-readiness and scientific limitations remain.

## Gate7 M2 recovered inference qualification — 2026-10-28

**READY_FOR_PRIVATE_GATE7_M2_INFERENCE_REVIEW** for the complete recovered final
repeat set, **M2-r0 and M2-r1**. The RES-545 final-weight inventory, checkpoint
manifest and usable-run registry independently agree on this set. Intermediate
and environment-qualification states were excluded. The preceding M0/M1 sections
remain historical records; the findings below describe the current M2 execution.

### Source-defined contract and safe implementation

Verified original model, extractor and training source define M2 as
Linear(39,64) → exact GELU → Linear(64,64) → exact GELU → Linear(64,2), with
**6,850 parameters**. There is no dropout, normalization, recurrence or embedding
in its forward path. All six state tensors must be finite float32:

| Tensor | Shape |
|---|---|
| `raw_deep.0.weight` | `(64, 39)` |
| `raw_deep.0.bias` | `(64,)` |
| `raw_deep.2.weight` | `(64, 64)` |
| `raw_deep.2.bias` | `(64,)` |
| `raw_deep.4.weight` | `(2, 64)` |
| `raw_deep.4.bias` | `(2,)` |

The original full preprocessing constructs raw `(N,39)`, history `(N,4,4)`,
horizon `(N,)` and basis `(N,5)` tensors. Independent source inspection established
that M2's forward uses only raw features. No additional builder contract is needed.
The adapter accepts the existing raw matrix in `GATE7_FEATURE_NAMES` order,
standardizes in float64 using the run's fitted raw mean/scale, then casts to
float32. Original fitting uses training-only mean and sample standard deviation
(`ddof=1`), replacing zero scales with one. No fitting or retraining ran.

Outputs are finite `(N,2)` innovations: relative mean concentric force (N/kg),
then relative concentric net impulse (m/s). Float32 network outputs are returned
as float64. The target transform is identity; evaluation cell scales and baseline
addition do not belong to this predictor.

With the optional `inference` extra installed, import `load_gate7_m2` and
`Gate7M2Predictor` from `model_reproduction.checkpoint_inference` under the
`cmj_recovery_dynamics` package. Supply explicit configuration/checkpoint paths,
independently verified `config_sha256`, `checkpoint_sha256`, and `repeat=0` or
`repeat=1`, then call `.predict(raw_features)`. This follows the M0/M1 API.
Private inventory/config/result/source association must be established before
supplying digest pins: hashes alone prove bytes, not provenance or pairing.

The loader checks candidate/repeat, width, feature and target ordering, fitted
preprocessing and output semantics. It rejects incompatible tensor names, shapes,
dtypes and nonfinite values. It deserializes only verified bytes using
`torch.load(..., map_location="cpu", weights_only=True)`, without unsafe fallback
or added globals. Execution uses evaluation mode and `torch.inference_mode()`.
M2's extra hidden layer and namespace remain distinct from M0/M1.

### Frozen synthetic source parity

The unchanged fixture contains 16 `training` observations followed by 8
`public_validation` observations, in the existing origin/H72/D7 order. These
partition names describe predictor-only synthetic inputs, not historical split
membership. Independent conversion into original-source records reproduced all
936 raw values exactly. The unmodified original predictor executed its complete
preprocessing path, and both fitted float32 raw tensors matched the adapter
exactly. Every output was finite `(24,2)`; repeated calls were exactly equal.

Before inference, source tolerance was fixed at `atol=1e-6`, `rtol=1e-5`, applied
as `abs(adapter-original) <= atol + rtol*abs(original)`.

| Repeat | Max absolute error | Max relative error | Source parity |
|---|---:|---:|---|
| M2-r0 | 0 | 0 | Pass, exactly equal |
| M2-r1 | 0 | 0 | Pass, exactly equal |

### Separate historical prediction replay

Each run-bound validation split contains **512 rows**. Before historical inference,
validation bytes matched the configuration's digest; participant cardinality,
training/validation participant separation, split role, query ordering, horizon
and target ordering verified. Saved prediction file checksums matched the ledger,
and canonical innovation digests matched result, registry and checkpoint manifest.
The configuration, result, final checkpoint, repeat, seed identity, original
source and canonical configuration digest were independently bound for each run.

Historical tolerance was separately predeclared at `atol=1e-5`, `rtol=1e-4`, using
the same elementwise combined rule. Original CPU source and adapter outputs were
exactly equal for both 512-row replays, with exact repeated adapter calls.
Against the saved CUDA-era predictions:

| Repeat | Max absolute error | Max relative error | Historical replay |
|---|---:|---:|---|
| M2-r0 | 1.9073486328125e-6 | 2.625571608819003e-4 | Pass, 512 rows |
| M2-r1 | 1.9073486328125e-6 | 4.186718942504574e-4 | Pass, 512 rows |

Relative error uses `abs(adapter-saved)/max(abs(saved), float64.tiny)`; its maximum
alone does not determine acceptance under the combined rule. This establishes
tolerance parity with saved cross-device predictions, not bitwise historical
reproducibility. Historical scores were not recomputed or reinterpreted.

Execution used Linux x86_64, Python 3.12, NumPy 2.5.3, PyTorch 2.14.1+cpu,
one CPU thread and deterministic algorithms. The private receipt retains complete
artifact/source identities, preprocessing digests, repeat associations, fixture
receipts, ordered prediction digests, errors, runtimes and reproduction commands.
Private sources, configurations, fitted values and prediction arrays remain
outside Git; no private fingerprints or machine locators are published here.

### Regression, packaging and limits

The complete suite passed **564 tests**, including **126 inference tests** and
**21 architecture/boundary tests**. Synthetic coverage checks all six M2 tensors,
nonzero multilayer execution, both repeats, deterministic inference, RNG
preservation, wrong candidate/repeat/pin associations, feature/target order,
invalid preprocessing, nonfinite inputs/weights, float32/output overflow and
weights-only rejection without fallback. Ruff lint and formatting passed; strict
Pyright reported zero diagnostics. Wheel and source-distribution builds passed.
Package inspection passed for both archives, including a private-identity and
machine-path scan. A fresh environment passed **237 installed-wheel tests** outside
the checkout. Actual M2 checkpoint execution was also repeated with the installed
wheel. The private verification receipt binds these checks and exact-final-commit
hosted CI results.

Fresh M0 and M1 original-source executions also replayed their synthetic and
historical inputs; every array matched the respective preserved private arrays
exactly. Existing public M0/M1 signatures and inference semantics are unchanged.

This qualifies private checkpoint inference for review. It does not establish
scientific validity, predictive accuracy, clinical applicability, production
readiness or checkpoint redistribution permission. No rights declarations,
scientific scores, original v1.0.0 tag or published artifacts changed.

## Final independent M2 integration qualification — 2026-10-28

The final qualification independently rechecked the preserved execution and
verification receipts against their evidence bytes, then re-executed both
original M2 repeats from verified, unmodified source. The recovery bundle,
complete final-repeat inventory, source tree, checkpoint/configuration/result
associations, six fitted float32 tensors, repeat-bound preprocessing, validation
split bytes and 512-row query/horizon/participant/target ordering all verified.
Original evidence was preserved; new receipts and arrays remain private.

The remaining construction finding is repaired: the loader now constructs only
the selected source-defined network. M0 remains 39→32→2, M1 remains 39→64→2,
and M2 remains 39→64→64→2. Focused regression coverage checks every constructed
linear layer for both repeats of all three candidates. Public APIs, weights-only
loading, fitted preprocessing, tensor validation and outputs are unchanged.

| Repeat | CPU source equality, 24 synthetic rows | CPU source equality, 512 historical rows | Saved CUDA predictions |
|---|---|---|---|
| M2-r0 | Exact | Exact | Pass, max absolute error 1.9073486328125e-6 |
| M2-r1 | Exact | Exact | Pass, max absolute error 1.9073486328125e-6 |

CPU comparisons require exact array equality. CUDA comparisons separately use the
previously declared elementwise tolerance `atol=1e-5`, `rtol=1e-4`; their maximum
relative errors remain those reported above. Deterministic repeated execution and
all preserved M2 output arrays match exactly. Fresh original-source and historical
M0/M1 replays also match all preserved arrays exactly; their public signatures and
prediction implementation are unchanged. No historical scientific score was
recomputed.

Final local qualification passed **570 pytest tests**, including **132 inference
tests** and **21 repository boundary tests** with adversarial path/secret cases.
Ruff lint and formatting passed; strict Pyright reported zero diagnostics.
Wheel/sdist builds and content inspection passed. Outside the checkout, the
installed-wheel environment passed **243 inference, projection and builder tests**
and reran both original M2 repeats with exact preserved-array equality. Private
qualification records bind the final commit, package identities and exact-head
GitHub CI results; these identities and machine locators are not published here.

This is private inference qualification only. Saved CUDA parity is tolerance
based; accuracy, clinical validity, out-of-distribution robustness, production
readiness and redistribution rights remain unestablished. Original v1.0.0 tag and
published release assets are preserved. No retraining, model selection, rights
change, force-push, merge or release publication is part of this qualification.


## Gate7 M3 recovered inference qualification — 2026-10-28

**READY_FOR_PRIVATE_GATE7_M3_INFERENCE_REVIEW**, for the complete independently
verified final set **M3-r0 and M3-r1**. This is the original Gate7 trained
candidate, distinct from the earlier scientific-reproduction milestone named M3.
Inventory, checkpoint manifest, usable-run registry, original seed derivation,
configuration and result records establish both final repeats. Intermediate and
environment-qualification checkpoints are excluded.

### Original architecture and state contract

The verified original model, extractor and training source establish **7,138
parameters**, with these branches:

- Raw: Linear(39,64) → exact GELU → Linear(64,64) → exact GELU → Dropout(0.10).
- History: a shared Linear(4,32) → exact GELU applied to each of four tokens.
  Concatenate the mean of all four encoded tokens with the latest encoded token.
- Concatenate the 64 raw and 64 history values, apply Dropout(0.10), then
  Linear(128,2). The same source-defined dropout module is used at both sites;
  dropout is disabled in evaluation mode.

There is no normalization, recurrence, embedding, attention, history mask or
padding. All eight checkpoint tensors must be finite float32:

| State key | Shape |
|---|---|
| `raw_backbone.0.weight` | `(64,39)` |
| `raw_backbone.0.bias` | `(64,)` |
| `raw_backbone.2.weight` | `(64,64)` |
| `raw_backbone.2.bias` | `(64,)` |
| `history_encoder.0.weight` | `(32,4)` |
| `history_encoder.0.bias` | `(32,)` |
| `head.weight` | `(2,128)` |
| `head.bias` | `(2,)` |

### Versioned history input and preprocessing

M3 consumes raw `(N,39)` in the existing `GATE7_FEATURE_NAMES` order and explicit
history `(N,4,4)`. The new `gate7_history_projection_v1` contract is bound to the
privately verified source by opaque authority **RES-546-M3-INPUT-AUTHORITY-01**.
`project_gate7_history_v1` reads existing typed `CampPredictionRow` observations:
it requires exactly four valid pre-origin assessments, sorts oldest to latest,
and reads the arithmetic trial summaries directly. It does not reconstruct
history from the raw matrix. The columns are:

| Column | Meaning | Unit |
|---|---|---|
| 0 | Time relative to prediction origin | h |
| 1 | Relative mean concentric force | N/kg |
| 2 | Relative concentric net impulse | m/s |
| 3 | Assessment depth | m |

No unavailable or masked assessment is filled, dropped or padded. The adapter
rejects masked arrays, nonfinite values, wrong shapes, nonchronological or
post-origin histories, and mispaired raw/history observation ordering. The
existing observation builder retains independently pinned origin and routine
metadata authority. Hashes establish bytes, not permission or truthful ingestion.

The original full preprocessor also constructs integer horizon `(N,)` and basis
`(N,5)` tensors. M3's forward does not consume them; its predictor accepts neither
as a separate argument. Horizon information already present in raw features
remains unchanged. No new horizon or basis builder is introduced.

Both consumed branches use their run-bound training-only means and sample
standard deviations (`ddof=1`, zero scales replaced with one). History statistics
are over the flattened training tokens, one mean and scale per column. Subtraction
and division occur in float64, followed by float32 conversion and execution.
No statistics were fitted or refitted during recovery.

Import `load_gate7_m3` and `Gate7M3Predictor` from
`cmj_recovery_dynamics.model_reproduction.checkpoint_inference` with the optional
`inference` extra installed. Supply explicit configuration/checkpoint paths,
independently associated SHA-256 pins and the verified repeat; call
`.predict(raw_features, history)`. The loader uses verified bytes and
`torch.load(..., map_location="cpu", weights_only=True)` exclusively. It validates
candidate/repeat, source-defined widths, dropout, feature/history/target order,
preprocessing and every state tensor. Inference preserves caller RNG state during
construction, uses evaluation mode and `torch.inference_mode()`, and rejects
nonfinite float32 preprocessing or outputs.

Outputs are `(N,2)` float64 representations of the original float32 innovations:
relative mean concentric force (N/kg), then relative concentric net impulse (m/s).
There is no inverse target scaling, cell-scale adjustment or baseline addition.

### Original trained-checkpoint execution and numerical parity

Before inference, the private harness verifies the recovery bundle, original
source bytes/tree, final checkpoint inventory, checkpoint/config/result digests,
canonical configuration digest, seed identities and repeat-bound preprocessing.
The unmodified original source executes its complete preprocessing and forward
path; its fitting and training functions are never invoked.

The frozen fixture supplies 16 training-named and 8 public-validation-named
synthetic observations. These are predictor-only fixture partitions, unrelated to
historical split membership. Both raw and history tensors, including the actual
float32 tensors entering the adapter, match original-source preprocessing exactly.
Source parity was predeclared at `atol=1e-6`, `rtol=1e-5`; exact array equality was
also required and achieved:

| Repeat | Synthetic output shape | Max absolute / relative error | Deterministic |
|---|---|---|---|
| M3-r0 | `(24,2)` | 0 / 0, exact | Yes |
| M3-r1 | `(24,2)` | 0 / 0, exact | Yes |

Each original run independently binds a **512-row, 128-participant** historical
validation split. The harness checks split bytes and role, participant counts and
train/validation separation, row/query order, horizons, target order and units,
saved prediction bytes and canonical innovation digest before replay. Historical
raw/history inputs and actual preprocessed model tensors match original source
exactly. CPU source and adapter outputs are exactly equal for both `(512,2)`
replays, with deterministic repeated inference.

Saved training-runtime CUDA predictions are compared separately using the
predeclared combined elementwise rule `abs(new-saved) <= 1e-5 + 1e-4*abs(saved)`:

| Repeat | Max absolute error | Max relative error | CUDA replay |
|---|---:|---:|---|
| M3-r0 | 2.384185791015625e-6 | 2.8760632446307496e-5 | Pass |
| M3-r1 | 1.1920928955078125e-6 | 3.515350363252871e-5 | Pass |

Relative error divides absolute error by the greater of absolute saved value and
float64 tiny. Its maximum alone does not define the combined-rule outcome.
No historical scientific score was recomputed.

### Regression, package qualification and limitations

Full pytest passed **652 tests**, including **214 inference tests** and **21
repository/architecture boundary tests**. Synthetic tests cover both repeats,
nonzero raw/history execution, pooling, every tensor, source-defined construction,
configuration/order/pin rejection, invalid preprocessing, unavailable history,
masks, nonfinite inputs/weights, float32/output overflow, RNG preservation and
weights-only rejection without fallback. M0/M1/M2 APIs and implementation remain
unchanged; fresh original-source executions match every preserved synthetic and
historical prediction array exactly for all six original repeats.

Ruff lint and formatting passed; strict Pyright reported zero diagnostics. Wheel
and sdist builds and content inspection passed, including private identity,
fitted-vector, restricted-row, secret and machine-path scans. Outside the checkout,
**325 installed-wheel tests** passed; both actual original M3 checkpoints also
execute through the installed wheel with exact source and preserved-array equality.
The Python CI workflow includes the new sequence-inference tests in its installed
wheel check. Exact-head hosted CI qualification is bound privately to the public
commit; no private artifact fingerprints or machine locators are published here.

The original v1.0.0 tag and all four published release asset identities are
unchanged. Existing rights decisions and evaluation contracts remain intact.
No retraining, fitting, model selection, score recomputation, checkpoint
redistribution, merge or package release is part of this recovery.

This qualifies historical private inference on the executed inputs. CPU equality
does not prove accuracy, clinical validity, out-of-distribution robustness or
production readiness. Saved CUDA parity is tolerance based, not bitwise
cross-device reproduction. Redistribution rights remain unestablished. Authorized
observations with all four valid assessments and independently paired artifact
pins remain required; no general missing-history behavior is claimed.

## Gate7 M5 recovery: CPU source qualified, historical CUDA blocked — 2026-10-29

**M5_CPU_SOURCE_QUALIFIED_CUDA_BLOCKED** for the complete final-repeat set
**M5-r0 and M5-r1**. CPU source recovery and saved-CUDA compatibility are separate
qualification axes. Both original CPU executions reproduce exactly; both saved
CUDA comparisons fail the unchanged elementwise rule. Full inference
qualification remains blocked. This result does not erase the CPU evidence or
claim historical CUDA equivalence.

M5 is based directly on integrated main. Blocked M4 PR #20 is neither merged nor
used as an implementation dependency; its findings and qualification requirements
are unchanged. M5's recurrent and horizon behavior was independently established
from authenticated original M5 source, configuration and checkpoint tensors.
No cloud execution or cloud-processing authorization is part of this work.

### Original authority and architecture

The private recovery bundle and Gate7 evidence ledger were checked before
loading. The checkpoint inventory, authoritative final-checkpoint manifest and
usable-run registry independently agree on both repeats. Original source Git
objects match the recovery source index and each run's recorded source tree.
Checkpoint bytes, configuration and result identities, canonical configuration
digests, original seed derivation and run-specific train-only fitted preprocessing
are bound together in private receipts. The opaque public review reference is
`RES-546-M5-INPUT-AUTHORITY-01`; source locators and full digests remain private.

The original M5 network has **10,658 trainable parameters**, all float32:

| Component | Exact source behavior |
|---|---|
| Raw backbone | Linear 39→64, exact GELU, Linear 64→64, exact GELU |
| History | Four chronological tokens, each with four features; GRU input 4, hidden 32, one unidirectional layer, batch first, biases enabled, implicit zero hidden state |
| History pooling | Concatenate mean over all four GRU output tokens and latest output token: 64 values |
| Separate horizon | Embedding with two entries of width 8; H72=0, D7=1 |
| Head | Concatenate raw 64, pooled history 64 and horizon 8, then Linear 136→2 |
| Dropout | Source dropout probability 0.10, disabled by evaluation mode; GRU dropout 0 |
| Output | Innovations in force then impulse order; no inverse target scaling or baseline addition |

There is no attention, masking, padding, bidirectionality, learned normalization,
or basis projection in M5. The original preprocessing constructs a five-column
basis tensor, but the M5 forward does not consume it. Independently changing that
unused original argument leaves the predictions exactly unchanged.

The exact state contract is:

| Tensor | Shape |
|---|---|
| `raw_backbone.0.weight`, `.bias` | `(64,39)`, `(64,)` |
| `raw_backbone.2.weight`, `.bias` | `(64,64)`, `(64,)` |
| `history_gru.weight_ih_l0`, `.weight_hh_l0` | `(96,4)`, `(96,32)` |
| `history_gru.bias_ih_l0`, `.bias_hh_l0` | `(96,)`, `(96,)` |
| `horizon_embedding.weight` | `(2,8)` |
| `head.weight`, `.bias` | `(2,136)`, `(2,)` |

### Public input and loading contract

Import `load_gate7_m5` and `Gate7M5Predictor` directly from the optional
`model_reproduction.checkpoint_inference` module. No checkpoint is bundled,
discovered or loaded at package import. Independently establish the exact
candidate/repeat/configuration/checkpoint association, then supply both byte
SHA-256 pins and the original repeat to the loader. Pins authenticate bytes;
they do not establish ownership, source authority or pair association by
themselves. Weights-only CPU loading has no unsafe fallback.

`predict(features, history, horizon)` requires:

- Finite unstandardized raw features `(N,39)` in `gate7_feature_projection_v1` order.
- Finite unstandardized history `(N,4,4)` in `gate7_history_projection_v1` order:
  hours relative to origin, force N/kg, impulse m/s, depth m. All assessments
  are pre-origin and chronological; their flattened values must exactly match
  raw columns 7–22. No masks, padding or missing-history imputation are accepted.
- An explicit int64 horizon vector `(N,)`, H72=0 and D7=1. Its indices must agree
  with the raw H72/D7 indicator columns. Float, boolean, masked, out-of-range
  and mispaired horizon inputs are rejected. No separate basis argument is
  accepted because that branch is unused by the original M5 forward.

Raw and history values are standardized with their independently associated
original train-only means and scales in float64, then cast to float32 exactly
as the source does. Original fitting uses training observations only and sample
standard deviations, replacing zero scales with one. This recovery loads those
preserved statistics; it does not refit them. Horizon indices are not normalized.
The output is finite float64 `(N,2)` containing the source's float32 predictions
in the original target order. Existing M0–M3 APIs and implementation bodies are
unchanged. Mathematical agreement among input branches is not origin authority;
callers still need authenticated observations and separately verified artifact
associations.

### Axis A: CPU_SOURCE_PARITY — PASS

The adapter and the unmodified original CPU source executed independently for
each repeat on the existing 24-row synthetic fixture and the actual 512-row
historical validation split. Every consumed forward tensor matched exactly:
float32 raw `(N,39)`, float32 history `(N,4,4)` and int64 horizon `(N,)`.
Original four-argument source calls also recorded the unused basis branch.
GRU output sequences and final hidden states matched exactly. Dropout was off,
outputs were finite and deterministic repetition was exact.

| Repeat | Synthetic CPU source max abs / relative error | Historical CPU source max abs / relative error |
|---|---|---|
| M5-r0 | 0 / 0; `(24,2)` | 0 / 0; `(512,2)` |
| M5-r1 | 0 / 0; `(24,2)` | 0 / 0; `(512,2)` |

The first CPU output arrays were preserved separately. Fresh executions,
including an isolated PyTorch 2.11.0 CPU environment and the installed wheel,
reproduced those arrays exactly. These checks establish source reproduction on
the executed observations, not new predictive-performance evidence.

Historical validation bytes matched their run-bound source/configuration
identities. Training and validation participant groups were disjoint; validation
contained 512 rows from 128 participant groups. Query uniqueness/order, horizon
order and target order matched the original saved predictions. Both saved file
byte checksums and canonical innovation digests matched the ledger, result,
registry and final-checkpoint manifest before numerical comparison. No historical
scientific scores were recomputed.

### Axis B: HISTORICAL_CUDA_COMPATIBILITY — BLOCKED

The rule was fixed before execution:
`abs(replayed - saved) <= 1e-5 + 1e-4 * abs(saved)`.
CPU source equality does not replace this separate historical check.

| Repeat | Max absolute error | Max relative error | Failing elements |
|---|---:|---:|---:|
| M5-r0 | 0.0003714561462402344 | 0.8963192561022859 | 443 / 1024 |
| M5-r1 | 0.0002703666687011719 | 0.08694005544530457 | 206 / 1024 |

Relative error is `abs(replayed-saved) / max(abs(saved), float64.tiny)`;
near-zero reference predictions can make relative error large. Acceptance uses
the fixed combined elementwise rule, not either maximum alone. No tolerance was
changed after observing these errors.

The principal replay used Python 3.12.13, NumPy 2.5.3, PyTorch 2.14.1+cpu,
one CPU thread, deterministic algorithms, float32 inference and no autocast.
A separate PyTorch 2.11.0+cpu replay produced exactly the same CPU arrays and
historical discrepancies. The preserved original result records CUDA inference
with PyTorch 2.11.0+cu128 on an RTX 5090. A matching torch version on CPU is not
the historical CUDA backend; no NVIDIA execution or cuDNN parity is claimed
here. The source, checkpoint and preprocessing findings do not establish the
cause of this discrepancy. It remains a numerical qualification blocker, separate
from M4's unresolved result.

### Regression and review evidence

All eight previously qualified M0–M3 final repeats were re-executed privately.
Their synthetic and historical outputs matched the preserved arrays exactly;
all retained their original-source parity and saved-CUDA tolerance passes. An AST
comparison also confirmed every integrated M0–M3 function/class body is unchanged.

Local verification passed **732 tests**, including **294 inference tests** and
**21 repository boundary tests**, Ruff lint/format and strict Pyright with zero
errors or warnings. The built wheel passed **405 projection, observation-builder
and inference tests** outside the checkout; real original M5 checkpoint execution
was also repeated through the installed package. Public tests use synthetic
parameters only and check the GRU gate equations, all three consumed branches,
state/configuration/input contracts, pinned-repeat separation, overflow and safe
weights-only rejection. CI includes the M5 tests in both the full suite and
installed-wheel checks. Wheel/sdist payload and private-identity boundary audits
are recorded privately, as are exact-head hosted checks.

Private execution and verification receipts retain the original identities,
seed/config/source associations, actual tensor digests, preserved CPU arrays,
per-repeat numerical evidence, backend limitations, regressions, package identities
and CI bindings. Only sanitized aggregate findings are public. No checkpoint,
fitted vector, participant metadata, historical observations/predictions, source
archive or private digest is published. The original v1.0.0 release identities,
rights declarations and scientific scores remain unchanged. The draft M5 PR is
reviewable as CPU source recovery while full inference qualification remains
CUDA-blocked; it is not a request to merge or publish a release.
