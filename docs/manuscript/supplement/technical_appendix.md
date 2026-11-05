# Technical supplement

## A1. Full formulation matrix

In this section, M1/M3 references describe historical evidence/reconstruction layers, not Gate7 neural family identifiers. The eight formulation identities and nine neural families are separate namespaces.

### Initial preseason

Identity: initial_preseason_camp_recovery. Status: SUPERSEDED. Parent: unresolved.

World: event_time_adaptation_recovery; observation: camp_history. Task: Force and impulse innovations at H72 / D7. Evaluation: Four-cell public selection; production calibration unavailable.

The initial camp sample asks about H72 and D7 using pre-origin assessments, exposures and known plans. Superseded sample/surface; direct parent is unresolved; task and world law match the canonical state. Linear baseline and M0 inference adapters exist. The historical 39-column projection is absent; a preserved private M0 checkpoint is not auto-loaded.

### Canonical preseason

Identity: canonical_preseason_camp_recovery. Status: SUPERSEDED. Parent: initial_preseason_camp_recovery.

World: event_time_adaptation_recovery; observation: camp_history. Task: Force and impulse innovations at H72 / D7. Evaluation: Native scorer exists; calibration and historical model binding unresolved.

A canonical horizon-row sample and query surface; the task and world law are retained. Canonical query surface and sample; not a new task or world law. Historical five-run campaign is numeric result evidence only; no runnable historical M3 model use is registered.

### Rich-history camp

Identity: rich_history_camp_recovery. Status: RETIRED. Parent: unresolved.

World: fitness_fatigue_impulse_response; observation: rich_monitoring. Task: Force and impulse innovations at H72 / D7. Evaluation: 24-cell raw-progress diagnostic; historical calibration locked.

Richer monitoring and variable histories; a distinct retired 24-cell diagnostic with unresolved ancestry. Retired formulation; its direct scientific parent is unresolved. Registered zero-innovation baseline is executable. Historical empirical-Bayes, boosted-residual and headroom results are evidence only. The new public ridge study is a separate experiment.

### Preliminary post-exposure

Identity: preliminary_post_exposure_recovery. Status: SUPERSEDED. Parent: unresolved.

World: biexponential_episode_response; observation: episode_summary. Task: Force and net-impulse innovations at H24 / H48 / H72. Evaluation: Production evaluation not implemented.

One current exposure and four prior episodes, using scalar paired-trial measurements. Direct parent is unresolved; preliminary measurement contract without a frozen force–impulse identity. No M3 model implementation and no public M1 numeric historical result are registered.

### Phase-consistent

Identity: phase_consistent_post_exposure_recovery. Status: SUPERSEDED. Parent: preliminary_post_exposure_recovery.

World: biexponential_episode_response; observation: phase_consistent_force_impulse. Task: Force and net-impulse innovations at H24 / H48 / H72. Evaluation: Six-cell research diagnostic; production scorer not implemented.

Both outcomes now come from the same concentric force trace; the episode response law is retained. Observation-law repair; the episode response law is retained. Historical ridge research result is evidence only; no executable M3 model adapter is registered.

### Correlated exposure

Identity: correlated_exposure_recovery. Status: SUPERSEDED. Parent: phase_consistent_post_exposure_recovery.

World: correlated_exposure_response; observation: phase_consistent_force_impulse. Task: Force and net-impulse innovations at H24 / H48 / H72. Evaluation: Six-cell, progress-ratio and progress-loss diagnostics; production scorer not implemented.

A correlated four-factor exposure distribution changes the forecasting world. Material correlated exposure-distribution change; later redesigned. Historical local, frontier and other predictor families are result evidence only; no exact historical numerical replay is qualified.

### Threshold response

Identity: threshold_response_recovery. Status: PROPOSED. Parent: correlated_exposure_recovery.

World: threshold_response; observation: phase_consistent_force_impulse. Task: Force and net-impulse innovations at H24 / H48 / H72. Evaluation: Proposed twelve-cell evaluation; calibration reference unavailable.

Participant-weighted high/low-load thresholds; a proposed alternate, not an accepted successor. Proposed alternate, not an accepted successor formulation. Reference predictor configuration is unresolved; its checkpoint is not public. No M1 numeric historical result is registered.

### Fixed-mode discrepancy

Identity: fixed_mode_discrepancy_recovery. Status: ACTIVE_CANDIDATE. Parent: correlated_exposure_recovery.

