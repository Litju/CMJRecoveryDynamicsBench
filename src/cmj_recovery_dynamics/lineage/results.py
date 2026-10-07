"""Concise result families, comparability findings, and explicit conflicts."""

from cmj_recovery_dynamics.contracts import ComparabilityStatus
from cmj_recovery_dynamics.lineage.contracts import (
    ComparabilityConclusion,
    ConflictDefinition,
    CoordinateBasis,
    EvidenceConfidence,
    EvidenceReference,
    EvidenceStatus,
    PosteriorRMSETrace,
    ResultDefinition,
    ResultValue,
    ScientificDisposition,
    classify_posterior_rmse_trace,
)
from cmj_recovery_dynamics.metrics.catalog import (
    CANONICAL_PRESEASON_CAMP_EVALUATION,
    PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY,
    POST_EXPOSURE_RESEARCH_EVALUATION,
    POSTERIOR_ENERGY_DIFFERENCE_EVALUATION,
    POSTERIOR_ENERGY_RESEARCH_EVALUATION,
    PROGRESS_RATIO_EVALUATION,
    PUBLIC_REFERENCE_SELECTION_EVALUATION,
    RELATIVE_PROGRESS_LOSS_EVALUATION,
)


def _evidence(
    *sources: str,
    status: EvidenceStatus = EvidenceStatus.DIRECT,
    confidence: EvidenceConfidence = EvidenceConfidence.HIGH,
    note: str = "",
) -> EvidenceReference:
    return EvidenceReference(status, tuple(sources), confidence, note)


def _result(
    name: str,
    experiment: str,
    dataset: str,
    split: str,
    evaluation: str,
    summary: str,
    *,
    models: tuple[str, ...] = (),
    values: tuple[ResultValue, ...] = (),
    comparability: ComparabilityStatus = ComparabilityStatus.UNKNOWN,
    disposition: ScientificDisposition = ScientificDisposition.UNKNOWN,
    production: bool = False,
    evidence_status: EvidenceStatus = EvidenceStatus.DIRECT,
    sources: tuple[str, ...] = ("RES-366: result registry",),
    note: str = "",
) -> ResultDefinition:
    return ResultDefinition(
        name,
        experiment,
        models,
        dataset,
        split,
        evaluation,
        values,
        comparability,
        disposition,
        summary,
        _evidence(*sources, status=evidence_status, note=note),
        production,
    )


_INITIAL = "initial_preseason_camp_recovery"
_CANONICAL = "canonical_preseason_camp_recovery"
_RICH = "rich_history_camp_recovery"
_PHASE = "phase_consistent_post_exposure_recovery"
_CORRELATED = "correlated_exposure_recovery"
_FIXED = "fixed_mode_discrepancy_recovery"

_INITIAL_DATA = "initial_preseason_camp_public_sample"
_CANONICAL_DATA = "canonical_preseason_camp_horizon_sample"
_RICH_DATA = "rich_history_camp_sample"
_FIXTURE_DATA = "initial_generator_fixture"
_PHASE_DATA = "phase_consistent_episode_sample"
_CORRELATED_DATA = "correlated_exposure_recovery_sample"
_FIXED_DATA = "fixed_mode_recovery_candidate_sample"
_SYSID_DATA = "manufactured_parameter_identification_histories"
_WHITE_DATA = "white_cmj_waveform_grounding_source"

_RICH_RAW = "rich_history_raw_progress_diagnostic"
_SYSID_RMSE = "manufactured_posterior_parameter_point_rmse"
_WHITE_RMSE = "white_waveform_participant_mean_rmse"
_QUALIFICATION = "public_synthetic_dataset_qualification"
_OWNER_DECISION = "owner_program_adjudication"
_GROUNDING_STATUS = "real_data_recovery_crosswalk_status"

