"""Parameterized participant-weighted softplus threshold response component."""

from dataclasses import dataclass
from math import exp, fsum, isfinite, log1p

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)

EXPOSURE_COMPONENT_COUNT = 7
THRESHOLD_RANGE = (0.35, 0.75)
SOFTPLUS_TEMPERATURE = 0.05
SOFTPLUS_SCALE = 4.0


@dataclass(frozen=True, slots=True)
class ThresholdResponseParameters:
    participant_load_weights: tuple[float, ...]
    threshold: float
    response_offset: float

    def __post_init__(self) -> None:
        if len(self.participant_load_weights) != EXPOSURE_COMPONENT_COUNT:
            raise ValueError("seven normalized load weights are required")
        if any(not isfinite(value) for value in self.participant_load_weights):
            raise ValueError("load weights must be finite")
        low, high = THRESHOLD_RANGE
        if not isfinite(self.threshold) or not low <= self.threshold <= high:
            raise ValueError("threshold must lie within its recovered range")
        if not isfinite(self.response_offset):
            raise ValueError("response offset must be finite")


def threshold_response_score(
    normalized_exposure_components: tuple[float, ...],
    parameters: ThresholdResponseParameters,
) -> float:
    """Compute the recovered softplus hinge term added to the response score."""
    if len(normalized_exposure_components) != EXPOSURE_COMPONENT_COUNT:
        raise ValueError("seven normalized exposure components are required")
    if any(not isfinite(value) for value in normalized_exposure_components):
        raise ValueError("exposure components must be finite")
    participant_load = fsum(
        weight * component
        for weight, component in zip(
            parameters.participant_load_weights,
            normalized_exposure_components,
            strict=True,
        )
    )
    scaled_distance = (participant_load - parameters.threshold) / SOFTPLUS_TEMPERATURE
    softplus = max(scaled_distance, 0.0) + log1p(exp(-abs(scaled_distance)))
    return SOFTPLUS_SCALE * SOFTPLUS_TEMPERATURE * softplus + parameters.response_offset


THRESHOLD_RESPONSE = DynamicsModel(
    name="threshold_response",
    family=DynamicsFamily.THRESHOLD_RESPONSE,
    equation_summary=(
        "Participant-weighted normalized load enters a softplus threshold hinge "
        "with a bounded threshold and response offset."
    ),
    implementation_status=ModelImplementationStatus.PARTIAL_EQUATION,
)
