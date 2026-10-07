"""Prior-whitened proper scores and probability qualification statistics."""

from __future__ import annotations

import math
from collections.abc import Sequence
from numbers import Real
from statistics import NormalDist

from cmj_recovery_dynamics.metrics.scoring import MetricInputError

Matrix = tuple[tuple[float, ...], ...]
Vector = tuple[float, ...]


def _finite(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise MetricInputError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise MetricInputError(f"{name} must be finite")
    return result


def _vector(values: Sequence[object], *, name: str) -> Vector:
    if isinstance(values, (str, bytes)) or not values:
        raise MetricInputError(f"{name} must be a non-empty numeric vector")
    return tuple(_finite(value, name=name) for value in values)


def _matrix(values: Sequence[Sequence[object]], *, name: str) -> Matrix:
    if isinstance(values, (str, bytes)) or not values:
        raise MetricInputError(f"{name} must be a non-empty numeric matrix")
    rows = tuple(_vector(row, name=name) for row in values)
    width = len(rows[0])
    if any(len(row) != width for row in rows) or len(rows) != width:
        raise MetricInputError(f"{name} must be square with one consistent row width")
    return rows


def _observations(
    values: Sequence[Sequence[object]], *, dimension: int, name: str
) -> tuple[Vector, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise MetricInputError(f"{name} must contain at least one vector")
    rows = tuple(_vector(row, name=name) for row in values)
    if any(len(row) != dimension for row in rows):
        raise MetricInputError(f"{name} vectors must all have dimension {dimension}")
    return rows


def _observation_matrix(values: Sequence[Sequence[object]], *, name: str) -> tuple[Vector, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise MetricInputError(f"{name} must contain at least one vector")
    first = _vector(values[0], name=name)
    return _observations(values, dimension=len(first), name=name)


def _distance(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise MetricInputError("distance vectors must have identical dimensions")
    result = 0.0
    for left_value, right_value in zip(left, right, strict=True):
        result = math.hypot(result, left_value - right_value)
    return result


def sample_covariance(observations: Sequence[Sequence[object]]) -> Matrix:
    """Unbiased sample covariance (denominator n−1), matching the qualification estimator."""
    rows = _observation_matrix(observations, name="observations")
    if len(rows) < 2:
        raise MetricInputError("sample covariance requires at least two observations")
    dimension = len(rows[0])
    means = tuple(math.fsum(row[column] for row in rows) / len(rows) for column in range(dimension))
    return tuple(
        tuple(
            math.fsum((row[left] - means[left]) * (row[right] - means[right]) for row in rows)
            / (len(rows) - 1)
            for right in range(dimension)
        )
        for left in range(dimension)
    )


def _cholesky(matrix: Matrix) -> Matrix:
    dimension = len(matrix)
    lower = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    for row in range(dimension):
        for column in range(row + 1):
            residual = matrix[row][column] - math.fsum(
                lower[row][index] * lower[column][index] for index in range(column)
            )
            if row == column:
                if residual <= 0.0:
                    raise MetricInputError("covariance must be positive definite")
                lower[row][column] = math.sqrt(residual)
            else:
                lower[row][column] = residual / lower[column][column]
    return tuple(tuple(row) for row in lower)


def validate_two_target_covariance(
    covariance: Sequence[Sequence[object]], *, condition_limit: float = 1.0e12
) -> Matrix:
    """Validate the force/impulse covariance without jitter or symmetrization."""
    matrix = _matrix(covariance, name="covariance")
    if len(matrix) != 2:
        raise MetricInputError("force/impulse covariance must have shape (2, 2)")
    if matrix[0][1] != matrix[1][0]:
        raise MetricInputError("covariance must be exactly symmetric")
    _cholesky(matrix)
    bound = _finite(condition_limit, name="condition limit")
    if bound <= 1.0:
        raise MetricInputError("condition limit must be greater than one")
    a, b, d = matrix[0][0], matrix[0][1], matrix[1][1]
    determinant = a * d - b * b
    trace = a + d
    discriminant = math.hypot(a - d, 2.0 * b)
    largest_eigenvalue = 0.5 * (trace + discriminant)
    smallest_eigenvalue = determinant / largest_eigenvalue if largest_eigenvalue else 0.0
    condition = largest_eigenvalue / smallest_eigenvalue if smallest_eigenvalue > 0.0 else math.inf
    if not math.isfinite(condition) or condition > bound:
        raise MetricInputError("covariance is ill-conditioned beyond the declared limit")
    return matrix


def _solve_lower(lower: Matrix, vector: Vector) -> Vector:
    if len(lower) != len(vector):
        raise MetricInputError("Cholesky factor and vector dimensions must match")
    result: list[float] = []
    for row in range(len(lower)):
        residual = vector[row] - math.fsum(
            lower[row][column] * result[column] for column in range(row)
        )
        result.append(residual / lower[row][row])
    return tuple(result)


def _solve_upper(upper: Matrix, vector: Vector) -> Vector:
    if len(upper) != len(vector):
        raise MetricInputError("triangular factor and vector dimensions must match")
    result = [0.0 for _ in vector]
    for row in range(len(upper) - 1, -1, -1):
        residual = vector[row] - math.fsum(
            upper[row][column] * result[column] for column in range(row + 1, len(upper))
        )
        result[row] = residual / upper[row][row]
    return tuple(result)


def whitened_vector(
    vector: Sequence[object], *, mean: Sequence[object], covariance: Sequence[Sequence[object]]
) -> Vector:
    """Apply the declared covariance whitening transform L⁻¹(x−μ), Σ=LLᵀ."""
    values = _vector(vector, name="vector")
    center = _vector(mean, name="mean")
    matrix = _matrix(covariance, name="covariance")
    if len(values) != len(center) or len(values) != len(matrix):
        raise MetricInputError("vector, mean, and covariance dimensions must match")
    for row in range(len(matrix)):
        if any(matrix[row][column] != matrix[column][row] for column in range(len(matrix))):
            raise MetricInputError("covariance must be exactly symmetric")
    lower = _cholesky(matrix)
    residual = tuple(value - location for value, location in zip(values, center, strict=True))
    return _solve_lower(lower, residual)


def mahalanobis_squared(
    residual: Sequence[object], covariance: Sequence[Sequence[object]]
) -> float:
    """Return rᵀΣ⁻¹r through Cholesky whitening, without forming an inverse."""
    vector = _vector(residual, name="residual")
    matrix = _matrix(covariance, name="covariance")
    if len(vector) != len(matrix):
        raise MetricInputError("residual and covariance dimensions must match")
    for row in range(len(matrix)):
        if any(matrix[row][column] != matrix[column][row] for column in range(len(matrix))):
            raise MetricInputError("covariance must be exactly symmetric")
    whitened = _solve_lower(_cholesky(matrix), vector)
    result = math.fsum(value * value for value in whitened)
    if not math.isfinite(result):
        raise MetricInputError("Mahalanobis squared residual overflowed")
    return result


def student_t_scale_from_covariance(
    covariance: Sequence[Sequence[object]], degrees_of_freedom: object
) -> Matrix:
    """Convert a multivariate Student-t covariance Ω to scale Ω(ν−2)/ν."""
    matrix = _matrix(covariance, name="covariance")
    if any(
        matrix[row][column] != matrix[column][row]
        for row in range(len(matrix))
        for column in range(len(matrix))
    ):
        raise MetricInputError("covariance must be exactly symmetric")
    _cholesky(matrix)
    nu = _finite(degrees_of_freedom, name="degrees of freedom")
    if nu <= 2.0:
        raise MetricInputError("Student-t covariance exists only for degrees of freedom > 2")
    factor = (nu - 2.0) / nu
    scaled = tuple(tuple(value * factor for value in row) for row in matrix)
    return _matrix(scaled, name="Student-t scale")


def student_t_covariance_from_scale(
    scale: Sequence[Sequence[object]], degrees_of_freedom: object
) -> Matrix:
    """Convert a multivariate Student-t scale matrix to covariance Ω=Σν/(ν−2)."""
    matrix = _matrix(scale, name="Student-t scale")
    if any(
        matrix[row][column] != matrix[column][row]
        for row in range(len(matrix))
        for column in range(len(matrix))
    ):
        raise MetricInputError("Student-t scale must be exactly symmetric")
    _cholesky(matrix)
    nu = _finite(degrees_of_freedom, name="degrees of freedom")
    if nu <= 2.0:
        raise MetricInputError("Student-t covariance exists only for degrees of freedom > 2")
    factor = nu / (nu - 2.0)
    covariance = tuple(tuple(value * factor for value in row) for row in matrix)
    return _matrix(covariance, name="Student-t covariance")


def empirical_energy_score(
    samples: Sequence[Sequence[object]],
    observation: Sequence[object],
    *,
    standardization_scales: Sequence[object],
) -> float:
    """Equal-weight empirical-distribution V-statistic; pairwise sum includes zero diagonal."""
    target = _vector(observation, name="energy-score observation")
    scales = _vector(standardization_scales, name="standardization scales")
    if len(scales) != len(target) or any(scale <= 0.0 for scale in scales):
        raise MetricInputError("energy score requires one positive scale per target")
    values = _observations(samples, dimension=len(target), name="ensemble samples")
    standardized = tuple(
        tuple(value / scale for value, scale in zip(row, scales, strict=True)) for row in values
    )
    standardized_target = tuple(value / scale for value, scale in zip(target, scales, strict=True))
    first_term = math.fsum(_distance(row, standardized_target) for row in standardized) / len(
        standardized
    )
    pairwise_sum = math.fsum(
        _distance(standardized[left], standardized[right])
        for left in range(len(standardized))
        for right in range(len(standardized))
    )
    result = first_term - pairwise_sum / (2.0 * len(standardized) ** 2)
    if not math.isfinite(result):
        raise MetricInputError("energy score must be finite")
    return result


def prior_whitened_energy_score(
    samples: Sequence[Sequence[object]],
    observation: Sequence[object],
    *,
    prior_mean: Sequence[object],
    prior_covariance: Sequence[Sequence[object]],
) -> float:
    """Unbiased finite-ensemble energy score after prior-covariance whitening."""
    target = whitened_vector(observation, mean=prior_mean, covariance=prior_covariance)
    values = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance) for sample in samples
    )
    if not values:
        raise MetricInputError("energy score requires at least one ensemble member")
    first_term = math.fsum(_distance(sample, target) for sample in values) / len(values)
    if len(values) < 2:
        return first_term
    unordered_pair_sum = math.fsum(
        _distance(values[left], values[right])
        for left in range(len(values))
        for right in range(left + 1, len(values))
    )
    # The U-statistic omits self-pairs and divides the unordered sum by n(n-1).
    result = first_term - unordered_pair_sum / (len(values) * (len(values) - 1))
    if not math.isfinite(result):
        raise MetricInputError("prior-whitened energy score must be finite")
    return result


def prior_whitened_energy_score_regret(
    forecast_samples: Sequence[Sequence[object]],
    reference_samples: Sequence[Sequence[object]],
    *,
    prior_mean: Sequence[object],
    prior_covariance: Sequence[Sequence[object]],
) -> float:
    """Cross-sample energy-score regret: cross distance minus half each pair distance."""
    forecast = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance)
        for sample in forecast_samples
    )
    reference = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance)
        for sample in reference_samples
    )
    if len(forecast) < 2 or len(reference) < 2:
        raise MetricInputError("energy-score regret needs at least two samples per distribution")
    if len(forecast[0]) != len(reference[0]):
        raise MetricInputError("forecast and reference sample dimensions must match")
    cross = math.fsum(_distance(left, right) for left in forecast for right in reference) / (
        len(forecast) * len(reference)
    )
    forecast_pairs = math.fsum(
        _distance(forecast[left], forecast[right])
        for left in range(len(forecast))
        for right in range(left + 1, len(forecast))
    ) / (len(forecast) * (len(forecast) - 1) / 2.0)
    reference_pairs = math.fsum(
        _distance(reference[left], reference[right])
        for left in range(len(reference))
        for right in range(left + 1, len(reference))
    ) / (len(reference) * (len(reference) - 1) / 2.0)
    return _finite(cross - 0.5 * forecast_pairs - 0.5 * reference_pairs, name="energy-score regret")


