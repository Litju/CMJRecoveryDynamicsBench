"""Typed authority claims for reproducing benchmark states."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ReproductionStatus(StrEnum):
    EXACT = "EXACT"
    SEMANTICALLY_EQUIVALENT = "SEMANTICALLY_EQUIVALENT"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    IRREPRODUCIBLE = "IRREPRODUCIBLE"
    DEFERRED_OUT_OF_SCOPE = "DEFERRED_OUT_OF_SCOPE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReproductionDimension(StrEnum):
    WORLD_LAW = "world_law"
    COMPLETE_GENERATOR = "complete_generator"
    RNG_ALGORITHM = "rng_algorithm"
    RNG_STATE = "rng_state"
    SEED_AUTHORITY = "seed_authority"
    RNG_STREAM_CONSTRUCTION = "rng_stream_construction"
    RNG_DRAW_ORDER = "rng_draw_order"
    RNG_SUBSTREAM_STRATEGY = "rng_substream_strategy"
    OBSERVATION = "observation"
    SCHEMA = "schema"
    SPLIT_ASSIGNMENT = "split_assignment"
    ROW_ORDERING = "row_ordering"
    SERIALIZATION = "serialization"
    DATASET_HASH = "dataset_hash"
    EVALUATION = "evaluation"
    MODEL_CONFIGURATION = "model_configuration"
    HISTORICAL_RESULT = "historical_result"


class SplitRole(StrEnum):
    TRAINING = "training"
    PUBLIC_VALIDATION = "public_validation"
    HIDDEN_TEST = "hidden_test"


class SplitUnit(StrEnum):
    PARTICIPANT = "participant"
    CAMP = "camp"
    PARTICIPANT_ORIGIN = "participant_origin"
    CAMP_PARTICIPANT_EPISODE = "camp_participant_episode"
    HISTORY = "history"
    UNKNOWN = "unknown"


class MaterializationState(StrEnum):
    MATERIALIZED = "materialized"
    UNKNOWN = "unknown"
    NOT_RECOVERED = "not_recovered"
    NOT_MATERIALIZED = "not_materialized"
    NOT_APPLICABLE = "not_applicable"


class EvaluationRole(StrEnum):
    ACCEPTED_BENCHMARK_SCORER = "accepted_benchmark_scorer"
    PROPOSED_BENCHMARK_SCORER = "proposed_benchmark_scorer"
    RESEARCH_DIAGNOSTIC = "research_diagnostic"
    QUALIFICATION_STATISTIC = "qualification_statistic"
    MODEL_SELECTION_METRIC = "model_selection_metric"
    UNIMPLEMENTED_EVALUATION = "unimplemented_evaluation"


class ProductionScorerStatus(StrEnum):
    ACCEPTED = "accepted"
    PROPOSED = "proposed"
    UNIMPLEMENTED = "unimplemented"


class CalibrationReferenceStatus(StrEnum):
    PUBLIC = "public"
    LOCKED_NOT_PUBLIC = "locked_not_public"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ReproductionClaim:
    dimension: ReproductionDimension
    status: ReproductionStatus
    rationale: str
    evidence: tuple[str, ...]
    missing: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    milestone_owner: str | None = None

    def __post_init__(self) -> None:
        if not self.rationale or not self.evidence:
            raise ValueError("every reproduction claim needs a rationale and M1 evidence")
        if any(not item for item in (*self.evidence, *self.missing, *self.scope)):
            raise ValueError("claim evidence, missing items, and scope must be non-empty strings")
        if self.status is ReproductionStatus.EXACT and self.missing:
            raise ValueError("an exact claim cannot have missing prerequisites")
        if self.status is ReproductionStatus.DEFERRED_OUT_OF_SCOPE and not self.milestone_owner:
            raise ValueError("deferred claims must name the owning milestone")
        if self.status is not ReproductionStatus.DEFERRED_OUT_OF_SCOPE and self.milestone_owner:
            raise ValueError("only deferred claims may name a milestone owner")


@dataclass(frozen=True, slots=True)
class ReproductionAuthority:
    m1_issues: tuple[str, ...]
    evidence_boundary: str

    def __post_init__(self) -> None:
        if not self.m1_issues or not self.evidence_boundary:
            raise ValueError("reproduction authority must identify its evidence boundary")
        if any(not issue for issue in self.m1_issues):
            raise ValueError("M1 issue references must be non-empty")


@dataclass(frozen=True, slots=True)
class RandomnessAuthority:
    algorithm: str
    state: str
    seed: str
    stream_construction: str
    draw_order: str
    substream_strategy: str

    def __post_init__(self) -> None:
        if any(
            not value
            for value in (
                self.algorithm,
                self.state,
                self.seed,
                self.stream_construction,
                self.draw_order,
                self.substream_strategy,
            )
        ):
            raise ValueError("randomness authority must describe each RNG component")


@dataclass(frozen=True, slots=True)
class SerializationAuthority:
    file_format: str | None
    writer_implementation: str | None
    column_order: str | None
    index_handling: str | None
    float_representation: str | None
    metadata: str | None
    compression_and_row_groups: str | None


@dataclass(frozen=True, slots=True)
class ReferenceHash:
    split_name: str
    digest: str
    authority: str
    algorithm: str = "sha256"
    publication_safe: bool = True

    def __post_init__(self) -> None:
        if not self.split_name or not self.authority:
            raise ValueError("reference hashes need a split name and authority")
        if self.algorithm != "sha256" or re.fullmatch(r"[0-9a-f]{64}", self.digest) is None:
            raise ValueError("reference hashes must be full lowercase SHA-256 digests")


@dataclass(frozen=True, slots=True)
class SplitReproductionAuthority:
    name: str
    role: SplitRole
    grouping_unit: SplitUnit
    assignment_status: ReproductionStatus
    assignment_rationale: str
    materialization_state: MaterializationState
    materialization_status: ReproductionStatus
    materialization_rationale: str
    evidence: tuple[str, ...]
    rows: int | None = None
    missing_assignment: tuple[str, ...] = ()
    missing_materialization: tuple[str, ...] = ()
    reference_hash: ReferenceHash | None = None
    planned_rows: int | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.assignment_rationale or not self.materialization_rationale:
            raise ValueError("split authority must identify its assignment and materialization")
        if not self.evidence or any(not item for item in self.evidence):
            raise ValueError("split authority must cite M1 evidence")
        if self.rows is not None and self.rows < 0:
            raise ValueError("split row counts must be nonnegative")
        if self.planned_rows is not None and self.planned_rows < 0:
            raise ValueError("planned split row counts must be nonnegative")
        if self.assignment_status is ReproductionStatus.EXACT and self.missing_assignment:
            raise ValueError("exact split assignment cannot have missing authority")
        if (
            self.role is SplitRole.HIDDEN_TEST
            and self.materialization_state
            in {
                MaterializationState.UNKNOWN,
                MaterializationState.NOT_RECOVERED,
                MaterializationState.NOT_MATERIALIZED,
            }
            and self.materialization_status is ReproductionStatus.EXACT
        ):
            raise ValueError(
                "unknown or absent hidden data cannot be promoted to exact materialization"
            )
        if self.materialization_status is ReproductionStatus.EXACT:
            if self.materialization_state is not MaterializationState.MATERIALIZED:
                raise ValueError(
                    "a split without materialized lineage cannot be exactly materialized"
                )
            if self.reference_hash is None:
                raise ValueError("exact split materialization requires its expected reference hash")
            if self.missing_materialization:
                raise ValueError("exact split materialization cannot have missing authority")
        if self.materialization_state is MaterializationState.NOT_MATERIALIZED:
            if self.materialization_status is not ReproductionStatus.NOT_APPLICABLE:
                raise ValueError("a split established as not materialized is not applicable")
            if self.reference_hash is not None:
                raise ValueError("a non-materialized split cannot have a materialized-data hash")
        if self.reference_hash is not None and self.reference_hash.split_name != self.name:
            raise ValueError("split reference hash must identify the same split")


@dataclass(frozen=True, slots=True)
class EvaluationAuthority:
    roles: tuple[EvaluationRole, ...]
    production_status: ProductionScorerStatus
    production_scorer: str | None
    research_diagnostics: tuple[str, ...] = ()
    qualification_statistics: tuple[str, ...] = ()
    model_selection_metrics: tuple[str, ...] = ()
    calibration_reference_status: CalibrationReferenceStatus = (
        CalibrationReferenceStatus.NOT_APPLICABLE
    )
    calibration_reference_value: float | None = None
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.roles or not self.rationale:
            raise ValueError("evaluation authority needs roles and a rationale")
        if self.production_status is ProductionScorerStatus.ACCEPTED:
            if (
                self.production_scorer is None
                or EvaluationRole.ACCEPTED_BENCHMARK_SCORER not in self.roles
            ):
                raise ValueError("accepted production scorers need an accepted scorer identity")
        elif self.production_status is ProductionScorerStatus.PROPOSED:
            if (
                self.production_scorer is None
                or EvaluationRole.PROPOSED_BENCHMARK_SCORER not in self.roles
            ):
                raise ValueError("proposed scorers must remain explicitly proposed")
        elif self.production_scorer is not None:
            raise ValueError("unimplemented production evaluation cannot name a production scorer")
        if (
            self.calibration_reference_status is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
            and self.calibration_reference_value is not None
        ):
            raise ValueError("a non-public calibration reference cannot include its value")


@dataclass(frozen=True, slots=True)
class BenchmarkReproductionContract:
    benchmark: str
    authority: ReproductionAuthority
    claims: tuple[ReproductionClaim, ...]
    randomness: RandomnessAuthority
    serialization: SerializationAuthority
    splits: tuple[SplitReproductionAuthority, ...]
    reference_hashes: tuple[ReferenceHash, ...]
    evaluation: EvaluationAuthority

    def __post_init__(self) -> None:
        if not self.benchmark:
            raise ValueError("benchmark identity is required")
        dimensions = tuple(claim.dimension for claim in self.claims)
        if len(dimensions) != len(set(dimensions)) or set(dimensions) != set(ReproductionDimension):
            raise ValueError("each reproduction dimension must have exactly one explicit claim")
        split_names = tuple(split.name for split in self.splits)
        if len(split_names) != len(set(split_names)):
            raise ValueError("split authorities must be unique")
        if len({item.split_name for item in self.reference_hashes}) != len(self.reference_hashes):
            raise ValueError("reference hashes must be unique by split")
        if set(item.split_name for item in self.reference_hashes) != {
            split.name for split in self.splits if split.reference_hash is not None
        }:
            raise ValueError("contract and split reference-hash authorities differ")

        claims = {claim.dimension: claim for claim in self.claims}
        for split in self.splits:
            if (
                split.reference_hash is not None
                and split.reference_hash not in self.reference_hashes
            ):
                raise ValueError("split hash is not present in the contract hash registry")

        dataset_hash = claims[ReproductionDimension.DATASET_HASH]
        if dataset_hash.status is ReproductionStatus.EXACT:
            required = {
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
                ReproductionDimension.ROW_ORDERING,
                ReproductionDimension.SERIALIZATION,
            }
            if any(
                claims[dimension].status is not ReproductionStatus.EXACT for dimension in required
            ):
                raise ValueError(
                    "exact dataset hashes require every generator and byte prerequisite"
                )
            serialization_details = (
                self.serialization.file_format,
                self.serialization.writer_implementation,
                self.serialization.column_order,
                self.serialization.index_handling,
                self.serialization.float_representation,
                self.serialization.metadata,
                self.serialization.compression_and_row_groups,
            )
            if any(detail is None or not detail for detail in serialization_details):
                raise ValueError("exact dataset hashes require complete serialization authority")
            if not dataset_hash.scope:
                raise ValueError("exact dataset hashes must declare their split scope")
            for dimension in required:
                claim_scope = claims[dimension].scope
                if claim_scope and not set(dataset_hash.scope).issubset(claim_scope):
                    raise ValueError(
                        f"exact dataset hash scope exceeds {dimension.value} authority"
                    )
            scoped_splits = {
                split.name: split for split in self.splits if split.name in dataset_hash.scope
            }
            if set(scoped_splits) != set(dataset_hash.scope):
                raise ValueError("dataset hash scope must resolve to declared splits")
            if any(
                split.assignment_status is not ReproductionStatus.EXACT
                or split.materialization_status is not ReproductionStatus.EXACT
                or split.materialization_state is not MaterializationState.MATERIALIZED
                or split.reference_hash is None
                or not split.reference_hash.publication_safe
                for split in scoped_splits.values()
            ):
                raise ValueError(
                    "exact dataset hashes require exact split and reference-hash authority"
                )

        evaluation_claim = claims[ReproductionDimension.EVALUATION]
        if self.evaluation.production_status is not ProductionScorerStatus.ACCEPTED:
            if evaluation_claim.status is ReproductionStatus.EXACT:
                raise ValueError("proposed or unimplemented production evaluation cannot be exact")
        if (
            self.evaluation.calibration_reference_status
            is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
            and self.evaluation.calibration_reference_value is None
            and evaluation_claim.status is ReproductionStatus.EXACT
        ):
            raise ValueError(
                "calibrated evaluation cannot be exact without its locked reference value"
            )

        historical_result = claims[ReproductionDimension.HISTORICAL_RESULT]
        if historical_result.status is ReproductionStatus.EXACT:
            if dataset_hash.status is not ReproductionStatus.EXACT:
                raise ValueError("exact historical results require exact dataset authority")
            if (
                claims[ReproductionDimension.MODEL_CONFIGURATION].status
                is not ReproductionStatus.EXACT
            ):
                raise ValueError(
                    "exact historical results require exact model/config/checkpoint authority"
                )
            if evaluation_claim.status is not ReproductionStatus.EXACT:
                raise ValueError("exact historical results require exact evaluation authority")

    def claim(self, dimension: ReproductionDimension) -> ReproductionClaim:
        return next(claim for claim in self.claims if claim.dimension is dimension)
