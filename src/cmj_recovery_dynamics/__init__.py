"""Typed scientific contracts for countermovement-jump recovery forecasting."""

from cmj_recovery_dynamics.contracts import (
    CANONICAL_OUTCOMES,
    FORCE_INNOVATION,
    NET_IMPULSE_INNOVATION,
    BenchmarkDefinition,
    ForecastHorizon,
    OutcomeDefinition,
    OutcomeVariable,
    PhysicalUnit,
    TaskDefinition,
    TaskType,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY, TASK_REGISTRY

__version__ = "0.1.0"

__all__ = [
    "BENCHMARK_REGISTRY",
    "CANONICAL_OUTCOMES",
    "FORCE_INNOVATION",
    "ForecastHorizon",
    "NET_IMPULSE_INNOVATION",
    "OutcomeDefinition",
    "OutcomeVariable",
    "PhysicalUnit",
    "TASK_REGISTRY",
    "BenchmarkDefinition",
    "TaskDefinition",
    "TaskType",
]
