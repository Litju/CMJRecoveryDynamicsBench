# Offline Gate7-native study execution, version 1

`cmj_recovery_dynamics.native_study.execute_native_study` completes the offline
execution path for a future legitimately authorized study. It provides no data,
model grants or approvals. No empirical study has been executed to qualify it.
The existing synthetic public APIs continue to reject empirical data, and native
preflight still cannot grant empirical eligibility. The new entry point requires
an independent institutional operator's pinned authorization before inference or
scoring. It reuses the existing measurement, projection, original loaders, native
pairing, bootstrap, sign-flip and Holm implementations; no new model is fitted.

## Trust and execution boundaries

Acquisition and real-person identity linkage are performed by authorized stewards,
not inferred by software. The steward first authenticates the exact version-1
native schema, full measurement/event/mass provenance, origin-known inputs,
complete four-cell origins, participant aliases/separation and permitted use.
`validate_native_dataset` checks arithmetic, structure and independently pinned
source decisions. Its existing empirical refusal is not removed: the offline
entry point accepts that single informational refusal only when every structural
and source/rights stage passed and the separate study authorization is valid.
No identity, rights, ethics, clinical validity or signature is inferred from hashes.

Install with the existing `inference` extra. Use a restricted offline process with
approved access, retention and disclosure procedures. There is no HTTP endpoint,
artifact search, dataset download, automatic file output or publication. The
returned receipt contains restricted cohort aggregates, not individual predictions;
it remains subject to the controller's disclosure decision. Exceptions do not
return partial analysis. Do not log input records or unfiltered exceptions.

## Exact authorized invocation

Call `execute_native_study(payload, plan=plan, grants=grants,
authorization=approval, expected_authorization_sha256=trusted_pin,
trusted_reviews=trusted_reviews)` from an institution-controlled runner.

- `payload`: the complete admitted `native_dataset_preflight_v1` representation.
  `candidate_indices` must be exactly 0–8. Both horizons and all five basis values
  are required at every retained origin; train/validation observations are never
  used for independent scoring. Keep registered/excluded-population accounting
  outside the retained-data representation and bind its counts in the approval.
- `plan`: the existing locked `AnalysisPlan`, primary M0, all four native rules,
  original r0/r1 family semantics, at least 10,000 resamples and fixed seed/methods.
  Real empirical use refuses `hypothetical_thresholds=True`; the investigator
  must supply all numerical decisions and their justified authority. Software
  does not supply clinical thresholds, an enrollment number or a retention default.
- `grants`: all18 existing `ModelGrant` identities, one per candidate/repeat,
  explicit config/weights paths and independently authenticated original pins,
  source and pair association. Existing loaders enforce config, dimensions,
  frozen preprocessing and safe weights-only deserialization. Do not refit.
- `trusted_reviews`: the existing independently acquired source-decision pins.
  Do not take these pins or `trusted_pin` from the incoming dataset or approval.

The approval is a restricted JSON-compatible mapping with these exact bindings:

| Field | Required value |
|---|---|
| `version` | `gate7_offline_study_authorization_v1` |
| `approved_at`, `expires_at` | Aware ISO8601 timestamps; approved_at ≤ current UTC < expires_at |
| `dataset_sha256` | Existing analysis `_digest(payload)` including reviewed records |
| `plan_sha256` | `_digest(dataclasses.asdict(plan))` |
| `models_sha256` | `_digest(model_identities(grants))`; sorted18 model/source/pair/config/weight identities, no paths |
| `trusted_reviews_sha256` | `_digest(dict(trusted_reviews))` |
| `runtime_sha256` | `_digest(study_runtime_identity())`; installed Python source, CPU runtime/library versions and thread count |
| `registered_participants`, `registered_origins` | Positive registered-population counts, not just retained counts |
| `minimum_retention_fraction` | Investigator-approved fraction >0 and ≤1 for both group and origin coverage |
| `decisions` | Every scope listed below, each with `decision="approved"`, nonempty actual `authority` and documentary `reference` |

Scopes are `investigator_plan_and_native_addendum`,
`measurement_and_origin_availability`, `participant_linkage_and_separation`,
`data_use_and_outcome_access`, `ethics_determination`, `checkpoint_execution`,
and `result_generation_and_disclosure`. An ethics scope may record an authentic
institutional exemption/non-human-subject determination where applicable; it must
not fabricate an approval. The native-only addendum explicitly addresses the
existing canonical-crosswalk gate for this bounded prospective study and does
not resolve historical canonical mappings or alter historical results.

The trusted operator authenticates these documents, signatory competence,
approval-before-outcome timing and allowed environment outside Python, then pins
`_digest(approval)` through a separate institutional channel. The digest function
is SHA256 of `json.dumps(value, sort_keys=True, allow_nan=False).encode()`, retaining
Python's default JSON separators. Preflight review pins separately retain their
existing compact-separator convention. This distinction is intentional. A changed
file, plan, grant, review or runtime requires a newly authenticated grant; self-
consistent rehashing of incoming records does not replace an independent pin.
The program cannot protect against a malicious trusted operator or discover an
unrecorded alias. These are explicit external trust boundaries, not approvals
created by a valid file.

## Execution and failure semantics

After authorization and full preflight, canonicalize participant aliases; retain
only test groups; enforce participant minima and both retention denominators;
reconstruct three-trial mechanics and baselines; derive raw39 and four history
tokens in shared query order; use H72=0/D7=1; construct the source schedule basis.
Load and predict with all18 pinned original grants. Any invalid output, missing
repeat or execution failure stops the entire analysis; no alternative primary or
partial success is produced. All candidates use identical complete queries.

The four native cells retain per-repeat RMSE/MAE/signed bias, means of per-repeat
metrics, zero-innovation paired contrasts, shared participant-cluster bootstrap,
exact sign flips through16 groups/Monte Carlo above16, Holm and investigator-
locked decision rules. The new path uses zero innovation only; optional train-only
constants remain outside this study's confirmatory hierarchy unless prospectively
added with independently authenticated fit authority. Receipt fields bind inputs,
models, authorization, source and runtime without returning prediction rows.
A `research_decision` is an authorized research operating decision, never proof of
clinical benefit, public disclosure permission or deployment readiness. Current
qualification uses invented fixtures/parameters only. Original-weight smokes use
unlabeled synthetic inputs and never score a real cohort.

Historical CPU/source parity and saved-CUDA limitations remain unchanged. M0–M3
passed prior CPU-to-saved-CUDA tolerances; M4–M8 failed them. This path records CPU
execution and does not claim historical GPU replay. Generic canonical crosswalks
and exact historical final materialization remain unresolved. No v1.0.0 artifact,
checkpoint or original loader is changed.
