# RES-546 execution plan

## Objective

Integrate only rights-cleared model metadata or inference code into
CMJRecoveryDynamicsBench. Keep all recovered checkpoints, parameter files, raw
predictions, source snapshots, and protected evaluation records outside the
public tree. The dated owner attestation resolves first-party ownership and
publication authority for the historical Preseason model families identified in
the RES-545 rights registry. This plan does not release checkpoint bytes or
extend Apache-2.0 to weights or datasets.

## Entry gates

1. **Ownership:** Gate7 M0-M8, Gate5 OLS, P8L6, and the matched historical
   Preseason model families have owner-attested first-party provenance. Do not
   require third-party permission for those owner-controlled artifacts. SP07 C1
   remains private because its author/task identity is not matched to the
   attestation; G3/G4 attack-study artifacts remain outside its scope.
2. **Distribution terms:** no public license has been assigned to recovered
   weights or fitted parameters. Apache-2.0 covers original repository
   software only. Adding any recovered model bytes requires an explicit
   owner-selected distribution license and an artifact-specific release
   decision; this is separate from the resolved ownership review.
3. **Input contract:** define and validate a public 39-feature projection for
   the Gate7 task. The current public initial-preseason row surface does not
   provide it. Do not infer missing columns or reuse hidden fields.
4. **Dataset identity:** preserve Gate7's public fixture identity separately
   from the OLS/P8L6 training-data identity. The OLS comparator can be replayed
   on the Gate7 evaluation split, but its fit data are not a matched Gate7
   training split.
5. **Evaluation authority:** publish a numeric result only after the
   evaluation data, result-summary rights, and scoring contract are cleared.
   P8L6 has no validation score to publish or replay.
6. **Technical qualification:** treat safe loading, source inference, score
   replay, and release readiness as separate statuses. Pickle/joblib remain
   unopened; G4 remains safely rejected without fallback. White-derived
   empirical material and confidential third-party data keep their existing
   restrictions.

The owner-rights gate is complete for the attested families. RES-546 now adds
source-verified feature projection software. It still does not add a recovered
checkpoint adapter or inference path; dataset, evaluation, technical, and
distribution-term gates for each model artifact remain separate.

## Planned integration

1. Add a separately namespaced Gate7 lineage record using the repository's
   existing typed model and checkpoint contracts. Keep it distinct from the
   existing initial-preseason M0 identity.
2. Record owner authority, license terms, actual release, inference, and
   score-replay statuses separately. Keep checkpoint digests and source
   locators in the private evidence record; do not put them in the public
   registry.
3. If the OLS evaluation data and result authority are available and its
   distribution terms are recorded, implement the adapter against the
   repository's existing feature and baseline helpers. Do not copy original
   task source or publish its JSON parameters without an explicit release
   decision.
4. Keep P8L6 out of the 39-feature path. A future integration would need its
   own 82-field schema, preprocessing contract, reconciled seed training
   contracts, and authorized evaluation.
5. Use the existing four-cell scorer only after the public feature projection
   and exact evaluation identity are established. Keep the Gate7 comparator
   distinct from a native historical OLS replay.

## Separate synthetic fallback

If technical compatibility, data identity, or result-summary restrictions
block historical integration, register a new synthetic study under a new
RES-546 study identity. This is a planning fallback, not a substitute
reproduction, and no rows or models were created in RES-545.

- Use the repository's public synthetic generator and freeze a new feature
  schema, target units/order, generator version, and deterministic split roots.
- Split by participant/group so no group crosses train, validation, and test.
- Fit preprocessing on training data only. Use the existing H72/D7 and
  force/impulse cell definitions only if the new generator supplies them
  without reconstructing withheld fields.
- Compare a declared public baseline and any newly authorized clean-room model
  only on the same generated split. Register source/config/data identities and
  scoring outputs before interpreting results.
- Keep any new weights private unless their own publication authority and
  distribution terms are recorded. Do not label the study a Gate7 or P8L6
  replay.

## Completion criteria

