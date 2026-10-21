"""Fixed mathematical modes with participant slopes and bounded discrepancy."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp, isfinite, sqrt, tanh
from typing import TYPE_CHECKING, Literal

import numpy as np

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
    LATENT_FACTOR_AXES,
    normalized_load_vector,
)
from cmj_recovery_dynamics.reproduction.single_exposure import PublicExposure

if TYPE_CHECKING:
    from cmj_recovery_dynamics.reproduction.single_exposure import KeyedRandomStreams

FAST_MODE_HOURS = 24.0
SLOW_MODE_HOURS = 84.0
AMPLITUDE_FAST_SUPPORT = (0.01, 0.08)
AMPLITUDE_SLOW_SUPPORT = (0.0, 0.08)
RESPONSE_BASIS_WEIGHTS = (
    (0.05, 0.60, 0.30, 0.05),
    (0.55, 0.05, 0.10, 0.30),
    (0.05, 0.20, 0.60, 0.15),
    (0.30, 0.05, 0.10, 0.55),
)
RESPONSE_BASIS_INTERACTIONS = (
    (1, 2, 0.25),
    (0, 3, 0.25),
    (2, 3, 0.25),
    (0, 2, 0.25),
)
PARTICIPANT_CONTEXT_MEAN_MATRIX = (
    (0.35, 0.20, 0.15, 0.05),
    (-0.10, 0.40, 0.05, 0.15),
    (0.05, 0.30, -0.10, 0.20),
    (0.25, -0.05, 0.10, 0.35),
)
PARTICIPANT_SENSITIVITY_RESIDUAL_SD = 0.45
PARTICIPANT_MODULATION_SCALE = 3.20
CAMP_AMPLITUDE_LOGIT_SD = 0.12
SHARED_DISCREPANCY_FEATURE_COUNT = 32
SHARED_DISCREPANCY_LENGTH_SCALE = 0.65
SHARED_DISCREPANCY_AMPLITUDE_FRACTION = 0.006
EPISODE_DISCREPANCY_SUPPORT = (0.0030, 0.0080)
EPISODE_DISCREPANCY_NOMINAL_FRACTION = 0.0055
DISCREPANCY_FACTOR_MODE_PROBABILITIES = (0.50, 0.20, 0.20, 0.10)
METRICS = ("force", "impulse")
COMPONENTS = ("fast", "slow")


@dataclass(frozen=True, slots=True)
class FixedModeResponseEffects:
    sensitivity: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if len(self.sensitivity) != 4 or any(
            not isfinite(value) or not -1.0 < value < 1.0 for value in self.sensitivity
        ):
            raise ValueError("four finite bounded sensitivity coordinates are required")


@dataclass(frozen=True, slots=True)
class FixedModeCampEffects:
    amplitude_logit_offsets: tuple[tuple[float, float], tuple[float, float]]


def sample_fixed_mode_response_effects(
    streams: KeyedRandomStreams,
    centered_context: tuple[float, float, float, float],
) -> FixedModeResponseEffects:
    """Draw four context-conditioned slopes with independent normal residuals."""
    context = np.asarray(centered_context, dtype=np.float64)
    matrix = np.asarray(PARTICIPANT_CONTEXT_MEAN_MATRIX, dtype=np.float64)
    if context.shape != (4,) or not np.isfinite(context).all():
        raise ValueError("participant context must contain four finite centered values")
    if np.any(context < -0.5 - 1e-12) or np.any(context > 0.5 + 1e-12):
        raise ValueError("participant centered context escaped [-0.5, 0.5]")
    residual = np.asarray(
        [
            streams.generator("participant_sensitivity_effect", axis).normal()
            for axis in LATENT_FACTOR_AXES
        ],
        dtype=np.float64,
    )
    values = np.tanh(matrix @ context + PARTICIPANT_SENSITIVITY_RESIDUAL_SD * residual)
    return FixedModeResponseEffects(tuple(float(value) for value in values))  # type: ignore[arg-type]


def sample_fixed_mode_camp_effects(streams: KeyedRandomStreams) -> FixedModeCampEffects:
    offsets = tuple(
        tuple(
            float(streams.generator("camp_amplitude_effect", metric, component).normal())
            * CAMP_AMPLITUDE_LOGIT_SD
            for component in COMPONENTS
        )
        for metric in METRICS
    )
    return FixedModeCampEffects(offsets)  # type: ignore[arg-type]


def response_axes(
    normalized_exposure_components: tuple[float, ...] | np.ndarray,
) -> tuple[float, ...]:
    values = np.asarray(normalized_exposure_components, dtype=np.float64)
    if values.shape != (7,) or not np.isfinite(values).all():
        raise ValueError("response map requires seven finite normalized public primitives")
    if np.any(values < -1e-12) or np.any(values > 1.0 + 1e-12):
        raise ValueError("response primitives escaped normalized support")
    axes = (
        (float(values[0]) + float(values[1])) / 2.0,
        (float(values[2]) + float(values[3])) / 2.0,
        (float(values[4]) + float(values[5])) / 2.0,
        float(values[6]),
    )
    return tuple(min(1.0, max(0.0, value)) for value in axes)


def _row_index(metric: str, component: str) -> int:
    if metric not in METRICS or component not in COMPONENTS:
        raise ValueError(f"unknown response channel: {metric}/{component}")
    return 2 * METRICS.index(metric) + COMPONENTS.index(component)


def fixed_mode_component_score(
    axes: tuple[float, ...],
    metric: Literal["force", "impulse"],
    component: Literal["fast", "slow"],
    participant: FixedModeResponseEffects,
) -> float:
    if len(axes) != 4 or any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in axes):
        raise ValueError("four normalized response axes are required")
    row_index = _row_index(metric, component)
    weights = RESPONSE_BASIS_WEIGHTS[row_index]
    left, right, coefficient = RESPONSE_BASIS_INTERACTIONS[row_index]
    score = sum(weight * (value - 0.5) for weight, value in zip(weights, axes, strict=True))
    score += coefficient * (axes[left] * axes[right] - 0.25)
    score += PARTICIPANT_MODULATION_SCALE * sum(
        weight * sensitivity * value
        for weight, sensitivity, value in zip(weights, participant.sensitivity, axes, strict=True)
    )
    return score


def response_component_scores(
    normalized_exposure_components: tuple[float, ...] | np.ndarray,
) -> tuple[float, float, float, float]:
    axes = response_axes(normalized_exposure_components)
    return tuple(
        sum(
            weight * (value - 0.5)
            for weight, value in zip(RESPONSE_BASIS_WEIGHTS[row], axes, strict=True)
        )
        + RESPONSE_BASIS_INTERACTIONS[row][2]
        * (
            axes[RESPONSE_BASIS_INTERACTIONS[row][0]] * axes[RESPONSE_BASIS_INTERACTIONS[row][1]]
            - 0.25
        )
        for row in range(4)
    )  # type: ignore[return-value]


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + exp(-value))
    exponential = exp(value)
    return exponential / (1.0 + exponential)


def response_parameters_for_exposure(
    exposure: PublicExposure,
    participant: FixedModeResponseEffects,
    camp: FixedModeCampEffects,
    metric: Literal["force", "impulse"],
) -> tuple[float, float, float, float]:
    if metric not in METRICS:
        raise ValueError(f"unknown response metric: {metric}")
    metric_index = METRICS.index(metric)
    axes = response_axes(normalized_load_vector(exposure))
    amplitudes: list[float] = []
    for index, component in enumerate(COMPONENTS):
        score = fixed_mode_component_score(axes, metric, component, participant)
        score += camp.amplitude_logit_offsets[metric_index][index]
        low, high = (AMPLITUDE_FAST_SUPPORT, AMPLITUDE_SLOW_SUPPORT)[index]
        amplitudes.append(low + (high - low) * _sigmoid(score))
    return amplitudes[0], FAST_MODE_HOURS, amplitudes[1], SLOW_MODE_HOURS


def fixed_mode_response(lag_hours: float, fast_amplitude: float, slow_amplitude: float) -> float:
    """Return the negative fixed 24 h and 84 h mathematical response modes."""
    if any(not isfinite(value) for value in (lag_hours, fast_amplitude, slow_amplitude)):
        raise ValueError("lag and amplitudes must be finite")
    if lag_hours < 0.0 or fast_amplitude < 0.0 or slow_amplitude < 0.0:
        raise ValueError("lag and mode amplitudes must be non-negative")
    return -fast_amplitude * exp(-lag_hours / FAST_MODE_HOURS) - slow_amplitude * exp(
        -lag_hours / SLOW_MODE_HOURS
    )


def nominal_response_fraction(
    exposure: PublicExposure,
    lag_hours: float,
    participant: FixedModeResponseEffects,
    camp: FixedModeCampEffects,
    metric: Literal["force", "impulse"],
) -> float:
    if not isfinite(lag_hours) or lag_hours < 0.0:
        raise ValueError("lag must be finite and non-negative")
    fast_amp, _fast_tau, slow_amp, _slow_tau = response_parameters_for_exposure(
        exposure, participant, camp, metric
    )
    return fixed_mode_response(lag_hours, fast_amp, slow_amp)


@lru_cache(maxsize=8)
def _rff_parameters(
    metric: str,
    component: str,
    feature_count: int = SHARED_DISCREPANCY_FEATURE_COUNT,
    length_scale: float = SHARED_DISCREPANCY_LENGTH_SCALE,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if feature_count <= 0 or not isfinite(length_scale) or length_scale <= 0.0:
        raise ValueError("discrepancy feature count and length scale must be positive")
    from cmj_recovery_dynamics.reproduction.single_exposure import KeyedRandomStreams

    # The source's private realization seed stays outside the public generator.
    streams = KeyedRandomStreams("fixed_mode_shared_discrepancy")
    channel = f"{metric}_{component}"
    frequencies = streams.generator("world_discrepancy_frequency", channel).normal(
        0.0, 1.0 / length_scale, size=(feature_count, 8)
    )
    phases = streams.generator("world_discrepancy_phase", channel).uniform(
        0.0, 2.0 * np.pi, size=feature_count
    )
    coefficients = streams.generator("world_discrepancy_coefficient", channel).normal(
        size=feature_count
    )
    return frequencies, phases, coefficients


def shared_discrepancy_component(
    exposure: PublicExposure,
    normalized_context: tuple[float, float, float, float],
    metric: Literal["force", "impulse"],
    component: Literal["fast", "slow"],
) -> float:
    if metric not in METRICS or component not in COMPONENTS:
        raise ValueError(f"unknown discrepancy channel: {metric}/{component}")
    context = np.asarray(normalized_context, dtype=np.float64)
    if context.shape != (4,) or not np.isfinite(context).all():
        raise ValueError("shared discrepancy context must contain four finite values")
    if np.any(context < -1e-12) or np.any(context > 1.0 + 1e-12):
        raise ValueError("shared discrepancy context escaped [0, 1]")
    query = np.concatenate(
        (np.asarray(response_axes(normalized_load_vector(exposure))), np.clip(context, 0.0, 1.0))
    )
    frequencies, phases, coefficients = _rff_parameters(metric, component)
    features = sqrt(2.0 / SHARED_DISCREPANCY_FEATURE_COUNT) * np.cos(frequencies @ query + phases)
    raw = float(features @ coefficients)
    value = SHARED_DISCREPANCY_AMPLITUDE_FRACTION * tanh(raw)
    if abs(value) > SHARED_DISCREPANCY_AMPLITUDE_FRACTION + 1e-15:
        raise RuntimeError("shared discrepancy escaped its frozen bound")
    return value


def shared_discrepancy_fraction(
    exposure: PublicExposure,
    normalized_context: tuple[float, float, float, float],
    lag_hours: float,
    metric: Literal["force", "impulse"],
) -> float:
    if not isfinite(lag_hours) or lag_hours < 0.0:
        raise ValueError("lag must be finite and non-negative")
    fast = shared_discrepancy_component(exposure, normalized_context, metric, "fast")
    slow = shared_discrepancy_component(exposure, normalized_context, metric, "slow")
    return fast * exp(-lag_hours / FAST_MODE_HOURS) + slow * exp(-lag_hours / SLOW_MODE_HOURS)


def fixed_mode_response_fraction(
    exposure: PublicExposure,
    lag_hours: float,
    participant: FixedModeResponseEffects,
    camp: FixedModeCampEffects,
    metric: Literal["force", "impulse"],
    normalized_context: tuple[float, float, float, float] | None = None,
) -> float:
    nominal = nominal_response_fraction(exposure, lag_hours, participant, camp, metric)
    if normalized_context is None:
        return nominal
    return nominal + shared_discrepancy_fraction(exposure, normalized_context, lag_hours, metric)


FIXED_MODE_DISCREPANCY_RESPONSE = DynamicsModel(
    name="fixed_mode_discrepancy_response",
    family=DynamicsFamily.FIXED_MODE_DISCREPANCY_RESPONSE,
    equation_summary=(
        "Four context-conditioned participant sensitivities map through a full-rank four-row "
        "basis to fixed 24 h and 84 h response modes, with bounded smooth shared discrepancy."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)

__all__ = [
    "AMPLITUDE_FAST_SUPPORT",
    "AMPLITUDE_SLOW_SUPPORT",
    "CAMP_AMPLITUDE_LOGIT_SD",
    "DISCREPANCY_FACTOR_MODE_PROBABILITIES",
    "EPISODE_DISCREPANCY_NOMINAL_FRACTION",
    "EPISODE_DISCREPANCY_SUPPORT",
    "FAST_MODE_HOURS",
    "FIXED_MODE_DISCREPANCY_RESPONSE",
    "FixedModeCampEffects",
    "FixedModeResponseEffects",
    "METRICS",
    "PARTICIPANT_CONTEXT_MEAN_MATRIX",
    "PARTICIPANT_MODULATION_SCALE",
    "PARTICIPANT_SENSITIVITY_RESIDUAL_SD",
    "RESPONSE_BASIS_INTERACTIONS",
    "RESPONSE_BASIS_WEIGHTS",
    "SHARED_DISCREPANCY_AMPLITUDE_FRACTION",
    "SHARED_DISCREPANCY_FEATURE_COUNT",
    "SHARED_DISCREPANCY_LENGTH_SCALE",
    "SLOW_MODE_HOURS",
    "fixed_mode_component_score",
    "fixed_mode_response",
    "fixed_mode_response_fraction",
    "nominal_response_fraction",
    "response_axes",
    "response_component_scores",
    "response_parameters_for_exposure",
    "sample_fixed_mode_camp_effects",
    "sample_fixed_mode_response_effects",
    "shared_discrepancy_component",
    "shared_discrepancy_fraction",
]
