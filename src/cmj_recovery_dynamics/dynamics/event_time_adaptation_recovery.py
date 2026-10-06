"""Parameterized Hill saturation and event-time memory pieces for camp dynamics."""

from dataclasses import dataclass
from math import exp, isfinite

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)


@dataclass(frozen=True, slots=True)
class EventTimeParameters:
    adaptation_gain_kappa: float
    dose_half_saturation_delta: float
    dose_exponent_gamma: float
    memory_time_constant_hours: float
    memory_exponent_beta: float

    def __post_init__(self) -> None:
        if any(
            not isfinite(value) or value <= 0
            for value in (
                self.adaptation_gain_kappa,
                self.dose_half_saturation_delta,
                self.dose_exponent_gamma,
                self.memory_time_constant_hours,
                self.memory_exponent_beta,
            )
        ):
            raise ValueError("event-time parameters must be finite and positive")


def hill_saturation(dose: float, parameters: EventTimeParameters) -> float:
    """Return κD^γ / (δ^γ + D^γ) for a non-negative normalized dose."""
    if not isfinite(dose) or dose < 0:
        raise ValueError("dose must be finite and non-negative")
    dose_power = dose**parameters.dose_exponent_gamma
    half_saturation_power = parameters.dose_half_saturation_delta**parameters.dose_exponent_gamma
    return parameters.adaptation_gain_kappa * dose_power / (half_saturation_power + dose_power)


def exponential_memory_kernel(
    elapsed_hours: float,
    parameters: EventTimeParameters,
) -> float:
    """Return exp[-(elapsed / τ)^β] for a non-negative event-time lag."""
    if not isfinite(elapsed_hours) or elapsed_hours < 0:
        raise ValueError("elapsed time must be finite and non-negative")
    scaled_lag = elapsed_hours / parameters.memory_time_constant_hours
    return exp(-(scaled_lag**parameters.memory_exponent_beta))


EVENT_TIME_ADAPTATION_RECOVERY = DynamicsModel(
    name="event_time_adaptation_recovery",
    family=DynamicsFamily.EVENT_TIME_ADAPTATION_RECOVERY,
    equation_summary=(
        "Normalized timestamped event doses feed Hill-saturated adaptation; "
        "a stretched-exponential kernel carries event-time memory."
    ),
    implementation_status=ModelImplementationStatus.PARTIAL_EQUATION,
)
