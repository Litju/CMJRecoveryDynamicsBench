"""Clean-room SP03/D04 W02, O02, R02, and E02 reproduction."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from cmj_recovery_dynamics.dynamics.fitness_fatigue_impulse_response import (
    DECREMENT_FLOOR_FRACTION,
    exposure_response_values,
)
from cmj_recovery_dynamics.metrics.scoring import (
    RICH_HISTORY_CELL_MIN_ROWS,
    RICH_HISTORY_CELLS,
    CellMetric,
    CellValues,
    RichHistoryAssessment,
    cellwise_normalized_rmse,
    rich_history_stratum,
    rich_history_target_metrics,
)
from cmj_recovery_dynamics.observations.rich_monitoring import (
    AssessmentMeasurements,
    AssessmentValidity,
    MeasurementModel,
    MonitoringAssessment,
    observe_assessments,
    observe_target,
    protocol_baseline,
)

Array = NDArray[Any]
PublicSplitName = Literal["public_train", "public_validation"]
_EMPTY_RECORD: Mapping[str, Any] = {}

# Scientific source authority; D04 materialization authority is recorded separately.
SP03_SOURCE_TREE = "e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b"
D04_DATA_PRODUCER_COMMIT = "6947771c8567438bba4cea8b5bb28d8f7992b307"
D04_DATA_PRODUCER_REPOSITORY_TREE = "c3c65d118cab0a368aafc7c1681a5660cd039bee"
D04_DATA_PRODUCER_TASK_TREE = "88e0cf68aa7fda864505a2a7e353e0487187919e"
D04_MANIFEST_BLOB_OID = "03864b433e678e582da3d50d66468443a77cba71"
D04_TRAIN_PARQUET_BLOB_OID = "8b789399f8b40feef3a02aff98eb9a86d193f335"
D04_VALIDATION_PARQUET_BLOB_OID = "d2987e1e349986319eeb01cc46972e0bae9c158c"
ALI490_RNG_CHANNELIZATION_COMMIT = "ad5e48a1dc9c1fd1e27ecd314940a9be1b4fd50a"
SP03_SOURCE_CLOSURE = (
    "environment/Dockerfile",
    "data_generation/src/lcmj_v3/core.py",
    "data_generation/src/lcmj_v3/families.py",
    "data_generation/src/lcmj_v3/measurement.py",
    "data_generation/src/lcmj_v3/params.py",
    "data_generation/src/lcmj_v3/projection.py",
    "data_generation/src/lcmj_v3/rng.py",
    "data_generation/src/lcmj_v3/schedule.py",
    "data_generation/src/lcmj_v3/splits.py",
    "data_generation/authority/parameters_v3.json",
    "data_generation/tests/test_ali488_source_repair.py",
    "data_generation/tests/test_ali490_rng_channels.py",
    "data_generation/tests/test_pipeline_v3.py",
    "data/canonical_v3.py",
    "data/public/manifest.json",
)
GENERATOR_VERSION = "LCMJ-V3-monitored-multicycle-1.1"


@dataclass(frozen=True, slots=True)
class RichHistoryReproductionMetadata:
    source_tree: str
    d04_data_producer_commit: str
    d04_data_producer_task_tree: str
    d04_manifest_blob_oid: str
    d04_train_parquet_blob_oid: str
    d04_validation_parquet_blob_oid: str
    d04_seed_construction: str
    d04_rng_topology: str
    d04_horizon_presence_draws: str
    d04_runtime_authority: str
    later_rng_channelization_commit: str
    generator_claim: str
    historical_rng_algorithm: str
    historical_rng_state: str
    seed_authority: str
    rng_stream_construction: str
    rng_draw_order: str
    rng_substream_strategy: str
    split_assignment: str
    row_ordering: str
    serialization: str
    dataset_hash: str
    oss_numpy_version: str
    oss_default_rng_bit_generator: str
    historical_calibration_reference: str


RICH_HISTORY_REPRODUCTION_METADATA = RichHistoryReproductionMetadata(
    source_tree=SP03_SOURCE_TREE,
    d04_data_producer_commit=D04_DATA_PRODUCER_COMMIT,
    d04_data_producer_task_tree=D04_DATA_PRODUCER_TASK_TREE,
    d04_manifest_blob_oid=D04_MANIFEST_BLOB_OID,
    d04_train_parquet_blob_oid=D04_TRAIN_PARQUET_BLOB_OID,
    d04_validation_parquet_blob_oid=D04_VALIDATION_PARQUET_BLOB_OID,
    d04_seed_construction=(
        "roots l05-public-train-v3/l05-public-validation-v3; SHA-256 of compact JSON string "
        "parts, first 8 bytes big-endian; np.random.default_rng(seed)"
    ),
    d04_rng_topology=(
        "one shared Generator per camp, consumed sequentially through horizon admission"
    ),
    d04_horizon_presence_draws=(
        "random(n) < 0.15, then integers(0, 2, n), from that same camp Generator"
    ),
    d04_runtime_authority=(
        "Dockerfile base tag runtime-ml-core-py313-local only; exact Python build, NumPy version, "
        "and BitGenerator unbound"
    ),
    later_rng_channelization_commit=ALI490_RNG_CHANNELIZATION_COMMIT,
    generator_claim="SEMANTICALLY_EQUIVALENT",
    historical_rng_algorithm="PARTIAL",
    historical_rng_state="PARTIAL",
    seed_authority="EXACT",
    rng_stream_construction="EXACT",
    rng_draw_order="EXACT",
    rng_substream_strategy="EXACT",
    split_assignment="PARTIAL",
    row_ordering="UNKNOWN",
    serialization="SEMANTICALLY_EQUIVALENT",
    dataset_hash="PARTIAL",
    oss_numpy_version=np.__version__,
    oss_default_rng_bit_generator=np.random.default_rng(0).bit_generator.__class__.__name__,
    historical_calibration_reference="UNAVAILABLE",
)


@dataclass(frozen=True, slots=True)
class HiddenDesignCounts:
    participants: int = 1152
    camps: int = 144
    origins: int = 2304
    materialization: str = "NOT_RECOVERED"


HISTORICAL_HIDDEN_DESIGN = HiddenDesignCounts()


@dataclass(frozen=True, slots=True)
class SchemaSpec:
    K_MAX: int = 6
    A_MAX: int = 14
    P_MAX: int = 3
    expect_all_slots_used: bool = True
    horizons: tuple[str, str] = ("H72", "D7")
    target_windows: tuple[tuple[float, float], tuple[float, float]] = (
        (66.0, 78.0),
        (156.0, 180.0),
    )


@dataclass(frozen=True, slots=True)
class KineticsPrior:
    level_force_mean: float = 25.0
    level_force_strength_slope: float = 1.5
    level_force_sd: float = 3.5
    level_impulse_mean: float = 2.70
    level_impulse_strength_slope: float = 0.12
    level_impulse_sd: float = 0.25
    amp_force_base: float = 1.25
    amp_force_strength_slope: float = 0.15
    amp_force_log_sd: float = 0.30
    amp_impulse_ratio_mean: float = 0.075
    amp_impulse_ratio_sd: float = 0.015
    fatigue_ratio_median: float = 3.5
    fatigue_ratio_strength_slope: float = -0.10
    fatigue_ratio_log_sd: float = 0.30
    fatigue_ratio_bounds: tuple[float, float] = (1.5, 5.0)
    fatigue_ratio_load_slope: float = 0.35
    fatigue_ratio_load_clip: tuple[float, float] = (0.6, 1.6)
    tau_fast_median_h: float = 66.0
    tau_fast_strength_slope: float = -0.15
    tau_fast_age_slope: float = -0.02
    tau_fast_log_sd: float = 0.30
    tau_fast_bounds_h: tuple[float, float] = (36.0, 110.0)
    tau_slow_median_h: float = 160.0
    tau_slow_log_sd: float = 0.25
    tau_slow_bounds_h: tuple[float, float] = (100.0, 260.0)
    state_floor_fraction: float = 0.38
    training_age_range_y: tuple[float, float] = (1.0, 12.0)
    pref_depth_range_m: tuple[float, float] = (0.20, 0.40)


@dataclass(frozen=True, slots=True)
class DoseModel:
    omega: tuple[tuple[str, float], ...] = (
        ("training", 1.0),
        ("match", 1.30),
        ("friendly", 1.15),
    )
    hill_kappa: float = 2.2
    hill_delta: float = 1.0
    hill_gamma: float = 2.0
    acc_depth: float = 0.45
    acc_bouts_scale: float = 3.0
    bouts_range: tuple[int, int] = (0, 8)


@dataclass(frozen=True, slots=True)
class ScheduleModel:
    window_range_h: tuple[float, float] = (504.0, 672.0)
    exposure_min_gap_h: float = 48.0
    exposure_kind_probs: tuple[tuple[str, float], ...] = (
        ("training", 0.6),
        ("match", 0.3),
        ("friendly", 0.1),
    )
    exposure_c_range: tuple[float, float] = (0.5, 1.5)
    k_range_dense: tuple[int, int] = (5, 6)
    k_range_sparse: tuple[int, int] = (3, 4)
    index_kind_probs: tuple[tuple[str, float], ...] = (("match", 0.7), ("training", 0.3))
    index_c_range: tuple[float, float] = (0.6, 1.4)
    plan_count_range: tuple[int, int] = (0, 3)
    plan_time_range_h: tuple[float, float] = (24.0, 160.0)
    plan_kind_probs: tuple[tuple[str, float], ...] = (("training", 0.85), ("friendly", 0.15))
    plan_c_range: tuple[float, float] = (0.5, 1.4)
    plan_eta_range: tuple[float, float] = (0.92, 1.0)
    assess_latest_h: float = 6.0
    assess_min_gap_h: float = 8.0
    monitor_window_h: tuple[float, float] = (14.0, 40.0)
    second_monitor_window_h: tuple[float, float] = (60.0, 84.0)
    monitor_second: bool = True
    baseline_opportunity_count: int = 2
    last_exposure_age_bands_h: tuple[tuple[float, float], tuple[float, float]] = (
        (16.0, 44.0),
        (48.0, 220.0),
    )
    trials_range_high: tuple[int, int] = (2, 3)
    trials_range_low: tuple[int, int] = (1, 3)
    baseline_window_h: tuple[float, float] = (-240.0, -24.0)
    baseline_recovered_gap_h: float = 60.0
    baseline_opportunity_exposure_gap_h: float = 80.0
    baseline_opportunity_final_exposure_buffer_h: float = 8.0
    single_horizon_rate: float = 0.15
    origin_spacing_min_h: float = 336.0


@dataclass(frozen=True, slots=True)
class CampRegimeTable:
    p_dense: float = 0.55
    p_quality_high: float = 0.55
    intensity_probs: tuple[float, float, float] = (0.33, 0.34, 0.33)
    heterogeneity_probs: tuple[float, float] = (0.7, 0.3)
    heterogeneity_levels: tuple[float, float] = (1.0, 1.15)
    monitor_p_high: float = 0.9
    monitor_p_low: float = 0.6
    last_age_band_probs: tuple[float, float] = (0.40, 0.60)


TRAIN_TABLE = CampRegimeTable()
VALIDATION_TABLE = CampRegimeTable(
    p_dense=0.60,
    p_quality_high=0.50,
    intensity_probs=(0.30, 0.40, 0.30),
    heterogeneity_probs=(0.6, 0.4),
    last_age_band_probs=(0.45, 0.55),
)


@dataclass(frozen=True, slots=True)
class SplitSpec:
    name: PublicSplitName
    root_seed: str
    key_namespace: str
    camps: int
    participants_per_camp: int = 8
    origins_per_participant: int = 2
    table: CampRegimeTable = TRAIN_TABLE


PUBLIC_SPLITS: Mapping[PublicSplitName, SplitSpec] = {
    "public_train": SplitSpec(
        "public_train", "l05-public-train-v3", "public-v3", camps=512, table=TRAIN_TABLE
    ),
    "public_validation": SplitSpec(
        "public_validation",
        "l05-public-validation-v3",
        "public-v3",
        camps=128,
        table=VALIDATION_TABLE,
    ),
}


@dataclass(frozen=True, slots=True)
class Parameters:
    schema: SchemaSpec = SchemaSpec()
    kinetics: KineticsPrior = KineticsPrior()
    dose: DoseModel = DoseModel()
    measurement: MeasurementModel = MeasurementModel()
    schedule: ScheduleModel = ScheduleModel()
    generator_version: str = GENERATOR_VERSION


DEFAULT = Parameters()
F2_LEVELS = ("L0", "L1", "L2")
F3_LEVELS = ("clean", "degraded")
F3_CLEAN_MIN_VALID = 6
F3_CLEAN_MIN_TRIALS = 2


@dataclass(frozen=True, slots=True)
class FieldBlock:
    name: str
    fields: tuple[str, ...]


ASSESSMENT_FIELDS = (
    "time_from_origin_hours",
    "relative_mean_concentric_force",
    "relative_concentric_net_impulse",
    "depth_m",
    "n_trials",
    "validity_state",
)
EXPOSURE_FIELDS = ("time_from_origin_hours", "event_kind", "duration_minutes", "c_context")
INDEX_FIELDS = ("event_kind", "duration_minutes", "c_context")
PLAN_FIELDS = (
    "time_from_origin_hours",
    "event_kind",
    "planned_duration_minutes",
    "planned_c_context",
)


def _field_names() -> tuple[str, ...]:
    fields = [
        "horizon",
        "target_time_hours",
        "target_window_low",
        "target_window_high",
        "baseline_force",
        "baseline_impulse",
        "participant.training_age_years",
        "participant.strength_index",
        "participant.bouts_prior_4wk",
        "n_assessments",
    ]
    fields.extend(
        f"history_assessment[{slot}].{name}"
        for slot in range(DEFAULT.schema.A_MAX)
        for name in ASSESSMENT_FIELDS
    )
    fields.append("n_history_exposures")
    fields.extend(
        f"history_exposure[{slot}].{name}"
        for slot in range(DEFAULT.schema.K_MAX)
        for name in EXPOSURE_FIELDS
    )
    fields.extend(f"index_exposure.{name}" for name in INDEX_FIELDS)
    fields.append("n_plan")
    fields.extend(
        f"known_plan[{slot}].{name}" for slot in range(DEFAULT.schema.P_MAX) for name in PLAN_FIELDS
    )
    return tuple(fields)


R02_FIELD_NAMES = _field_names()
_QUERY_FIELDS = (
    "horizon",
    "target_time_hours",
    "target_window_low",
    "target_window_high",
    "baseline_force",
    "baseline_impulse",
)
_PARTICIPANT_FIELDS = (
    "participant.training_age_years",
    "participant.strength_index",
    "participant.bouts_prior_4wk",
)
R02_FIELD_BLOCKS = (
    FieldBlock("query_and_baseline", _QUERY_FIELDS),
    FieldBlock("participant_context", _PARTICIPANT_FIELDS),
    FieldBlock("assessment_count", ("n_assessments",)),
    FieldBlock(
        "assessment_slots",
        tuple(field for field in R02_FIELD_NAMES if field.startswith("history_assessment[")),
    ),
    FieldBlock("exposure_count", ("n_history_exposures",)),
    FieldBlock(
        "prior_exposure_slots",
        tuple(field for field in R02_FIELD_NAMES if field.startswith("history_exposure[")),
    ),
    FieldBlock(
        "index_exposure",
        tuple(field for field in R02_FIELD_NAMES if field.startswith("index_exposure.")),
    ),
    FieldBlock("known_plan_count", ("n_plan",)),
    FieldBlock(
        "known_plan_slots",
        tuple(field for field in R02_FIELD_NAMES if field.startswith("known_plan[")),
    ),
)
CATEGORICAL_FIELDS = frozenset(
    {"horizon", "index_exposure.event_kind"}
    | {f"history_assessment[{i}].validity_state" for i in range(DEFAULT.schema.A_MAX)}
    | {f"history_exposure[{i}].event_kind" for i in range(DEFAULT.schema.K_MAX)}
    | {f"known_plan[{i}].event_kind" for i in range(DEFAULT.schema.P_MAX)}
)
NUMERIC_FIELDS = tuple(field for field in R02_FIELD_NAMES if field not in CATEGORICAL_FIELDS)
HORIZON_TARGET_COLUMNS = (
    "label.relative_mean_concentric_force_innovation",
    "label.relative_concentric_net_impulse_innovation",
)
PUBLIC_GROUPING_COLUMNS = ("participant_key", "origin_key", "query_key")
SCHEMA_IDENTITY = "LCMJ-V3-CANONICAL-HORIZON-ROW-1.1"
MISSING = "<MISSING>"
SCHEMA_DESCRIPTOR = {
    "schema_identity": SCHEMA_IDENTITY,
    "field_names": list(R02_FIELD_NAMES),
    "categorical_fields": sorted(CATEGORICAL_FIELDS),
    "target_columns": [
        "relative_mean_concentric_force_innovation",
        "relative_concentric_net_impulse_innovation",
    ],
    "horizons": ["H72", "D7"],
    "slots": {"K_MAX": 6, "A_MAX": 14, "P_MAX": 3},
}
SCHEMA_DIGEST = hashlib.sha256(
    json.dumps(SCHEMA_DESCRIPTOR, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def _number(value: Any) -> float:
    if value is None:
        return math.nan
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"numeric R02 field received {value!r}") from exc


def _category(value: object) -> str:
    if value is None:
        return MISSING
    category = str(value)
    return MISSING if category in ("", "nan", "None") else category


def flatten_r02_record(record: Mapping[str, Any]) -> dict[str, object]:
    """Flatten the exact 135-field nested public record."""
    features: Mapping[str, Any] = record["public_features"]
    output: dict[str, object] = {}
    horizon = _category(record["horizon"])
    output["horizon"] = horizon
    output["target_time_hours"] = _number(record["target_time_hours"])
    raw_window = record.get("target_window_hours")
    window_values = (
        cast(Mapping[str, Any], raw_window) if isinstance(raw_window, Mapping) else _EMPTY_RECORD
    )
    default_window = (66.0, 78.0) if horizon == "H72" else (156.0, 180.0)
    output["target_window_low"] = _number(window_values.get("low", default_window[0]))
    output["target_window_high"] = _number(window_values.get("high", default_window[1]))
    baseline: Mapping[str, Any] = record["baseline"]
    output["baseline_force"] = _number(baseline["relative_mean_concentric_force"])
    output["baseline_impulse"] = _number(baseline["relative_concentric_net_impulse"])
    participant: Mapping[str, Any] = features.get("participant") or {}
    output["participant.training_age_years"] = _number(participant.get("training_age_years"))
    output["participant.strength_index"] = _number(participant.get("strength_index"))
    output["participant.bouts_prior_4wk"] = _number(participant.get("bouts_prior_4wk"))

    assessments = list(
        cast(Sequence[Mapping[str, Any]], features.get("history_assessments") or ())
    )[: DEFAULT.schema.A_MAX]
    output["n_assessments"] = float(len(assessments))
    for slot in range(DEFAULT.schema.A_MAX):
        item = assessments[slot] if slot < len(assessments) else _EMPTY_RECORD
        for name in ASSESSMENT_FIELDS:
            field_name = f"history_assessment[{slot}].{name}"
            output[field_name] = (
                _category(item.get(name)) if name == "validity_state" else _number(item.get(name))
            )

    exposures = list(cast(Sequence[Mapping[str, Any]], features.get("history_exposures") or ()))[
        : DEFAULT.schema.K_MAX
    ]
    output["n_history_exposures"] = float(len(exposures))
    for slot in range(DEFAULT.schema.K_MAX):
        item = exposures[slot] if slot < len(exposures) else _EMPTY_RECORD
        for name in EXPOSURE_FIELDS:
            field_name = f"history_exposure[{slot}].{name}"
            output[field_name] = (
                _category(item.get(name)) if name == "event_kind" else _number(item.get(name))
            )

    index = cast(Mapping[str, Any], features.get("index_exposure") or _EMPTY_RECORD)
    for name in INDEX_FIELDS:
        output[f"index_exposure.{name}"] = (
            _category(index.get(name)) if name == "event_kind" else _number(index.get(name))
        )

    plans = list(cast(Sequence[Mapping[str, Any]], features.get("known_plan") or ()))[
        : DEFAULT.schema.P_MAX
    ]
    output["n_plan"] = float(len(plans))
    for slot in range(DEFAULT.schema.P_MAX):
        item = plans[slot] if slot < len(plans) else _EMPTY_RECORD
        for name in PLAN_FIELDS:
            field_name = f"known_plan[{slot}].{name}"
            output[field_name] = (
                _category(item.get(name)) if name == "event_kind" else _number(item.get(name))
            )
    return validate_r02_row(output)


def validate_r02_row(row: Mapping[str, object]) -> dict[str, object]:
    missing = [name for name in R02_FIELD_NAMES if name not in row]
    if missing:
        raise ValueError(f"R02 row is missing {len(missing)} fields, e.g. {missing[:3]}")
    output: dict[str, object] = {}
    for name in R02_FIELD_NAMES:
        output[name] = _category(row[name]) if name in CATEGORICAL_FIELDS else _number(row[name])
    if output["horizon"] not in ("H72", "D7"):
        raise ValueError(f"unknown rich-history horizon {output['horizon']!r}")
    return output


STREAM_CHANNELS = (
    "camp_regime",
    "participant_training_age",
    "participant_strength_index",
    "participant_prior_bouts",
    "participant_kinetics",
    "participant_preferred_depth",
    "exposure_count",
    "latest_exposure_band",
    "latest_exposure_age",
    "history_window_length",
    "prior_exposure_timing",
    "exposure_kind",
    "exposure_dose",
    "monitoring_opportunity_presence",
    "monitoring_opportunity_timing",
    "routine_assessment_trial_count",
    "index_exposure_kind",
    "index_exposure_dose",
    "known_plan_count",
    "known_plan_time",
    "known_plan_kind",
    "known_plan_dose",
    "known_plan_eta",
    "history_assessment_depth_context",
    "history_assessment_force_noise",
    "history_assessment_impulse_noise",
    "history_assessment_validity",
    "history_assessment_invalid_scale",
    "history_assessment_missingness",
    "target_time_H72",
    "target_time_D7",
    "horizon_single_presence",
    "horizon_dropped_index",
    "target_depth_context",
    "target_force_noise",
    "target_impulse_noise",
)


def seed_from(*parts: object) -> int:
    payload = json.dumps([str(part) for part in parts], separators=(",", ":")).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def rng_for(root_seed: str, split: str, *parts: object) -> np.random.Generator:
    return np.random.default_rng(seed_from(root_seed, split, *parts))


class RandomStreams:
    """Camp-rooted named streams, with local participant keys on two trait channels."""

    def __init__(self, *identity: object) -> None:
        if not identity:
            raise ValueError("a structural RNG identity is required")
        payload = json.dumps([str(part) for part in identity], separators=(",", ":")).encode(
            "utf-8"
        )
        self.identity = tuple(str(part) for part in identity)
        self.root_seed = hashlib.sha256(b"lcmj-v3-rng-root\0" + payload).hexdigest()

    @classmethod
    def from_generator(
        cls, generator: np.random.Generator, namespace: str = "legacy-generator"
    ) -> RandomStreams:
        return cls(namespace, int(generator.bit_generator.random_raw()))

    def generator(self, channel: str, *keys: object) -> np.random.Generator:
        if channel not in STREAM_CHANNELS:
            raise KeyError(f"unregistered RNG channel: {channel}")
        return rng_for(self.root_seed, "lcmj-v3", channel, *keys)


def opaque_key(namespace: str, kind: str, *parts: object) -> str:
    payload = json.dumps([str(part) for part in parts]).encode()
    digest = hashlib.sha256(
        ("lcmj-v3-key\0" + namespace + "\0" + kind + "\0").encode() + payload
    ).hexdigest()
    return f"{kind}-{digest[:32]}"


def _weighted_choice(
    rng: np.random.Generator, weights: tuple[tuple[str, float], ...], size: Any
) -> Array:
    names = [name for name, _ in weights]
    probabilities = np.asarray([weight for _, weight in weights], dtype=float)
    probabilities /= probabilities.sum()
    return np.asarray(names, dtype=object)[rng.choice(len(names), size=size, p=probabilities)]


def _uniform(
    rng: np.random.Generator, bounds: tuple[float, float], size: int | tuple[int, ...]
) -> Array:
    low, high = bounds
    return low + (high - low) * rng.random(size)


@dataclass(frozen=True, slots=True)
class CampRegime:
    dense: bool
    quality_high: bool
    intensity_scale: float
    heterogeneity: float
    monitor_probability: float
    last_age_band_probabilities: tuple[float, float]


def draw_camp_regime(rng: np.random.Generator, table: CampRegimeTable) -> CampRegime:
    quality_high = bool(rng.random() < table.p_quality_high)
    dense = bool(rng.random() < table.p_dense)
    intensity_index = int(
        rng.choice(3, p=np.asarray(table.intensity_probs) / np.sum(table.intensity_probs))
    )
    heterogeneity_index = int(
        rng.choice(
            2,
            p=np.asarray(table.heterogeneity_probs) / np.sum(table.heterogeneity_probs),
        )
    )
    age_probs = np.asarray(table.last_age_band_probs, dtype=float)
    age_probs /= age_probs.sum()
    return CampRegime(
        dense,
        quality_high,
        (0.85, 1.0, 1.15)[intensity_index],
        table.heterogeneity_levels[heterogeneity_index],
        table.monitor_p_high if quality_high else table.monitor_p_low,
        (float(age_probs[0]), float(age_probs[1])),
    )


@dataclass(frozen=True, slots=True)
class ParticipantTraits:
    training_age: Array
    strength_index: Array
    bouts_prior_4wk: Array
    level_force: Array
    level_impulse: Array
    amplitude_force: Array
    amplitude_impulse: Array
    response_ratio: Array
    tau_fast: Array
    tau_slow: Array
    preferred_depth: Array


def parameterize_participants(
    training_age: ArrayLike,
    strength_index: ArrayLike,
    heterogeneity: float,
    normal_draws: ArrayLike,
    *,
    preferred_depth: ArrayLike | None = None,
    bouts_prior_4wk: ArrayLike | None = None,
    parameters: Parameters = DEFAULT,
) -> ParticipantTraits:
    """Apply the exact shared-normal correlation and clipped kinetic priors."""
    prior = parameters.kinetics
    age = np.asarray(training_age, dtype=float)
    strength = np.asarray(strength_index, dtype=float)
    errors = np.asarray(normal_draws, dtype=float)
    if errors.shape != age.shape + (7,) or strength.shape != age.shape:
        raise ValueError("participant covariates and seven kinetic draws must align")
    if not math.isfinite(heterogeneity) or heterogeneity <= 0:
        raise ValueError("camp heterogeneity must be finite and positive")
    if preferred_depth is None:
        preferred = np.full(age.shape, np.nan, dtype=float)
    else:
        preferred = np.asarray(preferred_depth, dtype=float)
    if bouts_prior_4wk is None:
        bouts = np.full(age.shape, np.nan, dtype=float)
    else:
        bouts = np.asarray(bouts_prior_4wk, dtype=float)

    force_level = (
        prior.level_force_mean
        + prior.level_force_strength_slope * strength
        + prior.level_force_sd * errors[..., 0]
    )
    impulse_level = (
        prior.level_impulse_mean
        + prior.level_impulse_strength_slope * strength
        + prior.level_impulse_sd * (0.6 * errors[..., 0] + 0.8 * errors[..., 1])
    )
    amp_force = prior.amp_force_base * np.exp(
        prior.amp_force_strength_slope * strength
        + prior.amp_force_log_sd * heterogeneity * errors[..., 2]
    )
    amp_impulse = amp_force * (
        prior.amp_impulse_ratio_mean + prior.amp_impulse_ratio_sd * errors[..., 3]
    )
    ratio = np.clip(
        np.exp(
            np.log(prior.fatigue_ratio_median)
            + prior.fatigue_ratio_strength_slope * strength
            + prior.fatigue_ratio_log_sd * heterogeneity * errors[..., 4]
        ),
        *prior.fatigue_ratio_bounds,
    )
    tau_fast = np.clip(
        np.exp(
            np.log(prior.tau_fast_median_h)
            + prior.tau_fast_strength_slope * strength
            + prior.tau_fast_age_slope * (age - 6.0)
            + prior.tau_fast_log_sd * heterogeneity * errors[..., 5]
        ),
        *prior.tau_fast_bounds_h,
    )
    tau_slow = np.clip(
        np.exp(
            np.log(prior.tau_slow_median_h) + prior.tau_slow_log_sd * heterogeneity * errors[..., 6]
        ),
        *prior.tau_slow_bounds_h,
    )
    return ParticipantTraits(
        age,
        strength,
        bouts,
        force_level,
        impulse_level,
        amp_force,
        amp_impulse,
        ratio,
        tau_fast,
        tau_slow,
        preferred,
    )


def draw_participants(
    streams: RandomStreams,
    count: int,
    heterogeneity: float,
    parameters: Parameters = DEFAULT,
) -> ParticipantTraits:
    prior = parameters.kinetics
    age = streams.generator("participant_training_age").uniform(
        *prior.training_age_range_y, size=count
    )
    strength = streams.generator("participant_strength_index").normal(0.0, 1.0, count)
    errors = np.stack(
        [streams.generator("participant_kinetics", index).normal(size=7) for index in range(count)]
    )
    depth = np.asarray(
        [
            streams.generator("participant_preferred_depth", index).uniform(
                *prior.pref_depth_range_m
            )
            for index in range(count)
        ],
        dtype=float,
    )
    bouts = (
        streams.generator("participant_prior_bouts")
        .integers(parameters.dose.bouts_range[0], parameters.dose.bouts_range[1] + 1, count)
        .astype(float)
    )
    return parameterize_participants(
        age,
        strength,
        heterogeneity,
        errors,
        preferred_depth=depth,
        bouts_prior_4wk=bouts,
        parameters=parameters,
    )


def _repeat_traits(traits: ParticipantTraits, repeats: int) -> ParticipantTraits:
    return ParticipantTraits(
        *(
            np.repeat(getattr(traits, field), repeats)
            for field in ParticipantTraits.__dataclass_fields__
        )
    )


@dataclass(frozen=True, slots=True)
class CampSchedule:
    exposure_count: Array
    window_h: Array
    exposure_times: Array
    exposure_kinds: Array
    exposure_contexts: Array
    index_kinds: Array
    index_contexts: Array
    plan_count: Array
    plan_times: Array
    plan_contexts: Array
    plan_kinds: Array
    plan_execution: Array
    assessment_count: Array
    assessment_times: Array
    assessment_present: Array
    assessment_trials: Array
    baseline_opportunity_times: Array


def draw_schedule(
    streams: RandomStreams,
    count: int,
    regime: CampRegime,
    parameters: Parameters = DEFAULT,
) -> CampSchedule:
    schema, schedule = parameters.schema, parameters.schedule
    low_k, high_k = schedule.k_range_dense if regime.dense else schedule.k_range_sparse
    exposure_count = streams.generator("exposure_count").integers(low_k, high_k + 1, count)
    bands = np.asarray(schedule.last_exposure_age_bands_h, dtype=float)
    band_index = streams.generator("latest_exposure_band").choice(
        len(bands), size=count, p=np.asarray(regime.last_age_band_probabilities, dtype=float)
    )
    age_draw = streams.generator("latest_exposure_age").random(count)
    latest_age = bands[band_index, 0] + age_draw * (bands[band_index, 1] - bands[band_index, 0])
    required_window = (
        latest_age
        + 24.0
        + schedule.baseline_opportunity_exposure_gap_h
        + schedule.exposure_min_gap_h * (exposure_count - 2)
    )
    window_floor = np.maximum(schedule.window_range_h[0], required_window)
    if np.any(window_floor > schedule.window_range_h[1]):
        raise ValueError("frozen history window cannot fit the baseline opportunity schedule")
    window_draw = streams.generator("history_window_length").random(count)
    window = window_floor + window_draw * (schedule.window_range_h[1] - window_floor)

    exposure_times = np.full((count, schema.K_MAX), np.nan)
    exposure_kinds = np.full((count, schema.K_MAX), "", dtype=object)
    exposure_contexts = np.full((count, schema.K_MAX), np.nan)
    assessment_times = np.full((count, schema.A_MAX), np.nan)
    baseline_times = np.full((count, schedule.baseline_opportunity_count), np.nan)
    prior_draws = streams.generator("prior_exposure_timing").random(
        (count, max(schema.K_MAX - 1, 1))
    )

    for origin in range(count):
        k = int(exposure_count[origin])
        latest = -latest_age[origin]
        lower = -window[origin] + 24.0
        if schedule.baseline_opportunity_count != 2:
            raise ValueError("the source schedule requires exactly two baseline opportunities")
        prior_count = k - 1
        prior_upper = latest - schedule.baseline_opportunity_exposure_gap_h
        start_upper = prior_upper - schedule.exposure_min_gap_h * (prior_count - 1)
        if start_upper < lower - 1e-9:
            raise ValueError("baseline opportunity gap is infeasible for this exposure window")
        prior_starts = np.sort(lower + prior_draws[origin, :prior_count] * (start_upper - lower))
        prior_exposures = prior_starts + schedule.exposure_min_gap_h * np.arange(prior_count)
        times = np.concatenate([prior_exposures, [latest]])
        exposure_times[origin, :k] = times
        pair_end = min(
            schedule.baseline_window_h[1],
            latest - schedule.baseline_opportunity_final_exposure_buffer_h,
        )
        pair_first = pair_end - schedule.assess_min_gap_h
        if (
            pair_first < schedule.baseline_window_h[0]
            or pair_first - times[-2] < schedule.baseline_recovered_gap_h
        ):
            raise ValueError("scheduled baseline opportunities violate the recovery rule")
        baseline_times[origin] = (pair_first, pair_end)

    kind_rng = streams.generator("exposure_kind")
    exposure_kinds_draw = _weighted_choice(
        kind_rng, schedule.exposure_kind_probs, (count, schema.K_MAX)
    )
    exposure_dose_draw = _uniform(
        streams.generator("exposure_dose"), schedule.exposure_c_range, (count, schema.K_MAX)
    )
    for origin, raw_count in enumerate(exposure_count):
        k = int(raw_count)
        exposure_kinds[origin, :k] = exposure_kinds_draw[origin, :k]
        exposure_contexts[origin, :k] = exposure_dose_draw[origin, :k] * regime.intensity_scale

    opportunity_shape = (count, schema.K_MAX, 2)
    opportunity_presence = (
        streams.generator("monitoring_opportunity_presence").random(opportunity_shape)
        < regime.monitor_probability
    )
    opportunity_timing = streams.generator("monitoring_opportunity_timing").random(
        opportunity_shape
    )
    monitoring_windows = (schedule.monitor_window_h, schedule.second_monitor_window_h)
    safe_exposure_times = np.where(np.isfinite(exposure_times), exposure_times, 0.0)
    for origin in range(count):
        k = int(exposure_count[origin])
        monitoring: list[float] = []
        for event in range(k):
            for slot, bounds in enumerate(monitoring_windows):
                if slot == 1 and not schedule.monitor_second:
                    continue
                if opportunity_presence[origin, event, slot]:
                    monitoring.append(
                        safe_exposure_times[origin, event]
                        + bounds[0]
                        + opportunity_timing[origin, event, slot] * (bounds[1] - bounds[0])
                    )
        reserved = baseline_times[origin].tolist()
        monitoring = [
            time
            for time in monitoring
            if all(abs(time - fixed) >= schedule.assess_min_gap_h - 1e-9 for fixed in reserved)
        ]
        available = np.sort(
            np.asarray(
                [time for time in monitoring + reserved if time < -schedule.assess_latest_h],
                dtype=float,
            )
        )
        kept: list[float] = [float(available[0])] if len(available) else []
        for time in available[1:]:
            if time - kept[-1] >= schedule.assess_min_gap_h - 1e-9:
                kept.append(float(time))
        kept = kept[: schema.A_MAX]
        assessment_times[origin, : len(kept)] = kept

    assessment_present = np.isfinite(assessment_times)
    assessment_count = assessment_present.sum(axis=1)
    trial_bounds = schedule.trials_range_high if regime.quality_high else schedule.trials_range_low
    trial_draw = streams.generator("routine_assessment_trial_count").random((count, schema.A_MAX))
    assessment_trials = trial_bounds[0] + np.floor(
        trial_draw * (trial_bounds[1] - trial_bounds[0] + 1)
    ).astype(int)
    assessment_trials = np.where(assessment_present, assessment_trials, 0)

    index_kinds = _weighted_choice(
        streams.generator("index_exposure_kind"), schedule.index_kind_probs, count
    )
    index_contexts = (
        _uniform(streams.generator("index_exposure_dose"), schedule.index_c_range, count)
        * regime.intensity_scale
    )
    plan_count = streams.generator("known_plan_count").integers(
        schedule.plan_count_range[0], schedule.plan_count_range[1] + 1, count
    )
    plan_time_draw = _uniform(
        streams.generator("known_plan_time"), schedule.plan_time_range_h, (count, schema.P_MAX)
    )
    plan_kind_draw = _weighted_choice(
        streams.generator("known_plan_kind"), schedule.plan_kind_probs, (count, schema.P_MAX)
    )
    plan_context_draw = _uniform(
        streams.generator("known_plan_dose"), schedule.plan_c_range, (count, schema.P_MAX)
    )
    plan_execution_draw = _uniform(
        streams.generator("known_plan_eta"), schedule.plan_eta_range, (count, schema.P_MAX)
    )
    plan_times = np.full((count, schema.P_MAX), np.nan)
    plan_contexts = np.full((count, schema.P_MAX), np.nan)
    plan_kinds = np.full((count, schema.P_MAX), "", dtype=object)
    plan_execution = np.full((count, schema.P_MAX), np.nan)
    for origin, raw_count in enumerate(plan_count):
        number = int(raw_count)
        if number:
            order = np.argsort(plan_time_draw[origin, :number], kind="stable")
            plan_times[origin, :number] = plan_time_draw[origin, :number][order]
            plan_contexts[origin, :number] = plan_context_draw[origin, :number]
            plan_kinds[origin, :number] = plan_kind_draw[origin, :number]
            plan_execution[origin, :number] = plan_execution_draw[origin, :number]

    return CampSchedule(
        exposure_count,
        window,
        exposure_times,
        exposure_kinds,
        exposure_contexts,
        index_kinds,
        index_contexts,
        plan_count,
        plan_times,
        plan_contexts,
        plan_kinds,
        plan_execution,
        assessment_count,
        assessment_times,
        assessment_present,
        assessment_trials,
        baseline_times,
    )


def _kind_loads(kinds: Array, contexts: Array, parameters: Parameters = DEFAULT) -> Array:
    result = np.full(kinds.shape, np.nan, dtype=float)
    for kind, weight in parameters.dose.omega:
        result = np.where(kinds == kind, weight * contexts, result)
    return result


def _event_arrays(schedule: CampSchedule, parameters: Parameters = DEFAULT) -> tuple[Array, Array]:
    exposure_load = _kind_loads(schedule.exposure_kinds, schedule.exposure_contexts, parameters)
    index_load = _kind_loads(schedule.index_kinds, schedule.index_contexts, parameters)
    plan_load = (
        _kind_loads(schedule.plan_kinds, schedule.plan_contexts, parameters)
        * schedule.plan_execution
    )
    times = np.concatenate(
        [schedule.exposure_times, np.zeros((len(index_load), 1)), schedule.plan_times], axis=1
    )
    doses = np.concatenate([exposure_load, index_load[:, None], plan_load], axis=1)
    return times, doses


def _state_at(
    query_times: Array,
    event_times: Array,
    event_loads: Array,
    traits: ParticipantTraits,
    *,
    amplitude: Array,
    level: Array,
    floor_fraction: float = DECREMENT_FLOOR_FRACTION,
) -> Array:
    valid = np.isfinite(event_times) & np.isfinite(event_loads)
    safe_times = np.where(valid, event_times, 1e9)
    safe_loads = np.nan_to_num(event_loads)
    lag = query_times[:, :, None] - safe_times[:, None, :]
    contributions = exposure_response_values(
        lag,
        amplitude[:, None, None],
        safe_loads[:, None, :],
        traits.response_ratio[:, None, None],
        traits.bouts_prior_4wk[:, None, None],
        traits.tau_slow[:, None, None],
        traits.tau_fast[:, None, None],
    )
    net = contributions.sum(axis=2)
    return np.maximum(net, -floor_fraction * level[:, None])


@dataclass(frozen=True, slots=True)
class CampSimulation:
    regime: CampRegime
    participant_index: Array
    origin_index: Array
    traits: ParticipantTraits
    schedule: CampSchedule
    assessments: AssessmentMeasurements
    baseline_force: Array
    baseline_impulse: Array
    target_time: Array
    target_depth_context: Array
    horizon_present: Array
    force_innovation: Array
    impulse_innovation: Array


def _baseline_arrays(
    schedule: CampSchedule, assessments: AssessmentMeasurements, parameters: Parameters
) -> tuple[Array, Array]:
    baseline_force = np.full(len(schedule.exposure_count), np.nan)
    baseline_impulse = np.full(len(schedule.exposure_count), np.nan)
    model = parameters.schedule
    for origin in range(len(schedule.exposure_count)):
        assessments_for_origin: list[MonitoringAssessment] = []
        for slot in range(int(schedule.assessment_count[origin])):
            force = float(assessments.force[origin, slot])
            impulse = float(assessments.impulse[origin, slot])
            force_value = force if math.isfinite(force) else None
            impulse_value = impulse if math.isfinite(impulse) else None
            assessments_for_origin.append(
                MonitoringAssessment(
                    time_from_origin_hours=float(schedule.assessment_times[origin, slot]),
                    force=force_value,
                    impulse=impulse_value,
                    depth_m=float(assessments.depth[origin, slot]),
                    trial_count=int(schedule.assessment_trials[origin, slot]),
                    validity_state=AssessmentValidity(str(assessments.validity[origin, slot])),
                )
            )
        exposure_times = tuple(
            float(schedule.exposure_times[origin, slot])
            for slot in range(int(schedule.exposure_count[origin]))
        )
        baseline = protocol_baseline(
            tuple(assessments_for_origin),
            exposure_times,
            window_hours=model.baseline_window_h,
            recovered_gap_hours=model.baseline_recovered_gap_h,
        )
        if baseline is not None:
            baseline_force[origin] = baseline.force
            baseline_impulse[origin] = baseline.impulse
    return baseline_force, baseline_impulse


def _simulate_camp(
    spec: SplitSpec,
    camp_index: int,
    parameters: Parameters = DEFAULT,
    *,
    monitor_probability_override: float | None = None,
) -> CampSimulation:
    streams = RandomStreams("simulate-camp", spec.root_seed, spec.name, "camp", camp_index)
    regime = draw_camp_regime(streams.generator("camp_regime"), spec.table)
    if monitor_probability_override is not None:
        if not 0 <= monitor_probability_override <= 1:
            raise ValueError("monitor probability override must be in [0, 1]")
        regime = CampRegime(
            regime.dense,
            regime.quality_high,
            regime.intensity_scale,
            regime.heterogeneity,
            monitor_probability_override,
            regime.last_age_band_probabilities,
        )
    participant_traits = draw_participants(
        streams, spec.participants_per_camp, regime.heterogeneity, parameters
    )
    participant_index = np.repeat(
        np.arange(spec.participants_per_camp), spec.origins_per_participant
    )
    origin_index = np.tile(np.arange(spec.origins_per_participant), spec.participants_per_camp)
    traits = _repeat_traits(participant_traits, spec.origins_per_participant)
    unit_count = len(participant_index)
    schedule = draw_schedule(streams, unit_count, regime, parameters)
    event_times, event_loads = _event_arrays(schedule, parameters)
    assessment_query_times = np.where(schedule.assessment_present, schedule.assessment_times, -1e9)
    force_state = _state_at(
        assessment_query_times,
        event_times,
        event_loads,
        traits,
        amplitude=traits.amplitude_force,
        level=traits.level_force,
        floor_fraction=parameters.kinetics.state_floor_fraction,
    )
    impulse_state = _state_at(
        assessment_query_times,
        event_times,
        event_loads,
        traits,
        amplitude=traits.amplitude_impulse,
        level=traits.level_impulse,
        floor_fraction=parameters.kinetics.state_floor_fraction,
    )
    measurements = parameters.measurement
    assessments = observe_assessments(
        traits.level_force[:, None] + force_state,
        traits.level_impulse[:, None] + impulse_state,
        traits.preferred_depth,
        schedule.assessment_present,
        schedule.assessment_trials,
        measurements,
        depth_rng=streams.generator("history_assessment_depth_context"),
        force_rng=streams.generator("history_assessment_force_noise"),
        impulse_rng=streams.generator("history_assessment_impulse_noise"),
        validity_rng=streams.generator("history_assessment_validity"),
        invalid_scale_rng=streams.generator("history_assessment_invalid_scale"),
        missing_rng=streams.generator("history_assessment_missingness"),
    )
    baseline_force, baseline_impulse = _baseline_arrays(schedule, assessments, parameters)

    windows = parameters.schema.target_windows
    target_time = np.column_stack(
        [
            _uniform(streams.generator("target_time_H72"), windows[0], unit_count),
            _uniform(streams.generator("target_time_D7"), windows[1], unit_count),
        ]
    )
    force_state = _state_at(
        target_time,
        event_times,
        event_loads,
        traits,
        amplitude=traits.amplitude_force,
        level=traits.level_force,
        floor_fraction=parameters.kinetics.state_floor_fraction,
    )
    impulse_state = _state_at(
        target_time,
        event_times,
        event_loads,
        traits,
        amplitude=traits.amplitude_impulse,
        level=traits.level_impulse,
        floor_fraction=parameters.kinetics.state_floor_fraction,
    )
    target = observe_target(
        traits.level_force[:, None] + force_state,
        traits.level_impulse[:, None] + impulse_state,
        traits.preferred_depth,
        measurements,
        depth_rng=streams.generator("target_depth_context"),
        force_rng=streams.generator("target_force_noise"),
        impulse_rng=streams.generator("target_impulse_noise"),
    )
    single = (
        streams.generator("horizon_single_presence").random(unit_count)
        < parameters.schedule.single_horizon_rate
    )
    dropped = streams.generator("horizon_dropped_index").integers(0, 2, unit_count)
    horizon_present = np.ones((unit_count, 2), dtype=bool)
    horizon_present[single, dropped[single]] = False
    return CampSimulation(
        regime,
        participant_index,
        origin_index,
        traits,
        schedule,
        assessments,
        baseline_force,
        baseline_impulse,
        target_time,
        target.depth_context,
        horizon_present,
        target.force - baseline_force[:, None],
        target.impulse - baseline_impulse[:, None],
    )


@dataclass(frozen=True, slots=True)
class GroupingMetadata:
    split: PublicSplitName
    camp_index: int
    participant_index: int
    origin_index: int


@dataclass(frozen=True, slots=True)
class RichHistoryRow:
    participant_key: str
    origin_key: str
    query_key: str
    fields: Mapping[str, object]
    labels: Mapping[str, float | None]
    grouping: GroupingMetadata

    def public_mapping(self) -> dict[str, object]:
        row: dict[str, object] = {
            "participant_key": self.participant_key,
            "origin_key": self.origin_key,
            "query_key": self.query_key,
        }
        row.update(self.fields)
        row.update(self.labels)
        return row

    @property
    def stratum(self) -> str:
        exposure_times = tuple(
            float(
                cast(
                    float,
                    self.fields[f"history_exposure[{slot}].time_from_origin_hours"],
                )
            )
            for slot in range(DEFAULT.schema.K_MAX)
        )
        assessments = tuple(
            RichHistoryAssessment(
                time_from_origin_hours=float(
                    cast(
                        float,
                        self.fields[f"history_assessment[{slot}].time_from_origin_hours"],
                    )
                ),
                validity_state=str(self.fields[f"history_assessment[{slot}].validity_state"]),
                trial_count=float(cast(float, self.fields[f"history_assessment[{slot}].n_trials"])),
            )
            for slot in range(int(float(cast(float, self.fields["n_assessments"]))))
        )
        return rich_history_stratum(exposure_times, assessments)


def _finite_or_none(value: float) -> float | None:
    numeric = float(value)
    return round(numeric, 9) if math.isfinite(numeric) else None


def _event_kind(value: object) -> str | None:
    return None if value in ("", None) else str(value)


def public_grouping_keys(
    spec: SplitSpec, camp: int, participant: int, origin: int
) -> tuple[str, str, str, str]:
    namespace, split = spec.key_namespace, spec.name
    participant_key = opaque_key(namespace, "participant", split, camp, participant)
    origin_key = opaque_key(namespace, "origin", split, camp, participant, origin)
    return (
        participant_key,
        origin_key,
        opaque_key(namespace, "query", split, camp, participant, origin, "H72"),
        opaque_key(namespace, "query", split, camp, participant, origin, "D7"),
    )


def _project_row(
    simulation: CampSimulation,
    unit: int,
    horizon_index: int,
    keys: tuple[str, str, str, str],
    grouping: GroupingMetadata,
    parameters: Parameters = DEFAULT,
) -> RichHistoryRow:
    schema, schedule = parameters.schema, simulation.schedule
    horizon = schema.horizons[horizon_index]
    target_window = schema.target_windows[horizon_index]
    history_assessments: list[dict[str, object]] = []
    for slot in range(int(schedule.assessment_count[unit])):
        history_assessments.append(
            {
                "time_from_origin_hours": _finite_or_none(schedule.assessment_times[unit, slot]),
                "relative_mean_concentric_force": _finite_or_none(
                    simulation.assessments.force[unit, slot]
                ),
                "relative_concentric_net_impulse": _finite_or_none(
                    simulation.assessments.impulse[unit, slot]
                ),
                "depth_m": _finite_or_none(simulation.assessments.depth[unit, slot]),
                "n_trials": _finite_or_none(schedule.assessment_trials[unit, slot]),
                "validity_state": str(simulation.assessments.validity[unit, slot]),
            }
        )
    history_exposures: list[dict[str, object]] = []
    for slot in range(int(schedule.exposure_count[unit])):
        context = float(schedule.exposure_contexts[unit, slot])
        history_exposures.append(
            {
                "time_from_origin_hours": _finite_or_none(schedule.exposure_times[unit, slot]),
                "event_kind": _event_kind(schedule.exposure_kinds[unit, slot]),
                "duration_minutes": _finite_or_none(100.0 * context),
                "c_context": _finite_or_none(context),
            }
        )
    index_context = float(schedule.index_contexts[unit])
    known_plans: list[dict[str, object]] = []
    for slot in range(int(schedule.plan_count[unit])):
        context = float(schedule.plan_contexts[unit, slot])
        known_plans.append(
            {
                "time_from_origin_hours": _finite_or_none(schedule.plan_times[unit, slot]),
                "event_kind": _event_kind(schedule.plan_kinds[unit, slot]),
                "planned_duration_minutes": _finite_or_none(100.0 * context),
                "planned_c_context": _finite_or_none(context),
            }
        )

    record = {
        "schema_version": SCHEMA_IDENTITY,
        "participant_key": keys[0],
        "origin_key": keys[1],
        "query_key": keys[2 + horizon_index],
        "horizon": horizon,
        "target_time_hours": _finite_or_none(simulation.target_time[unit, horizon_index]),
        "target_window_hours": {"low": target_window[0], "high": target_window[1]},
        "baseline": {
            "relative_mean_concentric_force": _finite_or_none(simulation.baseline_force[unit]),
            "relative_concentric_net_impulse": _finite_or_none(simulation.baseline_impulse[unit]),
        },
        "public_features": {
            "participant": {
                "training_age_years": _finite_or_none(simulation.traits.training_age[unit]),
                "strength_index": _finite_or_none(simulation.traits.strength_index[unit]),
                "bouts_prior_4wk": _finite_or_none(simulation.traits.bouts_prior_4wk[unit]),
            },
            "history_assessments": history_assessments,
            "history_exposures": history_exposures,
            "index_exposure": {
                "event_kind": _event_kind(schedule.index_kinds[unit]),
                "duration_minutes": _finite_or_none(100.0 * index_context),
                "c_context": _finite_or_none(index_context),
            },
            "known_plan": known_plans,
        },
        "label": {
            "innovation": {
                "relative_mean_concentric_force": _finite_or_none(
                    simulation.force_innovation[unit, horizon_index]
                ),
                "relative_concentric_net_impulse": _finite_or_none(
                    simulation.impulse_innovation[unit, horizon_index]
                ),
            },
            "available": True,
        },
    }
    return project_public_record(record, grouping)


def project_public_record(record: Mapping[str, Any], grouping: GroupingMetadata) -> RichHistoryRow:
    """Project one nested public record; labels and grouping keys stay outside R02."""
    features = flatten_r02_record(record)
    labels_record: Mapping[str, Any] = record["label"]["innovation"]
    labels = {
        HORIZON_TARGET_COLUMNS[0]: _finite_or_none(
            _number(labels_record["relative_mean_concentric_force"])
        ),
        HORIZON_TARGET_COLUMNS[1]: _finite_or_none(
            _number(labels_record["relative_concentric_net_impulse"])
        ),
    }
    return RichHistoryRow(
        str(record["participant_key"]),
        str(record["origin_key"]),
        str(record["query_key"]),
        features,
        labels,
        grouping,
    )


def admitted_horizons(horizon_presence: ArrayLike) -> tuple[int, ...]:
    """D04 admission is solely the source's horizon-presence mask."""
    presence = np.asarray(horizon_presence, dtype=bool)
    if presence.shape != (2,):
        raise ValueError("one origin must provide two horizon-presence values")
    return tuple(index for index in range(2) if bool(presence[index]))