- Rights decisions cover every artifact or output proposed for public use.
- The public input/output adapter matches a versioned schema and unit contract.
- Safe loading and finite inference pass on authorized public rows.
- The scorer reproduces its registered results on the exact identified split.
- No private checkpoint, unsafe serialized estimator, raw result packet, or
  protected dataset enters the repository or release artifacts.
- The v1.0.0 release remains unchanged.

## RES-546 Gate7 feature projection V1 implementation status

**Projection outcome: `READY_FOR_GATE7_FULL_PROJECTION_REVIEW`.** The original feature
builder and its caller chain are recovered. `solution/train.py` and inference
call `Preprocessor.fit` or `Preprocessor.transform`, which call
`baselines.common.feature_matrix` and `feature_vector`. The ordered names match
the Gate7 M0 configuration and the versioned public data contract. The typed
contract keeps `gate7_m0_candidate` distinct from the initial-preseason public
M0.

The source-exact raw projection is implemented in
`cmj_recovery_dynamics.model_reproduction.gate7_projection`. It returns a
finite float64 matrix of shape `(N, 39)` and was differentially checked against
the recovered extractor on independent synthetic H72 and D7 rows. The tests
also cover stable ordering ties, invalid and missing fields, plan padding,
duration units, category one-hot order, reproducibility, and future-information
injection.

The recovered rules are:

- Sort the four history assessments by ascending `time_from_origin_hours` and
  copy time, force, impulse, and depth. The extractor does not filter on
  `validity_state`. All required values must convert to finite numbers; history
  is never padded or imputed.
- Sort history exposures by time and require exactly one. Copy its time and
  `duration_minutes` directly. Copy index-exposure time and duration directly.
  Duration values remain in minutes; the projection does not divide by the
  exposure normalization reference.
- Sort the query-specific known plan by time and accept exactly two or three
  records. With two records, only slot 2 is filled with zero time and duration.
  The source public plan includes the index event at time zero, so the Camp-row
  adapter prepends that event before sorting.
- Copy `routine_assessment.scheduled` as 0.0 or 1.0, then encode the five
  availability categories in the frozen feature order. The L05-R01 final
  public generator assigns one origin-keyed state independently of target
  values and copies it unchanged to H72 and D7 queries. This source state is
  available at origin in the synthetic Gate7 fixture. The prospective
  projection verifies this metadata against an application-pinned origin source
  and rejects unresolved, conflicting, mismatched, or post-origin state.
- Raw projection values use float64. M0 fits raw means and sample standard
  deviations (`ddof=1`) on training rows only, replaces zero scales with 1.0,
  applies `(x - mean) / scale`, then casts model tensors to float32. Fitted
  means and scales are not included.

`project_gate7_historical_v1` reproduces the raw historical transformation
without temporal filtering. `project_gate7_v1` adapts the public
`CampPredictionRow` plus an explicit `Gate7RoutineAssessment`, checks
prediction-origin availability, and returns a full matrix only when the row
contains exactly four usable assessment summaries and one prior exposure.
Missing or invalid inputs return machine-readable blockers; no values are
invented. The base `CampPredictionRow` has no routine-assessment field, so a
caller must provide that origin-keyed public metadata through the typed
wrapper and a separately trusted `Gate7RoutineSource`. An enum alone does not
establish authority. The current clean-room sample generator can produce rows that fail
the Gate7 cardinality checks; those rows remain blocked.

This establishes the feature projection for review. It does not load a
checkpoint, claim model inference, publish fitted preprocessing values, alter
historical scores, or change v1.0.0. No checkpoint, raw training row, private
source path, or private identifier is in the public diff.

The next integration step is to wire the origin-keyed routine state and
source-compatible assessment/exposure shape into the public observation
builder. Checkpoint distribution terms and model inference remain separate
review gates.


## Independent-review repairs and sanitized verification receipt

F1 is repaired by binding each `Gate7RoutineAssessment` to `origin_id`, the
source payload SHA-256, and the time the metadata became available relative to
origin. `Gate7RoutineSource` accepts immutable JSON bytes and verifies them
against an independently trusted digest. Its record format is an array of
`[origin_id, scheduled_boolean, registered_state, available_at_origin_hours]`
arrays. It rejects duplicate origins, malformed records, nonfinite availability
times, and unregistered categories. No production origin records are supplied
or inferred by this change.

