"""Publication-safe authority and shared primitives for SP04–SP06."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np

from cmj_recovery_dynamics.reproduction.contracts import ReproductionStatus as Status

HORIZONS = (("H24", 24.0), ("H48", 48.0), ("H72", 72.0))
WorldName = Literal["W03", "W04"]
ROW_KEY_FIELDS = ("participant_key", "episode_key", "query_key")
TARGET_FIELDS = (
    "label.relative_mean_concentric_force_innovation",
    "label.relative_concentric_net_impulse_innovation",
)
TARGET_UNITS = {TARGET_FIELDS[0]: "N/kg", TARGET_FIELDS[1]: "m/s"}
BASELINE_FIELDS = (
    "baseline.relative_mean_concentric_force",
    "baseline.relative_concentric_net_impulse",
    "baseline.depth_m",
)
PARTICIPANT_FIELDS = ("participant.training_age_years", "participant.strength_index")
EXPOSURE_FIELDS = (
    "duration_min",
    "total_distance_m",
    "high_speed_distance_m",
    "sprint_distance_m",
    "high_intensity_accel_count",
    "high_intensity_decel_count",
    "session_rpe_cr10",
    "session_rpe_load_au",
)
RECOVERY_FIELDS = tuple(
    f"{horizon}.{metric}_innovation"
    for horizon, _ in HORIZONS
    for metric in (
        "relative_mean_concentric_force",
        "relative_concentric_net_impulse",
    )
)
PREDICTOR_FIELDS = (
    ("horizon",)
    + BASELINE_FIELDS
    + PARTICIPANT_FIELDS
    + tuple(f"index_exposure.{name}" for name in EXPOSURE_FIELDS)
    + tuple(
        f"prior_episode[{index}].{name}"
        for index in range(4)
        for name in (
            *BASELINE_FIELDS,
            *(f"exposure.{field}" for field in EXPOSURE_FIELDS),
            *RECOVERY_FIELDS,
        )
    )
)
PREDICTOR_BLOCK_GEOMETRY = (1, 3, 2, 8, (17, 17, 17, 17))
if len(PREDICTOR_FIELDS) != 82 or len(set(PREDICTOR_FIELDS)) != 82:
    raise RuntimeError("R03 must contain exactly 82 unique predictor fields")

EXPOSURE_SUPPORTS: tuple[tuple[str, tuple[float, float]], ...] = (
    ("duration_min", (45.0, 120.0)),
    ("total_distance_m", (3000.0, 13000.0)),
    ("high_speed_distance_m", (0.0, 2000.0)),
    ("sprint_distance_m", (0.0, 600.0)),
    ("high_intensity_accel_count", (0.0, 150.0)),
    ("high_intensity_decel_count", (0.0, 150.0)),
    ("session_rpe_cr10", (2.0, 10.0)),
)

RNG_VERSION = "lcmj-v2-keyed-rng-1.0.0"
_RNG_CHANNELS = frozenset(
    {
        "camp_identity",
        "camp_amplitude_effect",
        "participant_training_age",
        "participant_strength_index",
        "participant_baseline_force",
        "participant_baseline_impulse",
        "participant_amplitude_effect",
        "participant_time_constant_effect",
        "current_load_class",
        "current_exposure",
        "prior_episode_exposure",
        "exposure_archetype_assignment",
        "exposure_factor_residual",
        "exposure_feature_residual",
        "current_discrepancy",
        "prior_episode_discrepancy",
        "assessment_session_error",
        "trial_noise",
        "baseline_depth_context",
        "opaque_keys",
    }
)


def _json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        items = cast(list[Any] | tuple[Any, ...], value)
        return [_json_value(item) for item in items]
    raise TypeError(f"RNG identity/key value is not a supported scalar: {type(value).__name__}")


class KeyedRandomStreams:
    """Reproduce the selected keyed ``default_rng`` stream construction."""

    def __init__(self, *identity: Any) -> None:
        if not identity:
            raise ValueError("a non-empty structural RNG identity is required")
        self.identity = tuple(_json_value(part) for part in identity)

    def _digest(self, channel: str, *keys: Any) -> bytes:
        if channel not in _RNG_CHANNELS:
            raise KeyError(f"unregistered V2 RNG channel: {channel}")
        payload = json.dumps(
            [_json_value(part) for part in (RNG_VERSION, self.identity, channel, keys)],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(b"lcmj-v2-rng\0" + payload).digest()

    def generator(self, channel: str, *keys: Any) -> np.random.Generator:
        seed = int.from_bytes(self._digest(channel, *keys)[:16], "big")
        return np.random.default_rng(seed)

    def child(self, *suffix: Any) -> KeyedRandomStreams:
        return KeyedRandomStreams(*self.identity, *suffix)

    def opaque_key(self, kind: str, *keys: Any) -> str:
        return f"{kind}-{self._digest('opaque_keys', kind, *keys).hex()[:32]}"


@dataclass(frozen=True, slots=True)
class PublicExposure:
    duration_min: float
    total_distance_m: float
    high_speed_distance_m: float
    sprint_distance_m: float
    high_intensity_accel_count: int
    high_intensity_decel_count: int
    session_rpe_cr10: float
    session_rpe_load_au: float
    archetype_index: int | None = None

    def __post_init__(self) -> None:
        values = self.as_dict()
        for name, (low, high) in EXPOSURE_SUPPORTS:
            value = float(values[name])
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite and within [{low}, {high}]")
        if (
            type(self.high_intensity_accel_count) is not int
            or type(self.high_intensity_decel_count) is not int
        ):
            raise ValueError("acceleration and deceleration counts must be integers")
        if not 0.0 <= self.sprint_distance_m <= self.high_speed_distance_m <= self.total_distance_m:
            raise ValueError("exposure distance ordering invariant failed")
        if self.session_rpe_load_au != self.duration_min * self.session_rpe_cr10:
            raise ValueError("sRPE load must equal duration multiplied by session RPE")
        if not math.isfinite(self.session_rpe_load_au):
            raise ValueError("sRPE load must be finite")
        if self.archetype_index is not None and not 0 <= self.archetype_index < 4:
            raise ValueError("archetype index must be one of the four source-defined classes")

    def as_dict(self) -> dict[str, float | int]:
        return {
            "duration_min": self.duration_min,
            "total_distance_m": self.total_distance_m,
            "high_speed_distance_m": self.high_speed_distance_m,
            "sprint_distance_m": self.sprint_distance_m,
            "high_intensity_accel_count": self.high_intensity_accel_count,
            "high_intensity_decel_count": self.high_intensity_decel_count,
            "session_rpe_cr10": self.session_rpe_cr10,
            "session_rpe_load_au": self.session_rpe_load_au,
        }


@dataclass(frozen=True, slots=True)
class SourceClosure:
    specimen: str
    parameter_authority: str
    source_commit: str
    task_tree: str
    source_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    schema_path: str
    manifest_path: str


_SOURCE_PATHS = (
    ("data_generation/src/lcmj_v2/__init__.py",)
    + tuple(
        f"data_generation/src/lcmj_v2/{name}.py"
        for name in (
            "params",
            "exposure",
            "response",
            "measurement",
            "generator",
            "projection",
            "rng",
            "splits",
        )
    )
    + ("data_generation/generate_public.py",)
)
_TEST_PATHS = (
    "data_generation/tests/test_lcmj_v2_parity.py",
    "data_generation/tests/test_lcmj_v2_properties.py",
    "data_generation/tests/test_lcmj_v2_rng_causality.py",
    "data_generation/tests/test_lcmj_v2_qualification.py",
)
SOURCE_CLOSURES = {
    "SP04": SourceClosure(
        "SP04",
        "LCMJ-V2-PARAMETERS-ALI-494-1.0.0",
        "da3fa115838b177f5ba2bd055a5c3465654c4e22",
        "e11c1140b362c52d40942463bb0714171ae165f8",
        _SOURCE_PATHS,
        _TEST_PATHS,
        "data/canonical_v2.py",
        "data/public/manifest.json",
    ),
    "SP05": SourceClosure(
        "SP05",
        "LCMJ-V2-PARAMETERS-ALI-494-1.1.0",
        "04e9db465a481a88f18e8fc062e317269204dce8",
        "5ef8ad267d3e57f8fa73dd3b82967937291b20ca",
        _SOURCE_PATHS,
        _TEST_PATHS,
        "data/canonical_v2.py",
        "data/public/manifest.json",
    ),
    "SP06": SourceClosure(
        "SP06",
        "LCMJ-V2-PARAMETERS-ALI-506-1.2.0",
        "144d283f7b43e6c1a2972b8b58cfc3e4e05b384a",
        "7dbd339858555e11065f9a022820708d8c012f96",
        _SOURCE_PATHS,
        _TEST_PATHS,
        "data/canonical_v2.py",
        "data/public/manifest.json",
    ),
}


@dataclass(frozen=True, slots=True)
class FormulationIdentity:
    specimen: str
    benchmark: str
    world: WorldName
    observation: str
    dataset: str
    task: str = "T02"
    representation: str = "R03"
    response_family: str = "W03_biexponential"
    response_mapping: str = "W03_seven_primitive"


FORMULATIONS = {
    "SP04": FormulationIdentity("SP04", "preliminary_post_exposure_recovery", "W03", "O03", "D05"),
    "SP05": FormulationIdentity(
        "SP05", "phase_consistent_post_exposure_recovery", "W03", "O04", "D06"
    ),
    "SP06": FormulationIdentity(
        "SP06",
        "correlated_exposure_recovery",
        "W04",
        "O04",
        "D07",
        response_mapping="W04_four_basis",
    ),
}


@dataclass(frozen=True, slots=True)
class FormulationTransition:
    source: str
    target: str
    changed: tuple[str, ...]
    unchanged: tuple[str, ...]


TRANSITIONS = (
    FormulationTransition(
        "SP04",
        "SP05",
        ("observation", "dataset"),
        ("world", "task", "representation"),
    ),
    FormulationTransition(
        "SP05",
        "SP06",
        ("world", "dataset"),
        ("observation", "task", "representation"),
    ),
)


@dataclass(frozen=True, slots=True)
class DatasetGeometry:
    camps: int
    participants: int
    episodes: int
    rows: int

    def __post_init__(self) -> None:
        if self.participants != self.camps * 250 or self.episodes != self.participants:
            raise ValueError("single-exposure public split requires 250 episodes per camp")
        if self.rows != self.episodes * len(HORIZONS):
            raise ValueError("single-exposure public split requires three rows per episode")


SPLIT_GEOMETRY = {
    "train": DatasetGeometry(96, 24000, 24000, 72000),
    "validation": DatasetGeometry(16, 4000, 4000, 12000),
}
PUBLIC_ROOT_SEED = "ALI-494-LCMJ-V2-PUBLIC-001"
ROW_ORDERING_STATUS = Status.UNKNOWN
# Historical reference digests only; regeneration does not establish byte identity.
REFERENCE_DATASET_HASHES = {
    "D05": (
        "3b15c95e0c3401f81b073ecd7133987c0220811a7c8876211dcc5f7a139d9471",
        "293d20551375c893577789c937ad6b86b2cf613f0e32caa8f3e2eab50a2038b4",
    ),
    "D06": (
        "c3a42297338a84e0dc9300a3d64100528c3e6d153ad6af6bd0837d0ecae27a4d",
        "b0db78f167cec78fe49992f71da187e2544c2c383adc2e9f1be37f1a577778f3",
    ),
    "D07": (
        "30f6ba1371908fde231b2f81ba989ccb7a141e1b4e19fe8c1f205b2d2b1a26cb",
        "018aa9885b7d9264170f0a413b815f4df6e5acbe3b9e8e10f3b99d9f0b979555",
    ),
}


@dataclass(frozen=True, slots=True)
class ExactnessBoundary:
    world_law: Status = Status.EXACT
    complete_generator: Status = Status.SEMANTICALLY_EQUIVALENT
    rng_algorithm: Status = Status.PARTIAL
    rng_state: Status = Status.PARTIAL
    seed_authority: Status = Status.EXACT
    rng_stream_construction: Status = Status.EXACT
    rng_draw_order: Status = Status.EXACT
    rng_substream_strategy: Status = Status.EXACT
    observation: Status = Status.EXACT
    schema: Status = Status.EXACT
    split_assignment: Status = Status.EXACT
    row_ordering: Status = Status.UNKNOWN
    serialization: Status = Status.SEMANTICALLY_EQUIVALENT
    dataset_hash: Status = Status.PARTIAL
    evaluation: Status = Status.PARTIAL
    model_configuration: Status = Status.DEFERRED_OUT_OF_SCOPE
    historical_result: Status = Status.DEFERRED_OUT_OF_SCOPE
    production_scorer: str = "UNIMPLEMENTED"
    research_metric: str = "six_cell_mean_cellwise_normalized_rmse (research-only)"


EXACTNESS_BOUNDARIES = {
    "SP04": ExactnessBoundary(
        complete_generator=Status.PARTIAL,
        observation=Status.PARTIAL,
    ),
    "SP05": ExactnessBoundary(),
    "SP06": ExactnessBoundary(),
}

BASELINE_PRE_EXPOSURE_HOURS = 2.0
CURRENT_EXPOSURE_TIME_HOURS = 0.0
PRIOR_COMPLETE_EPISODES = 4
TARGETS_PER_ROW = 2
CURRENT_EPISODE_EXPOSURES = (CURRENT_EXPOSURE_TIME_HOURS,)
NO_ADDITIONAL_EXPOSURE_THROUGH_H72 = True


@dataclass(frozen=True, slots=True)
class ObservedEpisode:
    baseline_force_n_per_kg: float
    baseline_impulse_m_per_s: float
    depth_m: float
    exposure: PublicExposure
    innovations: tuple[tuple[str, float, float], ...]

    def innovation(self, horizon: str, metric: str) -> float:
        for stored_horizon, force, impulse in self.innovations:
            if stored_horizon == horizon:
                if metric == "force":
                    return force
                if metric == "impulse":
                    return impulse
                break
        raise KeyError(f"no stored {metric} innovation for {horizon}")


@dataclass(frozen=True, slots=True)
class EpisodeRecord:
    participant_key: str
    episode_key: str
    query_keys: tuple[tuple[str, str], ...]
    training_age_years: float
    strength_index: float
    current: ObservedEpisode
    prior_episodes: tuple[ObservedEpisode, ObservedEpisode, ObservedEpisode, ObservedEpisode]
    camp_identity: str
    split: str
    camp_index: int
    participant_index: int

    def query_key(self, horizon: str) -> str:
        for stored_horizon, key in self.query_keys:
            if stored_horizon == horizon:
                return key
        raise KeyError(f"unknown query horizon: {horizon}")


def sample_baseline_depth(streams: KeyedRandomStreams, episode_slot: str) -> float:
    return float(streams.generator("baseline_depth_context", episode_slot).uniform(0.15, 0.45))


def _measure_assessment(
    observation: str,
    force_truth: float,
    impulse_truth: float,
    streams: KeyedRandomStreams,
    assessment_key: str,
) -> Any:
    if observation == "O03":
        from cmj_recovery_dynamics.observations.episode_summary import measure_scalar_assessment

        return measure_scalar_assessment(
            force_truth, impulse_truth, streams, assessment_key=assessment_key
        )
    from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
        measure_phase_consistent_assessment,
    )

    return measure_phase_consistent_assessment(
        force_truth, impulse_truth, streams, assessment_key=assessment_key
    )


def _observe_episode(
    streams: KeyedRandomStreams,
    *,
    specimen: str,
    episode_slot: str,
    baseline_force_truth: float,
    baseline_impulse_truth: float,
    depth_m: float,
    exposure: PublicExposure,
    participant_effects: Any,
    camp_effects: Any,
    discrepancy_channel: str,
) -> ObservedEpisode:
    from cmj_recovery_dynamics.dynamics.biexponential_episode_response import response_fraction
    from cmj_recovery_dynamics.observations.episode_summary import draw_episode_discrepancy

    observation = FORMULATIONS[specimen].observation
    world = FORMULATIONS[specimen].world
    baseline = _measure_assessment(
        observation,
        baseline_force_truth,
        baseline_impulse_truth,
        streams,
        f"{episode_slot}:dedicated_baseline",
    )
    discrepancy = draw_episode_discrepancy(streams, episode_slot, channel=discrepancy_channel)
    innovations: list[tuple[str, float, float]] = []
    for horizon, lag_hours in HORIZONS:
        force_truth = baseline_force_truth * (
            1.0
            + response_fraction(
                exposure, lag_hours, participant_effects, camp_effects, "force", world=world
            )
            + discrepancy[horizon]["force"]
        )
        impulse_truth = baseline_impulse_truth * (
            1.0
            + response_fraction(
                exposure, lag_hours, participant_effects, camp_effects, "impulse", world=world
            )
            + discrepancy[horizon]["impulse"]
        )
        if not (math.isfinite(force_truth) and force_truth > 0.0):
            raise RuntimeError(f"non-positive force criterion truth at {horizon}")
        if not (math.isfinite(impulse_truth) and impulse_truth > 0.0):
            raise RuntimeError(f"non-positive impulse criterion truth at {horizon}")
        criterion = _measure_assessment(
            observation,
            force_truth,
            impulse_truth,
            streams,
            f"{episode_slot}:criterion:{horizon}",
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


def generate_episode(
    *,
    specimen: str,
    split: str,
    camp_index: int,
    participant_index: int,
    root_seed: str = PUBLIC_ROOT_SEED,
) -> EpisodeRecord:
    """Generate one T02 episode and its four complete prior episode records."""
    if specimen not in FORMULATIONS:
        raise ValueError("specimen must be SP04, SP05, or SP06")
    if split not in SPLIT_GEOMETRY:
        raise ValueError("only the public train and validation splits are available")
    if camp_index < 0 or participant_index < 0:
        raise ValueError("camp and participant indexes must be non-negative")

    from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
        sample_camp_effects,
        sample_participant_context,
    )
    from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
        sample_correlated_exposure,
        sample_preliminary_exposure,
    )

    camp_streams = KeyedRandomStreams("lcmj-v2", root_seed, split, "camp", camp_index)
    participant_streams = camp_streams.child("participant", participant_index)
    camp_effects = sample_camp_effects(camp_streams)
    context = sample_participant_context(participant_streams)
    world = FORMULATIONS[specimen].world

    def sample_exposure(slot: str, *, prior: bool) -> PublicExposure:
        channel = "prior_episode_exposure" if prior else "current_exposure"
        if world == "W03":
            high_probability = 0.50 if prior else (0.30 if split == "train" else 0.70)
            return sample_preliminary_exposure(
                participant_streams,
                high_load_probability=high_probability,
                channel=channel,
                episode_key=slot,
            )
        from cmj_recovery_dynamics.dynamics.correlated_exposure_response import mixture_for

        return sample_correlated_exposure(
            participant_streams,
            archetype_probabilities=mixture_for(split, prior=prior),
            channel=channel,
            episode_key=slot,
        )

    prior: list[ObservedEpisode] = []
    for prior_index in range(PRIOR_COMPLETE_EPISODES):
        slot = f"prior_{prior_index}"
        prior.append(
            _observe_episode(
                participant_streams,
                specimen=specimen,
                episode_slot=slot,
                baseline_force_truth=context.baseline_force_n_per_kg,
                baseline_impulse_truth=context.baseline_impulse_m_per_s,
                depth_m=sample_baseline_depth(participant_streams, slot),
                exposure=sample_exposure(slot, prior=True),
                participant_effects=context.response_effects,
                camp_effects=camp_effects,
                discrepancy_channel="prior_episode_discrepancy",
            )
        )
    if len(prior) != PRIOR_COMPLETE_EPISODES:
        raise RuntimeError("T02 requires exactly four complete prior episodes")

    current = _observe_episode(
        participant_streams,
        specimen=specimen,
        episode_slot="current",
        baseline_force_truth=context.baseline_force_n_per_kg,
        baseline_impulse_truth=context.baseline_impulse_m_per_s,
        depth_m=sample_baseline_depth(participant_streams, "current"),
        exposure=sample_exposure("current", prior=False),
        participant_effects=context.response_effects,
        camp_effects=camp_effects,
        discrepancy_channel="current_discrepancy",
    )
    return EpisodeRecord(
        participant_key=participant_streams.opaque_key("participant", "group"),
        episode_key=participant_streams.opaque_key("episode", "current"),
        query_keys=tuple(
            (horizon, participant_streams.opaque_key("query", "current", horizon))
            for horizon, _ in HORIZONS
        ),
        training_age_years=context.training_age_years,
        strength_index=context.strength_index,
        current=current,
        prior_episodes=tuple(prior),  # type: ignore[arg-type]
        camp_identity=camp_streams.opaque_key("camp", "group"),
        split=split,
        camp_index=camp_index,
        participant_index=participant_index,
    )


def iter_public_members(split: str) -> Iterator[tuple[int, int]]:
    if split not in SPLIT_GEOMETRY:
        raise ValueError("only public train and validation split members are defined")
    for camp_index in range(SPLIT_GEOMETRY[split].camps):
        for participant_index in range(250):
            yield camp_index, participant_index


def iter_public_episodes(
    split: str, *, specimen: str, root_seed: str = PUBLIC_ROOT_SEED
) -> Iterator[EpisodeRecord]:
    for camp_index, participant_index in iter_public_members(split):
        yield generate_episode(
            specimen=specimen,
            split=split,
            camp_index=camp_index,
            participant_index=participant_index,
            root_seed=root_seed,
        )


def _validate_predictors(predictors: dict[str, Any]) -> dict[str, Any]:
    if set(predictors) != set(PREDICTOR_FIELDS):
        raise ValueError("R03 predictor row must contain exactly the 82 registered fields")
    output: dict[str, Any] = {}
    for field in PREDICTOR_FIELDS:
        value = predictors[field]
        if field == "horizon":
            if value not in {horizon for horizon, _ in HORIZONS}:
                raise ValueError("R03 horizon is unsupported")
            output[field] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field} must be numeric")
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f"{field} must be finite")
            if field.endswith("high_intensity_accel_count") or field.endswith(
                "high_intensity_decel_count"
            ):
                if not number.is_integer():
                    raise ValueError(f"{field} must be integer-valued")
                output[field] = int(number)
            else:
                output[field] = number
    return output


def project_episode(record: EpisodeRecord) -> list[dict[str, Any]]:
    """Project one episode to three R03 rows; alignment keys stay outside predictors."""
    prior_fields: dict[str, float | int] = {}
    for index, prior in enumerate(record.prior_episodes):
        prefix = f"prior_episode[{index}]."
        prior_fields.update(
            {
                f"{prefix}baseline.relative_mean_concentric_force": prior.baseline_force_n_per_kg,
                f"{prefix}baseline.relative_concentric_net_impulse": prior.baseline_impulse_m_per_s,
                f"{prefix}baseline.depth_m": prior.depth_m,
            }
        )
        prior_fields.update(
            {f"{prefix}exposure.{name}": value for name, value in prior.exposure.as_dict().items()}
        )
        for horizon, _ in HORIZONS:
            prior_fields[f"{prefix}{horizon}.relative_mean_concentric_force_innovation"] = (
                prior.innovation(horizon, "force")
            )
            prior_fields[f"{prefix}{horizon}.relative_concentric_net_impulse_innovation"] = (
                prior.innovation(horizon, "impulse")
            )

    current_fields: dict[str, Any] = {
        "baseline.relative_mean_concentric_force": record.current.baseline_force_n_per_kg,
        "baseline.relative_concentric_net_impulse": record.current.baseline_impulse_m_per_s,
        "baseline.depth_m": record.current.depth_m,
        "participant.training_age_years": record.training_age_years,
        "participant.strength_index": record.strength_index,
    }
    current_fields.update(
        {
            f"index_exposure.{name}": value
            for name, value in record.current.exposure.as_dict().items()
        }
    )
    current_fields.update(prior_fields)

    rows: list[dict[str, Any]] = []
    for horizon, _ in HORIZONS:
        predictor = _validate_predictors({**current_fields, "horizon": horizon})
        force = record.current.innovation(horizon, "force")
        impulse = record.current.innovation(horizon, "impulse")
        if not (math.isfinite(force) and math.isfinite(impulse)):
            raise ValueError("T02 labels must be finite")
        rows.append(
            {
                "participant_key": record.participant_key,
                "episode_key": record.episode_key,
                "query_key": record.query_key(horizon),
                **predictor,
                TARGET_FIELDS[0]: force,
                TARGET_FIELDS[1]: impulse,
            }
        )
    return rows


__all__ = [
    "BASELINE_FIELDS",
    "BASELINE_PRE_EXPOSURE_HOURS",
    "CURRENT_EXPOSURE_TIME_HOURS",
    "CURRENT_EPISODE_EXPOSURES",
    "DatasetGeometry",
    "EXACTNESS_BOUNDARIES",
    "EXPOSURE_FIELDS",
    "EXPOSURE_SUPPORTS",
    "ExactnessBoundary",
    "EpisodeRecord",
    "FORMULATIONS",
    "FormulationIdentity",
    "FormulationTransition",
    "HORIZONS",
    "KeyedRandomStreams",
    "NO_ADDITIONAL_EXPOSURE_THROUGH_H72",
    "ObservedEpisode",
    "PARTICIPANT_FIELDS",
    "PREDICTOR_BLOCK_GEOMETRY",
    "PREDICTOR_FIELDS",
    "PRIOR_COMPLETE_EPISODES",
    "PUBLIC_ROOT_SEED",
    "PublicExposure",
    "REFERENCE_DATASET_HASHES",
    "ROW_KEY_FIELDS",
    "ROW_ORDERING_STATUS",
    "RNG_VERSION",
    "RECOVERY_FIELDS",
    "SOURCE_CLOSURES",
    "SPLIT_GEOMETRY",
    "SourceClosure",
    "TARGET_FIELDS",
    "TRANSITIONS",
    "TARGETS_PER_ROW",
    "TARGET_UNITS",
    "generate_episode",
    "iter_public_episodes",
    "iter_public_members",
    "project_episode",
    "sample_baseline_depth",
]
