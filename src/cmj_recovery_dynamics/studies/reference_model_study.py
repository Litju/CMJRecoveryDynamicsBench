"""New public zero/ridge comparison for the rich-history formulation."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import cast

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.contracts import ForecastHorizon, OutcomeVariable, TargetCell
from cmj_recovery_dynamics.metrics.scoring import (
    RICH_HISTORY_CELLS,
    CellMetric,
    CellValues,
    MetricInputError,
    cellwise_normalized_rmse,
)
from cmj_recovery_dynamics.reproducibility.execution import (
    get_metric_implementation,
    get_model_execution_contract,
)
from cmj_recovery_dynamics.reproducibility.registry import get_public_dataset_interface
from cmj_recovery_dynamics.reproduction.rich_history import (
    CATEGORICAL_FIELDS,
    GENERATOR_VERSION,
    HORIZON_TARGET_COLUMNS,
    MISSING,
    NUMERIC_FIELDS,
    PUBLIC_SPLITS,
    R02_FIELD_NAMES,
    SCHEMA_DIGEST,
    SCHEMA_IDENTITY,
    RichHistoryRow,
    iter_rich_history_public_split,
)

FloatArray = NDArray[np.float64]

BASE_MAIN_SHA = "16dac3f"
BENCHMARK_NAME = "rich_history_camp_recovery"
EXPERIMENT_NAME = "rich_history_headroom_reconstruction"
BOOTSTRAP_REPLICATES = 500
BOOTSTRAP_SEED = 20261017
RIDGE_ALPHAS = (0.1, 1.0, 10.0)
PRIMARY_ALPHA = 1.0
SENSITIVITY_ALPHAS = tuple(alpha for alpha in RIDGE_ALPHAS if alpha != PRIMARY_ALPHA)
UNKNOWN_CATEGORY = "<UNKNOWN>"
EXCLUDED_FEATURES = frozenset({"target_time_hours"})
PREDICTOR_FIELDS = tuple(name for name in R02_FIELD_NAMES if name not in EXCLUDED_FEATURES)
NUMERIC_PREDICTORS = tuple(name for name in NUMERIC_FIELDS if name in PREDICTOR_FIELDS)
CATEGORICAL_PREDICTORS = tuple(name for name in R02_FIELD_NAMES if name in CATEGORICAL_FIELDS)
OUTCOMES = tuple(OutcomeVariable)
_FIELD_SET = frozenset(R02_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class FeatureEncoder:
    numeric_fields: tuple[str, ...]
    numeric_means: tuple[float, ...]
    categorical_levels: tuple[tuple[str, tuple[str, ...]], ...]
    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]

    def transform(self, rows: Sequence[RichHistoryRow]) -> FloatArray:
        raw = _raw_feature_matrix(
            rows,
            self.numeric_fields,
            self.numeric_means,
            self.categorical_levels,
        )
        transformed = (raw - np.asarray(self.feature_means)) / np.asarray(self.feature_scales)
        if not bool(np.isfinite(transformed).all()):
            raise ValueError("feature encoding produced non-finite values")
        return transformed


@dataclass(frozen=True, slots=True)
class RidgeFit:
    coefficients: FloatArray
    target_mean: float
    target_scale: float
    alpha: float
    training_rows: int

    def predict(self, features: FloatArray) -> FloatArray:
        if features.ndim != 2 or features.shape[1] + 1 != self.coefficients.shape[0]:
            raise ValueError("ridge prediction feature dimensions do not match the fitted model")
        design = np.column_stack((np.ones(features.shape[0]), features))
        prediction = (design @ self.coefficients) * self.target_scale + self.target_mean
        if not bool(np.isfinite(prediction).all()):
            raise ValueError("ridge model produced non-finite predictions")
        return prediction


def _numeric_or_missing(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"numeric R02 predictor is not a real number: {value!r}")
    numeric = float(value)
    if math.isnan(numeric):
        return None
    if not math.isfinite(numeric):
        raise ValueError("numeric R02 predictors must not be infinite")
    return numeric


def _category(value: object) -> str:
    if value is None:
        return MISSING
    category = str(value)
    if category in ("", "nan", "None", MISSING):
        return MISSING
    if category == UNKNOWN_CATEGORY:
        raise ValueError("categorical value collides with the reserved unknown token")
    return category


def _validate_rows(rows: Sequence[RichHistoryRow]) -> None:
    if not rows:
        raise ValueError("public split must contain at least one row")
    for row in rows:
        if frozenset(row.fields) != _FIELD_SET:
            raise ValueError("rich-history row fields do not match the fixed R02 schema")
        if frozenset(row.labels) != frozenset(HORIZON_TARGET_COLUMNS):
            raise ValueError("rich-history row labels do not match the two target contract")


def _feature_names(
    numeric_fields: Sequence[str],
    categorical_levels: Sequence[tuple[str, tuple[str, ...]]],
) -> tuple[str, ...]:
    names = [name for field in numeric_fields for name in (field, f"{field}__missing")]
    names.extend(
        f"{field}=={category}"
        for field, categories in categorical_levels
        for category in categories
    )
    return tuple(names)


def _raw_feature_matrix(
    rows: Sequence[RichHistoryRow],
    numeric_fields: Sequence[str],
    numeric_means: Sequence[float],
    categorical_levels: Sequence[tuple[str, tuple[str, ...]]],
) -> FloatArray:
    _validate_rows(rows)
    if len(numeric_fields) != len(numeric_means):
        raise ValueError("numeric feature means do not match the feature contract")
    column_count = 2 * len(numeric_fields) + sum(
        len(categories) for _, categories in categorical_levels
    )
    matrix = np.zeros((len(rows), column_count), dtype=np.float64)
    column = 0
    for field, train_mean in zip(numeric_fields, numeric_means, strict=True):
        for row_index, row in enumerate(rows):
            value = _numeric_or_missing(row.fields[field])
            matrix[row_index, column] = train_mean if value is None else value
            matrix[row_index, column + 1] = float(value is None)
        column += 2
    for field, categories in categorical_levels:
        category_indexes = {value: index for index, value in enumerate(categories)}
        unknown_index = category_indexes[UNKNOWN_CATEGORY]
        for row_index, row in enumerate(rows):
            value = _category(row.fields[field])
            category_index = category_indexes.get(value, unknown_index)
            matrix[row_index, column + category_index] = 1.0
        column += len(categories)
    return matrix


def fit_feature_encoder(rows: Sequence[RichHistoryRow]) -> tuple[FeatureEncoder, FloatArray]:
    """Fit imputation, category vocabulary, and scaling on training features only."""
    _validate_rows(rows)
    if set(NUMERIC_PREDICTORS).union(CATEGORICAL_PREDICTORS) != set(PREDICTOR_FIELDS):
        raise RuntimeError("R02 numeric and categorical fields do not cover the fixed predictors")
    numeric_means: list[float] = []
    for field in NUMERIC_PREDICTORS:
        observed = [
            value for row in rows if (value := _numeric_or_missing(row.fields[field])) is not None
        ]
        numeric_means.append(float(np.mean(observed)) if observed else 0.0)
    categorical_levels = tuple(
        (
            field,
            tuple(
                sorted({_category(row.fields[field]) for row in rows} | {MISSING, UNKNOWN_CATEGORY})
            ),
        )
        for field in CATEGORICAL_PREDICTORS
    )
    raw = _raw_feature_matrix(rows, NUMERIC_PREDICTORS, numeric_means, categorical_levels)
    feature_means = raw.mean(axis=0)
    feature_scales = raw.std(axis=0, ddof=0)
    feature_scales[feature_scales == 0.0] = 1.0
    encoder = FeatureEncoder(
        NUMERIC_PREDICTORS,
        tuple(numeric_means),
        categorical_levels,
        _feature_names(NUMERIC_PREDICTORS, categorical_levels),
        tuple(float(value) for value in feature_means),
        tuple(float(value) for value in feature_scales),
    )
    transformed = encoder.transform(rows)
    return encoder, transformed


def fit_ridge(features: FloatArray, targets: Sequence[float], *, alpha: float) -> RidgeFit:
    """Fit standardized ridge with an unpenalized intercept and fixed alpha."""
    y = np.asarray(targets, dtype=np.float64)
    if features.ndim != 2 or features.shape[0] != y.shape[0] or y.size < 2:
        raise ValueError("ridge inputs require matching two-dimensional features and two labels")
    if not bool(np.isfinite(features).all()) or not bool(np.isfinite(y).all()):
        raise ValueError("ridge training inputs must be finite")
    if isinstance(alpha, bool) or not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError("ridge alpha must be finite and positive")
    target_mean = float(y.mean())
    target_scale = float(y.std(ddof=0))
    if target_scale == 0.0:
        target_scale = 1.0
    standardized_target = (y - target_mean) / target_scale
    design = np.column_stack((np.ones(features.shape[0]), features))
    gram = design.T @ design / y.size
    gram[1:, 1:] += alpha * np.eye(features.shape[1])
    coefficients = np.linalg.solve(gram, design.T @ standardized_target / y.size)
    if not bool(np.isfinite(coefficients).all()):
        raise ValueError("ridge solver produced non-finite coefficients")
    return RidgeFit(coefficients, target_mean, target_scale, alpha, int(y.size))


def _target_value(row: RichHistoryRow, column: str) -> float | None:
    value = row.labels[column]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f"observed target {column} must be finite and numeric")
    return float(value)


def build_cell_values(
    rows: Sequence[RichHistoryRow], predictions: FloatArray, indices: Sequence[int] | None = None
) -> tuple[CellValues, ...]:
    if predictions.shape != (len(rows), len(OUTCOMES)):
        raise ValueError("predictions must contain one force and impulse value per row")
    selected = range(len(rows)) if indices is None else indices
    buckets: dict[TargetCell, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    horizon_by_name = {
        horizon.label: horizon for horizon in (ForecastHorizon.H72, ForecastHorizon.D7)
    }
    for row_index in selected:
        row = rows[row_index]
        try:
            horizon = horizon_by_name[str(row.fields["horizon"])]
        except KeyError as exc:
            raise ValueError("rich-history horizon is outside the H72/D7 target contract") from exc
        for outcome_index, column in enumerate(HORIZON_TARGET_COLUMNS):
            target = _target_value(row, column)
            if target is None:
                continue
            cell = TargetCell(OUTCOMES[outcome_index], horizon, row.stratum)
            if cell not in RICH_HISTORY_CELLS:
                raise ValueError(
                    f"generated target cell is outside the native contract: {cell.name}"
                )
            predicted, observed = buckets[cell]
            predicted.append(float(predictions[row_index, outcome_index]))
            observed.append(target)
    return tuple(
        CellValues(cell, tuple(buckets[cell][0]), tuple(buckets[cell][1]))
        for cell in RICH_HISTORY_CELLS
        if cell in buckets
    )


def _registered_raw_progress(cells: Sequence[CellValues]) -> float:
    binding = get_metric_implementation("rich_history_raw_progress_diagnostic")
    if not callable(binding.implementation):
        raise RuntimeError("registered rich-history raw-progress diagnostic is not callable")
    metric = cast(Callable[[Sequence[CellValues]], object], binding.implementation)
    value = metric(cells)
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError("registered raw-progress diagnostic returned a non-finite scalar")
    return float(value)


def _cell_results(metrics: Sequence[CellMetric]) -> list[dict[str, object]]:
    return [
        {
            "cell": item.cell.name,
            "rows": item.row_count,
            "rmse": item.root_mean_square_error,
            "validation_population_sd": item.observation_standard_deviation,
            "normalized_rmse": item.normalized_error,
            "normalized": item.normalized,
        }
        for item in metrics
    ]


def _model_result(
    name: str, rows: Sequence[RichHistoryRow], predictions: FloatArray
) -> tuple[dict[str, object], tuple[CellValues, ...]]:
    cells = build_cell_values(rows, predictions)
    metrics = cellwise_normalized_rmse(cells, RICH_HISTORY_CELLS, minimum_rows_per_cell=2)
    return (
        {
            "model": name,
            "raw_progress": _registered_raw_progress(cells),
            "mean_cell_normalized_rmse": float(
                np.mean([item.normalized_error for item in metrics])
            ),
            "cells": _cell_results(metrics),
        },
        cells,
    )


def _safe_json(value: object) -> object:
    if isinstance(value, np.generic):
        return _safe_json(cast(object, value.item()))
    if isinstance(value, float) and not math.isfinite(value):
        return "nan" if math.isnan(value) else "inf" if value > 0 else "-inf"
    if isinstance(value, Mapping):
        items = cast(Mapping[object, object], value).items()
        return {str(key): _safe_json(item) for key, item in items}
    if isinstance(value, (tuple, list)):
        items = cast(Sequence[object], value)
        return [_safe_json(item) for item in items]
    return value


def _split_digest(rows: Sequence[RichHistoryRow]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        record = row.public_mapping()
        record["split"] = row.grouping.split
        digest.update(
            json.dumps(
                _safe_json(record), sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _split_record(
    split_name: str, rows: Sequence[RichHistoryRow], expected_rows: int | None
) -> dict[str, object]:
    root_name = "public_train" if split_name == "training" else "public_validation"
    root = PUBLIC_SPLITS[root_name]
    return {
        "split": split_name,
        "root_seed": root.root_seed,
        "camps": root.camps,
        "m2_expected_rows": expected_rows,
        "observed_rows": len(rows),
        "study_input_sha256": _split_digest(rows),
        "labels": {
            column: {
                "observed": sum(_target_value(row, column) is not None for row in rows),
                "missing": sum(row.labels[column] is None for row in rows),
            }
            for column in HORIZON_TARGET_COLUMNS
        },
    }


def _ridge_predictions(
    training_rows: Sequence[RichHistoryRow],
    validation_rows: Sequence[RichHistoryRow],
    train_features: FloatArray,
    validation_features: FloatArray,
    alpha: float,
) -> tuple[FloatArray, list[dict[str, object]]]:
    predictions = np.empty((len(validation_rows), len(OUTCOMES)), dtype=np.float64)
    fit_records: list[dict[str, object]] = []
    for outcome_index, target_column in enumerate(HORIZON_TARGET_COLUMNS):
        for horizon in (ForecastHorizon.H72, ForecastHorizon.D7):
            train_indices = [
                index
                for index, row in enumerate(training_rows)
                if row.fields["horizon"] == horizon.label
                and _target_value(row, target_column) is not None
            ]
            validation_indices = [
                index
                for index, row in enumerate(validation_rows)
                if row.fields["horizon"] == horizon.label
            ]
            if len(train_indices) < 2:
                raise ValueError(
                    f"insufficient labeled training rows for {target_column}/{horizon.label}"
                )
            targets = [
                cast(float, _target_value(training_rows[index], target_column))
                for index in train_indices
            ]
            fitted = fit_ridge(train_features[train_indices], targets, alpha=alpha)
            if validation_indices:
                predictions[validation_indices, outcome_index] = fitted.predict(
                    validation_features[validation_indices]
                )
            fit_records.append(
                {
                    "target": target_column,
                    "horizon": horizon.label,
                    "training_rows": fitted.training_rows,
                    "alpha": alpha,
                }
            )
    return predictions, fit_records


def _bootstrap_delta(
    rows: Sequence[RichHistoryRow],
    zero_predictions: FloatArray,
    ridge_predictions: FloatArray,
) -> dict[str, object]:
    rows_by_camp: dict[int, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        rows_by_camp[row.grouping.camp_index].append(index)
    camps = np.asarray(sorted(rows_by_camp), dtype=np.int64)
    if camps.size < 2:
        raise ValueError("validation uncertainty requires at least two represented camps")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    deltas: list[float] = []
    invalid_replicates = 0
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled_camps = rng.choice(camps, size=camps.size, replace=True)
        indices = [index for camp in sampled_camps for index in rows_by_camp[int(camp)]]
        try:
            zero = _registered_raw_progress(build_cell_values(rows, zero_predictions, indices))
            ridge = _registered_raw_progress(build_cell_values(rows, ridge_predictions, indices))
        except MetricInputError:
            invalid_replicates += 1
            continue
        deltas.append(ridge - zero)
    if not deltas:
        raise ValueError("no valid camp-bootstrap replicates contained every score cell")
    low, high = np.quantile(np.asarray(deltas), (0.025, 0.975))
    return {
        "cluster": "validation camp",
        "represented_camps": int(camps.size),
        "replicates_requested": BOOTSTRAP_REPLICATES,
        "replicates_valid": len(deltas),
        "replicates_invalid": invalid_replicates,
        "seed": BOOTSTRAP_SEED,
        "delta_definition": "ridge alpha=1 raw progress minus zero/persistence raw progress",
        "delta_raw_progress_95_percentile_interval": [float(low), float(high)],
        "interpretation": "Conditional on the fixed public-training split and fitted models.",
    }


def run_study() -> dict[str, object]:
    training_rows = list(iter_rich_history_public_split("public_train"))
    validation_rows = list(iter_rich_history_public_split("public_validation"))
    train_encoder, train_features = fit_feature_encoder(training_rows)
    validation_features = train_encoder.transform(validation_rows)
    zero_contract = get_model_execution_contract(
        "rich_history_zero_baseline", BENCHMARK_NAME, EXPERIMENT_NAME
    )
    if not zero_contract.executable or not callable(zero_contract.implementation):
        raise RuntimeError("registered public zero/persistence baseline is not executable")
    zero_model = cast(Callable[[int, int], object], zero_contract.implementation)
    zero_predictions = np.asarray(zero_model(len(validation_rows), len(OUTCOMES)), dtype=np.float64)
    if zero_predictions.shape != (len(validation_rows), len(OUTCOMES)):
        raise ValueError("registered zero baseline returned an unexpected prediction shape")

    interface = get_public_dataset_interface(BENCHMARK_NAME)
    expected_train = interface.split_authority("training").rows
    expected_validation = interface.split_authority("public_validation").rows
    zero_result, _ = _model_result("registered_zero_persistence", validation_rows, zero_predictions)
    ridge_results: list[dict[str, object]] = []
    primary_predictions: FloatArray | None = None
    fit_count = 0
    for alpha in RIDGE_ALPHAS:
        predictions, fits = _ridge_predictions(
            training_rows,
            validation_rows,
            train_features,
            validation_features,
            alpha,
        )
        fit_count += len(fits)
        result, _ = _model_result(f"public_ridge_alpha_{alpha:g}", validation_rows, predictions)
        result["fits"] = fits
        ridge_results.append(result)
        if alpha == PRIMARY_ALPHA:
            primary_predictions = predictions
    if primary_predictions is None:
        raise RuntimeError("primary ridge alpha is absent from the fixed sensitivity set")

    zero_metrics = cast(list[dict[str, object]], zero_result["cells"])
    primary_result = next(
        item for item in ridge_results if item["model"] == f"public_ridge_alpha_{PRIMARY_ALPHA:g}"
    )
    ridge_metrics = cast(list[dict[str, object]], primary_result["cells"])
    cell_deltas = [
        cast(float, ridge["normalized_rmse"]) - cast(float, zero["normalized_rmse"])
        for zero, ridge in zip(zero_metrics, ridge_metrics, strict=True)
    ]
    feature_names_digest = hashlib.sha256(
        "\n".join(train_encoder.feature_names).encode("utf-8")
    ).hexdigest()
    return {
        "study": {
            "name": "M8 rich-history public zero/ridge baseline comparison",
            "classification": "new public synthetic experiment; not a historical model result",
            "base_public_main": BASE_MAIN_SHA,
            "benchmark": BENCHMARK_NAME,
            "formulation_status": "retired historical formulation; "
            "comparison is formulation-specific",
            "historical_reproduction_claim": False,
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "data": {
            "generator_version": GENERATOR_VERSION,
            "train": _split_record("training", training_rows, expected_train),
            "validation": _split_record("public_validation", validation_rows, expected_validation),
            "historical_dataset_identity": "not exact; generated clean-room splits are "
            "not M2 byte replays",
        },
        "feature_contract": {
            "schema_identity": SCHEMA_IDENTITY,
            "schema_sha256": SCHEMA_DIGEST,
            "source_fields": len(R02_FIELD_NAMES),
            "included_fields": len(PREDICTOR_FIELDS),
            "excluded_fields": sorted(EXCLUDED_FEATURES),
            "numeric_fields": len(NUMERIC_PREDICTORS),
            "categorical_fields": len(CATEGORICAL_PREDICTORS),
            "encoded_features": len(train_encoder.feature_names),
            "encoded_feature_names_sha256": feature_names_digest,
            "categorical_vocabulary_source": "training features only, sorted; missing and "
            "unknown reserved",
            "numeric_missingness": "train-mean imputation plus a missingness indicator per "
            "numeric field",
            "scaling": "training-feature mean and population standard deviation; zero scales set "
            "to one",
            "grouping_and_labels_as_predictors": False,
            "target_time_hours_excluded": True,
        },
        "target_contract": {
            "columns": list(HORIZON_TARGET_COLUMNS),
            "outcomes": [outcome.value for outcome in OUTCOMES],
            "horizons": [ForecastHorizon.H72.label, ForecastHorizon.D7.label],
            "cells": [cell.name for cell in RICH_HISTORY_CELLS],
            "missing_labels": "skip each missing outcome independently in fitting and scoring",
            "non_finite_labels": "rejected",
        },
        "training_budget": {
            "primary_ridge_alpha": PRIMARY_ALPHA,
            "sensitivity_alphas": list(SENSITIVITY_ALPHAS),
            "ridge_fits": fit_count,
            "primary_fits": 4,
            "fits_per_alpha": 4,
            "fit_partition": "one model per outcome and H72/D7 horizon; strata pooled",
            "selection": "no hyperparameter selection on public validation; alpha=1 is "
            "primary by declaration",
            "solver": "closed-form ridge; standardized targets; intercept unpenalized",
            "objective": "mean squared error plus alpha times squared coefficient norm",
            "training_randomness": "none; public training split order and solver are deterministic",
        },
        "evaluation": {
            "primary_metric": "registered rich_history_raw_progress_diagnostic",
            "cell_metric": "RMSE and RMSE divided by each validation cell's population SD",
            "progress": "for each outcome, average NRMSE over 12 cells (six strata across "
            "H72 and D7), clip 1-mean NRMSE to [0,1], then equally average outcomes; "
            "no unavailable final calibration",
            "zero_variance_cell": "native evaluator reports unnormalized RMSE",
            "minimum_valid_labels_per_cell": 2,
            "zero_persistence_equals_zero_innovation": True,
        },
        "models": {"zero_persistence": zero_result, "ridge_sensitivity": ridge_results},
        "comparison": {
            "primary_ridge_alpha": PRIMARY_ALPHA,
            "ridge_minus_zero_cell_normalized_rmse": cell_deltas,
            "cells_improved": sum(delta < 0.0 for delta in cell_deltas),
            "cells_tied": sum(delta == 0.0 for delta in cell_deltas),
            "cells_worse": sum(delta > 0.0 for delta in cell_deltas),
            "delta_raw_progress": cast(float, primary_result["raw_progress"])
            - cast(float, zero_result["raw_progress"]),
        },
        "uncertainty": _bootstrap_delta(validation_rows, zero_predictions, primary_predictions),
        "claim_boundary": (
            "Results describe these clean-room public synthetic splits only; they do not replay "
            "historical model scores, support empirical recovery claims, or authorize v1.0."
        ),
    }


def main() -> None:
    json.dump(
        run_study(), sys.stdout, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
