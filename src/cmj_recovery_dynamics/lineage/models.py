"""Scientific model families and evidence-bounded roles."""

from cmj_recovery_dynamics.contracts import StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    ArtifactAvailability,
    ArtifactReference,
    BenchmarkApplicability,
    ChangeClass,
    ConfigurationIdentity,
    ConfigurationStatus,
    EvidenceConfidence,
    EvidenceReference,
    EvidenceStatus,
    ModelFamily,
    ModelRole,
    RedistributionStatus,
)


def _evidence(*sources: str, note: str = "") -> EvidenceReference:
    return EvidenceReference(EvidenceStatus.DIRECT, tuple(sources), EvidenceConfidence.HIGH, note)


_MODEL_AUTHORITY = "RES-366: study, protocol, and result registries"
_UNKNOWN = "Exact architecture and hyperparameters are not established by the M1 authority."


def _model(
    name: str,
    architecture: str | None,
    roles: tuple[ModelRole, ...],
    benchmarks: tuple[str, ...],
    studies: tuple[StudyType, ...],
    objective: str,
    *,
    configuration: ConfigurationIdentity | None = None,
    config_status: ConfigurationStatus = ConfigurationStatus.UNKNOWN,
    checkpoint_status: ArtifactAvailability = ArtifactAvailability.UNKNOWN,
    checkpoint: ArtifactReference | None = None,
    introduction: ChangeClass = ChangeClass.MODEL_ONLY_CHANGE,
    sources: tuple[str, ...] = (_MODEL_AUTHORITY,),
    note: str = _UNKNOWN,
) -> ModelFamily:
    return ModelFamily(
        name=name,
        architecture=architecture,
        roles=roles,
        applicability=BenchmarkApplicability(benchmarks, studies),
        objective=objective,
        configuration=configuration,
        configuration_status=config_status,
        checkpoint_status=checkpoint_status,
        checkpoint=checkpoint,
        introduction_change=introduction,
        evidence=_evidence(*sources, note=note),
    )


_INITIAL = "initial_preseason_camp_recovery"
_CANONICAL = "canonical_preseason_camp_recovery"
_RICH = "rich_history_camp_recovery"
_PHASE = "phase_consistent_post_exposure_recovery"
_CORRELATED = "correlated_exposure_recovery"
_THRESHOLD = "threshold_response_recovery"
_FIXED = "fixed_mode_discrepancy_recovery"
_HEADROOM = StudyType.PREDICTIVE_HEADROOM
_OBSERVABILITY = StudyType.OBSERVABILITY
_RECONSTRUCTABILITY = StudyType.RECONSTRUCTABILITY
_SYSTEM_IDENTIFICATION = StudyType.SYSTEM_IDENTIFICATION
_REAL_DATA_GROUNDING = StudyType.REAL_DATA_GROUNDING


_PRESERVED_REFERENCE = ArtifactReference(
    "initial_public_reference_artifact",
    "reference model checkpoint metadata",
    ArtifactAvailability.PRESERVED_PRIVATELY,
    RedistributionStatus.UNRESOLVED,
)
_THRESHOLD_MODEL_ARTIFACT = ArtifactReference(
    "threshold_response_model_artifacts",
    "preserved model artifacts; exact checkpoint identity unresolved",
    ArtifactAvailability.PRESERVED_PRIVATELY,
    RedistributionStatus.UNRESOLVED,
)
_INITIAL_REFERENCE_CONFIGURATION = ConfigurationIdentity(
    "initial_public_reference_selection_configuration",
    ConfigurationStatus.PARTIALLY_SPECIFIED,
    ("Two-seed public selection; four-cell training-scale normalized RMSE.",),
    _evidence(
        "RES-366: public reference-selection protocol", "RES-367: model-selection evaluation"
    ),
)
_SYSID_EXACT_POSTERIOR_CONFIGURATION = ConfigurationIdentity(
    "manufactured_exact_linear_gaussian_posterior_configuration",
    ConfigurationStatus.IDENTIFIED,
    ("Exact posterior under the declared manufactured linear-Gaussian law.",),
    _evidence(
        "RES-361: preserved identification source and output",
        "RES-366: system-identification protocol",
    ),
)
_SYSID_EB_CONFIGURATION = ConfigurationIdentity(
    "manufactured_empirical_bayes_posterior_configuration",
    ConfigurationStatus.PARTIALLY_SPECIFIED,
    ("Empirical-Bayes fit used 512 separate histories.",),
    _evidence(
        "RES-361: preserved identification source and output",
        "RES-366: system-identification protocol",
    ),
)
_SYSID_NPE_CONFIGURATION = ConfigurationIdentity(
    "manufactured_amortized_neural_posterior_configuration",
    ConfigurationStatus.PARTIALLY_SPECIFIED,
    (
        "DeepSets episode/context encoders with a full-covariance Gaussian head.",
        "Training used 16,384 histories; exact remaining optimization settings stay unresolved.",
    ),
    _evidence(
        "RES-361: preserved identification source and output",
        "RES-366: system-identification protocol",
    ),
)

