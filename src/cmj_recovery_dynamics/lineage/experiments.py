"""Study contexts and concise experiment protocols from M1 evidence."""

from cmj_recovery_dynamics.contracts import StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    BootstrapProtocol,
    ChangeClass,
    EvidenceConfidence,
    EvidenceReference,
    EvidenceStatus,
    ExperimentDefinition,
    ExperimentPurpose,
    ExperimentStatus,
    ProtocolUnit,
    ScientificDisposition,
    StudyLineage,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    FIXED_MODE_DISCREPANCY_EVALUATION,
    PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    POSTERIOR_ENERGY_DIFFERENCE_EVALUATION,
    POSTERIOR_ENERGY_RESEARCH_EVALUATION,
    PREDICTIVE_PROGRESS_EVALUATION,
    PROGRESS_RATIO_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    RELATIVE_PROGRESS_LOSS_EVALUATION,
    RICH_HISTORY_EVALUATION,
    THRESHOLD_RESPONSE_PROPOSED_EVALUATION,
)


def _evidence(*sources: str, note: str = "") -> EvidenceReference:
    return EvidenceReference(EvidenceStatus.DIRECT, tuple(sources), EvidenceConfidence.HIGH, note)


_INITIAL = "initial_preseason_camp_recovery"
_CANONICAL = "canonical_preseason_camp_recovery"
_RICH = "rich_history_camp_recovery"
_PRELIMINARY = "preliminary_post_exposure_recovery"
_PHASE = "phase_consistent_post_exposure_recovery"
_CORRELATED = "correlated_exposure_recovery"
_THRESHOLD = "threshold_response_recovery"
_FIXED = "fixed_mode_discrepancy_recovery"

_INITIAL_DATA = "initial_preseason_camp_public_sample"
_CANONICAL_DATA = "canonical_preseason_camp_horizon_sample"
_RICH_DATA = "rich_history_camp_sample"
_PRELIMINARY_DATA = "preliminary_episode_measurement_sample"
_PHASE_DATA = "phase_consistent_episode_sample"
_CORRELATED_DATA = "correlated_exposure_recovery_sample"
_THRESHOLD_DATA = "threshold_response_proposed_sample"
_FIXED_DATA = "fixed_mode_recovery_candidate_sample"
_FIXTURE_DATA = "initial_generator_fixture"
_SYSID_DATA = "manufactured_parameter_identification_histories"
_WHITE_DATA = "white_cmj_waveform_grounding_source"

_INITIAL_SPLIT = "initial_camp_public_validation"
_CANONICAL_SPLIT = "canonical_camp_public_validation"
_RICH_PUBLIC_SPLIT = "rich_history_public_validation"
_RICH_HIDDEN_SPLIT = "rich_history_original_hidden_bank"
_PRELIMINARY_SPLIT = "preliminary_episode_public_validation"
_PHASE_SPLIT = "phase_consistent_episode_public_validation"
_CORRELATED_SPLIT = "correlated_exposure_public_validation"
_THRESHOLD_SPLIT = "threshold_response_public_validation"
_FIXED_SPLIT = "fixed_mode_public_validation"
_SYSID_TRAIN_SPLIT = "identification_training_histories"
_SYSID_TEST_SPLIT = "identification_heldout_history_regimes"
_WHITE_TRAIN_SPLIT = "waveform_training_participants"
_WHITE_VALIDATION_SPLIT = "waveform_public_validation_participants"

