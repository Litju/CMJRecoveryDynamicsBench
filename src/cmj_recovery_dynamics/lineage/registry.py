"""Cross-registry validation and read-only scientific lineage queries."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from cmj_recovery_dynamics.contracts import (
    BenchmarkDefinition,
    ComparabilityStatus,
    EvaluationDefinition,
    MetricCategory,
    StudyDefinition,
    StudyType,
)
from cmj_recovery_dynamics.lineage.contracts import (
    ArtifactAvailability,
    BenchmarkLineage,
    BenchmarkTransition,
    ComparabilityConclusion,
    ConflictDefinition,
    DatasetIdentity,
    DatasetKind,
    EvaluationBinding,
    ExperimentDefinition,
    ExperimentPurpose,
    ModelFamily,
    RedistributionStatus,
    RepresentationIdentity,
    ResultDefinition,
    SplitIdentity,
    SplitRole,
    StudyLineage,
)
from cmj_recovery_dynamics.lineage.datasets import (
    BENCHMARK_LINEAGE,
    BENCHMARK_TRANSITIONS,
    DATASETS,
    REPRESENTATIONS,
    SPLITS,
)
from cmj_recovery_dynamics.lineage.evaluations import EVALUATION_BINDINGS
from cmj_recovery_dynamics.lineage.experiments import ADJACENT_STUDIES, EXPERIMENTS
from cmj_recovery_dynamics.lineage.models import MODEL_FAMILIES
from cmj_recovery_dynamics.lineage.results import (
    COMPARABILITY_CONCLUSIONS,
    POSTERIOR_RMSE_CONFLICT,
    RESULTS,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY, EVALUATION_REGISTRY
from cmj_recovery_dynamics.studies import STUDY_DEFINITIONS

_EXPECTED_BENCHMARKS = frozenset(
    {
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
        "rich_history_camp_recovery",
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    }
)


def _index[T](
    values: Sequence[T],
    identity: Callable[[T], str],
    label: str,
) -> Mapping[str, T]:
    indexed: dict[str, T] = {}
    for value in values:
        name = identity(value)
        if name in indexed:
            raise ValueError(f"duplicate scientific {label} identity: {name}")
        indexed[name] = value
    return MappingProxyType(indexed)


@dataclass(frozen=True, slots=True)
class BenchmarkLineageView:
    benchmark: BenchmarkDefinition
    lineage: BenchmarkLineage
    dataset: DatasetIdentity
    splits: tuple[SplitIdentity, ...]
    evaluation: EvaluationDefinition
    models: tuple[ModelFamily, ...]
    adjacent_models: tuple[ModelFamily, ...]
    experiments: tuple[ExperimentDefinition, ...]
    results: tuple[ResultDefinition, ...]
    adjacent_studies: tuple[StudyLineage, ...]
    adjacent_experiments: tuple[ExperimentDefinition, ...]
    adjacent_results: tuple[ResultDefinition, ...]
    conflicts: tuple[ConflictDefinition, ...]


@dataclass(frozen=True, slots=True)
class ModelLineageView:
    model: ModelFamily
    experiments: tuple[ExperimentDefinition, ...]
    results: tuple[ResultDefinition, ...]


@dataclass(frozen=True, slots=True)
class ExperimentLineageView:
    experiment: ExperimentDefinition
    dataset: DatasetIdentity
    splits: tuple[SplitIdentity, ...]
    models: tuple[ModelFamily, ...]
    evaluations: tuple[EvaluationDefinition | EvaluationBinding, ...]
    results: tuple[ResultDefinition, ...]


class LineageRegistry:
    """Immutable registries with fail-fast cross-reference validation."""

    def __init__(
        self,
        *,
        benchmarks: Sequence[BenchmarkDefinition] = tuple(BENCHMARK_REGISTRY.values()),
        datasets: Sequence[DatasetIdentity] = DATASETS,
        splits: Sequence[SplitIdentity] = SPLITS,
        representations: Sequence[RepresentationIdentity] = REPRESENTATIONS,
        benchmark_lineage: Sequence[BenchmarkLineage] = BENCHMARK_LINEAGE,
        transitions: Sequence[BenchmarkTransition] = BENCHMARK_TRANSITIONS,
        studies: Sequence[StudyLineage] = ADJACENT_STUDIES,
        model_families: Sequence[ModelFamily] = MODEL_FAMILIES,
        experiments: Sequence[ExperimentDefinition] = EXPERIMENTS,
        results: Sequence[ResultDefinition] = RESULTS,
        comparisons: Sequence[ComparabilityConclusion] = COMPARABILITY_CONCLUSIONS,
        conflicts: Sequence[ConflictDefinition] = (POSTERIOR_RMSE_CONFLICT,),
        evaluation_bindings: Sequence[EvaluationBinding] = EVALUATION_BINDINGS,
        evaluations: Mapping[str, EvaluationDefinition] = EVALUATION_REGISTRY,
        study_definitions: Sequence[StudyDefinition] = STUDY_DEFINITIONS,
    ) -> None:
        self.benchmarks = _index(benchmarks, lambda item: item.name, "benchmark")
        self.datasets = _index(datasets, lambda item: item.name, "dataset")
        self.splits = _index(splits, lambda item: item.name, "split")
        self.representations = _index(
            representations,
            lambda item: item.name,
            "representation",
        )
        self.benchmark_lineage = _index(
            benchmark_lineage,
            lambda item: item.benchmark_name,
            "benchmark-lineage",
        )
        self.transitions = _index(transitions, lambda item: item.name, "transition")
        self.studies = _index(studies, lambda item: item.study_type.value, "study")
        self.model_families = _index(model_families, lambda item: item.name, "model")
        self.experiments = _index(experiments, lambda item: item.name, "experiment")
        self.results = _index(results, lambda item: item.name, "result")
        self.comparisons = _index(comparisons, lambda item: item.name, "comparison")
        self.conflicts = _index(conflicts, lambda item: item.name, "conflict")
        self.evaluations = _index(tuple(evaluations.values()), lambda item: item.name, "evaluation")
        custom = _index(evaluation_bindings, lambda item: item.name, "evaluation binding")
        duplicate_evaluations = set(self.evaluations).intersection(custom)
        if duplicate_evaluations:
            raise ValueError(
                f"duplicate scientific evaluation identity: {min(duplicate_evaluations)}"
            )
        self.custom_evaluations = custom
        self.study_definitions = _index(
            study_definitions,
            lambda item: item.study_type.value,
            "study definition",
        )
        self._validate()

    def _evaluation(self, name: str) -> EvaluationDefinition | EvaluationBinding:
        if name in self.evaluations:
            return self.evaluations[name]
        if name in self.custom_evaluations:
            return self.custom_evaluations[name]
        raise ValueError(f"unknown evaluation identity: {name}")

    def _validate(self) -> None:
        if frozenset(self.benchmarks) != _EXPECTED_BENCHMARKS:
            raise ValueError("lineage must bind exactly the eight canonical benchmark states")
        if set(self.benchmark_lineage) != set(self.benchmarks):
            raise ValueError("every canonical benchmark needs exactly one lineage record")
        if set(self.studies) != {item.value for item in StudyType}:
            raise ValueError(
                "adjacent-study registry must contain exactly the five defined study types"
            )
        if set(self.studies) != set(self.study_definitions):
            raise ValueError(
                "adjacent-study lineage must resolve to the scientific study definitions"
            )

        for study in self.studies.values():
            if any(name not in self.benchmarks for name in study.benchmark_names):
                raise ValueError(
                    f"adjacent study {study.study_type.value} references an "
                    "unknown related benchmark"
                )
            if any(name not in self.datasets for name in study.dataset_names):
                raise ValueError(
                    f"adjacent study {study.study_type.value} references an unknown dataset"
                )

        for dataset in self.datasets.values():
            unknown_superseded = dataset.supersedes_dataset
            if unknown_superseded is not None and unknown_superseded not in self.datasets:
                raise ValueError(f"dataset {dataset.name} supersedes an unknown dataset")
            dataset_splits = {
                split.name for split in self.splits.values() if split.dataset_name == dataset.name
            }
            if dataset_splits != set(dataset.split_names):
                raise ValueError(f"dataset {dataset.name} has unresolved or extra split identities")
            if any(self.splits[name].dataset_name != dataset.name for name in dataset.split_names):
                raise ValueError(f"dataset {dataset.name} split binding is inconsistent")

        for name, lineage in self.benchmark_lineage.items():
            benchmark = self.benchmarks[name]
            dataset = self.datasets.get(lineage.dataset_name)
            if dataset is None:
                raise ValueError(f"benchmark {name} references an unknown dataset")
            if benchmark.dataset_identity.scientific_name != lineage.dataset_name:
                raise ValueError(f"benchmark {name} dataset differs from its technical contract")
            if dataset.benchmark_names != (name,):
                raise ValueError(f"dataset {dataset.name} must bind only its named benchmark")
            if dataset.generator_identity != lineage.generator_identity:
                raise ValueError(f"benchmark {name} generator identity does not resolve")
            if dataset.observation_identity != lineage.observation_identity:
                raise ValueError(f"benchmark {name} observation identity does not resolve")
            if benchmark.observation.name != lineage.observation_identity:
                raise ValueError(f"benchmark {name} observation differs from its contract")
            if benchmark.evaluation_identity.name != lineage.evaluation_name:
                raise ValueError(f"benchmark {name} evaluation differs from its contract")
            if lineage.representation_name not in self.representations:
                raise ValueError(f"benchmark {name} references an unknown representation")
            if not lineage.split_names or any(
                split_name not in self.splits
                or self.splits[split_name].dataset_name != dataset.name
                for split_name in lineage.split_names
            ):
                raise ValueError(f"benchmark {name} has an unresolved data split")
            roles = {self.splits[split].role for split in lineage.split_names}
            if not {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}.issubset(roles):
                raise ValueError(
                    f"benchmark {name} needs explicit training and public-validation splits"
                )

        for transition in self.transitions.values():
            if transition.target_benchmark not in self.benchmarks:
                raise ValueError(f"transition {transition.name} has an unknown target benchmark")
            if (
                transition.source_benchmark is not None
                and transition.source_benchmark not in self.benchmarks
            ):
                raise ValueError(f"transition {transition.name} has an unknown source benchmark")

        for model in self.model_families.values():
            if any(name not in self.benchmarks for name in model.applicability.benchmark_names):
                raise ValueError(f"model {model.name} names an unknown compatible benchmark")
            if any(study.value not in self.studies for study in model.applicability.study_types):
                raise ValueError(f"model {model.name} names an unknown compatible study")
            if model.checkpoint is not None:
                if (
                    model.checkpoint.availability is ArtifactAvailability.PRESERVED_PRIVATELY
                    and model.checkpoint.redistribution is RedistributionStatus.ALLOWED
                    and model.checkpoint.rights_decision_reference is None
                ):
                    raise ValueError(
                        "private checkpoint cannot be public without a rights decision"
                    )

        for experiment in self.experiments.values():
            self._validate_experiment(experiment)

        for result in self.results.values():
            experiment = self.experiments.get(result.experiment_name)
            if experiment is None:
                raise ValueError(f"result {result.name} references an unknown experiment")
            if (
                result.dataset_name != experiment.dataset_name
                or result.split_name not in experiment.split_names
            ):
                raise ValueError(f"result {result.name} dataset/split differs from its experiment")
            if (
                result.split_name not in self.splits
                or self.splits[result.split_name].dataset_name != result.dataset_name
            ):
                raise ValueError(f"result {result.name} references an unknown dataset split")
            if result.evaluation_name not in experiment.evaluation_names:
                raise ValueError(f"result {result.name} evaluation is not bound to its experiment")
            evaluation = self._evaluation(result.evaluation_name)
            if not set(result.model_names).issubset(experiment.model_names):
                raise ValueError(f"result {result.name} references a model outside its experiment")
            if result.production_result and not self._is_production_scorer(evaluation):
                raise ValueError(
                    f"production result {result.name} uses a research-only or unresolved metric"
                )
            if (
                result.production_result
                and evaluation.category is not MetricCategory.BENCHMARK_SCORE
            ):
                raise ValueError(f"production result {result.name} is not a benchmark score")

        for comparison in self.comparisons.values():
            left = tuple(self._result_for_comparison(name) for name in comparison.left_result_names)
            right = tuple(
                self._result_for_comparison(name) for name in comparison.right_result_names
            )
            if comparison.status is ComparabilityStatus.DIRECTLY_COMPARABLE:
                for left_result in left:
                    for right_result in right:
                        self._validate_direct_comparison(left_result, right_result)
            if comparison.status is ComparabilityStatus.COMPARABLE_WITH_CAVEAT:
                for left_result in left:
                    for right_result in right:
                        if (
                            left_result.dataset_name != right_result.dataset_name
                            or left_result.evaluation_name != right_result.evaluation_name
                        ):
                            raise ValueError(
                                "caveated comparison needs the same dataset and evaluation"
                            )

    def _validate_experiment(self, experiment: ExperimentDefinition) -> None:
        dataset = self.datasets.get(experiment.dataset_name)
        if dataset is None:
            raise ValueError(f"experiment {experiment.name} references an unknown dataset")
        if any(
            split_name not in self.splits or self.splits[split_name].dataset_name != dataset.name
            for split_name in experiment.split_names
        ):
            raise ValueError(f"experiment {experiment.name} references an unknown dataset split")
        if experiment.benchmark_name is not None:
            if experiment.benchmark_name not in self.benchmarks:
                raise ValueError(f"experiment {experiment.name} references an unknown benchmark")
            benchmark_dataset = self.benchmark_lineage[experiment.benchmark_name].dataset_name
            if dataset.name != benchmark_dataset and not (
                dataset.kind is DatasetKind.SYNTHETIC
                and not dataset.benchmark_names
                and experiment.purpose is ExperimentPurpose.QUALIFICATION
            ):
                raise ValueError(
                    f"experiment {experiment.name} dataset is incompatible with its benchmark"
                )
        elif dataset.benchmark_names:
            raise ValueError(
                f"adjacent study experiment {experiment.name} binds a benchmark dataset"
            )

        if experiment.study_type is not None and experiment.study_type.value not in self.studies:
            raise ValueError(f"experiment {experiment.name} references an unknown adjacent study")
        if experiment.study_type is StudyType.SYSTEM_IDENTIFICATION:
            if (
                experiment.benchmark_name is not None
                or dataset.kind is not DatasetKind.MANUFACTURED
            ):
                raise ValueError(
                    "system-identification results cannot bind to point-forecast benchmark tasks"
                )
        if experiment.study_type is StudyType.REAL_DATA_GROUNDING:
            if experiment.benchmark_name is not None or dataset.kind is not DatasetKind.EMPIRICAL:
                raise ValueError("real-data grounding cannot bind as benchmark validation")

        for model_name in experiment.model_names:
            model = self.model_families.get(model_name)
            if model is None:
                raise ValueError(f"experiment {experiment.name} references an unknown model")
            if (
                experiment.benchmark_name is not None
                and experiment.benchmark_name not in model.applicability.benchmark_names
            ):
                raise ValueError(
                    f"model {model_name} is incompatible with benchmark {experiment.benchmark_name}"
                )
            if (
                experiment.study_type is not None
                and experiment.study_type not in model.applicability.study_types
            ):
                raise ValueError(
                    f"model {model_name} is incompatible with study {experiment.study_type.value}"
                )

        for evaluation_name in experiment.evaluation_names:
            evaluation = self._evaluation(evaluation_name)
            if isinstance(evaluation, EvaluationDefinition):
                if experiment.benchmark_name is not None:
                    if experiment.benchmark_name not in evaluation.compatible_benchmarks and not (
                        evaluation.category is MetricCategory.COMPATIBILITY_TRANSFORM
                        and experiment.change_class.value == "COMPATIBILITY_ONLY"
                    ):
                        raise ValueError(
                            f"evaluation {evaluation_name} is incompatible with "
                            f"benchmark {experiment.benchmark_name}"
                        )
                elif evaluation.category is MetricCategory.BENCHMARK_SCORE:
                    raise ValueError(
                        "benchmark scores cannot bind to adjacent-study-only experiments"
                    )
                if experiment.study_type is StudyType.SYSTEM_IDENTIFICATION and (
                    evaluation.compatible_benchmarks or getattr(evaluation, "target_variables", ())
                ):
                    raise ValueError(
                        "system-identification evaluation is incompatible with point-forecast tasks"
                    )
            else:
                if (
                    experiment.benchmark_name is not None
                    and experiment.benchmark_name not in evaluation.compatible_benchmarks
                ):
                    raise ValueError(
                        f"custom evaluation {evaluation_name} is incompatible with "
                        f"benchmark {experiment.benchmark_name}"
                    )
                if (
                    experiment.study_type is not None
                    and experiment.study_type not in evaluation.compatible_studies
                ):
                    raise ValueError(
                        f"custom evaluation {evaluation_name} is incompatible with "
                        f"study {experiment.study_type.value}"
                    )

    @staticmethod
    def _is_production_scorer(evaluation: EvaluationDefinition | EvaluationBinding) -> bool:
        if isinstance(evaluation, EvaluationBinding):
            return evaluation.production_scorer
        return evaluation.is_production_scorer

    def _result_for_comparison(self, name: str) -> ResultDefinition:
        try:
            return self.results[name]
        except KeyError as error:
            raise ValueError(
                f"comparability conclusion references an unknown result: {name}"
            ) from error

    def _validate_direct_comparison(
        self,
        left: ResultDefinition,
        right: ResultDefinition,
    ) -> None:
        if (
            left.dataset_name != right.dataset_name
            or left.split_name != right.split_name
            or left.evaluation_name != right.evaluation_name
        ):
            raise ValueError(
                "directly comparable results need identical dataset, split, "
                "and evaluation identities"
            )
        left_experiment = self.experiments[left.experiment_name]
        right_experiment = self.experiments[right.experiment_name]
        if left_experiment.protocol_unit is not right_experiment.protocol_unit:
            raise ValueError("directly comparable results need the same protocol unit")
        if left_experiment.bootstrap != right_experiment.bootstrap:
            raise ValueError("directly comparable results need the same bootstrap protocol")

    def benchmark_view(self, scientific_name: str) -> BenchmarkLineageView:
        benchmark = self.benchmarks[scientific_name]
        lineage = self.benchmark_lineage[scientific_name]
        dataset = self.datasets[lineage.dataset_name]
        evaluation = self.evaluations[lineage.evaluation_name]
        experiments = tuple(
            item for item in self.experiments.values() if item.benchmark_name == scientific_name
        )
        experiment_names = {item.name for item in experiments}
        result_items = tuple(
            item for item in self.results.values() if item.experiment_name in experiment_names
        )
        model_names = {model for item in experiments for model in item.model_names}
        related_studies = tuple(
            item for item in self.studies.values() if scientific_name in item.benchmark_names
        )
        related_types = {item.study_type for item in related_studies}
        adjacent_experiments = tuple(
            item
            for item in self.experiments.values()
            if item.study_type in related_types and item.benchmark_name is None
        )
        adjacent_names = {item.name for item in adjacent_experiments}
        adjacent_results = tuple(
            item for item in self.results.values() if item.experiment_name in adjacent_names
        )
        adjacent_model_names = {
            model_name for item in adjacent_experiments for model_name in item.model_names
        }
        conflict_items = tuple(
            item
            for item in self.conflicts.values()
            if StudyType.SYSTEM_IDENTIFICATION in related_types
        )
        return BenchmarkLineageView(
            benchmark,
            lineage,
            dataset,
            tuple(self.splits[name] for name in lineage.split_names),
            evaluation,
            tuple(self.model_families[name] for name in sorted(model_names)),
            tuple(self.model_families[name] for name in sorted(adjacent_model_names)),
            experiments,
            result_items,
            related_studies,
            adjacent_experiments,
            adjacent_results,
            conflict_items,
        )

    def results_for_study(self, study_type: StudyType) -> tuple[ResultDefinition, ...]:
        experiment_names = {
            experiment.name
            for experiment in self.experiments.values()
            if experiment.study_type is study_type
        }
        return tuple(
            result for result in self.results.values() if result.experiment_name in experiment_names
        )

    def model_view(self, scientific_name: str) -> ModelLineageView:
        model = self.model_families[scientific_name]
        experiments = tuple(
            item for item in self.experiments.values() if scientific_name in item.model_names
        )
        results = tuple(
            item for item in self.results.values() if scientific_name in item.model_names
        )
        return ModelLineageView(model, experiments, results)

    def experiment_view(self, scientific_name: str) -> ExperimentLineageView:
        experiment = self.experiments[scientific_name]
        return ExperimentLineageView(
            experiment,
            self.datasets[experiment.dataset_name],
            tuple(self.splits[name] for name in experiment.split_names),
            tuple(self.model_families[name] for name in experiment.model_names),
            tuple(self._evaluation(name) for name in experiment.evaluation_names),
            tuple(
                item for item in self.results.values() if item.experiment_name == scientific_name
            ),
        )


LINEAGE_REGISTRY = LineageRegistry()


def get_benchmark_lineage(scientific_name: str) -> BenchmarkLineageView:
    return LINEAGE_REGISTRY.benchmark_view(scientific_name)


def get_model_family(scientific_name: str) -> ModelFamily:
    return LINEAGE_REGISTRY.model_families[scientific_name]


def get_model_lineage(scientific_name: str) -> ModelLineageView:
    return LINEAGE_REGISTRY.model_view(scientific_name)


def get_experiment(scientific_name: str) -> ExperimentDefinition:
    return LINEAGE_REGISTRY.experiments[scientific_name]


def get_experiment_lineage(scientific_name: str) -> ExperimentLineageView:
    return LINEAGE_REGISTRY.experiment_view(scientific_name)


def get_result(scientific_name: str) -> ResultDefinition:
    return LINEAGE_REGISTRY.results[scientific_name]


__all__ = [
    "LINEAGE_REGISTRY",
    "BenchmarkLineageView",
    "ExperimentLineageView",
    "LineageRegistry",
    "ModelLineageView",
    "get_benchmark_lineage",
    "get_experiment",
    "get_experiment_lineage",
    "get_model_family",
    "get_model_lineage",
    "get_result",
]
