"""Preliminary scalar trial measurement and shared episode discrepancy law."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isfinite, sqrt
from typing import Literal

from cmj_recovery_dynamics.contracts import (
    InformationBoundary,
    InformationStatus,
    ObservationContract,
    TemporalAvailability,
)
from cmj_recovery_dynamics.reproduction.single_exposure import HORIZONS, KeyedRandomStreams

Metric = Literal["force", "impulse"]
TRIAL_COUNT = 3
FORCE_SESSION_PROCESS_CV = 0.0025
FORCE_TRIAL_CV = 0.0060
IMPULSE_SESSION_PROCESS_CV = 0.0035
IMPULSE_TRIAL_CV = 0.0090
DISCREPANCY_MAGNITUDE = (0.005, 0.015)
DISCREPANCY_FACTOR_MODE_PROBABILITIES = (0.50, 0.20, 0.20, 0.10)


@dataclass(frozen=True, slots=True)
class ScalarAssessmentObservation:
    """Three scalar trials per metric with no shared force-time trace."""

    force_trials: tuple[float, float, float]
    impulse_trials: tuple[float, float, float]

    @property
    def force_mean(self) -> float:
        return fsum(self.force_trials) / TRIAL_COUNT

    @property
    def impulse_mean(self) -> float:
        return fsum(self.impulse_trials) / TRIAL_COUNT


def _noise_support(metric: Metric) -> tuple[float, float]:
    if metric == "force":
        return FORCE_SESSION_PROCESS_CV, FORCE_TRIAL_CV
    if metric == "impulse":
        return IMPULSE_SESSION_PROCESS_CV, IMPULSE_TRIAL_CV
    raise ValueError(f"unknown measurement metric: {metric}")


def assessment_error_sd_fraction(metric: Metric) -> float:
    session_cv, trial_cv = _noise_support(metric)
    return sqrt(session_cv**2 + trial_cv**2 / TRIAL_COUNT)


def innovation_error_sd_fraction(metric: Metric) -> float:
    return sqrt(2.0) * assessment_error_sd_fraction(metric)


def assessment_trials(
    truth: float,
    *,
    metric: Metric,
    streams: KeyedRandomStreams,
    assessment_key: str,
) -> tuple[float, float, float]:
    if not isfinite(truth) or truth <= 0.0:
        raise ValueError("assessment truth must be positive and finite")
    session_cv, trial_cv = _noise_support(metric)
    session_error = float(
        streams.generator("assessment_session_error", assessment_key, metric).normal(
            0.0, session_cv
        )
    )
    return tuple(
        float(
            truth
            * (
                1.0
                + session_error
                + float(
                    streams.generator("trial_noise", assessment_key, metric, trial_index).normal(
                        0.0, trial_cv
                    )
                )
            )
        )
        for trial_index in range(TRIAL_COUNT)
    )  # type: ignore[return-value]


def measure_scalar_assessment(
    truth_force_n_per_kg: float,
    truth_impulse_m_per_s: float,
    streams: KeyedRandomStreams,
    *,
    assessment_key: str,
) -> ScalarAssessmentObservation:
    """Measure independent scalar force and impulse trial series."""
    return ScalarAssessmentObservation(
        assessment_trials(
            truth_force_n_per_kg,
            metric="force",
            streams=streams,
            assessment_key=assessment_key,
        ),
        assessment_trials(
            truth_impulse_m_per_s,
            metric="impulse",
            streams=streams,
            assessment_key=assessment_key,
        ),
    )


def draw_episode_discrepancy(
    streams: KeyedRandomStreams,
    episode_key: str,
    *,
    channel: str,
) -> dict[str, dict[str, float]]:
    if channel not in {"current_discrepancy", "prior_episode_discrepancy"}:
        raise ValueError(f"unsupported discrepancy RNG channel: {channel}")
    magnitude = float(
        streams.generator(channel, episode_key, "bounded_magnitude").uniform(*DISCREPANCY_MAGNITUDE)
    )
    mode = int(
        streams.generator(channel, episode_key, "correlation_topology").choice(
            4, p=DISCREPANCY_FACTOR_MODE_PROBABILITIES
        )
    )

    def sign(*keys: object) -> float:
        return (
            -1.0
            if streams.generator(channel, episode_key, "sign", *keys).integers(0, 2) == 0
            else 1.0
        )

    episode_sign = sign("episode")
    metric_signs = {metric: sign("metric", metric) for metric in ("force", "impulse")}
    horizon_signs = {horizon: sign("horizon", horizon) for horizon, _ in HORIZONS}
    cell_signs = {
        (metric, horizon): sign("cell", metric, horizon)
        for metric in ("force", "impulse")
        for horizon, _ in HORIZONS
    }
    output: dict[str, dict[str, float]] = {}
    for horizon, _ in HORIZONS:
        output[horizon] = {}
        for metric in ("force", "impulse"):
            factor = (
                episode_sign,
                metric_signs[metric],
                horizon_signs[horizon],
                cell_signs[(metric, horizon)],
            )[mode]
            output[horizon][metric] = magnitude * factor
    return output


EPISODE_SUMMARY_OBSERVATION = ObservationContract(
    name="episode_summary",
    baseline_measurements=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("force", "net impulse", "depth"),
        "One dedicated three-trial baseline approximately two hours before exposure.",
    ),
    assessment_history=InformationBoundary(
        InformationStatus.UNAVAILABLE,
        (),
        "The contract uses four prior episodes rather than a camp-wide assessment history.",
    ),
    exposure_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("eight current-exposure fields",),
        "Current exposure occurs at time zero.",
    ),
    participant_covariates=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("training age", "strength"),
        "Camp identifier and participant response effects are hidden.",
    ),
    prior_episode_information=InformationBoundary(
        InformationStatus.SPECIFIED,
        ("four episode baselines", "four prior exposures", "six outcomes per episode"),
        "Episodes are in generator order; inter-episode elapsed time is not provided.",
    ),
    temporal_availability=TemporalAvailability(
        information_cutoff=(
            "Current baseline, exposure, participant context, and four prior episodes."
        ),
        history_scope="No additional material exposure through H72; future labels are unavailable.",
        plans_known_at_origin_available=False,
        future_realized_exposure_available=False,
    ),
    hidden_variables=InformationBoundary(
        InformationStatus.SPECIFIED,
        (
            "latent response weights and kinetics",
            "participant and camp effects",
            "true recovery state",
            "measurement discrepancy and noise",
            "random generator state",
            "future targets",
        ),
    ),
    forbidden_variables=InformationBoundary(
        InformationStatus.PARTIALLY_SPECIFIED,
        ("episode keys", "future labels"),
        "Keys and labels are not predictor features; other exclusions remain unresolved.",
    ),
    measurement_construction=(
        "The preliminary observation measures three scalar force trials and three scalar impulse "
        "trials and takes each "
        "arithmetic mean. It freezes no shared force-time trace or force/impulse identity."
    ),
)

__all__ = [
    "DISCREPANCY_FACTOR_MODE_PROBABILITIES",
    "DISCREPANCY_MAGNITUDE",
    "EPISODE_SUMMARY_OBSERVATION",
    "FORCE_SESSION_PROCESS_CV",
    "FORCE_TRIAL_CV",
    "IMPULSE_SESSION_PROCESS_CV",
    "IMPULSE_TRIAL_CV",
    "ScalarAssessmentObservation",
    "TRIAL_COUNT",
    "assessment_error_sd_fraction",
    "assessment_trials",
    "draw_episode_discrepancy",
    "innovation_error_sd_fraction",
    "measure_scalar_assessment",
]
