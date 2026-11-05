# Recovering Reproducibility in Scientific Machine Learning: Reconstruction, Numerical Qualification, and Benchmarking of Countermovement-Jump Recovery Models

Private owner-review manuscript • qualified revision V2 • 4 November 2026 • Authorship, affiliations, funding and competing interests require owner confirmation before submission.

## Abstract

Scientific machine-learning archives often preserve source code without preserving the complete chain connecting fitted models, measurements and reported results. We investigate this problem through CMJRecoveryDynamicsBench, a reconstruction of the historical Preseason Recovery research program. We reconcile eight scientific formulations, nine original neural model families and two repeats per family through explicit source, preprocessing, measurement, numerical and rights contracts. Released documentation records exact original-source CPU inference agreement for all 18 model/repeat routes, while M4–M8 fail comparison with saved historical CUDA predictions under the unchanged elementwise tolerance. These findings establish source-equivalent inference rather than successful historical GPU replay or predictive validity. Separately, an existing public fixed-mode synthetic study compares four reference models across three independently seeded populations from the same generator. Mean six-cell normalized root-mean-square errors are 2.430659 for zero innovation, 1.036038 for a training constant, 0.736270 for ridge and 0.773316 for a structured comparator. We independently verify receipt arithmetic and preserve the distinction between this H24/H48/H72 diagnostic and native H72/D7 evaluation in physical units. The contribution is an artifact-bound reconstruction method, a reproducibility qualification matrix and a reproducible evidence-to-figure package. Historical campaign recovery remains partial; neither independent human-athlete predictive validity nor clinical utility is established.

## 1. Introduction

Archived code is necessary but insufficient for recovering a scientific machine-learning result. Inference depends on a selected fitted state, feature ordering, preprocessing parameters, output transformations and numerical execution. Evaluation additionally depends on measurement definitions, split membership, missingness, aggregation and selection rules. A program can execute correctly while answering a different scientific question from the historical experiment.

The historical Preseason Recovery program provides a useful case because its scientific formulations evolved alongside its model architectures. Counters such as M0–M8 have also been used for engineering milestones. We therefore distinguish the nine Gate7 neural candidates from the eight scientific formulations and from the public M8 reproduction milestone. They are different classifications, not interchangeable experiment identifiers.

Our central question is how heterogeneous historical experiments can become verifiable research software without erasing disagreement or treating incomplete preservation as successful replication. We contribute a reconstruction procedure that binds claims to specific artifacts; a separation of source-equivalent inference, saved-runtime compatibility and scientific validity; and an executable evidence-to-figure package. We claim methodological and engineering contributions, not a new learning algorithm. The study is a retrospective case analysis with a separate, already recorded synthetic benchmark; no model training was conducted for this manuscript.

## 2. Related work and methodological position

Pineau and colleagues [R9] describe a community reproducibility program combining code availability, reproduction challenges and reporting checklists. Their approach motivates explicit evidence reporting here, but a checklist cannot restore missing fitted states. Sandve and colleagues [R1] emphasize recording computational steps and retaining the precise inputs behind results. Our source and receipt ledger applies this principle at the level of each model route and scientific claim.

The FAIR principles [R6] and their research-software extension [R7] frame findability, accessibility, interoperability and reuse as properties that require explicit metadata. Here, accessibility must respect different rights for software, trained weights and scientific records. Public code and publicly documented qualification do not imply public access to the original fitted artifacts. Hashes identify bytes; they neither establish permission nor authenticate an empirical instrument.

Goldberg [R2] explains the foundations of floating-point arithmetic. Finite-precision arithmetic explains why numerical agreement must be stated relative to a specific operation and execution environment. We separate equality against preserved CPU source from compatibility with saved CUDA-era arrays. PyTorch's numerical-accuracy documentation explicitly warns that CPU and GPU calculations can disagree even with identical inputs. This is implementation context, not proof of the cause of any particular historical discrepancy. A reduced-precision approximation can support a mechanism without reproducing the original GPU execution.

CMJ methodology is similarly contract-dependent. Merrigan and colleagues [R4] emphasize metric-specific force-time reliability. Anicic and colleagues [R3] examine which CMJ quantities should be reported; force-time quantities cannot be treated as interchangeable measures of recovery. Their empirical measurement evidence does not validate this forecasting system. TRIPOD-Cluster [R5] motivates transparent reporting of clustered development and validation populations. We use that reporting distinction without asserting formal guideline certification or converting synthetic camps into human cohorts. Our contribution connects these established principles across source preservation, fitted inference and measurement-bound evaluation.

