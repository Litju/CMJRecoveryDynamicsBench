"""Hand-computable checks for metric equations, cells, and failure policies."""

from math import log, sqrt

import pytest

from cmj_recovery_dynamics.contracts import ForecastHorizon, OutcomeVariable, TargetCell
from cmj_recovery_dynamics.metrics import (
    INITIAL_CAMP_CELLS,
    POST_EXPOSURE_RESEARCH_CELLS,
    RICH_HISTORY_CELLS,
    THRESHOLD_RESPONSE_CELLS,
    CellMetric,
    CellValues,
    MetricInputError,
    RichHistoryAssessment,
    binary_auc,
    calibrated_benchmark_score,
    cellwise_normalized_rmse,
    empirical_energy_score,
    gaussian_kl_divergence,
    joint_ellipsoid_coverage,
    mahalanobis_squared,
    marginal_interval_coverage,
    mean_cellwise_normalized_rmse,
    mean_fold_auc,
    mean_prior_whitened_energy_score,
    mean_prior_whitened_variogram_score,
    mean_standardized_euclidean_error,
    mean_training_scale_normalized_rmse,
    normal_standardized_residual_diagnostics,
    paired_score_difference,
    parameter_root_mean_square_error,
    piecewise_linear_calibration,
    point_benchmark_score,
    posterior_trace_ratio,
    predictive_progress,
    prior_whitened_energy_score,
    prior_whitened_energy_score_regret,
    prior_whitened_variogram_score,
    prior_whitened_variogram_score_regret,
    progress_ratio,
    relative_progress_gain,
    relative_progress_loss,
    rich_history_benchmark_score,
    rich_history_stratum,
    rich_history_target_cell,
    rich_history_target_metrics,
    sample_covariance,
    sample_standard_deviation,
    student_t_covariance_from_scale,
    student_t_scale_from_covariance,
    threshold_load_index,
    threshold_load_regime,
    threshold_response_target_cell,
    training_axis_scales,
    two_seed_mean,
    validate_two_target_covariance,
    variogram_score,
    weighted_cell_mean,
)
from cmj_recovery_dynamics.metrics.compatibility import reanchor_historical_score
from cmj_recovery_dynamics.metrics.provenance import (
    HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE,
    HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE,
)


def _cell_values(cells: tuple[TargetCell, ...]) -> tuple[CellValues, ...]:
    return tuple(CellValues(cell, (1.0, 1.0), (0.0, 2.0)) for cell in cells)


def test_population_normalized_rmse_uses_population_sd_and_zero_sd_fallback() -> None:
    from cmj_recovery_dynamics.metrics import population_normalized_rmse

    assert population_normalized_rmse((1, 1), (0, 2)) == pytest.approx(1.0)
    assert population_normalized_rmse((3, 3), (2, 2)) == pytest.approx(1.0)
    with pytest.raises(MetricInputError, match="shapes must match"):
        population_normalized_rmse((0, 1), (0,))
    with pytest.raises(MetricInputError, match="finite"):
        population_normalized_rmse((0.0, float("nan")), (0.0, 1.0))


def test_scoring_cells_are_exact_and_zero_variance_policy_is_explicit() -> None:
    cells = POST_EXPOSURE_RESEARCH_CELLS
    perfect = tuple(CellValues(cell, (0.0, 2.0), (0.0, 2.0)) for cell in cells)
    assert mean_cellwise_normalized_rmse(perfect, cells) == 0.0
    assert len(INITIAL_CAMP_CELLS) == 4
    assert len(POST_EXPOSURE_RESEARCH_CELLS) == 6
    assert len(THRESHOLD_RESPONSE_CELLS) == 12
    assert len(RICH_HISTORY_CELLS) == 24

    degenerate = tuple(CellValues(cell, (2.0, 3.0), (2.0, 2.0)) for cell in cells)
    with pytest.raises(MetricInputError, match="zero truth standard deviation"):
        cellwise_normalized_rmse(
            degenerate, cells, minimum_rows_per_cell=2, require_nonzero_standard_deviation=True
        )
    fallback = cellwise_normalized_rmse(degenerate, cells)
    assert all(not metric.normalized for metric in fallback)
    assert all(metric.normalized_error == pytest.approx(sqrt(0.5)) for metric in fallback)


