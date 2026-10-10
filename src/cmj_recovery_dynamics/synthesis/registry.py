"""M6 synthesis composed only from the public M1-M5 authorities."""

from __future__ import annotations

from collections.abc import Sequence
from types import MappingProxyType

from cmj_recovery_dynamics.contracts import ComparabilityStatus, OptimizationDirection
from cmj_recovery_dynamics.lineage.contracts import (
    ResultValue,
)
from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY, get_result
from cmj_recovery_dynamics.model_reproduction.registry import (
    RESULT_REPRODUCTIONS,
    get_model_use_reproduction,
    get_result_reproduction,
    get_specimen_model_ladder,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY, get_evaluation
from cmj_recovery_dynamics.reproducibility.registry import (
    get_reproducibility_profiles,
)
from cmj_recovery_dynamics.reproduction.audit import FormulationReproducibility
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    ExperimentReconstruction,
    HistoricalGateState,
)
from cmj_recovery_dynamics.study_reconstruction.registry import (
    EXPERIMENT_RECONSTRUCTIONS,
    HISTORICAL_RULES,
    get_experiment_reconstruction,
    get_study_reconstruction,
)

from .contracts import (
    BenchmarkCharacterization,
    ComparativeEvidence,
    ConclusionStatus,
    ModelRoleEvidence,
    ProgramSynthesis,
    ScientificSynthesisClaim,
    StudyCharacterization,
    SynthesisAxis,
    SynthesisScope,
)

_PROFILES = {item.benchmark.name: item for item in get_reproducibility_profiles()}
_RESULTS = LINEAGE_REGISTRY.results
_EXPERIMENTS = LINEAGE_REGISTRY.experiments
_COMPARISONS = LINEAGE_REGISTRY.comparisons
_MODELS = LINEAGE_REGISTRY.model_families
_STUDIES = LINEAGE_REGISTRY.studies
_RULES = {item.name: item for item in HISTORICAL_RULES}
_BENCHMARK_NAMES = tuple(BENCHMARK_REGISTRY)
_ADJACENT_STUDY_NAMES = ("system_identification", "real_data_grounding")


def build_comparative_evidence(
    result_names: Sequence[str], *, comparison_name: str | None = None
) -> ComparativeEvidence:
    """Build fail-closed comparison evidence from M1 result identities."""
    names = tuple(result_names)
    if len(names) < 2 or len(names) != len(set(names)):
        raise ValueError("comparisons require at least two unique registered result identities")
    results = tuple(get_result(name) for name in names)
    statuses = tuple((item.name, item.comparability) for item in results)

    if comparison_name is not None:
        conclusion = _COMPARISONS[comparison_name]
        if set(names) != set((*conclusion.left_result_names, *conclusion.right_result_names)):
            raise ValueError(
                "result identities do not match the registered comparability conclusion"
            )
        return ComparativeEvidence(
            result_names=names,
            status=conclusion.status,
            comparison_name=conclusion.name,
            result_statuses=statuses,
        )

    if any(
        status in {ComparabilityStatus.NON_COMPARABLE, ComparabilityStatus.UNKNOWN}
        for _, status in statuses
    ):
        raise ValueError("registered result authority does not permit quantitative comparison")
    identities = {
        (
            result.experiment_name,
            result.dataset_name,
            result.split_name,
            result.evaluation_name,
        )
        for result in results
    }
    if len(identities) != 1:
        raise ValueError("results must share experiment, dataset, split, and evaluation identities")
    shared_identity = next(iter(identities))
    status = (
        ComparabilityStatus.COMPARABLE_WITH_CAVEAT
        if any(value is ComparabilityStatus.COMPARABLE_WITH_CAVEAT for _, value in statuses)
        else ComparabilityStatus.DIRECTLY_COMPARABLE
    )
    return ComparativeEvidence(
        result_names=names,
        status=status,
        shared_identity=shared_identity,
        result_statuses=statuses,
    )


def validate_synthesis_claim(claim: ScientificSynthesisClaim) -> None:
    """Validate all claim identities and comparison bindings against M1-M5."""
    if len(claim.benchmark_names) != len(set(claim.benchmark_names)):
        raise ValueError("benchmark evidence identities must be unique")
    if any(name not in BENCHMARK_REGISTRY for name in claim.benchmark_names):
        raise ValueError("synthesis claim references an unknown benchmark")
    if any(name not in _RESULTS for name in claim.result_names):
        raise ValueError("synthesis claim references an unknown result")
    if any(name not in _EXPERIMENTS for name in claim.experiment_names):
        raise ValueError("synthesis claim references an unknown experiment")
    if any(name not in _STUDIES for name in claim.study_names):
        raise ValueError("synthesis claim references an unknown adjacent study")
    if any(name not in _COMPARISONS for name in claim.comparison_names):
        raise ValueError("synthesis claim references an unknown comparability conclusion")
    if any(name not in _RULES for name in claim.historical_rule_names):
        raise ValueError("synthesis claim references an unknown historical decision rule")

    gates_by_experiment: dict[str, set[str]] = {
        reconstruction.experiment.name: {
            item.gate_name for item in reconstruction.historical_gate_outcomes
        }
        for reconstruction in EXPERIMENT_RECONSTRUCTIONS.values()
    }
    known_gates: set[str] = set()
    for gate_names in gates_by_experiment.values():
        known_gates.update(gate_names)
    if any(name not in known_gates for name in claim.gate_names):
        raise ValueError("synthesis claim references an unknown historical gate")
    allowed_gates: set[str] = set()
    for experiment_name in claim.experiment_names:
        allowed_gates.update(gates_by_experiment.get(experiment_name, set()))
    if any(name not in allowed_gates for name in claim.gate_names):
        raise ValueError("historical gate evidence is not bound to a named experiment")

    for name in claim.result_names:
        result = _RESULTS[name]
        if result.experiment_name not in claim.experiment_names:
            raise ValueError("every result must bind its registered experiment")
        experiment = _EXPERIMENTS[result.experiment_name]
        if (
            claim.scope is SynthesisScope.BENCHMARK
            and experiment.benchmark_name not in claim.benchmark_names
        ):
            raise ValueError("benchmark-scoped result belongs to a different benchmark")
        if claim.scope is SynthesisScope.STUDY and (
            experiment.study_type is None or experiment.study_type.value not in claim.study_names
        ):
            raise ValueError("study-scoped result belongs to a different study")

    for name in claim.experiment_names:
        experiment = _EXPERIMENTS[name]
        if (
            claim.scope is SynthesisScope.BENCHMARK
            and experiment.benchmark_name not in claim.benchmark_names
        ):
            raise ValueError("benchmark-scoped claim includes a different experiment")
        if claim.scope is SynthesisScope.STUDY and (
            experiment.benchmark_name is not None
            or experiment.study_type is None
            or experiment.study_type.value not in claim.study_names
        ):
            raise ValueError("adjacent-study experiments must remain outside benchmarks")

    for item in claim.model_roles:
        family = _MODELS.get(item.model_name)
        if family is None or family.roles != item.roles:
            raise ValueError("model-role evidence must match its registered M1 family roles")
    if claim.benchmark_names and claim.scope is SynthesisScope.BENCHMARK:
        if any(name not in claim.benchmark_names for name in claim.benchmark_names):
            raise ValueError("invalid benchmark scope")
    for name in claim.historical_rule_names:
        if _RULES[name].experiment_name not in claim.experiment_names:
            raise ValueError("historical rule evidence is not bound to a named experiment")
    for binding in claim.comparative_evidence:
        if (
            binding.comparison_name is not None
            and binding.comparison_name not in claim.comparison_names
        ):
            raise ValueError("comparative evidence conclusion is not named by the claim")
        expected = build_comparative_evidence(
            binding.result_names, comparison_name=binding.comparison_name
        )
        if binding != expected:
            raise ValueError("comparative evidence differs from registered M1 authority")