_SRE6 = POST_EXPOSURE_RESEARCH_EVALUATION.name
_PROGRESS = PREDICTIVE_PROGRESS_EVALUATION.name
_PROGRESS_RATIO = PROGRESS_RATIO_EVALUATION.name
_PROGRESS_LOSS = RELATIVE_PROGRESS_LOSS_EVALUATION.name
_INITIAL_UNRESOLVED = "unresolved_initial_camp_platform_metric"
_QUALIFICATION = "public_synthetic_dataset_qualification"
_RICH_PROGRESS = "rich_history_raw_progress_diagnostic"
_SYSID_RMSE = "manufactured_posterior_parameter_point_rmse"
_WAVEFORM_RMSE = "white_waveform_participant_mean_rmse"
_OWNER_DECISION = "owner_program_adjudication"
_GROUNDING_STATUS = "real_data_recovery_crosswalk_status"
_HEADROOM = StudyType.PREDICTIVE_HEADROOM
_OBSERVABILITY = StudyType.OBSERVABILITY
_RECONSTRUCTABILITY = StudyType.RECONSTRUCTABILITY
_SYSTEM_IDENTIFICATION = StudyType.SYSTEM_IDENTIFICATION
_REAL_DATA_GROUNDING = StudyType.REAL_DATA_GROUNDING


ADJACENT_STUDIES = (
    StudyLineage(
        StudyType.PREDICTIVE_HEADROOM,
        "How much forecast headroom remains for a named task and evaluation?",
        (_RICH, _CORRELATED, _FIXED),
        (_RICH_DATA, _CORRELATED_DATA, _FIXED_DATA),
        (
            "Compare baselines, structured models, and legitimate "
            "empirical predictors within each fixed task and "
            "evaluation."
        ),
        _evidence("RES-366: headroom and result registry"),
    ),
    StudyLineage(
        StudyType.OBSERVABILITY,
        "Which dynamic states can be inferred from measurements and history?",
        (_PHASE, _CORRELATED, _FIXED),
        (_PHASE_DATA, _CORRELATED_DATA, _FIXED_DATA),
        (
            "Assess which target-relevant distinctions can be inferred "
            "from available histories; local forecast attacks are not "
            "latent-truth labels."
        ),
        _evidence("RES-366: observation inversion boundary"),
    ),
    StudyLineage(
        StudyType.RECONSTRUCTABILITY,
        "Can public inputs and outputs reconstruct the response or measurement law?",
        (_RICH, _PHASE, _CORRELATED, _FIXED),
        (_RICH_DATA, _PHASE_DATA, _CORRELATED_DATA, _FIXED_DATA),
        (
            "Assess public response-map reconstruction risk without "
            "treating it as a new benchmark formulation."
        ),
        _evidence("RES-366: reconstruction and attack boundary"),
    ),
    StudyLineage(
        StudyType.SYSTEM_IDENTIFICATION,
        "Which response parameters are identifiable under the declared observation/noise model?",
        (_FIXED,),
        (_SYSID_DATA,),
        (
            "A follow-up motivated by the fixed-mode candidate infers a "
            "posterior over four statistical sensitivity coordinates; "
            "it is a separate manufactured inverse problem, not "
            "recovery point forecasting."
        ),
        _evidence(
            "RES-361: preserved identification result output",
            "RES-366: system-identification study",
        ),
    ),
    StudyLineage(
        StudyType.REAL_DATA_GROUNDING,
        "How do synthetic recovery outcomes relate to empirical CMJ data and measurements?",
        (_INITIAL, _PRELIMINARY, _FIXED),
        (_WHITE_DATA,),
        (
            "Test whether empirical waveform evidence can be "
            "crosswalked to camp and post-exposure recovery targets; no "
            "T01/T02 crosswalk is established."
        ),
        EvidenceReference(
            EvidenceStatus.UNKNOWN,
            ("RES-363: task-linked real-data authority", "RES-366: grounding boundary study"),
            EvidenceConfidence.UNKNOWN,
            "The separate waveform analysis does not validate the synthetic recovery benchmark.",
        ),
    ),
)