def mean_prior_whitened_energy_score(
    samples_by_case: Sequence[Sequence[Sequence[object]]],
    observations: Sequence[Sequence[object]],
    *,
    prior_means: Sequence[Sequence[object]],
    prior_covariances: Sequence[Sequence[Sequence[object]]],
) -> float:
    """Equal-case mean of paired prior-whitened ensemble energy scores."""
    count = len(observations)
    if (
        count == 0
        or len(samples_by_case) != count
        or len(prior_means) != count
        or len(prior_covariances) != count
    ):
        raise MetricInputError("energy-score case collections must have the same non-zero length")
    scores = tuple(
        prior_whitened_energy_score(
            samples_by_case[index],
            observations[index],
            prior_mean=prior_means[index],
            prior_covariance=prior_covariances[index],
        )
        for index in range(count)
    )
    return _finite(math.fsum(scores) / count, name="mean prior-whitened energy score")


def variogram_score(
    samples: Sequence[Sequence[object]], observation: Sequence[object], *, order: float = 0.5
) -> float:
    """Equal-pair variogram diagnostic using the ensemble mean of |xᵢ−xⱼ|ᵖ."""
    target = _vector(observation, name="variogram observation")
    values = _observations(samples, dimension=len(target), name="variogram samples")
    exponent = _finite(order, name="variogram order")
    if exponent <= 0.0 or len(target) < 2:
        raise MetricInputError("variogram score needs order > 0 and at least two dimensions")
    terms: list[float] = []
    for left in range(len(target)):
        for right in range(left + 1, len(target)):
            forecast = math.fsum(
                abs(sample[left] - sample[right]) ** exponent for sample in values
            ) / len(values)
            observed = abs(target[left] - target[right]) ** exponent
            terms.append((forecast - observed) ** 2)
    result = math.fsum(terms) / len(terms)
    if not math.isfinite(result):
        raise MetricInputError("variogram score must be finite")
    return result