def _value(name: str, measure: str | None = None, *, stratum: str | None = None) -> ResultValue:
    result = _RESULTS[name]
    matches = tuple(
        item
        for item in result.values
        if (measure is None or item.measure == measure) and item.stratum == stratum
    )
    if len(matches) != 1:
        raise ValueError(f"result {name} does not have one matching registered value")
    return matches[0]


def _scalar(name: str, measure: str | None = None) -> float:
    value = _value(name, measure)
    if value.value is None:
        raise ValueError(f"result {name} does not contain a scalar value")
    return value.value


def _range(name: str) -> tuple[float, float]:
    value = _value(name)
    if value.value_range is None:
        raise ValueError(f"result {name} does not contain a registered range")
    return value.value_range


def _strata(name: str) -> tuple[tuple[str, float], ...]:
    result = _RESULTS[name]
    return tuple(
        (value.stratum or "", value.value) for value in result.values if value.value is not None
    )


def _roles(*model_names: str) -> tuple[ModelRoleEvidence, ...]:
    return tuple(ModelRoleEvidence(name, _MODELS[name].roles) for name in model_names)


def _claim(
    name: str,
    axis: SynthesisAxis,
    scope: SynthesisScope,
    status: ConclusionStatus,
    statement: str,
    *,
    benchmark_names: tuple[str, ...] = (),
    result_names: tuple[str, ...] = (),
    experiment_names: tuple[str, ...] = (),
    study_names: tuple[str, ...] = (),
    comparison_names: tuple[str, ...] = (),
    comparisons: tuple[tuple[tuple[str, ...], str | None], ...] = (),
    model_names: tuple[str, ...] = (),
    historical_rule_names: tuple[str, ...] = (),
    gate_names: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
) -> ScientificSynthesisClaim:
    bound_results = tuple(dict.fromkeys(result_names))
    bound_experiments = tuple(
        dict.fromkeys(
            (
                *experiment_names,
                *(_RESULTS[result].experiment_name for result in bound_results),
            )
        )
    )
    claim = ScientificSynthesisClaim(
        name=name,
        axis=axis,
        scope=scope,
        status=status,
        statement=statement,
        benchmark_names=benchmark_names,
        result_names=bound_results,
        experiment_names=bound_experiments,
        study_names=study_names,
        comparison_names=comparison_names,
        comparative_evidence=tuple(
            build_comparative_evidence(names, comparison_name=comparison)
            for names, comparison in comparisons
        ),
        model_roles=_roles(*model_names),
        historical_rule_names=historical_rule_names,
        gate_names=gate_names,
        limitations=limitations,
    )
    validate_synthesis_claim(claim)
    return claim


_INITIAL = "initial_preseason_camp_recovery"
_CANONICAL = "canonical_preseason_camp_recovery"
_RICH = "rich_history_camp_recovery"
_PRELIMINARY = "preliminary_post_exposure_recovery"
_PHASE = "phase_consistent_post_exposure_recovery"
_CORRELATED = "correlated_exposure_recovery"
_THRESHOLD = "threshold_response_recovery"
_FIXED = "fixed_mode_discrepancy_recovery"
_SYSID = "system_identification"
_WHITE = "real_data_grounding"
_ALL_BENCHMARKS = tuple(BENCHMARK_REGISTRY)

_INITIAL_LINEAR = "initial_linear_public_baseline_result"
_INITIAL_REFERENCE = "initial_public_reference_selection_result"
_INITIAL_NEGATIVE = "initial_camp_negative_result_family"
_INITIAL_QUALIFICATION = "initial_confirmatory_qualification_result"
_CANONICAL_RESULT = "canonical_camp_public_campaign_result_family"
_RICH_ZERO = "rich_history_zero_baseline_result"
_RICH_EB = "rich_history_empirical_bayes_public_result"
_RICH_BOOSTED = "rich_history_boosted_residual_public_result"
_RICH_PUBLIC_HEADROOM = "rich_history_headroom_public_result"
_RICH_HIDDEN_HEADROOM = "rich_history_headroom_hidden_result"
_RICH_HIDDEN_REFERENCE = "rich_history_reference_hidden_result"
_RICH_GPU = "rich_history_gpu_reanchored_result_family"
_PHASE_RIDGE = "phase_consistent_ridge_research_result"
_PHASE_FRONTIER = "phase_consistent_restricted_frontier_research_result"
_CORR_RATIO = "correlated_exposure_local_frontier_ratio"
_CORR_INTERVAL = "correlated_exposure_local_frontier_paired_sre_difference"
_CORR_SCALAR = "correlated_exposure_scalar_progress_loss"
_FIXED_LOCAL = "fixed_mode_local_predictor_sre6"
_FIXED_NLME = "fixed_mode_nonlinear_mixed_effects_sre6"
_FIXED_RATIO = "fixed_mode_local_to_frontier_ratio"
_FIXED_1D = "fixed_mode_best_one_dimensional_sre6"
_FIXED_MLP = "fixed_mode_generic_mlp_sre6"
_FIXED_PCA = "fixed_mode_principal_component_diagnostic"
_FIXED_OWNER = "fixed_mode_owner_pivot_result"
_SYSID_PRIOR = "manufactured_prior_energy_scores"
_SYSID_MAP = "manufactured_map_energy_scores"
_SYSID_EXACT = "manufactured_exact_posterior_energy_scores"
_SYSID_EB = "manufactured_empirical_bayes_energy_scores"
_SYSID_NEURAL = "manufactured_neural_posterior_energy_scores"
_SYSID_RMSE = "manufactured_exact_posterior_raw_coordinate_rmse"
_SYSID_DIFF = "manufactured_neural_vs_exact_posterior_energy_difference"
_WHITE_CLASSICAL = "white_waveform_classical_validation_rmse"
_WHITE_TCN = "white_waveform_temporal_convolution_validation_rmse"
_WHITE_CROSSWALK = "white_recovery_crosswalk_unresolved_result"

_PHASE_EXPERIMENT = "phase_consistent_adversarial_survivability"
_CORRELATED_EXPERIMENT = "correlated_exposure_corrected_survivability"
_THRESHOLD_PROTOCOL = "threshold_response_proposed_protocol"
_THRESHOLD_ATTEMPT = "threshold_response_implementation_reference_attempt"
_FIXED_QUALIFICATION = "fixed_mode_public_dataset_qualification"
_FIXED_STUDY = "fixed_mode_completed_headroom_and_reconstruction_study"
_FIXED_PIVOT = "fixed_mode_owner_pivot_adjudication"
_FIXED_SCORER = "fixed_mode_production_scorer_status"
_FIXED_EXPERT = "fixed_mode_expert_reference_qualification"
_SYSID_EXPERIMENT = "manufactured_parameter_system_identification"
_WHITE_EXPERIMENT = "white_waveform_feasibility_boundary"

_CROSS_CAMP = "initial_vs_canonical_camp_results"
_RICH_BANK_COMPARISON = "rich_history_public_vs_hidden_bank"
_CORR_FIXED_COMPARISON = "correlated_exposure_vs_fixed_mode_research_results"
_SYSID_RECOVERY_COMPARISON = "system_identification_vs_recovery_point_forecast"
_WHITE_RECOVERY_COMPARISON = "white_waveform_vs_recovery_benchmark"
_CANONICAL_GPU_COMPARISON = "canonical_vs_rich_history_gpu_after_reanchoring"
_INITIAL_MODEL_COMPARISON = "initial_public_baseline_vs_reference_selection"