Checkpoint preservation is a data-management problem as well as an executable-code problem. ModelHub [R10] treats learned parameters and their versions as lifecycle artifacts. Our reconstruction adds a retrospective qualification question: whether an authenticated fitted state, its preprocessing and the recovered implementation reproduce a specific recorded operation. We do not attribute our biological measurement or rights contracts to ModelHub, or claim that inventory reconciliation proves a successful historical runtime replay.

Experiment provenance is richer than a file checksum. The Open Provenance Model [R11] represents past executions through annotated causal relationships. Our ledger records the concrete links needed for this case—source, configuration, selected checkpoint, inputs and qualification receipt—without claiming complete recovery of the historical execution graph. A digest detects byte substitution; scientific authority still depends on the origin and interpretation of the identified object.

Ahrens, Demmel and Nguyen [R13] give algorithms for summation that are reproducible despite changes in summation order. Their analysis explains why bitwise equality is a property to engineer rather than assume. It does not establish that summation order caused the Gate7 discrepancies. We retain the original acceptance rule and distinguish the explanatory TF32 diagnostic from authenticated GPU execution.

Morris, White and Crowther [R12] emphasize explicitly specifying data-generating mechanisms and performance measures in simulation studies. That distinction bounds our interpretation of three same-generator roots: they probe a controlled synthetic setting, not transportability to athlete populations. Breck and colleagues [R14] separate ML-specific testing and monitoring concerns from generic software testing. Their production-readiness rubric motivates our distinction between passing CI and demonstrating scientific validity; no production-readiness score is assigned here.

## 3. Scientific background and formulation genealogy

The task predicts additive changes in force and impulse relative to an origin-specific baseline, conditional on information available at that origin. Baseline-relative innovations are physical outcomes, not a validated recovery score. Forecasting an observation is distinct from inferring a physiological recovery state.

Figure 1 and Supplement Section A1 distinguish eight formulations. The initial and canonical preseason formulations ask about H72/D7 camp forecasting under an event-time adaptation world. Canonicalization changes the query/sample surface rather than establishing a new world law. Rich-history camp recovery uses richer monitoring and a fitness-fatigue impulse-response world; its retired 24-cell diagnostic is distinct. The preliminary episode formulation shifts to H24/H48/H72 with one current exposure and four prior episodes. Phase consistency repairs the force/impulse observation relation while retaining the episode response law. Correlated exposure changes the exposure distribution. Threshold response is a proposed alternate. Fixed-mode discrepancy is the active candidate, using fixed 24-hour and 84-hour mathematical modes with bounded smooth discrepancy. These modes are not identified biological compartments.

Direct ancestry is unresolved for several roots. We show only recorded parent relations and do not infer a linear progress narrative. Shared outcome names do not authorize metric pooling when observation laws, horizons, populations or normalizers differ.

## 4. Reconstruction methodology

We use a layered reconstruction contract (Figure 2). First, preserve originals and enumerate source, configuration, checkpoint and result identities without modifying them. Second, reconcile candidate, repeat and selected-state identities across the inventory and run-bound records. Third, recover architecture and fitted preprocessing, including feature order and dtype transitions. Fourth, compare authenticated input tensors before comparing outputs. Fifth, qualify the recovered inference path against original source on fixed inputs. Finally, retain saved-runtime comparisons and publish only rights-cleared summaries.

The historical verification used weights-only loading rather than unrestricted pickle execution. Fitted scalers were restored from authenticated configurations; no preprocessing fit or checkpoint selection was performed during inference recovery. A state dictionary alone is insufficient because the same tensor shapes can be attached to different input semantics. Authentication therefore covers both byte identity and the meaning of each forward input.

We pin scientific evidence to v1.1.0 source 401f87aad1e4ef4108011fa0c1d769a24f1ad329. Current main 6987cac1cb88e31a3b406945a48e0732f8453dee supplies later editorial guidance and must not replace release evidence. The older synthetic experiment retains its original study and receipt identities. Each evidence register entry gives an exact public path, commit, SHA-256, evidence type, status, interpretation and limitation. Private evidence remains private; public summaries are not independent public replays of the underlying artifacts.

