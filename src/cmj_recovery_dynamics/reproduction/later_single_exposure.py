"""Source-closed generation for the two later single-exposure formulations."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    DISCREPANCY_FACTOR_MODE_PROBABILITIES,
    EPISODE_DISCREPANCY_SUPPORT,
    FixedModeCampEffects,
    FixedModeResponseEffects,
    fixed_mode_response_fraction,
    sample_fixed_mode_camp_effects,
    sample_fixed_mode_response_effects,
)
from cmj_recovery_dynamics.dynamics.threshold_response import (
    PRIOR_HIGH_LOAD_PROBABILITY,
    ThresholdCampEffects,
    ThresholdResponseParameters,
    sample_threshold_camp_effects,
    sample_threshold_response_parameters,
    threshold_response_fraction,
)
from cmj_recovery_dynamics.reproduction.single_exposure import (
    CURRENT_EXPOSURE_TIME_HOURS,
    HORIZONS,
    NO_ADDITIONAL_EXPOSURE_THROUGH_H72,
    PRIOR_COMPLETE_EPISODES,
    RNG_IDENTITY_NAMESPACE,
    SPLIT_GEOMETRY,
    EpisodeRecord,
    KeyedRandomStreams,
    ObservedEpisode,
    PublicExposure,
    iter_public_members,
    project_episode,
    sample_baseline_depth,
)

LaterFormulation = Literal["threshold_response_recovery", "fixed_mode_discrepancy_recovery"]
_TRAIN_HIGH_LOAD_PROBABILITY = 0.30
_VALIDATION_HIGH_LOAD_PROBABILITY = 0.70
_THRESHOLD_EPISODE_DISCREPANCY_SUPPORT = (0.005, 0.015)
_THRESHOLD_DISCREPANCY_FACTOR_MODE_PROBABILITIES = (0.50, 0.20, 0.20, 0.10)


@dataclass(frozen=True, slots=True)
class LaterSourceClosure:
    benchmark_name: LaterFormulation
    parameter_authority_version: str
    parameter_authority_metadata_key: str
    public_root_metadata_key: str
    source_commit: str
    task_tree: str
    repository_task_path: str
    params_path: str
    response_path: str
    exposure_path: str
    generator_path: str
    rng_path: str
    split_path: str
    measurement_path: str
    projection_path: str
    public_generator_path: str
    scorer_path: str
    cell_definition_path: str | None
    test_paths: tuple[str, ...]
    schema_path: str
    manifest_path: str
    hidden_design: tuple[int, int, int] | None
    public_data_qualification_status: str | None
    scientific_adjudication_status: str | None


_TASK_PATH = "problems/preseason-exposure-cmj-recovery-forecast"
_DATA_GENERATION = "data_generation"


def _closure(
    benchmark_name: LaterFormulation,
    authority_version: str,
    metadata_key: str,
    commit: str,
    tree: str,
    tests: tuple[str, ...],
    hidden_design: tuple[int, int, int] | None,
    cell_definition_path: str | None,
    public_data_qualification_status: str | None,
    scientific_adjudication_status: str | None,
) -> LaterSourceClosure:
    source_root = f"{_DATA_GENERATION}/src/lcmj_v2"
    return LaterSourceClosure(
        benchmark_name,
        authority_version,
        metadata_key,
        metadata_key,
        commit,
        tree,
        _TASK_PATH,
        f"{source_root}/params.py",
        f"{source_root}/response.py",
        f"{source_root}/exposure.py",
        f"{source_root}/generator.py",
        f"{source_root}/rng.py",
        f"{source_root}/splits.py",
        f"{source_root}/measurement.py",
        f"{source_root}/projection.py",
        f"{_DATA_GENERATION}/generate_public.py",
        "scorer/compute_score.py",
        cell_definition_path,
        tuple(f"{_DATA_GENERATION}/tests/{path}" for path in tests),
        "data/canonical_v2.py",
        "data/public/manifest.json",
        hidden_design,
        public_data_qualification_status,
        scientific_adjudication_status,
    )


LATER_SOURCE_CLOSURES = MappingProxyType(
    {
        "threshold_response_recovery": _closure(
            "threshold_response_recovery",
            "2.1.0",
            "threshold_response_recovery.historical_labels",
            "059f42ebc7396662dba04f0b0021d834e4e1aa79",
            "d6758ab6f75262121bc6b6df1eb995cb32567386",
            (
                "conftest.py",
                "test_lcmj_c1_artifacts.py",
                "test_lcmj_c1_law.py",
                "test_lcmj_v2_parity.py",
                "test_lcmj_v2_properties.py",
                "test_lcmj_v2_qualification.py",
                "test_lcmj_v2_rng_causality.py",
            ),
            (21, 5250, 15750),
            "scorer/cells.py",
            None,
            None,
        ),
        "fixed_mode_discrepancy_recovery": _closure(
            "fixed_mode_discrepancy_recovery",
            "1.0.0",
            "fixed_mode_discrepancy_recovery.historical_labels",
            "984a9c740f7fab11d5ae10c5eee3c99f53f43537",
            "96dd5450512aca55d42c90c7c1a845ebbb2887bd",
            (
                "conftest.py",
                "test_candidate_h_contract.py",
                "test_lcmj_v2_parity.py",
                "test_lcmj_v2_properties.py",
                "test_lcmj_v2_qualification.py",
                "test_lcmj_v2_rng_causality.py",
            ),
            None,
            None,
            "PASS",
            "NOT_COMPLETED",
        ),
    }
)


@dataclass(frozen=True, slots=True)
class ParticipantBasics:
    training_age_years: float
    strength_index: float
    baseline_force_n_per_kg: float
    baseline_impulse_m_per_s: float
    normalized_context: tuple[float, float, float, float]
    centered_context: tuple[float, float, float, float]


def sample_participant_basics(streams: KeyedRandomStreams) -> ParticipantBasics:
    age = float(streams.generator("participant_training_age", "context").uniform(0.5, 18.0))
    strength = float(streams.generator("participant_strength_index", "context").uniform(-1.0, 1.0))
    strength_fraction = (strength + 1.0) / 2.0
    force_noise = float(streams.generator("participant_baseline_force", "context").uniform())
    impulse_noise = float(streams.generator("participant_baseline_impulse", "context").uniform())
    baseline_force = 18.0 + 12.0 * (0.75 * strength_fraction + 0.25 * force_noise)
    baseline_impulse = 2.0 + 2.0 * (0.40 * strength_fraction + 0.60 * impulse_noise)
    normalized = (
        (age - 0.5) / 17.5,
        strength_fraction,
        (baseline_force - 18.0) / 12.0,
        (baseline_impulse - 2.0) / 2.0,
    )
    return ParticipantBasics(
        age,
        strength,
        baseline_force,
        baseline_impulse,
        normalized,
        tuple(value - 0.5 for value in normalized),  # type: ignore[arg-type]
    )


def draw_episode_discrepancy(
    streams: KeyedRandomStreams,
    episode_key: str,
    *,
    channel: str,
    support: tuple[float, float],
    factor_probabilities: tuple[float, float, float, float],
) -> dict[str, dict[str, float]]:
    if channel not in {"current_discrepancy", "prior_episode_discrepancy"}:
        raise ValueError(f"unsupported discrepancy RNG channel: {channel}")
    low, high = support
    magnitude = float(
        streams.generator(channel, episode_key, "bounded_magnitude").uniform(low, high)
    )
    mode = int(
        streams.generator(channel, episode_key, "correlation_topology").choice(
            4, p=factor_probabilities
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
    for horizon, _lag in HORIZONS:
        output[horizon] = {}
        for metric in ("force", "impulse"):
            factor = (
                episode_sign,
                metric_signs[metric],
                horizon_signs[horizon],
                cell_signs[(metric, horizon)],
            )[mode]
            output[horizon][metric] = magnitude * factor
    if any(abs(value) > high + 1e-15 for metrics in output.values() for value in metrics.values()):
        raise RuntimeError("episode discrepancy escaped its frozen support")
    return output


def _observe_episode(
    streams: KeyedRandomStreams,
    *,
    episode_slot: str,
    baseline_force_truth: float,
    baseline_impulse_truth: float,
    exposure: PublicExposure,
    depth_m: float,
    response: Callable[[PublicExposure, float, str], float],
    discrepancy_support: tuple[float, float],
    discrepancy_probabilities: tuple[float, float, float, float],
    discrepancy_channel: str,
) -> ObservedEpisode:
    from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
        measure_phase_consistent_assessment,
    )

    baseline = measure_phase_consistent_assessment(
        baseline_force_truth,
        baseline_impulse_truth,
        streams,
        assessment_key=f"{episode_slot}:dedicated_baseline",
    )
    discrepancy = draw_episode_discrepancy(
        streams,
        episode_slot,
        channel=discrepancy_channel,
        support=discrepancy_support,
        factor_probabilities=discrepancy_probabilities,
    )
    innovations: list[tuple[str, float, float]] = []
    for horizon, lag_hours in HORIZONS:
        force_truth = baseline_force_truth * (
            1.0 + response(exposure, lag_hours, "force") + discrepancy[horizon]["force"]
        )
        impulse_truth = baseline_impulse_truth * (
            1.0 + response(exposure, lag_hours, "impulse") + discrepancy[horizon]["impulse"]
        )
        if not (math.isfinite(force_truth) and force_truth > 0.0):
            raise RuntimeError(f"non-positive force criterion truth at {horizon}")
        if not (math.isfinite(impulse_truth) and impulse_truth > 0.0):
            raise RuntimeError(f"non-positive impulse criterion truth at {horizon}")
        criterion = measure_phase_consistent_assessment(
            force_truth,
            impulse_truth,
            streams,
            assessment_key=f"{episode_slot}:criterion:{horizon}",
        )
        innovations.append(
            (
                horizon,
                criterion.force_mean - baseline.force_mean,
                criterion.impulse_mean - baseline.impulse_mean,
            )
        )
    return ObservedEpisode(
        baseline.force_mean,
        baseline.impulse_mean,
        depth_m,
        exposure,
        tuple(innovations),
    )


def generate_later_episode(
    *,
    benchmark_name: LaterFormulation,
    split: str,
    camp_index: int,
    participant_index: int,
    root_seed: str,
) -> EpisodeRecord:
    """Generate one public episode using the selected formulation and shared O04 path."""
    if benchmark_name not in LATER_SOURCE_CLOSURES:
        raise ValueError(f"unsupported later formulation: {benchmark_name}")
    if split not in {"train", "validation"}:
        raise ValueError("only public train and validation generation is supported")
    if camp_index < 0 or participant_index not in range(250):
        raise ValueError("camp and participant indexes are outside public split geometry")
    if camp_index >= SPLIT_GEOMETRY[split].camps:
        raise ValueError("camp index is outside the selected public split")

    camp_streams = KeyedRandomStreams(RNG_IDENTITY_NAMESPACE, root_seed, split, "camp", camp_index)
    participant_streams = camp_streams.child("participant", participant_index)
    basics = sample_participant_basics(participant_streams)
    threshold = benchmark_name == "threshold_response_recovery"
    if threshold:
        participant_effects: ThresholdResponseParameters | FixedModeResponseEffects = (
            sample_threshold_response_parameters(participant_streams)
        )
        camp_effects: ThresholdCampEffects | FixedModeCampEffects = sample_threshold_camp_effects(
            camp_streams
        )
        discrepancy_support = _THRESHOLD_EPISODE_DISCREPANCY_SUPPORT
        discrepancy_probabilities = _THRESHOLD_DISCREPANCY_FACTOR_MODE_PROBABILITIES
    else:
        participant_effects = sample_fixed_mode_response_effects(
            participant_streams, basics.centered_context
        )
        camp_effects = sample_fixed_mode_camp_effects(camp_streams)
        discrepancy_support = EPISODE_DISCREPANCY_SUPPORT
        discrepancy_probabilities = DISCREPANCY_FACTOR_MODE_PROBABILITIES

    def exposure_for_episode(slot: str, *, prior: bool) -> PublicExposure:
        channel = "prior_episode_exposure" if prior else "current_exposure"
        if threshold:
            probability = (
                PRIOR_HIGH_LOAD_PROBABILITY
                if prior
                else _TRAIN_HIGH_LOAD_PROBABILITY
                if split == "train"
                else _VALIDATION_HIGH_LOAD_PROBABILITY
            )
            from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
                sample_preliminary_exposure,
            )

            return sample_preliminary_exposure(
                participant_streams,
                high_load_probability=probability,
                channel=channel,
                episode_key=slot,
            )
        from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
            mixture_for,
            sample_correlated_exposure,
        )

        return sample_correlated_exposure(
            participant_streams,
            archetype_probabilities=tuple(mixture_for(split, prior=prior)),
            channel=channel,
            episode_key=slot,
        )

    def response(exposure: PublicExposure, lag_hours: float, metric: str) -> float:
        if threshold:
            return threshold_response_fraction(
                exposure,
                lag_hours,
                participant_effects,  # type: ignore[arg-type]
                camp_effects,  # type: ignore[arg-type]
                metric,  # type: ignore[arg-type]
            )
        return fixed_mode_response_fraction(
            exposure,
            lag_hours,
            participant_effects,  # type: ignore[arg-type]
            camp_effects,  # type: ignore[arg-type]
            metric,  # type: ignore[arg-type]
            basics.normalized_context,
        )

    prior: list[ObservedEpisode] = []
    for index in range(PRIOR_COMPLETE_EPISODES):
        slot = f"prior_{index}"
        prior.append(
            _observe_episode(
                participant_streams,
                episode_slot=slot,
                baseline_force_truth=basics.baseline_force_n_per_kg,
                baseline_impulse_truth=basics.baseline_impulse_m_per_s,
                exposure=exposure_for_episode(slot, prior=True),
                depth_m=sample_baseline_depth(participant_streams, slot),
                response=response,
                discrepancy_support=discrepancy_support,
                discrepancy_probabilities=discrepancy_probabilities,
                discrepancy_channel="prior_episode_discrepancy",
            )
        )
    if len(prior) != PRIOR_COMPLETE_EPISODES:
        raise RuntimeError("single-exposure episodes require exactly four complete prior episodes")

    current = _observe_episode(
        participant_streams,
        episode_slot="current",
        baseline_force_truth=basics.baseline_force_n_per_kg,
        baseline_impulse_truth=basics.baseline_impulse_m_per_s,
        exposure=exposure_for_episode("current", prior=False),
        depth_m=sample_baseline_depth(participant_streams, "current"),
        response=response,
        discrepancy_support=discrepancy_support,
        discrepancy_probabilities=discrepancy_probabilities,
        discrepancy_channel="current_discrepancy",
    )
    return EpisodeRecord(
        participant_streams.opaque_key("participant", "group"),
        participant_streams.opaque_key("episode", "current"),
        tuple(
            (horizon, participant_streams.opaque_key("query", "current", horizon))
            for horizon, _ in HORIZONS
        ),
        basics.training_age_years,
        basics.strength_index,
        current,
        tuple(prior),  # type: ignore[arg-type]
        camp_streams.opaque_key("camp", "group"),
        split,
        camp_index,
        participant_index,
    )


def iter_later_public_episodes(
    split: str,
    *,
    benchmark_name: LaterFormulation,
    root_seed: str,
) -> Iterator[EpisodeRecord]:
    if split not in SPLIT_GEOMETRY:
        raise ValueError("only public train and validation splits are available")
    for camp_index, participant_index in iter_public_members(split):
        yield generate_later_episode(
            benchmark_name=benchmark_name,
            split=split,
            camp_index=camp_index,
            participant_index=participant_index,
            root_seed=root_seed,
        )


def project_later_episode(record: EpisodeRecord) -> list[dict[str, object]]:
    return project_episode(record)


__all__ = [
    "CURRENT_EXPOSURE_TIME_HOURS",
    "LATER_SOURCE_CLOSURES",
    "LaterFormulation",
    "LaterSourceClosure",
    "NO_ADDITIONAL_EXPOSURE_THROUGH_H72",
    "ParticipantBasics",
    "draw_episode_discrepancy",
    "generate_later_episode",
    "iter_later_public_episodes",
    "project_later_episode",
    "sample_participant_basics",
]