def prior_whitened_variogram_score(
    samples: Sequence[Sequence[object]],
    observation: Sequence[object],
    *,
    prior_mean: Sequence[object],
    prior_covariance: Sequence[Sequence[object]],
    order: float = 0.5,
) -> float:
    """Apply the separate variogram diagnostic in the declared prior-whitened space."""
    whitened_samples = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance) for sample in samples
    )
    whitened_observation = whitened_vector(
        observation, mean=prior_mean, covariance=prior_covariance
    )
    return variogram_score(whitened_samples, whitened_observation, order=order)


def prior_whitened_variogram_score_regret(
    forecast_samples: Sequence[Sequence[object]],
    reference_samples: Sequence[Sequence[object]],
    *,
    prior_mean: Sequence[object],
    prior_covariance: Sequence[Sequence[object]],
    order: float = 0.5,
) -> float:
    """Equal-pair squared difference of forecast and reference variogram moments."""
    forecast = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance)
        for sample in forecast_samples
    )
    reference = tuple(
        whitened_vector(sample, mean=prior_mean, covariance=prior_covariance)
        for sample in reference_samples
    )
    if not forecast or not reference or len(forecast[0]) != len(reference[0]):
        raise MetricInputError("variogram regret needs matching non-empty distributions")
    exponent = _finite(order, name="variogram order")
    if exponent <= 0.0 or len(forecast[0]) < 2:
        raise MetricInputError("variogram regret needs order > 0 and at least two dimensions")
    terms: list[float] = []
    for left in range(len(forecast[0])):
        for right in range(left + 1, len(forecast[0])):
            forecast_moment = math.fsum(
                abs(row[left] - row[right]) ** exponent for row in forecast
            ) / len(forecast)
            reference_moment = math.fsum(
                abs(row[left] - row[right]) ** exponent for row in reference
            ) / len(reference)
            terms.append((forecast_moment - reference_moment) ** 2)
    return _finite(math.fsum(terms) / len(terms), name="variogram score regret")


