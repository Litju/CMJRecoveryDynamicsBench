"""Typed, publication-safe contracts for scientific lineage."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from cmj_recovery_dynamics.contracts import ComparabilityStatus, MetricCategory, StudyType


class EvidenceStatus(StrEnum):
    DIRECT = "DIRECT"
    RECONSTRUCTED = "RECONSTRUCTED"
    HYPOTHESIZED = "HYPOTHESIZED"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"


class EvidenceConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    status: EvidenceStatus
    sources: tuple[str, ...]
    confidence: EvidenceConfidence
    note: str = ""

    def __post_init__(self) -> None:
        if not self.sources and self.status is not EvidenceStatus.UNKNOWN:
            raise ValueError("non-unknown evidence must identify at least one authority")
        if any(not source for source in self.sources):
            raise ValueError("evidence source references must be non-empty")


class ChangeClass(StrEnum):
    WORLD_CHANGE = "WORLD_CHANGE"
    OBSERVATION_CHANGE = "OBSERVATION_CHANGE"
    TASK_CHANGE = "TASK_CHANGE"
    DATASET_SPLIT_CHANGE = "DATASET_SPLIT_CHANGE"
    EVALUATION_CHANGE = "EVALUATION_CHANGE"
    REPRESENTATION_CHANGE = "REPRESENTATION_CHANGE"
    MODEL_ONLY_CHANGE = "MODEL_ONLY_CHANGE"
    TRAINING_ONLY_CHANGE = "TRAINING_ONLY_CHANGE"
    RERUN_ONLY = "RERUN_ONLY"
    COMPATIBILITY_ONLY = "COMPATIBILITY_ONLY"
    UNKNOWN = "UNKNOWN"


class ScientificDisposition(StrEnum):
    ACCEPTED = "ACCEPTED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED_RATIONALE_UNKNOWN = "RETIRED_RATIONALE_UNKNOWN"
    PROPOSED_ALTERNATE = "PROPOSED_ALTERNATE"
    ACTIVE_CANDIDATE = "ACTIVE_CANDIDATE"
    COMPLETED_POSITIVE = "COMPLETED_POSITIVE"
    COMPLETED_NEGATIVE = "COMPLETED_NEGATIVE"
    COMPLETED_MIXED = "COMPLETED_MIXED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"
    PROGRAM_PIVOT = "PROGRAM_PIVOT"
    NOT_ML_TASK = "NOT_ML_TASK"
    NOT_BENCHMARK_VALIDATION = "NOT_BENCHMARK_VALIDATION"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


class ExperimentStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"
    SUPERSEDED = "SUPERSEDED"
    CANCELED = "CANCELED"
    PROPOSED_NOT_RUN = "PROPOSED_NOT_RUN"
    BLOCKED = "BLOCKED"
    NOT_ML_TASK = "NOT_ML_TASK"
    UNKNOWN = "UNKNOWN"


class ExperimentPurpose(StrEnum):
    QUALIFICATION = "QUALIFICATION"
    BASELINE_EVALUATION = "BASELINE_EVALUATION"
    REFERENCE_MODEL_EVALUATION = "REFERENCE_MODEL_EVALUATION"
    HEADROOM = "HEADROOM"
    OBSERVABILITY = "OBSERVABILITY"
    RECONSTRUCTABILITY = "RECONSTRUCTABILITY"
    SYSTEM_IDENTIFICATION = "SYSTEM_IDENTIFICATION"
    ADVERSARIAL_RECONSTRUCTION = "ADVERSARIAL_RECONSTRUCTION"
    ROBUSTNESS = "ROBUSTNESS"
    DATA_QUALIFICATION = "DATA_QUALIFICATION"
    REAL_DATA_GROUNDING = "REAL_DATA_GROUNDING"
    REDESIGN = "REDESIGN"
    FALSIFICATION = "FALSIFICATION"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    IMPLEMENTATION_VALIDATION = "IMPLEMENTATION_VALIDATION"
    OTHER = "OTHER"


class ModelRole(StrEnum):
    NAIVE_BASELINE = "NAIVE_BASELINE"
    PUBLIC_BASELINE = "PUBLIC_BASELINE"
    REFERENCE_MODEL = "REFERENCE_MODEL"
    EXPERT_ORACLE_RESEARCH_MODEL = "EXPERT_ORACLE_RESEARCH_MODEL"
    EMPIRICAL_FRONTIER = "EMPIRICAL_FRONTIER"
    LOCAL_STRUCTURED_PREDICTOR = "LOCAL_STRUCTURED_PREDICTOR"
    LEARNED_LOW_DIMENSIONAL_PREDICTOR = "LEARNED_LOW_DIMENSIONAL_PREDICTOR"
    GENERIC_HIGH_CAPACITY_PREDICTOR = "GENERIC_HIGH_CAPACITY_PREDICTOR"
    PROBABILISTIC_POSTERIOR_ESTIMATOR = "PROBABILISTIC_POSTERIOR_ESTIMATOR"
    EXACT_ANALYTIC_REFERENCE = "EXACT_ANALYTIC_REFERENCE"
    RECONSTRUCTABILITY_ATTACK = "RECONSTRUCTABILITY_ATTACK"
    UNKNOWN = "UNKNOWN"


class ConfigurationStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    PARTIALLY_SPECIFIED = "PARTIALLY_SPECIFIED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ArtifactAvailability(StrEnum):
    EXISTS = "EXISTS"
    PRESERVED_PRIVATELY = "PRESERVED_PRIVATELY"
    RECOVERABLE = "RECOVERABLE"
    MISSING = "MISSING"
    NOT_RECOVERED = "NOT_RECOVERED"
    NOT_MATERIALIZED = "NOT_MATERIALIZED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RedistributionStatus(StrEnum):
    ALLOWED = "ALLOWED"
    PROHIBITED = "PROHIBITED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    name: str
    role: str
    availability: ArtifactAvailability
    redistribution: RedistributionStatus
    rights_decision_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.role:
            raise ValueError("artifact name and role are required")
        if (
            self.redistribution is RedistributionStatus.ALLOWED
            and not self.rights_decision_reference
        ):
            raise ValueError("public redistribution requires an explicit rights decision")


class DatasetKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    MANUFACTURED = "MANUFACTURED"
    EMPIRICAL = "EMPIRICAL"


class SplitRole(StrEnum):
    TRAINING = "TRAINING"
    PUBLIC_VALIDATION = "PUBLIC_VALIDATION"
    HIDDEN_TEST = "HIDDEN_TEST"
    GENERATION_FIXTURE = "GENERATION_FIXTURE"
    UNKNOWN = "UNKNOWN"


class SplitUnit(StrEnum):
    PARTICIPANT = "PARTICIPANT"
    CAMP = "CAMP"
    PARTICIPANT_ORIGIN = "PARTICIPANT_ORIGIN"
    CAMP_PARTICIPANT_EPISODE = "CAMP_PARTICIPANT_EPISODE"
    SYNTHETIC_HISTORY = "SYNTHETIC_HISTORY"
    EMPIRICAL_PARTICIPANT = "EMPIRICAL_PARTICIPANT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class DatasetIdentity:
    name: str
    kind: DatasetKind
    generator_identity: str | None
    observation_identity: str | None
    split_names: tuple[str, ...]
    benchmark_names: tuple[str, ...]
    materialized_artifact_status: ArtifactAvailability
    redistribution: RedistributionStatus
    supersedes_dataset: str | None
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name or not self.split_names:
            raise ValueError("dataset identity needs a name and at least one split")
        if len(self.split_names) != len(set(self.split_names)):
            raise ValueError("dataset split names must be unique")
        if self.kind is DatasetKind.EMPIRICAL and self.generator_identity is not None:
            raise ValueError("empirical datasets must not claim a synthetic generator")


@dataclass(frozen=True, slots=True)
class SplitIdentity:
    name: str
    dataset_name: str
    role: SplitRole
    split_unit: SplitUnit
    rows: int | None
    participants: int | None = None
    camps: int | None = None
    origins_or_episodes: int | None = None
    artifact_status: ArtifactAvailability = ArtifactAvailability.UNKNOWN
    labels_available: bool | None = None
    notes: str = ""
    evidence: EvidenceReference | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.dataset_name:
            raise ValueError("split identity and dataset identity are required")
        for count in (self.rows, self.participants, self.camps, self.origins_or_episodes):
            if count is not None and count < 0:
                raise ValueError("split counts must be nonnegative")


@dataclass(frozen=True, slots=True)
class ConfigurationIdentity:
    name: str
    status: ConfigurationStatus
    known_details: tuple[str, ...]
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("configuration identity must be named")
        if self.status is ConfigurationStatus.UNKNOWN and self.known_details:
            raise ValueError("unknown configurations cannot carry inferred details")


@dataclass(frozen=True, slots=True)
class BenchmarkApplicability:
    benchmark_names: tuple[str, ...] = ()
    study_types: tuple[StudyType, ...] = ()

    def __post_init__(self) -> None:
        if len(self.benchmark_names) != len(set(self.benchmark_names)):
            raise ValueError("benchmark applicability names must be unique")
        if len(self.study_types) != len(set(self.study_types)):
            raise ValueError("study applicability types must be unique")


@dataclass(frozen=True, slots=True)
class ModelFamily:
    name: str
    architecture: str | None
    roles: tuple[ModelRole, ...]
    applicability: BenchmarkApplicability
    objective: str
    configuration: ConfigurationIdentity | None
    configuration_status: ConfigurationStatus
    checkpoint_status: ArtifactAvailability
    checkpoint: ArtifactReference | None
    introduction_change: ChangeClass
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name or not self.roles or not self.objective:
            raise ValueError("model family needs a scientific name, role, and objective")
        if len(self.roles) != len(set(self.roles)):
            raise ValueError("model roles must be unique")
        if (
            self.configuration is None
            and self.configuration_status is ConfigurationStatus.IDENTIFIED
        ):
            raise ValueError("identified model configurations need a typed identity")
        if (
            self.checkpoint is not None
            and self.checkpoint.availability is not self.checkpoint_status
        ):
            raise ValueError("checkpoint status must match its artifact reference")


@dataclass(frozen=True, slots=True)
class RepresentationIdentity:
    name: str
    description: str
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name or not self.description:
            raise ValueError("representation identity needs a name and description")


@dataclass(frozen=True, slots=True)
class BenchmarkLineage:
    benchmark_name: str
    dataset_name: str
    split_names: tuple[str, ...]
    generator_identity: str
    observation_identity: str
    representation_name: str
    evaluation_name: str
    disposition: ScientificDisposition
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not all(
            (
                self.benchmark_name,
                self.dataset_name,
                self.split_names,
                self.generator_identity,
                self.observation_identity,
                self.representation_name,
                self.evaluation_name,
            )
        ):
            raise ValueError(
                "benchmark lineage must bind dataset, split, world, observation, and evaluation"
            )


@dataclass(frozen=True, slots=True)
class BenchmarkTransition:
    name: str
    source_benchmark: str | None
    target_benchmark: str
    change_classes: tuple[ChangeClass, ...]
    accepted_successor: bool
    rationale: str
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if (
            not self.name
            or not self.target_benchmark
            or not self.change_classes
            or not self.rationale
        ):
            raise ValueError("benchmark transition needs a target, change class, and rationale")
        if len(self.change_classes) != len(set(self.change_classes)):
            raise ValueError("benchmark transition change classes must be unique")


@dataclass(frozen=True, slots=True)
class StudyLineage:
    study_type: StudyType
    research_question: str
    benchmark_names: tuple[str, ...]
    dataset_names: tuple[str, ...]
    conclusion: str
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.research_question or not self.conclusion:
            raise ValueError("adjacent study lineage needs a research question and conclusion")
        if len(self.benchmark_names) != len(set(self.benchmark_names)):
            raise ValueError("adjacent study benchmark references must be unique")
        if len(self.dataset_names) != len(set(self.dataset_names)):
            raise ValueError("adjacent study dataset references must be unique")


class ProtocolUnit(StrEnum):
    QUERY_ROW = "QUERY_ROW"
    PARTICIPANT = "PARTICIPANT"
    CAMP = "CAMP"
    SYNTHETIC_HISTORY = "SYNTHETIC_HISTORY"
    SCORING_CELL = "SCORING_CELL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class BootstrapProtocol:
    unit: ProtocolUnit
    resamples: int
    seed: int | None
    paired: bool
    shared_sample_matrix: bool

    def __post_init__(self) -> None:
        if self.resamples < 1:
            raise ValueError("bootstrap resample count must be positive")


@dataclass(frozen=True, slots=True)
class ExperimentDefinition:
    name: str
    scientific_question: str
    benchmark_name: str | None
    study_type: StudyType | None
    purpose: ExperimentPurpose
    dataset_name: str
    split_names: tuple[str, ...]
    model_names: tuple[str, ...]
    evaluation_names: tuple[str, ...]
    protocol_unit: ProtocolUnit
    status: ExperimentStatus
    disposition: ScientificDisposition
    decision_purpose: str
    change_class: ChangeClass
    repetitions: int | None
    seed_values: tuple[int, ...]
    bootstrap: BootstrapProtocol | None
    fold_count: int | None
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name or not self.scientific_question or not self.dataset_name:
            raise ValueError("experiment needs a scientific identity, question, and dataset")
        if self.benchmark_name is None and self.study_type is None:
            raise ValueError("experiment needs a benchmark or adjacent-study context")
        if not self.split_names or not self.evaluation_names:
            raise ValueError("experiment needs explicit split and evaluation identities")
        if len(self.split_names) != len(set(self.split_names)):
            raise ValueError("experiment split identities must be unique")
        if len(self.evaluation_names) != len(set(self.evaluation_names)):
            raise ValueError("experiment evaluation identities must be unique")
        if self.repetitions is not None and self.repetitions < 1:
            raise ValueError("experiment repetitions must be positive")
        if self.fold_count is not None and self.fold_count < 1:
            raise ValueError("experiment fold count must be positive")


@dataclass(frozen=True, slots=True)
class EvaluationBinding:
    name: str
    category: MetricCategory | None
    compatible_benchmarks: tuple[str, ...]
    compatible_studies: tuple[StudyType, ...]
    production_scorer: bool
    implementation_evidence: EvidenceStatus
    description: str

    def __post_init__(self) -> None:
        if not self.name or not self.description:
            raise ValueError("evaluation binding needs a scientific name and description")
        if self.production_scorer and self.category is not MetricCategory.BENCHMARK_SCORE:
            raise ValueError("production scorers must use the benchmark-score category")


@dataclass(frozen=True, slots=True)
class ResultValue:
    measure: str
    unit: str
    value: float | None = None
    interval: tuple[float, float] | None = None
    value_range: tuple[float, float] | None = None
    sample_count: int | None = None
    stratum: str | None = None

    def __post_init__(self) -> None:
        if not self.measure or not self.unit:
            raise ValueError("result value needs a measure and unit")
        numbers = tuple(value for value in (self.value,) if value is not None)
        if self.interval is not None:
            numbers += self.interval
            if self.interval[1] < self.interval[0]:
                raise ValueError("result interval upper bound must be >= lower bound")
        if self.value_range is not None:
            numbers += self.value_range
            if self.value_range[1] < self.value_range[0]:
                raise ValueError("result range upper bound must be >= lower bound")
        if any(not math.isfinite(value) for value in numbers):
            raise ValueError("result values must be finite")
        if self.sample_count is not None and self.sample_count < 1:
            raise ValueError("result sample count must be positive")


@dataclass(frozen=True, slots=True)
class ResultDefinition:
    name: str
    experiment_name: str
    model_names: tuple[str, ...]
    dataset_name: str
    split_name: str
    evaluation_name: str
    values: tuple[ResultValue, ...]
    comparability: ComparabilityStatus
    disposition: ScientificDisposition
    summary: str
    evidence: EvidenceReference
    production_result: bool = False

    def __post_init__(self) -> None:
        if not all(
            (
                self.name,
                self.experiment_name,
                self.dataset_name,
                self.split_name,
                self.evaluation_name,
                self.summary,
            )
        ):
            raise ValueError("result must bind experiment, data split, evaluation, and summary")
        if len(self.model_names) != len(set(self.model_names)):
            raise ValueError("result model identities must be unique")
        if len({(value.measure, value.stratum) for value in self.values}) != len(self.values):
            raise ValueError("result measures must be unique within each stratum")


@dataclass(frozen=True, slots=True)
class ComparabilityConclusion:
    name: str
    left_result_names: tuple[str, ...]
    right_result_names: tuple[str, ...]
    status: ComparabilityStatus
    identity_basis: str
    rationale: str
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        if not self.name or not self.left_result_names or not self.right_result_names:
            raise ValueError("comparability conclusion needs two result families")
        if not self.identity_basis or not self.rationale:
            raise ValueError("comparability conclusion needs a basis and rationale")


class ConflictStatus(StrEnum):
    RESOLVED_RAW_COORDINATE = "RESOLVED_RAW_COORDINATE"
    RESOLVED_PRIOR_WHITENED = "RESOLVED_PRIOR_WHITENED"
    MULTIPLE_DISTINCT_RESULTS = "MULTIPLE_DISTINCT_RESULTS"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"


class CoordinateBasis(StrEnum):
    RAW_COORDINATE = "RAW_COORDINATE"
    PRIOR_WHITENED = "PRIOR_WHITENED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PosteriorRMSETrace:
    result_identity: str
    evaluator_reference: str
    source_output_reference: str
    configuration_identity: str
    source_basis: CoordinateBasis
    same_result_binding: bool
    rounded_values_match: bool
    multiple_distinct_results: bool = False

    def __post_init__(self) -> None:
        if not self.result_identity:
            raise ValueError("posterior-RMSE trace needs a scientific result identity")


def classify_posterior_rmse_trace(trace: PosteriorRMSETrace) -> ConflictStatus:
    if trace.multiple_distinct_results:
        return ConflictStatus.MULTIPLE_DISTINCT_RESULTS
    if not (
        trace.evaluator_reference
        and trace.source_output_reference
        and trace.configuration_identity
        and trace.same_result_binding
        and trace.rounded_values_match
    ):
        return ConflictStatus.UNRESOLVED_CONFLICT
    if trace.source_basis is CoordinateBasis.RAW_COORDINATE:
        return ConflictStatus.RESOLVED_RAW_COORDINATE
    if trace.source_basis is CoordinateBasis.PRIOR_WHITENED:
        return ConflictStatus.RESOLVED_PRIOR_WHITENED
    return ConflictStatus.UNRESOLVED_CONFLICT


@dataclass(frozen=True, slots=True)
class ConflictDefinition:
    name: str
    status: ConflictStatus
    trace: PosteriorRMSETrace
    evidence: EvidenceReference
    resolution: str

    def __post_init__(self) -> None:
        if not self.name or not self.resolution:
            raise ValueError("conflict definition needs a name and resolution state")
        if self.status is not classify_posterior_rmse_trace(self.trace):
            raise ValueError("posterior-RMSE conflict status requires exact source evidence")
