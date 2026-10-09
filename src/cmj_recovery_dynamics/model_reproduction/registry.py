"""Evidence-bounded M3 model, experiment-use, and result registries."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from cmj_recovery_dynamics.lineage.contracts import ConfigurationStatus, ExperimentStatus
from cmj_recovery_dynamics.lineage.experiments import EXPERIMENTS
from cmj_recovery_dynamics.lineage.models import MODEL_FAMILIES
from cmj_recovery_dynamics.lineage.results import RESULTS

from .contracts import (
    CheckpointState,
    ModelConfigurationStatus,
    ModelReproduction,
    ModelReproductionStatus,
    ModelUseReproduction,
    ResultReplayAuthority,
    ResultReproduction,
    ResultReproductionStatus,
    SourceClosure,
    SpecimenModelLadder,
    SpecimenModelStatus,
)

BENCHMARK_NAMES = (
    "initial_preseason_camp_recovery",
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
)

_SOURCE_ROOT = "problems/preseason-exposure-cmj-recovery-forecast"
_BASELINE_SOURCES = SourceClosure(
    source_commit="8e3ea4932b4a399640dfaa139b2f273fbd3f73cd",
    task_tree="a35491509f7917e02cb08178e4cf0365700e83e2",
    source_snapshot="ALI-400 preserved v26-source-9c671067 Gate 5/6 source",
    model_source=f"{_SOURCE_ROOT}/baselines/linear/solution.py",
    training_source=f"{_SOURCE_ROOT}/baselines/linear/train.py",
    configuration_source=f"{_SOURCE_ROOT}/baselines/linear/strategy.manifest.json",
    checkpoint_metadata_authority=f"{_SOURCE_ROOT}/baselines/linear/strategy.manifest.json",
    evaluation_source=f"{_SOURCE_ROOT}/solution/train.py and RES-367 metrics/scoring.py",
    result_source=f"{_SOURCE_ROOT}/solution/reference/selection_result.json",
    seed_fold_authority=f"{_SOURCE_ROOT}/data_generation/authority/gate6_seed_contract.json",
    source_hashes=(
        (
            f"{_SOURCE_ROOT}/baselines/common.py",
            "50c56313c2bc2d2da9fcd6a43ef9361f4f2d3aeabda54de7fe7bf1be031e2d53",
        ),
        (
            f"{_SOURCE_ROOT}/baselines/linear/train.py",
            "644759686beefeb7db58b5629716531bf9cd10c1e39654c3ac792e24d9af868f",
        ),
        (
            f"{_SOURCE_ROOT}/baselines/linear/solution.py",
            "6c94e2bb9d07e85891f6aee72974feab0c0940c22295fa1aefc7ec06b575b686",
        ),
        (
            f"{_SOURCE_ROOT}/baselines/linear/strategy.manifest.json",
            "ae9540b0b2f6a306a6d7ca71bcb79d3dd861ff167a6dd1900ef55c552411ce58",
        ),
        (
            f"{_SOURCE_ROOT}/solution/reference/selection_result.json",
            "bbf5d6e2cb340221a596f2e313443e69c8594b9f4e1525487aca72ae3b733e53",
        ),
        (
            f"{_SOURCE_ROOT}/data_generation/authority/gate6_seed_contract.json",
            "34eb136731615128b88802e0c589365b0351d9913dd73b4814118a42347f15bb",
        ),
    ),
    evidence=("RES-361 preserved source", "RES-366 M1 result binding", "RES-367 M1 evaluation"),
)
_REFERENCE_SOURCES = SourceClosure(
    source_commit="8e3ea4932b4a399640dfaa139b2f273fbd3f73cd",
    task_tree="a35491509f7917e02cb08178e4cf0365700e83e2",
    source_snapshot="ALI-400 preserved v26-source-9c671067 Gate 5/6 source",
    model_source=f"{_SOURCE_ROOT}/solution/model.py",
    training_source=f"{_SOURCE_ROOT}/solution/train.py",
    configuration_source=f"{_SOURCE_ROOT}/solution/reference/model_config.json",
    checkpoint_metadata_authority=f"{_SOURCE_ROOT}/solution/reference/strategy.manifest.json",
    evaluation_source=f"{_SOURCE_ROOT}/solution/train.py and RES-367 metrics/scoring.py",
    result_source=f"{_SOURCE_ROOT}/solution/reference/selection_result.json",
    seed_fold_authority=f"{_SOURCE_ROOT}/data_generation/authority/gate6_seed_contract.json",
    runtime_authority=f"{_SOURCE_ROOT}/solution/reference/candidate_result.json",
    source_hashes=(
        (
            f"{_SOURCE_ROOT}/solution/model.py",
            "d81eb44409ce40ff4490f209acf701b9883244fcdb9e516dad619973a693db19",
        ),
        (
            f"{_SOURCE_ROOT}/solution/train.py",
            "ede5e2a42a4ee0dfea90dc2eb91f7273ad6a4a15b4a918b7e9a6e6c7f30dfc06",
        ),
        (
            f"{_SOURCE_ROOT}/solution/reference/model_config.json",
            "2e98f79417e0bc96db16ca083214eb48f41e1355a57deda8585bb4e367f70323",
        ),
        (
            f"{_SOURCE_ROOT}/solution/reference/selection_result.json",
            "bbf5d6e2cb340221a596f2e313443e69c8594b9f4e1525487aca72ae3b733e53",
        ),
        (
            f"{_SOURCE_ROOT}/solution/reference/strategy.manifest.json",
            "e932408518d53bda798d5742f0400b266f69fb9b281cc0a170457b150859be1a",
        ),
        (
            f"{_SOURCE_ROOT}/solution/reference/candidate_result.json",
            "0027d493931091e898bfdd044b3145c009432c03900d6aead9ccd19a58b8ac6c",
        ),
        (
            f"{_SOURCE_ROOT}/data_generation/authority/gate6_seed_contract.json",
            "34eb136731615128b88802e0c589365b0351d9913dd73b4814118a42347f15bb",
        ),
        (
            f"{_SOURCE_ROOT}/data_generation/authority/gate6_reference_training_contract.json",
            "f0b18faf5896a8f77e73357f81bd94db26f127aa821ac9a46de811fe80841ea9",
        ),
    ),
    evidence=("RES-361 preserved source", "RES-366 M1 result binding", "RES-367 M1 evaluation"),
)

_USE_OVERRIDES: Mapping[tuple[str, str], dict[str, object]] = MappingProxyType(
    {
        ("linear_public_baseline", "initial_linear_public_baseline_evaluation"): {
            "implementation_status": ModelReproductionStatus.SEMANTIC_IMPLEMENTATION,
            "configuration_status": ModelConfigurationStatus.EXACT,
            "architecture": "39-feature, two-output ordinary least-squares linear regression",
            "feature_surface": (
                "39 ordered public-only columns: baseline, horizon/query, four "
                "history assessments, exposure/plan, and routine-assessment availability; "
                "participant identity is not a feature."
            ),
            "preprocessing": (
                "Train-only feature mean and sample standard deviation (ddof=1); "
                "zero scales become 1; "
                "an intercept is fitted and targets remain in innovation units."
            ),
            "training_objective": (
                "Multi-output ordinary least squares via numpy.linalg.lstsq(rcond=None)."
            ),
            "hyperparameters": (
                ("estimator", "numpy.linalg.lstsq(rcond=None)"),
                ("seed", "0"),
                ("training_rows", "4096"),
                ("training_participant_groups", "1024"),
                ("target_order", "relative_mean_concentric_force; relative_concentric_net_impulse"),
            ),
            "seed_identities": ("seed=0",),
            "seed_metrics": (),
            "fold_grouping": (
                "One fixed public train/validation participant-group split; "
                "1024 training groups and "
                "128 validation groups; no cross-validation folds."
            ),
            "checkpoint_state": CheckpointState.PRESERVED_PRIVATELY,
            "checkpoint_identity_sha256": (
                "d21a81a35803c873a0e1437f1f754f29bf9ac3d58972fb3842eac517e1665dff"
            ),
            "runtime_details": None,
            "source_closure": _BASELINE_SOURCES,
            "missing_authority": (
                "M3 implements the estimator over the frozen 39-column matrix; "
                "the task-specific row projection remains in the preserved source.",
                "No M3 numerical rerun was performed; M2 does not classify "
                "the historical dataset hash as EXACT.",
                "Historical baseline runtime details are absent.",
            ),
        },
        ("initial_public_reference_model", "initial_public_reference_selection"): {
            "implementation_status": ModelReproductionStatus.SEMANTIC_IMPLEMENTATION,
            "configuration_status": ModelConfigurationStatus.EXACT,
            "architecture": (
                "M0 public MLP: Linear(39, 32) -> exact GELU -> Linear(32, 2); 1,346 parameters."
            ),
            "feature_surface": (
                "The same 39 ordered public-only features as the Gate 5 linear "
                "baseline; no author-side fields."
            ),
            "preprocessing": (
                "Train-only mean/sample-standard-deviation scaling (ddof=1), "
                "with zero scales set to 1; "
                "outputs are two target innovations."
            ),
            "training_objective": (
                "MSE on innovations standardized by train-only target-cell scales."
            ),
            "hyperparameters": (
                ("optimizer", "AdamW"),
                ("learning_rate", "0.001"),
                ("weight_decay", "0.0001"),
                ("batch_size", "64"),
                ("gradient_clip_norm", "1.0"),
                ("epochs", "20 minimum; 200 maximum; evaluate every 5"),
                (
                    "early_stopping",
                    "20 evaluations without >=0.0001 improvement; earliest tied epoch",
                ),
                ("augmentation", "none"),
                ("validation_fit", "false"),
                ("mixed_precision", "bfloat16 CUDA autocast; float32 master weights"),
                ("seed_selection", "mean of repeat 0 and repeat 1; no best-seed selection"),
            ),
            "seed_identities": (
                "repeat=0; model=279072964; loader=2115274314; dropout=365358155; "
                "selection=1056043477; augmentation disabled (seed=185199805)",
                "repeat=1; model=1255891457; loader=1191659341; dropout=627264576; "
                "selection=1595417134; augmentation disabled (seed=256100766)",
            ),
            "seed_metrics": (
                ("M0 repeat=0", 0.36102172987192604),
                ("M0 repeat=1", 0.3575973272130363),
            ),
            "fold_grouping": (
                "One fixed public train/validation participant-group split; "
                "1024 training groups/4096 rows, "
                "128 validation groups/512 rows; two training repeats, no cross-validation folds."
            ),
            "checkpoint_state": CheckpointState.PRESERVED_PRIVATELY,
            "checkpoint_identity_sha256": (
                "c8b72aa46a52fbc25a9f27330c3f62f54c67adbc5d64c5d5d0b91680a6a0842e"
            ),
            "runtime_details": (
                "Packaged repeat 0: NVIDIA GeForce RTX 5090, Python 3.13.14, PyTorch 2.11.0+cu128, "
                "CUDA 12.8, 31.543557 seconds, 200 epochs. Repeat 1 runtime is unknown."
            ),
            "source_closure": _REFERENCE_SOURCES,
            "missing_authority": (
                "M3 implements the exact M0 inference equation but does not train "
                "or load private weights.",
                "The preserved packaged checkpoint is M0 repeat 0; it is not "
                "the two-seed aggregate result.",
                "No M3 numerical rerun was performed; M2 does not classify "
                "the historical dataset hash as EXACT.",
            ),
        },
        ("rich_history_zero_baseline", "rich_history_headroom_reconstruction"): {
            "implementation_status": ModelReproductionStatus.EXACT_IMPLEMENTATION,
            "configuration_status": ModelConfigurationStatus.NOT_APPLICABLE,
            "architecture": "Constant zero-innovation predictor.",
            "feature_surface": "No features.",
            "preprocessing": "None.",
            "training_objective": None,
            "hyperparameters": (),
            "seed_identities": (),
            "seed_metrics": (),
            "fold_grouping": None,
            "checkpoint_state": CheckpointState.NOT_APPLICABLE,
            "checkpoint_identity_sha256": None,
            "runtime_details": None,
            "source_closure": SourceClosure(
                evidence=("RES-366: deterministic zero-predictor result definition",),
            ),
            "missing_authority": (
                "The historical raw-progress score has not been replayed against "
                "an EXACT M2 dataset identity.",
            ),
        },
    }
)

_MODEL_FAMILIES = {family.name: family for family in MODEL_FAMILIES}
_EXPERIMENTS = {experiment.name: experiment for experiment in EXPERIMENTS}
_RESULTS = {result.name: result for result in RESULTS}
_RESULTS_BY_EXPERIMENT: dict[str, list[str]] = {}
for _result in RESULTS:
    if _result.name in _RESULTS_BY_EXPERIMENT.setdefault(_result.experiment_name, []):
        raise ValueError(f"duplicate result identity: {_result.name}")
    _RESULTS_BY_EXPERIMENT[_result.experiment_name].append(_result.name)

_BENCHMARK_MODELS = {
    family.name
    for family in MODEL_FAMILIES
    if set(family.applicability.benchmark_names).intersection(BENCHMARK_NAMES)
}


def _configuration_status(status: ConfigurationStatus) -> ModelConfigurationStatus:
    if status is ConfigurationStatus.IDENTIFIED:
        return ModelConfigurationStatus.EXACT
    if status is ConfigurationStatus.PARTIALLY_SPECIFIED:
        return ModelConfigurationStatus.PARTIAL
    return ModelConfigurationStatus.UNKNOWN


def _checkpoint_state(name: str) -> CheckpointState:
    family = _MODEL_FAMILIES[name]
    if family.checkpoint_status.value == "PRESERVED_PRIVATELY":
        return CheckpointState.PRESERVED_PRIVATELY
    if family.checkpoint_status.value == "NOT_APPLICABLE":
        return CheckpointState.NOT_APPLICABLE
    if family.checkpoint_status.value == "NOT_RECOVERED":
        return CheckpointState.NOT_RECOVERED
    return CheckpointState.UNKNOWN


def _use_contract(model_name: str, experiment_name: str) -> ModelUseReproduction:
    experiment = _EXPERIMENTS[experiment_name]
    if experiment.benchmark_name not in BENCHMARK_NAMES:
        raise ValueError("M3 model uses must be attached to one of the eight benchmark specimens")
    result_names = tuple(
        name
        for name in _RESULTS_BY_EXPERIMENT.get(experiment_name, ())
        if model_name in _RESULTS[name].model_names
    )
    override = _USE_OVERRIDES.get((model_name, experiment_name))
    if override is not None:
        values = dict(override)
        return ModelUseReproduction(
            model_name=model_name,
            benchmark_name=experiment.benchmark_name,
            experiment=experiment,
            dataset_name=experiment.dataset_name,
            split_names=experiment.split_names,
            evaluation_names=experiment.evaluation_names,
            result_names=result_names,
            experiment_status=experiment.status,
            scientific_disposition=experiment.disposition,
            **values,  # type: ignore[arg-type]
        )

    family = _MODEL_FAMILIES[model_name]
    if experiment.status is ExperimentStatus.PROPOSED_NOT_RUN:
        implementation_status = ModelReproductionStatus.NOT_APPLICABLE
    elif result_names:
        implementation_status = ModelReproductionStatus.RESULT_EVIDENCE_ONLY
    else:
        implementation_status = ModelReproductionStatus.UNRESOLVED
    missing = (
        "Exact architecture and hyperparameters are not established by M1 source authority.",
        "Feature preprocessing and fitted target state are not source-closed.",
        "Seed/fold/run details are unknown unless separately recorded by the M1 experiment.",
        "No checkpoint-to-result association is established.",
        "Historical dataset identity is not EXACT under M2.",
    )
    if experiment.status is ExperimentStatus.OPERATIONAL_FAILURE:
        missing = (
            "The run ended operationally before a scientific result was established.",
            "The operational failure does not establish a negative model result.",
            *missing[1:],
        )
    elif experiment.status is ExperimentStatus.CANCELED:
        missing = ("The run was canceled; no scientific result was established.", *missing[1:])
    return ModelUseReproduction(
        model_name=model_name,
        benchmark_name=experiment.benchmark_name,
        experiment=experiment,
        dataset_name=experiment.dataset_name,
        split_names=experiment.split_names,
        evaluation_names=experiment.evaluation_names,
        result_names=result_names,
        experiment_status=experiment.status,
        scientific_disposition=experiment.disposition,
        implementation_status=implementation_status,
        configuration_status=_configuration_status(family.configuration_status),
        architecture=family.architecture,
        feature_surface=None,
        preprocessing=None,
        training_objective=None,
        hyperparameters=(),
        seed_identities=None,
        seed_metrics=(),
        fold_grouping=None,
        checkpoint_state=_checkpoint_state(model_name),
        checkpoint_identity_sha256=None,
        runtime_details=None,
        source_closure=SourceClosure(evidence=family.evidence.sources),
        missing_authority=missing,
    )


def _aggregate_status(
    uses: tuple[ModelUseReproduction, ...], unbound: tuple[str, ...]
) -> ModelReproductionStatus:
    if not uses:
        return ModelReproductionStatus.UNRESOLVED
    statuses = {use.implementation_status for use in uses}
    if unbound or len(statuses) > 1:
        return ModelReproductionStatus.RESULT_EVIDENCE_ONLY
    return next(iter(statuses))


def _model_contract(name: str) -> ModelReproduction:
    family = _MODEL_FAMILIES[name]
    experiment_names = tuple(
        experiment.name for experiment in EXPERIMENTS if name in experiment.model_names
    )
    uses = tuple(_use_contract(name, experiment) for experiment in experiment_names)
    bound_benchmarks = {use.benchmark_name for use in uses}
    unbound = tuple(
        benchmark
        for benchmark in family.applicability.benchmark_names
        if benchmark in BENCHMARK_NAMES and benchmark not in bound_benchmarks
    )
    status = _aggregate_status(uses, unbound)
    config_statuses = {use.configuration_status for use in uses}
    if unbound or len(config_statuses) > 1:
        configuration_status = ModelConfigurationStatus.PARTIAL
    elif config_statuses:
        configuration_status = next(iter(config_statuses))
    else:
        configuration_status = _configuration_status(family.configuration_status)
    missing = tuple(
        f"M1 lists {benchmark} as applicable, but no benchmark experiment/result "
        "binds this family there."
        for benchmark in unbound
    )
    if unbound:
        missing += ("No cross-specimen architecture or configuration equivalence is inferred.",)
    if not missing:
        missing = tuple(dict.fromkeys(item for use in uses for item in use.missing_authority))
    return ModelReproduction(
        model_name=name,
        model_family=family,
        status=status,
        configuration_status=configuration_status,
        uses=uses,
        unbound_applicability=unbound,
        missing_authority=missing,
    )


MODEL_REPRODUCTIONS: Mapping[str, ModelReproduction] = MappingProxyType(
    {name: _model_contract(name) for name in sorted(_BENCHMARK_MODELS)}
)


def _result_contract(result_name: str) -> ResultReproduction:
    result = _RESULTS[result_name]
    experiment = _EXPERIMENTS[result.experiment_name]
    if experiment.benchmark_name not in BENCHMARK_NAMES:
        raise ValueError("benchmark-linked results must resolve to one of the eight specimens")
    source_reproducible = result_name in {
        "initial_linear_public_baseline_result",
        "initial_public_reference_selection_result",
    }
    status = (
        ResultReproductionStatus.SOURCE_REPRODUCIBLE
        if source_reproducible
        else ResultReproductionStatus.RESULT_EVIDENCE_ONLY
    )
    authority = ResultReplayAuthority(
        historical_dataset_hash_exact=False,
        target_semantics_exact=result.evaluation_name != "unresolved_initial_camp_platform_metric",
        model_configuration_exact=source_reproducible
        or result_name == "rich_history_zero_baseline_result",
        seed_fold_protocol_exact=source_reproducible,
        checkpoint_or_training_procedure_exact=source_reproducible
        or result_name == "rich_history_zero_baseline_result",
        evaluation_implementation_exact=result.evaluation_name
        != "unresolved_initial_camp_platform_metric",
        calibration_available=result.evaluation_name != "unresolved_initial_camp_platform_metric",
        runtime_determinism_resolved=False,
    )
    model_uses = tuple(
        use
        for model_name in result.model_names
        for use in MODEL_REPRODUCTIONS[model_name].uses
        if use.experiment.name == experiment.name
    )
    seed_identities = (
        tuple(seed for use in model_uses for seed in use.seed_identities or ())
        if model_uses and all(use.seed_identities is not None for use in model_uses)
        else None
    )
    fold_grouping = (
        model_uses[0].fold_grouping
        if model_uses
        and all(use.fold_grouping == model_uses[0].fold_grouping for use in model_uses)
        else None
    )
    runtime_details = tuple(
        dict.fromkeys(use.runtime_details for use in model_uses if use.runtime_details is not None)
    )
    missing = ["M2 does not establish an EXACT historical dataset hash."]
    if source_reproducible:
        missing.extend(
            (
                "The historical score was not numerically replayed during M3.",
                "M2 data byte identity therefore prevents EXACT_REPLAYABLE status.",
            )
        )
    else:
        missing.extend(
            (
                "Exact model/configuration and seed/run source closure is absent "
                "for at least one bound model.",
                "The preserved numerical result remains evidence, not a reproduced score.",
            )
        )
    if result.evaluation_name == "unresolved_initial_camp_platform_metric":
        missing.append("The historical platform score implementation is unresolved.")
    return ResultReproduction(
        result=result,
        benchmark_name=experiment.benchmark_name,
        experiment=experiment,
        experiment_status=experiment.status,
        experiment_disposition=experiment.disposition,
        status=status,
        replay_authority=authority,
        seed_identities=seed_identities,
        fold_grouping=fold_grouping,
        runtime_details=runtime_details,
        numerically_replayed=False,
        replay_basis=(
            "Preserved training/configuration/result source closes the procedure, "
            "but the historical score was not rerun."
            if source_reproducible
            else "M1 directly binds this preserved result family to its model, "
            "experiment, dataset, split, and evaluation."
        ),
        missing_authority=tuple(missing),
    )


_BENCHMARK_RESULT_NAMES = tuple(
    result.name
    for result in RESULTS
    if result.model_names and any(name in _BENCHMARK_MODELS for name in result.model_names)
)
RESULT_REPRODUCTIONS: Mapping[str, ResultReproduction] = MappingProxyType(
    {name: _result_contract(name) for name in _BENCHMARK_RESULT_NAMES}
)


_SPECIMEN_NOTES = {
    "initial_preseason_camp_recovery": (
        SpecimenModelStatus.RECOVERED,
        "The linear OLS baseline and two-seed M0 reference have source-bound configurations; "
        "the five-submission negative family keeps its scorer and architecture unresolved.",
    ),
    "canonical_preseason_camp_recovery": (
        SpecimenModelStatus.RESULT_EVIDENCE_ONLY,
        "Five campaign scores are preserved; model, checkpoint, training seed, "
        "and evaluation bank remain unresolved.",
    ),
    "rich_history_camp_recovery": (
        SpecimenModelStatus.RESULT_EVIDENCE_ONLY,
        "The zero predictor is exact; other public/hidden/GPU result families "
        "remain evidence-only and distinct by split/evaluation.",
    ),
    "preliminary_post_exposure_recovery": (
        SpecimenModelStatus.NOT_ESTABLISHED,
        "No independent baseline/reference result is bound to this specimen; "
        "no completed model ladder is evidenced.",
    ),
    "phase_consistent_post_exposure_recovery": (
        SpecimenModelStatus.RESULT_EVIDENCE_ONLY,
        "Ridge and restricted-frontier SRE6 values are research results; ridge "
        "configuration and frontier membership remain unresolved.",
    ),
    "correlated_exposure_recovery": (
        SpecimenModelStatus.RESULT_EVIDENCE_ONLY,
        "Only this specimen's corrected research protocol binds the preserved "
        "ratios, interval, and progress loss; no campaign is rerun.",
    ),
    "threshold_response_recovery": (
        SpecimenModelStatus.PROPOSED,
        "The reference attempt is NOT_ESTABLISHED; configuration and checkpoint "
        "association remain unknown, and no accepted result exists.",
    ),
    "fixed_mode_discrepancy_recovery": (
        SpecimenModelStatus.RESULT_EVIDENCE_ONLY,
        "Completed-study model results are bound separately from the operational "
        "failure and canceled replay; no architecture is inferred.",
    ),
}


def _specimen_ladder(benchmark_name: str) -> SpecimenModelLadder:
    status, note = _SPECIMEN_NOTES[benchmark_name]
    uses = tuple(
        use
        for model in MODEL_REPRODUCTIONS.values()
        for use in model.uses
        if use.benchmark_name == benchmark_name
    )
    model_names = tuple(sorted({use.model_name for use in uses}))
    result_names = tuple(
        sorted(
            result_name
            for result_name, result in RESULT_REPRODUCTIONS.items()
            if result.benchmark_name == benchmark_name
        )
    )
    experiment_names = tuple(sorted({use.experiment.name for use in uses}))
    return SpecimenModelLadder(
        benchmark_name, status, model_names, result_names, experiment_names, note
    )


SPECIMEN_MODEL_LADDERS: Mapping[str, SpecimenModelLadder] = MappingProxyType(
    {name: _specimen_ladder(name) for name in BENCHMARK_NAMES}
)


def get_model_reproduction(model_name: str) -> ModelReproduction:
    return MODEL_REPRODUCTIONS[model_name]


def get_model_use_reproduction(
    model_name: str, benchmark_name: str, experiment_name: str | None = None
) -> ModelUseReproduction:
    uses = tuple(
        use
        for use in get_model_reproduction(model_name).uses
        if use.benchmark_name == benchmark_name
        and (experiment_name is None or use.experiment.name == experiment_name)
    )
    if len(uses) != 1:
        raise KeyError((model_name, benchmark_name, experiment_name))
    return uses[0]


def get_result_reproduction(result_name: str) -> ResultReproduction:
    return RESULT_REPRODUCTIONS[result_name]


def get_specimen_model_ladder(benchmark_name: str) -> SpecimenModelLadder:
    return SPECIMEN_MODEL_LADDERS[benchmark_name]


def directly_comparable(left: ResultReproduction, right: ResultReproduction) -> bool:
    """Require identical scored specimen, data split, evaluation, and protocol."""

    left_experiment = _EXPERIMENTS[left.result.experiment_name]
    right_experiment = _EXPERIMENTS[right.result.experiment_name]
    return (
        left.benchmark_name == right.benchmark_name
        and left.result.dataset_name == right.result.dataset_name
        and left.result.split_name == right.result.split_name
        and left.result.evaluation_name == right.result.evaluation_name
        and left_experiment.protocol_unit == right_experiment.protocol_unit
        and left_experiment.seed_values == right_experiment.seed_values
        and left_experiment.fold_count == right_experiment.fold_count
        and left_experiment.bootstrap == right_experiment.bootstrap
    )


__all__ = [
    "BENCHMARK_NAMES",
    "MODEL_REPRODUCTIONS",
    "RESULT_REPRODUCTIONS",
    "SPECIMEN_MODEL_LADDERS",
    "directly_comparable",
    "get_model_reproduction",
    "get_model_use_reproduction",
    "get_result_reproduction",
    "get_specimen_model_ladder",
]
