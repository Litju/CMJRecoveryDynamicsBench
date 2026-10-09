"""Executable, dependency-light baseline implementations recovered for M3."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, sqrt
from numbers import Integral

import numpy as np
from numpy.typing import ArrayLike, NDArray


class ModelInputError(ValueError):
    """Raised when model inputs do not match the recovered feature contract."""


@dataclass(frozen=True, slots=True)
class LinearBaselineParameters:
    feature_mean: tuple[float, ...]
    feature_scale: tuple[float, ...]
    coefficients: tuple[tuple[float, ...], ...]


@dataclass(frozen=True, slots=True)
class ReferenceM0Parameters:
    """M0 weights in matrix orientation (input, output); checkpoint stays external."""

    feature_mean: tuple[float, ...]
    feature_scale: tuple[float, ...]
    input_weights: tuple[tuple[float, ...], ...]
    input_bias: tuple[float, ...]
    output_weights: tuple[tuple[float, ...], ...]
    output_bias: tuple[float, ...]


def _matrix(values: ArrayLike, *, name: str, columns: int | None = None) -> NDArray[np.float64]:
    try:
        result = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ModelInputError(f"{name} must be a rectangular numeric matrix") from exc
    if result.ndim != 2 or not result.shape[0] or not result.shape[1]:
        raise ModelInputError(f"{name} must be a non-empty two-dimensional matrix")
    if columns is not None and result.shape[1] != columns:
        raise ModelInputError(f"{name} must contain exactly {columns} columns")
    if not bool(np.isfinite(result).all()):
        raise ModelInputError(f"{name} must contain only finite values")
    return result


def fit_linear_public_baseline(features: ArrayLike, targets: ArrayLike) -> LinearBaselineParameters:
    """Fit the recovered 39-feature, two-target OLS baseline with train-only scaling."""

    x = _matrix(features, name="features", columns=39)
    y = _matrix(targets, name="targets", columns=2)
    if x.shape[0] != y.shape[0] or x.shape[0] < 2:
        raise ModelInputError("features and targets need matching rows and at least two samples")
    mean = x.mean(axis=0)
    scale = x.std(axis=0, ddof=1)
    scale[scale == 0.0] = 1.0
    design = np.column_stack((np.ones(x.shape[0]), (x - mean) / scale))
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    return LinearBaselineParameters(
        tuple(float(value) for value in mean),
        tuple(float(value) for value in scale),
        tuple(tuple(float(value) for value in row) for row in coefficients),
    )


def predict_linear_public_baseline(
    features: ArrayLike, parameters: LinearBaselineParameters
) -> NDArray[np.float64]:
    x = _matrix(features, name="features", columns=len(parameters.feature_mean))
    if (
        len(parameters.feature_scale) != x.shape[1]
        or len(parameters.coefficients) != x.shape[1] + 1
    ):
        raise ModelInputError("linear baseline parameters have inconsistent feature dimensions")
    mean = np.asarray(parameters.feature_mean)
    scale = np.asarray(parameters.feature_scale)
    coefficients = np.asarray(parameters.coefficients)
    if coefficients.shape != (x.shape[1] + 1, 2) or bool((scale <= 0.0).any()):
        raise ModelInputError(
            "linear baseline requires positive scales and two output coefficients"
        )
    design = np.column_stack((np.ones(x.shape[0]), (x - mean) / scale))
    prediction = design @ coefficients
    if not bool(np.isfinite(prediction).all()):
        raise ModelInputError("linear baseline produced non-finite predictions")
    return prediction


def predict_reference_m0(
    features: ArrayLike, parameters: ReferenceM0Parameters
) -> NDArray[np.float64]:
    """Run the recovered M0: Linear(39, 32), exact GELU, Linear(32, 2)."""

    x = _matrix(features, name="features", columns=39)
    mean = np.asarray(parameters.feature_mean)
    scale = np.asarray(parameters.feature_scale)
    input_weights = _matrix(parameters.input_weights, name="M0 input weights", columns=32)
    output_weights = _matrix(parameters.output_weights, name="M0 output weights", columns=2)
    input_bias = np.asarray(parameters.input_bias)
    output_bias = np.asarray(parameters.output_bias)
    if (
        mean.shape != (39,)
        or scale.shape != (39,)
        or input_weights.shape != (39, 32)
        or input_bias.shape != (32,)
        or output_weights.shape != (32, 2)
        or output_bias.shape != (2,)
        or bool((scale <= 0.0).any())
    ):
        raise ModelInputError("M0 parameters do not match the recovered 39-32-2 architecture")
    hidden = ((x - mean) / scale) @ input_weights + input_bias
    cdf = np.fromiter(
        (erf(float(value) / sqrt(2.0)) for value in hidden.flat),
        dtype=np.float64,
        count=hidden.size,
    ).reshape(hidden.shape)
    prediction = (0.5 * hidden * (1.0 + cdf)) @ output_weights + output_bias
    if not bool(np.isfinite(prediction).all()):
        raise ModelInputError("M0 produced non-finite predictions")
    return prediction


def zero_innovation_prediction(row_count: int, target_count: int = 2) -> NDArray[np.float64]:
    """Predict zero innovation for every requested row and target."""

    if (
        isinstance(row_count, bool)
        or isinstance(target_count, bool)
        or not isinstance(row_count, Integral)
        or not isinstance(target_count, Integral)
        or row_count < 1
        or target_count < 1
    ):
        raise ModelInputError("row_count and target_count must be positive integers")
    return np.zeros((int(row_count), int(target_count)), dtype=np.float64)


__all__ = [
    "LinearBaselineParameters",
    "ModelInputError",
    "ReferenceM0Parameters",
    "fit_linear_public_baseline",
    "predict_linear_public_baseline",
    "predict_reference_m0",
    "zero_innovation_prediction",
]