RESULTS = (
    _result(
        "initial_camp_negative_result_family",
        "initial_camp_failure_certificate",
        _INITIAL_DATA,
        "initial_camp_public_validation",
        "unresolved_initial_camp_platform_metric",
        (
            "Five initial-formulation attempts scored about 0.59–0.60 "
            "and failed the frozen PASS@5 decision; reference underfit "
            "and depth leakage were documented."
        ),
        models=("initial_submission_family_unresolved",),
        values=(
            ResultValue(
                "historical score range",
                "unresolved platform score",
                value_range=(0.59, 0.60),
                sample_count=5,
            ),
        ),
        disposition=ScientificDisposition.COMPLETED_NEGATIVE,
        evidence_status=EvidenceStatus.DIRECT,
        note=(
            "This negative result belongs only to the initial camp "
            "formulation; its exact production scorer binding remains "
            "unresolved."
        ),
    ),
    _result(
        "initial_generator_fixture_qualification_result",
        "initial_generator_fixture_qualification",
        _FIXTURE_DATA,
        "generator_fixture_validation",
        _QUALIFICATION,
        (
            "The deterministic generator fixture qualification passed; "
            "this is source validation, not benchmark performance."
        ),
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "initial_confirmatory_qualification_result",
        "initial_confirmatory_source_world_qualification",
        _FIXTURE_DATA,
        "generator_fixture_validation",
        _QUALIFICATION,
        (
            "Confirmatory qualification failed difficulty and "
            "heterogeneity criteria; signal/bootstrap evidence was "
            "inconclusive."
        ),
        disposition=ScientificDisposition.COMPLETED_NEGATIVE,
        note="This qualification result is not an overall benchmark-failure verdict.",
    ),
    _result(
        "initial_linear_public_baseline_result",
        "initial_linear_public_baseline_evaluation",
        _INITIAL_DATA,
        "initial_camp_public_validation",
        PUBLIC_REFERENCE_SELECTION_EVALUATION.name,
        "Public linear baseline under the four-cell training-scale selection metric.",
        models=("linear_public_baseline",),
        values=(
            ResultValue("aggregate normalized RMSE", "dimensionless", value=0.40366749638706456),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "initial_public_reference_selection_result",
        "initial_public_reference_selection",
        _INITIAL_DATA,
        "initial_camp_public_validation",
        PUBLIC_REFERENCE_SELECTION_EVALUATION.name,
        "The selected public reference has a two-seed mean selection error of 0.35931.",
        models=("initial_public_reference_model",),
        values=(
            ResultValue(
                "aggregate normalized RMSE",
                "dimensionless",
                value=0.35930952854248116,
                sample_count=2,
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "canonical_camp_public_campaign_result_family",
        "canonical_camp_public_campaign",
        _CANONICAL_DATA,
        "canonical_camp_public_validation",
        CANONICAL_PRESEASON_CAMP_EVALUATION.name,
        (
            "Five canonical-sample public campaign scores range from "
            "0.5176 to 0.5266; exact model and evaluation-bank "
            "associations remain unresolved."
        ),
        models=("canonical_campaign_predictor_unresolved",),
        values=(
            ResultValue(
                "calibrated benchmark score",
                "dimensionless",
                value_range=(0.5176, 0.5266),
                sample_count=5,
            ),
        ),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.COMPLETED_MIXED,
        production=True,
        note="This family is not directly comparable with the initial camp score family.",
    ),
    _result(
        "rich_history_zero_baseline_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_public_validation",
        _RICH_RAW,
        "Zero predictor raw progress on rich-history public validation.",
        models=("rich_history_zero_baseline",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.0),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "rich_history_empirical_bayes_public_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_public_validation",
        _RICH_RAW,
        "Structured empirical-Bayes raw progress on rich-history public validation.",
        models=("rich_history_empirical_bayes_predictor",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.7165342249074321),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "rich_history_boosted_residual_public_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_public_validation",
        _RICH_RAW,
        (
            "Structured predictor plus boosted residual raw progress on "
            "rich-history public validation."
        ),
        models=("rich_history_boosted_residual_predictor",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.7184639474288889),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "rich_history_headroom_public_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_public_validation",
        _RICH_RAW,
        "Research headroom reference raw progress on the public validation split.",
        models=("rich_history_headroom_reference",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.7216319938969343),),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "rich_history_headroom_hidden_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_original_hidden_bank",
        _RICH_RAW,
        "Research headroom reference raw progress on the original hidden-bank reproduction.",
        models=("rich_history_headroom_reference",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.6822285834382722),),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
        note=(
            "The hidden design is not a materialization claim; report "
            "this result separately and do not pool it with public "
            "validation."
        ),
    ),
    _result(
        "rich_history_reference_hidden_result",
        "rich_history_headroom_reconstruction",
        _RICH_DATA,
        "rich_history_original_hidden_bank",
        _RICH_RAW,
        "Historical reference raw progress on the original hidden-bank reproduction.",
        models=("rich_history_reference_predictor",),
        values=(ResultValue("raw progress", "dimensionless progress", value=0.6441322434740403),),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "rich_history_gpu_reanchored_result_family",
        "rich_history_gpu_frontier_reconstruction",
        _RICH_DATA,
        "rich_history_public_validation",
        PIECEWISE_LINEAR_REANCHOR_COMPATIBILITY.name,
        (
            "Four authored-GPU scores reanchor to approximately "
            "0.51845–0.57444; reanchoring changes score scale only."
        ),
        models=("rich_history_gpu_frontier_unresolved",),
        values=(
            ResultValue(
                "reanchored progress range",
                "dimensionless progress",
                value_range=(0.518449025523233, 0.5744433248809966),
                sample_count=4,
            ),
        ),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.COMPLETED_MIXED,
        evidence_status=EvidenceStatus.RECONSTRUCTED,
        note="The transform cannot align this result with canonical camp data or target banks.",
    ),
    _result(
        "phase_consistent_ridge_research_result",
        "phase_consistent_adversarial_survivability",
        "phase_consistent_episode_sample",
        "phase_consistent_episode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Ridge six-cell normalized RMSE in the phase-consistent study.",
        models=("post_exposure_ridge_baseline",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.727472),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_NEGATIVE,
    ),
    _result(
        "phase_consistent_restricted_frontier_research_result",
        "phase_consistent_adversarial_survivability",
        "phase_consistent_episode_sample",
        "phase_consistent_episode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Restricted empirical frontier six-cell normalized RMSE in the phase-consistent study.",
        models=("restricted_post_exposure_empirical_frontier",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.786234),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_NEGATIVE,
    ),
    _result(
        "correlated_exposure_sre6_result_family",
        "correlated_exposure_corrected_survivability",
        _CORRELATED_DATA,
        "correlated_exposure_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        (
            "Corrected correlated-exposure local and empirical result "
            "family; the exact result table is summarized without "
            "copying its historical payload."
        ),
        models=("local_history_structured_attacker", "correlated_exposure_empirical_frontier"),
        comparability=ComparabilityStatus.NON_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "correlated_exposure_local_frontier_ratio",
        "correlated_exposure_corrected_survivability",
        _CORRELATED_DATA,
        "correlated_exposure_public_validation",
        PROGRESS_RATIO_EVALUATION.name,
        "Corrected correlated-exposure local-to-empirical progress ratio from ALI-507.",
        models=("local_history_structured_attacker", "correlated_exposure_empirical_frontier"),
        values=(
            ResultValue(
                "local-to-frontier progress ratio",
                "dimensionless ratio",
                value=0.9977002240012199,
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
        sources=("ALI-507: authoritative final result receipt", "RES-366: result registry"),
        note=(
            "The paired SRE-difference interval is recorded separately; "
            "it is not uncertainty for this progress ratio."
        ),
    ),
    _result(
        "correlated_exposure_local_frontier_paired_sre_difference",
        "correlated_exposure_corrected_survivability",
        _CORRELATED_DATA,
        "correlated_exposure_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Paired local-history minus empirical-frontier six-cell SRE difference.",
        models=("local_history_structured_attacker", "correlated_exposure_empirical_frontier"),
        values=(
            ResultValue(
                "paired local-minus-empirical SRE difference (95% CI)",
                "dimensionless SRE difference",
                interval=(-0.0014055337702137793, 0.002354712208178295),
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
        sources=("ALI-507: authoritative final result receipt", "RES-366: result registry"),
        note=(
            "ALI-507 reports paired SRE(A4R) - SRE(STRONG_EMPIRICAL); "
            "this interval is not uncertainty for the separate progress ratio."
        ),
    ),
    _result(
        "correlated_exposure_scalar_progress_loss",
        "correlated_exposure_corrected_survivability",
        _CORRELATED_DATA,
        "correlated_exposure_public_validation",
        RELATIVE_PROGRESS_LOSS_EVALUATION.name,
        (
            "Full-to-best-scalar relative progress loss was about "
            "3.12%, below the frozen 5% threshold."
        ),
        models=(
            "correlated_exposure_empirical_frontier",
            "learned_one_dimensional_exposure_predictor",
        ),
        values=(ResultValue("relative progress loss", "fraction", value=0.031238600840498513),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_dataset_qualification_result",
        "fixed_mode_public_dataset_qualification",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        _QUALIFICATION,
        (
            "The public source and split passed the declared data "
            "qualification; this does not qualify a model."
        ),
        disposition=ScientificDisposition.COMPLETED_POSITIVE,
    ),
    _result(
        "fixed_mode_local_predictor_sre6",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        (
            "Best local structured predictor six-cell normalized RMSE "
            "in the completed fixed-mode study."
        ),
        models=("local_history_structured_attacker",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.641366),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_nonlinear_mixed_effects_sre6",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Best empirical nonlinear mixed-effects frontier six-cell normalized RMSE.",
        models=("fixed_mode_nonlinear_mixed_effects_predictor",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.641307),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_best_one_dimensional_sre6",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Best learned one-dimensional exposure predictor six-cell normalized RMSE.",
        models=("learned_one_dimensional_exposure_predictor",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.735083),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_generic_mlp_sre6",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Three-seed generic multilayer perceptron full-model six-cell normalized RMSE summary.",
        models=("generic_multilayer_perceptron_predictor",),
        values=(
            ResultValue(
                "six-cell normalized RMSE", "dimensionless", value=0.762320, sample_count=3
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_principal_component_diagnostic",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Principal-component exposure compression was diagnostic only, not a gate model.",
        models=("principal_component_exposure_diagnostic",),
        values=(ResultValue("six-cell normalized RMSE", "dimensionless", value=0.750521),),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_additional_model_family_results",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "Additional model results are grouped without row-level values.",
        models=(
            "fixed_mode_empirical_bayes_predictor",
            "fixed_mode_smooth_structured_predictor",
            "generic_ridge_predictor",
            "generic_gradient_boosted_tree_predictor",
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
        note="Model-to-experiment lineage is retained without copying the historical result table.",
    ),
    _result(
        "fixed_mode_local_to_frontier_ratio",
        "fixed_mode_completed_headroom_and_reconstruction_study",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        PROGRESS_RATIO_EVALUATION.name,
        "Local-to-empirical progress ratio under the paired validation-camp bootstrap.",
        models=(
            "local_history_structured_attacker",
            "fixed_mode_nonlinear_mixed_effects_predictor",
        ),
        values=(
            ResultValue(
                "local-to-frontier progress ratio",
                "dimensionless ratio",
                value=0.999835,
                interval=(0.998542, 1.001165),
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_MIXED,
    ),
    _result(
        "fixed_mode_owner_pivot_result",
        "fixed_mode_owner_pivot_adjudication",
        _FIXED_DATA,
        "fixed_mode_public_validation",
        _OWNER_DECISION,
        (
            "Owner applied the frozen research thresholds and pivoted "
            "to posterior system-identification research; forward "
            "redesign stopped."
        ),
        comparability=ComparabilityStatus.UNKNOWN,
        disposition=ScientificDisposition.PROGRAM_PIVOT,
    ),
    _result(
        "manufactured_prior_energy_scores",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        "Prior posterior energy scores across held-out K=2/4/8 history regimes.",
        models=("identification_prior_posterior",),
        values=(
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=1.322,
                stratum="history_count_2",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=1.323,
                stratum="history_count_4",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=1.323,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "manufactured_map_energy_scores",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        "MAP point energy scores across held-out K=2/4/8 history regimes.",
        models=("identification_map_point_estimator",),
        values=(
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=1.269,
                stratum="history_count_2",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.971,
                stratum="history_count_4",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.713,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "manufactured_exact_posterior_energy_scores",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        "Exact analytic posterior energy scores across held-out K=2/4/8 history regimes.",
        models=("identification_exact_analytic_posterior",),
        values=(
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.897,
                stratum="history_count_2",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.687,
                stratum="history_count_4",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.504,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "manufactured_empirical_bayes_energy_scores",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        "Empirical-Bayes posterior energy scores across held-out K=2/4/8 history regimes.",
        models=("identification_empirical_bayes_posterior",),
        values=(
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.902,
                stratum="history_count_2",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.690,
                stratum="history_count_4",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.506,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "manufactured_neural_posterior_energy_scores",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_RESEARCH_EVALUATION.name,
        "Weak amortized neural posterior energy scores across held-out K=2/4/8 history regimes.",
        models=("identification_amortized_neural_posterior",),
        values=(
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.925,
                stratum="history_count_2",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.728,
                stratum="history_count_4",
            ),
            ResultValue(
                "prior-whitened energy score",
                "dimensionless",
                value=0.550,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "manufactured_exact_posterior_raw_coordinate_rmse",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        _SYSID_RMSE,
        (
            "Exact posterior point RMSE is 0.372/0.284/0.207 over the "
            "four raw sensitivity coordinates for K=2/4/8."
        ),
        models=("identification_exact_analytic_posterior",),
        values=(
            ResultValue(
                "posterior point RMSE",
                "raw sensitivity-coordinate units",
                value=0.372,
                stratum="history_count_2",
            ),
            ResultValue(
                "posterior point RMSE",
                "raw sensitivity-coordinate units",
                value=0.284,
                stratum="history_count_4",
            ),
            ResultValue(
                "posterior point RMSE",
                "raw sensitivity-coordinate units",
                value=0.207,
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        disposition=ScientificDisposition.NOT_ML_TASK,
        sources=(
            "RES-361: preserved identification source and output",
            "RES-366: exact parameter-RMSE result rows",
            "RES-367: recorded metric conflict",
        ),
        note=(
            "The three history counts are separate regimes. The "
            "historical registry's prior-whitened unit label is "
            "resolved as raw-coordinate for these exact values."
        ),
    ),
    _result(
        "manufactured_neural_vs_exact_posterior_energy_difference",
        "manufactured_parameter_system_identification",
        "manufactured_parameter_identification_histories",
        "identification_heldout_history_regimes",
        POSTERIOR_ENERGY_DIFFERENCE_EVALUATION.name,
        (
            "The amortized neural posterior has higher energy-score "
            "loss than the exact posterior at every history count."
        ),
        models=(
            "identification_amortized_neural_posterior",
            "identification_exact_analytic_posterior",
        ),
        values=(
            ResultValue(
                "neural-minus-exact energy score",
                "dimensionless difference",
                value=0.0279,
                interval=(0.0244, 0.0319),
                stratum="history_count_2",
            ),
            ResultValue(
                "neural-minus-exact energy score",
                "dimensionless difference",
                value=0.0401,
                interval=(0.0358, 0.0442),
                stratum="history_count_4",
            ),
            ResultValue(
                "neural-minus-exact energy score",
                "dimensionless difference",
                value=0.0462,
                interval=(0.0422, 0.0502),
                stratum="history_count_8",
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.COMPLETED_NEGATIVE,
        sources=(
            "RES-361: preserved identification result output",
            "RES-366: system-identification result registry",
        ),
    ),
    _result(
        "white_waveform_classical_validation_rmse",
        "white_waveform_feasibility_boundary",
        _WHITE_DATA,
        "waveform_public_validation_participants",
        _WHITE_RMSE,
        (
            "Best classical participant-mean waveform validation RMSE "
            "on the separate empirical waveform task; terminal status was "
            "insufficient independent N and rankings were unstable."
        ),
        models=("white_waveform_classical_predictor",),
        values=(
            ResultValue(
                "participant-mean waveform RMSE", "body weights", value=0.4088, sample_count=9
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_BENCHMARK_VALIDATION,
    ),
    _result(
        "white_waveform_temporal_convolution_validation_rmse",
        "white_waveform_feasibility_boundary",
        _WHITE_DATA,
        "waveform_public_validation_participants",
        _WHITE_RMSE,
        (
            "Five-seed temporal-convolution participant-mean waveform "
            "validation RMSE on the separate empirical waveform task; "
            "terminal status was insufficient independent N and rankings were unstable."
        ),
        models=("white_waveform_temporal_convolutional_predictor",),
        values=(
            ResultValue(
                "participant-mean waveform RMSE", "body weights", value=0.4117, sample_count=9
            ),
        ),
        comparability=ComparabilityStatus.DIRECTLY_COMPARABLE,
        disposition=ScientificDisposition.NOT_BENCHMARK_VALIDATION,
    ),
    _result(
        "white_recovery_crosswalk_unresolved_result",
        "white_recovery_grounding_crosswalk",
        _WHITE_DATA,
        "waveform_public_validation_participants",
        _GROUNDING_STATUS,
        (
            "No preserved source/split/scorer crosswalk binds the "
            "empirical waveform task to T01/T02 recovery outcomes."
        ),
        comparability=ComparabilityStatus.NON_COMPARABLE,
        disposition=ScientificDisposition.UNKNOWN,
        evidence_status=EvidenceStatus.UNKNOWN,
        sources=("RES-363: task-linked real-data authority", "RES-366: grounding boundary report"),
    ),
)


COMPARABILITY_CONCLUSIONS = (
    ComparabilityConclusion(
        "initial_vs_canonical_camp_results",
        ("initial_camp_negative_result_family",),
        ("canonical_camp_public_campaign_result_family",),
        ComparabilityStatus.NON_COMPARABLE,
        "Different dataset/split and distinct scorer identity.",
        (
            "Shared camp task intent and similar score ranges do not "
            "align initial and canonical result families."
        ),
        _evidence(
            "RES-366: result comparability registry", "RES-367: evaluation comparison repairs"
        ),
    ),
    ComparabilityConclusion(
        "initial_public_baseline_vs_reference_selection",
        ("initial_linear_public_baseline_result",),
        ("initial_public_reference_selection_result",),
        ComparabilityStatus.DIRECTLY_COMPARABLE,
        "Same initial public validation split and four-cell training-scale selection metric.",
        (
            "The public linear baseline and selected reference use the "
            "same model-selection evaluation, not the hidden calibrated "
            "score."
        ),
        _evidence(
            "RES-366: model-selection result registry",
            "RES-367: public reference selection evaluation",
        ),
    ),
    ComparabilityConclusion(
        "rich_history_public_vs_hidden_bank",
        ("rich_history_headroom_public_result",),
        ("rich_history_headroom_hidden_result",),
        ComparabilityStatus.COMPARABLE_WITH_CAVEAT,
        "Same rich-history formulation and raw-progress equation; different target bank and split.",
        (
            "Report bank-specific results separately and do not pool "
            "public-validation and original hidden-bank values."
        ),
        _evidence(
            "RES-366: result comparability registry", "RES-367: rich-history scorer identity"
        ),
    ),
    ComparabilityConclusion(
        "correlated_exposure_vs_fixed_mode_research_results",
        ("correlated_exposure_sre6_result_family",),
        ("fixed_mode_local_predictor_sre6",),
        ComparabilityStatus.NON_COMPARABLE,
        (
            "Different generator/world and dataset identity despite "
            "sharing the six-cell research equation."
        ),
        (
            "The common research metric does not make "
            "correlated-exposure and fixed-mode results a paired "
            "comparison."
        ),
        _evidence(
            "RES-366: result comparability registry", "RES-367: post-exposure research metric"
        ),
    ),
    ComparabilityConclusion(
        "fixed_mode_local_vs_empirical_frontier",
        ("fixed_mode_local_predictor_sre6",),
        ("fixed_mode_nonlinear_mixed_effects_sre6",),
        ComparabilityStatus.DIRECTLY_COMPARABLE,
        "Same fixed-mode validation rows, six cells, research metric, and paired camp bootstrap.",
        (
            "Both models share 16 validation camps, 5,000 paired camp "
            "resamples, and the shared resample matrix."
        ),
        _evidence(
            "RES-366: completed-study protocol and result registry",
            "RES-367: SRE6 evaluation identity",
        ),
    ),
    ComparabilityConclusion(
        "fixed_mode_one_dimensional_vs_full_mlp",
        ("fixed_mode_best_one_dimensional_sre6",),
        ("fixed_mode_generic_mlp_sre6",),
        ComparabilityStatus.DIRECTLY_COMPARABLE,
        (
            "Same completed fixed-mode study, D09 validation, six "
            "cells, and paired bootstrap protocol."
        ),
        (
            "The learned one-dimensional model and full MLP were "
            "evaluated within the same completed study."
        ),
        _evidence(
            "RES-366: completed-study protocol and result registry",
            "RES-367: SRE6 evaluation identity",
        ),
    ),
    ComparabilityConclusion(
        "system_identification_vs_recovery_point_forecast",
        ("manufactured_exact_posterior_energy_scores",),
        ("fixed_mode_local_predictor_sre6",),
        ComparabilityStatus.NON_COMPARABLE,
        (
            "Posterior inference over statistical sensitivities versus "
            "force/impulse point forecasting."
        ),
        (
            "The manufactured law, estimand, output, dataset, and score "
            "differ; system identification is an adjacent study."
        ),
        _evidence(
            "RES-366: system-identification boundary and comparison registry",
            "RES-367: posterior energy evaluation",
        ),
    ),
    ComparabilityConclusion(
        "white_waveform_vs_recovery_benchmark",
        ("white_waveform_classical_validation_rmse",),
        ("fixed_mode_local_predictor_sre6",),
        ComparabilityStatus.NON_COMPARABLE,
        "Empirical waveform RMSE versus synthetic recovery force/impulse innovation SRE6.",
        (
            "No empirical-to-recovery crosswalk exists; the waveform "
            "result is grounding-boundary evidence only."
        ),
        _evidence("RES-366: White waveform boundary and comparison registry"),
    ),
    ComparabilityConclusion(
        "canonical_vs_rich_history_gpu_after_reanchoring",
        ("canonical_camp_public_campaign_result_family",),
        ("rich_history_gpu_reanchored_result_family",),
        ComparabilityStatus.NON_COMPARABLE,
        "Different world, dataset, observation surface, and evaluation target bank.",
        (
            "The compatibility transform changes score scale only and "
            "does not align benchmark identities."
        ),
        _evidence(
            "RES-366: historical GPU result registry", "RES-367: score reanchoring comparison"
        ),
    ),
)


POSTERIOR_RMSE_TRACE = PosteriorRMSETrace(
    result_identity="manufactured_exact_posterior_raw_coordinate_rmse",
    evaluator_reference=(
        "preserved posterior source `_summary` computes "
        "sqrt(mean((posterior_mean - truth) ** 2)) across raw "
        "sensitivity coordinates"
    ),
    source_output_reference=("Preserved `posterior.point_rmse` output for held-out K=2/4/8 cases."),
    configuration_identity=(
        "manufactured linear-Gaussian identification configuration with held-out seed 522"
    ),
    source_basis=CoordinateBasis.RAW_COORDINATE,
    same_result_binding=True,
    rounded_values_match=True,
)

POSTERIOR_RMSE_CONFLICT = ConflictDefinition(
    "posterior_point_rmse_coordinate_label",
    classify_posterior_rmse_trace(POSTERIOR_RMSE_TRACE),
    POSTERIOR_RMSE_TRACE,
    _evidence(
        "RES-361: preserved posterior source, configuration, and result output",
        "RES-366: exact posterior-RMSE result registry rows",
        "RES-367: recorded source/registry conflict",
        note=(
            "The registry's rounded values .372/.284/.207 match the preserved output field; "
            "the source expression averages unwhitened coordinate residuals. The result-row "
            "protocol key differs from the study summary key, so that metadata mismatch remains "
            "explicit while the exact source/config/result values resolve the metric label."
        ),
    ),
    (
        "Resolved to raw-coordinate RMSE for these exact result "
        "rows; the prior-whitened registry unit was a labeling "
        "error. Prior whitening is used by the separate "
        "energy-score evaluator."
    ),
)


__all__ = [
    "COMPARABILITY_CONCLUSIONS",
    "POSTERIOR_RMSE_CONFLICT",
    "POSTERIOR_RMSE_TRACE",
    "RESULTS",
]
