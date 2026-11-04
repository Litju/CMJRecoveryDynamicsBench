# RES-546 Gate7 M0/M1/M2/M3/M4 inference verification

The current M4 findings appear under **Gate7 M4 recovered inference — blocked
CUDA qualification** below. Earlier M0/M1/M2/M3 sections retain historical
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


## Gate7 M4 recovered inference — blocked CUDA qualification

**M4_INFERENCE_BLOCKED** — 2026-10-29. The complete original final set is
**M4-r0 and M4-r1**, independently identified from the preserved final-weight
inventory, authoritative checkpoint manifest and usable-run registry. Both
checkpoints execute safely and reproduce unmodified original CPU source exactly.
Both fail the separately predeclared saved-CUDA numerical compatibility gate.
This draft recovery must not be treated as integration qualification.

### Original source architecture and state

Opaque authority **RES-546-M4-INFERENCE-AUTHORITY-01** binds the original model,
extractor, training implementation and artifact associations privately. Original
source and both checkpoints establish **10,626 parameters**:

- Raw backbone: Linear(39,64) → exact GELU → Linear(64,64) → exact GELU.
- History: `GRU(4,32,num_layers=1,batch_first=True)`, unidirectional, with biases,
  implicit zero initial hidden state and zero internal GRU dropout. It uses the
  standard PyTorch reset/update/new gate layout and sigmoid/tanh operations.
- Concatenate mean over all four GRU output tokens with the latest output token,
  yielding 64 history values. Concatenate these with the 64 raw values, then
  Linear(128,2).
- The source's Dropout(0.10) is applied after the raw backbone and after combined
  features; it is disabled in evaluation mode. No normalization, embedding,
  masking, sequence packing, padding or imputation is present.

All ten checkpoint tensors must be finite float32:

| State key | Shape |
|---|---|
| `raw_backbone.0.weight` | `(64,39)` |
| `raw_backbone.0.bias` | `(64,)` |
| `raw_backbone.2.weight` | `(64,64)` |
| `raw_backbone.2.bias` | `(64,)` |
| `history_gru.weight_ih_l0` | `(96,4)` |
| `history_gru.weight_hh_l0` | `(96,32)` |
| `history_gru.bias_ih_l0` | `(96,)` |
| `history_gru.bias_hh_l0` | `(96,)` |
| `head.weight` | `(2,128)` |
| `head.bias` | `(2,)` |

M4 has its own explicit model, predictor and loader; M0–M3 implementation,
preprocessing and public signatures remain unchanged.

### Input, preprocessing and output authority

The original M4 forward consumes raw `(N,39)` in `GATE7_FEATURE_NAMES` order and
history `(N,4,4)`. The existing `gate7_history_projection_v1` reads four valid,
chronological, strictly pre-origin typed assessments directly. Its columns are
relative time (h), relative mean concentric force (N/kg), relative concentric net
impulse (m/s) and depth (m). Original trial-summary aggregation and duplicated
raw/history information agree exactly. Numerical agreement is a consistency check,
not authorization: the independently pinned observation builder remains responsible
for origin availability and authorized ingestion.

The original full preprocessor also constructs horizon `(N,)` and basis `(N,5)`;
M4 does not consume these as separate branches. No additional input builder is
needed. No history is reconstructed from raw features or invented for missing data.

Both consumed branches use their original run-bound train-only fitted statistics.
History statistics are over flattened training tokens. Original fitting uses
sample standard deviation (`ddof=1`), replacing zero scales with one. Recovery
performs no fitting: it applies float64 subtraction/division using pinned values,
then casts to float32. Outputs are finite `(N,2)` float64 representations of
float32 innovations, ordered force (N/kg), then impulse (m/s). There is no target
rescaling, cell-scale adjustment or baseline addition.

With the optional inference extra, import `load_gate7_m4` / `Gate7M4Predictor`
from `cmj_recovery_dynamics.model_reproduction.checkpoint_inference`. The loader
requires explicit configuration/checkpoint paths, independently associated SHA-256
pins and repeat identity. It checks the M4 architecture/configuration, feature and
history ordering, preprocessing and every tensor before verified-byte
`torch.load(..., map_location="cpu", weights_only=True)`, without unsafe fallback.
Call `.predict(raw_features, history)`. Construction preserves caller RNG state;
execution uses evaluation mode and `torch.inference_mode()`.

