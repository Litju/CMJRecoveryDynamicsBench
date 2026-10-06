"""Registry completeness, relationships, and benchmark claim ceilings."""

from cmj_recovery_dynamics.contracts import (
    CANONICAL_OUTCOMES,
    REQUIRED_UNSUPPORTED_CLAIMS,
    BenchmarkStatus,
    TaskType,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY, TASK_REGISTRY

EXPECTED_BENCHMARK_NAMES = frozenset(
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


def test_registry_contains_exactly_eight_unique_scientific_benchmarks() -> None:
    assert len(BENCHMARK_REGISTRY) == 8
    assert set(BENCHMARK_REGISTRY) == EXPECTED_BENCHMARK_NAMES
    assert len(set(benchmark.name for benchmark in BENCHMARK_REGISTRY.values())) == 8


def test_registry_contains_only_the_two_established_task_types() -> None:
    assert len(TASK_REGISTRY) == 2
    assert {task.task_type for task in TASK_REGISTRY.values()} == set(TaskType)


def test_each_benchmark_binds_valid_task_observation_dynamics_and_claims() -> None:
    for benchmark in BENCHMARK_REGISTRY.values():
        assert benchmark.task.name in TASK_REGISTRY
        assert TASK_REGISTRY[benchmark.task.name] == benchmark.task
        assert benchmark.observation.name
        assert benchmark.dynamics.name
        assert benchmark.horizons == benchmark.task.horizons
        assert benchmark.outcomes == benchmark.task.outcomes == CANONICAL_OUTCOMES
        assert benchmark.claim_boundary is not None
        assert benchmark.claim_boundary.unsupported_claims == REQUIRED_UNSUPPORTED_CLAIMS
        assert benchmark.dataset_identity.scientific_name
        assert benchmark.evaluation_identity.scientific_name
        assert isinstance(benchmark.status, BenchmarkStatus)


def test_supported_parent_relationships_resolve_without_cycles() -> None:
    for benchmark in BENCHMARK_REGISTRY.values():
        ancestry: set[str] = set()
        current = benchmark
        while current.parent_name is not None:
            assert current.parent_name in BENCHMARK_REGISTRY
            assert current.name not in ancestry
            ancestry.add(current.name)
            current = BENCHMARK_REGISTRY[current.parent_name]


def test_each_recovered_information_boundary_captures_required_categories() -> None:
    observed = {
        benchmark.observation.name: benchmark.observation
        for benchmark in BENCHMARK_REGISTRY.values()
    }
    assert len(observed) == 4
    for contract in observed.values():
        assert contract.baseline_measurements.status
        assert contract.assessment_history.status
        assert contract.exposure_information.status
        assert contract.participant_covariates.status
        assert contract.prior_episode_information.status
        assert contract.temporal_availability.information_cutoff
        assert contract.hidden_variables.status
        assert contract.forbidden_variables.status
        assert contract.measurement_construction
    phase_consistent = observed["phase_consistent_force_impulse"]
    assert phase_consistent.force_impulse_relationship is not None
    assert (
        phase_consistent.force_impulse_relationship.gravitational_acceleration_m_per_s_squared
        == 9.80665
    )