def iter_rich_history_public_split(
    split_name: PublicSplitName,
) -> Iterator[RichHistoryRow]:
    """Yield clean-room rows for one of the two source-defined public splits."""
    try:
        spec = PUBLIC_SPLITS[split_name]
    except KeyError as exc:
        raise ValueError(f"unknown public rich-history split: {split_name}") from exc
    for camp in range(spec.camps):
        simulation = _simulate_camp(spec, camp)
        for unit in range(len(simulation.participant_index)):
            participant = int(simulation.participant_index[unit])
            origin = int(simulation.origin_index[unit])
            keys = public_grouping_keys(spec, camp, participant, origin)
            grouping = GroupingMetadata(split_name, camp, participant, origin)
            for horizon in admitted_horizons(simulation.horizon_present[unit]):
                yield _project_row(simulation, unit, horizon, keys, grouping)


@dataclass(frozen=True, slots=True)
class RichHistoryNativeProgress:
    cells: tuple[CellMetric, ...]
    outcome_progress: tuple[tuple[str, float], ...]
    aggregate_progress: float


def rich_history_native_progress(values: Sequence[CellValues]) -> RichHistoryNativeProgress:
    """Compute E02 progress before its unavailable historical PWL calibration."""
    metrics = cellwise_normalized_rmse(
        values,
        RICH_HISTORY_CELLS,
        minimum_rows_per_cell=RICH_HISTORY_CELL_MIN_ROWS,
    )
    targets = rich_history_target_metrics(metrics)
    progress = tuple((target.name, min(1.0, max(0.0, 1.0 - target.value))) for target in targets)
    aggregate = math.fsum(value for _, value in progress) / len(progress)
    return RichHistoryNativeProgress(metrics, progress, aggregate)


