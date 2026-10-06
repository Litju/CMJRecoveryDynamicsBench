"""Typed exposure-mixture contract for correlated exposure-response dynamics."""

from dataclasses import dataclass
from enum import StrEnum
from math import isclose

from cmj_recovery_dynamics.contracts import (
    DynamicsFamily,
    DynamicsModel,
    ModelImplementationStatus,
)


class ExposureArchetype(StrEnum):
    LOW_DEMAND = "low_demand"
    HIGH_SPEED_MODERATE = "high_speed_moderate"
    HIGH_VOLUME_MODERATE = "high_volume_moderate"
    SPEED_CHANGE_NEUROMUSCULAR = "speed_change_neuromuscular"


class ExposureSample(StrEnum):
    TRAINING = "training"
    VALIDATION = "validation"
    PRIOR = "prior"


@dataclass(frozen=True, slots=True)
class ExposureMixture:
    sample: ExposureSample
    archetype_probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.archetype_probabilities) != len(ExposureArchetype):
            raise ValueError("one probability is required per exposure archetype")
        if any(not 0 <= value <= 1 for value in self.archetype_probabilities):
            raise ValueError("archetype probabilities must lie in [0, 1]")
        if not isclose(sum(self.archetype_probabilities), 1.0, abs_tol=1e-9):
            raise ValueError("archetype probabilities must sum to one")


@dataclass(frozen=True, slots=True)
class CorrelatedExposureSpecification:
    latent_factor_axes: tuple[str, ...]
    archetypes: tuple[ExposureArchetype, ...]
    mixtures: tuple[ExposureMixture, ...]

    def __post_init__(self) -> None:
        if len(self.latent_factor_axes) != 4:
            raise ValueError("the recovered correlated exposure contract has four factor axes")
        if self.archetypes != tuple(ExposureArchetype):
            raise ValueError("archetype order must match the recovered exposure contract")
        if {mixture.sample for mixture in self.mixtures} != set(ExposureSample):
            raise ValueError("training, validation, and prior mixtures are required")


CORRELATED_EXPOSURE_SPECIFICATION = CorrelatedExposureSpecification(
    latent_factor_axes=("volume", "speed", "change", "internal"),
    archetypes=tuple(ExposureArchetype),
    mixtures=(
        ExposureMixture(ExposureSample.TRAINING, (0.40, 0.30, 0.20, 0.10)),
        ExposureMixture(ExposureSample.VALIDATION, (0.10, 0.20, 0.45, 0.25)),
        ExposureMixture(ExposureSample.PRIOR, (0.25, 0.25, 0.25, 0.25)),
    ),
)

CORRELATED_EXPOSURE_RESPONSE = DynamicsModel(
    name="correlated_exposure_response",
    family=DynamicsFamily.CORRELATED_EXPOSURE_RESPONSE,
    equation_summary=(
        "The two-exponential response family is retained while exposure vectors arise "
        "from four correlated latent factors and four exposure archetypes."
    ),
    implementation_status=ModelImplementationStatus.PARAMETER_CONTRACT,
)
