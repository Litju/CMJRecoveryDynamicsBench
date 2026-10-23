# RES-546 execution plan

## Objective

Integrate only rights-cleared model metadata or inference code into
CMJRecoveryDynamicsBench. Keep all recovered checkpoints, parameter files, raw
predictions, source snapshots, and protected evaluation records outside the
public tree. This plan does not authorize redistribution or training.

## Entry gates

1. **Rights:** record explicit decisions for each checkpoint/model, original
   source, dataset and split, OLS parameter file, and aggregate result summary.
   `PUBLIC_CANDIDATE` and repository presence do not grant permission.
2. **Input contract:** define and validate a public 39-feature projection for
   the Gate7 task. The current public initial-preseason row surface does not
   provide it. Do not infer missing columns or reuse hidden fields.
3. **Dataset identity:** preserve Gate7's public fixture identity separately
   from the OLS/P8L6 training-data identity. The OLS comparator can be replayed
   on the Gate7 evaluation split, but its fit data are not a matched Gate7
   training split.
4. **Evaluation authority:** publish a numeric result only after the
   evaluation data, result-summary rights, and scoring contract are cleared.
   P8L6 has no validation score to publish or replay.

Until these gates pass, RES-546 is metadata-only and must not add a runnable
recovered model adapter.

## Planned integration

1. Add a separately namespaced Gate7 lineage record using the repository's
   existing typed model and checkpoint contracts. Keep it distinct from the
   existing initial-preseason M0 identity.
2. Record recovery, inference, score-replay, and redistribution statuses
   separately. Keep checkpoint digests and source locators in the private
   evidence record; do not put them in the public registry.
3. If the OLS model and its data/parameters are cleared, implement the adapter
   against the repository's existing feature and baseline helpers. Do not copy
   original task source or publish its JSON parameters without separate
   authorization.
4. Keep P8L6 out of the 39-feature path. A future integration would need its
   own 82-field schema, preprocessing contract, reconciled seed training
   contracts, and authorized evaluation.
5. Use the existing four-cell scorer only after the public feature projection
   and exact evaluation identity are established. Keep the Gate7 comparator
   distinct from a native historical OLS replay.

## Separate synthetic fallback

If source, dataset, or result rights block historical integration, register a
new synthetic study under a new RES-546 study identity. This is a planning
fallback, not a substitute reproduction, and no rows or models were created in
RES-545.

- Use the repository's public synthetic generator and freeze a new feature
  schema, target units/order, generator version, and deterministic split roots.
- Split by participant/group so no group crosses train, validation, and test.
- Fit preprocessing on training data only. Use the existing H72/D7 and
  force/impulse cell definitions only if the new generator supplies them
  without reconstructing withheld fields.
- Compare a declared public baseline and any newly authorized clean-room model
  only on the same generated split. Register source/config/data identities and
  scoring outputs before interpreting results.
- Keep any new weights private unless their own rights decision explicitly
  allows redistribution. Do not label the study a Gate7 or P8L6 replay.

## Completion criteria

- Rights decisions cover every artifact or output proposed for public use.
- The public input/output adapter matches a versioned schema and unit contract.
- Safe loading and finite inference pass on authorized public rows.
- The scorer reproduces its registered results on the exact identified split.
- No private checkpoint, unsafe serialized estimator, raw result packet, or
  protected dataset enters the repository or release artifacts.
- The v1.0.0 release remains unchanged.