MODEL_FAMILIES = (
    _model(
        "initial_submission_family_unresolved",
        None,
        (ModelRole.UNKNOWN,),
        (_INITIAL,),
        (),
        "Historical task submission; scientific architecture and training objective unresolved.",
        sources=("RES-366: initial camp negative result",),
    ),
    _model(
        "linear_public_baseline",
        "linear regression",
        (ModelRole.PUBLIC_BASELINE,),
        (_INITIAL, _RICH),
        (),
        "Public-data point prediction of force and impulse innovations.",
        note=(
            "The linear baseline is named in the result registry; "
            "feature preprocessing details remain unresolved."
        ),
    ),
    _model(
        "initial_public_reference_model",
        None,
        (ModelRole.REFERENCE_MODEL,),
        (_INITIAL,),
        (),
        "Reference prediction selected under the public model-selection rule.",
        configuration=_INITIAL_REFERENCE_CONFIGURATION,
        config_status=ConfigurationStatus.PARTIALLY_SPECIFIED,
        checkpoint_status=ArtifactAvailability.PRESERVED_PRIVATELY,
        checkpoint=_PRESERVED_REFERENCE,
        note=(
            "A frozen reference artifact and two-seed selection result "
            "are preserved; architecture and complete configuration "
            "remain unknown."
        ),
    ),
    _model(
        "planned_expert_reference_model",
        None,
        (ModelRole.EXPERT_ORACLE_RESEARCH_MODEL,),
        (_FIXED, _RICH),
        (_HEADROOM,),
        "Planned expert/reference qualification; no recovered production evaluation was run.",
        checkpoint_status=ArtifactAvailability.NOT_APPLICABLE,
        introduction=ChangeClass.UNKNOWN,
        note=(
            "Expert/reference protocols are preparation-only or not "
            "run; this record preserves the unrun role without "
            "inventing a model implementation."
        ),
    ),
    _model(
        "canonical_campaign_predictor_unresolved",
        None,
        (ModelRole.UNKNOWN,),
        (_CANONICAL,),
        (),
        "Historical public point prediction; architecture and objective unresolved.",
        note=(
            "Five campaign scores survive, but their exact model, "
            "checkpoint, and configuration do not."
        ),
    ),
    _model(
        "rich_history_zero_baseline",
        "constant zero predictor",
        (ModelRole.NAIVE_BASELINE,),
        (_RICH,),
        (_HEADROOM,),
        "Predict zero innovation for every target cell.",
    ),
    _model(
        "rich_history_reference_predictor",
        None,
        (ModelRole.REFERENCE_MODEL,),
        (_RICH,),
        (_HEADROOM,),
        "Reference point prediction used in historical headroom reconstruction.",
        note="The reference result is identified; implementation and configuration are unresolved.",
    ),
    _model(
        "rich_history_empirical_bayes_predictor",
        "empirical-Bayes structured predictor",
        (ModelRole.EMPIRICAL_FRONTIER, ModelRole.LOCAL_STRUCTURED_PREDICTOR),
        (_RICH,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Estimate a structured population response and participant effects.",
        note=(
            "The empirical-Bayes family is named in the RES-366 result "
            "registry; exact fit configuration is unresolved."
        ),
    ),
    _model(
        "rich_history_boosted_residual_predictor",
        "empirical-Bayes predictor with gradient-boosted residual",
        (ModelRole.EMPIRICAL_FRONTIER, ModelRole.GENERIC_HIGH_CAPACITY_PREDICTOR),
        (_RICH,),
        (_HEADROOM,),
        "Add a boosted-tree residual to the structured empirical predictor.",
        note=(
            "The family-level result is identified; tree and residual "
            "hyperparameters are unresolved."
        ),
    ),
    _model(
        "rich_history_headroom_reference",
        None,
        (ModelRole.REFERENCE_MODEL,),
        (_RICH,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Research reference used to quantify public predictive headroom.",
        note=(
            "Public-validation and original hidden-bank outputs are "
            "identified; exact model construction is unresolved."
        ),
    ),
    _model(
        "rich_history_gpu_frontier_unresolved",
        None,
        (ModelRole.UNKNOWN,),
        (_RICH,),
        (_HEADROOM,),
        "Historical GPU frontier evaluation; model family is not resolved to architecture.",
        introduction=ChangeClass.TRAINING_ONLY_CHANGE,
        note=(
            "The GPU lane is a training/evaluation campaign under the "
            "same rich-history formulation; aliases and run names are "
            "provenance only."
        ),
    ),
    _model(
        "post_exposure_ridge_baseline",
        "ridge regression",
        (ModelRole.PUBLIC_BASELINE,),
        (_PHASE,),
        (_RECONSTRUCTABILITY,),
        "Predict the six force/impulse horizon targets from the episode query.",
        note=(
            "A ridge baseline is directly named in the completed "
            "phase-consistent study; regularization details are "
            "unresolved."
        ),
    ),
    _model(
        "restricted_post_exposure_empirical_frontier",
        None,
        (ModelRole.EMPIRICAL_FRONTIER,),
        (_PHASE,),
        (_RECONSTRUCTABILITY,),
        "Restricted empirical comparison frontier for the episode task.",
        note=(
            "The restricted frontier is a grouped result family; "
            "architecture and complete configuration are unresolved."
        ),
    ),
    _model(
        "local_history_structured_attacker",
        "participant-local response reconstruction from observed history",
        (ModelRole.LOCAL_STRUCTURED_PREDICTOR, ModelRole.RECONSTRUCTABILITY_ATTACK),
        (_PHASE, _CORRELATED, _FIXED),
        (_OBSERVABILITY, _RECONSTRUCTABILITY, _HEADROOM),
        (
            "Use an individual's observed episode history to estimate "
            "target-relevant response structure."
        ),
        note=(
            "Several local attack variants are grouped by scientific "
            "method; per-variant configuration is unresolved where the "
            "exact run contract is absent."
        ),
    ),
    _model(
        "correlated_exposure_empirical_frontier",
        None,
        (ModelRole.EMPIRICAL_FRONTIER,),
        (_CORRELATED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Train a legitimate empirical predictor under the correlated exposure distribution.",
        note=(
            "The frontier role is explicit; no architecture is inferred "
            "from the historical family label."
        ),
    ),
    _model(
        "fixed_mode_empirical_bayes_predictor",
        "structured empirical-Bayes predictor",
        (ModelRole.EMPIRICAL_FRONTIER, ModelRole.LOCAL_STRUCTURED_PREDICTOR),
        (_FIXED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Fit a structured population predictor with participant-level effects.",
        note=(
            "The family is named in the completed study; exact "
            "hyperparameters and checkpoint association are unresolved."
        ),
    ),
    _model(
        "fixed_mode_nonlinear_mixed_effects_predictor",
        "nonlinear mixed-effects predictor",
        (ModelRole.EMPIRICAL_FRONTIER, ModelRole.LOCAL_STRUCTURED_PREDICTOR),
        (_FIXED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Fit a nonlinear population response with local participant effects.",
        note=(
            "This was the best empirical frontier in the completed "
            "study; full configuration remains unresolved."
        ),
    ),
    _model(
        "fixed_mode_smooth_structured_predictor",
        "structured empirical-Bayes predictor with smooth residual features",
        (ModelRole.EMPIRICAL_FRONTIER, ModelRole.LOCAL_STRUCTURED_PREDICTOR),
        (_FIXED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Add smooth residual structure to an empirical-Bayes predictor.",
        note=(
            "The scientific family is identified; feature-map and "
            "regularization values are not bound to the completed "
            "result here."
        ),
    ),
    _model(
        "generic_ridge_predictor",
        "ridge regression",
        (ModelRole.GENERIC_PREDICTOR,),
        (_FIXED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Fit a general-purpose point predictor for the force and impulse targets.",
    ),
    _model(
        "generic_gradient_boosted_tree_predictor",
        "histogram-based gradient-boosted trees",
        (ModelRole.GENERIC_HIGH_CAPACITY_PREDICTOR,),
        (_RICH, _PHASE, _CORRELATED, _FIXED),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Fit a general-purpose nonlinear point predictor.",
        note=(
            "The model family is supported; run-specific "
            "hyperparameters are unresolved unless a separate "
            "configuration binding is recorded."
        ),
    ),
    _model(
        "generic_multilayer_perceptron_predictor",
        "multilayer perceptron",
        (ModelRole.GENERIC_HIGH_CAPACITY_PREDICTOR,),
        (_RICH, _PHASE, _CORRELATED, _FIXED),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Fit a general-purpose neural point predictor.",
        note=(
            "The model family is supported; run-specific "
            "hyperparameters and checkpoint identities remain "
            "unresolved."
        ),
    ),
    _model(
        "learned_one_dimensional_exposure_predictor",
        "learned scalar bottleneck over exposure inputs",
        (ModelRole.LEARNED_LOW_DIMENSIONAL_PREDICTOR,),
        (_CORRELATED, _FIXED),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Compress current and prior exposure inputs to a learned one-dimensional representation.",
        note=(
            "The one-dimensional family is a completed-study "
            "comparison; exact winning implementation identity is not "
            "carried into the public result family."
        ),
    ),
    _model(
        "principal_component_exposure_diagnostic",
        "first principal component of exposure inputs",
        (ModelRole.LEARNED_LOW_DIMENSIONAL_PREDICTOR,),
        (_FIXED,),
        (_HEADROOM, _RECONSTRUCTABILITY),
        "Measure one-dimensional exposure compression as a diagnostic only.",
        note="Diagnostic only; excluded from the best one-dimensional model and frozen gates.",
    ),
    _model(
        "threshold_response_reference_predictor",
        None,
        (ModelRole.REFERENCE_MODEL,),
        (_THRESHOLD,),
        (),
        "Reference-training attempt for a proposed high/low threshold-response formulation.",
        checkpoint_status=ArtifactAvailability.PRESERVED_PRIVATELY,
        checkpoint=_THRESHOLD_MODEL_ARTIFACT,
        introduction=ChangeClass.UNKNOWN,
        note=(
            "Implementation and model artifacts are reported, but no "
            "accepted evaluation or exact checkpoint/configuration "
            "association survives."
        ),
    ),
    _model(
        "identification_prior_posterior",
        "context-conditioned prior distribution over four response sensitivities",
        (ModelRole.NAIVE_BASELINE, ModelRole.PROBABILISTIC_POSTERIOR_ESTIMATOR),
        (),
        (_SYSTEM_IDENTIFICATION,),
        "Return the declared prior distribution without conditioning on episode history.",
        configuration=ConfigurationIdentity(
            "manufactured_sensitivity_prior_configuration",
            ConfigurationStatus.IDENTIFIED,
            ("Context-conditioned prior over four statistical exposure sensitivities.",),
            _evidence(
                "RES-361: preserved identification source and output",
                "RES-366: system-identification protocol",
            ),
        ),
        config_status=ConfigurationStatus.IDENTIFIED,
    ),
    _model(
        "identification_map_point_estimator",
        "maximum a posteriori point estimator",
        (ModelRole.PROBABILISTIC_POSTERIOR_ESTIMATOR,),
        (),
        (_SYSTEM_IDENTIFICATION,),
        "Return the posterior mode as a point estimate of the four statistical sensitivities.",
        configuration=ConfigurationIdentity(
            "manufactured_map_point_configuration",
            ConfigurationStatus.IDENTIFIED,
            ("Maximum a posteriori point estimate under the declared linear-Gaussian model.",),
            _evidence(
                "RES-361: preserved identification source and output",
                "RES-366: system-identification protocol",
            ),
        ),
        config_status=ConfigurationStatus.IDENTIFIED,
    ),
    _model(
        "identification_exact_analytic_posterior",
        "exact linear-Gaussian posterior via MAP and Laplace update",
        (ModelRole.PROBABILISTIC_POSTERIOR_ESTIMATOR, ModelRole.EXACT_ANALYTIC_REFERENCE),
        (),
        (_SYSTEM_IDENTIFICATION,),
        "Compute the exact posterior for the declared manufactured linear-Gaussian model.",
        configuration=_SYSID_EXACT_POSTERIOR_CONFIGURATION,
        config_status=ConfigurationStatus.IDENTIFIED,
        note=(
            "The result/source/config association is direct; inference "
            "does not establish biological parameter identification."
        ),
    ),
    _model(
        "identification_empirical_bayes_posterior",
        "empirical-Bayes Gaussian posterior estimator",
        (ModelRole.PROBABILISTIC_POSTERIOR_ESTIMATOR, ModelRole.EMPIRICAL_FRONTIER),
        (),
        (_SYSTEM_IDENTIFICATION,),
        "Estimate a context-conditioned posterior mean and covariance from separate histories.",
        configuration=_SYSID_EB_CONFIGURATION,
        config_status=ConfigurationStatus.PARTIALLY_SPECIFIED,
    ),
    _model(
        "identification_amortized_neural_posterior",
        "DeepSets posterior estimator with a full-covariance Gaussian head",
        (ModelRole.PROBABILISTIC_POSTERIOR_ESTIMATOR, ModelRole.GENERIC_HIGH_CAPACITY_PREDICTOR),
        (),
        (_SYSTEM_IDENTIFICATION,),
        "Approximate the manufactured posterior from complete episode histories.",
        configuration=_SYSID_NPE_CONFIGURATION,
        config_status=ConfigurationStatus.PARTIALLY_SPECIFIED,
        note=(
            "Architecture and training-set size are reported; "
            "checkpoint and full training configuration are not "
            "resolved as public artifacts."
        ),
    ),
    _model(
        "white_waveform_classical_predictor",
        "classical participant-mean waveform predictor",
        (ModelRole.PUBLIC_BASELINE,),
        (),
        (_REAL_DATA_GROUNDING,),
        "Predict the held-out vertical-force waveform from the separate empirical waveform task.",
        introduction=ChangeClass.MODEL_ONLY_CHANGE,
        note="This model is empirical waveform work and has no recovery-benchmark applicability.",
    ),
    _model(
        "white_waveform_temporal_convolutional_predictor",
        "temporal convolutional network",
        (ModelRole.GENERIC_HIGH_CAPACITY_PREDICTOR,),
        (),
        (_REAL_DATA_GROUNDING,),
        "Predict the separate empirical vertical-force waveform.",
        introduction=ChangeClass.TRAINING_ONLY_CHANGE,
        note=(
            "Five-seed waveform results are adjacent feasibility "
            "evidence, not recovery-benchmark validation."
        ),
    ),
)


__all__ = ["MODEL_FAMILIES"]
