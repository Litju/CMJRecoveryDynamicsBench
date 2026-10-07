"""Immutable, typed contracts shared by benchmark, task, and study definitions."""

import math
from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum


def _is_enum_member(value: object, enum_type: type[Enum]) -> bool:
    return isinstance(value, enum_type)


class ForecastHorizon(IntEnum):
    """Nominal forecast time in hours; day seven is represented as 168 hours."""

    H24 = 24
    H48 = 48
    H72 = 72
    D7 = 168

    @property
    def label(self) -> str:
        return "D7" if self is ForecastHorizon.D7 else f"H{self.value}"


@dataclass(frozen=True, slots=True)
class ForecastWindow:
    """Observed target window around a nominal forecast horizon."""

    horizon: ForecastHorizon
    start_offset_hours: int
    end_offset_hours: int

    def __post_init__(self) -> None:
        if self.start_offset_hours < 0:
            raise ValueError("forecast windows cannot start before the prediction origin")
        if self.end_offset_hours < self.start_offset_hours:
            raise ValueError("forecast window end must not precede its start")


class PhysicalUnit(StrEnum):
    NEWTON_PER_KILOGRAM = "N/kg"
    METER_PER_SECOND = "m/s"
    METER_PER_SECOND_SQUARED = "m/s²"
    SECOND = "s"


class OutcomeVariable(StrEnum):
    RELATIVE_PEAK_MEAN_FORCE_INNOVATION = "relative_peak_mean_force_innovation"
    NET_IMPULSE_INNOVATION = "net_impulse_innovation"


@dataclass(frozen=True, slots=True)
class OutcomeDefinition:
    variable: OutcomeVariable
    unit: PhysicalUnit
    semantics: str

    def __post_init__(self) -> None:
        expected_unit = {
            OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION: PhysicalUnit.NEWTON_PER_KILOGRAM,
            OutcomeVariable.NET_IMPULSE_INNOVATION: PhysicalUnit.METER_PER_SECOND,
        }[self.variable]
        if self.unit is not expected_unit:
            raise ValueError(f"{self.variable.value} must use {expected_unit.value}")


FORCE_INNOVATION = OutcomeDefinition(
    variable=OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION,
    unit=PhysicalUnit.NEWTON_PER_KILOGRAM,
    semantics=(
        "Baseline-relative observed peak/mean countermovement-jump force change; an additive "
        "innovation, not a percentage, latent state, or causal effect."
    ),
)
NET_IMPULSE_INNOVATION = OutcomeDefinition(
    variable=OutcomeVariable.NET_IMPULSE_INNOVATION,
    unit=PhysicalUnit.METER_PER_SECOND,
    semantics=(
        "Baseline-relative observed net-impulse change; an additive innovation, "
        "not a percentage, latent state, or causal effect."
    ),
)
CANONICAL_OUTCOMES = (FORCE_INNOVATION, NET_IMPULSE_INNOVATION)


class TaskType(StrEnum):
    PRESEASON_CAMP_RECOVERY = "preseason_camp_recovery"
    POST_EXPOSURE_RECOVERY = "post_exposure_recovery"


class EstimandType(StrEnum):
    CAMP_STATE_INNOVATION = "camp_state_innovation"
    SINGLE_EXPOSURE_INNOVATION = "single_exposure_innovation"


class ExposurePolicy(StrEnum):
    CAMP_TRAJECTORY_THROUGH_HORIZON = "camp_trajectory_through_horizon"
    ONE_CURRENT_EXPOSURE_THROUGH_H72 = "one_current_exposure_through_h72"