def test_missing_duplicate_unexpected_and_nonfinite_cells_fail_closed() -> None:
    cells = POST_EXPOSURE_RESEARCH_CELLS
    complete = _cell_values(cells)
    with pytest.raises(MetricInputError, match="missing="):
        cellwise_normalized_rmse(complete[:-1], cells)
    with pytest.raises(MetricInputError, match="duplicate scoring cell"):
        cellwise_normalized_rmse(complete + (complete[0],), cells)
    with pytest.raises(MetricInputError, match="unexpected="):
        cellwise_normalized_rmse(
            complete[:-1]
            + (
                CellValues(
                    TargetCell(OutcomeVariable.NET_IMPULSE_INNOVATION, ForecastHorizon.D7),
                    (0.0,),
                    (0.0,),
                ),
            ),
            cells,
        )
    malformed = complete[:-1] + (CellValues(cells[-1], (0.0, 1.0), (0.0,)),)
    with pytest.raises(MetricInputError, match="shapes differ"):
        cellwise_normalized_rmse(malformed, cells)
    nonfinite = complete[:-1] + (CellValues(cells[-1], (float("inf"),), (0.0,)),)
    with pytest.raises(MetricInputError, match="finite"):
        cellwise_normalized_rmse(nonfinite, cells)


def test_uniform_and_explicit_nonuniform_cell_weights_are_visible() -> None:
    first, second = POST_EXPOSURE_RESEARCH_CELLS[:2]
    metrics = (
        CellMetric(first, 0.0, 1.0, 0.2, 2, True),
        CellMetric(second, 0.0, 1.0, 0.8, 2, True),
    )
    assert weighted_cell_mean(metrics, ((first, 1.0), (second, 1.0))) == pytest.approx(0.5)
    assert weighted_cell_mean(metrics, ((first, 1.0), (second, 3.0))) == pytest.approx(0.65)


def test_rich_history_aggregates_strata_per_outcome_before_progress_clipping() -> None:
    metrics = tuple(
        CellMetric(
            cell,
            root_mean_square_error=0.5
            if cell.outcome is OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION
            else 1.5,
            observation_standard_deviation=1.0,
            normalized_error=0.5
            if cell.outcome is OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION
            else 1.5,
            row_count=2,
            normalized=True,
        )
        for cell in RICH_HISTORY_CELLS
    )
    targets = rich_history_target_metrics(metrics)
    assert len(targets) == 2
    assert targets[0].value == pytest.approx(0.5)
    assert targets[1].value == pytest.approx(1.5)
    score = calibrated_benchmark_score(targets, reference_progress=0.5)
    assert score.aggregate_progress == pytest.approx(0.25)
    assert score.score == pytest.approx(0.25)

    complete = tuple(CellValues(cell, (0.0, 2.0), (0.0, 2.0)) for cell in RICH_HISTORY_CELLS)
    assert (
        len(cellwise_normalized_rmse(complete, RICH_HISTORY_CELLS, minimum_rows_per_cell=2)) == 24
    )
    with pytest.raises(MetricInputError, match="missing="):
        cellwise_normalized_rmse(complete[:-1], RICH_HISTORY_CELLS, minimum_rows_per_cell=2)


def test_calibrated_point_score_distinguishes_the_two_camp_floors() -> None:
    cells = _cell_values(INITIAL_CAMP_CELLS)
    initial = point_benchmark_score(
        cells, INITIAL_CAMP_CELLS, normalization_floor=1.01, reference_progress=0.5
    )
    canonical = point_benchmark_score(
        cells, INITIAL_CAMP_CELLS, normalization_floor=1.0, reference_progress=0.5
    )
    assert (
        point_benchmark_score(
            cells, INITIAL_CAMP_CELLS, normalization_floor=1.01, reference_progress=0.5
        )
        == initial
    )
    assert initial.score == pytest.approx(0.01 / 1.01)
    assert canonical.score == 0.0
    assert piecewise_linear_calibration(0.5, 0.5) == 0.5
    assert piecewise_linear_calibration(1.0, 0.5) == 1.0
    assert piecewise_linear_calibration(0.0, 0.5) == 0.0

    rich_values = tuple(CellValues(cell, (0.0, 2.0), (0.0, 2.0)) for cell in RICH_HISTORY_CELLS)
    rich = rich_history_benchmark_score(rich_values, reference_progress=0.5)
    assert rich.score == 1.0


def test_history_strata_use_strict_time_and_exact_quality_thresholds() -> None:
    six_clean = tuple(RichHistoryAssessment(0.0, "valid", 2.0) for _ in range(6))
    assert rich_history_stratum((0.0,), six_clean) == "L0|clean"
    one_after = (RichHistoryAssessment(1.0, "valid", 2.0),) + six_clean[1:]
    assert rich_history_stratum((0.0,), one_after) == "L1|clean"
    degraded = (RichHistoryAssessment(1.0, "valid", 1.0),) + six_clean[1:]
    assert rich_history_stratum((0.0,), degraded) == "L1|degraded"
    missing_time = (RichHistoryAssessment(float("nan"), "valid", 2.0),) + six_clean[1:]
    assert rich_history_stratum((float("nan"),), missing_time) == "L2|clean"
    assert (
        rich_history_target_cell(
            ForecastHorizon.D7,
            OutcomeVariable.NET_IMPULSE_INNOVATION,
            (0.0,),
            six_clean,
        ).stratum
        == "L0|clean"
    )