def _experiment(
    name: str,
    question: str,
    dataset: str,
    splits: tuple[str, ...],
    evaluations: tuple[str, ...],
    purpose: ExperimentPurpose,
    status: ExperimentStatus,
    disposition: ScientificDisposition,
    decision: str,
    *,
    benchmark: str | None = None,
    study: StudyType | None = None,
    models: tuple[str, ...] = (),
    unit: ProtocolUnit = ProtocolUnit.CAMP,
    change: ChangeClass = ChangeClass.UNKNOWN,
    repetitions: int | None = None,
    seeds: tuple[int, ...] = (),
    bootstrap: BootstrapProtocol | None = None,
    folds: int | None = None,
    sources: tuple[str, ...] = ("RES-366: experiment protocol and result registry",),
    note: str = "",
) -> ExperimentDefinition:
    return ExperimentDefinition(
        name,
        question,
        benchmark,
        study,
        purpose,
        dataset,
        splits,
        models,
        evaluations,
        unit,
        status,
        disposition,
        decision,
        change,
        repetitions,
        seeds,
        bootstrap,
        folds,
        _evidence(*sources, note=note),
    )


_FIXED_BOOTSTRAP = BootstrapProtocol(ProtocolUnit.CAMP, 5000, 49505000, True, True)

EXPERIMENTS = (
    _experiment(
        "initial_camp_failure_certificate",
        (
            "Does the initial camp task support reliable public "
            "forecasting under its recovered evaluation?"
        ),
        _INITIAL_DATA,
        (_INITIAL_SPLIT,),
        (_INITIAL_UNRESOLVED,),
        ExperimentPurpose.NEGATIVE_RESULT,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_NEGATIVE,
        "Bound the original negative result to the initial formulation.",
        benchmark=_INITIAL,
        models=("initial_submission_family_unresolved",),
        unit=ProtocolUnit.PARTICIPANT,
        repetitions=5,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note=(
            "The reference was underfit and depth was an exact "
            "quasi-identifier; this result does not adjudicate later "
            "camp formulations."
        ),
    ),
    _experiment(
        "initial_generator_fixture_qualification",
        (
            "Does the small deterministic generation fixture satisfy "
            "the declared source and split checks?"
        ),
        _FIXTURE_DATA,
        ("generator_fixture_training", "generator_fixture_validation"),
        (_QUALIFICATION,),
        ExperimentPurpose.QUALIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_POSITIVE,
        "Validate the generator fixture only.",
        benchmark=_INITIAL,
        unit=ProtocolUnit.QUERY_ROW,
        change=ChangeClass.UNKNOWN,
        sources=(
            "RES-366: implementation and source qualification",
            "RES-365: fixture dataset lineage",
        ),
    ),
    _experiment(
        "initial_confirmatory_source_world_qualification",
        "Does the initial source/world qualify under the frozen confirmatory criteria?",
        _FIXTURE_DATA,
        ("generator_fixture_validation",),
        (_QUALIFICATION,),
        ExperimentPurpose.QUALIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_NEGATIVE,
        "Qualify source and world before predictive claims.",
        benchmark=_INITIAL,
        unit=ProtocolUnit.QUERY_ROW,
        note=(
            "Difficulty and heterogeneity criteria fail; "
            "signal/bootstrap evidence is inconclusive. The protocol "
            "amendment is separate and generated no new confirmatory "
            "result."
        ),
    ),
    _experiment(
        "initial_linear_public_baseline_evaluation",
        "How does the public linear baseline perform on initial-formulation validation?",
        _INITIAL_DATA,
        (_INITIAL_SPLIT,),
        (PUBLIC_REFERENCE_SELECTION_EVALUATION.name,),
        ExperimentPurpose.BASELINE_EVALUATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_POSITIVE,
        "Provide the initial public selection baseline.",
        benchmark=_INITIAL,
        models=("linear_public_baseline",),
        unit=ProtocolUnit.PARTICIPANT,
        change=ChangeClass.MODEL_ONLY_CHANGE,
    ),
    _experiment(
        "initial_public_reference_selection",
        "Which frozen reference candidate is selected under the two-seed public rule?",
        _INITIAL_DATA,
        (_INITIAL_SPLIT,),
        (PUBLIC_REFERENCE_SELECTION_EVALUATION.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_POSITIVE,
        "Select a public reference predictor.",
        benchmark=_INITIAL,
        models=("initial_public_reference_model",),
        unit=ProtocolUnit.PARTICIPANT,
        repetitions=2,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note="The two seed values are not recovered as a stable public configuration identity.",
    ),
    _experiment(
        "canonical_camp_public_campaign",
        "What scores were reported by the canonical camp public campaign?",
        _CANONICAL_DATA,
        (_CANONICAL_SPLIT,),
        (CANONICAL_PRESEASON_CAMP_EVALUATION.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_MIXED,
        "Record canonical-sample campaign outcomes without merging the initial result family.",
        benchmark=_CANONICAL,
        models=("canonical_campaign_predictor_unresolved",),
        unit=ProtocolUnit.PARTICIPANT,
        repetitions=5,
        change=ChangeClass.TRAINING_ONLY_CHANGE,
        note="Exact model, checkpoint, evaluation bank, and run configurations are unresolved.",
    ),
    _experiment(
        "rich_history_headroom_reconstruction",
        (
            "What structured predictive headroom is visible under the "
            "rich-history public and hidden result banks?"
        ),
        _RICH_DATA,
        (_RICH_PUBLIC_SPLIT, _RICH_HIDDEN_SPLIT),
        (_RICH_PROGRESS, RICH_HISTORY_EVALUATION.name),
        ExperimentPurpose.HEADROOM,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_POSITIVE,
        "Describe within-formulation headroom and preserve the split caveat.",
        benchmark=_RICH,
        study=_HEADROOM,
        models=(
            "rich_history_zero_baseline",
            "rich_history_reference_predictor",
            "rich_history_empirical_bayes_predictor",
            "rich_history_boosted_residual_predictor",
            "rich_history_headroom_reference",
        ),
        unit=ProtocolUnit.PARTICIPANT,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note=(
            "Public validation and original hidden-bank values remain "
            "separate; no pooling is supported."
        ),
    ),
    _experiment(
        "rich_history_gpu_frontier_reconstruction",
        (
            "Can historical GPU scores be reanchored for within-lane "
            "description without treating the transform as a benchmark "
            "score?"
        ),
        _RICH_DATA,
        (_RICH_PUBLIC_SPLIT,),
        (PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_MIXED,
        "Retain score transformations as compatibility evidence only.",
        benchmark=_RICH,
        study=_HEADROOM,
        models=("rich_history_gpu_frontier_unresolved",),
        unit=ProtocolUnit.UNKNOWN,
        repetitions=4,
        change=ChangeClass.COMPATIBILITY_ONLY,
        note=(
            "The first GPU terminal label was later rejected as a "
            "task-level verdict; the amended expert run was "
            "preparation-only."
        ),
    ),
    _experiment(
        "rich_history_final_expert_frontier_protocol",
        "Would the amended expert frontier change the rich-history headroom conclusion?",
        _RICH_DATA,
        (_RICH_PUBLIC_SPLIT,),
        (RICH_HISTORY_EVALUATION.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.PROPOSED_NOT_RUN,
        ScientificDisposition.NOT_ESTABLISHED,
        "Preserve the expert frontier as unrun preparation.",
        benchmark=_RICH,
        study=_HEADROOM,
        models=("planned_expert_reference_model",),
        unit=ProtocolUnit.PARTICIPANT,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        sources=("RES-366: V3 expert-frontier status",),
    ),
    _experiment(
        "phase_consistent_adversarial_survivability",
        (
            "Do structured and generic predictors outperform the "
            "observed-history baseline after the phase-consistent "
            "measurement repair?"
        ),
        _PHASE_DATA,
        (_PHASE_SPLIT,),
        (_SRE6,),
        ExperimentPurpose.FALSIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_NEGATIVE,
        "Test scalar-collapse and comparator/oracle assumptions before the correlated redesign.",
        benchmark=_PHASE,
        study=_RECONSTRUCTABILITY,
        models=("post_exposure_ridge_baseline", "restricted_post_exposure_empirical_frontier"),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note=(
            "Ridge outperformed the restricted frontier on the "
            "preserved validation comparison; this result belongs to "
            "the phase-consistent state."
        ),
    ),
    _experiment(
        "correlated_exposure_corrected_survivability",
        (
            "Does local reconstruction or scalar exposure compression "
            "outperform the empirical frontier under the correlated "
            "exposure distribution?"
        ),
        _CORRELATED_DATA,
        (_CORRELATED_SPLIT,),
        (_SRE6, _PROGRESS_RATIO, _PROGRESS_LOSS),
        ExperimentPurpose.FALSIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_MIXED,
        "Evaluate corrected comparator and oracle definitions on the correlated-exposure state.",
        benchmark=_CORRELATED,
        study=_RECONSTRUCTABILITY,
        models=(
            "local_history_structured_attacker",
            "correlated_exposure_empirical_frontier",
            "learned_one_dimensional_exposure_predictor",
        ),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        sources=(
            "ALI-507: authoritative final correlated-exposure result receipt",
            "RES-366: experiment protocol and result registry",
        ),
        note=(
            "ALI-507's terminal interpretation was "
            "RUNTIME_SCORER_REPAIR_REQUIRED; its scientific findings "
            "remain distinct from the later fixed-mode result."
        ),
    ),
    _experiment(
        "threshold_response_proposed_protocol",
        (
            "Does the proposed participant-weighted threshold response "
            "define a useful alternate benchmark?"
        ),
        _THRESHOLD_DATA,
        (_THRESHOLD_SPLIT,),
        (THRESHOLD_RESPONSE_PROPOSED_EVALUATION.name,),
        ExperimentPurpose.REDESIGN,
        ExperimentStatus.PROPOSED_NOT_RUN,
        ScientificDisposition.PROPOSED_ALTERNATE,
        "Represent a proposed alternate without implying acceptance or rejection.",
        benchmark=_THRESHOLD,
        change=ChangeClass.WORLD_CHANGE,
        sources=(
            "RES-364: proposed alternate genealogy",
            "RES-365: proposed data and evaluation contract",
        ),
    ),
    _experiment(
        "threshold_response_implementation_reference_attempt",
        (
            "Was a reference implementation and training attempt "
            "preserved for the proposed threshold response?"
        ),
        _THRESHOLD_DATA,
        (_THRESHOLD_SPLIT,),
        (THRESHOLD_RESPONSE_PROPOSED_EVALUATION.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.NOT_ESTABLISHED,
        "Record the implementation attempt without an accepted result or decision.",
        benchmark=_THRESHOLD,
        models=("threshold_response_reference_predictor",),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note=(
            "Model artifacts and training receipt exist in preserved "
            "evidence; no accepted evaluation survives."
        ),
    ),
    _experiment(
        "fixed_mode_public_dataset_qualification",
        (
            "Does the fixed-mode public dataset pass source, support, "
            "measurement, deterministic, and split-disjointness checks?"
        ),
        _FIXED_DATA,
        ("fixed_mode_training", _FIXED_SPLIT),
        (_QUALIFICATION,),
        ExperimentPurpose.DATA_QUALIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_POSITIVE,
        "Qualify public data only; do not infer model performance.",
        benchmark=_FIXED,
        unit=ProtocolUnit.CAMP,
        note=(
            "Train has 96 camps/24,000 participants/72,000 rows; public "
            "validation has 16 camps/4,000 participants/12,000 rows; no "
            "hidden challenge was materialized."
        ),
    ),
    _experiment(
        "fixed_mode_partial_headroom_attempt",
        "Can a first public headroom attempt complete the required model and split audit?",
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (_SRE6,),
        ExperimentPurpose.HEADROOM,
        ExperimentStatus.OPERATIONAL_FAILURE,
        ScientificDisposition.NOT_ESTABLISHED,
        "Keep runtime failures separate from scientific conclusions.",
        benchmark=_FIXED,
        study=_HEADROOM,
        models=(
            "local_history_structured_attacker",
            "generic_gradient_boosted_tree_predictor",
            "generic_multilayer_perceptron_predictor",
        ),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.TRAINING_ONLY_CHANGE,
        repetitions=2,
        note=(
            "Both result-bearing attempts ended before final scores, "
            "bootstrap, validation substitutions, and scientific "
            "adjudication."
        ),
    ),
    _experiment(
        "fixed_mode_stopped_replay",
        "Does the stopped partial replay produce an adjudicable scientific result?",
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (_SRE6,),
        ExperimentPurpose.HEADROOM,
        ExperimentStatus.CANCELED,
        ScientificDisposition.CANCELED,
        "Preserve the stopped replay as a separate operational record.",
        benchmark=_FIXED,
        study=_HEADROOM,
        models=(
            "generic_gradient_boosted_tree_predictor",
            "generic_multilayer_perceptron_predictor",
        ),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.RERUN_ONLY,
        note="The stopped attempt was excluded from the completed study adjudication.",
    ),
    _experiment(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        (
            "How much recoverable predictive performance remains, and "
            "can local history reconstruction match the empirical "
            "frontier?"
        ),
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (_SRE6, _PROGRESS_RATIO, _PROGRESS_LOSS),
        ExperimentPurpose.ADVERSARIAL_RECONSTRUCTION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.COMPLETED_MIXED,
        "Apply the frozen paired-camp thresholds and record the program pivot.",
        benchmark=_FIXED,
        study=_RECONSTRUCTABILITY,
        models=(
            "local_history_structured_attacker",
            "fixed_mode_empirical_bayes_predictor",
            "fixed_mode_nonlinear_mixed_effects_predictor",
            "fixed_mode_smooth_structured_predictor",
            "generic_ridge_predictor",
            "generic_gradient_boosted_tree_predictor",
            "generic_multilayer_perceptron_predictor",
            "learned_one_dimensional_exposure_predictor",
            "principal_component_exposure_diagnostic",
        ),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        repetitions=3,
        bootstrap=_FIXED_BOOTSTRAP,
        note=(
            "Five thousand paired resamples use all rows from each of "
            "16 validation camps; the production scorer remains "
            "unimplemented."
        ),
    ),
    _experiment(
        "fixed_mode_production_scorer_status",
        "Is an accepted production scorer available for the fixed-mode candidate?",
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (FIXED_MODE_DISCREPANCY_EVALUATION.name,),
        ExperimentPurpose.IMPLEMENTATION_VALIDATION,
        ExperimentStatus.BLOCKED,
        ScientificDisposition.NOT_ESTABLISHED,
        "Keep production scoring blocked until an accepted scorer exists.",
        benchmark=_FIXED,
        unit=ProtocolUnit.QUERY_ROW,
        note=(
            "The fail-closed production evaluation identity is "
            "unimplemented; research SRE6 is not a production scorer."
        ),
    ),
    _experiment(
        "fixed_mode_expert_reference_qualification",
        "Can an expert/reference predictor be qualified with an accepted production evaluation?",
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (FIXED_MODE_DISCREPANCY_EVALUATION.name,),
        ExperimentPurpose.REFERENCE_MODEL_EVALUATION,
        ExperimentStatus.PROPOSED_NOT_RUN,
        ScientificDisposition.NOT_ESTABLISHED,
        "Record the unrun expert/reference qualification.",
        benchmark=_FIXED,
        models=("planned_expert_reference_model",),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        note=(
            "No production expert/reference was trained; the forward "
            "redesign was stopped after the owner pivot."
        ),
    ),
    _experiment(
        "fixed_mode_owner_pivot_adjudication",
        "Do completed research diagnostics justify continuing forward recovery forecasting?",
        _FIXED_DATA,
        (_FIXED_SPLIT,),
        (_OWNER_DECISION,),
        ExperimentPurpose.REDESIGN,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.PROGRAM_PIVOT,
        "Apply frozen thresholds and record the research pivot.",
        benchmark=_FIXED,
        models=(
            "local_history_structured_attacker",
            "fixed_mode_nonlinear_mixed_effects_predictor",
        ),
        unit=ProtocolUnit.CAMP,
        change=ChangeClass.UNKNOWN,
        note=(
            "The owner decision pivoted to posterior system "
            "identification; forward redesign stopped. It is not a "
            "benchmark failure verdict."
        ),
    ),
    _experiment(
        "manufactured_parameter_system_identification",
        (
            "Can a posterior over four statistical exposure "
            "sensitivities be identified from K=2/4/8 complete noisy "
            "episodes, and does neural amortization improve on "
            "classical inference?"
        ),
        _SYSID_DATA,
        (_SYSID_TRAIN_SPLIT, _SYSID_TEST_SPLIT),
        (
            POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
            POSTERIOR_ENERGY_DIFFERENCE_EVALUATION.name,
            _SYSID_RMSE,
        ),
        ExperimentPurpose.SYSTEM_IDENTIFICATION,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.NOT_ML_TASK,
        (
            "Assess the posterior-inference proposal only; do not bind "
            "to force/impulse point forecasting."
        ),
        study=_SYSTEM_IDENTIFICATION,
        models=(
            "identification_prior_posterior",
            "identification_map_point_estimator",
            "identification_exact_analytic_posterior",
            "identification_empirical_bayes_posterior",
            "identification_amortized_neural_posterior",
        ),
        unit=ProtocolUnit.SYNTHETIC_HISTORY,
        repetitions=1,
        seeds=(522,),
        folds=4,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        sources=(
            "RES-361: preserved manufactured identification source and output",
            "RES-366: system-identification protocol and result registry",
            "RES-367: posterior energy evaluation identity",
        ),
        note=(
            "Posterior energy is prior-whitened; the separately "
            "reported parameter RMSE is raw-coordinate. The run does "
            "not falsify point-forecast tasks."
        ),
    ),
    _experiment(
        "white_waveform_feasibility_boundary",
        (
            "How well do classical and temporal-convolution models "
            "predict held-out empirical CMJ waveforms?"
        ),
        _WHITE_DATA,
        (_WHITE_TRAIN_SPLIT, _WHITE_VALIDATION_SPLIT),
        (_WAVEFORM_RMSE,),
        ExperimentPurpose.REAL_DATA_GROUNDING,
        ExperimentStatus.COMPLETED,
        ScientificDisposition.NOT_BENCHMARK_VALIDATION,
        "Record adjacent waveform-source feasibility without validating recovery forecasting.",
        study=_REAL_DATA_GROUNDING,
        models=(
            "white_waveform_classical_predictor",
            "white_waveform_temporal_convolutional_predictor",
        ),
        unit=ProtocolUnit.PARTICIPANT,
        repetitions=5,
        change=ChangeClass.MODEL_ONLY_CHANGE,
        sources=("RES-366: real-data boundary result registry",),
        note=(
            "The waveform task uses participant-level data and has no "
            "T01/T02 recovery source/split/scorer crosswalk."
        ),
    ),
    _experiment(
        "white_recovery_grounding_crosswalk",
        (
            "Can empirical waveform records be aligned to the recovery "
            "benchmark's longitudinal exposures, split, and "
            "force/impulse innovation targets?"
        ),
        _WHITE_DATA,
        (_WHITE_VALIDATION_SPLIT,),
        (_GROUNDING_STATUS,),
        ExperimentPurpose.REAL_DATA_GROUNDING,
        ExperimentStatus.UNKNOWN,
        ScientificDisposition.UNKNOWN,
        "Preserve the missing crosswalk as unknown.",
        study=_REAL_DATA_GROUNDING,
        unit=ProtocolUnit.PARTICIPANT,
        change=ChangeClass.UNKNOWN,
        sources=("RES-363: task-linked real-data authority", "RES-366: grounding boundary report"),
        note=(
            "No completed recovery-target crosswalk or benchmark "
            "evaluation is preserved; redistribution rights remain "
            "unresolved."
        ),
    ),
)


__all__ = ["ADJACENT_STUDIES", "EXPERIMENTS"]