@dataclass(frozen=True, slots=True)
class Estimand:
    name: str
    estimand_type: EstimandType
    target_semantics: str
    baseline_relative: bool = True


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    name: str
    task_type: TaskType
    research_question: str
    estimand: Estimand
    horizons: tuple[ForecastHorizon, ...]
    horizon_windows: tuple[ForecastWindow, ...]
    outcomes: tuple[OutcomeDefinition, ...]
    exposure_policy: ExposurePolicy
    baseline_definition: str
    prediction_time_information: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("task name must not be empty")
        if not self.horizons or len(set(self.horizons)) != len(self.horizons):
            raise ValueError("task horizons must be non-empty and unique")
        window_horizons = tuple(window.horizon for window in self.horizon_windows)
        if len(set(window_horizons)) != len(window_horizons):
            raise ValueError("task must define one target window per horizon")
        if set(window_horizons) != set(self.horizons):
            raise ValueError("task windows must match its forecast horizons")
        if self.outcomes != CANONICAL_OUTCOMES:
            raise ValueError("recovery tasks must use both canonical observed innovations")
        if self.task_type is TaskType.PRESEASON_CAMP_RECOVERY:
            if self.exposure_policy is not ExposurePolicy.CAMP_TRAJECTORY_THROUGH_HORIZON:
                raise ValueError("camp recovery must include exposure history through its horizon")
        elif self.exposure_policy is not ExposurePolicy.ONE_CURRENT_EXPOSURE_THROUGH_H72:
            raise ValueError("post-exposure recovery must isolate one exposure through H72")


class InformationStatus(StrEnum):
    SPECIFIED = "specified"
    PARTIALLY_SPECIFIED = "partially_specified"
    UNAVAILABLE = "unavailable"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class InformationBoundary:
    status: InformationStatus
    variables: tuple[str, ...] = ()
    details: str = ""


@dataclass(frozen=True, slots=True)
class TemporalAvailability:
    information_cutoff: str
    history_scope: str
    plans_known_at_origin_available: bool
    future_realized_exposure_available: bool


@dataclass(frozen=True, slots=True)
class ForceImpulseRelationship:
    gravitational_acceleration_m_per_s_squared: float
    formula: str = "J_net = (F_mean - g) * duration"


@dataclass(frozen=True, slots=True)
class ObservationContract:
    name: str
    baseline_measurements: InformationBoundary
    assessment_history: InformationBoundary
    exposure_information: InformationBoundary
    participant_covariates: InformationBoundary
    prior_episode_information: InformationBoundary
    temporal_availability: TemporalAvailability
    hidden_variables: InformationBoundary
    forbidden_variables: InformationBoundary
    measurement_construction: str
    force_impulse_relationship: ForceImpulseRelationship | None = None


class DynamicsFamily(StrEnum):
    EVENT_TIME_ADAPTATION_RECOVERY = "event_time_adaptation_recovery"
    FITNESS_FATIGUE_IMPULSE_RESPONSE = "fitness_fatigue_impulse_response"
    BIEXPONENTIAL_EPISODE_RESPONSE = "biexponential_episode_response"
    CORRELATED_EXPOSURE_RESPONSE = "correlated_exposure_response"
    THRESHOLD_RESPONSE = "threshold_response"
    FIXED_MODE_DISCREPANCY_RESPONSE = "fixed_mode_discrepancy_response"


class ModelImplementationStatus(StrEnum):
    PARTIAL_EQUATION = "partial_equation"
    PARAMETER_CONTRACT = "parameter_contract"


@dataclass(frozen=True, slots=True)
class DynamicsModel:
    name: str
    family: DynamicsFamily
    equation_summary: str
    implementation_status: ModelImplementationStatus


class BenchmarkStatus(StrEnum):
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    PROPOSED = "proposed"
    ACTIVE_CANDIDATE = "active_candidate"


class ReferenceStatus(StrEnum):
    IDENTIFIED = "identified"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class IdentityReference:
    scientific_name: str
    status: ReferenceStatus
    details: str = ""


class MetricCategory(StrEnum):
    BENCHMARK_SCORE = "BENCHMARK_SCORE"
    RESEARCH_DIAGNOSTIC = "RESEARCH_DIAGNOSTIC"
    QUALIFICATION_STATISTIC = "QUALIFICATION_STATISTIC"
    MODEL_SELECTION_METRIC = "MODEL_SELECTION_METRIC"
    COMPATIBILITY_TRANSFORM = "COMPATIBILITY_TRANSFORM"
    UNIMPLEMENTED_EVALUATION = "UNIMPLEMENTED_EVALUATION"


