"""Event-time camp exposure, fatigue, adaptation, and recovery equations."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, fsum, isfinite, nextafter

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)


@dataclass(frozen=True, slots=True)
class EventTimeParameters:
    """W01 response parameters; bounded design ranges are not population biology."""

    dose_response_ceiling_kappa: float
    dose_half_saturation_delta: float
    dose_exponent_gamma: float
    fast_fatigue_time_constant_hours: float
    slow_adaptation_time_constant_hours: float
    memory_shape_beta: float
    fatigue_force_amplitude_n_per_kg: float
    adaptation_force_amplitude_n_per_kg: float
    fatigue_impulse_amplitude_m_per_s: float
    adaptation_impulse_amplitude_m_per_s: float

    def __post_init__(self) -> None:
        bounded = (
            (self.dose_response_ceiling_kappa, 0.0, 10.0, True, "κ"),
            (self.dose_half_saturation_delta, 0.1, 10.0, True, "δ"),
            (self.dose_exponent_gamma, 0.1, 6.9, True, "γ"),
            (self.fast_fatigue_time_constant_hours, 6.0, 120.0, True, "fast τ"),
            (self.slow_adaptation_time_constant_hours, 72.0, 504.0, True, "slow τ"),
            (self.memory_shape_beta, 0.5, 1.5, True, "β"),
            (self.fatigue_force_amplitude_n_per_kg, 0.0, 10.0, False, "force fatigue amplitude"),
            (
                self.adaptation_force_amplitude_n_per_kg,
                0.0,
                10.0,
                False,
                "force adaptation amplitude",
            ),
            (self.fatigue_impulse_amplitude_m_per_s, 0.0, 2.0, False, "impulse fatigue amplitude"),
            (
                self.adaptation_impulse_amplitude_m_per_s,
                0.0,
                2.0,
                False,
                "impulse adaptation amplitude",
            ),
        )
        for value, lower, upper, strictly_positive, name in bounded:
            if (
                not isfinite(value)
                or not lower <= value <= upper
                or (strictly_positive and value <= 0)
            ):
                raise ValueError(f"{name} must be finite and within [{lower}, {upper}]")


def hill_saturation(dose: float, parameters: EventTimeParameters) -> float:
    """Return W3(D)=κD^γ/(δ^γ+D^γ), evaluated in an overflow-safe ratio form."""
    if not isfinite(dose) or dose < 0:
        raise ValueError("dose must be finite and non-negative")
    if dose == 0:
        return 0.0
    ratio = (parameters.dose_half_saturation_delta / dose) ** parameters.dose_exponent_gamma
    result = parameters.dose_response_ceiling_kappa / (1.0 + ratio)
    if result == parameters.dose_response_ceiling_kappa:
        return nextafter(result, 0.0)
    return result


def stretched_exponential_memory(
    elapsed_hours: float,
    time_constant_hours: float,
    beta: float,
) -> float:
    """Return W2(Δt)=exp[-(Δt/τ)^β] for nonnegative elapsed time."""
    if not isfinite(elapsed_hours) or elapsed_hours < 0:
        raise ValueError("elapsed time must be finite and non-negative")
    if not isfinite(time_constant_hours) or time_constant_hours <= 0:
        raise ValueError("time constant must be finite and positive")
    if not isfinite(beta) or beta <= 0:
        raise ValueError("memory shape β must be finite and positive")
    try:
        exponent = (elapsed_hours / time_constant_hours) ** beta
    except OverflowError:
        return 0.0
    return exp(-exponent)


@dataclass(frozen=True, slots=True)
class ExposureComponent:
    """Public component measurement and its explicit normalization reference."""

    name: str
    value: float | None
    units: str
    normalization: float
    observed: bool = True
    day_mask: bool = True
    event_mask: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.units.strip():
            raise ValueError("exposure component name and units are required")
        if not isfinite(self.normalization) or self.normalization <= 0:
            raise ValueError("exposure normalization must be finite and positive")
        if self.observed:
            if self.value is None or not isfinite(self.value) or self.value < 0:
                raise ValueError("observed exposure values must be finite and non-negative")
        elif self.value is not None:
            raise ValueError("unobserved exposure components must use value=None")

    @property
    def contribution(self) -> float | None:
        if not (self.observed and self.day_mask and self.event_mask):
            return None
        assert self.value is not None
        return self.value / self.normalization


def normalized_exposure_dose(components: tuple[ExposureComponent, ...]) -> float:
    """Sum observed, unmasked public components as cᵢ=xᵢ/rᵢ."""
    if not components:
        raise ValueError("at least one exposure component is required")
    if len({component.name for component in components}) != len(components):
        raise ValueError("exposure component names must be unique within an event")
    included = tuple(component.contribution for component in components)
    values = tuple(value for value in included if value is not None)
    if not values:
        raise ValueError("an exposure with no observed public component is not zero dose")
    dose = fsum(values)
    if not isfinite(dose):
        raise ValueError("normalized exposure dose must remain finite")
    return dose


@dataclass(frozen=True, slots=True)
class ExposureEvent:
    event_id: str
    timestamp_hours: float
    kind: str
    components: tuple[ExposureComponent, ...]

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.kind.strip():
            raise ValueError("exposure event id and kind are required")
        if not isfinite(self.timestamp_hours) or self.timestamp_hours < 0:
            raise ValueError("exposure event time must be finite and non-negative")
        if not self.components:
            raise ValueError("exposure events require public components")

    @property
    def joint_dose(self) -> float:
        return normalized_exposure_dose(self.components)


@dataclass(frozen=True, slots=True)
class AssessmentEvent:
    assessment_id: str
    timestamp_hours: float

    def __post_init__(self) -> None:
        if not self.assessment_id.strip():
            raise ValueError("assessment id is required")
        if not isfinite(self.timestamp_hours) or self.timestamp_hours < 0:
            raise ValueError("assessment time must be finite and non-negative")


type DynamicsEvent = ExposureEvent | AssessmentEvent


@dataclass(frozen=True, slots=True)
class CampResponseState:
    timestamp_hours: float
    cumulative_dose: float
    fatigue_force_n_per_kg: float
    adaptation_force_n_per_kg: float
    fatigue_impulse_m_per_s: float
    adaptation_impulse_m_per_s: float

    @property
    def net_force_innovation_n_per_kg(self) -> float:
        return self.adaptation_force_n_per_kg - self.fatigue_force_n_per_kg

    @property
    def net_impulse_innovation_m_per_s(self) -> float:
        return self.adaptation_impulse_m_per_s - self.fatigue_impulse_m_per_s


@dataclass(frozen=True, slots=True)
class EventTransition:
    event_id: str
    event_kind: str
    timestamp_hours: float
    state_before_event: CampResponseState
    state_after_event: CampResponseState
    dose_increment: float
    fatigue_increment_force_n_per_kg: float
    adaptation_increment_force_n_per_kg: float
    fatigue_increment_impulse_m_per_s: float
    adaptation_increment_impulse_m_per_s: float


@dataclass(frozen=True, slots=True)
class CampSimulation:
    transitions: tuple[EventTransition, ...]
    queried_states: tuple[tuple[float, CampResponseState], ...]

    def state_at(self, timestamp_hours: float) -> CampResponseState:
        for timestamp, state in self.queried_states:
            if timestamp == timestamp_hours:
                return state
        raise ValueError(f"time {timestamp_hours} was not queried")


def _evolve(
    state: CampResponseState,
    target_time_hours: float,
    parameters: EventTimeParameters,
) -> CampResponseState:
    if target_time_hours < state.timestamp_hours:
        raise ValueError("event-time dynamics cannot move backwards")
    elapsed = target_time_hours - state.timestamp_hours
    if elapsed == 0:
        return state
    fast = stretched_exponential_memory(
        elapsed, parameters.fast_fatigue_time_constant_hours, parameters.memory_shape_beta
    )
    slow = stretched_exponential_memory(
        elapsed, parameters.slow_adaptation_time_constant_hours, parameters.memory_shape_beta
    )
    return CampResponseState(
        timestamp_hours=target_time_hours,
        cumulative_dose=state.cumulative_dose,
        fatigue_force_n_per_kg=state.fatigue_force_n_per_kg * fast,
        adaptation_force_n_per_kg=state.adaptation_force_n_per_kg * slow,
        fatigue_impulse_m_per_s=state.fatigue_impulse_m_per_s * fast,
        adaptation_impulse_m_per_s=state.adaptation_impulse_m_per_s * slow,
    )


def simulate_camp_response(
    events: tuple[DynamicsEvent, ...],
    query_times_hours: tuple[float, ...],
    parameters: EventTimeParameters,
) -> CampSimulation:
    """Apply timestamped dose increments, then evolve fast and slow states."""
    if not query_times_hours:
        raise ValueError("at least one query time is required")
    if any(not isfinite(time) or time < 0 for time in query_times_hours):
        raise ValueError("query times must be finite and non-negative")
    event_ids = tuple(
        event.event_id if isinstance(event, ExposureEvent) else event.assessment_id
        for event in events
    )
    if len(set(event_ids)) != len(event_ids):
        raise ValueError("event identifiers must be unique")
    if any(not isfinite(event.timestamp_hours) or event.timestamp_hours < 0 for event in events):
        raise ValueError("event times must be finite and non-negative")
    ordered = tuple(
        sorted(
            events,
            key=lambda event: (
                event.timestamp_hours,
                0 if isinstance(event, ExposureEvent) else 1,
                event.event_id if isinstance(event, ExposureEvent) else event.assessment_id,
            ),
        )
    )
    if any(event.timestamp_hours < 0 for event in ordered):
        raise ValueError("events cannot precede the camp index origin")
    initial = CampResponseState(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    if any(time < initial.timestamp_hours for time in query_times_hours):
        raise ValueError("query time precedes the camp index origin")

    sorted_queries = sorted(enumerate(query_times_hours), key=lambda item: item[1])
    query_states: list[CampResponseState | None] = [None] * len(query_times_hours)
    transitions: list[EventTransition] = []
    current = initial
    event_index = 0
    for query_index, query_time in sorted_queries:
        while event_index < len(ordered) and ordered[event_index].timestamp_hours <= query_time:
            event = ordered[event_index]
            before = _evolve(current, event.timestamp_hours, parameters)
            if isinstance(event, ExposureEvent):
                dose = event.joint_dose
                dose_after = before.cumulative_dose + dose
                transformed_increment = hill_saturation(dose_after, parameters) - hill_saturation(
                    before.cumulative_dose, parameters
                )
                if transformed_increment < 0 or not isfinite(transformed_increment):
                    raise ValueError(
                        "cumulative Hill dose increment must be finite and non-negative"
                    )
                fatigue_force = parameters.fatigue_force_amplitude_n_per_kg * transformed_increment
                adaptation_force = (
                    parameters.adaptation_force_amplitude_n_per_kg * transformed_increment
                )
                fatigue_impulse = (
                    parameters.fatigue_impulse_amplitude_m_per_s * transformed_increment
                )
                adaptation_impulse = (
                    parameters.adaptation_impulse_amplitude_m_per_s * transformed_increment
                )
                after = CampResponseState(
                    event.timestamp_hours,
                    dose_after,
                    before.fatigue_force_n_per_kg + fatigue_force,
                    before.adaptation_force_n_per_kg + adaptation_force,
                    before.fatigue_impulse_m_per_s + fatigue_impulse,
                    before.adaptation_impulse_m_per_s + adaptation_impulse,
                )
                kind = event.kind
                dose_increment = dose
            else:
                after = before
                kind = "assessment"
                dose_increment = 0.0
                fatigue_force = adaptation_force = fatigue_impulse = adaptation_impulse = 0.0
            transitions.append(
                EventTransition(
                    event.event_id if isinstance(event, ExposureEvent) else event.assessment_id,
                    kind,
                    event.timestamp_hours,
                    before,
                    after,
                    dose_increment,
                    fatigue_force,
                    adaptation_force,
                    fatigue_impulse,
                    adaptation_impulse,
                )
            )
            current = after
            event_index += 1
        query_states[query_index] = _evolve(current, query_time, parameters)
    assert all(state is not None for state in query_states)
    return CampSimulation(
        tuple(transitions),
        tuple(
            (query_times_hours[i], state)
            for i, state in enumerate(query_states)
            if state is not None
        ),
    )


EVENT_TIME_ADAPTATION_RECOVERY = DynamicsModel(
    name="event_time_adaptation_recovery",
    family=DynamicsFamily.EVENT_TIME_ADAPTATION_RECOVERY,
    equation_summary=(
        "Normalized public event doses enter a cumulative Hill transform; its increments "
        "feed fast fatigue and slow adaptation states with stretched-exponential memory. "
        "Net force and impulse innovations are adaptation minus fatigue."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)


__all__ = [
    "AssessmentEvent",
    "CampResponseState",
    "CampSimulation",
    "DynamicsEvent",
    "EventTimeParameters",
    "EventTransition",
    "EVENT_TIME_ADAPTATION_RECOVERY",
    "ExposureComponent",
    "ExposureEvent",
    "hill_saturation",
    "normalized_exposure_dose",
    "simulate_camp_response",
    "stretched_exponential_memory",
]