The application must obtain the expected digest from its authoritative ingestion
process, outside prediction requests, then retain the same source across H72/D7
queries and separate projection calls. Every supplied routine assessment must
exactly match its unique source record and prediction origin; availability must
be at or before origin. No source means no prospective authority. A caller's enum,
hash, or assertion alone cannot pass. A digest verifies source identity, not the
truth of arbitrary data: allowing a request to replace both payload and trusted
digest would violate this ingestion boundary. Source replacement/versioning is
an application authority decision; there is no claim of global consistency
between independently configured authorities. This enforces cross-call
consistency through authoritative origin records, rather than batch-local memory.
The historical extractor remains independent of these checks.

F2 is repaired only in the prospective adapter. Inspection and execution of the
preserved extractor confirm that it reads raw numeric `duration_minutes` from
history, index, and plan records. It does not read `ExposureComponent`, component
masks, `contribution`, units labels, or normalization. The historical projection
therefore continues to copy raw minutes. In contrast, the prospective Camp
adapter requires exactly one observed, unmasked component explicitly labelled
`minutes`. A masked component has `contribution=None`, so its value is not usable
as prospective evidence. The adapter rejects it instead of assuming zero or
using a suppressed value. Accepted duration remains raw minutes, not normalized
contribution. Tests cover observed/unobserved/masked values in all three positions,
malformed values, duplicate components, and incorrect unit labels.

F3 was re-executed against the unmodified preserved original `feature_vector`.
The public harness `tests/verify_feature_projection.py` builds independent
synthetic dictionaries directly from literals, independently adapts those inputs
to the public typed surface, checks feature names, and compares every column.
It does not use the earlier golden vectors, load checkpoints, read historical
datasets, train models, or calculate scores. Its assert-based invalid-input
checks require both extractors to reject each malformed fixture.

To reproduce with authorized access to the original source, run from this
checkout with the project environment:

```sh
PYTHONPATH=src python tests/verify_feature_projection.py \
  --original-source "$AUTHORIZED_ORIGINAL_SOURCE" \
  --source-sha256-file "$PRIVATE_AUTHORITY_SHA256_FILE"
```

The harness requires the exact source-module SHA-256 from the independently
verified private recovery index and fails on a mismatch. Supply that digest in a
private text file; neither its value nor its path enters the public receipt. The original source is intentionally excluded from public Git and
release artifacts; a public checkout alone cannot execute that private half of
the comparison. The fixture construction, comparison logic, source identity,
and sanitized observed results are public and independently rerunnable by an
authorized reviewer. This receipt attests an actual local execution, not a
surrogate or a comparison to copied goldens.

```json
{
  "source_contract": "gate7_feature_projection_v1",
  "model_identity": "gate7_m0_candidate",
  "source_authority": "RES-546-EXTRACTOR-AUTHORITY-01",
  "fixture_identity": "independent_synthetic_projection_v1",
  "fixture_sha256": "7dd45f9e9c2111a0b9b4596aa5af6620ca07fd7dcaf2c4c7e4c0735f47dfa60a",
  "method": "unmodified original feature_vector versus public historical projection",
  "column_count": 39,
  "valid_vectors": 20,
  "column_comparisons": 780,
  "invalid_vectors_rejected_by_both": 15,
  "absolute_tolerance": 0.0,
  "relative_tolerance": 0.0,
  "max_absolute_difference": 0.0,
  "coverage": [
    "H72/D7",
    "stable assessment and plan ties",
    "two-plan zero padding",
    "three-plan preservation",
    "all five routine states",
    "raw minute durations",
    "missing records",
    "null/nonnumeric/nonfinite durations"
  ],
  "result": "PASS"
}
```

The Python CI workflow runs full pytest (including architecture boundaries),
Ruff, strict Pyright, a wheel/sdist build, and installed-wheel projection tests
outside the checkout. The private-source differential harness is deliberately
not run by public GitHub CI. Review readiness and CI outcomes are reported for
the atomic repair commit; no approval or merge is implied by these checks.