__all__ = [
    "ALI490_RNG_CHANNELIZATION_COMMIT",
    "CATEGORICAL_FIELDS",
    "D04_DATA_PRODUCER_COMMIT",
    "D04_DATA_PRODUCER_REPOSITORY_TREE",
    "D04_DATA_PRODUCER_TASK_TREE",
    "D04_MANIFEST_BLOB_OID",
    "D04_TRAIN_PARQUET_BLOB_OID",
    "D04_VALIDATION_PARQUET_BLOB_OID",
    "DEFAULT",
    "F2_LEVELS",
    "F3_LEVELS",
    "HISTORICAL_HIDDEN_DESIGN",
    "HORIZON_TARGET_COLUMNS",
    "PUBLIC_GROUPING_COLUMNS",
    "PUBLIC_SPLITS",
    "R02_FIELD_BLOCKS",
    "R02_FIELD_NAMES",
    "RICH_HISTORY_REPRODUCTION_METADATA",
    "SP03_SOURCE_CLOSURE",
    "SP03_SOURCE_TREE",
    "CampRegime",
    "GroupingMetadata",
    "HiddenDesignCounts",
    "PublicSplitName",
    "RichHistoryNativeProgress",
    "RichHistoryRow",
    "RandomStreams",
    "SCHEMA_DIGEST",
    "STREAM_CHANNELS",
    "admitted_horizons",
    "flatten_r02_record",
    "iter_rich_history_public_split",
    "opaque_key",
    "parameterize_participants",
    "project_public_record",
    "public_grouping_keys",
    "rich_history_native_progress",
    "rng_for",
    "seed_from",
    "validate_r02_row",
]
