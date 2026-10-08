"""Exactness claims fail closed when any byte-identity authority is missing."""

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from cmj_recovery_dynamics.reproduction import (
    REPRODUCTION_CONTRACTS,
    BenchmarkReproductionContract,
    CalibrationReferenceStatus,
    EvaluationAuthority,
    EvaluationRole,
    MaterializationState,
    ProductionScorerStatus,
    ReferenceHash,
    SerializationAuthority,
    SplitRole,
    get_reproduction_contract,
)
from cmj_recovery_dynamics.reproduction import (
    ReproductionDimension as D,
)
from cmj_recovery_dynamics.reproduction import (
    ReproductionStatus as S,
)

EXPECTED_BENCHMARKS = {
    "initial_preseason_camp_recovery",
    "canonical_preseason_camp_recovery",
    "rich_history_camp_recovery",
    "preliminary_post_exposure_recovery",
    "phase_consistent_post_exposure_recovery",
    "correlated_exposure_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
}
_HASH_SCOPE = ("training", "public_validation")
_HASH_PREREQUISITES = {
    D.WORLD_LAW,
    D.COMPLETE_GENERATOR,
    D.RNG_ALGORITHM,
    D.RNG_STATE,
    D.SEED_AUTHORITY,
    D.RNG_STREAM_CONSTRUCTION,
    D.RNG_DRAW_ORDER,
    D.RNG_SUBSTREAM_STRATEGY,
    D.OBSERVATION,
    D.SCHEMA,
    D.ROW_ORDERING,
    D.SERIALIZATION,
}


def _exact_public_hash_contract() -> BenchmarkReproductionContract:
    contract = get_reproduction_contract("fixed_mode_discrepancy_recovery")
    claims = tuple(
        replace(
            claim,
            status=S.EXACT,
            missing=(),
            milestone_owner=None,
            scope=_HASH_SCOPE
            if claim.dimension in {D.SEED_AUTHORITY, D.SPLIT_ASSIGNMENT}
            else claim.scope,
        )
        if claim.dimension in _HASH_PREREQUISITES
        else replace(claim, status=S.EXACT, missing=(), milestone_owner=None, scope=_HASH_SCOPE)
        if claim.dimension is D.DATASET_HASH
        else claim
        for claim in contract.claims
    )
    splits = tuple(
        replace(
            split,
            assignment_status=S.EXACT,
            missing_assignment=(),
            materialization_status=S.EXACT,
            missing_materialization=(),
        )
        if split.role in {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}
        else split
        for split in contract.splits
    )
    evaluation = EvaluationAuthority(
        roles=(EvaluationRole.ACCEPTED_BENCHMARK_SCORER,),
        production_status=ProductionScorerStatus.ACCEPTED,
        production_scorer="test_exact_scorer",
        calibration_reference_status=CalibrationReferenceStatus.PUBLIC,
        calibration_reference_value=0.5,
        rationale="Test-only complete evaluation authority.",
    )
    serialization = SerializationAuthority(
        file_format="PARQUET",
        writer_implementation="pyarrow test writer 1.0",
        column_order="fixed schema order",
        index_handling="index disabled",
        float_representation="IEEE-754 binary64",
        metadata="fixed metadata map",
        compression_and_row_groups="uncompressed, fixed row groups",
    )
    return replace(
        contract,
        claims=claims,
        splits=splits,
        evaluation=evaluation,
        serialization=serialization,
    )


def test_all_eight_benchmarks_have_one_explicit_claim_per_dimension() -> None:
    assert set(REPRODUCTION_CONTRACTS) == EXPECTED_BENCHMARKS
    for name, contract in REPRODUCTION_CONTRACTS.items():
        assert get_reproduction_contract(name) is contract
        assert {claim.dimension for claim in contract.claims} == set(D)
        assert len(contract.claims) == len(D)
        assert all(isinstance(claim.status, S) for claim in contract.claims)
        assert contract.authority.m1_issues == (
            "RES-363",
            "RES-364",
            "RES-365",
            "RES-366",
            "RES-367",
            "RES-368",
        )