def mean_prior_whitened_variogram_score(
    samples_by_case: Sequence[Sequence[Sequence[object]]],
    observations: Sequence[Sequence[object]],
    *,
    prior_means: Sequence[Sequence[object]],
    prior_covariances: Sequence[Sequence[Sequence[object]]],
    order: float = 0.5,
) -> float:
    """Equal-case mean of prior-whitened variogram scores."""
    count = len(observations)
    if (
        count == 0
        or len(samples_by_case) != count
        or len(prior_means) != count
        or len(prior_covariances) != count
    ):
        raise MetricInputError("variogram case collections must have the same non-zero length")
    scores = tuple(
        prior_whitened_variogram_score(
            samples_by_case[index],
            observations[index],
            prior_mean=prior_means[index],
            prior_covariance=prior_covariances[index],
            order=order,
        )
        for index in range(count)
    )
    return _finite(math.fsum(scores) / count, name="mean prior-whitened variogram score")


def mean_standardized_euclidean_error(
    predictions: Sequence[Sequence[object]],
    observations: Sequence[Sequence[object]],
    *,
    scales: Sequence[object],
) -> float:
    """Mean rowwise Euclidean norm of residuals divided by explicit axis scales."""
    scale_values = _vector(scales, name="standardization scales")
    if any(value <= 0.0 for value in scale_values):
        raise MetricInputError("standardization scales must be positive")
    predicted = _observations(predictions, dimension=len(scale_values), name="predictions")
    actual = _observations(observations, dimension=len(scale_values), name="observations")
    if len(predicted) != len(actual):
        raise MetricInputError("prediction and observation row counts must match")
    errors = (
        _distance(
            tuple(p / s for p, s in zip(prediction, scale_values, strict=True)),
            tuple(y / s for y, s in zip(observation, scale_values, strict=True)),
        )
        for prediction, observation in zip(predicted, actual, strict=True)
    )
    return _finite(math.fsum(errors) / len(predicted), name="mean standardized Euclidean error")


