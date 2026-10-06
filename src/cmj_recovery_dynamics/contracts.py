"""Immutable, typed contracts shared by benchmark, task, and study definitions."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum


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


UNRESOLVED_EVALUATION_IDENTITY = IdentityReference(
    scientific_name="evaluation_identity_unresolved",
    status=ReferenceStatus.UNRESOLVED,
    details="Metric and scorer lineage remain outside this bootstrap contract.",
)


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
    evaluation_identity: IdentityReference
    claim_boundary: ClaimBoundary
    parent_name: str | None = None
    disposition_note: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("benchmark name must not be empty")
        if self.horizons != self.task.horizons:
            raise ValueError("benchmark horizons must match its task")
        if self.outcomes != self.task.outcomes:
            raise ValueError("benchmark outcomes must match its task")


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
