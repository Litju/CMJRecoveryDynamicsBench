"""Immutable model, result, and source-closure contracts for M3."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from cmj_recovery_dynamics.contracts import (
    CalibrationReferenceStatus,
    EvaluationDefinition,
    EvaluationImplementation,
    MetricCategory,
    ProductionAcceptance,
)
from cmj_recovery_dynamics.lineage.contracts import (
    ExperimentDefinition,
    ExperimentStatus,
    ModelFamily,
    ResultDefinition,
    ScientificDisposition,
)


class ModelReproductionStatus(StrEnum):
    EXACT_IMPLEMENTATION = "EXACT_IMPLEMENTATION"
    SEMANTIC_IMPLEMENTATION = "SEMANTIC_IMPLEMENTATION"
    PARTIAL_CONFIGURATION = "PARTIAL_CONFIGURATION"
    RESULT_EVIDENCE_ONLY = "RESULT_EVIDENCE_ONLY"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ModelConfigurationStatus(StrEnum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CheckpointState(StrEnum):
    PRESERVED_PRIVATELY = "PRESERVED_PRIVATELY"
    NOT_RECOVERED = "NOT_RECOVERED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResultReproductionStatus(StrEnum):
    EXACT_REPLAYABLE = "EXACT_REPLAYABLE"
    SEMANTICALLY_REPLAYABLE = "SEMANTICALLY_REPLAYABLE"
    SOURCE_REPRODUCIBLE = "SOURCE_REPRODUCIBLE"
    RESULT_EVIDENCE_ONLY = "RESULT_EVIDENCE_ONLY"
    UNRESOLVED = "UNRESOLVED"


class EvaluationRole(StrEnum):
    ACCEPTED_PRODUCTION_SCORER = "ACCEPTED_PRODUCTION_SCORER"
    PROPOSED_SCORER = "PROPOSED_SCORER"
    RESEARCH_DIAGNOSTIC = "RESEARCH_DIAGNOSTIC"
    QUALIFICATION_STATISTIC = "QUALIFICATION_STATISTIC"
    MODEL_SELECTION_METRIC = "MODEL_SELECTION_METRIC"
    COMPATIBILITY_TRANSFORM = "COMPATIBILITY_TRANSFORM"
    UNIMPLEMENTED = "UNIMPLEMENTED"


class SpecimenModelStatus(StrEnum):
    RECOVERED = "RECOVERED"
    RESULT_EVIDENCE_ONLY = "RESULT_EVIDENCE_ONLY"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    PROPOSED = "PROPOSED"


@dataclass(frozen=True, slots=True)
class SourceClosure:
    source_commit: str | None = None
    task_tree: str | None = None
    source_snapshot: str | None = None
    model_source: str | None = None
    training_source: str | None = None
    configuration_source: str | None = None
    checkpoint_metadata_authority: str | None = None
    evaluation_source: str | None = None
    result_source: str | None = None
    seed_fold_authority: str | None = None
    runtime_authority: str | None = None
    source_hashes: tuple[tuple[str, str], ...] = ()
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        paths = (
            self.source_snapshot,
            self.model_source,
            self.training_source,
            self.configuration_source,
            self.checkpoint_metadata_authority,
            self.evaluation_source,
            self.result_source,
            self.seed_fold_authority,
            self.runtime_authority,
            *(path for path, _ in self.source_hashes),
        )
        if any(path is not None and _unsafe_public_path(path) for path in paths):
            raise ValueError("source closure paths must be publication-safe relative paths")
        if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None for _, digest in self.source_hashes):
            raise ValueError("source hashes must be lowercase SHA-256 values")
        if len({path for path, _ in self.source_hashes}) != len(self.source_hashes):
            raise ValueError("source hash paths must be unique")


def _unsafe_public_path(path: str) -> bool:
    value = PurePosixPath(path)
    return value.is_absolute() or ".." in value.parts or "\\" in path


@dataclass(frozen=True, slots=True)
class ModelUseReproduction:
    """One model family as used by one benchmark experiment."""

    model_name: str
    benchmark_name: str
    experiment: ExperimentDefinition
    dataset_name: str
    split_names: tuple[str, ...]
    evaluation_names: tuple[str, ...]
    result_names: tuple[str, ...]
    experiment_status: ExperimentStatus
    scientific_disposition: ScientificDisposition
    implementation_status: ModelReproductionStatus
    configuration_status: ModelConfigurationStatus
    architecture: str | None
    feature_surface: str | None
    preprocessing: str | None
    training_objective: str | None
    hyperparameters: tuple[tuple[str, str], ...]
    seed_identities: tuple[str, ...] | None
    seed_metrics: tuple[tuple[str, float], ...]
    fold_grouping: str | None
    checkpoint_state: CheckpointState
    checkpoint_identity_sha256: str | None
    runtime_details: str | None
    source_closure: SourceClosure
    missing_authority: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all((self.model_name, self.benchmark_name, self.dataset_name)):
            raise ValueError("model uses need exact model, benchmark, and dataset names")
        if not self.split_names or not self.evaluation_names:
            raise ValueError("model uses need split and evaluation identities")
        if self.experiment.benchmark_name != self.benchmark_name:
            raise ValueError("model use benchmark must match its experiment")
        if self.experiment.dataset_name != self.dataset_name:
            raise ValueError("model use dataset must match its experiment")
        if self.experiment.status is not self.experiment_status:
            raise ValueError("model use status must match its experiment")
        if (
            self.checkpoint_identity_sha256 is not None
            and re.fullmatch(r"[0-9a-f]{64}", self.checkpoint_identity_sha256) is None
        ):
            raise ValueError("checkpoint identity must be a lowercase SHA-256 value")
        if len({seed for seed, _ in self.seed_metrics}) != len(self.seed_metrics):
            raise ValueError("seed metric identities must be unique")
        if any(not name or not math.isfinite(value) for name, value in self.seed_metrics):
            raise ValueError("seed metrics need unique names and finite values")
        if self.implementation_status is ModelReproductionStatus.EXACT_IMPLEMENTATION:
            if self.configuration_status not in {
                ModelConfigurationStatus.EXACT,
                ModelConfigurationStatus.NOT_APPLICABLE,
            }:
                raise ValueError("exact implementations need exact or inapplicable configuration")


@dataclass(frozen=True, slots=True)
class ModelReproduction:
    model_name: str
    model_family: ModelFamily
    status: ModelReproductionStatus
    configuration_status: ModelConfigurationStatus
    uses: tuple[ModelUseReproduction, ...]
    unbound_applicability: tuple[str, ...]
    missing_authority: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.model_name != self.model_family.name:
            raise ValueError("M3 model name must preserve the M1 family identity")
        if any(use.model_name != self.model_name for use in self.uses):
            raise ValueError("model uses must retain their family name")


@dataclass(frozen=True, slots=True)
class ResultReplayAuthority:
    historical_dataset_hash_exact: bool
    target_semantics_exact: bool
    model_configuration_exact: bool
    seed_fold_protocol_exact: bool
    checkpoint_or_training_procedure_exact: bool
    evaluation_implementation_exact: bool
    calibration_available: bool
    runtime_determinism_resolved: bool

    @property
    def semantic_replay_ready(self) -> bool:
        return all(
            (
                self.target_semantics_exact,
                self.evaluation_implementation_exact,
                self.calibration_available,
            )
        )

    @property
    def exact_replay_ready(self) -> bool:
        return all(
            (
                self.historical_dataset_hash_exact,
                self.target_semantics_exact,
                self.model_configuration_exact,
                self.seed_fold_protocol_exact,
                self.checkpoint_or_training_procedure_exact,
                self.evaluation_implementation_exact,
                self.calibration_available,
                self.runtime_determinism_resolved,
            )
        )


@dataclass(frozen=True, slots=True)
class ResultReproduction:
    result: ResultDefinition
    benchmark_name: str
    experiment: ExperimentDefinition
    experiment_status: ExperimentStatus
    experiment_disposition: ScientificDisposition
    status: ResultReproductionStatus
    replay_authority: ResultReplayAuthority
    seed_identities: tuple[str, ...] | None
    fold_grouping: str | None
    runtime_details: tuple[str, ...]
    numerically_replayed: bool
    replay_basis: str
    missing_authority: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.result.model_names:
            raise ValueError("benchmark result contracts must bind at least one model")
        if not all(
            (
                self.benchmark_name,
                self.result.experiment_name,
                self.result.dataset_name,
                self.result.split_name,
                self.result.evaluation_name,
                self.replay_basis,
            )
        ):
            raise ValueError(
                "result contracts need benchmark, experiment, data, evaluation, and basis"
            )
        if (
            self.experiment.name != self.result.experiment_name
            or self.experiment.dataset_name != self.result.dataset_name
            or self.result.split_name not in self.experiment.split_names
            or self.result.evaluation_name not in self.experiment.evaluation_names
        ):
            raise ValueError("result experiment must bind its exact dataset, split, and evaluation")
        if self.experiment.status is not self.experiment_status:
            raise ValueError("result experiment status must match its bound experiment")
        if self.status is ResultReproductionStatus.EXACT_REPLAYABLE:
            if not self.replay_authority.exact_replay_ready or not self.numerically_replayed:
                raise ValueError("exact replay requires complete authority and a numerical replay")
        if self.status is ResultReproductionStatus.SEMANTICALLY_REPLAYABLE:
            if not self.replay_authority.semantic_replay_ready or not self.numerically_replayed:
                raise ValueError(
                    "semantic replay requires semantic evaluation authority and a numerical replay"
                )


@dataclass(frozen=True, slots=True)
class EvaluationReproduction:
    name: str
    role: EvaluationRole
    category: MetricCategory | None
    production_acceptance: ProductionAcceptance | None
    definition: EvaluationDefinition | None
    formula: str | None
    implementation_id: str | None
    compatible_benchmarks: tuple[str, ...]
    evidence: tuple[str, ...]
    missing_authority: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.evidence:
            raise ValueError("evaluation contracts need a name and evidence")
        if self.role is EvaluationRole.ACCEPTED_PRODUCTION_SCORER:
            if self.definition is None or not self.definition.is_accepted_production_scorer:
                raise ValueError(
                    "accepted production evaluations need an accepted scorer definition"
                )
        if self.role is EvaluationRole.PROPOSED_SCORER:
            if self.definition is None or not self.definition.is_proposed_scorer:
                raise ValueError("proposed evaluations need a proposed scorer definition")

    @property
    def implementation_exact(self) -> bool:
        if self.role is EvaluationRole.UNIMPLEMENTED:
            return False
        if self.definition is not None:
            return self.definition.implementation_status is EvaluationImplementation.IMPLEMENTED
        return self.implementation_id is not None

    @property
    def calibration_available(self) -> bool:
        if self.role in {
            EvaluationRole.RESEARCH_DIAGNOSTIC,
            EvaluationRole.QUALIFICATION_STATISTIC,
            EvaluationRole.MODEL_SELECTION_METRIC,
            EvaluationRole.COMPATIBILITY_TRANSFORM,
        }:
            return True
        if (
            self.role
            not in {
                EvaluationRole.ACCEPTED_PRODUCTION_SCORER,
                EvaluationRole.PROPOSED_SCORER,
            }
            or self.definition is None
        ):
            return False

        match self.definition.calibration_reference_status:
            case CalibrationReferenceStatus.NOT_APPLICABLE:
                return True
            case CalibrationReferenceStatus.KNOWN:
                return self.definition.calibration_reference_value is not None
            case (
                CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
                | CalibrationReferenceStatus.UNKNOWN
            ):
                return False
            case _:
                return False


@dataclass(frozen=True, slots=True)
class SpecimenModelLadder:
    benchmark_name: str
    status: SpecimenModelStatus
    model_names: tuple[str, ...]
    result_names: tuple[str, ...]
    experiment_names: tuple[str, ...]
    note: str

    def __post_init__(self) -> None:
        if not self.benchmark_name or not self.note:
            raise ValueError("specimen ladder contracts need a benchmark and explanation")