def parameter_root_mean_square_error(
    estimates: Sequence[Sequence[object]], truths: Sequence[Sequence[object]]
) -> float:
    """Root mean square across all estimate × parameter coordinates."""
    predicted = _observation_matrix(estimates, name="parameter estimates")
    actual = _observations(truths, dimension=len(predicted[0]), name="parameter truths")
    if len(predicted) != len(actual):
        raise MetricInputError("parameter estimate and truth row counts must match")
    squared_errors = [
        (estimate - truth) ** 2
        for predicted_row, truth_row in zip(predicted, actual, strict=True)
        for estimate, truth in zip(predicted_row, truth_row, strict=True)
    ]
    result = math.sqrt(math.fsum(squared_errors) / len(squared_errors))
    if not math.isfinite(result):
        raise MetricInputError("parameter RMSE must be finite")
    return result


def gaussian_kl_divergence(
    mean: Sequence[object],
    covariance: Sequence[Sequence[object]],
    *,
    reference_mean: Sequence[object],
    reference_covariance: Sequence[Sequence[object]],
) -> float:
    """KL[N(mean,covariance) || N(reference_mean,reference_covariance)] in nats."""
    location = _vector(mean, name="posterior mean")
    reference_location = _vector(reference_mean, name="reference mean")
    posterior = _matrix(covariance, name="posterior covariance")
    reference = _matrix(reference_covariance, name="reference covariance")
    dimension = len(location)
    if (
        len(reference_location) != dimension
        or len(posterior) != dimension
        or len(reference) != dimension
    ):
        raise MetricInputError("Gaussian KL inputs must have identical dimensions")
    if any(posterior[i][j] != posterior[j][i] for i in range(dimension) for j in range(dimension)):
        raise MetricInputError("posterior covariance must be exactly symmetric")
    if any(reference[i][j] != reference[j][i] for i in range(dimension) for j in range(dimension)):
        raise MetricInputError("reference covariance must be exactly symmetric")
    posterior_factor = _cholesky(posterior)
    reference_factor = _cholesky(reference)
    whitened_delta = _solve_lower(
        reference_factor,
        tuple(left - right for left, right in zip(reference_location, location, strict=True)),
    )
    quadratic = math.fsum(value * value for value in whitened_delta)
    trace_terms: list[float] = []
    for column in range(dimension):
        column_vector = tuple(posterior[row][column] for row in range(dimension))
        whitened_column = _solve_lower(reference_factor, column_vector)
        reference_upper = tuple(
            tuple(reference_factor[column][row] for column in range(dimension))
            for row in range(dimension)
        )
        solved_column = _solve_upper(reference_upper, whitened_column)
        trace_terms.append(solved_column[column])
    logdet_posterior = 2.0 * math.fsum(
        math.log(posterior_factor[index][index]) for index in range(dimension)
    )
    logdet_reference = 2.0 * math.fsum(
        math.log(reference_factor[index][index]) for index in range(dimension)
    )
    result = 0.5 * (
        math.fsum(trace_terms) + quadratic - dimension + logdet_reference - logdet_posterior
    )
    if not math.isfinite(result) or result < -1e-10:
        raise MetricInputError("Gaussian KL divergence is invalid")
    return max(0.0, result)