def test_unknown_and_deferred_are_queryable_and_distinct_from_irreproducible() -> None:
    initial = get_reproduction_contract("initial_preseason_camp_recovery")
    fixed = get_reproduction_contract("fixed_mode_discrepancy_recovery")
    assert initial.claim(D.SEED_AUTHORITY).status is S.UNKNOWN
    assert initial.claim(D.SEED_AUTHORITY).missing
    assert fixed.claim(D.HISTORICAL_RESULT).status is S.DEFERRED_OUT_OF_SCOPE
    assert fixed.claim(D.HISTORICAL_RESULT).milestone_owner == "M3/M4"
    assert S.DEFERRED_OUT_OF_SCOPE is not S.IRREPRODUCIBLE
    assert S.DEFERRED_OUT_OF_SCOPE.value != S.IRREPRODUCIBLE.value


def test_independent_world_exactness_does_not_promote_rng_or_data_hash() -> None:
    for name, contract in REPRODUCTION_CONTRACTS.items():
        assert contract.claim(D.WORLD_LAW).status is S.EXACT
        assert contract.claim(D.DATASET_HASH).status is S.PARTIAL
        ordering = contract.claim(D.ROW_ORDERING).status
        assert ordering is (S.EXACT if name == "rich_history_camp_recovery" else S.UNKNOWN)


def test_exact_public_hash_claim_is_possible_only_with_complete_prerequisites() -> None:
    contract = _exact_public_hash_contract()
    assert contract.claim(D.DATASET_HASH).status is S.EXACT
    assert contract.claim(D.DATASET_HASH).scope == _HASH_SCOPE


def test_exact_split_membership_does_not_make_dataset_hash_exact() -> None:
    contract = get_reproduction_contract("rich_history_camp_recovery")
    assert contract.claim(D.SPLIT_ASSIGNMENT).status is S.EXACT
    assert contract.claim(D.RNG_ALGORITHM).status is S.PARTIAL
    assert contract.claim(D.RNG_STATE).status is S.PARTIAL
    assert contract.claim(D.SERIALIZATION).status is S.SEMANTICALLY_EQUIVALENT
    with pytest.raises(ValueError, match="every generator and byte prerequisite"):
        replace(
            contract,
            claims=tuple(
                replace(claim, status=S.EXACT, missing=())
                if claim.dimension is D.DATASET_HASH
                else claim
                for claim in contract.claims
            ),
        )


@pytest.mark.parametrize(
    ("benchmark", "file_format"),
    (
        ("initial_preseason_camp_recovery", "JSONL"),
        ("canonical_preseason_camp_recovery", "JSONL"),
        ("rich_history_camp_recovery", "Parquet"),
        ("preliminary_post_exposure_recovery", "Parquet"),
        ("phase_consistent_post_exposure_recovery", "Parquet"),
        ("correlated_exposure_recovery", "Parquet"),
        ("threshold_response_recovery", "Parquet"),
        ("fixed_mode_discrepancy_recovery", "Parquet"),
    ),
)
def test_file_format_is_separate_from_byte_serialization_exactness(
    benchmark: str,
    file_format: str,
) -> None:
    contract = get_reproduction_contract(benchmark)
    assert contract.serialization.file_format == file_format
    assert contract.serialization.writer_implementation is None
    assert contract.claim(D.SERIALIZATION).status is not S.EXACT


@pytest.mark.parametrize(
    "dimension",
    (
        D.RNG_ALGORITHM,
        D.RNG_STATE,
        D.SEED_AUTHORITY,
        D.RNG_STREAM_CONSTRUCTION,
        D.RNG_DRAW_ORDER,
        D.RNG_SUBSTREAM_STRATEGY,
    ),
)
def test_missing_rng_authority_blocks_byte_exact_dataset_claim(
    dimension: D,
) -> None:
    contract = _exact_public_hash_contract()
    claims = tuple(
        replace(claim, status=S.PARTIAL, missing=("defect injected",))
        if claim.dimension is dimension
        else claim
        for claim in contract.claims
    )
    with pytest.raises(ValueError, match="every generator and byte prerequisite"):
        replace(contract, claims=claims)


def test_missing_serialization_authority_blocks_byte_exact_dataset_claim() -> None:
    contract = _exact_public_hash_contract()
    with pytest.raises(ValueError, match="every generator and byte prerequisite"):
        replace(
            contract,
            claims=tuple(
                replace(claim, status=S.PARTIAL, missing=("writer missing",))
                if claim.dimension is D.SERIALIZATION
                else claim
                for claim in contract.claims
            ),
        )
    with pytest.raises(ValueError, match="complete serialization authority"):
        replace(
            contract,
            serialization=replace(contract.serialization, writer_implementation=None),
        )


