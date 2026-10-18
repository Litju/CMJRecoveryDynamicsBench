"""Leakage-safe public reference study for fixed-mode discrepancy recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.contracts import MetricCategory, OutcomeVariable, TargetCell
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (
    FAST_MODE_HOURS,
    SLOW_MODE_HOURS,
)
from cmj_recovery_dynamics.metrics.catalog import POST_EXPOSURE_RESEARCH_EVALUATION
from cmj_recovery_dynamics.metrics.scoring import (
    POST_EXPOSURE_RESEARCH_CELLS,
    CellValues,
    cellwise_normalized_rmse,
)
from cmj_recovery_dynamics.reproducibility.contracts import SeedIdentity, SeedKind
from cmj_recovery_dynamics.reproducibility.execution import (
    PublicDatasetInterface,
    get_metric_implementation,
)
from cmj_recovery_dynamics.reproducibility.registry import get_public_dataset_interface
from cmj_recovery_dynamics.reproduction.single_exposure import (
    BASELINE_FIELDS,
    EXPOSURE_SUPPORTS,
    HORIZONS,
    OSS_ROOT_SEED,
    PARTICIPANT_FIELDS,
    PREDICTOR_FIELDS,
    RNG_IDENTITY_NAMESPACE,
    ROW_KEY_FIELDS,
    SPLIT_GEOMETRY,
    TARGET_FIELDS,
    iter_public_members,
)

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

BENCHMARK_NAME = "fixed_mode_discrepancy_recovery"
DATASET_NAME = "fixed_mode_recovery_candidate_sample"
BASE_MAIN_SHA = "ecdf930915175891596cd35a7ddaaf222c021078"
TRAINING_SPLIT = "training"
DEVELOPMENT_SPLIT = "public_validation"
TEST_SPLIT = "public_validation"
PILOT_TRAIN_CAMPS = 4
PILOT_DEVELOPMENT_CAMPS = 2
RIDGE_ALPHA_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 49_505_000
SAMPLE_EFFICIENCY_SEED = 52_610_526
SAMPLE_EFFICIENCY_CAMP_COUNTS = (24, 48, 96)
TEST_ROOTS = (
    "res-526-public-eval-root-a-2026-10-18",
    "res-526-public-eval-root-b-2026-10-18",
    "res-526-public-eval-root-c-2026-10-18",
)
HORIZON_LABELS = tuple(horizon for horizon, _ in HORIZONS)
HORIZON_HOURS = tuple(int(hours) for _, hours in HORIZONS)
NUMERIC_PREDICTOR_FIELDS = tuple(name for name in PREDICTOR_FIELDS if name != "horizon")
RIDGE_FEATURE_NAMES = NUMERIC_PREDICTOR_FIELDS + tuple(
    f"horizon=={horizon}" for horizon in HORIZON_LABELS
)
OUTCOME_TARGETS = (
    (OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION, TARGET_FIELDS[0]),
    (OutcomeVariable.NET_IMPULSE_INNOVATION, TARGET_FIELDS[1]),
)
OUTCOME_INDEX = {outcome: index for index, (outcome, _) in enumerate(OUTCOME_TARGETS)}
TARGET_INDEX = {field: index for index, (_, field) in enumerate(OUTCOME_TARGETS)}
CELLS = tuple(POST_EXPOSURE_RESEARCH_CELLS)
_EXPECTED_ROW_FIELDS = frozenset((*ROW_KEY_FIELDS, *PREDICTOR_FIELDS, *TARGET_FIELDS))
_SPLIT_CAMP_COUNT = {"training": 96, "public_validation": 16}
_ROWS_PER_CAMP = 250 * len(HORIZONS)
_TEST_ROOT_SET = frozenset(TEST_ROOTS)
_PROTOCOL_VERSION = "res-526-fixed-mode-reference-v1"


@dataclass(frozen=True, slots=True)
class SplitData:
    split: str
    root_seed: str
    seed_kind: str
    rows: int
    camp_count: int
    features: FloatArray
    targets: FloatArray
    horizons: IntArray
    camps: IntArray
    key_sets: Mapping[str, frozenset[str]]
    sha256: str
    generation_seconds: float


@dataclass(frozen=True, slots=True)
class CellRidgeModel:
    alpha: float
    training_rows: int
    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    target_mean: float
    target_scale: float
    coefficients: tuple[float, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.alpha) or self.alpha <= 0.0 or self.training_rows < 2:
            raise ValueError("locked ridge model alpha and training count are invalid")
        if not self.feature_names or len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("locked ridge feature names must be non-empty and unique")
        if len(self.feature_means) != len(self.feature_names):
            raise ValueError("locked ridge feature means do not match its feature names")
        if len(self.feature_scales) != len(self.feature_names) or any(
            not math.isfinite(value) or value <= 0.0 for value in self.feature_scales
        ):
            raise ValueError("locked ridge feature scales must be finite and positive")
        if len(self.coefficients) != len(self.feature_names) + 1:
            raise ValueError("locked ridge coefficient count does not include one intercept")
        if (
            not math.isfinite(self.target_mean)
            or not math.isfinite(self.target_scale)
            or self.target_scale <= 0.0
            or any(not math.isfinite(value) for value in (*self.feature_means, *self.coefficients))
        ):
            raise ValueError("locked ridge parameters must all be finite")

    def predict(self, features: FloatArray, feature_names: Sequence[str]) -> FloatArray:
        if tuple(feature_names) != self.feature_names:
            raise ValueError("prediction feature names do not match the locked model")
        if features.ndim != 2 or features.shape[1] != len(self.feature_names):
            raise ValueError("prediction feature dimensions do not match the locked model")
        standardized = (features - np.asarray(self.feature_means)) / np.asarray(self.feature_scales)
        design = np.column_stack((np.ones(features.shape[0]), standardized))
        prediction = (design @ np.asarray(self.coefficients)) * self.target_scale + self.target_mean
        if not bool(np.isfinite(prediction).all()):
            raise ValueError("locked ridge model produced non-finite predictions")
        return prediction

    def to_record(self) -> dict[str, object]:
        return {
            "alpha": self.alpha,
            "training_rows": self.training_rows,
            "feature_names": list(self.feature_names),
            "feature_means": list(self.feature_means),
            "feature_scales": list(self.feature_scales),
            "target_mean": self.target_mean,
            "target_scale": self.target_scale,
            "coefficients": list(self.coefficients),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CellRidgeModel:
        return cls(
            _record_float(record["alpha"], "alpha"),
            _record_int(record["training_rows"], "training_rows"),
            tuple(cast(list[str], record["feature_names"])),
            tuple(
                _record_float(value, "feature_mean")
                for value in cast(list[object], record["feature_means"])
            ),
            tuple(
                _record_float(value, "feature_scale")
                for value in cast(list[object], record["feature_scales"])
            ),
            _record_float(record["target_mean"], "target_mean"),
            _record_float(record["target_scale"], "target_scale"),
            tuple(
                _record_float(value, "coefficient")
                for value in cast(list[object], record["coefficients"])
            ),
        )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _record_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"selection lock {field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"selection lock {field} must be finite")
    return result


def _record_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"selection lock {field} must be an integer")
    return value


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def package_source_sha256() -> str:
    package_root = Path(__file__).resolve().parent.parent
    digest = hashlib.sha256()
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\n")
    return digest.hexdigest()


def _feature_contract() -> dict[str, object]:
    return {
        "schema": "single_exposure_public_predictor_fields",
        "source_fields": len(PREDICTOR_FIELDS),
        "source_field_names_sha256": hashlib.sha256(
            "\n".join(PREDICTOR_FIELDS).encode("utf-8")
        ).hexdigest(),
        "encoded_fields": len(RIDGE_FEATURE_NAMES),
        "encoded_feature_names_sha256": hashlib.sha256(
            "\n".join(RIDGE_FEATURE_NAMES).encode("utf-8")
        ).hexdigest(),
        "horizon_encoding": "one-hot over the registered H24/H48/H72 forecast horizon",
        "numeric_preprocessing": "training-only mean and population SD; zero SD set to one",
        "missing_predictors": "rejected; the public 82-field projection is complete",
        "grouping_keys_as_predictors": False,
        "target_labels_as_predictors": False,
        "target_time_or_post_query_fields": "absent from the registered 82-field schema",
    }


def protocol_record() -> dict[str, object]:
    return {
        "version": _PROTOCOL_VERSION,
        "benchmark": BENCHMARK_NAME,
        "dataset": DATASET_NAME,
        "base_public_main": BASE_MAIN_SHA,
        "training_split": TRAINING_SPLIT,
        "development_split": DEVELOPMENT_SPLIT,
        "registered_public_source_root": OSS_ROOT_SEED,
        "test_split": TEST_SPLIT,
        "test_roots": list(TEST_ROOTS),
        "test_root_role": "caller-supplied public roots; never historical or private test data",
        "camp_unit_identity": "keyed RNG namespace + root seed + split + public camp index",
        "registered_metric": POST_EXPOSURE_RESEARCH_EVALUATION.name,
        "registered_cells": [cell.name for cell in CELLS],
        "minimum_rows_per_cell": 2,
        "zero_truth_sd": "rejected by the registered metric",
        "selection_rule": "minimum development six-cell mean NRMSE; ties choose lower alpha",
        "alpha_grid": list(RIDGE_ALPHA_GRID),
        "alpha_selection_scope": "one alpha per model family or ablation, shared across six cells",
        "linear_fit": {
            "features": "training-only mean and population SD; zero SD set to one",
            "targets": "training-only mean and population SD; zero SD set to one",
            "intercept": "unpenalized",
            "objective": "mean squared error plus alpha times squared coefficient norm",
            "solver": "deterministic closed-form normal equations",
        },
        "baselines": {
            "zero_innovation": "predict zero for each innovation",
            "training_constant": "training label mean per outcome and horizon",
        },
        "structured_basis": {
            "mathematical_modes_hours": [FAST_MODE_HOURS, SLOW_MODE_HOURS],
            "amplitudes": "coefficients estimated from public training rows only",
            "inputs": "normalized public current exposure primitives, public baselines, "
            "participant context, and observed prior-episode innovations",
            "hidden_effects_or_oracle_states": False,
        },
        "sample_efficiency": {
            "camp_counts": list(SAMPLE_EFFICIENCY_CAMP_COUNTS),
            "seed": SAMPLE_EFFICIENCY_SEED,
            "nested_subset_order": "one seeded permutation of the 96 public training camps",
            "hyperparameters": "selected once on full training/development, then held fixed",
        },
        "bootstrap": {
            "unit": "camp; all 250 episodes and three horizons remain together",
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "generator": "NumPy default_rng / PCG64",
            "interval": "paired 2.5th and 97.5th percentiles",
        },
        "ablation_variants": [
            "ridge_no_prior_history",
            "ridge_no_current_exposure",
            "ridge_no_participant_context",
            "structured_no_prior_history",
        ],
        "feature_schema": _feature_contract(),
    }


def _registered_metric(values: Sequence[CellValues]) -> float:
    binding = get_metric_implementation(POST_EXPOSURE_RESEARCH_EVALUATION.name)
    if binding.implementation_id != "mean_cellwise_normalized_rmse":
        raise RuntimeError("registered six-cell research metric has an unexpected implementation")
    value = binding.evaluate(values, CELLS)
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError("registered six-cell research metric returned a non-finite scalar")
    return float(value)


def to_feature_row(row: Mapping[str, object]) -> tuple[FloatArray, int]:
    if frozenset(row) != _EXPECTED_ROW_FIELDS:
        raise ValueError(
            "public interface row does not match the fixed 82-field predictor contract"
        )
    horizon = row["horizon"]
    if not isinstance(horizon, str) or horizon not in HORIZON_LABELS:
        raise ValueError(f"unsupported forecast horizon: {horizon!r}")
    hours = int(dict(HORIZONS)[horizon])
    numeric_values: list[float] = []
    for field in NUMERIC_PREDICTOR_FIELDS:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"public predictor {field} must be numeric")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"public predictor {field} must be finite")
        numeric_values.append(numeric)
    encoded_horizon = [float(horizon == label) for label in HORIZON_LABELS]
    return np.asarray((*numeric_values, *encoded_horizon), dtype=np.float64), hours


def _target_numeric(value: object, field: str) -> float:
    if value is None:
        return math.nan
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"observed label {field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"observed label {field} must be finite")
    return numeric


def validate_episode_rows(
    episode_rows: Sequence[Mapping[str, object]],
) -> tuple[str, str]:
    if len(episode_rows) != len(HORIZON_LABELS):
        raise ValueError("each public episode must provide exactly three horizon rows")
    participant_key = episode_rows[0]["participant_key"]
    episode_key = episode_rows[0]["episode_key"]
    if not isinstance(participant_key, str) or not isinstance(episode_key, str):
        raise ValueError("public participant and episode keys must be strings")
    if any(
        row["participant_key"] != participant_key or row["episode_key"] != episode_key
        for row in episode_rows
    ):
        raise ValueError("H24/H48/H72 query rows must remain in one episode group")
    if tuple(row["horizon"] for row in episode_rows) != HORIZON_LABELS:
        raise ValueError("public episode rows must follow the registered horizon order")
    return participant_key, episode_key


def _read_public_split(
    interface: PublicDatasetInterface,
    split_name: str,
    *,
    seed_identity: SeedIdentity | None = None,
    camp_limit: int | None = None,
) -> SplitData:
    if split_name not in _SPLIT_CAMP_COUNT:
        raise ValueError("only public training and public-validation splits are supported")
    total_camps = _SPLIT_CAMP_COUNT[split_name]
    if camp_limit is not None and (
        type(camp_limit) is not int or camp_limit < 1 or camp_limit > total_camps
    ):
        raise ValueError("camp limit must be between one and the registered split geometry")
    selected_camps = total_camps if camp_limit is None else camp_limit
    native_split = "train" if split_name == TRAINING_SPLIT else "validation"
    native_geometry = SPLIT_GEOMETRY[native_split]
    if total_camps != native_geometry.camps:
        raise RuntimeError("study split camp counts differ from the registered public geometry")
    participants_per_camp = native_geometry.participants // native_geometry.camps
    if native_geometry.rows != native_geometry.camps * _ROWS_PER_CAMP:
        raise RuntimeError(
            "registered public split geometry no longer matches the episode contract"
        )
    identity = seed_identity or interface.make_seed_identity(split_name)
    if identity.value is None or not isinstance(identity.value, str):
        raise ValueError("fixed-mode public roots must have an explicit string identity")
    row_limit = None if camp_limit is None else selected_camps * _ROWS_PER_CAMP
    row_iterator = iter(interface.iter_rows(split_name, seed_identity=identity, limit=row_limit))
    expected_rows = selected_camps * _ROWS_PER_CAMP
    features = np.empty((expected_rows, len(RIDGE_FEATURE_NAMES)), dtype=np.float64)
    targets = np.empty((expected_rows, len(TARGET_FIELDS)), dtype=np.float64)
    horizons = np.empty(expected_rows, dtype=np.int64)
    camps = np.empty(expected_rows, dtype=np.int64)
    key_sets: dict[str, set[str]] = {field: set() for field in ROW_KEY_FIELDS}
    participant_to_episode: dict[str, str] = {}
    digest = hashlib.sha256()
    row_index = 0
    started = time.perf_counter()
    members = iter_public_members(native_split)
    for camp_index in range(selected_camps):
        for participant_index in range(participants_per_camp):
            if next(members, None) != (camp_index, participant_index):
                raise ValueError("public member order differs from the registered camp geometry")
            episode_rows: list[Mapping[str, object]] = []
            for _ in HORIZONS:
                row = next(row_iterator, None)
                if row is None:
                    raise ValueError("public interface ended before the registered row count")
                episode_rows.append(row)
            participant_key, episode_key = validate_episode_rows(episode_rows)
            if participant_key in participant_to_episode:
                raise ValueError("a public participant appears in more than one episode")
            if episode_key in key_sets["episode_key"]:
                raise ValueError("a public episode key appears more than once")
            participant_to_episode[participant_key] = episode_key
            key_sets["participant_key"].add(participant_key)
            key_sets["episode_key"].add(episode_key)
            for row in episode_rows:
                vector, horizon_hours = to_feature_row(row)
                if row_index >= expected_rows:
                    raise ValueError("public interface returned more rows than its split geometry")
                features[row_index] = vector
                horizons[row_index] = horizon_hours
                camps[row_index] = camp_index
                for target_index, target_field in enumerate(TARGET_FIELDS):
                    targets[row_index, target_index] = _target_numeric(
                        row[target_field], target_field
                    )
                query_key = row["query_key"]
                if not isinstance(query_key, str):
                    raise ValueError("public query key must be a string")
                if query_key in key_sets["query_key"]:
                    raise ValueError("public query key is not unique")
                key_sets["query_key"].add(query_key)
                digest.update(_canonical_json_bytes(dict(row)))
                digest.update(b"\n")
                row_index += 1
    if row_index != expected_rows or next(row_iterator, None) is not None:
        raise ValueError("public interface row count does not match the registered camp geometry")
    if camp_limit is None and next(members, None) is not None:
        raise ValueError("public member iterator returned more camps than requested")
    return SplitData(
        split_name,
        identity.value,
        identity.kind.value,
        row_index,
        selected_camps,
        features,
        targets,
        horizons,
        camps,
        {key: frozenset(values) for key, values in key_sets.items()},
        digest.hexdigest(),
        time.perf_counter() - started,
    )


def assert_disjoint_splits(left: SplitData, right: SplitData) -> None:
    for key_field in ROW_KEY_FIELDS:
        overlap = left.key_sets[key_field].intersection(right.key_sets[key_field])
        if overlap:
            raise ValueError(f"training and development {key_field} values overlap")
    if camp_unit_ids(left.split, left.root_seed, left.camp_count).intersection(
        camp_unit_ids(right.split, right.root_seed, right.camp_count)
    ):
        raise ValueError("training and development camp/episode units overlap")


def camp_unit_ids(split_name: str, root_seed: str, camp_count: int) -> frozenset[str]:
    if split_name not in _SPLIT_CAMP_COUNT or not root_seed or camp_count < 1:
        raise ValueError("camp-unit identity requires a public split, root, and positive count")
    native_split = "train" if split_name == TRAINING_SPLIT else "validation"
    return frozenset(
        f"{RNG_IDENTITY_NAMESPACE}\0{root_seed}\0{native_split}\0camp\0{camp_index}"
        for camp_index in range(camp_count)
    )


def _split_record(data: SplitData) -> dict[str, object]:
    return {
        "split": data.split,
        "root_seed": data.root_seed,
        "seed_kind": data.seed_kind,
        "camps": data.camp_count,
        "episodes": len(data.key_sets["episode_key"]),
        "rows": data.rows,
        "row_stream_sha256": data.sha256,
        "camp_unit_identity_sha256": _sha256(
            sorted(camp_unit_ids(data.split, data.root_seed, data.camp_count))
        ),
        "grouping_keys": {
            field: {
                "unique_values": len(data.key_sets[field]),
                "sha256": hashlib.sha256(
                    "\n".join(sorted(data.key_sets[field])).encode("utf-8")
                ).hexdigest(),
            }
            for field in ROW_KEY_FIELDS
        },
        "labels": {
            field: {
                "observed": int(np.isfinite(data.targets[:, index]).sum()),
                "missing": int(np.isnan(data.targets[:, index]).sum()),
            }
            for index, field in enumerate(TARGET_FIELDS)
        },
        "generation_seconds": data.generation_seconds,
    }


def _check_metric_path() -> None:
    interface = get_public_dataset_interface(BENCHMARK_NAME)
    if interface.benchmark_name != BENCHMARK_NAME:
        raise RuntimeError("public interface resolved the wrong benchmark")
    if interface.generator_identity != "fixed_mode_discrepancy_world":
        raise RuntimeError("public interface resolved an unexpected fixed-mode generator")
    binding = get_metric_implementation(POST_EXPOSURE_RESEARCH_EVALUATION.name)
    if binding.implementation_id != "mean_cellwise_normalized_rmse":
        raise RuntimeError("registered fixed-mode research metric is not the six-cell NRMSE")
    if (
        binding.evaluation is None
        or binding.evaluation.category is not MetricCategory.RESEARCH_DIAGNOSTIC
    ):
        raise RuntimeError("registered six-cell metric is not a research-only diagnostic")


def _target_for_cell(cell: TargetCell) -> tuple[int, int]:
    if cell.outcome not in OUTCOME_INDEX:
        raise ValueError(f"unexpected research outcome: {cell.name}")
    return OUTCOME_INDEX[cell.outcome], int(cell.horizon.value)


def cell_values_from_arrays(
    horizons: IntArray,
    targets: FloatArray,
    predictions: FloatArray,
) -> tuple[CellValues, ...]:
    if targets.shape != predictions.shape or targets.shape != (len(horizons), len(TARGET_FIELDS)):
        raise ValueError("target and prediction arrays do not match the query-row contract")
    values: list[CellValues] = []
    for cell in CELLS:
        outcome_index, horizon = _target_for_cell(cell)
        mask = horizons == horizon
        y = targets[mask, outcome_index]
        prediction = predictions[mask, outcome_index]
        missing = np.isnan(y)
        if bool(np.isinf(y).any()) or not bool(np.isfinite(prediction).all()):
            raise ValueError(f"non-finite observed values or predictions in {cell.name}")
        observed = y[~missing]
        predicted = prediction[~missing]
        values.append(
            CellValues(
                cell,
                tuple(float(value) for value in predicted),
                tuple(float(value) for value in observed),
            )
        )
    return tuple(values)


def _ridge_view_names(variant: str) -> tuple[str, ...]:
    if variant not in {
        "ridge_full",
        "ridge_no_prior_history",
        "ridge_no_current_exposure",
        "ridge_no_participant_context",
    }:
        raise ValueError(f"unknown ridge feature variant: {variant}")
    names: list[str] = []
    for name in RIDGE_FEATURE_NAMES:
        if variant == "ridge_no_prior_history" and name.startswith("prior_episode["):
            continue
        if variant == "ridge_no_current_exposure" and name.startswith("index_exposure."):
            continue
        if variant == "ridge_no_participant_context" and name in PARTICIPANT_FIELDS:
            continue
        names.append(name)
    return tuple(names)


def _matrix_view(
    data: SplitData, variant: str, outcome_index: int
) -> tuple[FloatArray, tuple[str, ...]]:
    if variant.startswith("ridge_"):
        names = _ridge_view_names(variant)
        column_index = {name: index for index, name in enumerate(RIDGE_FEATURE_NAMES)}
        selected = [column_index[name] for name in names]
        return data.features[:, selected], names
    if variant not in {"structured_full", "structured_no_prior_history"}:
        raise ValueError(f"unknown model feature variant: {variant}")
    return structured_features(data, outcome_index, include_prior=variant == "structured_full")


def structured_features(
    data: SplitData, outcome_index: int, *, include_prior: bool
) -> tuple[FloatArray, tuple[str, ...]]:
    field_index = {name: index for index, name in enumerate(NUMERIC_PREDICTOR_FIELDS)}
    exposure_values = {
        name: data.features[:, field_index[f"index_exposure.{name}"]]
        for name, _ in EXPOSURE_SUPPORTS
    }
    load_columns = [
        np.clip(
            (exposure_values[name] - low) / (high - low),
            0.0,
            1.0,
        )
        for name, (low, high) in EXPOSURE_SUPPORTS
    ]
    load = np.column_stack(load_columns)
    fast = np.exp(-data.horizons / FAST_MODE_HOURS)
    slow = np.exp(-data.horizons / SLOW_MODE_HOURS)
    basis = np.column_stack((load * fast[:, None], load * slow[:, None]))
    load_names = tuple(name for name, _ in EXPOSURE_SUPPORTS)
    names = tuple(f"fixed_24h:{name}" for name in load_names) + tuple(
        f"fixed_84h:{name}" for name in load_names
    )
    baseline_context_fields = (*BASELINE_FIELDS, *PARTICIPANT_FIELDS)
    context = np.column_stack(
        [data.features[:, field_index[name]] for name in baseline_context_fields]
    )
    names += tuple(f"public_context:{name}" for name in baseline_context_fields)
    matrices = [basis, context]
    if include_prior:
        metric_field = (
            "relative_mean_concentric_force_innovation"
            if outcome_index == 0
            else "relative_concentric_net_impulse_innovation"
        )
        prior_names = tuple(
            f"prior_episode[{episode}].{horizon}.{metric_field}"
            for episode in range(4)
            for horizon in HORIZON_LABELS
        )
        prior = np.column_stack([data.features[:, field_index[name]] for name in prior_names])
        matrices.append(prior)
        names += prior_names
    result = np.column_stack(matrices)
    if result.shape[1] != len(names) or not bool(np.isfinite(result).all()):
        raise ValueError("structured public feature construction is inconsistent or non-finite")
    if any("label." in name for name in names):
        raise ValueError("structured comparator feature set contains a forbidden field")
    return result, names


def fit_cell_model(
    features: FloatArray,
    targets: Sequence[float],
    feature_names: tuple[str, ...],
    alpha: float,
) -> CellRidgeModel:
    y = np.asarray(targets, dtype=np.float64)
    if features.ndim != 2 or features.shape[0] != y.size or y.size < 2:
        raise ValueError("ridge fit requires aligned features and at least two labels")
    if not bool(np.isfinite(features).all()) or not bool(np.isfinite(y).all()):
        raise ValueError("ridge fit inputs must be finite")
    if not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError("ridge alpha must be finite and positive")
    means = features.mean(axis=0)
    scales = features.std(axis=0, ddof=0)
    scales[scales == 0.0] = 1.0
    standardized_features = (features - means) / scales
    target_mean = float(y.mean())
    target_scale = float(y.std(ddof=0))
    if target_scale == 0.0:
        target_scale = 1.0
    standardized_target = (y - target_mean) / target_scale
    design = np.column_stack((np.ones(y.size), standardized_features))
    gram = design.T @ design / y.size
    gram[1:, 1:] += alpha * np.eye(features.shape[1])
    coefficients = np.linalg.solve(gram, design.T @ standardized_target / y.size)
    if not bool(np.isfinite(coefficients).all()):
        raise ValueError("ridge solver returned non-finite coefficients")
    return CellRidgeModel(
        alpha,
        int(y.size),
        feature_names,
        tuple(float(value) for value in means),
        tuple(float(value) for value in scales),
        target_mean,
        target_scale,
        tuple(float(value) for value in coefficients),
    )


def _fit_cell_models(
    training: SplitData,
    alpha: float,
    views: Mapping[int, tuple[FloatArray, tuple[str, ...]]],
) -> dict[str, CellRidgeModel]:
    fitted: dict[str, CellRidgeModel] = {}
    for cell in CELLS:
        outcome_index, horizon = _target_for_cell(cell)
        mask = (training.horizons == horizon) & np.isfinite(training.targets[:, outcome_index])
        matrix, names = views[outcome_index]
        fitted[cell.name] = fit_cell_model(
            matrix[mask],
            training.targets[mask, outcome_index],
            names,
            alpha,
        )
    return fitted


def _prediction_from_cell_models(
    data: SplitData,
    cell_models: Mapping[str, CellRidgeModel],
    views: Mapping[int, tuple[FloatArray, tuple[str, ...]]],
) -> FloatArray:
    predictions = np.empty((data.rows, len(TARGET_FIELDS)), dtype=np.float64)
    for cell in CELLS:
        outcome_index, horizon = _target_for_cell(cell)
        mask = data.horizons == horizon
        matrix, names = views[outcome_index]
        model = cell_models[cell.name]
        predictions[mask, outcome_index] = model.predict(matrix[mask], names)
    if not bool(np.isfinite(predictions).all()):
        raise ValueError("model predictions are non-finite or incomplete")
    return predictions


def _views_for_split(
    data: SplitData, variant: str
) -> dict[int, tuple[FloatArray, tuple[str, ...]]]:
    return {outcome_index: _matrix_view(data, variant, outcome_index) for outcome_index in range(2)}


def score_predictions(data: SplitData, predictions: FloatArray) -> dict[str, object]:
    values = cell_values_from_arrays(data.horizons, data.targets, predictions)
    metrics = cellwise_normalized_rmse(
        values,
        CELLS,
        minimum_rows_per_cell=2,
        require_nonzero_standard_deviation=True,
    )
    aggregate = _registered_metric(values)
    return {
        "mean_six_cell_nrmse": aggregate,
        "unclipped_research_progress": 1.0 - aggregate,
        "cells": [
            {
                "cell": item.cell.name,
                "rows": item.row_count,
                "rmse": item.root_mean_square_error,
                "truth_population_sd": item.observation_standard_deviation,
                "nrmse": item.normalized_error,
            }
            for item in metrics
        ],
    }


def _select_alpha(
    training: SplitData,
    development: SplitData,
    variant: str,
) -> tuple[dict[str, CellRidgeModel], dict[str, object]]:
    training_views = _views_for_split(training, variant)
    development_views = _views_for_split(development, variant)
    best_models: dict[str, CellRidgeModel] | None = None
    best_score = math.inf
    best_alpha = math.inf
    score_path: list[dict[str, float]] = []
    for alpha in RIDGE_ALPHA_GRID:
        models = _fit_cell_models(training, alpha, training_views)
        predictions = _prediction_from_cell_models(development, models, development_views)
        score = cast(float, score_predictions(development, predictions)["mean_six_cell_nrmse"])
        score_path.append({"alpha": alpha, "development_mean_six_cell_nrmse": score})
        if score < best_score or (score == best_score and alpha < best_alpha):
            best_score = score
            best_alpha = alpha
            best_models = models
    if best_models is None:
        raise RuntimeError("fixed ridge alpha grid produced no fitted model")
    selected_alpha = next(model.alpha for model in best_models.values())
    selected_predictions = _prediction_from_cell_models(development, best_models, development_views)
    return best_models, {
        "variant": variant,
        "selected_alpha": selected_alpha,
        "alpha_grid": list(RIDGE_ALPHA_GRID),
        "alpha_scores": score_path,
        "selection_rule": "minimum development six-cell mean NRMSE; ties choose lower alpha",
        "development_result": score_predictions(development, selected_predictions),
    }


def _constant_values(
    data: SplitData, camp_subset: frozenset[int] | None = None
) -> dict[str, float]:
    result: dict[str, float] = {}
    for cell in CELLS:
        outcome_index, horizon = _target_for_cell(cell)
        mask = (data.horizons == horizon) & np.isfinite(data.targets[:, outcome_index])
        if camp_subset is not None:
            mask &= np.isin(data.camps, tuple(camp_subset))
        labels = data.targets[mask, outcome_index]
        if labels.size < 2:
            raise ValueError(f"training constant has fewer than two labels for {cell.name}")
        result[cell.name] = float(labels.mean())
    return result


def _predict_spec(data: SplitData, specification: Mapping[str, object]) -> FloatArray:
    kind = str(specification["kind"])
    if kind == "zero_innovation":
        return np.zeros((data.rows, len(TARGET_FIELDS)), dtype=np.float64)
    if kind == "training_constant":
        values = cast(Mapping[str, float], specification["values"])
        predictions = np.empty((data.rows, len(TARGET_FIELDS)), dtype=np.float64)
        for cell in CELLS:
            outcome_index, horizon = _target_for_cell(cell)
            predictions[data.horizons == horizon, outcome_index] = float(values[cell.name])
        return predictions
    if kind != "cellwise_ridge":
        raise ValueError(f"unsupported locked model kind: {kind}")
    variant = str(specification["variant"])
    raw_models = cast(Mapping[str, Mapping[str, object]], specification["cells"])
    models = {name: CellRidgeModel.from_record(record) for name, record in raw_models.items()}
    views = _views_for_split(data, variant)
    return _prediction_from_cell_models(data, models, views)


def _ridge_spec(variant: str, models: Mapping[str, CellRidgeModel]) -> dict[str, object]:
    return {
        "kind": "cellwise_ridge",
        "variant": variant,
        "selected_alpha": next(iter(models.values())).alpha,
        "cells": {name: model.to_record() for name, model in models.items()},
    }


def _campaign_permutation(camp_count: int) -> tuple[int, ...]:
    return tuple(
        int(index)
        for index in np.random.default_rng(SAMPLE_EFFICIENCY_SEED).permutation(camp_count)
    )


def _selection_lock(
    interface: PublicDatasetInterface,
    training: SplitData,
    development: SplitData,
    *,
    study_git_sha: str,
) -> tuple[dict[str, object], dict[str, float]]:
    assert_disjoint_splits(training, development)
    compute: dict[str, float] = {
        "training_generation_seconds": training.generation_seconds,
        "development_generation_seconds": development.generation_seconds,
    }
    models: dict[str, object] = {
        "zero_innovation": {"kind": "zero_innovation"},
        "training_constant": {"kind": "training_constant", "values": _constant_values(training)},
    }
    selection: dict[str, object] = {}
    dev_predictions = {
        "zero_innovation": _predict_spec(
            development, cast(Mapping[str, object], models["zero_innovation"])
        ),
        "training_constant": _predict_spec(
            development, cast(Mapping[str, object], models["training_constant"])
        ),
    }
    development_results: dict[str, object] = {
        name: score_predictions(development, predictions)
        for name, predictions in dev_predictions.items()
    }

    variants = (
        ("ridge_full", "ridge_full"),
        ("structured_full", "structured_full"),
        ("ridge_no_prior_history", "ridge_no_prior_history"),
        ("ridge_no_current_exposure", "ridge_no_current_exposure"),
        ("ridge_no_participant_context", "ridge_no_participant_context"),
        ("structured_no_prior_history", "structured_no_prior_history"),
    )
    for model_name, variant in variants:
        started = time.perf_counter()
        fitted, selection_record = _select_alpha(training, development, variant)
        compute[f"selection_{model_name}_seconds"] = time.perf_counter() - started
        models[model_name] = _ridge_spec(variant, fitted)
        selection[model_name] = selection_record
        development_results[model_name] = selection_record["development_result"]

    sample_order = _campaign_permutation(training.camp_count)
    sample_plan: dict[str, list[int]] = {}
    for count in SAMPLE_EFFICIENCY_CAMP_COUNTS:
        selected_camps = tuple(sample_order[:count])
        sample_plan[str(count)] = list(selected_camps)
        row_mask = np.isin(training.camps, selected_camps)
        subset = SplitData(
            training.split,
            training.root_seed,
            training.seed_kind,
            int(row_mask.sum()),
            count,
            training.features[row_mask],
            training.targets[row_mask],
            training.horizons[row_mask],
            training.camps[row_mask],
            training.key_sets,
            training.sha256,
            0.0,
        )
        models[f"training_constant_n{count}"] = {
            "kind": "training_constant",
            "values": _constant_values(subset),
        }
        if count == training.camp_count:
            models[f"ridge_n{count}"] = models["ridge_full"]
            models[f"structured_n{count}"] = models["structured_full"]
        else:
            for name in ("ridge_full", "structured_full"):
                locked = cast(Mapping[str, object], models[name])
                variant = str(locked["variant"])
                alpha = _record_float(locked["selected_alpha"], "selected_alpha")
                started = time.perf_counter()
                views = _views_for_split(subset, variant)
                fitted = _fit_cell_models(subset, alpha, views)
                compute[f"sample_efficiency_{name}_n{count}_seconds"] = (
                    time.perf_counter() - started
                )
                model_name = "ridge" if name == "ridge_full" else "structured"
                models[f"{model_name}_n{count}"] = _ridge_spec(variant, fitted)
    for model_name, specification in models.items():
        if model_name in development_results:
            continue
        predictions = _predict_spec(development, cast(Mapping[str, object], specification))
        development_results[model_name] = score_predictions(development, predictions)

    protocol = protocol_record()
    lock: dict[str, object] = {
        "lock_version": 1,
        "study_code_sha": study_git_sha,
        "package_source_sha256": package_source_sha256(),
        "base_public_main": BASE_MAIN_SHA,
        "benchmark": BENCHMARK_NAME,
        "dataset": DATASET_NAME,
        "generator_identity": interface.generator_identity,
        "protocol": protocol,
        "protocol_sha256": _sha256(protocol),
        "data": {"training": _split_record(training), "development": _split_record(development)},
        "feature_contract": _feature_contract(),
        "selection_rule": (
            "train on public training camps; select alpha only on public development camps"
        ),
        "selection": selection,
        "development_results": development_results,
        "sample_efficiency_camp_order": list(sample_order),
        "sample_efficiency_subsets": sample_plan,
        "models": models,
        "no_test_data_used_for_selection": True,
    }
    lock["selection_lock_sha256"] = _sha256(lock)
    return lock, compute


def _verify_selection_lock(lock: Mapping[str, object], study_git_sha: str) -> None:
    if lock.get("lock_version") != 1 or lock.get("study_code_sha") != study_git_sha:
        raise ValueError("selection lock version or study commit does not match the evaluator")
    if lock.get("package_source_sha256") != package_source_sha256():
        raise ValueError(
            "installed study package differs from the content-addressed selection lock"
        )
    protocol = cast(Mapping[str, object], lock.get("protocol"))
    if _sha256(protocol) != lock.get("protocol_sha256") or _sha256(protocol) != _sha256(
        protocol_record()
    ):
        raise ValueError("selection lock protocol does not match the frozen evaluation protocol")
    expected_digest = str(lock.get("selection_lock_sha256"))
    without_digest = dict(lock)
    without_digest.pop("selection_lock_sha256", None)
    if _sha256(without_digest) != expected_digest:
        raise ValueError("selection lock digest is invalid")
    if lock.get("no_test_data_used_for_selection") is not True:
        raise ValueError("selection lock must explicitly exclude test-root outcomes")


def _cell_camp_statistics(
    data: SplitData,
    predictions: FloatArray,
    camp_values: Sequence[int],
) -> dict[str, FloatArray]:
    camp_n = np.zeros((len(camp_values), len(CELLS)), dtype=np.float64)
    camp_sum_y = np.zeros_like(camp_n)
    camp_sum_y2 = np.zeros_like(camp_n)
    camp_sse = np.zeros_like(camp_n)
    for cell_index, cell in enumerate(CELLS):
        outcome_index, horizon = _target_for_cell(cell)
        horizon_mask = data.horizons == horizon
        y = data.targets[:, outcome_index]
        p = predictions[:, outcome_index]
        valid = horizon_mask & np.isfinite(y)
        if not bool(np.isfinite(p[valid]).all()):
            raise ValueError(f"non-finite prediction in bootstrap cell {cell.name}")
        for camp_position, camp_value in enumerate(camp_values):
            mask = valid & (data.camps == camp_value)
            observed = y[mask]
            residual = p[mask] - observed
            camp_n[camp_position, cell_index] = observed.size
            camp_sum_y[camp_position, cell_index] = float(observed.sum())
            camp_sum_y2[camp_position, cell_index] = float(observed @ observed)
            camp_sse[camp_position, cell_index] = float(residual @ residual)
    return {"n": camp_n, "sum_y": camp_sum_y, "sum_y2": camp_sum_y2, "sse": camp_sse}


def camp_bootstrap_intervals(
    data: SplitData,
    predictions_by_model: Mapping[str, FloatArray],
) -> dict[str, object]:
    camp_values = tuple(sorted(int(value) for value in np.unique(data.camps)))
    if len(camp_values) != data.camp_count:
        raise ValueError("bootstrap requires all registered public camps")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sampled = rng.integers(
        0,
        len(camp_values),
        size=(BOOTSTRAP_REPLICATES, len(camp_values)),
        endpoint=False,
    )
    counts = np.stack(
        [np.bincount(row, minlength=len(camp_values)) for row in sampled], axis=0
    ).astype(np.float64)
    stats = {
        name: _cell_camp_statistics(data, predictions, camp_values)
        for name, predictions in predictions_by_model.items()
    }
    aggregate: dict[str, NDArray[np.float64]] = {}
    valid_by_model: dict[str, NDArray[np.bool_]] = {}
    for name, values in stats.items():
        n = counts @ values["n"]
        sum_y = counts @ values["sum_y"]
        sum_y2 = counts @ values["sum_y2"]
        sse = counts @ values["sse"]
        mean_y = np.divide(sum_y, n, out=np.zeros_like(sum_y), where=n > 0.0)
        variance = np.maximum(
            np.divide(sum_y2, n, out=np.zeros_like(sum_y2), where=n > 0.0) - mean_y * mean_y,
            0.0,
        )
        valid = (n >= 2.0) & (variance > 0.0) & np.isfinite(sse) & np.isfinite(variance)
        rmse = np.sqrt(np.maximum(np.divide(sse, n, out=np.zeros_like(sse), where=n > 0.0), 0.0))
        nrmse = np.divide(
            rmse, np.sqrt(variance), out=np.full_like(rmse, np.nan), where=variance > 0.0
        )
        valid_by_model[name] = np.all(valid, axis=1) & np.isfinite(nrmse).all(axis=1)
        aggregate[name] = nrmse.mean(axis=1)
    zero = aggregate.get("zero_innovation")
    zero_valid = valid_by_model.get("zero_innovation")
    if zero is None or zero_valid is None:
        raise ValueError("paired bootstrap requires the zero-innovation baseline")
    result: dict[str, object] = {
        "cluster": "camp; 250 episodes and three horizons stay together",
        "represented_camps": len(camp_values),
        "replicates_requested": BOOTSTRAP_REPLICATES,
        "seed": BOOTSTRAP_SEED,
        "invalid_replicates_by_model": {},
        "models": {},
    }
    invalids = cast(dict[str, int], result["invalid_replicates_by_model"])
    summaries = cast(dict[str, object], result["models"])
    for name, values in aggregate.items():
        valid = valid_by_model[name] & zero_valid
        valid_values = values[valid]
        paired_delta = values[valid] - zero[valid]
        if valid_values.size == 0:
            raise ValueError(f"no valid paired camp-bootstrap replicates for {name}")
        nrmse_interval = np.quantile(valid_values, (0.025, 0.975))
        delta_interval = np.quantile(paired_delta, (0.025, 0.975))
        invalids[name] = int(BOOTSTRAP_REPLICATES - valid_values.size)
        summaries[name] = {
            "valid_replicates": int(valid_values.size),
            "mean_six_cell_nrmse_95_percentile_interval": [
                float(nrmse_interval[0]),
                float(nrmse_interval[1]),
            ],
            "paired_nrmse_delta_vs_zero_95_percentile_interval": [
                float(delta_interval[0]),
                float(delta_interval[1]),
            ],
        }
    return result


def _runtime_record() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "numpy": np.__version__,
        "os": platform.system(),
        "architecture": platform.machine(),
    }


def _cost_record(
    lock_wrapper: Mapping[str, object], evaluation_seconds: float
) -> dict[str, object]:
    selection_costs = cast(Mapping[str, float], lock_wrapper.get("selection_costs", {}))
    return {
        "selection_stage_wall_seconds": dict(selection_costs),
        "evaluation_stage_wall_seconds": evaluation_seconds,
    }


def _root_summary(roots: Sequence[Mapping[str, object]]) -> dict[str, object]:
    model_names = tuple(cast(Mapping[str, object], roots[0]["models"]))
    summary: dict[str, object] = {}
    for name in model_names:
        model_rows = [
            cast(Mapping[str, object], cast(Mapping[str, object], root["models"])[name])
            for root in roots
        ]
        values = [
            _record_float(item["mean_six_cell_nrmse"], "mean_six_cell_nrmse") for item in model_rows
        ]
        deltas = [
            _record_float(item["paired_nrmse_delta_vs_zero"], "paired_nrmse_delta_vs_zero")
            for item in model_rows
        ]
        per_root_cells = [
            {
                str(cast(Mapping[str, object], cell)["cell"]): cast(Mapping[str, object], cell)
                for cell in cast(Sequence[object], model["cells"])
            }
            for model in model_rows
        ]
        cell_summary: dict[str, object] = {}
        for cell in CELLS:
            cell_values = [
                _record_float(row_cells[cell.name]["nrmse"], f"{cell.name} nrmse")
                for row_cells in per_root_cells
            ]
            cell_summary[cell.name] = {
                "root_mean_nrmse": float(np.mean(cell_values)),
                "root_sample_sd_nrmse": float(np.std(cell_values, ddof=1)),
                "root_min_nrmse": float(min(cell_values)),
                "root_max_nrmse": float(max(cell_values)),
                "root_values": cell_values,
            }
        summary[name] = {
            "root_mean_nrmse": float(np.mean(values)),
            "root_sample_sd_nrmse": float(np.std(values, ddof=1)),
            "root_min_nrmse": float(min(values)),
            "root_max_nrmse": float(max(values)),
            "root_mean_delta_vs_zero": float(np.mean(deltas)),
            "root_sample_sd_delta_vs_zero": float(np.std(deltas, ddof=1)),
            "root_values": values,
            "root_deltas_vs_zero": deltas,
            "cell_nrmse_across_roots": cell_summary,
        }
    return summary


def _scientific_digest(result: Mapping[str, object]) -> str:
    stable = {
        key: value
        for key, value in result.items()
        if key not in {"compute_costs", "scientific_results_sha256"}
    }
    return _sha256(stable)


def run_pilot(study_git_sha: str) -> dict[str, object]:
    _check_metric_path()
    interface = get_public_dataset_interface(BENCHMARK_NAME)
    training = _read_public_split(interface, TRAINING_SPLIT, camp_limit=PILOT_TRAIN_CAMPS)
    development = _read_public_split(
        interface, DEVELOPMENT_SPLIT, camp_limit=PILOT_DEVELOPMENT_CAMPS
    )
    assert_disjoint_splits(training, development)
    zero = np.zeros((development.rows, len(TARGET_FIELDS)), dtype=np.float64)
    score = score_predictions(development, zero)
    return {
        "study": "RES-526 deterministic pilot; no evaluation test roots used",
        "study_code_sha": study_git_sha,
        "generator_identity": interface.generator_identity,
        "feature_contract": _feature_contract(),
        "training": _split_record(training),
        "development": _split_record(development),
        "key_intersections": {field: 0 for field in ROW_KEY_FIELDS},
        "zero_baseline_development_result": score,
        "pilot_seconds": training.generation_seconds + development.generation_seconds,
    }


def run_selection(study_git_sha: str) -> dict[str, object]:
    _check_metric_path()
    interface = get_public_dataset_interface(BENCHMARK_NAME)
    training = _read_public_split(interface, TRAINING_SPLIT)
    development = _read_public_split(interface, DEVELOPMENT_SPLIT)
    started = time.perf_counter()
    lock, selection_costs = _selection_lock(
        interface, training, development, study_git_sha=study_git_sha
    )
    selection_costs["full_train_development_selection_seconds"] = time.perf_counter() - started
    return {"selection_lock": lock, "selection_costs": selection_costs}


def run_evaluation(lock_wrapper: Mapping[str, object], study_git_sha: str) -> dict[str, object]:
    lock = cast(Mapping[str, object], lock_wrapper.get("selection_lock"))
    _verify_selection_lock(lock, study_git_sha)
    protocol = cast(Mapping[str, object], lock["protocol"])
    if tuple(cast(list[str], protocol["test_roots"])) != TEST_ROOTS:
        raise ValueError("selection lock test roots do not match the frozen root list")
    interface = get_public_dataset_interface(BENCHMARK_NAME)
    if interface.generator_identity != "fixed_mode_discrepancy_world":
        raise ValueError("evaluation interface does not match the frozen generator identity")
    training_record = cast(
        Mapping[str, object], cast(Mapping[str, object], lock["data"])["training"]
    )
    development_record = cast(
        Mapping[str, object], cast(Mapping[str, object], lock["data"])["development"]
    )
    source_roots = {str(training_record["root_seed"]), str(development_record["root_seed"])}
    if _TEST_ROOT_SET.intersection(source_roots):
        raise ValueError("evaluation roots overlap public training or development roots")
    source_camp_units = camp_unit_ids(
        str(training_record["split"]),
        str(training_record["root_seed"]),
        _record_int(training_record["camps"], "training_camps"),
    ) | camp_unit_ids(
        str(development_record["split"]),
        str(development_record["root_seed"]),
        _record_int(development_record["camps"], "development_camps"),
    )
    specifications = cast(Mapping[str, Mapping[str, object]], lock["models"])
    roots: list[dict[str, object]] = []
    test_key_sets: dict[str, list[frozenset[str]]] = {field: [] for field in ROW_KEY_FIELDS}
    evaluation_started = time.perf_counter()
    for root_index, root_seed in enumerate(TEST_ROOTS):
        seed = interface.make_seed_identity(TEST_SPLIT, root_seed)
        if seed.kind is not SeedKind.CALLER_SUPPLIED_PUBLIC:
            raise ValueError("independent evaluation roots must be caller-supplied public seeds")
        data = _read_public_split(interface, TEST_SPLIT, seed_identity=seed)
        if data.camp_count != SPLIT_GEOMETRY["validation"].camps:
            raise ValueError("evaluation root does not preserve public validation camp geometry")
        if data.root_seed in source_roots:
            raise ValueError("evaluation seed reused a training or development source root")
        if source_camp_units.intersection(
            camp_unit_ids(data.split, data.root_seed, data.camp_count)
        ):
            raise ValueError("evaluation camp/episode units overlap training or development")
        for key_field in ROW_KEY_FIELDS:
            previous = test_key_sets[key_field]
            if any(data.key_sets[key_field].intersection(keys) for keys in previous):
                raise ValueError(f"independent evaluation roots share {key_field} values")
            previous.append(data.key_sets[key_field])

        predictions = {
            name: _predict_spec(data, specification)
            for name, specification in specifications.items()
        }
        model_results: dict[str, object] = {}
        zero_metric = cast(
            float,
            score_predictions(data, predictions["zero_innovation"])["mean_six_cell_nrmse"],
        )
        for name, prediction in predictions.items():
            result = score_predictions(data, prediction)
            result["paired_nrmse_delta_vs_zero"] = (
                cast(float, result["mean_six_cell_nrmse"]) - zero_metric
            )
            result["paired_unclipped_progress_delta_vs_zero"] = -float(
                result["paired_nrmse_delta_vs_zero"]
            )
            model_results[name] = result
        bootstrap = camp_bootstrap_intervals(data, predictions)
        roots.append(
            {
                "root_id": f"test_root_{root_index + 1}",
                "root_seed": root_seed,
                "seed_kind": seed.kind.value,
                "split": TEST_SPLIT,
                "data": _split_record(data),
                "models": model_results,
                "paired_camp_bootstrap": bootstrap,
            }
        )
    evaluation_seconds = time.perf_counter() - evaluation_started
    result: dict[str, object] = {
        "study": {
            "name": "RES-526 fixed-mode public reference-model study",
            "classification": "new synthetic research study; not a historical replay",
            "base_public_main": BASE_MAIN_SHA,
            "study_code_sha": study_git_sha,
            "package_source_sha256": package_source_sha256(),
            "benchmark": BENCHMARK_NAME,
            "dataset": DATASET_NAME,
            "production_score_claim": False,
            "historical_private_score_use": False,
            "human_data_use": False,
        },
        "runtime": _runtime_record(),
        "protocol": protocol,
        "protocol_sha256": lock["protocol_sha256"],
        "selection_lock_sha256": lock["selection_lock_sha256"],
        "feature_contract": lock["feature_contract"],
        "data": lock["data"],
        "selection": lock["selection"],
        "development_results": lock["development_results"],
        "independent_test_roots": roots,
        "across_root_variability": _root_summary(roots),
        "compute_costs": _cost_record(lock_wrapper, evaluation_seconds),
        "claim_boundary": (
            "Results describe the declared clean-room training/development splits and three new "
            "caller-supplied public validation-geometry populations only. They do not use hidden "
            "generator effects or oracle states, replay historical private scores, establish "
            "empirical athlete performance, or qualify a production benchmark score."
        ),
    }
    result["scientific_results_sha256"] = _scientific_digest(result)
    return result


def _write_json(value: object, output: str | None) -> None:
    rendered = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    if output is None or output == "-":
        sys.stdout.write(rendered)
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pilot", "select", "evaluate"))
    parser.add_argument("--output", help="JSON output path; defaults to stdout")
    parser.add_argument("--lock", help="selection-lock JSON produced by the select stage")
    parser.add_argument("--git-sha", required=True, help="full Git SHA of the frozen study code")
    args = parser.parse_args()
    if len(args.git_sha) != 40 or any(
        character not in "0123456789abcdef" for character in args.git_sha
    ):
        parser.error("--git-sha must be a full lowercase 40-character SHA")
    if args.stage == "pilot":
        result = run_pilot(args.git_sha)
        _write_json(result, args.output)
        return
    if args.stage == "select":
        result = run_selection(args.git_sha)
        if args.output is None or args.output == "-":
            parser.error("select requires --output so the lock is written before test evaluation")
        _write_json(result, args.output)
        return
    if args.lock is None:
        parser.error("evaluate requires --lock from a completed select stage")
    lock_wrapper = json.loads(Path(args.lock).read_text(encoding="utf-8"))
    if not isinstance(lock_wrapper, Mapping):
        parser.error("selection lock file must contain a JSON object")
    result = run_evaluation(cast(Mapping[str, object], lock_wrapper), args.git_sha)
    _write_json(result, args.output)


if __name__ == "__main__":
    main()