def posterior_trace_ratio(
    covariances: Sequence[Sequence[Sequence[object]]], prior_covariance: Sequence[Sequence[object]]
) -> float:
    """Mean posterior covariance trace divided by the prior covariance trace."""
    prior = _matrix(prior_covariance, name="prior covariance")
    if any(prior[i][j] != prior[j][i] for i in range(len(prior)) for j in range(len(prior))):
        raise MetricInputError("prior covariance must be exactly symmetric")
    _cholesky(prior)
    prior_trace = math.fsum(prior[index][index] for index in range(len(prior)))
    if prior_trace <= 0.0:
        raise MetricInputError("prior covariance trace must be positive")
    values = tuple(_matrix(covariance, name="posterior covariance") for covariance in covariances)
    if not values:
        raise MetricInputError("at least one posterior covariance is required")
    if any(len(matrix) != len(prior) for matrix in values):
        raise MetricInputError("posterior covariance dimensions must match the prior")
    for matrix in values:
        if any(
            matrix[i][j] != matrix[j][i] for i in range(len(matrix)) for j in range(len(matrix))
        ):
            raise MetricInputError("posterior covariance must be exactly symmetric")
        _cholesky(matrix)
    trace_mean = math.fsum(
        math.fsum(matrix[index][index] for index in range(len(prior))) for matrix in values
    ) / len(values)
    result = trace_mean / prior_trace
    if not math.isfinite(result):
        raise MetricInputError("posterior trace ratio must be finite")
    return result


def marginal_interval_coverage(
    observations: Sequence[Sequence[object]],
    lower: Sequence[object],
    upper: Sequence[object],
) -> tuple[float, ...]:
    """Empirical marginal coverage per target; joint coverage is not implied."""
    lows = _vector(lower, name="interval lower bounds")
    highs = _vector(upper, name="interval upper bounds")
    if len(lows) != len(highs) or any(low > high for low, high in zip(lows, highs, strict=True)):
        raise MetricInputError("interval bounds must match and satisfy lower <= upper")
    values = _observations(observations, dimension=len(lows), name="coverage observations")
    return tuple(
        sum(low <= row[index] <= high for row in values) / len(values)
        for index, (low, high) in enumerate(zip(lows, highs, strict=True))
    )


def normal_standardized_residual_diagnostics(
    residuals: Sequence[object], *, confidence: float = 0.90
) -> tuple[float, float]:
    """Return mean |z| and central normal interval coverage for standardized residuals."""
    values = _vector(residuals, name="standardized residuals")
    level = _finite(confidence, name="nominal confidence")
    if not 0.0 < level < 1.0:
        raise MetricInputError("nominal confidence must lie inside (0, 1)")
    cutoff = NormalDist().inv_cdf(0.5 + level / 2.0)
    mean_absolute = math.fsum(abs(value) for value in values) / len(values)
    coverage = sum(abs(value) <= cutoff for value in values) / len(values)
    return mean_absolute, coverage