def test_missing_expected_hash_blocks_byte_exact_dataset_claim() -> None:
    contract = _exact_public_hash_contract()
    training = next(split for split in contract.splits if split.name == "training")
    without_training_hash = replace(
        training,
        materialization_status=S.PARTIAL,
        missing_materialization=("expected hash missing",),
        reference_hash=None,
    )
    splits = tuple(
        without_training_hash if split.name == training.name else split for split in contract.splits
    )
    hashes = tuple(item for item in contract.reference_hashes if item.split_name != "training")
    with pytest.raises(ValueError, match="exact split and reference-hash authority"):
        replace(contract, splits=splits, reference_hashes=hashes)


@pytest.mark.parametrize(
    "state",
    (
        MaterializationState.UNKNOWN,
        MaterializationState.NOT_RECOVERED,
        MaterializationState.NOT_MATERIALIZED,
    ),
)
def test_hidden_split_cannot_be_promoted_to_exact_materialization(
    state: MaterializationState,
) -> None:
    hidden = get_reproduction_contract("fixed_mode_discrepancy_recovery").splits[-1]
    with pytest.raises(ValueError, match="hidden data cannot be promoted"):
        replace(
            hidden,
            materialization_state=state,
            materialization_status=S.EXACT,
            missing_materialization=(),
            reference_hash=ReferenceHash(
                "hidden_test", "0" * 64, "defect injection", publication_safe=True
            ),
        )


def test_unimplemented_production_evaluation_cannot_be_exact() -> None:
    contract = get_reproduction_contract("fixed_mode_discrepancy_recovery")
    with pytest.raises(ValueError, match="proposed or unimplemented production evaluation"):
        replace(
            contract,
            claims=tuple(
                replace(claim, status=S.EXACT, missing=())
                if claim.dimension is D.EVALUATION
                else claim
                for claim in contract.claims
            ),
        )


def test_threshold_score_remains_proposed_and_unresolved() -> None:
    threshold = get_reproduction_contract("threshold_response_recovery")
    assert threshold.evaluation.production_status is ProductionScorerStatus.PROPOSED
    assert EvaluationRole.PROPOSED_BENCHMARK_SCORER in threshold.evaluation.roles
    assert threshold.claim(D.EVALUATION).status is S.PARTIAL


def test_camp_calibration_values_remain_unavailable() -> None:
    for name in (
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
        "rich_history_camp_recovery",
    ):
        evaluation = get_reproduction_contract(name).evaluation
        assert (
            evaluation.calibration_reference_status is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
        )
        assert evaluation.calibration_reference_value is None


def test_initial_and_canonical_results_remain_non_comparable() -> None:
    for name in ("initial_preseason_camp_recovery", "canonical_preseason_camp_recovery"):
        claim = get_reproduction_contract(name).claim(D.HISTORICAL_RESULT)
        assert claim.status is S.DEFERRED_OUT_OF_SCOPE
        assert "non-comparable" in claim.rationale


@pytest.mark.parametrize("missing_dimension", (D.MODEL_CONFIGURATION, D.EVALUATION))
def test_historical_result_exact_requires_model_and_evaluation_authority(
    missing_dimension: D,
) -> None:
    contract = _exact_public_hash_contract()
    claims = tuple(
        replace(
            claim,
            status=(S.PARTIAL if claim.dimension is missing_dimension else S.EXACT),
            missing=("defect injected",) if claim.dimension is missing_dimension else (),
            milestone_owner=None,
        )
        for claim in contract.claims
    )
    with pytest.raises(ValueError, match="exact historical results require"):
        replace(contract, claims=claims)


def test_core_reproduction_modules_do_not_import_historical_alias_provenance() -> None:
    package = Path(__file__).parents[1] / "src" / "cmj_recovery_dynamics" / "reproduction"
    forbidden = {"cmj_recovery_dynamics.provenance", "historical_aliases", "lineage_aliases"}
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        )
        assert not any(
            module in forbidden
            or module.endswith(tuple(forbidden - {"cmj_recovery_dynamics.provenance"}))
            for module in imported
        )