## Public observation builder v1

The separately versioned `cmj_recovery_dynamics.observations.public_builder`
module implements `gate7_public_observation_v1`. It leaves the historical camp
generator, dataset identities, raw historical projection, scores, rights records,
and official v1.0.0 artifacts unchanged. The package version remains unchanged;
a review-branch build is not a replacement official release artifact.

`Gate7OriginObservation` is a complete, label-free origin snapshot. It requires
four distinct valid pre-origin assessments, each with exactly three criterion
trials. Force is in N/kg, net impulse in m/s, and depth in meters; all are finite
and positive. Assessment summaries are arithmetic trial means. The existing
`select_camp_baseline` takes the two latest valid assessment means in the inclusive
24–240 hour window. No historical assessments are modified, padded or discarded
to meet this contract.

Exactly one prior exposure, an index event at zero, and two origin-known plan
events at 48 and 120 hours are required. Each event carries exactly one observed,
unmasked public `duration_minutes` component labelled `minutes`; its raw
nonnegative value is used without dividing by its normalization reference.
The snapshot's `available_at_origin_hours` is the time its last datum became
known, including all trial measurements and plan details. It must be finite,
no later than zero, and no earlier than any historical assessment/exposure.
This field is an ingestion authority assertion, not a timestamp inferred from
an outcome. Realized future durations or retrospective validity decisions must
never be entered as origin-known observations. Plan durations are the declared
plan measurements at origin, not later realized event measurements.

### Independent public ingestion and pinned authority

An application obtains independently authorized public observations and routine
metadata before prediction. It builds typed `AssessmentObservation`,
`CriterionTrial`, `CampExposure`, and `PlannedExposure` values and submits the
seven exact fields of `Gate7OriginObservation` through
`gate7_origin_from_mapping`. This is a typed ingestion API, not a JSON decoder.
Unknown or missing fields, including labels and future target assessments, fail
closed. Nested records require the registered concrete types; trial counts,
availability states, times, units and masks are checked without imputation.

The authority canonicalizes origins with
`gate7_observation_payload_v1(source_identity, origins)` and independently pins
its SHA-256. The UTF-8 payload binds the schema, independently named source,
participant grouping, all observation fields and origin identity. JSON uses
sorted object keys, compact separators, ASCII escaping and no NaN; origins are
ordered by origin id, and submitted history/trial arrays retain their order.
It separately pins a `Gate7RoutineSource` payload and SHA-256 using the existing
four-field origin-record format. Exactly the same origin set is required in
both sources. Routine flags must be consistent with their registered category,
and availability must be no later than origin.

Configure `Gate7ObservationBuilderV1(source_identity, origins,
expected_observations_sha256, routine_source)` once outside prediction requests.
Retain that immutable builder and source for both horizons and subsequent calls.
`build(origin_id, horizon, target_time_hours=None)` accepts only an existing
origin and a registered query. It cannot accept replacement source data or
routine metadata. Pinning proves byte identity, not truth or authorization:
constructing an entirely new builder with new trusted digests is an explicit
application authority change, outside this request API. There is no global
registry across independently configured applications.

The builder returns the existing `Gate7CampPredictionInput`. It derives the
baseline, orders assessments, and projects the complete known plan through the
query time: H72 gets the 48-hour plan event, D7 gets both events. The existing
projection adapter includes the index in the plan slots and zero-pads the final
H72 plan slot, as required by the recovered extractor. Routine records and
all other origin observations stay identical across horizons and calls.
`project_gate7_v1((builder.build(origin_id, horizon),),
routine_source=builder.routine_source)` executes the existing projection contract.
`builder.inputs()` orders origin ids ascending, then H72 before D7;
`builder.matrix()` returns finite float64 `(N, 39)` values in the existing frozen
feature order and units, without scaling or inference.

### Distinct synthetic fixture and reproduction

Run the complete pipeline and print its verification receipts with:

```sh
python -m cmj_recovery_dynamics.observations.public_builder
```