_corr_rules = tuple(
    item.name for item in HISTORICAL_RULES if item.experiment_name == _CORRELATED_EXPERIMENT
)
_fixed_rules = tuple(item.name for item in HISTORICAL_RULES if item.experiment_name == _FIXED_STUDY)
_fixed_study_reconstruction = get_experiment_reconstruction(_FIXED_STUDY)
_fixed_pivot_reconstruction = get_experiment_reconstruction(_FIXED_PIVOT)
_fixed_pivot_decision = _fixed_pivot_reconstruction.decision
if _fixed_pivot_decision is None or _fixed_pivot_decision.benchmark_disposition is None:
    raise ValueError(
        "fixed-mode M4 authority must preserve the owner pivot and benchmark disposition"
    )
_fixed_pivot_disposition = _fixed_pivot_decision.benchmark_disposition
_threshold_protocol_reconstruction = get_experiment_reconstruction(_THRESHOLD_PROTOCOL)
_threshold_attempt_reconstruction = get_experiment_reconstruction(_THRESHOLD_ATTEMPT)
_sysid_reconstruction = get_experiment_reconstruction(_SYSID_EXPERIMENT)
_white_reconstruction = get_experiment_reconstruction(_WHITE_EXPERIMENT)
_initial_negative_replay = get_result_reproduction(_INITIAL_NEGATIVE)
_canonical_model_use = get_model_use_reproduction(
    "canonical_campaign_predictor_unresolved",
    _CANONICAL,
    "canonical_camp_public_campaign",
)


def _format(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}f}"


def _optimization_phrase(result_name: str) -> str:
    direction = get_evaluation(_RESULTS[result_name].evaluation_name).optimization_direction
    if direction is OptimizationDirection.LOWER_IS_BETTER:
        return "lower is better"
    if direction is OptimizationDirection.HIGHER_IS_BETTER:
        return "higher is better"
    raise ValueError(f"result {result_name} has no ranking direction")


def _history_scores(result_name: str) -> str:
    return ", ".join(
        f"{stratum.removeprefix('history_count_')}={value:.3f}"
        for stratum, value in _strata(result_name)
    )


def _sysid_energy_matrix() -> str:
    result_names = (_SYSID_PRIOR, _SYSID_MAP, _SYSID_EXACT, _SYSID_EB, _SYSID_NEURAL)
    score_rows = {name: dict(_strata(name)) for name in result_names}
    strata = tuple(stratum for stratum, _ in _strata(_SYSID_EXACT))
    return "; ".join(
        f"K={stratum.removeprefix('history_count_')}: "
        + ", ".join(
            f"{label}={score_rows[name][stratum]:.3f}"
            for label, name in (
                ("prior", _SYSID_PRIOR),
                ("MAP", _SYSID_MAP),
                ("exact", _SYSID_EXACT),
                ("EB", _SYSID_EB),
                ("neural", _SYSID_NEURAL),
            )
        )
        for stratum in strata
    )


def _sysid_energy_difference_summary() -> str:
    return ", ".join(
        f"{value.value:.4f} {value.interval}"
        for value in _RESULTS[_SYSID_DIFF].values
        if value.value is not None
    )


def _gate_sentence(reconstruction: ExperimentReconstruction) -> str:
    passed = tuple(
        item.gate_name
        for item in reconstruction.historical_gate_outcomes
        if item.state is HistoricalGateState.PASS
    )
    failed = tuple(
        item.gate_name
        for item in reconstruction.historical_gate_outcomes
        if item.state is HistoricalGateState.FAIL
    )
    return (
        f"The frozen historical protocol records {len(passed)} PASS gates ({', '.join(passed)}) "
        f"and {len(failed)} FAIL gates ({', '.join(failed)})."
    )


_initial_linear_value = _scalar(_INITIAL_LINEAR)
_initial_reference_value = _scalar(_INITIAL_REFERENCE)
_initial_negative_low, _initial_negative_high = _range(_INITIAL_NEGATIVE)
_canonical_low, _canonical_high = _range(_CANONICAL_RESULT)
_rich_eb_value = _scalar(_RICH_EB)
_rich_boosted_value = _scalar(_RICH_BOOSTED)
_rich_headroom_value = _scalar(_RICH_PUBLIC_HEADROOM)
_phase_ridge_value = _scalar(_PHASE_RIDGE)
_phase_frontier_value = _scalar(_PHASE_FRONTIER)
_correlated_loss = _scalar(_CORR_SCALAR)
_correlated_loss_rule = next(
    item for item in HISTORICAL_RULES if item.name == "correlated_scalar_progress_minimum"
)
_fixed_training_split = next(
    split
    for split in LINEAGE_REGISTRY.benchmark_view(_FIXED).splits
    if split.role.value == "TRAINING"
)
_fixed_validation_split = next(
    split
    for split in LINEAGE_REGISTRY.benchmark_view(_FIXED).splits
    if split.role.value == "PUBLIC_VALIDATION"
)
_rich_hidden_split = next(
    split
    for split in _PROFILES[_RICH].reproduction_contract.splits
    if split.role.value == "hidden_test"
)
_fixed_hidden_split = next(
    split
    for split in _PROFILES[_FIXED].reproduction_contract.splits
    if split.role.value == "hidden_test"
)
_fixed_production_status = _PROFILES[
    _FIXED
].reproduction_contract.evaluation.production_status.value.upper()
_threshold_hidden_split = next(
    split
    for split in _PROFILES[_THRESHOLD].reproduction_contract.splits
    if split.role.value == "hidden_test"
)
_sysid_terminal_decision = _sysid_reconstruction.decision
if _sysid_terminal_decision is None:
    raise ValueError("SYSID M4 authority must preserve its terminal decision")
_white_terminal_decision = _white_reconstruction.decision
if _white_terminal_decision is None:
    raise ValueError("White M4 authority must preserve its grounding boundary")
_benchmark_statuses = tuple(
    (name, _PROFILES[name].final_reproduction_audit.overall_status) for name in _ALL_BENCHMARKS
)
_benchmark_status_text = "; ".join(
    f"{name}: {status.value}" for name, status in _benchmark_statuses
)
_partial_benchmarks = tuple(
    name
    for name, status in _benchmark_statuses
    if status is FormulationReproducibility.PARTIALLY_REPRODUCIBLE
)
_semantic_benchmarks = tuple(
    name
    for name, status in _benchmark_statuses
    if status is FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
)
if any(status is FormulationReproducibility.EXACT for _, status in _benchmark_statuses):
    raise ValueError("M5 now contains an exact benchmark; review the M6 reproducibility synthesis")