In this qualification revision we independently rehashed the original checkpoint, configuration and candidate-result files for all 18 routes, compared them with the preserved inventory and qualification receipts, and recomputed canonical fitted-preprocessor digests. All associations agreed. These are read-only artifact checks, not a fresh inference run. The internal matrix retains private identities; Table 2 reports only public model contracts and recorded qualification. The sanitized route table records the availability boundary without exporting private checkpoint or configuration hashes.

## 5. Original model architectures and inference contracts

Figure 3 and Table 2 distinguish the nine Gate7 model families. Every family has final repeats r0 and r1. M0 uses a 39-to-32-to-2 network; M1 widens the hidden layer to 64; M2 uses two 64-unit hidden layers. Exact GELU is part of the recovered contract. M3 adds a shared pointwise history encoder and mean/latest pooling. M4 replaces that history encoder with a single-layer 4-to-32 GRU. M5 adds a two-entry, eight-dimensional horizon embedding. M6 adds a projected basis branch but uses only the first two basis values. M7 consumes all five basis values. M8 adds a bias-free five-to-two basis head to the residual output.

The public architecture table is descriptive; repeat-specific checkpoint and selected-state hashes remain privately authenticated. These models are not aliases for the four public synthetic reference models. Their inference fixtures include 24 synthetic rows and a preserved 512-row validation split. An inference smoke with no outcome evaluation is not an accuracy experiment.

Inputs include 39 raw features, four history tokens with four values each where required, a horizon identity, and five schedule-derived basis values where required. Fitted standardization precedes float32 neural inference. Outputs are two additive innovations ordered as relative mean concentric force (N/kg) and relative concentric net impulse (m/s). The output transform is identity. Loss/evaluation scaling must not be applied as an inverse prediction transform, and baseline addition is outside this adapter. Supplement A2 preserves the architecture and input contracts.

## 6. Numerical verification

For replayed element a and reference element b, the recorded historical acceptance rule is

|a − b| ≤ 10⁻⁵ + 10⁻⁴ |b|. (1)

Earlier source-comparison tolerance was 10⁻⁶ + 10⁻⁵|b|; the composed CPU-source qualification additionally requires exact array equality. Maximum relative error is |a−b|/max(|b|, float64.tiny). Its maximum alone does not decide the combined tolerance. We do not change a threshold after seeing a failure.

The released record reports zero CPU-source error for all 18 final routes; this qualification revision confirms those recorded results against the preserved receipts without rerunning inference. Saved-CUDA comparisons pass for M0–M3 and fail for both repeats of M4–M8 (Figure 4). For M8, maximum absolute discrepancies are 0.00022125244140625 and 0.00030422210693359375; respectively 98 and 145 of 1,024 output elements fail. The units differ between output columns, so these global maxima are arithmetic diagnostics, not a pooled physical-error score.

A fixed CPU TF32 approximation produces no tolerance failures for the recorded M8 comparisons. This supports a numerical mechanism but is not authentic historical CUDA replay. Runtime attribution remains unresolved. Exact agreement in a qualified CPU environment establishes an implementation relationship; it does not establish portability across every library, device, precision mode or reduction order. The manuscript reproduces receipt arithmetic, not private historical inference.

## 7. Native biomechanical mechanics and assessment construction

Let Fz(t) denote upward gross vertical ground-reaction force in N, m the positive accelerated system mass in kg and g positive gravity in m/s². The system includes mechanically accelerated attached mass. For supplied concentric onset t_co and takeoff t_to, T=t_to−t_co>0,

F_rel = [∫ from t_co to t_to Fz(t) dt] / (mT), in N/kg. (2)

J_rel = [∫ from t_co to t_to (Fz(t)−mg) dt] / m, in m/s. (3)

The mathematical identity F_rel=g+J_rel/T provides a consistency check. It does not authorize a crosswalk to another benchmark's force target. This is gross time-mean concentric force, not peak force. Net impulse is the change in centre-of-mass velocity over the interval; a zero origin for that velocity coordinate is not an empirical velocity estimate.

