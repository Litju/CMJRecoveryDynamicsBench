"""Read-only registries for the two task families and eight benchmark states."""

from collections.abc import Mapping
from types import MappingProxyType

from cmj_recovery_dynamics.benchmarks import BENCHMARK_DEFINITIONS
from cmj_recovery_dynamics.contracts import BenchmarkDefinition, TaskDefinition
from cmj_recovery_dynamics.tasks import TASKS


def _unique_names(names: tuple[str, ...], collection: str) -> None:
    if len(names) != len(set(names)):
        raise ValueError(f"{collection} names must be unique")


_unique_names(tuple(task.name for task in TASKS), "task")
_unique_names(tuple(benchmark.name for benchmark in BENCHMARK_DEFINITIONS), "benchmark")

TASK_REGISTRY: Mapping[str, TaskDefinition] = MappingProxyType({task.name: task for task in TASKS})
BENCHMARK_REGISTRY: Mapping[str, BenchmarkDefinition] = MappingProxyType(
    {benchmark.name: benchmark for benchmark in BENCHMARK_DEFINITIONS}
)

if len(TASK_REGISTRY) != 2:
    raise ValueError("the scientific API currently defines exactly two task families")
if len(BENCHMARK_REGISTRY) != 8:
    raise ValueError("the scientific registry currently defines exactly eight benchmarks")


def get_benchmark(scientific_name: str) -> BenchmarkDefinition:
    """Return one registered benchmark by its scientific name."""
    return BENCHMARK_REGISTRY[scientific_name]