def joint_ellipsoid_coverage(
    observations: Sequence[Sequence[object]],
    means: Sequence[Sequence[object]],
    covariances: Sequence[Sequence[Sequence[object]]],
    *,
    squared_radius: float,
) -> float:
    """Coverage of supplied Mahalanobis ellipsoids; caller supplies χ² cutoff."""
    targets = _observation_matrix(observations, name="coverage observations")
    centers = _observations(means, dimension=len(targets[0]), name="predictive means")
    matrices = tuple(_matrix(matrix, name="predictive covariance") for matrix in covariances)
    if len(centers) != len(targets) or len(matrices) != len(targets):
        raise MetricInputError("joint coverage needs one mean and covariance per observation")
    radius = _finite(squared_radius, name="squared ellipsoid radius")
    if radius < 0.0:
        raise MetricInputError("squared ellipsoid radius must be non-negative")
    covered = 0
    for target, center, covariance in zip(targets, centers, matrices, strict=True):
        if len(covariance) != len(target):
            raise MetricInputError("predictive covariance has the wrong dimension")
        residual = tuple(left - right for left, right in zip(target, center, strict=True))
        covered += mahalanobis_squared(residual, covariance) <= radius
    return covered / len(targets)


def binary_auc(labels: Sequence[object], scores: Sequence[object]) -> float:
    """Tie-corrected ROC AUC as the positive-negative Mann–Whitney probability."""
    if len(labels) != len(scores) or not labels:
        raise MetricInputError("AUC labels and scores need the same non-empty length")
    pairs = tuple(
        (label, _finite(score, name="classifier score"))
        for label, score in zip(labels, scores, strict=True)
    )
    if any(label not in (0, 1, False, True) for label, _score in pairs):
        raise MetricInputError("AUC labels must be binary 0/1 values")
    positives = sum(bool(label) for label, _score in pairs)
    negatives = len(pairs) - positives
    if positives == 0 or negatives == 0:
        raise MetricInputError("AUC requires both positive and negative labels")
    ordered = sorted(pairs, key=lambda pair: pair[1])
    positive_rank_sum = 0.0
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0
        positive_rank_sum += average_rank * sum(bool(label) for label, _score in ordered[start:end])
        start = end
    result = (positive_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)
    if not math.isfinite(result):
        raise MetricInputError("AUC must be finite")
    return result


def mean_fold_auc(fold_aucs: Sequence[float]) -> float:
    """Equal-fold mean used by the two-sample posterior diagnostic."""
    values = _vector(fold_aucs, name="fold AUC values")
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise MetricInputError("AUC values must be in [0, 1]")
    return _finite(math.fsum(values) / len(values), name="mean fold AUC")


def paired_score_difference(
    first_scores: Sequence[object], second_scores: Sequence[object]
) -> float:
    """Mean paired first-minus-second score difference; no row broadcasting."""
    first = _vector(first_scores, name="first score vector")
    second = _vector(second_scores, name="second score vector")
    if len(first) != len(second):
        raise MetricInputError("paired score vectors must have identical lengths")
    differences = tuple(left - right for left, right in zip(first, second, strict=True))
    return _finite(math.fsum(differences) / len(differences), name="paired score difference")


__all__ = [
    "Matrix",
    "Vector",
    "binary_auc",
    "empirical_energy_score",
    "gaussian_kl_divergence",
    "joint_ellipsoid_coverage",
    "mahalanobis_squared",
    "mean_fold_auc",
    "mean_prior_whitened_energy_score",
    "prior_whitened_energy_score_regret",
    "mean_prior_whitened_variogram_score",
    "mean_standardized_euclidean_error",
    "marginal_interval_coverage",
    "normal_standardized_residual_diagnostics",
    "parameter_root_mean_square_error",
    "paired_score_difference",
    "posterior_trace_ratio",
    "prior_whitened_energy_score",
    "prior_whitened_variogram_score",
    "prior_whitened_variogram_score_regret",
    "sample_covariance",
    "student_t_covariance_from_scale",
    "student_t_scale_from_covariance",
    "variogram_score",
    "validate_two_target_covariance",
    "whitened_vector",
]
