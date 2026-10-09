"""Publication-safe contracts for reconstructing historical scientific studies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from cmj_recovery_dynamics.contracts import EvaluationDefinition, StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    BootstrapProtocol,
    ComparabilityConclusion,
    DatasetIdentity,
    EvaluationBinding,
    EvidenceReference,
    ExperimentDefinition,
    ExperimentPurpose,
    ExperimentStatus,
    ModelFamily,
    ProtocolUnit,
    ResultDefinition,
    ScientificDisposition,
    SplitIdentity,
    StudyLineage,
)

if TYPE_CHECKING:
    from cmj_recovery_dynamics.lineage.registry import ExperimentLineageView


class StudyClassification(StrEnum):
    BENCHMARK_CHANGE = "BENCHMARK_CHANGE"
    EXPERIMENT = "EXPERIMENT"
    AUDIT = "AUDIT"
    FALSIFIER = "FALSIFIER"
    PROPOSED_REDESIGN = "PROPOSED_REDESIGN"


class ProtocolCompleteness(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    PROTOCOL_ONLY = "PROTOCOL_ONLY"
    OPERATIONAL_ONLY = "OPERATIONAL_ONLY"
    UNKNOWN = "UNKNOWN"


class ResultAuthority(StrEnum):
    DIRECT_RESULT = "DIRECT_RESULT"
    RECONSTRUCTED_ARITHMETIC = "RECONSTRUCTED_ARITHMETIC"
    PROTOCOL_ONLY = "PROTOCOL_ONLY"
    PARTIAL_OUTPUT_EXCLUDED = "PARTIAL_OUTPUT_EXCLUDED"
    UNKNOWN = "UNKNOWN"


class RuleRole(StrEnum):
    HISTORICAL_PROGRAM_RULE = "HISTORICAL_PROGRAM_RULE"


class RuleDirection(StrEnum):
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"


class StudyDecisionOutcome(StrEnum):
    RUNTIME_SCORER_REPAIR_REQUIRED = "RUNTIME_SCORER_REPAIR_REQUIRED"
    SOURCE_DATA_QUALIFIED = "SOURCE_DATA_QUALIFIED"
    PROGRAM_PIVOT = "PROGRAM_PIVOT"
    NOT_ML_TASK = "NOT_ML_TASK"
    NOT_BENCHMARK_VALIDATION = "NOT_BENCHMARK_VALIDATION"


@dataclass(frozen=True, slots=True)
class HistoricalDecisionRule:
    name: str
    experiment_name: str
    quantity: str
    threshold: float
    direction: RuleDirection
    historical_purpose: str
    source: tuple[str, ...]
    applied: bool
    caused_historical_decision: bool
    role: RuleRole = RuleRole.HISTORICAL_PROGRAM_RULE
    scientific_requirement: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.experiment_name or not self.quantity:
            raise ValueError("historical rule needs an identity, experiment, and quantity")
        if not self.historical_purpose or not self.source:
            raise ValueError("historical rule needs its purpose and authority")
        if not math.isfinite(self.threshold):
            raise ValueError("historical decision threshold must be finite")
        if self.scientific_requirement:
            raise ValueError("historical program rules are not universal scientific requirements")

    def is_satisfied_by(self, value: float) -> bool:
        if not math.isfinite(value):
            raise ValueError("historical rule input must be finite")
        if self.direction is RuleDirection.GREATER_THAN:
            return value > self.threshold
        if self.direction is RuleDirection.GREATER_THAN_OR_EQUAL:
            return value >= self.threshold
        if self.direction is RuleDirection.LESS_THAN:
            return value < self.threshold
        return value <= self.threshold


@dataclass(frozen=True, slots=True)
class ResultAuthorityBinding:
    result_name: str
    authority: ResultAuthority


@dataclass(frozen=True, slots=True)
class SourceClosure:
    source_commit: tuple[str, ...] = ()
    task_tree: tuple[str, ...] = ()
    protocol_source: tuple[str, ...] = ()
    runner_source: tuple[str, ...] = ()
    model_source: tuple[str, ...] = ()
    evaluation_source: tuple[str, ...] = ()
    result_source: tuple[str, ...] = ()
    decision_source: tuple[str, ...] = ()
    bootstrap_source: tuple[str, ...] = ()
    environment_runtime_source: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StudyDecision:
    name: str
    experiment_name: str
    scientific_observation: str
    historical_rule_names: tuple[str, ...]
    outcome: StudyDecisionOutcome
    downstream_program_action: str
    benchmark_disposition: ScientificDisposition | None
    source: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not all(
                (
                    self.name,
                    self.experiment_name,
                    self.scientific_observation,
                    self.downstream_program_action,
                )
            )
            or not self.source
        ):
            raise ValueError("study decision needs an experiment, observation, action, and source")


@dataclass(frozen=True, slots=True)
class ExperimentReconstruction:
    lineage: ExperimentLineageView
    classification: StudyClassification
    protocol_completeness: ProtocolCompleteness
    result_authority: ResultAuthority
    result_authorities: tuple[ResultAuthorityBinding, ...]
    historical_decision_rules: tuple[HistoricalDecisionRule, ...]
    decision: StudyDecision | None
    conclusion: str
    downstream_action: str
    missing_authority: tuple[str, ...]
    source_closure: SourceClosure
    comparability: tuple[ComparabilityConclusion, ...]

    @property
    def experiment(self) -> ExperimentDefinition:
        return self.lineage.experiment

    @property
    def canonical_name(self) -> str:
        return self.experiment.name

    @property
    def study_type(self) -> StudyType | None:
        return self.experiment.study_type

    @property
    def purpose(self) -> ExperimentPurpose:
        return self.experiment.purpose

    @property
    def benchmark_name(self) -> str | None:
        return self.experiment.benchmark_name

    @property
    def specimen_name(self) -> str | None:
        return self.experiment.benchmark_name

    @property
    def dataset(self) -> DatasetIdentity:
        return self.lineage.dataset

    @property
    def splits(self) -> tuple[SplitIdentity, ...]:
        return self.lineage.splits

    @property
    def question(self) -> str:
        return self.experiment.scientific_question

    @property
    def models(self) -> tuple[ModelFamily, ...]:
        return self.lineage.models

    @property
    def evaluations(self) -> tuple[EvaluationDefinition | EvaluationBinding, ...]:
        return self.lineage.evaluations

    @property
    def protocol_unit(self) -> ProtocolUnit:
        return self.experiment.protocol_unit

    @property
    def repetitions(self) -> int | None:
        return self.experiment.repetitions

    @property
    def seed_values(self) -> tuple[int, ...]:
        return self.experiment.seed_values

    @property
    def fold_count(self) -> int | None:
        return self.experiment.fold_count

    @property
    def bootstrap(self) -> BootstrapProtocol | None:
        return self.experiment.bootstrap

    @property
    def protocol_evidence(self) -> EvidenceReference:
        return self.experiment.evidence

    @property
    def results(self) -> tuple[ResultDefinition, ...]:
        return self.lineage.results

    @property
    def result_identities(self) -> tuple[str, ...]:
        return tuple(result.name for result in self.results)

    @property
    def execution_status(self) -> ExperimentStatus:
        return self.experiment.status

    @property
    def scientific_disposition(self) -> ScientificDisposition:
        return self.experiment.disposition


@dataclass(frozen=True, slots=True)
class StudyReconstruction:
    name: str
    study_type: StudyType | None
    lineage: StudyLineage | None
    question: str
    experiment_names: tuple[str, ...]
    conclusion: str
    evidence_sources: tuple[str, ...]


__all__ = [
    "ExperimentReconstruction",
    "HistoricalDecisionRule",
    "ProtocolCompleteness",
    "ResultAuthority",
    "ResultAuthorityBinding",
    "RuleDirection",
    "RuleRole",
    "SourceClosure",
    "StudyClassification",
    "StudyDecision",
    "StudyDecisionOutcome",
    "StudyReconstruction",
]
