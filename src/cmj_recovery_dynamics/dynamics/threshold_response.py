"""Participant-weighted threshold response with bounded episode kinetics."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, fsum, isfinite, log1p
from typing import TYPE_CHECKING, Literal

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import normalized_load_vector
from cmj_recovery_dynamics.reproduction.single_exposure import (
    PublicExposure,
)

if TYPE_CHECKING:
    from cmj_recovery_dynamics.reproduction.single_exposure import KeyedRandomStreams

EXPOSURE_COMPONENT_COUNT = 7
THRESHOLD_RANGE = (0.35, 0.75)
SOFTPLUS_TEMPERATURE = 0.05
SOFTPLUS_SCALE = 4.0
HINGE_OFFSET = -0.30

FAST_AMPLITUDE_SUPPORT = (0.01, 0.08)
SLOW_AMPLITUDE_SUPPORT = (0.0, 0.08)
FAST_TIME_CONSTANT_SUPPORT_HOURS = (12.0, 36.0)
SLOW_TIME_CONSTANT_SUPPORT_HOURS = (48.0, 120.0)
PARTICIPANT_AMPLITUDE_LOGIT_SD = 0.6
PARTICIPANT_SLOW_AMPLITUDE_SD_MULTIPLIER = 0.90
CAMP_AMPLITUDE_LOGIT_SD = 0.12
PARTICIPANT_TIME_CONSTANT_LOGIT_SD = 0.80
PARTICIPANT_SENSITIVITY_LOG_SD = 0.9

FAST_BASE_WEIGHTS = (0.14, 0.14, 0.16, 0.16, 0.14, 0.12, 0.14)
SLOW_BASE_WEIGHTS = (0.18, 0.18, 0.13, 0.10, 0.12, 0.12, 0.17)
FAST_INTERACTIONS = ((2, 3, 0.60), (4, 5, 0.35), (0, 6, 0.20))
SLOW_INTERACTIONS = ((0, 1, 0.45), (6, 4, 0.25), (2, 5, 0.20))
METRICS = ("force", "impulse")
COMPONENTS = ("fast", "slow")
PRIOR_HIGH_LOAD_PROBABILITY = 0.30


@dataclass(frozen=True, slots=True)
class ThresholdResponseParameters:
    participant_load_weights_fast: tuple[float, ...]
    participant_load_weights_slow: tuple[float, ...]
    threshold: float
    amplitude_logits: tuple[tuple[float, float], tuple[float, float]] = ((0.0, 0.0), (0.0, 0.0))
    time_constant_logits: tuple[tuple[float, float], tuple[float, float]] = (
        (0.0, 0.0),
        (0.0, 0.0),
    )

    def __post_init__(self) -> None:
        for weights in (self.participant_load_weights_fast, self.participant_load_weights_slow):
            if len(weights) != EXPOSURE_COMPONENT_COUNT or any(
                not isfinite(value) or value <= 0.0 for value in weights
            ):
                raise ValueError("seven finite positive participant load weights are required")
            if not abs(fsum(weights) - 1.0) <= 1e-12:
                raise ValueError("participant load weights must sum to one")
        low, high = THRESHOLD_RANGE
        if not isfinite(self.threshold) or not low <= self.threshold <= high:
            raise ValueError("threshold must lie within its recovered range")
        if (
            any(
                len(row) != 2 or any(not isfinite(value) for value in row)
                for matrix in (self.amplitude_logits, self.time_constant_logits)
                for row in matrix
            )
            or len(self.amplitude_logits) != 2
            or len(self.time_constant_logits) != 2
        ):
            raise ValueError("force and impulse require finite fast/slow participant effects")


@dataclass(frozen=True, slots=True)
class ThresholdCampEffects:
    amplitude_logit_offsets: tuple[tuple[float, float], tuple[float, float]]


def sample_threshold_response_parameters(
    streams: KeyedRandomStreams,
) -> ThresholdResponseParameters:
    """Draw source-defined amplitude, time, load-sensitivity, and threshold effects."""
    amplitude_logits = tuple(
        (
            float(streams.generator("participant_amplitude_effect", metric, "fast").normal())
            * PARTICIPANT_AMPLITUDE_LOGIT_SD,
            float(streams.generator("participant_amplitude_effect", metric, "slow").normal())
            * PARTICIPANT_AMPLITUDE_LOGIT_SD
            * PARTICIPANT_SLOW_AMPLITUDE_SD_MULTIPLIER,
        )
        for metric in METRICS
    )
    time_constant_logits = tuple(
        tuple(
            float(streams.generator("participant_time_constant_effect", metric, component).normal())
            * PARTICIPANT_TIME_CONSTANT_LOGIT_SD
            for component in COMPONENTS
        )
        for metric in METRICS
    )
    latent = tuple(
        float(streams.generator("participant_sensitivity", "dimension", index).normal())
        for index in range(EXPOSURE_COMPONENT_COUNT)
    )
    multipliers = tuple(exp(PARTICIPANT_SENSITIVITY_LOG_SD * value) for value in latent)

    def normalized_weights(base: tuple[float, ...]) -> tuple[float, ...]:
        weighted = tuple(
            value * multiplier for value, multiplier in zip(base, multipliers, strict=True)
        )
        total = fsum(weighted)
        return tuple(value / total for value in weighted)

    threshold = float(
        streams.generator("participant_load_threshold", "threshold").uniform(*THRESHOLD_RANGE)
    )
    return ThresholdResponseParameters(
        normalized_weights(FAST_BASE_WEIGHTS),
        normalized_weights(SLOW_BASE_WEIGHTS),
        threshold,
        amplitude_logits,  # type: ignore[arg-type]
        time_constant_logits,  # type: ignore[arg-type]
    )


def sample_threshold_camp_effects(streams: KeyedRandomStreams) -> ThresholdCampEffects:
    offsets = tuple(
        tuple(
            float(streams.generator("camp_amplitude_effect", metric, component).normal())
            * CAMP_AMPLITUDE_LOGIT_SD
            for component in COMPONENTS
        )
        for metric in METRICS
    )
    return ThresholdCampEffects(offsets)  # type: ignore[arg-type]


def participant_load(
    normalized_exposure_components: tuple[float, ...],
    parameters: ThresholdResponseParameters,
    component: Literal["fast", "slow"] = "fast",
) -> float:
    if len(normalized_exposure_components) != EXPOSURE_COMPONENT_COUNT:
        raise ValueError("seven normalized exposure components are required")
    if any(
        not isfinite(value) or not 0.0 <= value <= 1.0 for value in normalized_exposure_components
    ):
        raise ValueError("normalized exposure components must lie in [0, 1]")
    weights = (
        parameters.participant_load_weights_fast
        if component == "fast"
        else parameters.participant_load_weights_slow
    )
    return fsum(
        weight * value
        for weight, value in zip(weights, normalized_exposure_components, strict=True)
    )


def softplus_threshold_hinge(participant_load_value: float, threshold: float) -> float:
    if not isfinite(participant_load_value) or not isfinite(threshold):
        raise ValueError("participant load and threshold must be finite")
    scaled = (participant_load_value - threshold) / SOFTPLUS_TEMPERATURE
    softplus = max(scaled, 0.0) + log1p(exp(-abs(scaled)))
    return SOFTPLUS_SCALE * SOFTPLUS_TEMPERATURE * softplus + HINGE_OFFSET


def threshold_response_score(
    normalized_exposure_components: tuple[float, ...],
    parameters: ThresholdResponseParameters,
    component: Literal["fast", "slow"] = "fast",
) -> float:
    """Return load, interaction, and threshold-hinge score before random effects."""
    load = participant_load(normalized_exposure_components, parameters, component)
    interactions = FAST_INTERACTIONS if component == "fast" else SLOW_INTERACTIONS
    return (
        load
        - 0.5
        + fsum(
            coefficient
            * (normalized_exposure_components[left] * normalized_exposure_components[right] - 0.25)
            for left, right, coefficient in interactions
        )
        + softplus_threshold_hinge(load, parameters.threshold)
    )


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + exp(-value))
    exponential = exp(value)
    return exponential / (1.0 + exponential)


def response_parameters_for_exposure(
    exposure: PublicExposure,
    participant: ThresholdResponseParameters,
    camp: ThresholdCampEffects,
    metric: Literal["force", "impulse"],
) -> tuple[float, float, float, float]:
    if metric not in METRICS:
        raise ValueError(f"unknown response metric: {metric}")
    vector = normalized_load_vector(exposure)
    metric_index = METRICS.index(metric)
    amplitude_supports = (FAST_AMPLITUDE_SUPPORT, SLOW_AMPLITUDE_SUPPORT)
    time_supports = (FAST_TIME_CONSTANT_SUPPORT_HOURS, SLOW_TIME_CONSTANT_SUPPORT_HOURS)
    amplitudes: list[float] = []
    time_constants: list[float] = []
    for index, component in enumerate(COMPONENTS):
        score = threshold_response_score(vector, participant, component)
        score += participant.amplitude_logits[metric_index][index]
        score += camp.amplitude_logit_offsets[metric_index][index]
        low, high = amplitude_supports[index]
        amplitudes.append(low + (high - low) * _sigmoid(score))
        time_low, time_high = time_supports[index]
        time_constants.append(
            time_low
            + (time_high - time_low)
            * _sigmoid(participant.time_constant_logits[metric_index][index])
        )
    return amplitudes[0], time_constants[0], amplitudes[1], time_constants[1]


def threshold_response_fraction(
    exposure: PublicExposure,
    lag_hours: float,
    participant: ThresholdResponseParameters,
    camp: ThresholdCampEffects,
    metric: Literal["force", "impulse"],
) -> float:
    if not isfinite(lag_hours) or lag_hours < 0.0:
        raise ValueError("lag must be finite and non-negative")
    fast_amp, fast_tau, slow_amp, slow_tau = response_parameters_for_exposure(
        exposure, participant, camp, metric
    )
    return -fast_amp * exp(-lag_hours / fast_tau) - slow_amp * exp(-lag_hours / slow_tau)


THRESHOLD_RESPONSE = DynamicsModel(
    name="threshold_response",
    family=DynamicsFamily.THRESHOLD_RESPONSE,
    equation_summary=(
        "Participant-specific normalized seven-feature weights and a bounded softplus threshold "
        "hinge map to bounded fast/slow episode amplitudes and time constants."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)

__all__ = [
    "CAMP_AMPLITUDE_LOGIT_SD",
    "COMPONENTS",
    "EXPOSURE_COMPONENT_COUNT",
    "FAST_AMPLITUDE_SUPPORT",
    "FAST_BASE_WEIGHTS",
    "FAST_INTERACTIONS",
    "FAST_TIME_CONSTANT_SUPPORT_HOURS",
    "HINGE_OFFSET",
    "METRICS",
    "PARTICIPANT_SENSITIVITY_LOG_SD",
    "PRIOR_HIGH_LOAD_PROBABILITY",
    "SLOW_AMPLITUDE_SUPPORT",
    "SLOW_BASE_WEIGHTS",
    "SLOW_INTERACTIONS",
    "SLOW_TIME_CONSTANT_SUPPORT_HOURS",
    "SOFTPLUS_SCALE",
    "SOFTPLUS_TEMPERATURE",
    "THRESHOLD_RANGE",
    "THRESHOLD_RESPONSE",
    "ThresholdCampEffects",
    "ThresholdResponseParameters",
    "participant_load",
    "response_parameters_for_exposure",
    "sample_threshold_camp_effects",
    "sample_threshold_response_parameters",
    "softplus_threshold_hinge",
    "threshold_response_fraction",
    "threshold_response_score",
]