World: fixed_mode_discrepancy_response; observation: phase_consistent_force_impulse. Task: Force and net-impulse innovations at H24 / H48 / H72. Evaluation: Six-cell research NRMSE and relative-progress diagnostics; production scorer not implemented.

Fixed 24 h / 84 h mathematical response modes plus bounded smooth discrepancy; not biological compartments. Active candidate; fixed modes are mathematical anchors, not biological compartments. Historical local, generic and structured predictors are result evidence only. The new public study fits zero, constant, ridge and structured models independently of historical replay.

## A2. Original architecture and input matrix

M0 (r0, r1): 39 → 32 → 2; exact GELU. Inputs: 39 raw features. Parameters: 1346. CPU: Exact source parity. Historical CUDA comparison: Within recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M1 (r0, r1): 39 → 64 → 2; exact GELU. Inputs: 39 raw features. Parameters: 2690. CPU: Exact source parity. Historical CUDA comparison: Within recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M2 (r0, r1): 39 → 64 → 64 → 2; exact GELU. Inputs: 39 raw features. Parameters: 6850. CPU: Exact source parity. Historical CUDA comparison: Within recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M3 (r0, r1): Raw backbone + pointwise history encoder; mean/latest pooling → 128 → 2. Inputs: 39 raw + 4 × 4 history. Parameters: 7138. CPU: Exact source parity. Historical CUDA comparison: Within recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M4 (r0, r1): Raw backbone + 4 → 32 GRU; mean/latest pooling → 128 → 2. Inputs: 39 raw + 4 × 4 history. Parameters: 10626. CPU: Exact source parity. Historical CUDA comparison: Outside recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M5 (r0, r1): M4 + 2 × 8 horizon embedding → 136 → 2. Inputs: 39 raw + 4 × 4 history + horizon. Parameters: 10658. CPU: Exact source parity. Historical CUDA comparison: Outside recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M6 (r0, r1): M5 + first two basis values → 16 → 152 → 2. Inputs: 39 raw + 4 × 4 history + horizon + 5 basis values. Parameters: 10738. CPU: Exact source parity. Historical CUDA comparison: Outside recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M7 (r0, r1): M5 + all five basis values → 16 → 152 → 2. Inputs: 39 raw + 4 × 4 history + horizon + 5 basis values. Parameters: 10786. CPU: Exact source parity. Historical CUDA comparison: Outside recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

M8 (r0, r1): M7 + bias-free 5 → 2 linear basis head. Inputs: 39 raw + 4 × 4 history + horizon + 5 basis values. Parameters: 10796. CPU: Exact source parity. Historical CUDA comparison: Outside recorded tolerance. Outputs: force then net impulse, additive innovations, identity transform.

## A3. Tolerances, metrics and assumptions

Equation (1) in the manuscript is the frozen elementwise saved-CUDA rule; exact CPU equality is a separate acceptance requirement. Near-zero denominators make maximum relative error alone unsuitable as acceptance. Arrays contain 512×2 historical outputs; failures count elements, not participants. Original runtime attribution remains unresolved for M4–M8. No M10 inference or tolerance change occurred.

For the public synthetic study, six cells are normalized independently before equal-weight aggregation. Root SD uses ddof=1; truth SD uses ddof=0. There are three roots, not three human cohorts. Reported bootstrap intervals are paired against zero, use 5,000 resamples of 16 whole camps and cannot be transformed into an unreported ridge-vs-structured contrast. Native analysis instead uses separate force/impulse cells at H72/D7; at least 10,000 participant bootstrap resamples, marginal percentile intervals, exact sign enumeration for ≤16 participants and sampled allocations otherwise. Sampled sign tests use a plus-one correction; exact enumeration does not. Holm correction applies to the four locked primary tests. Independent clusters and symmetry of cluster loss differences are assumptions. Neither bootstrap supplies transportability evidence.

## A4. Artifact-bound provenance and reproduction

Public evidence files S01–S27 are byte-extracted from immutable release source and indexed by full SHA-256 in evidence/sources.json. Claims are in evidence/claims.json and CSV. The original synthetic study's scientific digest is independently checked by removing compute_costs and scientific_results_sha256, then hashing sorted compact UTF-8 JSON. The full receipt retains per-root/per-cell RMSE, truth SD, NRMSE, paired intervals, model choices and runtime. Figure inputs retain that receipt unchanged.

Public figure regeneration needs only the staged plot inputs and plotting script. It does not require checkpoint access, training, athlete data or execution of the historical experiment. Original study rerun instructions are preserved in S02 for context; selection/refitting is outside the authorization of this manuscript production and was not executed. Exact historical private inference requires separately authorized original artifacts and a matched runtime. Checksum consistency is not independent empirical authentication.

