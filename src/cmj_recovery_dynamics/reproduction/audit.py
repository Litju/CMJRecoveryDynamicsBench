"""Final formulation-level reproducibility views derived from M1 contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from cmj_recovery_dynamics.reproduction.contracts import (
    BenchmarkReproductionContract,
    ReproductionDimension,
    ReproductionStatus,
    SplitRole,
)
from cmj_recovery_dynamics.reproduction.registry import REPRODUCTION_CONTRACTS


class FormulationReproducibility(StrEnum):
    EXACT = "EXACT"
    SEMANTICALLY_REPRODUCIBLE = "SEMANTICALLY_REPRODUCIBLE"
    PARTIALLY_REPRODUCIBLE = "PARTIALLY_REPRODUCIBLE"
    UNKNOWN = "UNKNOWN"
    IRREPRODUCIBLE = "IRREPRODUCIBLE"


@dataclass(frozen=True, slots=True)
class BenchmarkReproductionAudit:
    contract: BenchmarkReproductionContract
    overall_status: FormulationReproducibility
    public_scope: tuple[str, ...]
    unresolved_dimensions: tuple[ReproductionDimension, ...]
    deferred_dimensions: tuple[ReproductionDimension, ...]
    exact_dimensions: tuple[ReproductionDimension, ...]
    semantic_dimensions: tuple[ReproductionDimension, ...]
    public_seed_authority_key: str | None

    @property
    def benchmark(self) -> str:
        return self.contract.benchmark


_EXACT_IDENTITY_DIMENSIONS = (
    ReproductionDimension.WORLD_LAW,
    ReproductionDimension.COMPLETE_GENERATOR,
    ReproductionDimension.RNG_ALGORITHM,
    ReproductionDimension.RNG_STATE,
    ReproductionDimension.SEED_AUTHORITY,
    ReproductionDimension.RNG_STREAM_CONSTRUCTION,
    ReproductionDimension.RNG_DRAW_ORDER,
    ReproductionDimension.RNG_SUBSTREAM_STRATEGY,
    ReproductionDimension.OBSERVATION,
    ReproductionDimension.SCHEMA,
    ReproductionDimension.SPLIT_ASSIGNMENT,
    ReproductionDimension.ROW_ORDERING,
    ReproductionDimension.SERIALIZATION,
    ReproductionDimension.DATASET_HASH,
    ReproductionDimension.EVALUATION,
)
_SEMANTIC_CORE = (
    ReproductionDimension.WORLD_LAW,
    ReproductionDimension.COMPLETE_GENERATOR,
    ReproductionDimension.OBSERVATION,
    ReproductionDimension.SCHEMA,
    ReproductionDimension.SPLIT_ASSIGNMENT,
)


def _public_scope(contract: BenchmarkReproductionContract) -> tuple[str, ...]:
    return tuple(
        split.name
        for split in contract.splits
        if split.role in {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}
    )


def _scope_covers_public_splits(
    contract: BenchmarkReproductionContract,
    dimension: ReproductionDimension,
    public_scope: tuple[str, ...],
) -> bool:
    claim = contract.claim(dimension)
    if claim.scope and not set(public_scope).issubset(claim.scope):
        return False
    if dimension is ReproductionDimension.SPLIT_ASSIGNMENT:
        return all(
            split.assignment_status is ReproductionStatus.EXACT
            for split in contract.splits
            if split.name in public_scope
        )
    return True


def _classify(
    contract: BenchmarkReproductionContract,
    public_scope: tuple[str, ...],
) -> FormulationReproducibility:
    statuses = {dimension: contract.claim(dimension).status for dimension in ReproductionDimension}
    if all(
        statuses[dimension] is ReproductionStatus.EXACT for dimension in _EXACT_IDENTITY_DIMENSIONS
    ) and all(
        _scope_covers_public_splits(contract, dimension, public_scope)
        for dimension in _EXACT_IDENTITY_DIMENSIONS
    ):
        return FormulationReproducibility.EXACT

    semantic = (
        statuses[ReproductionDimension.WORLD_LAW] is ReproductionStatus.EXACT
        and statuses[ReproductionDimension.COMPLETE_GENERATOR]
        in {ReproductionStatus.EXACT, ReproductionStatus.SEMANTICALLY_EQUIVALENT}
        and all(
            statuses[dimension] is ReproductionStatus.EXACT
            for dimension in _SEMANTIC_CORE
            if dimension is not ReproductionDimension.COMPLETE_GENERATOR
        )
        and all(
            _scope_covers_public_splits(contract, dimension, public_scope)
            for dimension in _SEMANTIC_CORE
        )
    )
    if semantic:
        return FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE

    core = tuple(statuses[dimension] for dimension in _SEMANTIC_CORE)
    if all(status is ReproductionStatus.IRREPRODUCIBLE for status in core):
        return FormulationReproducibility.IRREPRODUCIBLE
    if all(
        status in {ReproductionStatus.UNKNOWN, ReproductionStatus.NOT_APPLICABLE} for status in core
    ):
        return FormulationReproducibility.UNKNOWN
    return FormulationReproducibility.PARTIALLY_REPRODUCIBLE


def _audit(contract: BenchmarkReproductionContract) -> BenchmarkReproductionAudit:
    claims = contract.claims
    public_scope = _public_scope(contract)
    return BenchmarkReproductionAudit(
        contract=contract,
        overall_status=_classify(contract, public_scope),
        public_scope=public_scope,
        unresolved_dimensions=tuple(
            claim.dimension
            for claim in claims
            if claim.status
            in {
                ReproductionStatus.PARTIAL,
                ReproductionStatus.UNKNOWN,
                ReproductionStatus.IRREPRODUCIBLE,
            }
        ),
        deferred_dimensions=tuple(
            claim.dimension
            for claim in claims
            if claim.status is ReproductionStatus.DEFERRED_OUT_OF_SCOPE
        ),
        exact_dimensions=tuple(
            claim.dimension for claim in claims if claim.status is ReproductionStatus.EXACT
        ),
        semantic_dimensions=tuple(
            claim.dimension
            for claim in claims
            if claim.status is ReproductionStatus.SEMANTICALLY_EQUIVALENT
        ),
        public_seed_authority_key=contract.benchmark,
    )


FINAL_REPRODUCTION_STATUS: Mapping[str, BenchmarkReproductionAudit] = MappingProxyType(
    {name: _audit(contract) for name, contract in REPRODUCTION_CONTRACTS.items()}
)


def get_final_reproduction_status(name: str) -> BenchmarkReproductionAudit:
    """Return the immutable final audit derived from the named M1 reproduction contract."""
    return FINAL_REPRODUCTION_STATUS[name]
