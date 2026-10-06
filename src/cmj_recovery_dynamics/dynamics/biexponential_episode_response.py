"""Parameterized two-negative-exponential episode-response equation."""

from dataclasses import dataclass
from math import exp, isfinite

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)


@dataclass(frozen=True, slots=True)
class BiexponentialEpisodeParameters:
    fast_amplitude: float
    slow_amplitude: float
    fast_time_constant_hours: float
    slow_time_constant_hours: float

    def __post_init__(self) -> None:
        if any(
            not isfinite(value)
            for value in (
                self.fast_amplitude,
                self.slow_amplitude,
                self.fast_time_constant_hours,
                self.slow_time_constant_hours,
            )
        ):
            raise ValueError("episode-response parameters must be finite")
        if self.fast_amplitude < 0 or self.slow_amplitude < 0:
            raise ValueError("decrement amplitudes must be non-negative")
        if self.fast_time_constant_hours <= 0 or self.slow_time_constant_hours <= 0:
            raise ValueError("time constants must be positive")


def episode_response(lag_hours: float, parameters: BiexponentialEpisodeParameters) -> float:
    """Return -a_fast exp(-t/τ_fast) - a_slow exp(-t/τ_slow)."""
    if not isfinite(lag_hours) or lag_hours < 0:
        raise ValueError("lag must be finite and non-negative")
    return -parameters.fast_amplitude * exp(
        -lag_hours / parameters.fast_time_constant_hours
    ) - parameters.slow_amplitude * exp(-lag_hours / parameters.slow_time_constant_hours)


BIEXPONENTIAL_EPISODE_RESPONSE = DynamicsModel(
    name="biexponential_episode_response",
    family=DynamicsFamily.BIEXPONENTIAL_EPISODE_RESPONSE,
    equation_summary=(
        "Each exposure contributes a fast and slow negative exponential; "
        "historical load-to-parameter maps remain separate from this equation."
    ),
    implementation_status=ModelImplementationStatus.PARTIAL_EQUATION,
)