_CLAIMS = (
    _claim(
        "program_cross_specimen_leaderboard_invalid",
        SynthesisAxis.PREDICTIVE_PERFORMANCE,
        SynthesisScope.PROGRAM,
        ConclusionStatus.UNRESOLVED,
        (
            "No valid cross-specimen model leaderboard exists: the benchmarks use "
            "different worlds, datasets, evaluation identities, target banks, and "
            "scientific questions. The eight specimens must not be averaged or ranked by "
            "difficulty."
        ),
        benchmark_names=_ALL_BENCHMARKS,
        result_names=(
            _INITIAL_NEGATIVE,
            _CANONICAL_RESULT,
            _CORR_RATIO,
            _FIXED_LOCAL,
            _SYSID_EXACT,
            _WHITE_CLASSICAL,
        ),
        study_names=(_SYSID, _WHITE),
        comparison_names=(
            _CROSS_CAMP,
            _CORR_FIXED_COMPARISON,
            _SYSID_RECOVERY_COMPARISON,
            _WHITE_RECOVERY_COMPARISON,
            _CANONICAL_GPU_COMPARISON,
        ),
        limitations=(
            (
                "The registered comparisons explicitly identify specimen pairs that are "
                "NON_COMPARABLE; no aggregate model score is scientifically "
                "defined."
            ),
        ),
    ),
    _claim(
        "initial_public_model_selection",
        SynthesisAxis.PREDICTIVE_PERFORMANCE,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED,
        (
            f"On the same initial public validation split and public model-selection metric, "
            f"the selected reference had normalized RMSE {_format(_initial_reference_value, 17)} "
            f"versus {_format(_initial_linear_value, 17)} for the linear public baseline; "
            f"{_optimization_phrase(_INITIAL_REFERENCE)}. This is not an exact historical "
            "benchmark-score replay."
        ),
        benchmark_names=(_INITIAL,),
        result_names=(_INITIAL_LINEAR, _INITIAL_REFERENCE),
        comparison_names=(_INITIAL_MODEL_COMPARISON,),
        comparisons=(((_INITIAL_LINEAR, _INITIAL_REFERENCE), _INITIAL_MODEL_COMPARISON),),
        model_names=("linear_public_baseline", "initial_public_reference_model"),
        limitations=(
            (
                "The conclusion applies only to the public model-selection metric and "
                "split, not to the unresolved historical platform "
                "score."
            ),
        ),
    ),
    _claim(
        "initial_historical_attempts_negative",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Five initial historical attempts scored about "
            f"{_initial_negative_low:.2f}–{_initial_negative_high:.2f} and were recorded "
            f"COMPLETED_NEGATIVE; M3 replay status is {_initial_negative_replay.status.value} "
            f"and numerical replay is {_initial_negative_replay.numerically_replayed}. "
            "Their values are not compared with the public model-selection results."
        ),
        benchmark_names=(_INITIAL,),
        result_names=(_INITIAL_NEGATIVE,),
        model_names=("initial_submission_family_unresolved",),
        limitations=(
            (
                "The exact production scorer binding is unresolved; the negative family "
                "uses a different metric authority from the public model-selection "
                "values."
            ),
        ),
    ),
    _claim(
        "initial_confirmatory_qualification_not_failure_verdict",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Initial confirmatory source/world qualification was negative or "
            "inconclusive on difficulty, heterogeneity, signal, and bootstrap criteria; "
            "this qualification is not a benchmark-failure "
            "verdict."
        ),
        benchmark_names=(_INITIAL,),
        result_names=(_INITIAL_QUALIFICATION,),
        limitations=(
            "This is source/world qualification evidence, not model-performance adjudication.",
        ),
    ),
    _claim(
        "initial_historical_replay_and_calibration_incomplete",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            f"The initial M2 formulation status is "
            f"{_PROFILES[_INITIAL].final_reproduction_audit.overall_status.value}; "
            "exact historical score replay is unavailable and the locked calibration "
            "reference is "
            f"{_PROFILES[_INITIAL].reproduction_contract.evaluation.calibration_reference_status.value}."
        ),
        benchmark_names=(_INITIAL,),
        result_names=(_INITIAL_NEGATIVE, _INITIAL_LINEAR, _INITIAL_REFERENCE),
        limitations=(
            (
                "The accepted scorer identity does not supply the unavailable locked "
                "calibration value or an exact historical result "
                "binding."
            ),
        ),
    ),
    _claim(
        "canonical_campaign_range_identity_unresolved",
        SynthesisAxis.PREDICTIVE_PERFORMANCE,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            f"The canonical public campaign outcome range is {_canonical_low:.4f}–"
            f"{_canonical_high:.4f} across five attempts. M3 configuration is "
            f"{_canonical_model_use.configuration_status.value}, checkpoint is "
            f"{_canonical_model_use.checkpoint_state.value}, and the evaluation-bank "
            "association remains unresolved, so this family cannot scientifically rank "
            "model families."
        ),
        benchmark_names=(_CANONICAL,),
        result_names=(_CANONICAL_RESULT,),
        model_names=("canonical_campaign_predictor_unresolved",),
        limitations=(
            (
                "These scores are not comparable with initial-campaign scores, and exact "
                "run/configuration associations are "
                "missing."
            ),
        ),
    ),
    _claim(
        "canonical_run_robustness_not_established",
        SynthesisAxis.ROBUSTNESS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.UNRESOLVED,
        (
            "The five canonical outcomes do not establish seed or run robustness because "
            "the individual run configurations and model/checkpoint associations are "
            "unresolved."
        ),
        benchmark_names=(_CANONICAL,),
        result_names=(_CANONICAL_RESULT,),
        limitations=(
            (
                "A narrow score range without identified run configurations is not a "
                "seed-robustness "
                "estimate."
            ),
        ),
    ),
    _claim(
        "rich_history_public_headroom",
        SynthesisAxis.PREDICTIVE_PERFORMANCE,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Within the rich-history public lane, structured empirical Bayes reached raw "
            f"progress {_rich_eb_value:.16f}, boosted residual reached "
            f"{_rich_boosted_value:.16f}, and the headroom reference reached "
            f"{_rich_headroom_value:.16f}. Structured empirical Bayes captured most "
            "observed public headroom; the boosted residual added only a small point gain "
            "on this lane."
        ),
        benchmark_names=(_RICH,),
        result_names=(_RICH_ZERO, _RICH_EB, _RICH_BOOSTED, _RICH_PUBLIC_HEADROOM),
        comparisons=(((_RICH_ZERO, _RICH_EB, _RICH_BOOSTED, _RICH_PUBLIC_HEADROOM), None),),
        model_names=(
            "rich_history_zero_baseline",
            "rich_history_empirical_bayes_predictor",
            "rich_history_boosted_residual_predictor",
            "rich_history_headroom_reference",
        ),
        limitations=(
            (
                "These are public raw-progress diagnostics from one lane; ‘small’ is not "
                "a universal threshold and the headroom reference carries caveated "
                "comparability."
            ),
        ),
    ),
    _claim(
        "rich_history_public_hidden_bank_separation",
        SynthesisAxis.ROBUSTNESS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The public headroom reference is "
            f"{_scalar(_RICH_PUBLIC_HEADROOM):.16f}; original hidden-bank headroom is "
            f"{_scalar(_RICH_HIDDEN_HEADROOM):.16f} and its historical reference is "
            f"{_scalar(_RICH_HIDDEN_REFERENCE):.16f}. These public and original "
            "hidden-bank results are preserved separately. The "
            f"hidden bank is {_rich_hidden_split.materialization_state.value.upper()}; "
            "its result values are not pooled with public "
            "validation and do not establish recovery of hidden "
            "bytes."
        ),
        benchmark_names=(_RICH,),
        result_names=(_RICH_PUBLIC_HEADROOM, _RICH_HIDDEN_HEADROOM, _RICH_HIDDEN_REFERENCE),
        comparison_names=(_RICH_BANK_COMPARISON,),
        limitations=(
            (
                "The public and hidden results use different target banks/splits; hidden "
                "bytes remain "
                "unrecovered."
            ),
        ),
    ),
    _claim(
        "rich_history_gpu_reanchoring_compatibility_only",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Historical GPU reanchoring is compatibility evidence only. It is not "
            "benchmark scoring and does not align the rich-history specimen with "
            "canonical-campaign "
            "results."
        ),
        benchmark_names=(_RICH,),
        result_names=(_RICH_GPU,),
        comparison_names=(_CANONICAL_GPU_COMPARISON,),
        limitations=(
            (
                "The explicit score transform changes scale but does not resolve model, "
                "dataset, or evaluation "
                "identity."
            ),
        ),
    ),
    _claim(
        "rich_history_expert_frontier_and_retirement_unresolved",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.UNRESOLVED,
        (
            "The final expert-frontier protocol remains PROPOSED_NOT_RUN; no final "
            "expert result or adjudication establishes the retirement "
            "rationale."
        ),
        benchmark_names=(_RICH,),
        experiment_names=("rich_history_final_expert_frontier_protocol",),
        model_names=("planned_expert_reference_model",),
        limitations=(
            (
                "The protocol-only reconstruction has no amended expert result or V3 "
                "retirement "
                "decision."
            ),
        ),
    ),
    _claim(
        "phase_consistent_ridge_beats_restricted_frontier",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED,
        (
            "In the completed phase-consistent study, ridge SRE6 was "
            f"{_phase_ridge_value:.6f} and the restricted frontier SRE6 was "
            f"{_phase_frontier_value:.6f}; "
            f"{_optimization_phrase(_PHASE_RIDGE)}. Ridge outperformed the "
            "restricted frontier for this specimen/protocol."
        ),
        benchmark_names=(_PHASE,),
        result_names=(_PHASE_RIDGE, _PHASE_FRONTIER),
        comparisons=(((_PHASE_RIDGE, _PHASE_FRONTIER), None),),
        model_names=("post_exposure_ridge_baseline", "restricted_post_exposure_empirical_frontier"),
        limitations=(
            (
                "The negative result does not adjudicate correlated-exposure or "
                "fixed-mode "
                "formulations."
            ),
        ),
    ),
    _claim(
        "correlated_exposure_local_reconstructability",
        SynthesisAxis.OBSERVABILITY_RECONSTRUCTABILITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Under the corrected correlated-exposure study, the local-history structured "
            "reconstruction reached a local-to-empirical progress ratio of "
            f"{_scalar(_CORR_RATIO):.16f}; its paired local-minus-empirical SRE6 95% "
            f"interval is {_value(_CORR_INTERVAL).interval}. This is close empirical-"
            "frontier reconstruction evidence, not evidence that a biological state was "
            "observable."
        ),
        benchmark_names=(_CORRELATED,),
        result_names=(_CORR_RATIO, _CORR_INTERVAL),
        experiment_names=(_CORRELATED_EXPERIMENT,),
        model_names=("local_history_structured_attacker", "correlated_exposure_empirical_frontier"),
        limitations=(
            (
                "The inference is limited to local forecast reconstruction under the "
                "corrected synthetic protocol; full model configurations and row-level "
                "scores are not "
                "published."
            ),
        ),
    ),
    _claim(
        "correlated_scalar_loss_below_historical_rule",
        SynthesisAxis.TASK_DESIGN_SENSITIVITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The full multidimensional exposure representation retained a relative "
            f"progress loss of {_correlated_loss:.18f} versus the best scalar "
            "representation. This is below the historical program rule of "
            f"{_correlated_loss_rule.threshold:.2f}; the rule is historical, not a "
            "universal scientific requirement."
        ),
        benchmark_names=(_CORRELATED,),
        result_names=(_CORR_SCALAR,),
        experiment_names=(_CORRELATED_EXPERIMENT,),
        model_names=(
            "correlated_exposure_empirical_frontier",
            "learned_one_dimensional_exposure_predictor",
        ),
        historical_rule_names=("correlated_scalar_progress_minimum",),
        limitations=(
            (
                "The frozen 5% rule records the historical decision and is not a "
                "universal minimum effect "
                "size."
            ),
        ),
    ),
    _claim(
        "correlated_terminal_runtime_repair_required",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The correlated study terminal state is RUNTIME_SCORER_REPAIR_REQUIRED. It "
            "is not converted into benchmark PASS or FAIL, and correlated results remain "
            "NON_COMPARABLE with fixed-mode "
            "results."
        ),
        benchmark_names=(_CORRELATED,),
        result_names=(_CORR_RATIO,),
        experiment_names=(_CORRELATED_EXPERIMENT,),
        comparison_names=(_CORR_FIXED_COMPARISON,),
        limitations=(
            (
                "The runtime scorer must be repaired before benchmark-level "
                "adjudication; the shared SRE6 name does not make formulations "
                "comparable."
            ),
        ),
    ),
    _claim(
        "threshold_response_proposed_unadjudicated",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.UNRESOLVED,
        (
            f"The threshold protocol is {_EXPERIMENTS[_THRESHOLD_PROTOCOL].status.value} "
            f"with disposition {_EXPERIMENTS[_THRESHOLD_PROTOCOL].disposition.value}; "
            "M4 result authority is "
            f"{_threshold_protocol_reconstruction.result_authority.value}. "
            "The implementation/reference attempt is "
            f"{_EXPERIMENTS[_THRESHOLD_ATTEMPT].status.value} with disposition "
            f"{_EXPERIMENTS[_THRESHOLD_ATTEMPT].disposition.value}; M4 authority is "
            "M4 result authority is "
            f"{_threshold_attempt_reconstruction.result_authority.value}. "
            "Threshold response "
            "is a proposed alternate with implementation evidence, not a validated or "
            "rejected benchmark formulation; no predictive-quality ranking is supported."
        ),
        benchmark_names=(_THRESHOLD,),
        experiment_names=(_THRESHOLD_PROTOCOL, _THRESHOLD_ATTEMPT),
        model_names=("threshold_response_reference_predictor",),
        limitations=(
            (
                "No accepted benchmark result or acceptance/rejection adjudication "
                "exists; NOT_ESTABLISHED is not a negative scientific "
                "result."
            ),
        ),
    ),
    _claim(
        "fixed_mode_public_data_qualification",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            f"Fixed-mode public qualification covers training {_fixed_training_split.camps} "
            f"camps, {_fixed_training_split.participants} participants, "
            f"{_fixed_training_split.rows} rows and validation "
            f"{_fixed_validation_split.camps} camps, "
            f"{_fixed_validation_split.participants} participants, "
            f"{_fixed_validation_split.rows} rows. This qualifies public data/source only, "
            "not benchmark performance."
        ),
        benchmark_names=(_FIXED,),
        experiment_names=(_FIXED_QUALIFICATION,),
        limitations=(
            "No hidden challenge was materialized, and production scoring remains unimplemented.",
        ),
    ),
    _claim(
        "fixed_mode_within_study_model_behavior",
        SynthesisAxis.STRUCTURED_VS_LEARNED,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Within the completed fixed-mode study, local structured SRE6="
            f"{_scalar(_FIXED_LOCAL):.6f}, nonlinear mixed-effects SRE6="
            f"{_scalar(_FIXED_NLME):.6f}, learned 1-D SRE6={_scalar(_FIXED_1D):.6f}, "
            f"generic MLP SRE6={_scalar(_FIXED_MLP):.6f}, and PCA diagnostic SRE6="
            f"{_scalar(_FIXED_PCA):.6f} ({_optimization_phrase(_FIXED_LOCAL)}). "
            "Local structured and "
            "nonlinear mixed-effects approaches outperformed the reported generic MLP "
            "and learned 1-D result; the learned 1-D model outperformed the full MLP. "
            "Higher capacity did not produce a monotonic advantage in this specimen."
        ),
        benchmark_names=(_FIXED,),
        result_names=(_FIXED_LOCAL, _FIXED_NLME, _FIXED_1D, _FIXED_MLP, _FIXED_PCA),
        experiment_names=(_FIXED_STUDY,),
        comparisons=(((_FIXED_LOCAL, _FIXED_NLME, _FIXED_1D, _FIXED_MLP, _FIXED_PCA), None),),
        model_names=(
            "local_history_structured_attacker",
            "fixed_mode_nonlinear_mixed_effects_predictor",
            "learned_one_dimensional_exposure_predictor",
            "generic_multilayer_perceptron_predictor",
            "principal_component_exposure_diagnostic",
        ),
        limitations=(
            (
                "This is a specimen-specific research study and does not establish "
                "universal structured-model superiority or production "
                "performance."
            ),
        ),
    ),
    _claim(
        "fixed_mode_frontier_and_historical_gate_pivot",
        SynthesisAxis.ROBUSTNESS,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The local-to-empirical progress ratio is "
            f"{_scalar(_FIXED_RATIO):.6f} with 95% CI "
            f"{_value(_FIXED_RATIO).interval}. The study is "
            f"{_fixed_study_reconstruction.experiment.status.value} with result authority "
            f"{_fixed_study_reconstruction.result_authority.value} and protocol "
            f"{_fixed_study_reconstruction.protocol_completeness.value}. "
            f"{_gate_sentence(_fixed_study_reconstruction)} The owner decision is "
            f"{_fixed_pivot_decision.outcome.value} and keeps the "
            "benchmark disposition "
            f"{_fixed_pivot_disposition.value}; "
            "the pivot was a research-program decision, not a benchmark-failure verdict."
        ),
        benchmark_names=(_FIXED,),
        result_names=(_FIXED_LOCAL, _FIXED_NLME, _FIXED_RATIO, _FIXED_OWNER),
        experiment_names=(_FIXED_STUDY, _FIXED_PIVOT),
        comparisons=(((_FIXED_LOCAL, _FIXED_NLME), None),),
        model_names=(
            "local_history_structured_attacker",
            "fixed_mode_nonlinear_mixed_effects_predictor",
        ),
        gate_names=tuple(
            item.gate_name for item in _fixed_study_reconstruction.historical_gate_outcomes
        ),
        historical_rule_names=tuple(
            item.name for item in HISTORICAL_RULES if item.experiment_name == _FIXED_PIVOT
        ),
        limitations=(
            (
                "The 8 PASS/4 FAIL matrix applies to its frozen historical research "
                "protocol; it is not a production robustness certification or benchmark "
                "PASS/FAIL."
            ),
        ),
    ),
    _claim(
        "fixed_mode_scorer_and_expert_qualification_unresolved",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.UNRESOLVED,
        (
            "The fixed-mode production scorer is "
            f"{_fixed_production_status}; "
            f"expert/reference qualification is {_EXPERIMENTS[_FIXED_EXPERT].status.value}. "
            "The benchmark "
            f"remains {_fixed_pivot_disposition.value}."
        ),
        benchmark_names=(_FIXED,),
        experiment_names=(_FIXED_SCORER, _FIXED_EXPERT, _FIXED_PIVOT),
        limitations=(
            (
                "The production scorer is unimplemented and expert/reference "
                "qualification was not "
                "run."
            ),
        ),
    ),
    _claim(
        "preliminary_model_performance_unresolved",
        SynthesisAxis.PREDICTIVE_PERFORMANCE,
        SynthesisScope.BENCHMARK,
        ConclusionStatus.UNRESOLVED,
        (
            "No independent baseline/reference result or completed model ladder is bound "
            "to the preliminary post-exposure benchmark; model performance remains "
            "unresolved."
        ),
        benchmark_names=(_PRELIMINARY,),
        limitations=("M3 records no bound model result for this benchmark.",),
    ),
    _claim(
        "sysid_history_improves_manufactured_inference",
        SynthesisAxis.OBSERVABILITY_RECONSTRUCTABILITY,
        SynthesisScope.STUDY,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "In the manufactured system-identification inverse problem, exact-posterior "
            f"energy scores across history K=2/4/8 were {_history_scores(_SYSID_EXACT)} "
            "and raw sensitivity-coordinate point RMSEs were "
            f"{_history_scores(_SYSID_RMSE)}. Increasing complete episode history "
            f"improved posterior concentration/performance within this problem; "
            f"the terminal decision is {_sysid_terminal_decision.outcome.value}."
        ),
        result_names=(_SYSID_EXACT, _SYSID_RMSE),
        study_names=(_SYSID,),
        model_names=("identification_exact_analytic_posterior",),
        limitations=(
            (
                "This is information/identifiability evidence in a manufactured inverse "
                "problem, not recovery-forecasting sample efficiency or biological "
                "parameter "
                "identification."
            ),
        ),
    ),
    _claim(
        "sysid_classical_inference_beats_neural_amortization",
        SynthesisAxis.STRUCTURED_VS_LEARNED,
        SynthesisScope.STUDY,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Registered prior/MAP/exact/empirical-Bayes/neural energy scores are "
            f"{_sysid_energy_matrix()}. Across K=2/4/8, neural-minus-exact differences "
            "and 95% intervals are "
            f"{_sysid_energy_difference_summary()}; "
            "each interval is positive. Exact analytic and empirical-Bayes inference "
            f"outperformed amortized neural inference ({_optimization_phrase(_SYSID_EXACT)}) "
            "under this study's energy score."
        ),
        result_names=(
            _SYSID_PRIOR,
            _SYSID_MAP,
            _SYSID_EXACT,
            _SYSID_EB,
            _SYSID_NEURAL,
            _SYSID_DIFF,
        ),
        study_names=(_SYSID,),
        comparisons=(((_SYSID_EXACT, _SYSID_EB, _SYSID_NEURAL), None),),
        model_names=(
            "identification_exact_analytic_posterior",
            "identification_empirical_bayes_posterior",
            "identification_amortized_neural_posterior",
        ),
        limitations=(
            (
                "The terminal decision is NOT_ML_TASK for this manufactured proposal and "
                "cannot establish recovery-forecasting impossibility or falsify "
                "T02."
            ),
        ),
    ),
    _claim(
        "sysid_terminal_not_ml_task_boundary",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.STUDY,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            f"The manufactured system-identification proposal ended "
            f"{_sysid_terminal_decision.outcome.value}. It is a "
            "separate inverse problem and does not establish that recovery forecasting "
            "is impossible, falsify T02, or identify biological sensitivity "
            "parameters."
        ),
        result_names=(_SYSID_EXACT, _SYSID_NEURAL),
        experiment_names=(_SYSID_EXPERIMENT,),
        study_names=(_SYSID,),
        limitations=(
            "The decision is confined to the declared manufactured posterior-inference task.",
        ),
    ),
    _claim(
        "white_waveform_rank_is_unstable",
        SynthesisAxis.ROBUSTNESS,
        SynthesisScope.STUDY,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            f"On White public validation with N={_value(_WHITE_CLASSICAL).sample_count}, "
            f"classical waveform RMSE was {_scalar(_WHITE_CLASSICAL):.4f} body weights "
            f"and TCN RMSE was {_scalar(_WHITE_TCN):.4f}. The study reports insufficient "
            "independent N and unstable rankings, so no stable classical-versus-TCN "
            f"superiority is supported despite the point estimates; M4 outcome is "
            f"{_white_terminal_decision.outcome.value}."
        ),
        result_names=(_WHITE_CLASSICAL, _WHITE_TCN),
        study_names=(_WHITE,),
        comparisons=(((_WHITE_CLASSICAL, _WHITE_TCN), None),),
        model_names=(
            "white_waveform_classical_predictor",
            "white_waveform_temporal_convolutional_predictor",
        ),
        limitations=(
            (
                "White is adjacent empirical waveform feasibility evidence and is not "
                "recovery-benchmark "
                "validation."
            ),
        ),
    ),
    _claim(
        "recovery_empirical_grounding_unresolved",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.UNRESOLVED,
        (
            "Empirical grounding of the recovery benchmarks remains unresolved: White "
            "waveform evidence is a separate task, and no source/split/scorer crosswalk "
            "binds it to T01/T02 recovery outcomes. The synthetic recovery program is "
            "neither empirically validated nor empirically invalidated by this "
            "boundary."
        ),
        benchmark_names=(_INITIAL, _PRELIMINARY, _FIXED),
        result_names=(_WHITE_CLASSICAL, _WHITE_TCN, _WHITE_CROSSWALK, _FIXED_LOCAL),
        study_names=(_WHITE,),
        comparison_names=(_WHITE_RECOVERY_COMPARISON,),
        limitations=(
            (
                "The recovery target map, split identity, scorer identity, and rights "
                "decision remain unresolved; rights are M7 "
                "scope."
            ),
        ),
    ),
    _claim(
        "program_sample_efficiency_unresolved",
        SynthesisAxis.SAMPLE_EFFICIENCY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.UNRESOLVED,
        (
            "Program-wide recovery-forecasting sample efficiency is unresolved because "
            "no controlled, comparable training-set-size learning curve spans recovery "
            "model families. Row, participant, camp, seed, and repeated-run counts are "
            "not sample-efficiency "
            "estimates."
        ),
        benchmark_names=_ALL_BENCHMARKS,
        result_names=(_SYSID_EXACT, _WHITE_CLASSICAL, _WHITE_TCN),
        study_names=(_SYSID, _WHITE),
        limitations=(
            (
                "SYSID K=2/4/8 is history-information evidence in its manufactured "
                "inverse problem; White N=9 is an insufficiency warning, not an "
                "efficiency "
                "estimate."
            ),
        ),
    ),
    _claim(
        "program_compute_efficiency_unresolved",
        SynthesisAxis.COMPUTE_EFFICIENCY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.UNRESOLVED,
        (
            "Program-wide compute efficiency is unresolved because no normalized, "
            "directly comparable compute-budget study spans the recovery model families. "
            "GPU/CPU labels, anecdotes, architecture complexity, and row or seed counts "
            "do not establish compute efficiency; M5 runtime accounting is future "
            "reproducibility "
            "tooling."
        ),
        benchmark_names=_ALL_BENCHMARKS,
        experiment_names=tuple(
            name
            for name, experiment in _EXPERIMENTS.items()
            if experiment.benchmark_name in BENCHMARK_REGISTRY and experiment.model_names
        ),
        limitations=(
            (
                "Historical runtime authority is incomplete and no comparable compute "
                "protocol is "
                "registered."
            ),
        ),
    ),
    _claim(
        "program_robustness_is_study_specific",
        SynthesisAxis.ROBUSTNESS,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Robustness evidence exists only on declared study-specific axes: fixed mode "
            "records shortcut-leakage, shift-support, statistical-adequacy, "
            "runtime-seal, and validation-substitution PASS gates; rich public/hidden "
            "results remain separate bank evidence; canonical seed robustness is "
            "unestablished; White model rankings are unstable at N=9. There is no "
            "universal robustness score or production robustness "
            "certification."
        ),
        benchmark_names=(_CANONICAL, _RICH, _FIXED),
        result_names=(
            _CANONICAL_RESULT,
            _RICH_PUBLIC_HEADROOM,
            _RICH_HIDDEN_HEADROOM,
            _WHITE_CLASSICAL,
            _WHITE_TCN,
            _FIXED_LOCAL,
            _FIXED_NLME,
        ),
        experiment_names=(_FIXED_STUDY, _WHITE_EXPERIMENT),
        study_names=(_WHITE,),
        comparison_names=(_RICH_BANK_COMPARISON,),
        gate_names=(
            "SHORTCUT_LEAKAGE",
            "SHIFT_SUPPORT",
            "STATISTICAL_ADEQUACY",
            "RUNTIME_SEAL",
            "VALIDATION_SUBSTITUTION",
        ),
        limitations=(
            (
                "Every robustness statement remains bound to its specimen, split, or "
                "frozen research "
                "protocol."
            ),
        ),
    ),
    _claim(
        "program_task_design_sensitivity",
        SynthesisAxis.TASK_DESIGN_SENSITIVITY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Scientific conclusions were sensitive to formulation and information "
            "design: ridge beat the restricted frontier in the phase-consistent state; "
            "correlated exposure showed near-frontier local reconstruction and a "
            "measurable multidimensional-over-scalar advantage below the historical "
            "rule; fixed mode again showed local reconstruction at the frontier and "
            "weaker generic-MLP results, with four frozen design gates failing and the "
            "owner pivoting. Redesign changed which failure modes were exposed; it does "
            "not define a monotonic performance "
            "trajectory."
        ),
        benchmark_names=(_PHASE, _CORRELATED, _FIXED),
        result_names=(
            _PHASE_RIDGE,
            _PHASE_FRONTIER,
            _CORR_RATIO,
            _CORR_SCALAR,
            _FIXED_LOCAL,
            _FIXED_NLME,
            _FIXED_1D,
            _FIXED_MLP,
            _FIXED_OWNER,
        ),
        experiment_names=(_PHASE_EXPERIMENT, _CORRELATED_EXPERIMENT, _FIXED_STUDY, _FIXED_PIVOT),
        historical_rule_names=(*_corr_rules, *_fixed_rules),
        gate_names=tuple(
            item.gate_name for item in _fixed_study_reconstruction.historical_gate_outcomes
        ),
        limitations=(
            (
                "These studies use different worlds and datasets; no cross-world numeric "
                "delta or monotonic performance trajectory is "
                "valid."
            ),
        ),
    ),
    _claim(
        "program_structured_and_analytic_methods_no_universal_winner",
        SynthesisAxis.STRUCTURED_VS_LEARNED,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "Structured, local, or analytic methods were highly competitive and "
            "sometimes superior within their own valid studies: rich-history empirical "
            "Bayes captured most public headroom; fixed-mode structured/local approaches "
            "outperformed the reported generic MLP and 1-D result; exact and "
            "empirical-Bayes inference beat neural amortization in SYSID. White does not "
            "establish classical superiority. The evidence does not support a universal "
            "structured-over-learned "
            "rule."
        ),
        benchmark_names=(_RICH, _FIXED),
        result_names=(
            _RICH_ZERO,
            _RICH_EB,
            _RICH_BOOSTED,
            _RICH_PUBLIC_HEADROOM,
            _FIXED_LOCAL,
            _FIXED_NLME,
            _FIXED_1D,
            _FIXED_MLP,
            _SYSID_EXACT,
            _SYSID_EB,
            _SYSID_NEURAL,
            _WHITE_CLASSICAL,
            _WHITE_TCN,
        ),
        study_names=(_SYSID, _WHITE),
        comparisons=(
            (((_RICH_ZERO, _RICH_EB, _RICH_BOOSTED, _RICH_PUBLIC_HEADROOM)), None),
            (((_FIXED_LOCAL, _FIXED_NLME, _FIXED_1D, _FIXED_MLP)), None),
            (((_SYSID_EXACT, _SYSID_EB, _SYSID_NEURAL)), None),
            (((_WHITE_CLASSICAL, _WHITE_TCN)), None),
        ),
        model_names=(
            "rich_history_empirical_bayes_predictor",
            "rich_history_boosted_residual_predictor",
            "rich_history_headroom_reference",
            "local_history_structured_attacker",
            "fixed_mode_nonlinear_mixed_effects_predictor",
            "learned_one_dimensional_exposure_predictor",
            "generic_multilayer_perceptron_predictor",
            "identification_exact_analytic_posterior",
            "identification_empirical_bayes_posterior",
            "identification_amortized_neural_posterior",
            "white_waveform_classical_predictor",
            "white_waveform_temporal_convolutional_predictor",
        ),
        limitations=(
            (
                "The comparisons are confined to their separate study identities; they "
                "do not support cross-specimen ranking or a universal family "
                "preference."
            ),
        ),
    ),
    _claim(
        "program_negative_results_preserved",
        SynthesisAxis.NEGATIVE_RESULTS,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The synthesis preserves the initial attempt-family negative result, initial "
            "negative/inconclusive qualification, phase-consistent falsification, "
            "correlated scalar-rule failure with RUNTIME_SCORER_REPAIR_REQUIRED, "
            "fixed-mode four failed research gates with PROGRAM_PIVOT, SYSID "
            "neural-versus-exact negative result with NOT_ML_TASK, and White's "
            "unstable-ranking/NOT_BENCHMARK_VALIDATION boundary. Threshold's "
            "NOT_ESTABLISHED attempt is unresolved evidence, not a scientific failure; "
            "fixed's pivot is not benchmark "
            "failure."
        ),
        benchmark_names=(_INITIAL, _PHASE, _CORRELATED, _THRESHOLD, _FIXED),
        result_names=(
            _INITIAL_NEGATIVE,
            _INITIAL_QUALIFICATION,
            _PHASE_RIDGE,
            _PHASE_FRONTIER,
            _CORR_RATIO,
            _CORR_SCALAR,
            _FIXED_OWNER,
            _SYSID_DIFF,
            _WHITE_CLASSICAL,
            _WHITE_TCN,
        ),
        experiment_names=(
            _CORRELATED_EXPERIMENT,
            _THRESHOLD_PROTOCOL,
            _THRESHOLD_ATTEMPT,
            _FIXED_STUDY,
            _FIXED_PIVOT,
            _SYSID_EXPERIMENT,
            _WHITE_EXPERIMENT,
        ),
        study_names=(_SYSID, _WHITE),
        historical_rule_names=(*_corr_rules, *_fixed_rules),
        gate_names=tuple(
            item.gate_name for item in _fixed_study_reconstruction.historical_gate_outcomes
        ),
        limitations=(
            (
                "Operationally incomplete, unadjudicated, and not-established outcomes "
                "remain distinct from completed scientific negative "
                "results."
            ),
        ),
    ),
    _claim(
        "program_benchmark_quality_reproducibility",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "M5 preserves each benchmark's M2 formulation status: "
            f"{_benchmark_status_text}. No benchmark is EXACT. "
            f"PARTIALLY_REPRODUCIBLE states are {', '.join(_partial_benchmarks)}; "
            "SEMANTICALLY_REPRODUCIBLE states are "
            f"{', '.join(_semantic_benchmarks)}. Semantic reproducibility does not "
            "establish exact historical bytes, model/result replay, or scorer completeness."
        ),
        benchmark_names=_ALL_BENCHMARKS,
        limitations=(
            (
                "Hidden-test materialization, scorer/evaluation completeness, and "
                "model/result replay remain benchmark-specific; the exact M5 profiles "
                "are exposed on each benchmark "
                "characterization."
            ),
        ),
    ),
    _claim(
        "program_exact_historical_replay_unresolved",
        SynthesisAxis.BENCHMARK_QUALITY,
        SynthesisScope.PROGRAM,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The public program is reproducible at partial or semantic levels, not as "
            "exact historical replay. Hidden challenge limitations remain "
            "specimen-specific: fixed mode is "
            f"{_fixed_hidden_split.materialization_state.value.upper()}, rich history is "
            f"{_rich_hidden_split.materialization_state.value.upper()}, and threshold "
            f"response is {_threshold_hidden_split.materialization_state.value.upper()}."
        ),
        benchmark_names=(
            _INITIAL,
            _CANONICAL,
            _RICH,
            _PRELIMINARY,
            _PHASE,
            _CORRELATED,
            _THRESHOLD,
            _FIXED,
        ),
        limitations=(
            (
                "M5 profiles distinguish formulation reproducibility from hidden "
                "materialization, evaluation completeness, and M3 result replay "
                "authority."
            ),
        ),
    ),
    _claim(
        "program_sample_efficiency_sysid_boundary",
        SynthesisAxis.SAMPLE_EFFICIENCY,
        SynthesisScope.STUDY,
        ConclusionStatus.SUPPORTED_WITH_CAVEAT,
        (
            "The SYSID K=2/4/8 strata provide valid evidence that more complete episode "
            "history improves inference within that manufactured problem. They do not "
            "estimate sample efficiency across recovery forecasting "
            "models."
        ),
        result_names=(_SYSID_EXACT,),
        study_names=(_SYSID,),
        model_names=("identification_exact_analytic_posterior",),
        limitations=(
            (
                "The varied quantity is episode-history information in one inverse "
                "problem, not recovery-model training-set "
                "size."
            ),
        ),
    ),
)