def test_threshold_load_strata_clip_support_and_include_the_half_boundary() -> None:
    from cmj_recovery_dynamics.metrics.scoring import THRESHOLD_LOAD_SUPPORTS

    lows = {name: low for name, low, _high in THRESHOLD_LOAD_SUPPORTS}
    highs = {name: high for name, _low, high in THRESHOLD_LOAD_SUPPORTS}
    mids = {name: (low + high) / 2.0 for name, low, high in THRESHOLD_LOAD_SUPPORTS}
    assert threshold_load_index(lows) == 0.0
    assert threshold_load_index(highs) == 1.0
    assert threshold_load_index(mids) == pytest.approx(0.5)
    assert threshold_load_regime(mids) == "high"
    cell = threshold_response_target_cell(
        ForecastHorizon.H24, OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION, mids
    )
    assert cell.stratum == "high"
    with pytest.raises(MetricInputError, match="exactly the seven"):
        threshold_load_index({**lows, "unregistered": 0.0})


def test_model_selection_uses_training_sample_sd_and_two_seed_mean() -> None:
    assert sample_standard_deviation((0.0, 2.0)) == pytest.approx(sqrt(2.0))
    values = _cell_values(INITIAL_CAMP_CELLS)
    scales = tuple((cell, sqrt(2.0)) for cell in INITIAL_CAMP_CELLS)
    assert mean_training_scale_normalized_rmse(values, INITIAL_CAMP_CELLS, scales) == pytest.approx(
        1.0 / sqrt(2.0)
    )
    assert two_seed_mean((0.3, 0.5)) == pytest.approx(0.4)
    with pytest.raises(MetricInputError, match="two seeds"):
        two_seed_mean((0.3,))

    assert training_axis_scales(((0.0, 0.0), (2.0, 0.0)), minimum_scale=1e-9) == pytest.approx(
        (sqrt(2.0), 1e-9)
    )


def test_progress_ratios_keep_numerator_denominator_and_thresholds_separate() -> None:
    assert predictive_progress(0.6) == pytest.approx(0.4)
    assert progress_ratio(0.6, 0.5) == pytest.approx(0.8)
    assert relative_progress_loss(0.5, 0.6) == pytest.approx(0.2)
    assert relative_progress_gain(0.5, 0.6) == pytest.approx(0.25)
    with pytest.raises(MetricInputError, match="zero progress"):
        progress_ratio(0.5, 1.0)
    with pytest.raises(MetricInputError, match="zero progress"):
        progress_ratio(0.5, 1.0 - 1e-13)


def test_historical_score_reanchor_is_an_explicit_transform_only() -> None:
    expected = (
        0.5
        * HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE
        / HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE
    )
    assert reanchor_historical_score(0.5) == pytest.approx(expected)


