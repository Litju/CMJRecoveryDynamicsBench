"""Fixed exponential modes and typed smooth-discrepancy scale contract."""

from math import exp, isfinite

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)

FAST_MODE_HOURS = 24.0
SLOW_MODE_HOURS = 84.0
DISCREPANCY_FEATURE_COUNT = 32
DISCREPANCY_LENGTH_SCALE = 0.65
DISCREPANCY_AMPLITUDE_FRACTION = 0.006


def fixed_mode_response(lag_hours: float, fast_amplitude: float, slow_amplitude: float) -> float:
    """Return the recovered fixed 24 h / 84 h negative exponential modes."""
    if any(not isfinite(value) for value in (lag_hours, fast_amplitude, slow_amplitude)):
        raise ValueError("lag and amplitudes must be finite")
    if lag_hours < 0 or fast_amplitude < 0 or slow_amplitude < 0:
        raise ValueError("lag and mode amplitudes must be non-negative")
    return -fast_amplitude * exp(-lag_hours / FAST_MODE_HOURS) - slow_amplitude * exp(
        -lag_hours / SLOW_MODE_HOURS
    )


FIXED_MODE_DISCREPANCY_RESPONSE = DynamicsModel(
    name="fixed_mode_discrepancy_response",
    family=DynamicsFamily.FIXED_MODE_DISCREPANCY_RESPONSE,
    equation_summary=(
        "Fixed mathematical 24 h and 84 h modes are combined with a bounded smooth "
        "discrepancy; random-feature coefficients are not part of this contract."
    ),
    implementation_status=ModelImplementationStatus.PARTIAL_EQUATION,
)