### Independent original-checkpoint executions

Before each execution, the harness authenticates recovery and Gate7 ledgers,
original source/tree, inventory, configuration/result/checkpoint associations,
canonical configuration digest, original seed derivation and preprocessing pins.
Both source and adapter load exactly the original trained tensors.

The unchanged synthetic fixture contains 24 observations, with legitimate typed
raw and history inputs. Both actual preprocessed forward inputs and intermediate
GRU sequence `(N,4,32)` and final hidden `(1,N,32)` outputs match original source
exactly. The source comparison requires exact equality, stronger than the preceding
`atol=1e-6, rtol=1e-5` source precedent.

Each original M4 run independently binds a **512-row, 128-participant** historical
validation split. Split byte identities, train/validation participant separation,
row/query ordering, horizons, target order/units, saved prediction bytes and
canonical innovation digests all verify before replay.

| Repeat | Synthetic CPU source, `(24,2)` | Historical CPU source, `(512,2)` | Repeated inference |
|---|---|---|---|
| M4-r0 | Exact, zero error | Exact, zero error | Exact |
| M4-r1 | Exact, zero error | Exact, zero error | Exact |

### Saved CUDA prediction incompatibility

Before predictions, CUDA compatibility was fixed at the existing combined rule:
`abs(replayed-saved) <= 1e-5 + 1e-4*abs(saved)`. It was not widened after observing
failures. Compared with the preserved CUDA-era innovations:

| Repeat | Max absolute error | Max relative error | Failing elements / 1024 | Result |
|---|---:|---:|---:|---|
| M4-r0 | 0.00047588348388671875 | 0.0485345624100217 | 254 | Fail |
| M4-r1 | 0.00032639503479003906 | 0.02698545132189602 | 146 | Fail |

Relative error divides by `max(abs(saved), float64.tiny)`; acceptance uses the
combined elementwise rule, not the relative-error maximum alone. Maximum error
relative to the allowed elementwise error is approximately 25.51 for r0 and 13.27
for r1. Saved prediction identities are verified; their numerical agreement fails.
Historical scientific scores were not recomputed.

The discrepancy persists with both PyTorch 2.14.1+cpu and 2.11.0+cpu. Both CPU
versions reproduce the unmodified original source exactly and yield the same
reported CUDA error aggregates. The original recorded training-runtime predictor
used PyTorch 2.11.0+cu128. CUDA hardware is unavailable in the recovery environment;
the historical backend cause remains unresolved. No backend equivalence or
alternate tolerance acceptance is claimed.

### Engineering qualification and limits

Engineering checks passed **738 pytest tests**, including **300 inference tests**
and **21 repository boundary tests**. Shared synthetic tests now cover M3 and M4,
including independent GRU gate equations, zero initial state, source-defined
construction, tensor/configuration/order/pin rejection, determinism, masks,
nonfinite inputs/weights, overflow and weights-only deserialization rejection.
All eight previously qualified M0–M3 repeats reproduce their original CPU source
and preserved synthetic/historical arrays exactly; their existing definitions and
public signatures are unchanged.

Ruff lint and formatting, strict Pyright with zero diagnostics, wheel/sdist builds
and package-content inspection passed. Outside checkout, **411 installed-wheel
tests** passed, and both real M4 checkpoints executed through the installed wheel.
Installed execution retains exact CPU source and forward-input parity and repeats
the saved-CUDA incompatibility. Exact-head push/PR engineering CI identities and
results are bound privately to the public commit. Engineering CI success does not
remove this historical numerical blocker.

Private receipts retain source and artifact identities, seed/configuration and
preprocessing bindings, dataset and prediction digests, per-repeat measurements,
runtime investigation, package identities and CI results. Private sources, fitted
vectors, checkpoints, restricted rows, machine locators and per-row arrays remain
outside Git and built packages. Original v1.0.0 tag and all published release asset
identities remain unchanged; existing rights and evaluation definitions are intact.

This is partial historical CPU inference recovery. Saved CUDA compatibility remains
blocked and must be independently resolved before qualification. CPU equality on
executed observations establishes neither predictive accuracy, clinical validity,
OOD robustness, production readiness nor redistribution permission. No retraining,
refitting, selection, score recomputation, checkpoint redistribution, merge,
force-push or package release is part of this work.
