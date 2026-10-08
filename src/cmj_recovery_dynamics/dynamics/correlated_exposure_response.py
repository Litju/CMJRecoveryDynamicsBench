"""Base and correlated exposure generators."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import erfc, isclose, isfinite, sqrt

import numpy as np

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)
from cmj_recovery_dynamics.reproduction.single_exposure import (
    EXPOSURE_SUPPORTS,
    KeyedRandomStreams,
    PublicExposure,
)

LOAD_DIMENSIONS = tuple(name for name, _bounds in EXPOSURE_SUPPORTS)
LATENT_FACTOR_AXES = ("volume", "speed", "change", "internal")
EXPOSURE_THRESHOLD_SEMANTICS = (
    ("high_speed_distance_m", ">5.5 m/s"),
    ("sprint_distance_m", ">=7.0 m/s"),
    ("high_intensity_accel_count", ">=+2.0 m/s²"),
    ("high_intensity_decel_count", "<=-2.0 m/s²"),
)


class ExposureArchetype(StrEnum):
    LOW_DEMAND = "low_demand"
    HIGH_SPEED_MODERATE = "high_speed_moderate"
    HIGH_VOLUME_MODERATE = "high_volume_moderate"
    SPEED_CHANGE_NEUROMUSCULAR = "speed_change_neuromuscular"


CORRELATED_SOURCE_ARCHETYPE_NAMES = (
    "LOW_DEMAND",
    "HIGH_SPEED_MODERATE",
    "MATCH_HIGH_DEMAND",
    "SPEED_CHANGE_NEUROMUSCULAR",
)


class ExposureSample(StrEnum):
    TRAINING = "training"
    VALIDATION = "validation"
    PRIOR = "prior"


@dataclass(frozen=True, slots=True)
class ExposureMixture:
    sample: ExposureSample
    archetype_probabilities: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        values = self.archetype_probabilities
        if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("archetype probabilities must be finite and lie in [0, 1]")
        if not isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValueError("archetype probabilities must sum to one")


@dataclass(frozen=True, slots=True)
class CorrelatedExposureSpecification:
    latent_factor_axes: tuple[str, ...]
    archetypes: tuple[ExposureArchetype, ...]
    mixtures: tuple[ExposureMixture, ...]
    source_archetype_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.latent_factor_axes != LATENT_FACTOR_AXES:
            raise ValueError("correlated exposure requires the four source-defined factor axes")
        if self.archetypes != tuple(ExposureArchetype):
            raise ValueError("correlated archetypes must retain their source-defined order")
        if self.source_archetype_names != CORRELATED_SOURCE_ARCHETYPE_NAMES:
            raise ValueError("correlated source archetype labels must be preserved")
        if {mixture.sample for mixture in self.mixtures} != set(ExposureSample):
            raise ValueError("correlated exposure requires train, validation, and prior mixtures")


@dataclass(frozen=True, slots=True)
class BaseExposureParameters:
    high_speed_threshold_m_s: float = 5.5
    sprint_threshold_m_s: float = 7.0
    acceleration_threshold_m_s2: float = 2.0
    deceleration_threshold_m_s2: float = -2.0
    high_load_threshold: float = 0.5
    load_index_weights: tuple[float, ...] = (1.0 / 7.0,) * 7
    low_intensity: tuple[float, float] = (0.0, 0.35)
    high_intensity: tuple[float, float] = (0.65, 1.0)
    feature_variation: tuple[float, float] = (-0.15, 0.15)
    train_high_load_probability: float = 0.30
    validation_high_load_probability: float = 0.70
    prior_high_load_probability: float = 0.50


@dataclass(frozen=True, slots=True)
class CorrelatedExposureParameters:
    factor_sd: float = 0.60
    factor_correlation: tuple[tuple[float, ...], ...] = (
        (1.00, 0.20, 0.15, 0.30),
        (0.20, 1.00, 0.15, 0.25),
        (0.15, 0.15, 1.00, 0.25),
        (0.30, 0.25, 0.25, 1.00),
    )
    factor_cholesky: tuple[tuple[float, ...], ...] = (
        (1.0, 0.0, 0.0, 0.0),
        (0.2, 0.9797958971132712, 0.0, 0.0),
        (0.15, 0.12247448713915891, 0.9810708435174292, 0.0),
        (0.3, 0.19391793797033494, 0.18474710689613924, 0.9155677691066019),
    )
    archetype_means: tuple[tuple[float, ...], ...] = (
        (-1.00, -1.00, -1.00, -0.80),
        (-0.30, 1.20, -0.40, 0.20),
        (0.90, 0.80, 0.60, 0.80),
        (-0.30, -0.20, 1.20, 0.40),
    )
    train_probabilities: tuple[float, float, float, float] = (0.40, 0.30, 0.20, 0.10)
    validation_probabilities: tuple[float, float, float, float] = (0.10, 0.20, 0.45, 0.25)
    prior_probabilities: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)
    feature_loadings: tuple[tuple[float, ...], ...] = (
        (0.90, 0.10, 0.05, 0.05),
        (0.80, 0.30, 0.05, 0.05),
        (0.05, 0.95, 0.05, 0.05),
        (0.02, 0.98, 0.02, 0.02),
        (0.15, 0.05, 0.95, 0.05),
        (0.20, 0.05, 0.90, 0.05),
        (0.20, 0.15, 0.20, 0.85),
    )
    feature_residual_sds: tuple[float, ...] = (0.50, 0.45, 0.50, 0.55, 0.50, 0.50, 0.55)

    @property
    def factor_covariance(self) -> tuple[tuple[float, ...], ...]:
        return tuple(
            tuple(self.factor_sd**2 * value for value in row) for row in self.factor_correlation
        )


BASE_EXPOSURE_PARAMETERS = BaseExposureParameters()
CORRELATED_EXPOSURE_PARAMETERS = CorrelatedExposureParameters()
CORRELATED_EXPOSURE_SPECIFICATION = CorrelatedExposureSpecification(
    LATENT_FACTOR_AXES,
    tuple(ExposureArchetype),
    (
        ExposureMixture(
            ExposureSample.TRAINING, CORRELATED_EXPOSURE_PARAMETERS.train_probabilities
        ),
        ExposureMixture(
            ExposureSample.VALIDATION, CORRELATED_EXPOSURE_PARAMETERS.validation_probabilities
        ),
        ExposureMixture(ExposureSample.PRIOR, CORRELATED_EXPOSURE_PARAMETERS.prior_probabilities),
    ),
    CORRELATED_SOURCE_ARCHETYPE_NAMES,
)


def normalized_load_vector(
    exposure: PublicExposure | Mapping[str, float],
) -> tuple[float, ...]:
    values = exposure.as_dict() if isinstance(exposure, PublicExposure) else exposure
    vector = tuple(
        (float(values[name]) - low) / (high - low) for name, (low, high) in EXPOSURE_SUPPORTS
    )
    if not all(isfinite(value) for value in vector):
        raise ValueError("exposure load vector must be finite")
    if any(value < -1e-12 or value > 1.0 + 1e-12 for value in vector):
        raise ValueError("exposure load vector is outside its frozen supports")
    return tuple(min(1.0, max(0.0, value)) for value in vector)


def _exposure_from_unit_vector(
    vector: Mapping[str, float], archetype_index: int | None = None
) -> PublicExposure:
    bounds = dict(EXPOSURE_SUPPORTS)
    values = {name: low + vector[name] * (high - low) for name, (low, high) in bounds.items()}
    duration = float(values["duration_min"])
    rpe = float(2.0 + vector["session_rpe_cr10"] * 8.0)
    high_speed = float(values["high_speed_distance_m"])
    sprint = min(600.0 * vector["sprint_distance_m"], high_speed)
    accel = int(round(150.0 * vector["high_intensity_accel_count"]))
    decel = int(round(150.0 * vector["high_intensity_decel_count"]))
    return PublicExposure(
        duration_min=duration,
        total_distance_m=float(values["total_distance_m"]),
        high_speed_distance_m=high_speed,
        sprint_distance_m=float(sprint),
        high_intensity_accel_count=accel,
        high_intensity_decel_count=decel,
        session_rpe_cr10=rpe,
        session_rpe_load_au=duration * rpe,
        archetype_index=archetype_index,
    )


def sample_preliminary_exposure(
    streams: KeyedRandomStreams,
    *,
    high_load_probability: float,
    channel: str = "current_exposure",
    episode_key: str = "current",
    params: BaseExposureParameters = BASE_EXPOSURE_PARAMETERS,
) -> PublicExposure:
    """Sample the seven exposure primitives from the base scalar mixture."""
    if channel not in {"current_exposure", "prior_episode_exposure"}:
        raise ValueError(f"unsupported exposure RNG channel: {channel}")
    if not isfinite(high_load_probability) or not 0.0 <= high_load_probability <= 1.0:
        raise ValueError("high-load probability must be finite and lie in [0, 1]")
    selector_channel = "current_load_class" if channel == "current_exposure" else channel
    high = (
        streams.generator(selector_channel, episode_key, "high_load_assignment").random()
        < high_load_probability
    )
    low, high_bound = params.high_intensity if high else params.low_intensity
    intensity = float(
        streams.generator(channel, episode_key, "shared_latent_intensity").uniform(low, high_bound)
    )
    unit_values: dict[str, float] = {}
    for name, _bounds in EXPOSURE_SUPPORTS:
        delta = streams.generator(channel, f"{episode_key}:{name}", "specific_variation").uniform(
            *params.feature_variation
        )
        unit_values[name] = min(1.0, max(0.0, intensity + float(delta)))
    return _exposure_from_unit_vector(unit_values)


def is_high_load(
    exposure: PublicExposure,
    params: BaseExposureParameters = BASE_EXPOSURE_PARAMETERS,
) -> bool:
    vector = normalized_load_vector(exposure)
    if not isclose(sum(params.load_index_weights), 1.0, abs_tol=1e-12):
        raise ValueError("base load-index weights must sum to one")
    score = sum(a * b for a, b in zip(vector, params.load_index_weights, strict=True))
    return score >= params.high_load_threshold


def mixture_for(split: str, *, prior: bool = False) -> tuple[float, ...]:
    if prior:
        return CORRELATED_EXPOSURE_PARAMETERS.prior_probabilities
    if split == "train":
        return CORRELATED_EXPOSURE_PARAMETERS.train_probabilities
    if split == "validation":
        return CORRELATED_EXPOSURE_PARAMETERS.validation_probabilities
    raise ValueError("public split must be train or validation")


def sample_correlated_exposure(
    streams: KeyedRandomStreams,
    *,
    archetype_probabilities: tuple[float, ...],
    channel: str = "current_exposure",
    episode_key: str = "current",
    params: CorrelatedExposureParameters = CORRELATED_EXPOSURE_PARAMETERS,
) -> PublicExposure:
    """Sample correlated factors, archetype noise, and the seven public primitives."""
    if channel not in {"current_exposure", "prior_episode_exposure"}:
        raise ValueError(f"unsupported exposure RNG channel: {channel}")
    probabilities = np.asarray(archetype_probabilities, dtype=np.float64)
    if (
        probabilities.shape != (4,)
        or not np.isfinite(probabilities).all()
        or np.any(probabilities < 0.0)
        or not np.isclose(probabilities.sum(), 1.0)
    ):
        raise ValueError("archetype probabilities must be four finite values summing to one")
    archetype_index = int(
        streams.generator("exposure_archetype_assignment", channel, episode_key).choice(
            4, p=probabilities
        )
    )
    factor_residual = streams.generator("exposure_factor_residual", channel, episode_key).normal(
        size=4
    )
    correlation = np.asarray(params.factor_correlation, dtype=np.float64)
    loadings = np.asarray(params.feature_loadings, dtype=np.float64)
    factor = np.asarray(params.archetype_means[archetype_index]) + params.factor_sd * (
        np.asarray(params.factor_cholesky, dtype=np.float64) @ factor_residual
    )
    variances = np.sqrt(
        params.factor_sd**2 * np.einsum("ij,jk,ik->i", loadings, correlation, loadings)
        + np.square(params.feature_residual_sds)
    )
    unit_values: dict[str, float] = {}
    for index, name in enumerate(LOAD_DIMENSIONS):
        raw = float(loadings[index] @ factor) + params.feature_residual_sds[index] * float(
            streams.generator("exposure_feature_residual", channel, episode_key, name).normal()
        )
        unit_values[name] = 0.5 * erfc(-raw / (float(variances[index]) * sqrt(2.0)))
    return _exposure_from_unit_vector(unit_values, archetype_index)


CORRELATED_EXPOSURE_RESPONSE = DynamicsModel(
    name="correlated_exposure_response",
    family=DynamicsFamily.CORRELATED_EXPOSURE_RESPONSE,
    equation_summary=(
        "The correlated exposure formulation samples seven public primitives from "
        "four latent factors, "
        "four ordered archetypes, and split-specific mixtures; the response remains the "
        "participant-conditioned two-exponential family."
    ),
    implementation_status=ModelImplementationStatus.COMPLETE_EQUATION,
)

__all__ = [
    "CORRELATED_EXPOSURE_RESPONSE",
    "CORRELATED_EXPOSURE_SPECIFICATION",
    "CorrelatedExposureSpecification",
    "ExposureArchetype",
    "ExposureMixture",
    "ExposureSample",
    "EXPOSURE_THRESHOLD_SEMANTICS",
    "LATENT_FACTOR_AXES",
    "LOAD_DIMENSIONS",
    "BASE_EXPOSURE_PARAMETERS",
    "BaseExposureParameters",
    "CORRELATED_EXPOSURE_PARAMETERS",
    "CORRELATED_SOURCE_ARCHETYPE_NAMES",
    "CorrelatedExposureParameters",
    "is_high_load",
    "mixture_for",
    "normalized_load_vector",
    "sample_correlated_exposure",
    "sample_preliminary_exposure",
]