def test_empirical_v_score_and_unbiased_prior_whitened_score_are_distinct() -> None:
    samples = ((0.0, 0.0), (2.0, 0.0))
    observation = (1.0, 0.0)
    assert empirical_energy_score(
        samples, observation, standardization_scales=(1.0, 1.0)
    ) == pytest.approx(0.5)
    assert empirical_energy_score(
        samples, observation, standardization_scales=(1.0, 1.0)
    ) == empirical_energy_score(samples, observation, standardization_scales=(1.0, 1.0))
    with pytest.raises(MetricInputError, match="dimension"):
        empirical_energy_score(samples, (1.0,), standardization_scales=(1.0,))
    with pytest.raises(MetricInputError, match="finite"):
        empirical_energy_score(
            ((0.0, float("inf")),), observation, standardization_scales=(1.0, 1.0)
        )
    assert prior_whitened_energy_score(
        samples,
        observation,
        prior_mean=(0.0, 0.0),
        prior_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(0.0)
    assert mean_prior_whitened_energy_score(
        samples_by_case=(samples, ((0.0, 0.0), (0.0, 0.0))),
        observations=(observation, (1.0, 0.0)),
        prior_means=((0.0, 0.0), (0.0, 0.0)),
        prior_covariances=(
            ((1.0, 0.0), (0.0, 1.0)),
            ((1.0, 0.0), (0.0, 1.0)),
        ),
    ) == pytest.approx(0.5)
    assert prior_whitened_energy_score_regret(
        forecast_samples=((0.0, 0.0), (1.0, 0.0)),
        reference_samples=((0.0, 0.0), (2.0, 0.0)),
        prior_mean=(0.0, 0.0),
        prior_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(-0.5)
    variogram = prior_whitened_variogram_score(
        samples,
        observation,
        prior_mean=(0.0, 0.0),
        prior_covariance=((1.0, 0.0), (0.0, 1.0)),
    )
    assert variogram == pytest.approx((sqrt(2.0) / 2.0 - 1.0) ** 2)
    assert mean_prior_whitened_variogram_score(
        samples_by_case=(samples, samples),
        observations=(observation, observation),
        prior_means=((0.0, 0.0), (0.0, 0.0)),
        prior_covariances=(
            ((1.0, 0.0), (0.0, 1.0)),
            ((1.0, 0.0), (0.0, 1.0)),
        ),
    ) == pytest.approx(variogram)
    assert variogram_score(samples, observation) == pytest.approx(variogram)
    assert prior_whitened_variogram_score_regret(
        forecast_samples=((0.0, 0.0), (1.0, 0.0)),
        reference_samples=((0.0, 0.0), (2.0, 0.0)),
        prior_mean=(0.0, 0.0),
        prior_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx((0.5 - sqrt(2.0) / 2.0) ** 2)
    assert paired_score_difference((0.9, 0.6), (0.7, 0.8)) == pytest.approx(0.0)


def test_covariance_whitening_student_t_and_coverage_equations() -> None:
    covariance = ((4.0, 0.2), (0.2, 0.04))
    assert validate_two_target_covariance(covariance) == covariance
    assert mahalanobis_squared((0.2, 0.05), covariance) == pytest.approx(0.0633333333333333)
    scale = student_t_scale_from_covariance(covariance, 5.0)
    assert scale[0][0] == pytest.approx(2.4)
    recovered = student_t_covariance_from_scale(scale, 5.0)
    for row, expected_row in zip(recovered, covariance, strict=True):
        assert row == pytest.approx(expected_row)
    with pytest.raises(MetricInputError, match="symmetric"):
        validate_two_target_covariance(((1.0, 0.2), (0.1, 1.0)))
    with pytest.raises(MetricInputError, match="positive definite"):
        validate_two_target_covariance(((1.0, 2.0), (2.0, 1.0)))
    with pytest.raises(MetricInputError, match="ill-conditioned"):
        validate_two_target_covariance(((1.0, 0.0), (0.0, 1e-14)))

    observations = ((0.0, 0.2), (2.0, 0.6))
    assert marginal_interval_coverage(observations, (0.0, 0.0), (2.0, 1.0)) == (1.0, 1.0)
    residual_mean, residual_coverage = normal_standardized_residual_diagnostics(
        (-2.0, 0.0, 2.0), confidence=0.90
    )
    assert residual_mean == pytest.approx(4.0 / 3.0)
    assert residual_coverage == pytest.approx(1.0 / 3.0)
    assert joint_ellipsoid_coverage(
        observations=((0.0, 0.0), (2.0, 0.0)),
        means=((0.0, 0.0), (0.0, 0.0)),
        covariances=(((1.0, 0.0), (0.0, 1.0)), ((1.0, 0.0), (0.0, 1.0))),
        squared_radius=1.0,
    ) == pytest.approx(0.5)


def test_probability_research_diagnostics_use_explicit_hand_computable_equations() -> None:
    assert sample_covariance(((0.0, 0.0), (2.0, 0.0))) == ((2.0, 0.0), (0.0, 0.0))
    assert mean_standardized_euclidean_error(
        predictions=((1.0, 2.0), (0.0, 0.0)),
        observations=((0.0, 0.0), (0.0, 0.0)),
        scales=(1.0, 2.0),
    ) == pytest.approx(sqrt(2.0) / 2.0)
    assert parameter_root_mean_square_error(((1.0, 0.0),), ((0.0, 0.0),)) == pytest.approx(
        sqrt(0.5)
    )
    assert gaussian_kl_divergence(
        (0.0, 0.0),
        ((1.0, 0.0), (0.0, 1.0)),
        reference_mean=(0.0, 0.0),
        reference_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(0.0)
    assert gaussian_kl_divergence(
        (1.0, 0.0),
        ((1.0, 0.0), (0.0, 1.0)),
        reference_mean=(0.0, 0.0),
        reference_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(0.5)
    assert gaussian_kl_divergence(
        (0.0, 0.0),
        ((2.0, 0.0), (0.0, 1.0)),
        reference_mean=(0.0, 0.0),
        reference_covariance=((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(0.5 * (1.0 - log(2.0)))
    assert posterior_trace_ratio(
        (((0.5, 0.0), (0.0, 0.5)), ((1.0, 0.0), (0.0, 1.0))),
        ((1.0, 0.0), (0.0, 1.0)),
    ) == pytest.approx(0.75)
    assert binary_auc((0, 1, 0, 1), (0.1, 0.8, 0.4, 0.6)) == 1.0
    assert binary_auc((0, 1), (0.5, 0.5)) == pytest.approx(0.5)
    assert mean_fold_auc((0.8, 0.6)) == pytest.approx(0.7)