Or obtain a matrix directly:

```python
from cmj_recovery_dynamics.observations.public_builder import generate_gate7_fixture_v1

builder = generate_gate7_fixture_v1("training")
matrix = builder.matrix()  # float64, (16, 39)
```

Generator `oss_gate7_observation_fixture_v1`, dataset
`oss_gate7_observation_integration_v1`, and seed `20261024` are new OSS
identities. Split names are `training` and `public_validation`, with four and
two participants respectively, two origins per participant, and two horizons
per origin. Split-qualified SHA-256 participant keys keep groups disjoint;
grouping keys never enter the 39 predictors. Draws use SHA-256 of generator,
seed and semantic keys, first eight bytes as a big-endian integer divided by
2**64, affine scaling and rounding to nine decimal places. Participant, origin,
session, trial, duration and routine keys are distinct. Session deviations are
shared within each three-trial assessment; trial errors use independent semantic
keys. Routine state depends only on its origin key and never on a target.
Fixture history is at -240, -72, -48 and -24 hours; prior exposure is at -96.
These schedules match the recovered L05-R01 public shape.

This predictor-only integration fixture does not simulate a calibrated response
law, provide labels, or establish athlete performance. Its numerical ranges and
seed are new conventions. Shape/units and extractor compatibility do not mean
exact replay of Gate7 training/validation membership, measurements, generator
randomness, fitted preprocessing, or scores. Historical dataset authorities
remain separate; the existing clean-room camp sample is not silently adapted.

Frozen source and output SHA-256 values:

| Split | Origin observations | Routine source | Matrix |
| --- | --- | --- | --- |
| training | `cc9df5158b4ccd3100f42588a69ca79a4e0f04ed5685f2dddf76f80a94d354cf` | `60f813fcc98bca2444c28ab94e07c74f042b5661e176fa5d7482399c586b5eed` | `3404bd1c6c2988a76b33cebbeb40de9a5152f0881a5182d47a4248e3a213c8a6` |
| public_validation | `979adc14bf17250dfaf38061e2ff1c962ad95a27da13692d4f612f62ef594726` | `7fb7915f3d8e88e6487b9713ed759d9ada82cedb71763f78bfff040c8216c25b` | `2d236629413f250697a6f21df66ff04bec56a6e8ddc760ae49c63d2dc6a6e147` |

Matrix hashes use little-endian float64 bytes in C order. Shapes are `(16, 39)`
and `(8, 39)`. Tests pin these six hashes, verify every column against independent
literal H72/D7 vectors, cover all five routine categories, and test temporal
leakage, source replacement, cardinalities, invalid trials, durations and group
isolation. The original extractor identified privately by the opaque authority
`RES-546-EXTRACTOR-AUTHORITY-01`
was also executed privately on the 24 new fixture rows: every column was exactly
equal. Only synthetic inputs were used; no recovered data or source is published.

Local verification: full pytest **437 passed**, including repository boundaries;
Ruff lint/format passed; strict Pyright reported zero errors, warnings or
informations. The wheel (88 entries) contained only package Python and dist-info,
and its builder bytes matched source. The sdist (153 entries) included the
builder and its tests, with no model/data payloads. A fresh Python 3.12 environment
installed the wheel and NumPy 2.5.3, then ran outside the checkout: **111 tests
passed**, and both complete CLI receipts matched the source run exactly.
GitHub Python CI now repeats builder/projection tests and the executable fixture
pipeline after installing the wheel outside the checkout.

### Source-fingerprint publication handling

`RES-546-EXTRACTOR-AUTHORITY-01` is an opaque reference to the privately verified
extractor source record. Existing M7 occurrence handling uses opaque references
and does not infer disclosure permission from private preservation; the RES-545
public review and PR #13 also withhold source hashes. No separate decision
clearing this source fingerprint for public disclosure was found. Consistent
with those decisions, the full digest stays in the private recovery index and
reviewer-supplied pin file. The harness still verifies exact bytes before source
execution and publishes only the opaque reference. This is a current-tree repair,
not a history rewrite, and does not reopen ownership or licensing decisions.
