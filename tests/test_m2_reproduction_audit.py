"""Executable cross-formulation audit for the M2 reproduction contracts."""

from __future__ import annotations

import ast
import hashlib
import json
import random
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from cmj_recovery_dynamics.benchmarks.threshold_response_recovery import (
    THRESHOLD_RESPONSE_RECOVERY,
)
from cmj_recovery_dynamics.contracts import BenchmarkStatus, MetricCategory, ProductionAcceptance
from cmj_recovery_dynamics.lineage.contracts import (
    ArtifactAvailability,
    ChangeClass,
    ConfigurationStatus,
)
from cmj_recovery_dynamics.lineage.datasets import BENCHMARK_TRANSITIONS
from cmj_recovery_dynamics.lineage.registry import get_benchmark_lineage, get_model_family
from cmj_recovery_dynamics.metrics.catalog import POST_EXPOSURE_RESEARCH_EVALUATION
from cmj_recovery_dynamics.provenance import (
    HISTORICAL_ALIASES,
    PUBLIC_ROOT_AUTHORITIES,
    get_public_root_authority,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY
from cmj_recovery_dynamics.reproduction import (
    FINAL_REPRODUCTION_STATUS,
    REPRODUCTION_CONTRACTS,
    CalibrationReferenceStatus,
    FormulationReproducibility,
    MaterializationState,
    ProductionScorerStatus,
    SplitRole,
    get_final_reproduction_status,
    get_reproduction_contract,
)
from cmj_recovery_dynamics.reproduction import (
    ReproductionDimension as D,
)
from cmj_recovery_dynamics.reproduction import (
    ReproductionStatus as S,
)
from cmj_recovery_dynamics.reproduction import camp_history as camp_history_module
from cmj_recovery_dynamics.reproduction.audit import (
    _classify as _classify_reproduction,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    OSS_REPRODUCTION_ID,
    generate_canonical_camp_sample,
    generate_initial_camp_sample,
)
from cmj_recovery_dynamics.reproduction.d04_membership import (
    d04_membership_fingerprint,
    replay_d04_membership,
)
from cmj_recovery_dynamics.reproduction.later_single_exposure import (
    LATER_SOURCE_CLOSURES,
    LaterFormulation,
    generate_later_episode,
)
from cmj_recovery_dynamics.reproduction.rich_history import (
    HISTORICAL_HIDDEN_DESIGN,
    PUBLIC_SPLITS,
    R02_FIELD_NAMES,
    PublicSplitName,
    iter_rich_history_public_split,
)
from cmj_recovery_dynamics.reproduction.single_exposure import (
    OSS_ROOT_SEED,
    PREDICTOR_FIELDS,
    ROW_KEY_FIELDS,
    TARGET_FIELDS,
    generate_episode,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_EVIDENCE: dict[tuple[str, D], tuple[str, ...]] = {}


def _cover(benchmarks: tuple[str, ...], dimension: D, *references: str) -> None:
    for benchmark in benchmarks:
        _EVIDENCE[(benchmark, dimension)] = references


_WORLD_EVIDENCE = {
    "initial_preseason_camp_recovery": (
        "tests/test_dynamics.py::test_one_event_composes_fast_fatigue_and_slow_adaptation",
    ),
    "canonical_preseason_camp_recovery": (
        "tests/test_dynamics.py::test_one_event_composes_fast_fatigue_and_slow_adaptation",
    ),
    "rich_history_camp_recovery": (
        "tests/test_dynamics.py::test_rich_history_load_bout_hill_and_summed_decrement_floor",
    ),
    "preliminary_post_exposure_recovery": (
        "tests/test_single_exposure.py::test_base_equation_p1_corner_values_and_p2_monotone_recovery",
    ),
    "phase_consistent_post_exposure_recovery": (
        "tests/test_single_exposure.py::test_base_equation_p1_corner_values_and_p2_monotone_recovery",
    ),
    "correlated_exposure_recovery": (
        "tests/test_single_exposure.py::test_correlated_zero_residual_draw_replays_factor_to_primitive_mapping",
    ),
    "threshold_response_recovery": (
        "tests/test_later_single_exposure.py::test_threshold_hinge_zero_below_at_and_above_threshold",
    ),
    "fixed_mode_discrepancy_recovery": (
        "tests/test_dynamics.py::test_fixed_modes_use_the_mathematical_24_and_84_hour_scales",
    ),
}
for _benchmark, _references in _WORLD_EVIDENCE.items():
    _cover((_benchmark,), D.WORLD_LAW, *_references)

_CAMP = ("initial_preseason_camp_recovery", "canonical_preseason_camp_recovery")
_CAMP_RNG_EVIDENCE = (
    "tests/test_m2_reproduction_audit.py::test_camp_semantic_rng_uses_random_v2_seed",
    "tests/test_camp_history.py::test_clean_room_seed_is_repeatable_and_seed_identity_is_new",
)
for _dimension in (
    D.RNG_ALGORITHM,
    D.RNG_STREAM_CONSTRUCTION,
    D.RNG_DRAW_ORDER,
    D.RNG_SUBSTREAM_STRATEGY,
):
    _cover(_CAMP, _dimension, *_CAMP_RNG_EVIDENCE)

for _dimension in (
    D.RNG_STREAM_CONSTRUCTION,
    D.RNG_DRAW_ORDER,
    D.RNG_SUBSTREAM_STRATEGY,
):
    _cover(
        ("rich_history_camp_recovery",),
        _dimension,
        "tests/test_rich_history.py::test_rng_hierarchy_and_new_numpy_runtime_metadata_stay_separate",
        "tests/test_d04_membership.py::test_d04_ordered_membership_fingerprints_and_dual_authority",
    )

_SINGLE_EXPOSURE = (
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
)
_SINGLE_RNG_EVIDENCE = (
    "tests/test_single_exposure.py::test_rng_exact_construction_does_not_upgrade_algorithm_or_state_claims",
    "tests/test_m2_reproduction_audit.py::test_bounded_single_exposure_root_replay",
)
for _dimension in (D.RNG_STREAM_CONSTRUCTION, D.RNG_DRAW_ORDER):
    _cover(_SINGLE_EXPOSURE, _dimension, *_SINGLE_RNG_EVIDENCE)
_cover(
    (
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "fixed_mode_discrepancy_recovery",
    ),
    D.RNG_SUBSTREAM_STRATEGY,
    *_SINGLE_RNG_EVIDENCE,
)

for _benchmark in (
    "rich_history_camp_recovery",
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
):
    _cover(
        (_benchmark,),
        D.SEED_AUTHORITY,
        "tests/test_m2_reproduction_audit.py::test_public_roots_are_first_class_and_match_claim_scope",
    )

_OBSERVATION_EVIDENCE = {
    "canonical_preseason_camp_recovery": (
        "tests/test_camp_history.py::test_three_trial_assessment_uses_shared_session_and_independent_trial_errors",
    ),
    "rich_history_camp_recovery": (
        "tests/test_rich_history.py::test_o02_baseline_uses_latest_two_valid_qualifying_assessments",
        "tests/test_rich_history.py::test_o02_monitoring_invalid_missing_depth_and_target_trial_behavior",
    ),
    "phase_consistent_post_exposure_recovery": (
        "tests/test_single_exposure.py::test_phase_consistent_trace_integrates_force_and_impulse",
    ),
    "correlated_exposure_recovery": (
        "tests/test_single_exposure.py::test_phase_consistent_trace_integrates_force_and_impulse",
    ),
    "threshold_response_recovery": (
        "tests/test_single_exposure.py::test_phase_consistent_trace_integrates_force_and_impulse",
    ),
    "fixed_mode_discrepancy_recovery": (
        "tests/test_single_exposure.py::test_phase_consistent_trace_integrates_force_and_impulse",
    ),
}
for _benchmark, _references in _OBSERVATION_EVIDENCE.items():
    _cover((_benchmark,), D.OBSERVATION, *_references)

_SCHEMA_EXACT = (
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
    *_SINGLE_EXPOSURE,
)
_cover(
    _SCHEMA_EXACT,
    D.SCHEMA,
    "tests/test_m2_reproduction_audit.py::test_semantic_schema_sizes_and_observation_boundaries",
)
_cover(
    ("canonical_preseason_camp_recovery",),
    D.SCHEMA,
    "tests/test_camp_history.py::test_prediction_representation_rejects_future_history_and_labels",
)
_cover(
    ("rich_history_camp_recovery",),
    D.SCHEMA,
    "tests/test_rich_history.py::test_r02_semantic_fields_and_source_blocks_are_exact",
)
for _benchmark in _SINGLE_EXPOSURE:
    _cover(
        (_benchmark,),
        D.SCHEMA,
        "tests/test_single_exposure.py::test_82_field_schema_block_geometry_keys_and_no_future_label_leakage",
    )
_cover(
    ("rich_history_camp_recovery",),
    D.SPLIT_ASSIGNMENT,
    "tests/test_d04_membership.py::test_d04_public_membership_geometry_and_masks",
    "tests/test_d04_membership.py::test_d04_ordered_membership_fingerprints_and_dual_authority",
)
for _benchmark in _SINGLE_EXPOSURE:
    _cover(
        (_benchmark,),
        D.SPLIT_ASSIGNMENT,
        "tests/test_single_exposure.py::test_named_dataset_geometry_exact_split_membership_and_reference_hashes",
        "tests/test_later_single_exposure.py::test_public_geometry_and_train_validation_group_keys",
    )
_cover(
    ("rich_history_camp_recovery",),
    D.ROW_ORDERING,
    "tests/test_d04_membership.py::test_d04_ordered_membership_fingerprints_and_dual_authority",
)


_EXPECTED_AGGREGATES = {
    "initial_preseason_camp_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
    "canonical_preseason_camp_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
    "rich_history_camp_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
    "preliminary_post_exposure_recovery": FormulationReproducibility.PARTIALLY_REPRODUCIBLE,
    "phase_consistent_post_exposure_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
    "correlated_exposure_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
    "threshold_response_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
    "fixed_mode_discrepancy_recovery": FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE,
}


def _listed_tests(reference: str) -> bool:
    path_string, function_name = reference.split("::", maxsplit=1)
    path = _REPOSITORY_ROOT / path_string
    if not path.is_file():
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
        for node in ast.walk(tree)
    )


def test_final_status_is_contract_derived_and_fail_closed() -> None:
    assert (
        set(FINAL_REPRODUCTION_STATUS) == set(_EXPECTED_AGGREGATES) == set(REPRODUCTION_CONTRACTS)
    )
    assert set(HISTORICAL_ALIASES) == set(FINAL_REPRODUCTION_STATUS)
    for name, expected in _EXPECTED_AGGREGATES.items():
        audit = get_final_reproduction_status(name)
        contract = get_reproduction_contract(name)
        assert audit.contract is contract
        assert audit.benchmark == name
        assert audit.overall_status is expected
        assert audit.public_scope == ("training", "public_validation")
        assert audit.public_seed_authority_key == name
        assert audit.exact_dimensions == tuple(
            claim.dimension for claim in contract.claims if claim.status is S.EXACT
        )
        assert audit.semantic_dimensions == tuple(
            claim.dimension
            for claim in contract.claims
            if claim.status is S.SEMANTICALLY_EQUIVALENT
        )
        assert audit.unresolved_dimensions == tuple(
            claim.dimension
            for claim in contract.claims
            if claim.status in {S.PARTIAL, S.UNKNOWN, S.IRREPRODUCIBLE}
        )
        assert audit.deferred_dimensions == tuple(
            claim.dimension for claim in contract.claims if claim.status is S.DEFERRED_OUT_OF_SCOPE
        )
        assert contract.claim(D.DATASET_HASH).status is S.PARTIAL
        assert contract.claim(D.SERIALIZATION).status is not S.EXACT
    with pytest.raises(TypeError):
        FINAL_REPRODUCTION_STATUS["ninth_state"] = get_final_reproduction_status(  # type: ignore[index]
            "initial_preseason_camp_recovery"
        )
    with pytest.raises(FrozenInstanceError):
        get_final_reproduction_status("rich_history_camp_recovery").overall_status = (  # type: ignore[reportAttributeAccessIssue]
            FormulationReproducibility.EXACT
        )
    with pytest.raises(KeyError):
        get_final_reproduction_status("ninth_state")


def test_unknown_and_irreproducible_aggregate_branches_follow_core_claims() -> None:
    contract = get_reproduction_contract("fixed_mode_discrepancy_recovery")
    core = {D.WORLD_LAW, D.COMPLETE_GENERATOR, D.OBSERVATION, D.SCHEMA, D.SPLIT_ASSIGNMENT}
    for claim_status, expected in (
        (S.UNKNOWN, FormulationReproducibility.UNKNOWN),
        (S.IRREPRODUCIBLE, FormulationReproducibility.IRREPRODUCIBLE),
    ):
        changed = replace(
            contract,
            claims=tuple(
                replace(claim, status=claim_status) if claim.dimension in core else claim
                for claim in contract.claims
            ),
        )
        assert _classify_reproduction(changed, ("training", "public_validation")) is expected


def test_every_exact_claim_has_direct_test_evidence() -> None:
    exact_claims = {
        (name, claim.dimension)
        for name, contract in REPRODUCTION_CONTRACTS.items()
        for claim in contract.claims
        if claim.status is S.EXACT
    }
    assert set(_EVIDENCE) == exact_claims
    for references in _EVIDENCE.values():
        assert references
        assert all(_listed_tests(reference) for reference in references)


def test_camp_semantic_rng_uses_random_v2_seed() -> None:
    kwargs = {
        "seed": 811,
        "split": "training",
        "world_id": "world-test",
        "origin_id": "origin-test",
        "cluster_id": "cluster-test",
        "entity_id": "participant-test",
        "event_or_assessment_id": "assessment-test",
        "purpose_namespace": "trial_noise",
    }
    material = {
        "project_id": "CMJRecoveryDynamicsBench",
        "contract_version": OSS_REPRODUCTION_ID,
        "root_seed": kwargs["seed"],
        **{key: value for key, value in kwargs.items() if key != "seed"},
    }
    payload = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    derived = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big", signed=False)
    expected = random.Random()
    expected.seed(derived, version=2)
    actual = camp_history_module._rng(  # pyright: ignore[reportPrivateUsage]
        seed=811,
        split="training",
        world_id="world-test",
        origin_id="origin-test",
        cluster_id="cluster-test",
        entity_id="participant-test",
        event_or_assessment_id="assessment-test",
        purpose_namespace="trial_noise",
    )
    assert actual.random() == expected.random()


def test_public_roots_are_first_class_and_match_claim_scope() -> None:
    assert set(PUBLIC_ROOT_AUTHORITIES) == set(REPRODUCTION_CONTRACTS)
    for name, contract in REPRODUCTION_CONTRACTS.items():
        authority_key = get_final_reproduction_status(name).public_seed_authority_key
        assert authority_key is not None
        assert authority_key == name
        authority = get_public_root_authority(authority_key)
        assert authority.benchmark == name
        assert authority.status is contract.claim(D.SEED_AUTHORITY).status
        if authority.status is S.EXACT:
            assert (authority.shared_root is not None) != (
                authority.training_root is not None or authority.validation_root is not None
            )
            assert authority.shared_root or (authority.training_root and authority.validation_root)
        else:
            assert authority.status is S.UNKNOWN
            assert (
                authority.shared_root
                is authority.training_root
                is authority.validation_root
                is None
            )
    assert get_public_root_authority("rich_history_camp_recovery").training_root is not None
    assert get_public_root_authority("rich_history_camp_recovery").validation_root is not None
    rich_roots = get_public_root_authority("rich_history_camp_recovery")
    assert PUBLIC_SPLITS["public_train"].root_seed != rich_roots.training_root
    assert PUBLIC_SPLITS["public_validation"].root_seed != rich_roots.validation_root
    assert get_public_root_authority("initial_preseason_camp_recovery").status is S.UNKNOWN
    assert get_public_root_authority("canonical_preseason_camp_recovery").status is S.UNKNOWN
    assert get_public_root_authority("threshold_response_recovery").status is S.EXACT


def test_camp_clean_room_seeds_remain_nonhistorical() -> None:
    roots_before = dict(PUBLIC_ROOT_AUTHORITIES)
    for generate in (generate_initial_camp_sample, generate_canonical_camp_sample):
        first = generate(seed=1403, participant_count=2)
        replay = generate(seed=1403, participant_count=2)
        other = generate(seed=1404, participant_count=2)
        assert first.to_jsonl() == replay.to_jsonl()
        assert first.to_jsonl() != other.to_jsonl()
        assert first.identity.seed_authority == "new_reproduction_authority"
        assert first.identity.historical_status(D.SEED_AUTHORITY) is S.UNKNOWN
    assert dict(PUBLIC_ROOT_AUTHORITIES) == roots_before


def test_bounded_single_exposure_root_replay() -> None:
    roots_before = dict(PUBLIC_ROOT_AUTHORITIES)
    structural_keys = ((0, 0), (1, 17), (95, 249))

    base_benchmarks = (
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
    )
    for index, benchmark in enumerate(base_benchmarks):
        root = f"m2-clean-room-audit-{index}"
        for camp_index, participant_index in structural_keys:
            first = generate_episode(
                benchmark_name=benchmark,
                split="train",
                camp_index=camp_index,
                participant_index=participant_index,
                root_seed=root,
            )
            assert (
                generate_episode(
                    benchmark_name=benchmark,
                    split="train",
                    camp_index=camp_index,
                    participant_index=participant_index,
                    root_seed=root,
                )
                == first
            )
            other_root_episode = generate_episode(
                benchmark_name=benchmark,
                split="train",
                camp_index=camp_index,
                participant_index=participant_index,
                root_seed=f"{root}-different",
            )
            if (camp_index, participant_index) == structural_keys[0]:
                assert other_root_episode != first
                assert tuple(h for h, _, _ in first.current.innovations) == ("H24", "H48", "H72")
                assert len(first.prior_episodes) == 4
        assert get_reproduction_contract(benchmark).claim(D.SEED_AUTHORITY).status is S.EXACT
        assert get_public_root_authority(benchmark) is roots_before[benchmark]

    later_benchmarks: tuple[LaterFormulation, ...] = (
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    )
    for index, benchmark in enumerate(later_benchmarks, start=len(base_benchmarks)):
        root = f"m2-clean-room-audit-{index}"
        for camp_index, participant_index in structural_keys:
            first = generate_later_episode(
                benchmark_name=benchmark,
                split="train",
                camp_index=camp_index,
                participant_index=participant_index,
                root_seed=root,
            )
            assert (
                generate_later_episode(
                    benchmark_name=benchmark,
                    split="train",
                    camp_index=camp_index,
                    participant_index=participant_index,
                    root_seed=root,
                )
                == first
            )
            other_root_episode = generate_later_episode(
                benchmark_name=benchmark,
                split="train",
                camp_index=camp_index,
                participant_index=participant_index,
                root_seed=f"{root}-different",
            )
            if (camp_index, participant_index) == structural_keys[0]:
                assert other_root_episode != first
                assert tuple(h for h, _, _ in first.current.innovations) == ("H24", "H48", "H72")
                assert len(first.prior_episodes) == 4
        assert get_reproduction_contract(benchmark).claim(D.SEED_AUTHORITY).status is S.EXACT
        assert get_public_root_authority(benchmark) is roots_before[benchmark]
    assert (
        OSS_ROOT_SEED != get_public_root_authority("preliminary_post_exposure_recovery").shared_root
    )


def test_rich_history_oss_root_replay_does_not_change_historical_authority() -> None:
    authority = get_public_root_authority("rich_history_camp_recovery")
    roots_before = dict(PUBLIC_ROOT_AUTHORITIES)
    first = next(iter_rich_history_public_split("public_train", root_seed="audit-rich-oss-a"))
    replay = next(iter_rich_history_public_split("public_train", root_seed="audit-rich-oss-a"))
    other = next(iter_rich_history_public_split("public_train", root_seed="audit-rich-oss-b"))
    assert first == replay
    assert first != other
    assert get_public_root_authority("rich_history_camp_recovery") is authority
    assert dict(PUBLIC_ROOT_AUTHORITIES) == roots_before


def test_d04_membership_and_fingerprints_replay_twice() -> None:
    roots = get_public_root_authority("rich_history_camp_recovery")
    expected: tuple[tuple[PublicSplitName, int], ...] = (
        ("public_train", 15182),
        ("public_validation", 3795),
    )
    for split, rows_expected in expected:
        root = roots.training_root if split == "public_train" else roots.validation_root
        assert root is not None
        first = list(replay_d04_membership(split, root_seed=root))
        second = list(replay_d04_membership(split, root_seed=root))
        assert len(first) == rows_expected
        assert first == second
        assert d04_membership_fingerprint(split, root_seed=root) == d04_membership_fingerprint(
            split, root_seed=root
        )


def test_semantic_schema_sizes_and_observation_boundaries() -> None:
    assert (
        get_reproduction_contract("initial_preseason_camp_recovery").claim(D.SCHEMA).status
        is S.PARTIAL
    )
    assert (
        get_reproduction_contract("canonical_preseason_camp_recovery").claim(D.SCHEMA).status
        is S.EXACT
    )
    assert len(R02_FIELD_NAMES) == 135
    assert len(PREDICTOR_FIELDS) == 82
    assert len(ROW_KEY_FIELDS) == 3
    assert len(TARGET_FIELDS) == 2
    assert not set(ROW_KEY_FIELDS).intersection(PREDICTOR_FIELDS)
    assert all("label." not in field for field in PREDICTOR_FIELDS)
    assert (
        get_reproduction_contract("preliminary_post_exposure_recovery").claim(D.OBSERVATION).status
        is S.PARTIAL
    )
    for name in (
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    ):
        assert get_reproduction_contract(name).claim(D.OBSERVATION).status is S.EXACT
        assert get_reproduction_contract(name).claim(D.SCHEMA).status is S.EXACT


def test_cross_formulation_transitions_keep_alternates_as_siblings() -> None:
    initial = BENCHMARK_REGISTRY["initial_preseason_camp_recovery"]
    canonical = BENCHMARK_REGISTRY["canonical_preseason_camp_recovery"]
    rich = BENCHMARK_REGISTRY["rich_history_camp_recovery"]
    assert initial.dynamics.name == canonical.dynamics.name
    assert initial.observation.name == canonical.observation.name
    assert initial.task.name == canonical.task.name
    assert initial.dataset_identity != canonical.dataset_identity
    assert (
        get_reproduction_contract(initial.name).claim(D.SCHEMA).status is S.PARTIAL
        and get_reproduction_contract(canonical.name).claim(D.SCHEMA).status is S.EXACT
    )
    assert rich.dynamics.name != canonical.dynamics.name
    assert rich.observation.name != canonical.observation.name
    assert rich.dataset_identity != canonical.dataset_identity
    assert rich.evaluation_identity.name != canonical.evaluation_identity.name
    rich_transition = next(t for t in BENCHMARK_TRANSITIONS if t.target_benchmark == rich.name)
    assert rich_transition.source_benchmark is None
    assert {
        ChangeClass.WORLD_CHANGE,
        ChangeClass.OBSERVATION_CHANGE,
        ChangeClass.DATASET_SPLIT_CHANGE,
        ChangeClass.EVALUATION_CHANGE,
    }.issubset(rich_transition.change_classes)

    preliminary = BENCHMARK_REGISTRY["preliminary_post_exposure_recovery"]
    phase = BENCHMARK_REGISTRY["phase_consistent_post_exposure_recovery"]
    correlated = BENCHMARK_REGISTRY["correlated_exposure_recovery"]
    threshold = BENCHMARK_REGISTRY["threshold_response_recovery"]
    fixed = BENCHMARK_REGISTRY["fixed_mode_discrepancy_recovery"]
    prelim_lineage = get_benchmark_lineage(preliminary.name)
    phase_lineage = get_benchmark_lineage(phase.name)
    correlated_lineage = get_benchmark_lineage(correlated.name)
    threshold_lineage = get_benchmark_lineage(threshold.name)
    fixed_lineage = get_benchmark_lineage(fixed.name)

    assert preliminary.dynamics.name == phase.dynamics.name
    assert preliminary.task.name == phase.task.name
    assert prelim_lineage.lineage.representation_name == phase_lineage.lineage.representation_name
    assert preliminary.observation.name != phase.observation.name
    assert preliminary.dataset_identity != phase.dataset_identity

    assert phase.observation.name == correlated.observation.name
    assert phase.task.name == correlated.task.name
    assert (
        phase_lineage.lineage.representation_name == correlated_lineage.lineage.representation_name
    )
    assert phase.dynamics.name != correlated.dynamics.name
    assert phase.dataset_identity != correlated.dataset_identity

    for alternate, lineage in ((threshold, threshold_lineage), (fixed, fixed_lineage)):
        assert alternate.parent_name == correlated.name
        assert alternate.task.name == correlated.task.name
        assert alternate.observation.name == correlated.observation.name
        assert lineage.lineage.representation_name == correlated_lineage.lineage.representation_name
        assert alternate.dynamics.name != correlated.dynamics.name
        assert alternate.dataset_identity != correlated.dataset_identity
    assert threshold.status is BenchmarkStatus.PROPOSED
    assert fixed.status is BenchmarkStatus.ACTIVE_CANDIDATE
    assert THRESHOLD_RESPONSE_RECOVERY is threshold
    threshold_transition = next(
        t for t in BENCHMARK_TRANSITIONS if t.target_benchmark == threshold.name
    )
    assert threshold_transition.source_benchmark == correlated.name
    assert not threshold_transition.accepted_successor
    assert {
        ChangeClass.WORLD_CHANGE,
        ChangeClass.DATASET_SPLIT_CHANGE,
        ChangeClass.EVALUATION_CHANGE,
    }.issubset(threshold_transition.change_classes)
    fixed_transition = next(t for t in BENCHMARK_TRANSITIONS if t.target_benchmark == fixed.name)
    assert fixed_transition.source_benchmark == correlated.name
    assert not fixed_transition.accepted_successor
    assert not any(
        t.source_benchmark == threshold.name and t.target_benchmark == fixed.name
        for t in BENCHMARK_TRANSITIONS
    )


def test_evaluation_authority_and_hidden_data_stay_separate() -> None:
    for name in (
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
        "rich_history_camp_recovery",
    ):
        evaluation = get_reproduction_contract(name).evaluation
        assert evaluation.production_status is ProductionScorerStatus.ACCEPTED
        assert (
            evaluation.calibration_reference_status is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
        )
        assert evaluation.calibration_reference_value is None
        benchmark_evaluation = BENCHMARK_REGISTRY[name].evaluation_identity
        assert benchmark_evaluation.name == evaluation.production_scorer
        assert benchmark_evaluation.is_accepted_production_scorer
    assert (
        len(BENCHMARK_REGISTRY["rich_history_camp_recovery"].evaluation_identity.scoring_cells)
        == 24
    )

    for name in (
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "fixed_mode_discrepancy_recovery",
    ):
        evaluation = get_reproduction_contract(name).evaluation
        assert evaluation.production_status is ProductionScorerStatus.UNIMPLEMENTED
        assert evaluation.production_scorer is None
    assert POST_EXPOSURE_RESEARCH_EVALUATION.category is MetricCategory.RESEARCH_DIAGNOSTIC
    assert all(
        benchmark.evaluation_identity is not POST_EXPOSURE_RESEARCH_EVALUATION
        for benchmark in BENCHMARK_REGISTRY.values()
    )

    threshold = get_reproduction_contract("threshold_response_recovery")
    assert threshold.evaluation.production_status is ProductionScorerStatus.PROPOSED
    assert (
        threshold.evaluation.calibration_reference_status
        is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
    )
    assert threshold.evaluation.calibration_reference_value is None
    assert threshold.claim(D.EVALUATION).status is S.PARTIAL
    assert BENCHMARK_REGISTRY[
        "threshold_response_recovery"
    ].evaluation_identity.production_acceptance is (ProductionAcceptance.PROPOSED_UNRESOLVED)
    assert BENCHMARK_REGISTRY["threshold_response_recovery"].evaluation_identity.is_proposed_scorer
    assert not BENCHMARK_REGISTRY[
        "threshold_response_recovery"
    ].evaluation_identity.is_accepted_production_scorer
    assert len(THRESHOLD_RESPONSE_RECOVERY.evaluation_identity.scoring_cells) == 12
    threshold_reference = get_model_family("threshold_response_reference_predictor")
    assert threshold_reference.configuration_status is ConfigurationStatus.UNKNOWN
    assert threshold_reference.checkpoint_status is ArtifactAvailability.PRESERVED_PRIVATELY
    assert get_final_reproduction_status("threshold_response_recovery").overall_status is (
        FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
    )

    rich_hidden = next(
        split
        for split in get_reproduction_contract("rich_history_camp_recovery").splits
        if split.role is SplitRole.HIDDEN_TEST
    )
    assert rich_hidden.materialization_state is MaterializationState.NOT_RECOVERED
    assert rich_hidden.rows is None and rich_hidden.reference_hash is None
    assert HISTORICAL_HIDDEN_DESIGN.materialization == "NOT_RECOVERED"

    threshold_hidden = next(
        split for split in threshold.splits if split.role is SplitRole.HIDDEN_TEST
    )
    assert threshold_hidden.assignment_status is S.PARTIAL
    assert threshold_hidden.planned_rows == 15750
    assert threshold_hidden.materialization_state is MaterializationState.UNKNOWN
    assert threshold_hidden.materialization_status is S.UNKNOWN
    assert threshold_hidden.rows is None and threshold_hidden.reference_hash is None

    fixed_hidden = next(
        split
        for split in get_reproduction_contract("fixed_mode_discrepancy_recovery").splits
        if split.role is SplitRole.HIDDEN_TEST
    )
    assert fixed_hidden.assignment_status is S.NOT_APPLICABLE
    assert fixed_hidden.materialization_state is MaterializationState.NOT_MATERIALIZED
    assert fixed_hidden.materialization_status is S.NOT_APPLICABLE
    assert fixed_hidden.rows is None and fixed_hidden.planned_rows is None
    assert fixed_hidden.reference_hash is None
    assert (
        LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].public_data_qualification_status
        == "PASS"
    )
    assert (
        LATER_SOURCE_CLOSURES["fixed_mode_discrepancy_recovery"].scientific_adjudication_status
        == "NOT_COMPLETED"
    )
    assert (
        LATER_SOURCE_CLOSURES["threshold_response_recovery"].scientific_adjudication_status is None
    )


def test_historical_model_results_and_dataset_bytes_remain_deferred() -> None:
    for contract in REPRODUCTION_CONTRACTS.values():
        assert contract.claim(D.MODEL_CONFIGURATION).status is S.DEFERRED_OUT_OF_SCOPE
        assert contract.claim(D.HISTORICAL_RESULT).status is S.DEFERRED_OUT_OF_SCOPE
        assert contract.claim(D.DATASET_HASH).status is S.PARTIAL
    assert S.DEFERRED_OUT_OF_SCOPE is not S.IRREPRODUCIBLE
    assert get_final_reproduction_status("fixed_mode_discrepancy_recovery").overall_status is (
        FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
    )