## A5. Known failures, nonclaims and availability

The public code reconstructs source-faithful research inference routes but ships no original trained checkpoints. Archived numerical comparisons establish no athlete predictive accuracy. M4–M8 historical CUDA compatibility failed. The rich-history reproduction differs in row counts. Historical dataset-hash authority remains partial even for matching counts. Source mathematics does not close unresolved canonical target crosswalks. No production scorer, clinical utility, out-of-distribution validation or manual NVDA acceptance is established. Software CI demonstrates tested implementation behavior, not scientific qualification of a cohort.

The source package is Apache-2.0; trained states and restricted records are separately governed. All draft outputs require owner publication approval. No submission, DOI or peer-review status is asserted.

## A6. Detailed released technical evidence

The following unchanged public technical records accompany this supplement in evidence/: S06 original inference qualification; S07 CPU integration policy; S08 M8 recovery; S09 complete native mechanics/basis specification; S10 complete native statistical methods; S11 fitted-artifact rights; S12–S15 historical M4–M7 numerical findings. They contain the source-supported parameter counts, raw/history feature definitions, original preprocessing behavior, detailed failures and output contracts. These records are supporting evidence, not a replacement for unresolved historical authority.


## A7. Machine-readable tables and exact experiment identities

Table A2 (rendered below and in architecture_qualification.csv) is the architecture/qualification matrix; it lists all nine model families, two repeats, verified parameter counts, inputs, architecture and separate qualification states. Table A3 (rendered below and in six_cell_results.csv) lists all four reference models and six cells, exact three-root values, means and sample SDs. The full original per-root uncertainty record is preserved unchanged in S01.

Study provenance (literal receipt fields):

{
  "base_public_main": "ecdf93091517",
  "benchmark": "fixed_mode_discrepancy_recovery",
  "classification": "new synthetic research study; not a historical replay",
  "dataset": "fixed_mode_recovery_candidate_sample",
  "historical_private_score_use": false,
  "human_data_use": false,
  "name": "RES-526 fixed-mode public reference-model study",
  "package_source_sha256": "12e9e192accefb867707765098a4dd9eeabfd735097646fa4d4bcae5db60d0c3",
  "production_score_claim": false,
  "study_code_sha_abbreviated": "7421f02f39d7"
}

Selection lock SHA-256: 07ce6ed56c292e2f56d306eb38b2ff8ea574f4cf0cc3f0644b94fa2db872cb21. Protocol SHA-256: 972733eb2d85e49f61281955eaad327f06adadce8b66a1ec32e74fcba7838f48.


## A8. Complete schedule basis and interpretation

For exposure i at time t_i≤T, let d_i be duration in minutes divided by 100 minutes, C_i=Σ_{j≤i}d_j, h(C)=10C/(1+C), Δ_i=h(C_i)−h(C_{i−1}), C_0=0, and w_τ(i)=exp[−max(0,T−t_i)/τ]. The ordered five-value basis is (Σ_i d_i w_36(i), Σ_i d_i w_120(i), h(C_final), Σ_i Δ_i w_36(i), Σ_i Δ_i w_120(i)). All values are dimensionless. Nominal times and durations must be known at the origin; no target assessment enters this function. Basis constants 36/120 hours differ from the separate public synthetic comparator's 24/84-hour anchors. Gamma is declared as one in the original configuration but is not separately applied in its rational saturation arithmetic. Event dose zero contributes zero. A schedule event at target time has decay weight one.

## A9. Qualification revision audit

The revision reconciles original checkpoint, configuration and candidate-result bytes and fitted preprocessing for all 18 final routes against the preserved inventory and qualification receipts. It does not reload checkpoints, execute inference, fit models or regenerate historical data. Exact CPU equality is a recorded comparison rechecked in those receipts. Private source associations are retained internally; public code and public technical reports provide disclosure-safe support for the architecture contracts. New hashes of private artifacts remain solely in the internal evidence directory. Public summaries provide no private download mechanism and no license to redistribute weights.

The sentence-level register identifies every substantive sentence, equation paragraph and tabular block in this supplement and manuscript, including interpretive and nonclaim statements. Evidence support uses immutable public source lines, verified scholarly sources or explicitly identified current audit artifacts. Scientific inference is distinguished from source-reported behavior and direct arithmetic. Owner authorship/funding/conflict decisions are submission metadata, not missing scientific observations.
