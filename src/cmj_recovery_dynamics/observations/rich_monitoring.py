"""O02 rich monitoring and target-measurement process."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.contracts import (
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)

Array = NDArray[Any]


class AssessmentValidity(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    MISSING_VALUES = "missing_values"


MISSING_VALUE = "<MISSING>"
TARGET_TRIAL_COUNT = 5


@dataclass(frozen=True, slots=True)
class MeasurementModel:
    trial_sd_force: float = 0.45
    trial_sd_impulse: float = 0.040
    target_trials: int = TARGET_TRIAL_COUNT
    depth_history_jitter_m: float = 0.02
    depth_target_jitter_m: float = 0.006
    depth_grid_m: float = 0.005
    depth_clip_m: tuple[float, float] = (0.15, 0.45)
    invalid_rate: float = 0.05
    invalid_scale_range: tuple[float, float] = (0.75, 0.92)
    missing_rate: float = 0.04

    def __post_init__(self) -> None:
        if self.target_trials != TARGET_TRIAL_COUNT:
            raise ValueError("the target protocol requires exactly five valid trials")
        if min(self.trial_sd_force, self.trial_sd_impulse, self.depth_grid_m) <= 0:
            raise ValueError("measurement scales must be positive")
        if not 0 <= self.invalid_rate <= 1 or not 0 <= self.missing_rate <= 1:
            raise ValueError("measurement validity rates must be probabilities")
        if not 0 < self.invalid_scale_range[0] <= self.invalid_scale_range[1] <= 1:
            raise ValueError("invalid-assessment scaling must lie in (0, 1]")
        if not 0 < self.depth_clip_m[0] < self.depth_clip_m[1]:
            raise ValueError("depth clipping bounds must be increasing and positive")


@dataclass(frozen=True, slots=True)
class MonitoringAssessment:
    time_from_origin_hours: float
    force: float | None
    impulse: float | None
    depth_m: float
    trial_count: int
    validity_state: AssessmentValidity


@dataclass(frozen=True, slots=True)
class ProtocolBaseline:
    force: float
    impulse: float


@dataclass(frozen=True, slots=True)
class AssessmentMeasurements:
    force: Array
    impulse: Array
    depth: Array
    validity: Array
    usable: Array
    force_raw: Array
    impulse_raw: Array


@dataclass(frozen=True, slots=True)
class TargetMeasurements:
    force: Array
    impulse: Array
    depth_context: Array


def protocol_baseline(
    assessments: tuple[MonitoringAssessment, ...],
    exposure_times_hours: tuple[float, ...],
    *,
    window_hours: tuple[float, float] = (-240.0, -24.0),
    recovered_gap_hours: float = 60.0,
) -> ProtocolBaseline | None:
    """Mean the two latest valid assessments >=60 h after the preceding exposure."""
    if recovered_gap_hours < 0 or window_hours[0] > window_hours[1]:
        raise ValueError("baseline window and recovered gap must be valid")
    qualifying: list[MonitoringAssessment] = []
    for assessment in assessments:
        time = assessment.time_from_origin_hours
        if not isfinite(time) or not window_hours[0] <= time <= window_hours[1]:
            continue
        if assessment.validity_state is not AssessmentValidity.VALID:
            continue
        if assessment.force is None or assessment.impulse is None:
            continue
        if not isfinite(assessment.force) or not isfinite(assessment.impulse):
            continue
        previous = max(
            (event_time for event_time in exposure_times_hours if event_time < time),
            default=float("-inf"),
        )
        if time - previous >= recovered_gap_hours:
            qualifying.append(assessment)
    if len(qualifying) < 2:
        return None
    selected = sorted(qualifying, key=lambda item: item.time_from_origin_hours)[-2:]
    return ProtocolBaseline(
        (selected[0].force + selected[1].force) / 2.0,  # type: ignore[operator]
        (selected[0].impulse + selected[1].impulse) / 2.0,  # type: ignore[operator]
    )


def observe_assessments(
    true_force: Array,
    true_impulse: Array,
    preferred_depth: Array,
    present: Array,
    trial_count: Array,
    model: MeasurementModel,
    *,
    depth_rng: np.random.Generator,
    force_rng: np.random.Generator,
    impulse_rng: np.random.Generator,
    validity_rng: np.random.Generator,
    invalid_scale_rng: np.random.Generator,
    missing_rng: np.random.Generator,
) -> AssessmentMeasurements:
    """Observe fixed-shape history slots; depth is context and has no outcome effect."""
    rows, slots = present.shape
    shape = (rows, slots)
    depth_jitter = depth_rng.normal(0.0, model.depth_history_jitter_m, shape)
    force_noise = force_rng.normal(0.0, 1.0, shape)
    impulse_noise = impulse_rng.normal(0.0, 1.0, shape)
    invalid_draw = validity_rng.random(shape)
    invalid_scale = invalid_scale_rng.uniform(*model.invalid_scale_range, size=shape)
    missing_draw = missing_rng.random(shape)

    depth = np.clip(
        preferred_depth[:, None] + depth_jitter,
        *model.depth_clip_m,
    )
    trials = np.maximum(trial_count, 1)
    force_raw = true_force + force_noise * model.trial_sd_force / np.sqrt(trials)
    impulse_raw = true_impulse + impulse_noise * model.trial_sd_impulse / np.sqrt(trials)
    invalid = present & (invalid_draw < model.invalid_rate)
    force_raw = np.where(invalid, force_raw * invalid_scale, force_raw)
    missing = present & ~invalid & (missing_draw < model.missing_rate)
    usable = present & ~invalid & ~missing
    force = np.where(present & ~missing, force_raw, np.nan)
    impulse = np.where(present & ~missing, impulse_raw, np.nan)
    depth = np.where(present, np.round(depth / model.depth_grid_m) * model.depth_grid_m, np.nan)
    validity = np.where(
        ~present,
        MISSING_VALUE,
        np.where(
            invalid,
            AssessmentValidity.INVALID.value,
            np.where(
                missing, AssessmentValidity.MISSING_VALUES.value, AssessmentValidity.VALID.value
            ),
        ),
    ).astype(object)
    return AssessmentMeasurements(
        force,
        impulse,
        depth,
        validity,
        usable,
        force_raw,
        impulse_raw,
    )


def observe_target(
    true_force: Array,
    true_impulse: Array,
    preferred_depth: Array,
    model: MeasurementModel,
    *,
    depth_rng: np.random.Generator,
    force_rng: np.random.Generator,
    impulse_rng: np.random.Generator,
) -> TargetMeasurements:
    """Measure five valid standard-depth trials; keep target depth hidden and unlinked."""
    rows = true_force.shape[0]
    shape = (rows, 2)
    depth_jitter = depth_rng.normal(0.0, model.depth_target_jitter_m, shape)
    force_noise = force_rng.normal(0.0, 1.0, shape)
    impulse_noise = impulse_rng.normal(0.0, 1.0, shape)
    depth = np.clip(preferred_depth[:, None] + depth_jitter, *model.depth_clip_m)
    force = true_force + force_noise * model.trial_sd_force / np.sqrt(model.target_trials)
    impulse = true_impulse + impulse_noise * model.trial_sd_impulse / np.sqrt(model.target_trials)
    return TargetMeasurements(force, impulse, depth)


RICH_MONITORING_OBSERVATION = ObservationContract(
    name="rich_monitoring",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("relative force", "net impulse"),
        (
            "Mean of the two latest valid assessments in [-240,-24] h; each is at least 60 h "
            "after its preceding exposure. Fewer than two means no baseline."
        ),
    ),
    assessment_history=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("time", "force", "net impulse", "depth", "trial count", "validity"),
        (
            "Two to fourteen present assessments use one to three trials; invalid and "
            "missing-value states remain explicit."
        ),
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("time", "kind", "duration", "dose", "index exposure", "known plans"),
        (
            "Three to six prior exposures span 504–672 h; the index exposure is at origin, "
            "and up to three plans are known for 24–160 h."
        ),
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("training age", "strength", "prior four-week bout count"),
        (
            "Training age, strength, and prior bout count are public; kinetics, response "
            "amplitudes, and camp effects are hidden."
        ),
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("prior exposure history", "prior assessments"),
        "Only prior exposures and assessments available before the origin are projected.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff="Pre-origin observations and plans known at the index origin.",
        history_scope=(
            "Prior exposures in 21–28 days; monitoring at +14–40 h and +60–84 h after "
            "exposure, plus two fixed baseline opportunities."
        ),
        plans_known_at_origin_available=True,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent kinetics",
            "latent response amplitudes",
            "camp effects",
            "latent state",
            "target-time depth",
            "future outcomes",
            "random generator state",
            "scorer truth",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent kinetics",
            "latent response amplitudes",
            "camp effects",
            "latent state",
            "target-time depth",
            "future outcomes",
            "random generator state",
            "scorer truth",
            "grouping/query keys as predictors",
        ),
        "Grouping/query keys are carried outside the 135 predictor fields.",
    ),
    measurement_construction=(
        "Routine depth is contextual only and does not change force or impulse. "
        "The target uses five valid standardized-depth trials; its generated depth is "
        "hidden and has no outcome multiplier."
    ),
)
