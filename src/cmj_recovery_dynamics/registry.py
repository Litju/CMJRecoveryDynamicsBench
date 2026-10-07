"""Read-only registries for the two task families and eight benchmark states."""

from collections.abc import Mapping
from types import MappingProxyType

from cmj_recovery_dynamics.benchmarks import BENCHMARK_DEFINITIONS
from cmj_recovery_dynamics.contracts import (
    BenchmarkDefinition,
    EvaluationDefinition,
    TaskDefinition,
)
from cmj_recovery_dynamics.metrics.catalog import ALL_EVALUATION_DEFINITIONS
from cmj_recovery_dynamics.metrics.provenance import HISTORICAL_COMPARISONS
from cmj_recovery_dynamics.tasks import TASKS


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
if any(
    name != "UNKNOWN" and name not in EVALUATION_REGISTRY
    for comparison in HISTORICAL_COMPARISONS
    for name in (
        comparison.left_evaluation_name,
        comparison.right_evaluation_name,
        comparison.compatibility_transform_name or "UNKNOWN",
    )
):
    raise ValueError("historical comparisons must reference registered evaluation definitions")


def get_benchmark(scientific_name: str) -> BenchmarkDefinition:
    """Return one registered benchmark by its scientific name."""
    return BENCHMARK_REGISTRY[scientific_name]


def get_evaluation(scientific_name: str) -> EvaluationDefinition:
    """Return a metric definition by its clean scientific name."""
    return EVALUATION_REGISTRY[scientific_name]
