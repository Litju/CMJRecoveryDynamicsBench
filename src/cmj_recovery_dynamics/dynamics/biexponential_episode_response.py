"""Participant-conditioned biexponential response formulations."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isclose, isfinite
from typing import Literal

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import normalized_load_vector
from cmj_recovery_dynamics.reproduction.single_exposure import (
    KeyedRandomStreams,
    PublicExposure,
)

Metric = Literal["force", "impulse"]
Component = Literal["fast", "slow"]
METRICS: tuple[Metric, Metric] = ("force", "impulse")
COMPONENTS: tuple[Component, Component] = ("fast", "slow")

FAST_AMPLITUDE_SUPPORT = (0.01, 0.08)
SLOW_AMPLITUDE_SUPPORT = (0.0, 0.08)
FAST_TAU_SUPPORT_HOURS = (12.0, 36.0)
SLOW_TAU_SUPPORT_HOURS = (48.0, 120.0)

BASE_FAST_LINEAR_WEIGHTS = (0.14, 0.14, 0.16, 0.16, 0.14, 0.12, 0.14)
BASE_FAST_INTERACTIONS = ((2, 3, 0.60), (4, 5, 0.35), (0, 6, 0.20))
BASE_SLOW_LINEAR_WEIGHTS = (0.18, 0.18, 0.13, 0.10, 0.12, 0.12, 0.17)
BASE_SLOW_INTERACTIONS = ((0, 1, 0.45), (6, 4, 0.25), (2, 5, 0.20))

# Correlated exposure keeps the same response equation but uses this source-frozen
# map from four summaries of the seven public exposure primitives to each mode.
CORRELATED_RESPONSE_BASIS_WEIGHTS = (
    (0.02, 0.68, 0.28, 0.02),
    (0.18, 0.03, 0.69, 0.10),
    (0.02, 0.63, 0.03, 0.32),
    (0.55, 0.03, 0.03, 0.39),
)
CORRELATED_RESPONSE_BASIS_INTERACTIONS = (
    (1, 2, 0.30),
    (0, 2, 0.25),
    (1, 3, 0.25),
    (0, 3, 0.30),
)

PARTICIPANT_AMPLITUDE_LOGIT_SD = 0.60
PARTICIPANT_SLOW_AMPLITUDE_SD_MULTIPLIER = 0.90
CAMP_AMPLITUDE_LOGIT_SD = 0.12
PARTICIPANT_TAU_LOGIT_SD = 0.80


@dataclass(frozen=True, slots=True)
class BiexponentialEpisodeParameters:
    fast_amplitude: float
    slow_amplitude: float
    fast_time_constant_hours: float
    slow_time_constant_hours: float

    def __post_init__(self) -> None:
        values = (
            self.fast_amplitude,
            self.slow_amplitude,
            self.fast_time_constant_hours,
            self.slow_time_constant_hours,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("episode-response parameters must be finite")
        if self.fast_amplitude < 0.0 or self.slow_amplitude < 0.0:
            raise ValueError("episode-response amplitudes must be non-negative")
        if self.fast_time_constant_hours <= 0.0 or self.slow_time_constant_hours <= 0.0:
            raise ValueError("episode-response time constants must be positive")


@dataclass(frozen=True, slots=True)
class ResponseEffects:
    amplitude_logits: tuple[tuple[float, float], tuple[float, float]]
    tau_logits: tuple[tuple[float, float], tuple[float, float]]


@dataclass(frozen=True, slots=True)
class CampEffects:
    amplitude_logit_offsets: tuple[tuple[float, float], tuple[float, float]]


@dataclass(frozen=True, slots=True)
class ParticipantContext:
    training_age_years: float
    strength_index: float
    baseline_force_n_per_kg: float
    baseline_impulse_m_per_s: float
    response_effects: ResponseEffects


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + exp(-value))
    e = exp(value)
    return e / (1.0 + e)


def sample_participant_effects(streams: KeyedRandomStreams) -> ResponseEffects:
    amplitude_logits: list[tuple[float, float]] = []
    tau_logits: list[tuple[float, float]] = []
    for metric in METRICS:
        fast_amp = float(streams.generator("participant_amplitude_effect", metric, "fast").normal())
        slow_amp = float(streams.generator("participant_amplitude_effect", metric, "slow").normal())
        amplitude_logits.append(
            (
                fast_amp * PARTICIPANT_AMPLITUDE_LOGIT_SD,
                slow_amp
                * PARTICIPANT_AMPLITUDE_LOGIT_SD
                * PARTICIPANT_SLOW_AMPLITUDE_SD_MULTIPLIER,
            )
        )
        fast_tau = float(
            streams.generator("participant_time_constant_effect", metric, "fast").normal()
        )
        slow_tau = float(
            streams.generator("participant_time_constant_effect", metric, "slow").normal()
        )
        tau_logits.append(
            (fast_tau * PARTICIPANT_TAU_LOGIT_SD, slow_tau * PARTICIPANT_TAU_LOGIT_SD)
        )
    return ResponseEffects(tuple(amplitude_logits), tuple(tau_logits))  # type: ignore[arg-type]


def sample_camp_effects(streams: KeyedRandomStreams) -> CampEffects:
    offsets = tuple(
        tuple(
            float(streams.generator("camp_amplitude_effect", metric, component).normal())
            * CAMP_AMPLITUDE_LOGIT_SD
            for component in COMPONENTS
        )
        for metric in METRICS
    )
    return CampEffects(offsets)  # type: ignore[arg-type]


def sample_participant_context(streams: KeyedRandomStreams) -> ParticipantContext:
    """Sample the source-defined covariates and stable baseline references.

    Strength affects baseline force and impulse through the recovered affine
    mappings. Training age is observed context and has no direct response-law
    coefficient in the selected source.
    """
    age = float(streams.generator("participant_training_age", "context").uniform(0.5, 18.0))
    strength = float(streams.generator("participant_strength_index", "context").uniform(-1.0, 1.0))
    strength_fraction = (strength + 1.0) / 2.0
    force_noise = float(streams.generator("participant_baseline_force", "context").uniform())
    impulse_noise = float(streams.generator("participant_baseline_impulse", "context").uniform())
    baseline_force = 18.0 + 12.0 * (0.75 * strength_fraction + 0.25 * force_noise)
    baseline_impulse = 2.0 + 2.0 * (0.40 * strength_fraction + 0.60 * impulse_noise)
    return ParticipantContext(
        age,
        strength,
        baseline_force,
        baseline_impulse,
        sample_participant_effects(streams),
    )


def _base_load_score(vector: tuple[float, ...], component: Component) -> float:
    if component == "fast":
        weights, interactions = BASE_FAST_LINEAR_WEIGHTS, BASE_FAST_INTERACTIONS
    else:
        weights, interactions = BASE_SLOW_LINEAR_WEIGHTS, BASE_SLOW_INTERACTIONS
    if len(vector) != 7 or not all(isfinite(value) for value in vector):
        raise ValueError("base response map requires seven finite normalized primitives")
    if not isclose(sum(weights), 1.0, abs_tol=1e-12):
        raise ValueError("base response weights must sum to one")
    score = sum(value * weight for value, weight in zip(vector, weights, strict=True)) - 0.5
    return score + sum(
        coefficient * (vector[left] * vector[right] - 0.25)
        for left, right, coefficient in interactions
    )


def _correlated_load_score(
    vector: tuple[float, ...], component: Component, metric: Metric
) -> float:
    if len(vector) != 7 or not all(isfinite(value) for value in vector):
        raise ValueError("correlated response map requires seven finite normalized primitives")
    basis = (
        (vector[0] + vector[1]) / 2.0,
        (vector[2] + vector[3]) / 2.0,
        (vector[4] + vector[5]) / 2.0,
        vector[6],
    )
    component_index = COMPONENTS.index(component)
    row_index = 2 * METRICS.index(metric) + component_index
    weights = CORRELATED_RESPONSE_BASIS_WEIGHTS[row_index]
    left, right, coefficient = CORRELATED_RESPONSE_BASIS_INTERACTIONS[row_index]
    if not isclose(sum(weights), 1.0, abs_tol=1e-12):
        raise ValueError("correlated response basis weights must sum to one")
    return sum(weight * (value - 0.5) for weight, value in zip(weights, basis, strict=True)) + (
        coefficient * (basis[left] * basis[right] - 0.25)
    )


def response_parameters_for_exposure(
    exposure: PublicExposure,
    participant: ResponseEffects,
    camp: CampEffects,
    metric: Metric,
    *,
    world: Literal["base_biexponential", "correlated_exposure"] = "base_biexponential",
) -> BiexponentialEpisodeParameters:
    if metric not in METRICS:
        raise ValueError(f"unknown response metric: {metric}")
    if world not in {"base_biexponential", "correlated_exposure"}:
        raise ValueError(f"unknown response map world: {world}")
    metric_index = METRICS.index(metric)
    vector = normalized_load_vector(exposure)
    amplitudes: list[float] = []
    taus: list[float] = []
    amplitude_supports = (FAST_AMPLITUDE_SUPPORT, SLOW_AMPLITUDE_SUPPORT)
    tau_supports = (FAST_TAU_SUPPORT_HOURS, SLOW_TAU_SUPPORT_HOURS)
    for component_index, component in enumerate(COMPONENTS):
        low, high = amplitude_supports[component_index]
        if world == "base_biexponential":
            amplitude_score = _base_load_score(vector, component)
        else:
            amplitude_score = _correlated_load_score(vector, component, metric)
        amplitude_score += participant.amplitude_logits[metric_index][component_index]
        amplitude_score += camp.amplitude_logit_offsets[metric_index][component_index]
        amplitudes.append(low + (high - low) * _sigmoid(amplitude_score))
        tau_low, tau_high = tau_supports[component_index]
        tau_score = participant.tau_logits[metric_index][component_index]
        taus.append(tau_low + (tau_high - tau_low) * _sigmoid(tau_score))
    parameters = BiexponentialEpisodeParameters(amplitudes[0], amplitudes[1], taus[0], taus[1])
    source_supports = (
        FAST_AMPLITUDE_SUPPORT,
        SLOW_AMPLITUDE_SUPPORT,
        FAST_TAU_SUPPORT_HOURS,
        SLOW_TAU_SUPPORT_HOURS,
    )
    values = (
        parameters.fast_amplitude,
        parameters.slow_amplitude,
        parameters.fast_time_constant_hours,
        parameters.slow_time_constant_hours,
    )
    if any(
        not low <= value <= high for value, (low, high) in zip(values, source_supports, strict=True)
    ):
        raise ValueError("single-exposure parameters escaped their frozen supports")
    return parameters


def episode_response(lag_hours: float, parameters: BiexponentialEpisodeParameters) -> float:
    """Return ``-A_fast exp(-t/tau_fast) - A_slow exp(-t/tau_slow)``."""
    if not isfinite(lag_hours) or lag_hours < 0.0:
        raise ValueError("lag must be finite and non-negative")
    return -parameters.fast_amplitude * exp(
        -lag_hours / parameters.fast_time_constant_hours
    ) - parameters.slow_amplitude * exp(-lag_hours / parameters.slow_time_constant_hours)


def response_fraction(
    exposure: PublicExposure,
    lag_hours: float,
    participant: ResponseEffects,
    camp: CampEffects,
    metric: Metric,
    *,
    world: Literal["base_biexponential", "correlated_exposure"] = "base_biexponential",
) -> float:
    return episode_response(
        lag_hours,
        response_parameters_for_exposure(exposure, participant, camp, metric, world=world),
    )


def frozen_scaffold_fraction(
    lag_hours: float,
    fast_amplitude: float,
    slow_amplitude: float,
    fast_tau_hours: float,
    slow_tau_hours: float,
) -> float:
    return episode_response(
        lag_hours,
        BiexponentialEpisodeParameters(
            fast_amplitude, slow_amplitude, fast_tau_hours, slow_tau_hours
        ),
    )


BIEXPONENTIAL_EPISODE_RESPONSE = DynamicsModel(
    name="biexponential_episode_response",
    family=DynamicsFamily.BIEXPONENTIAL_EPISODE_RESPONSE,
    equation_summary=(
        "Each exposure contributes a bounded fast and slow negative exponential. The base "
        "formulation uses its seven-primitive logistic map; correlated exposure keeps the "
        "equation and uses its source-defined four-basis outcome-specific map."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)

__all__ = [
    "BIEXPONENTIAL_EPISODE_RESPONSE",
    "CAMP_AMPLITUDE_LOGIT_SD",
    "CampEffects",
    "FAST_AMPLITUDE_SUPPORT",
    "FAST_TAU_SUPPORT_HOURS",
    "ParticipantContext",
    "PARTICIPANT_AMPLITUDE_LOGIT_SD",
    "PARTICIPANT_SLOW_AMPLITUDE_SD_MULTIPLIER",
    "PARTICIPANT_TAU_LOGIT_SD",
    "ResponseEffects",
    "SLOW_AMPLITUDE_SUPPORT",
    "SLOW_TAU_SUPPORT_HOURS",
    "BASE_FAST_INTERACTIONS",
    "BASE_FAST_LINEAR_WEIGHTS",
    "BASE_SLOW_INTERACTIONS",
    "BASE_SLOW_LINEAR_WEIGHTS",
    "CORRELATED_RESPONSE_BASIS_INTERACTIONS",
    "CORRELATED_RESPONSE_BASIS_WEIGHTS",
    "episode_response",
    "frozen_scaffold_fraction",
    "response_fraction",
    "response_parameters_for_exposure",
    "sample_camp_effects",
    "sample_participant_context",
    "sample_participant_effects",
]