SYNTHESIS_CLAIMS = MappingProxyType({claim.name: claim for claim in _CLAIMS})
if len(SYNTHESIS_CLAIMS) != len(_CLAIMS):
    raise ValueError("synthesis claim names must be unique")
if any(validate_synthesis_claim(claim) is not None for claim in _CLAIMS):
    raise ValueError("invalid synthesis claim registry")


BENCHMARK_CHARACTERIZATIONS = MappingProxyType(
    {
        name: BenchmarkCharacterization(
            benchmark_name=name,
            reproducibility_profile=_PROFILES[name],
            model_ladder=get_specimen_model_ladder(name),
            result_reproductions=tuple(
                result for result in RESULT_REPRODUCTIONS.values() if result.benchmark_name == name
            ),
            claim_names=tuple(claim.name for claim in _CLAIMS if name in claim.benchmark_names),
        )
        for name in _BENCHMARK_NAMES
    }
)


STUDY_CHARACTERIZATIONS = MappingProxyType(
    {
        name: StudyCharacterization(
            study_name=name,
            reconstruction=get_study_reconstruction(name),
            experiment_reconstructions=tuple(
                get_experiment_reconstruction(experiment.name)
                for experiment in LINEAGE_REGISTRY.experiments.values()
                if experiment.benchmark_name is None
                and experiment.study_type is not None
                and experiment.study_type.value == name
                and experiment.name in EXPERIMENT_RECONSTRUCTIONS
            ),
            claim_names=tuple(claim.name for claim in _CLAIMS if name in claim.study_names),
        )
        for name in _ADJACENT_STUDY_NAMES
    }
)