class OptimizationDirection(StrEnum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    UNKNOWN = "unknown"


class MetricUnits(StrEnum):
    DIMENSIONLESS = "dimensionless"
    DIMENSIONLESS_WITH_TARGET_UNIT_FALLBACK = (
        "dimensionless; target units if zero-variance RMSE fallback applies"
    )
    TARGET_UNITS = "target units"
    PARAMETER_UNITS = "parameter units"
    NATS = "nats"
    AUC = "area under ROC curve"
    UNKNOWN = "UNKNOWN"


class AggregationLevel(StrEnum):
    PREDICTION_ROW = "prediction_row"
    ORIGIN = "origin"
    PARTICIPANT = "participant"
    POSTERIOR_CASE = "posterior_case"
    ENSEMBLE_MEMBER = "ensemble_member"
    SCORING_CELL = "scoring_cell"
    OUTCOME = "outcome"
    REPEATED_RUN = "repeated_run"
    CAMP = "camp"
    BENCHMARK = "benchmark"
    UNKNOWN = "UNKNOWN"


class NormalizationRule(StrEnum):
    POPULATION_STANDARD_DEVIATION = "population_standard_deviation_ddof_0"
    TRAINING_SAMPLE_STANDARD_DEVIATION = "training_sample_standard_deviation_ddof_1"
    EXPLICIT_AXIS_SCALES = "explicit_axis_scales"
    PRIOR_COVARIANCE_WHITENING = "prior_covariance_whitening"
    NONE = "none"
    UNKNOWN = "UNKNOWN"


class WeightingRule(StrEnum):
    EQUAL_SCORING_CELLS = "equal_scoring_cells"
    EQUAL_OUTCOMES = "equal_outcomes"
    EQUAL_ROWS = "equal_rows_within_cell"
    EQUAL_ENSEMBLE_MEMBERS = "equal_ensemble_member_weights"
    EXPLICIT = "explicit_weights"
    UNKNOWN = "UNKNOWN"


class MissingCellPolicy(StrEnum):
    REJECT = "reject_missing_or_duplicate_required_cells"
    MASK_ROWS_OUTSIDE_CELL = "mask_truth_outside_the_registered_cell"
    UNKNOWN = "UNKNOWN"


class EvaluationImplementation(StrEnum):
    IMPLEMENTED = "implemented"
    NOT_IMPLEMENTED = "not_implemented"


class ProductionAcceptance(StrEnum):
    ACCEPTED_HISTORICAL = "accepted_historical"
    PROPOSED_UNRESOLVED = "proposed_unresolved"
    NONE = "none"


class ComparabilityStatus(StrEnum):
    DIRECTLY_COMPARABLE = "DIRECTLY_COMPARABLE"
    COMPARABLE_WITH_CAVEAT = "COMPARABLE_WITH_CAVEAT"
    NON_COMPARABLE = "NON_COMPARABLE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class CalibrationReferenceStatus(StrEnum):
    LOCKED_VALUE_NOT_PUBLIC = "locked_value_not_public"
    KNOWN = "known"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TargetCell:
    """One outcome × horizon × optional stratum in an evaluation contract."""

    outcome: OutcomeVariable
    horizon: ForecastHorizon
    stratum: str | None = None

    def __post_init__(self) -> None:
        if not _is_enum_member(self.outcome, OutcomeVariable):
            raise ValueError("target-cell outcome must be an OutcomeVariable")
        if not _is_enum_member(self.horizon, ForecastHorizon):
            raise ValueError("target-cell horizon must be a ForecastHorizon")
        if self.stratum is not None and not self.stratum:
            raise ValueError("target-cell stratum must be non-empty when provided")

    @property
    def name(self) -> str:
        label = f"{self.horizon.label}/{self.outcome.value}"
        return label if self.stratum is None else f"{label}/{self.stratum}"


@dataclass(frozen=True, slots=True)
class WeightedTargetCell:
    cell: TargetCell
    weight: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("target-cell weights must be positive and finite")


@dataclass(frozen=True, slots=True)
class WeightedOutcome:
    outcome: OutcomeVariable
    weight: float

    def __post_init__(self) -> None:
        if not _is_enum_member(self.outcome, OutcomeVariable):
            raise ValueError("weighted target must be an OutcomeVariable")
        if not math.isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("outcome weights must be positive and finite")


@dataclass(frozen=True, slots=True)
class EvaluationDefinition:
    """Immutable mathematical identity and scientific role of an evaluation."""

    name: str
    category: MetricCategory
    implementation_status: EvaluationImplementation
    production_acceptance: ProductionAcceptance
    formula: str
    optimization_direction: OptimizationDirection
    units: MetricUnits
    target_variables: tuple[OutcomeVariable, ...]
    horizons: tuple[ForecastHorizon, ...]
    scoring_cells: tuple[TargetCell, ...]
    normalization_rule: NormalizationRule
    normalization_reference: str
    aggregation_order: tuple[AggregationLevel, ...]
    scoring_unit: AggregationLevel
    weighting_rule: WeightingRule
    cell_weights: tuple[WeightedTargetCell, ...]
    missing_cell_policy: MissingCellPolicy
    non_finite_policy: str
    minimum_rows_per_cell: int | None
    final_score_interpretation: str
    raw_metric_units: MetricUnits | None = None
    implementation_id: str | None = None
    raw_metric_direction: OptimizationDirection = OptimizationDirection.UNKNOWN
    normalization_floor: float | None = None
    perfect_metric_value: float | None = None
    score_bounds: tuple[float, float] | None = None
    calibration_reference: str = "UNKNOWN"
    calibration_reference_status: CalibrationReferenceStatus = CalibrationReferenceStatus.UNKNOWN
    calibration_reference_value: float | None = None
    uncertainty_unit: AggregationLevel | None = None
    uncertainty_protocol: str = "UNKNOWN"
    compatible_benchmarks: tuple[str, ...] = ()
    comparable_result_families: tuple[str, ...] = ()
    target_names: tuple[str, ...] = ()
    cell_definition: str = "UNKNOWN"
    target_weights: tuple[WeightedOutcome, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.formula or not self.final_score_interpretation:
            raise ValueError("evaluation name, formula, and interpretation are required")
        if not _is_enum_member(self.category, MetricCategory):
            raise ValueError("evaluation category must be a MetricCategory")
        if not _is_enum_member(self.optimization_direction, OptimizationDirection):
            raise ValueError("evaluation direction must be an OptimizationDirection")
        if len(set(self.target_variables)) != len(self.target_variables):
            raise ValueError("evaluation target variables must be unique")
        if len(set(self.horizons)) != len(self.horizons):
            raise ValueError("evaluation horizons must be unique")
        if len(set(self.scoring_cells)) != len(self.scoring_cells):
            raise ValueError("evaluation scoring cells must be unique")
        weighted_cells = tuple(item.cell for item in self.cell_weights)
        if len(set(weighted_cells)) != len(weighted_cells):
            raise ValueError("evaluation cell weights must not repeat cells")
        if any(cell not in self.scoring_cells for cell in weighted_cells):
            raise ValueError("cell weights must refer to registered scoring cells")
        weighted_targets = tuple(item.outcome for item in self.target_weights)
        if len(set(weighted_targets)) != len(weighted_targets):
            raise ValueError("evaluation target weights must not repeat outcomes")
        if any(outcome not in self.target_variables for outcome in weighted_targets):
            raise ValueError("target weights must refer to registered outcome variables")
        if self.minimum_rows_per_cell is not None and self.minimum_rows_per_cell < 1:
            raise ValueError("minimum_rows_per_cell must be positive")
        for value, name in (
            (self.normalization_floor, "normalization floor"),
            (self.perfect_metric_value, "perfect metric value"),
            (self.calibration_reference_value, "calibration reference value"),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.raw_metric_direction is OptimizationDirection.LOWER_IS_BETTER:
            if (
                self.normalization_floor is not None
                and self.perfect_metric_value is not None
                and self.normalization_floor <= self.perfect_metric_value
            ):
                raise ValueError("lower-is-better floor must exceed the perfect metric value")
        if self.raw_metric_direction is OptimizationDirection.HIGHER_IS_BETTER:
            if (
                self.normalization_floor is not None
                and self.perfect_metric_value is not None
                and self.normalization_floor >= self.perfect_metric_value
            ):
                raise ValueError("higher-is-better floor must be below the perfect metric value")
        if len(set(self.target_names)) != len(self.target_names) or any(
            not name for name in self.target_names
        ):
            raise ValueError("evaluation target names must be non-empty and unique")
        if len(set(self.compatible_benchmarks)) != len(self.compatible_benchmarks):
            raise ValueError("compatible benchmark names must be unique")
        if self.score_bounds is not None:
            low, high = self.score_bounds
            if not math.isfinite(low) or not math.isfinite(high) or low > high:
                raise ValueError("score bounds must be finite and ordered")
        if self.implementation_status is EvaluationImplementation.IMPLEMENTED:
            if self.implementation_id is None:
                raise ValueError("implemented evaluations need an implementation id")
        elif self.implementation_id is not None:
            raise ValueError("unimplemented evaluations cannot name an implementation")
        if self.category is MetricCategory.UNIMPLEMENTED_EVALUATION:
            if self.implementation_status is not EvaluationImplementation.NOT_IMPLEMENTED:
                raise ValueError("unimplemented evaluation category must remain unimplemented")
            if self.production_acceptance is not ProductionAcceptance.NONE:
                raise ValueError("unimplemented production evaluations cannot be accepted")
        if self.production_acceptance is ProductionAcceptance.PROPOSED_UNRESOLVED:
            if self.category is not MetricCategory.BENCHMARK_SCORE:
                raise ValueError("only a benchmark score may have a proposed production contract")
        if self.production_acceptance is ProductionAcceptance.ACCEPTED_HISTORICAL:
            if self.category is not MetricCategory.BENCHMARK_SCORE:
                raise ValueError("only a benchmark score may be historically accepted")
        if self.calibration_reference_status is CalibrationReferenceStatus.KNOWN:
            if self.calibration_reference_value is None:
                raise ValueError("known calibration reference needs a numeric value")
        elif self.calibration_reference_value is not None:
            raise ValueError("unknown calibration reference value must not be populated")

    @property
    def is_production_scorer(self) -> bool:
        return (
            self.category is MetricCategory.BENCHMARK_SCORE
            and self.production_acceptance is ProductionAcceptance.ACCEPTED_HISTORICAL
        )

    @property
    def is_accepted_production_scorer(self) -> bool:
        return self.is_production_scorer

    @property
    def is_proposed_scorer(self) -> bool:
        return self.production_acceptance is ProductionAcceptance.PROPOSED_UNRESOLVED


@dataclass(frozen=True, slots=True)
class HistoricalComparison:
    """Evidence-bounded comparison conclusion without result payloads."""

    comparison_name: str
    status: ComparabilityStatus
    left_result_family: str
    right_result_family: str
    identity_basis: str
    rationale: str
    provenance_aliases: tuple[str, ...] = ()
    left_evaluation_name: str = "UNKNOWN"
    right_evaluation_name: str = "UNKNOWN"
    compatibility_transform_name: str | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.comparison_name,
                self.left_result_family,
                self.right_result_family,
                self.identity_basis,
                self.rationale,
            )
        ):
            raise ValueError("historical comparison identity and rationale are required")
        if not self.left_evaluation_name or not self.right_evaluation_name:
            raise ValueError("comparison evaluation names must be explicit or UNKNOWN")


class ClaimType(StrEnum):
    CAUSAL_TRAINING_EFFECTS = "causal_training_effects"
    REAL_ATHLETE_VALIDITY = "real_athlete_validity"
    BIOLOGICAL_PARAMETER_IDENTIFICATION = "biological_parameter_identification"
    TRAINING_PRESCRIPTION_UTILITY = "training_prescription_utility"
    SUPPORT_EXTERNAL_GENERALIZATION = "support_external_generalization"


REQUIRED_UNSUPPORTED_CLAIMS = frozenset(ClaimType)


@dataclass(frozen=True, slots=True)
class ClaimBoundary:
    performance_alone_establishes: str
    unsupported_claims: frozenset[ClaimType]

    def __post_init__(self) -> None:
        if self.unsupported_claims != REQUIRED_UNSUPPORTED_CLAIMS:
            raise ValueError("claim boundary must state all current scientific claim ceilings")


PERFORMANCE_ONLY_CLAIM_BOUNDARY = ClaimBoundary(
    performance_alone_establishes=(
        "Forecast performance under the named synthetic task, observation contract, "
        "benchmark formulation, and evaluation protocol."
    ),
    unsupported_claims=REQUIRED_UNSUPPORTED_CLAIMS,
)


@dataclass(frozen=True, slots=True)
class BenchmarkDefinition:
    name: str
    research_question: str
    task: TaskDefinition
    observation: ObservationContract
    dynamics: DynamicsModel
    horizons: tuple[ForecastHorizon, ...]
    outcomes: tuple[OutcomeDefinition, ...]
    status: BenchmarkStatus
    dataset_identity: IdentityReference
    evaluation_identity: EvaluationDefinition
    claim_boundary: ClaimBoundary
    parent_name: str | None = None
    disposition_note: str = ""
    research_evaluations: tuple[EvaluationDefinition, ...] = ()
    qualification_evaluations: tuple[EvaluationDefinition, ...] = ()
    model_selection_evaluations: tuple[EvaluationDefinition, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("benchmark name must not be empty")
        if self.horizons != self.task.horizons:
            raise ValueError("benchmark horizons must match its task")
        if self.outcomes != self.task.outcomes:
            raise ValueError("benchmark outcomes must match its task")
        if self.name not in self.evaluation_identity.compatible_benchmarks:
            raise ValueError("benchmark must reference a compatible evaluation definition")
        for evaluation in self.research_evaluations:
            if evaluation.category is not MetricCategory.RESEARCH_DIAGNOSTIC:
                raise ValueError("research_evaluations must contain research diagnostics only")
            if self.name not in evaluation.compatible_benchmarks:
                raise ValueError("research diagnostic is not compatible with this benchmark")
        for evaluation in self.qualification_evaluations:
            if evaluation.category is not MetricCategory.QUALIFICATION_STATISTIC:
                raise ValueError(
                    "qualification_evaluations must contain qualification statistics only"
                )
            if self.name not in evaluation.compatible_benchmarks:
                raise ValueError("qualification statistic is not compatible with this benchmark")
        for evaluation in self.model_selection_evaluations:
            if evaluation.category is not MetricCategory.MODEL_SELECTION_METRIC:
                raise ValueError("model_selection_evaluations must contain selection metrics only")
            if self.name not in evaluation.compatible_benchmarks:
                raise ValueError("selection metric is not compatible with this benchmark")

    @property
    def production_evaluation(self) -> EvaluationDefinition:
        """The only evaluation definition used by production benchmark scoring."""
        return self.evaluation_identity


class StudyType(StrEnum):
    PREDICTIVE_HEADROOM = "predictive_headroom"
    OBSERVABILITY = "observability"
    RECONSTRUCTABILITY = "reconstructability"
    SYSTEM_IDENTIFICATION = "system_identification"
    REAL_DATA_GROUNDING = "real_data_grounding"


class StudyStatus(StrEnum):
    CONTRACT_ONLY = "contract_only"


@dataclass(frozen=True, slots=True)
class StudyDefinition:
    name: str
    study_type: StudyType
    research_question: str
    status: StudyStatus = StudyStatus.CONTRACT_ONLY