Finite strictly increasing timestamps may be nonuniform. Event-boundary forces are linearly interpolated where necessary; interior samples and both boundaries are integrated with sequential composite trapezoids. Source mathematics accepts supplied event times and does not supply an empirical detector or filter. Measurement correctness requires independently authenticated calibration, timing, phase selection and system mass.

An assessment is the arithmetic mean of exactly three distinct valid trials, not the best trial or median. The baseline averages the two latest distinct valid qualifying assessments in the inclusive 24–240-hour pre-origin interval. Native H72 permits 66–78 hours; D7 permits 156–180 hours. Figure 6 displays these windows. Output innovations use a separately evaluated additive latent-plus-error expression. Subtracting serialized absolute values and baselines need not reproduce those innovations bitwise.

The five-value schedule basis divides each exposure duration measured in minutes by 100 minutes to obtain dimensionless dose. It uses exponential decays with 36-hour and 120-hour constants and saturating cumulative dose h(C)=10C/(1+C). It includes two duration-weighted decays, final h(C), and two decay-weighted increments of h(C). The index exposure already occurs once in the known plan. These are public schedule functions, not inferred physiological states.

## 8. Existing public synthetic experiment

The fixed-mode study is a separate synthetic research experiment with frozen train/development selection and three test roots from the same generator. Training contains 96 camps, 24,000 episodes and 72,000 horizon rows. Development and each test root contain 16 camps, 4,000 episodes and 12,000 rows. An episode's three horizon queries stay together. Separation checks include participant, episode, query and camp identities.

The predictor schema has 82 public fields: horizon, three baseline fields, two participant-context fields, eight current-exposure fields and four prior episodes with 17 fields each. Horizon one-hot encoding produces 84 numeric columns. Means and population SDs are fitted on training rows only; zero scales become one. Labels, target-time realizations, generator effects and oracle states are excluded.

The four reference models are zero innovation, a training-only outcome-by-horizon constant, cellwise ridge, and a structured comparator using normalized exposure primitives with fixed 24-hour/84-hour decays plus observed covariates. Ridge and structured regularization use a frozen alpha grid {0.01,0.1,1,10,100}, selected on development six-cell NRMSE with lower-alpha tie breaking. All recorded selected configurations choose 0.01, the grid boundary. This is a limitation, not permission for post-test adjustment.

For outcome/horizon cell c with n_c observations,

RMSE_c = sqrt[Σ_i (prediction_i−truth_i)²/n_c]; NRMSE_c = RMSE_c / SD_pop(truth_c). (4)

The primary score is the equal-weight mean of six NRMSE cells. Each cell needs at least two observations and nonzero truth population SD (ddof=0). Research progress is 1 minus that mean, without clipping. This score is not a native four-cell physical-unit metric or a production recovery score.

## 9. Results and statistical interpretation

Table 1 and Figure 5 report the existing four-model results. Across three roots, full ridge has lower mean diagnostic error than the structured comparator. This is a descriptive same-generator result, not a new cross-model significance test. Root-to-root sample SD describes three generated populations; it is not a confidence interval for real-athlete generalization.

Reported uncertainty uses 5,000 paired whole-camp bootstrap resamples of 16 camps per root, PCG64 seed 49,505,000. Model and zero-baseline comparisons share draws. With only 16 clusters, intervals are descriptive and can be coarse. We preserve the reported model-vs-zero intervals and do not infer a ridge-vs-structured interval from separate marginal intervals.

Recorded ablations give mean NRMSE 0.819681 without prior history, 0.867735 without current exposure and 0.736346 without participant context, compared with 0.736270 for full ridge. Removing participant context changes the rounded aggregate by approximately +0.000076. These diagnostics suggest which fields help within this generator; they do not identify causal athlete mechanisms. Nested 24/48/96-camp ridge results are 0.736889/0.736602/0.736270 with full-data alpha fixed. The apparent small sample-size effect is conditional on thousands of synthetic episodes and the selected generator.

The public reproduction record also preserves rich-history disagreements: training has 15,134 clean-room rows versus 15,182 historical rows; validation has 3,799 versus 3,795. These are documented reproduction differences in horizon membership, not newly discovered experimental effects. Matching row counts elsewhere does not prove historical dataset identity. All eight historical formulation chains remain partially reproducible.

