"""Clean implementations of the recovered point-score and research equations."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real

from cmj_recovery_dynamics.contracts import ForecastHorizon, OutcomeVariable, TargetCell


class MetricInputError(ValueError):
    """An evaluation input violates its declared numeric or cell contract."""


@dataclass(frozen=True, slots=True)
class CellValues:
    cell: TargetCell
    predictions: tuple[float, ...]
    observations: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class CellMetric:
    cell: TargetCell
    root_mean_square_error: float
    observation_standard_deviation: float
    normalized_error: float
    row_count: int
    normalized: bool


@dataclass(frozen=True, slots=True)
class TargetMetricValue:
    name: str
    value: float
    floor: float
    perfect: float
    weight: float = 1.0
    lower_is_better: bool = True


@dataclass(frozen=True, slots=True)
class BenchmarkScoreResult:
    score: float
    aggregate_progress: float
    target_progress: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class RichHistoryAssessment:
    time_from_origin_hours: float | None
    validity_state: str
    trial_count: float | None


THRESHOLD_LOAD_SUPPORTS: tuple[tuple[str, float, float], ...] = (
    ("duration_min", 45.0, 120.0),
    ("total_distance_m", 3000.0, 13000.0),
    ("high_speed_distance_m", 0.0, 2000.0),
    ("sprint_distance_m", 0.0, 600.0),
    ("high_intensity_accel_count", 0.0, 150.0),
    ("high_intensity_decel_count", 0.0, 150.0),
    ("session_rpe_cr10", 2.0, 10.0),
)

THRESHOLD_LOAD_HIGH_CUTOFF = 0.5
PROGRESS_RATIO_DENOMINATOR_TOLERANCE = 1e-12
RICH_HISTORY_CLEAN_MIN_VALID_ASSESSMENTS = 6
RICH_HISTORY_CLEAN_MIN_TRIALS = 2
RICH_HISTORY_CELL_MIN_ROWS = 2

_POST_EXPOSURE_HORIZONS = (
    ForecastHorizon.H24,
    ForecastHorizon.H48,
    ForecastHorizon.H72,
)
_RICH_HISTORY_HORIZONS = (ForecastHorizon.H72, ForecastHorizon.D7)
_RICH_HISTORY_STRATA = tuple(
    f"{load_count}|{quality}"
    for load_count in ("L0", "L1", "L2")
    for quality in ("clean", "degraded")
)

INITIAL_CAMP_CELLS = tuple(
    TargetCell(outcome, horizon)
    for horizon in _RICH_HISTORY_HORIZONS
    for outcome in OutcomeVariable
)
RICH_HISTORY_CELLS = tuple(
    TargetCell(outcome, horizon, stratum)
    for outcome in OutcomeVariable
    for horizon in _RICH_HISTORY_HORIZONS
    for stratum in _RICH_HISTORY_STRATA
)
THRESHOLD_RESPONSE_CELLS = tuple(
    TargetCell(outcome, horizon, regime)
    for horizon in _POST_EXPOSURE_HORIZONS
    for regime in ("high", "low")
    for outcome in OutcomeVariable
)
POST_EXPOSURE_RESEARCH_CELLS = tuple(
    TargetCell(outcome, horizon)
    for horizon in _POST_EXPOSURE_HORIZONS
    for outcome in OutcomeVariable
)


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise MetricInputError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise MetricInputError(f"{name} must be finite")
    return result


def _vector(values: Sequence[object], *, name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise MetricInputError(f"{name} must be a non-empty numeric vector")
    return tuple(_number(value, name=name) for value in values)


def _rmse(predictions: tuple[float, ...], observations: tuple[float, ...]) -> float:
    if len(predictions) != len(observations):
        raise MetricInputError("prediction and observation shapes must match exactly")
    if not predictions:
        raise MetricInputError("prediction and observation vectors must not be empty")
    scale = max(
        max((abs(value) for value in predictions), default=0.0),
        max((abs(value) for value in observations), default=0.0),
    )
    if scale == 0.0:
        return 0.0
    normalized_errors = tuple(
        prediction / scale - observation / scale
        for prediction, observation in zip(predictions, observations, strict=True)
    )
    ratio = math.sqrt(math.fsum(error * error for error in normalized_errors) / len(predictions))
    result = scale * ratio
    if not math.isfinite(result):
        raise MetricInputError("root-mean-square error overflowed its finite range")
    return result


def _population_standard_deviation(values: tuple[float, ...]) -> float:
    scale = max((abs(value) for value in values), default=0.0)
    if scale == 0.0:
        return 0.0
    scaled = tuple(value / scale for value in values)
    mean = math.fsum(scaled) / len(scaled)
    variance = math.fsum((value - mean) ** 2 for value in scaled) / len(scaled)
    return scale * math.sqrt(max(variance, 0.0))


def sample_standard_deviation(values: Sequence[object]) -> float:
    """Sample SD with ddof=1, used for the public reference-selection scale."""
    vector = _vector(values, name="training observations")
    if len(vector) < 2:
        raise MetricInputError("sample standard deviation requires at least two observations")
    scale = max(abs(value) for value in vector)
    if scale == 0.0:
        return 0.0
    normalized = tuple(value / scale for value in vector)
    mean = math.fsum(normalized) / len(normalized)
    variance = math.fsum((value - mean) ** 2 for value in normalized) / (len(normalized) - 1)
    return scale * math.sqrt(max(variance, 0.0))


def training_axis_scales(
    training_targets: Sequence[Sequence[object]], *, minimum_scale: float
) -> tuple[float, ...]:
    """Compute ddof=1 target-axis scales with an explicit positive floor."""
    if not training_targets:
        raise MetricInputError("training targets must contain at least one row")
    first = _vector(training_targets[0], name="training targets")
    rows = tuple(_vector(row, name="training targets") for row in training_targets)
    if any(len(row) != len(first) for row in rows):
        raise MetricInputError("training target row dimensions must match")
    floor = _number(minimum_scale, name="minimum training scale")
    if floor <= 0.0:
        raise MetricInputError("minimum training scale must be positive")
    scales = tuple(
        max(sample_standard_deviation(tuple(row[column] for row in rows)), floor)
        for column in range(len(first))
    )
    return scales


def population_normalized_rmse(
    predictions: Sequence[object], observations: Sequence[object]
) -> float:
    """RMSE / population SD (ddof=0); when SD is zero, return native-unit RMSE."""
    predicted = _vector(predictions, name="predictions")
    observed = _vector(observations, name="observations")
    rmse = _rmse(predicted, observed)
    standard_deviation = _population_standard_deviation(observed)
    return rmse if standard_deviation == 0.0 else rmse / standard_deviation


def _validate_expected_cells(expected_cells: Sequence[TargetCell]) -> tuple[TargetCell, ...]:
    expected = tuple(expected_cells)
    if not expected or len(set(expected)) != len(expected):
        raise MetricInputError("expected scoring cells must be non-empty and unique")
    return expected


def cellwise_normalized_rmse(
    values: Sequence[CellValues],
    expected_cells: Sequence[TargetCell],
    *,
    minimum_rows_per_cell: int = 1,
    require_nonzero_standard_deviation: bool = False,
) -> tuple[CellMetric, ...]:
    """Score exact cells independently; no implicit row, shape, or cell broadcasting."""
    expected = _validate_expected_cells(expected_cells)
    if minimum_rows_per_cell < 1:
        raise MetricInputError("minimum_rows_per_cell must be positive")
    by_cell: dict[TargetCell, CellValues] = {}
    for item in values:
        if item.cell in by_cell:
            raise MetricInputError(f"duplicate scoring cell: {item.cell.name}")
        by_cell[item.cell] = item
    if set(by_cell) != set(expected):
        missing = sorted(cell.name for cell in set(expected) - set(by_cell))
        unexpected = sorted(cell.name for cell in set(by_cell) - set(expected))
        raise MetricInputError(f"scoring-cell mismatch; missing={missing}, unexpected={unexpected}")

    results: list[CellMetric] = []
    for cell in expected:
        item = by_cell[cell]
        predictions = _vector(item.predictions, name=f"{cell.name} predictions")
        observations = _vector(item.observations, name=f"{cell.name} observations")
        if len(predictions) != len(observations):
            raise MetricInputError(f"prediction and observation shapes differ for {cell.name}")
        if len(predictions) < minimum_rows_per_cell:
            raise MetricInputError(f"{cell.name} requires at least {minimum_rows_per_cell} rows")
        rmse = _rmse(predictions, observations)
        standard_deviation = _population_standard_deviation(observations)
        if standard_deviation == 0.0:
            if require_nonzero_standard_deviation:
                raise MetricInputError(f"{cell.name} has zero truth standard deviation")
            normalized = rmse
            is_normalized = False
        else:
            normalized = rmse / standard_deviation
            is_normalized = True
        results.append(
            CellMetric(
                cell=cell,
                root_mean_square_error=rmse,
                observation_standard_deviation=standard_deviation,
                normalized_error=normalized,
                row_count=len(predictions),
                normalized=is_normalized,
            )
        )
    return tuple(results)


def target_metrics_from_cells(
    metrics: Sequence[CellMetric],
    expected_cells: Sequence[TargetCell],
    *,
    floor: float,
    perfect: float,
    weight: float = 1.0,
) -> tuple[TargetMetricValue, ...]:
    """Bind one benchmark target metric to each complete scoring cell."""
    expected = _validate_expected_cells(expected_cells)
    by_cell: dict[TargetCell, CellMetric] = {}
    for metric in metrics:
        if metric.cell in by_cell:
            raise MetricInputError(f"duplicate cell metric: {metric.cell.name}")
        by_cell[metric.cell] = metric
    if set(by_cell) != set(expected):
        raise MetricInputError("target metric binding requires the exact registered cell set")
    raw_floor = _number(floor, name="metric floor")
    raw_perfect = _number(perfect, name="perfect metric value")
    raw_weight = _number(weight, name="target metric weight")
    if raw_weight <= 0.0:
        raise MetricInputError("target metric weight must be positive")
    return tuple(
        TargetMetricValue(
            name=cell.name,
            value=_number(by_cell[cell].normalized_error, name=f"metric {cell.name}"),
            floor=raw_floor,
            perfect=raw_perfect,
            weight=raw_weight,
        )
        for cell in expected
    )


def rich_history_target_metrics(metrics: Sequence[CellMetric]) -> tuple[TargetMetricValue, ...]:
    """Average 12 history strata per outcome before target progress is clipped."""
    by_cell: dict[TargetCell, CellMetric] = {}
    for metric in metrics:
        if metric.cell in by_cell:
            raise MetricInputError(f"duplicate cell metric: {metric.cell.name}")
        by_cell[metric.cell] = metric
    if set(by_cell) != set(RICH_HISTORY_CELLS):
        raise MetricInputError("rich-history scorer requires all 24 registered cells")
    targets: list[TargetMetricValue] = []
    for outcome in OutcomeVariable:
        cells = tuple(cell for cell in RICH_HISTORY_CELLS if cell.outcome is outcome)
        value = math.fsum(by_cell[cell].normalized_error for cell in cells) / len(cells)
        targets.append(
            TargetMetricValue(
                name=outcome.value,
                value=value,
                floor=1.0,
                perfect=0.0,
                weight=1.0,
            )
        )
    return tuple(targets)


def weighted_cell_mean(
    metrics: Sequence[CellMetric], weights: Sequence[tuple[TargetCell, float]]
) -> float:
    """Return an explicit normalized weighted mean over an exact cell set."""
    by_cell: dict[TargetCell, CellMetric] = {}
    for metric in metrics:
        if metric.cell in by_cell:
            raise MetricInputError(f"duplicate cell metric: {metric.cell.name}")
        by_cell[metric.cell] = metric
    weight_by_cell: dict[TargetCell, float] = {}
    for cell, raw_weight in weights:
        if cell in weight_by_cell:
            raise MetricInputError(f"duplicate weight for cell: {cell.name}")
        weight = _number(raw_weight, name=f"weight for {cell.name}")
        if weight <= 0.0:
            raise MetricInputError("cell weights must be positive")
        weight_by_cell[cell] = weight
    if set(by_cell) != set(weight_by_cell):
        raise MetricInputError("cell metric and cell-weight sets must match exactly")
    total_weight = math.fsum(weight_by_cell.values())
    result = (
        math.fsum(
            _number(by_cell[cell].normalized_error, name=f"metric {cell.name}")
            * weight_by_cell[cell]
            for cell in weight_by_cell
        )
        / total_weight
    )
    if not math.isfinite(result):
        raise MetricInputError("weighted cell mean must be finite")
    return result


def _target_progress(metric: TargetMetricValue) -> float:
    value = _number(metric.value, name=f"metric {metric.name}")
    floor = _number(metric.floor, name=f"floor for {metric.name}")
    perfect = _number(metric.perfect, name=f"perfect value for {metric.name}")
    weight = _number(metric.weight, name=f"weight for {metric.name}")
    if weight <= 0.0:
        raise MetricInputError("target weights must be positive")
    if metric.lower_is_better:
        if floor <= perfect:
            raise MetricInputError("lower-is-better metric requires floor > perfect")
        progress = (floor - value) / (floor - perfect)
    else:
        if floor >= perfect:
            raise MetricInputError("higher-is-better metric requires floor < perfect")
        progress = (value - floor) / (perfect - floor)
    return min(1.0, max(0.0, progress))


def piecewise_linear_calibration(progress: float, reference_progress: float) -> float:
    """Map progress through (0,0), (reference,0.5), (1,1), clamped to [0,1]."""
    x = _number(progress, name="aggregate progress")
    reference = _number(reference_progress, name="calibration reference progress")
    if not 0.0 < reference < 1.0:
        raise MetricInputError("calibration reference progress must be inside (0, 1)")
    x = min(1.0, max(0.0, x))
    if x <= reference:
        return 0.5 * x / reference
    return 0.5 + 0.5 * (x - reference) / (1.0 - reference)


def calibrated_benchmark_score(
    target_metrics: Sequence[TargetMetricValue], *, reference_progress: float
) -> BenchmarkScoreResult:
    """Aggregate target progress and apply the task-locked piecewise-linear curve."""
    metrics = tuple(target_metrics)
    if not metrics:
        raise MetricInputError("at least one target metric is required")
    if len({metric.name for metric in metrics}) != len(metrics):
        raise MetricInputError("target metric names must be unique")
    progress = tuple((metric.name, _target_progress(metric)) for metric in metrics)
    weights = tuple(_number(metric.weight, name=f"weight for {metric.name}") for metric in metrics)
    weight_sum = math.fsum(weights)
    aggregate = (
        math.fsum(value * weight for (_, value), weight in zip(progress, weights, strict=True))
        / weight_sum
    )
    return BenchmarkScoreResult(
        score=piecewise_linear_calibration(aggregate, reference_progress),
        aggregate_progress=aggregate,
        target_progress=progress,
    )


def point_benchmark_score(
    values: Sequence[CellValues],
    expected_cells: Sequence[TargetCell],
    *,
    normalization_floor: float,
    reference_progress: float,
    minimum_rows_per_cell: int = 1,
) -> BenchmarkScoreResult:
    """Reusable equal-cell point score for the two camp and threshold contracts."""
    cells = _validate_expected_cells(expected_cells)
    metrics = cellwise_normalized_rmse(values, cells, minimum_rows_per_cell=minimum_rows_per_cell)
    targets = target_metrics_from_cells(metrics, cells, floor=normalization_floor, perfect=0.0)
    return calibrated_benchmark_score(targets, reference_progress=reference_progress)


def rich_history_benchmark_score(
    values: Sequence[CellValues], *, reference_progress: float
) -> BenchmarkScoreResult:
    """Implement the 24-cell score with per-outcome aggregation before clipping."""
    metrics = cellwise_normalized_rmse(
        values,
        RICH_HISTORY_CELLS,
        minimum_rows_per_cell=RICH_HISTORY_CELL_MIN_ROWS,
    )
    targets = rich_history_target_metrics(metrics)
    return calibrated_benchmark_score(targets, reference_progress=reference_progress)


def rich_history_raw_progress(values: Sequence[CellValues]) -> float:
    """Return 24-cell raw progress before the unavailable final score calibration."""
    metrics = cellwise_normalized_rmse(
        values,
        RICH_HISTORY_CELLS,
        minimum_rows_per_cell=RICH_HISTORY_CELL_MIN_ROWS,
    )
    targets = rich_history_target_metrics(metrics)
    return math.fsum(_target_progress(target) for target in targets) / len(targets)


def mean_cellwise_normalized_rmse(
    values: Sequence[CellValues], expected_cells: Sequence[TargetCell]
) -> float:
    """Equal-weight mean of six cellwise normalized errors for post-exposure research."""
    if tuple(expected_cells) != POST_EXPOSURE_RESEARCH_CELLS:
        raise MetricInputError("post-exposure research score requires the six frozen target cells")
    metrics = cellwise_normalized_rmse(
        values,
        POST_EXPOSURE_RESEARCH_CELLS,
        minimum_rows_per_cell=2,
        require_nonzero_standard_deviation=True,
    )
    return weighted_cell_mean(metrics, tuple((cell, 1.0) for cell in POST_EXPOSURE_RESEARCH_CELLS))


def mean_training_scale_normalized_rmse(
    values: Sequence[CellValues],
    expected_cells: Sequence[TargetCell],
    training_scales: Sequence[tuple[TargetCell, float]],
) -> float:
    """Four-cell mean RMSE / TRAIN sample SD (ddof=1), used for model selection."""
    expected = _validate_expected_cells(expected_cells)
    by_cell: dict[TargetCell, CellValues] = {}
    for item in values:
        if item.cell in by_cell:
            raise MetricInputError(f"duplicate scoring cell: {item.cell.name}")
        by_cell[item.cell] = item
    scales: dict[TargetCell, float] = {}
    for cell, raw_scale in training_scales:
        if cell in scales:
            raise MetricInputError(f"duplicate training scale for {cell.name}")
        scale = _number(raw_scale, name=f"training scale for {cell.name}")
        if scale <= 0.0:
            raise MetricInputError(f"training scale for {cell.name} must be positive")
        scales[cell] = scale
    if set(by_cell) != set(expected) or set(scales) != set(expected):
        raise MetricInputError(
            "selection metric requires every expected validation cell and training scale"
        )
    normalized_errors: list[float] = []
    for cell in expected:
        item = by_cell[cell]
        predictions = _vector(item.predictions, name=f"{cell.name} predictions")
        observations = _vector(item.observations, name=f"{cell.name} observations")
        if len(predictions) != len(observations):
            raise MetricInputError(f"prediction and observation shapes differ for {cell.name}")
        normalized_errors.append(_rmse(predictions, observations) / scales[cell])
    return math.fsum(normalized_errors) / len(normalized_errors)


def two_seed_mean(metric_values: Sequence[float]) -> float:
    """Arithmetic mean of exactly two complete, finite model-selection runs."""
    if len(metric_values) != 2:
        raise MetricInputError("the recovered public reference-selection metric requires two seeds")
    values = tuple(_number(value, name="seed metric") for value in metric_values)
    return math.fsum(values) / 2.0


def predictive_progress(normalized_error: float, *, baseline_error: float = 1.0) -> float:
    """Progress over a cell-mean constant predictor: baseline error minus model error."""
    return _number(baseline_error, name="baseline error") - _number(
        normalized_error, name="normalized error"
    )


def progress_ratio(
    numerator_error: float, denominator_error: float, *, baseline_error: float = 1.0
) -> float:
    """Progress(numerator model) / progress(denominator reference model)."""
    numerator = predictive_progress(numerator_error, baseline_error=baseline_error)
    denominator = predictive_progress(denominator_error, baseline_error=baseline_error)
    if abs(denominator) <= PROGRESS_RATIO_DENOMINATOR_TOLERANCE:
        raise MetricInputError("progress ratio denominator has zero progress")
    return _number(numerator / denominator, name="progress ratio")


def relative_progress_loss(
    full_error: float, comparator_error: float, *, baseline_error: float = 1.0
) -> float:
    """(progress(full) - progress(comparator)) / progress(full), without a gate threshold."""
    full_progress = predictive_progress(full_error, baseline_error=baseline_error)
    comparator_progress = predictive_progress(comparator_error, baseline_error=baseline_error)
    if full_progress <= 0.0:
        raise MetricInputError("relative progress loss denominator has zero progress")
    return _number(
        (full_progress - comparator_progress) / full_progress,
        name="relative progress loss",
    )


def relative_progress_gain(
    candidate_error: float, reference_error: float, *, baseline_error: float = 1.0
) -> float:
    """(progress(candidate) - progress(reference)) / progress(reference)."""
    candidate_progress = predictive_progress(candidate_error, baseline_error=baseline_error)
    reference_progress = predictive_progress(reference_error, baseline_error=baseline_error)
    if reference_progress <= 0.0:
        raise MetricInputError("relative progress gain denominator has zero progress")
    return _number(
        (candidate_progress - reference_progress) / reference_progress,
        name="relative progress gain",
    )


def threshold_load_index(primitives: Mapping[str, object]) -> float:
    """Mean of seven support-scaled current-load dimensions, clipped to [0,1]."""
    required = {name for name, _low, _high in THRESHOLD_LOAD_SUPPORTS}
    if set(primitives) != required:
        raise MetricInputError(
            "threshold load input must contain exactly the seven public primitives"
        )
    values: list[float] = []
    for name, low, high in THRESHOLD_LOAD_SUPPORTS:
        value = _number(primitives[name], name=name)
        scaled = (value - low) / (high - low)
        values.append(min(1.0, max(0.0, scaled)))
    return math.fsum(values) / len(values)


def threshold_load_regime(primitives: Mapping[str, object]) -> str:
    """Return high at an index of exactly 0.5 or greater, low otherwise."""
    return "high" if threshold_load_index(primitives) >= THRESHOLD_LOAD_HIGH_CUTOFF else "low"


def rich_history_stratum(
    exposure_times_hours: Sequence[float | None],
    assessments: Sequence[RichHistoryAssessment],
) -> str:
    """Return the recovered exposure-observability × assessment-quality stratum."""
    exposure_times_list: list[float] = []
    for value in exposure_times_hours:
        if value is None:
            continue
        if math.isnan(value):
            continue
        exposure_times_list.append(_number(value, name="history exposure time"))
    exposure_times = tuple(exposure_times_list)
    latest_exposure = max(exposure_times, default=-math.inf)
    valid_count = 0
    trials: list[float] = []
    after_exposure_count = 0
    for assessment in assessments:
        if assessment.validity_state != "valid":
            continue
        valid_count += 1
        if assessment.trial_count is None:
            raise MetricInputError("valid history assessments require trial counts")
        trials.append(_number(assessment.trial_count, name="assessment trial count"))
        if assessment.time_from_origin_hours is not None:
            time_value = assessment.time_from_origin_hours
            if math.isnan(time_value):
                continue
            assessment_time = _number(time_value, name="assessment time")
            if assessment_time > latest_exposure:
                after_exposure_count += 1
    load_level = ("L0", "L1", "L2")[min(after_exposure_count, 2)]
    clean = (
        valid_count >= RICH_HISTORY_CLEAN_MIN_VALID_ASSESSMENTS
        and min(trials, default=math.inf) >= RICH_HISTORY_CLEAN_MIN_TRIALS
    )
    quality = "clean" if clean else "degraded"
    return f"{load_level}|{quality}"


def rich_history_target_cell(
    horizon: ForecastHorizon,
    outcome: OutcomeVariable,
    exposure_times_hours: Sequence[float | None],
    assessments: Sequence[RichHistoryAssessment],
) -> TargetCell:
    """Construct one rich-history target cell from the recovered history strata."""
    if horizon not in _RICH_HISTORY_HORIZONS:
        raise MetricInputError("rich-history horizon must be H72 or D7")
    return TargetCell(
        outcome,
        horizon,
        rich_history_stratum(exposure_times_hours, assessments),
    )


def threshold_response_target_cell(
    horizon: ForecastHorizon,
    outcome: OutcomeVariable,
    primitives: Mapping[str, object],
) -> TargetCell:
    """Construct one proposed threshold-response target cell from public inputs."""
    if horizon not in _POST_EXPOSURE_HORIZONS:
        raise MetricInputError("threshold-response horizon must be H24, H48, or H72")
    return TargetCell(outcome, horizon, threshold_load_regime(primitives))


def compatibility_reanchor_score(
    calibrated_score: float, *, old_reference_progress: float, new_reference_progress: float
) -> float:
    """Invert one historical curve, then apply another; never used by benchmark scoring."""
    score = _number(calibrated_score, name="historical calibrated score")
    if not 0.0 <= score <= 1.0:
        raise MetricInputError("historical calibrated score must be inside [0, 1]")
    old_reference = _number(old_reference_progress, name="old reference progress")
    new_reference = _number(new_reference_progress, name="new reference progress")
    if not 0.0 < old_reference < 1.0 or not 0.0 < new_reference < 1.0:
        raise MetricInputError("reanchoring reference progress values must lie inside (0, 1)")
    if score <= 0.5:
        raw_progress = 2.0 * score * old_reference
    else:
        raw_progress = old_reference + 2.0 * (score - 0.5) * (1.0 - old_reference)
    return piecewise_linear_calibration(raw_progress, new_reference)


__all__ = [
    "BenchmarkScoreResult",
    "CellMetric",
    "CellValues",
    "INITIAL_CAMP_CELLS",
    "MetricInputError",
    "POST_EXPOSURE_RESEARCH_CELLS",
    "PROGRESS_RATIO_DENOMINATOR_TOLERANCE",
    "RICH_HISTORY_CELLS",
    "RICH_HISTORY_CLEAN_MIN_TRIALS",
    "RICH_HISTORY_CLEAN_MIN_VALID_ASSESSMENTS",
    "RICH_HISTORY_CELL_MIN_ROWS",
    "RichHistoryAssessment",
    "THRESHOLD_LOAD_HIGH_CUTOFF",
    "THRESHOLD_LOAD_SUPPORTS",
    "THRESHOLD_RESPONSE_CELLS",
    "TargetMetricValue",
    "calibrated_benchmark_score",
    "cellwise_normalized_rmse",
    "compatibility_reanchor_score",
    "mean_cellwise_normalized_rmse",
    "mean_training_scale_normalized_rmse",
    "piecewise_linear_calibration",
    "population_normalized_rmse",
    "predictive_progress",
    "progress_ratio",
    "relative_progress_gain",
    "relative_progress_loss",
    "rich_history_stratum",
    "rich_history_target_cell",
    "rich_history_target_metrics",
    "rich_history_benchmark_score",
    "point_benchmark_score",
    "sample_standard_deviation",
    "target_metrics_from_cells",
    "threshold_load_index",
    "threshold_load_regime",
    "threshold_response_target_cell",
    "two_seed_mean",
    "training_axis_scales",
    "weighted_cell_mean",
]