if len(BENCHMARK_CHARACTERIZATIONS) != 8:
    raise ValueError("M6 must characterize exactly the eight registered benchmarks")
if set(BENCHMARK_CHARACTERIZATIONS) != set(BENCHMARK_REGISTRY):
    raise ValueError("M6 benchmark identities must exactly match the benchmark registry")
if set(STUDY_CHARACTERIZATIONS) != set(_ADJACENT_STUDY_NAMES):
    raise ValueError(
        "M6 adjacent study identities must remain system-identification and grounding only"
    )


PROGRAM_SYNTHESIS = ProgramSynthesis(
    benchmark_names=tuple(BENCHMARK_CHARACTERIZATIONS),
    study_names=tuple(STUDY_CHARACTERIZATIONS),
    claims=_CLAIMS,
)


def get_program_synthesis() -> ProgramSynthesis:
    return PROGRAM_SYNTHESIS


def get_benchmark_characterization(name: str) -> BenchmarkCharacterization:
    return BENCHMARK_CHARACTERIZATIONS[name]


def get_study_characterization(name: str) -> StudyCharacterization:
    return STUDY_CHARACTERIZATIONS[name]


def get_synthesis_claim(name: str) -> ScientificSynthesisClaim:
    return SYNTHESIS_CLAIMS[name]


def get_synthesis_claims(
    axis: SynthesisAxis | None = None,
    benchmark_name: str | None = None,
) -> tuple[ScientificSynthesisClaim, ...]:
    if benchmark_name is not None and benchmark_name not in BENCHMARK_CHARACTERIZATIONS:
        raise KeyError(benchmark_name)
    return tuple(
        claim
        for claim in _CLAIMS
        if (axis is None or claim.axis is axis)
        and (benchmark_name is None or benchmark_name in claim.benchmark_names)
    )


__all__ = [
    "BENCHMARK_CHARACTERIZATIONS",
    "PROGRAM_SYNTHESIS",
    "STUDY_CHARACTERIZATIONS",
    "SYNTHESIS_CLAIMS",
    "build_comparative_evidence",
    "get_benchmark_characterization",
    "get_program_synthesis",
    "get_study_characterization",
    "get_synthesis_claim",
    "get_synthesis_claims",
    "validate_synthesis_claim",
]