Native analysis is an engineering capability rather than a completed athlete study. It reports query-weighted RMSE, MAE and signed bias separately in four cells, with family metrics defined as the arithmetic mean of repeat metrics rather than prediction ensembling. Participant bootstrap resamples retain all queries per participant. The sign-flip test requires independent clusters and symmetry of cluster loss differences under the null. Holm adjustment covers four primary tests. With six strictly positive participant improvements, the smallest exact p is 1/64 and the smallest Holm-adjusted value is 4/64=0.0625; this engineering example cannot meet 0.05. Such a failure is correct analysis behavior, not evidence against a fitted model.

## 10. Discussion

Reconstruction succeeds when the meaning and limits of a result become inspectable. Here, the same recovered model can be source-qualified and historically CUDA-incompatible. Reporting a single reproduced/not-reproduced flag would erase that distinction. A useful reproducibility record instead binds an operation, artifact, input set, runtime and acceptance rule.

Measurement contracts are equally consequential. Correct trapezoidal integration does not establish that an empirical event detector selected the intended phase. Consistent baseline arithmetic does not establish that the baseline measures the scientific construct of recovery. Predictive validity requires separate data, protocol and population authority. An artifact hash can prevent accidental substitution while leaving the scientific origin of an artifact unresolved.

The synthetic benchmark demonstrates that a completely public diagnostic can be useful without retroactively becoming historical validation. Its controlled exposure and response laws allow leakage and aggregation checks, but also favor information structures specific to that world. Fixed response modes provide modeling anchors rather than biological identification. The weaker structured comparator is a meaningful negative result for this setup and should not be hidden by a novelty narrative.

## 11. Limitations

Historical M4–M8 CUDA comparisons fail unchanged tolerances; authentic historical replay is not established. Historical campaign reproduction is partial, including the rich-history row-count discrepancies and missing final materialization authority. Original fitted states and restricted records are not publicly distributed, limiting independent replay of private qualification. A public summary of private checks is weaker access than public executable verification of the same artifacts.

There is no independent human-athlete predictive validation, demonstrated clinical utility, proven out-of-distribution transportability or production recovery-score readiness. The synthetic roots vary seeds within one generator, not populations sampled from reality. Cluster uncertainty relies on limited numbers of camps and specific resampling assumptions. Native study infrastructure supplies no empirical cohort or approvals. Manual NVDA acceptance remains outstanding; automated browser and CI checks cannot establish that human accessibility acceptance.

## 12. Research integrity and availability

Public v1.1.0 software is available at https://github.com/Litju/CMJRecoveryDynamicsBench/releases/tag/v1.1.0 under Apache-2.0. Source licensing does not grant redistribution rights to original checkpoints, fitted parameters or restricted scientific records. This manuscript stages public evidence separately from private verification metadata; all manuscript artifacts remain private pending owner approval. No external dataset was acquired, no checkpoints were modified and no model was trained for this work. Human authors must confirm accountability and all submission declarations; the software citation metadata is not treated as consent to manuscript authorship.

The historical public reproduction record used Python 3.12.13, NumPy 2.5.3 and Linux x86_64 without an accelerator. The fixed-mode receipt records stage-specific costs, including 566.6 s training generation and 209.6 s evaluation; these are historical host measurements, not portable performance guarantees. Current manuscript rendering and arithmetic checking use a separately recorded environment. We did not repeat the incidental release-qualification ridge fit, which supplies no manuscript result.

AI assistance: OpenAI Codex (GPT-6 agent environment) assisted evidence inspection, prose drafting, plotting code, arithmetic checks and document review. No finer model-build identity was exposed by the execution environment. Verification included original-artifact byte reconciliation, receipt arithmetic, primary-source citation checks and inspection of rendered outputs. Human authors must review every scientific assertion and accept responsibility before submission. No AI system is an author. Author identities, contributions, funding, conflicts and any institutional declarations require explicit human completion; no institutional approval is asserted here.

## 13. Conclusion

The defensible recovered object is a chain of qualified relationships among source, fitted artifacts, measurements and results. CMJRecoveryDynamicsBench preserves exact recorded CPU-source inference alongside failed historical CUDA comparisons and partial campaign recovery. Its separate public synthetic benchmark supports bounded same-generator diagnostics. The resulting evidence register, numerical qualification matrix and reproducible figures offer a practical reconstruction method without converting software execution into an unsupported claim of scientific or clinical validity.
