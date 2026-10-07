"""Read-only registries for tasks, benchmarks, evaluations, and lineage."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from cmj_recovery_dynamics.benchmarks import BENCHMARK_DEFINITIONS
from cmj_recovery_dynamics.contracts import (
    BenchmarkDefinition,
    EvaluationDefinition,
    TaskDefinition,
)
from cmj_recovery_dynamics.metrics.catalog import ALL_EVALUATION_DEFINITIONS
from cmj_recovery_dynamics.tasks import TASKS

if TYPE_CHECKING:
    from cmj_recovery_dynamics.lineage.contracts import (
        ExperimentDefinition,
        ModelFamily,
        ResultDefinition,
    )
    from cmj_recovery_dynamics.lineage.registry import (
        BenchmarkLineageView,
        ExperimentLineageView,
        ModelLineageView,
    )


def _unique_names(names: tuple[str, ...], collection: str) -> None:
    if len(names) != len(set(names)):
        raise ValueError(f"{collection} names must be unique")


_unique_names(tuple(task.name for task in TASKS), "task")
_unique_names(tuple(benchmark.name for benchmark in BENCHMARK_DEFINITIONS), "benchmark")
_unique_names(tuple(item.name for item in ALL_EVALUATION_DEFINITIONS), "evaluation")

TASK_REGISTRY: Mapping[str, TaskDefinition] = MappingProxyType({task.name: task for task in TASKS})
BENCHMARK_REGISTRY: Mapping[str, BenchmarkDefinition] = MappingProxyType(
    {benchmark.name: benchmark for benchmark in BENCHMARK_DEFINITIONS}
)
EVALUATION_REGISTRY: Mapping[str, EvaluationDefinition] = MappingProxyType(
    {evaluation.name: evaluation for evaluation in ALL_EVALUATION_DEFINITIONS}
)

if len(TASK_REGISTRY) != 2:
    raise ValueError("the scientific API currently defines exactly two task families")
if len(BENCHMARK_REGISTRY) != 8:
    raise ValueError("the scientific registry currently defines exactly eight benchmarks")
if any(
    EVALUATION_REGISTRY.get(benchmark.evaluation_identity.name) != benchmark.evaluation_identity
    for benchmark in BENCHMARK_DEFINITIONS
):
    raise ValueError("every benchmark evaluation identity must resolve in the evaluation registry")
if any(
    EVALUATION_REGISTRY.get(evaluation.name) != evaluation
    for benchmark in BENCHMARK_DEFINITIONS
    for evaluation in (
        *benchmark.research_evaluations,
        *benchmark.qualification_evaluations,
        *benchmark.model_selection_evaluations,
    )
):
    raise ValueError("every auxiliary benchmark evaluation must resolve in the evaluation registry")


def get_benchmark(scientific_name: str) -> BenchmarkDefinition:
    """Return one registered benchmark by its scientific name."""
    return BENCHMARK_REGISTRY[scientific_name]


def get_evaluation(scientific_name: str) -> EvaluationDefinition:
    """Return a metric definition by its clean scientific name."""
    return EVALUATION_REGISTRY[scientific_name]


def get_benchmark_lineage(scientific_name: str) -> BenchmarkLineageView:
    """Return the full benchmark, dataset, model, experiment, and result view."""
    from cmj_recovery_dynamics.lineage.registry import get_benchmark_lineage as query

    return query(scientific_name)


def get_model_family(scientific_name: str) -> ModelFamily:
    """Return one model family by its scientific name."""
    from cmj_recovery_dynamics.lineage.registry import get_model_family as query

    return query(scientific_name)


def get_model_lineage(scientific_name: str) -> ModelLineageView:
    """Return a model and its associated experiments and results."""
    from cmj_recovery_dynamics.lineage.registry import get_model_lineage as query

    return query(scientific_name)


def get_experiment(scientific_name: str) -> ExperimentDefinition:
    """Return one experiment by its scientific name."""
    from cmj_recovery_dynamics.lineage.registry import get_experiment as query

    return query(scientific_name)


def get_experiment_lineage(scientific_name: str) -> ExperimentLineageView:
    """Return an experiment with its dataset, splits, models, evaluations, and results."""
    from cmj_recovery_dynamics.lineage.registry import get_experiment_lineage as query

    return query(scientific_name)


def get_result(scientific_name: str) -> ResultDefinition:
    """Return one result family by its scientific name."""
    from cmj_recovery_dynamics.lineage.registry import get_result as query

    return query(scientific_name)
