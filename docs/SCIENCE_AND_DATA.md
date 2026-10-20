# Science, data and interpretation

This site is a research exhibition over frozen, public synthetic evidence. It is not an athlete-monitoring product, an empirical CMJ study or a production recovery-score implementation.

## Authority and reproducibility

The preserved scientific source is [`Litju/CMJRecoveryDynamicsBench`](https://github.com/Litju/CMJRecoveryDynamicsBench) at commit [`3dc4c82f0c948add6e4a9ebdebfd227933c823d3`](https://github.com/Litju/CMJRecoveryDynamicsBench/tree/3dc4c82f0c948add6e4a9ebdebfd227933c823d3). It is not a submodule and is not modified by this website task.

| Receipt or fixture | SHA-256 | Use |
| --- | --- | --- |
| `source/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json` | `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9` | Pinned fixed-mode study results and registered protocol |
| `src/data/results.json` and `public/data/results.json` | `4d3b9d8ce4d40a8fdf956ee19585aee01dc5a6b6cf1af802b7011ecf03803bca` | Deterministic exhibition fixture; byte-identical copies |
| `source/M8_V1_RELEASE_AUDIT_RECEIPT.json` | `60b17138deee66d22e766740847a344bede3f07ff794fe6ad524ea4a690151ba` | Preserved upstream release audit receipt |

`source/manifest.json`, `source/lineage/manifest.json` and `source/exhibition/manifest.json` pin the individual upstream files. Run `npm run build` or `node scripts/prepare-data.mjs --check` to verify those hashes and that `src/data/` and `public/data/` match the expected fixture serialization. These checks are offline. `npm test` independently checks fixture identity, exact displayed values, all 17 diagnostic variants and selection minima, scientific definitions, lineage contracts and the mathematical identities used in the lab.

`source/CITATION.cff` is preserved exactly from the scientific repository and identifies Julio Rodriguez, version 0.1.0. Cite the upstream scientific software using that file; the website has no separate citation record or versioned scientific result.

## What the active numbers mean

The default explorer exposes four variants and three public roots (A, B and C): zero innovation, training constant, full ridge and fixed-mode structured. The fixture also preserves 17 receipt-reported variants for methods and sample-efficiency comparisons.

The registered active metric is the **mean of six cellwise NRMSE values**: mean-force innovation and net-impulse innovation at H24, H48 and H72. For each outcome/horizon cell, NRMSE is RMSE divided by that cell's truth population standard deviation (`ddof=0`). The six cells receive equal weight; force and impulse RMSE stay in their separate units. A root score is the mean of its six ratios. The across-root summary is the mean of the three root scores; its root-to-root sample standard deviation uses `ddof=1`.

| Displayed variant | Across-root mean six-cell NRMSE |
| --- | ---: |
| Zero innovation | 2.430659 |
| Training constant | 1.036038 |
| Full ridge | 0.736270 |
| Fixed-mode structured | 0.773316 |

These rounded values are copied from the pinned receipt through the fixture; lower is better for this synthetic diagnostic. They do not measure prediction accuracy in athletes. No direct ridge-versus-structured confidence interval or pooled across-root interval is reported. The UI's 96 views are the 4 displayed variants × 4 root choices (`mean`, A, B, C) × 3 horizons × 2 outcomes. They are alternate views over the same receipt, not 96 new experiments.

The registered study uses 96 training camps and 16 development camps. Each of the three caller-supplied public evaluation roots has 16 camps, with 4,000 rows per outcome/horizon cell. The three roots share the same declared synthetic world; they are not three different populations or an out-of-distribution test. The fixed-mode result is a new public synthetic diagnostic, not a historical campaign replay. Hyperparameters are selected on the declared training/development procedure, not by the evaluation-root filter. For the six reported selection configurations, the selected alpha is 0.01, the lower edge of the registered grid; this does not establish that weaker regularization is optimal outside that grid.

The receipt's reported bootstrap uses 5,000 whole-camp resamples of 16 camps with seed 49,505,000. Episodes and forecast horizons remain together within each sampled camp. The displayed intervals are per-root aggregates and paired contrasts against zero. Do not read them as cell intervals, a direct comparison interval between the ridge and structured models, or uncertainty from refitting on new training samples.

## Eight-formulation lineage

The exhibit preserves the scientific identifiers, status labels and only the parent edges present in the pinned contracts. `Not registered` means the snapshot has no parent edge; it does not authorize a newly inferred relationship.

| Scientific identifier | Status | Registered parent |
| --- | --- | --- |
| `initial_preseason_camp_recovery` | Superseded | Not registered |
| `canonical_preseason_camp_recovery` | Superseded | `initial_preseason_camp_recovery` |
| `rich_history_camp_recovery` | Retired | Unresolved in the source record |
| `preliminary_post_exposure_recovery` | Superseded | Unresolved in the source record |
| `phase_consistent_post_exposure_recovery` | Superseded | `preliminary_post_exposure_recovery` |
| `correlated_exposure_recovery` | Superseded | `phase_consistent_post_exposure_recovery` |
| `threshold_response_recovery` | Proposed | `correlated_exposure_recovery` |
| `fixed_mode_discrepancy_recovery` | Active candidate | `correlated_exposure_recovery` |

Five parent edges are registered. The rich-history branch has no exact direct parent in the source record. The threshold formulation remains **proposed**; fixed-mode discrepancy remains an **active candidate**. An active-candidate status is not an accepted metric or scorer. Historical formulations have partial exact historical-replay authority: source code or receipts exist for parts of the chains, while several adapters, checkpoints or evaluation components remain unavailable. The retired rich-history 24-cell raw-progress score is not comparable to the active six-cell NRMSE.

## Illustrations and claim boundaries

- The Episode Theater is a conceptual information-flow display. Its schematic trials and later-observer view are not raw generated records or evidence that a predictor may use future observations.
- The apparatus and exposure figures explain measurement constructs; they are schematics, not participant trials.
- The Recovery Lab evaluates an explicit two-exponential equation with user-selected arbitrary amplitudes and fixed 24 h / 84 h time constants. It is not fitted from the benchmark receipt and does not reproduce the benchmark's full response, discrepancy, noise or exposure generator.
- The 24 h / 84 h mathematical modes are time constants, not half-lives. Signed curve area is not training dose, accumulated physiological burden or a validated fatigue measure.
- There are no human participants or external athlete cohort results in this showcase. Same-generator synthetic evidence does not establish empirical validity, transportability, out-of-distribution robustness or causal interpretation.
- The site does not deliver an accepted production scorer or athlete-specific advice. No result should be used to prescribe training or assess readiness.

## Source and license boundary

Upstream scientific code and its Apache-2.0 license are preserved in `source/`; the upstream citation remains in `source/CITATION.cff`. This license does not automatically extend to the website's original source, screenshots or prose. The site currently has no root license. The Geist font's separate OFL notice is included under `public/fonts/`. See the [release checklist](RELEASE_CHECKLIST.md) before making this repository public.
