from __future__ import annotations

import math
from typing import cast

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import MetricCategory
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import normalized_load_vector
from cmj_recovery_dynamics.metrics.catalog import POST_EXPOSURE_RESEARCH_EVALUATION
from cmj_recovery_dynamics.metrics.scoring import MetricInputError
from cmj_recovery_dynamics.reproduction.single_exposure import (
    EXPOSURE_SUPPORTS,
    HORIZONS,
    PREDICTOR_FIELDS,
    ROW_KEY_FIELDS,
    TARGET_FIELDS,
)
from cmj_recovery_dynamics.studies.fixed_mode_reference_study import (
    BOOTSTRAP_REPLICATES,
    CELLS,
    RIDGE_FEATURE_NAMES,
    TEST_ROOTS,
    SplitData,
    assert_disjoint_splits,
    camp_bootstrap_intervals,
    camp_unit_ids,
    cell_values_from_arrays,
    fit_cell_model,
    protocol_record,
    score_predictions,
    structured_features,
    to_feature_row,
    validate_episode_rows,
)


def _row(horizon: str, key: int) -> dict[str, object]:
    row: dict[str, object] = {field: 0.5 for field in PREDICTOR_FIELDS if field != "horizon"}
    row["horizon"] = horizon
    for field, (low, high) in EXPOSURE_SUPPORTS:
        row[f"index_exposure.{field}"] = (low + high) / 2.0
    row.update(
        {
            "participant_key": f"participant-{key}",
            "episode_key": f"episode-{key}",
            "query_key": f"query-{key}-{horizon}",
            TARGET_FIELDS[0]: 0.1 + key,
            TARGET_FIELDS[1]: 0.2 + key,
        }
    )
    return row


def _split_data(
    *,
    split: str,
    participant_key: str,
    episode_key: str,
    query_key: str,
) -> SplitData:
    features = np.zeros((1, len(RIDGE_FEATURE_NAMES)), dtype=np.float64)
    targets = np.asarray([[0.1, 0.2]], dtype=np.float64)
    return SplitData(
        split,
        f"{split}-root",
        "oss_clean_room",
        1,
        1,
        features,
        targets,
        np.asarray([24], dtype=np.int64),
        np.asarray([0], dtype=np.int64),
        {
            "participant_key": frozenset({participant_key}),
            "episode_key": frozenset({episode_key}),
            "query_key": frozenset({query_key}),
        },
        "0" * 64,
        0.0,
    )


def test_public_schema_excludes_labels_and_grouping_keys() -> None:
    assert len(PREDICTOR_FIELDS) == 82
    assert len(RIDGE_FEATURE_NAMES) == 84
    assert not set(PREDICTOR_FIELDS).intersection(ROW_KEY_FIELDS)
    assert not set(PREDICTOR_FIELDS).intersection(TARGET_FIELDS)
    assert "target_time_hours" not in PREDICTOR_FIELDS
    encoded, hours = to_feature_row(_row("H48", 0))
    assert encoded.shape == (84,)
    assert hours == 48
    assert tuple(encoded[-3:]) == (0.0, 1.0, 0.0)
    with pytest.raises(ValueError, match="82-field"):
        to_feature_row({**_row("H24", 0), "future_target": 1.0})


def test_episode_rows_keep_all_horizons_in_one_group() -> None:
    rows = [_row(horizon, 1) for horizon, _ in HORIZONS]
    assert validate_episode_rows(rows) == ("participant-1", "episode-1")
    with pytest.raises(ValueError, match="one episode group"):
        validate_episode_rows([rows[0], rows[1], {**rows[2], "episode_key": "other"}])
    with pytest.raises(ValueError, match="horizon order"):
        validate_episode_rows([rows[1], rows[0], rows[2]])


def test_training_and_development_keys_must_be_disjoint() -> None:
    training = _split_data(
        split="training",
        participant_key="shared-participant",
        episode_key="train-episode",
        query_key="train-query",
    )
    development = _split_data(
        split="public_validation",
        participant_key="shared-participant",
        episode_key="dev-episode",
        query_key="dev-query",
    )
    with pytest.raises(ValueError, match="participant_key"):
        assert_disjoint_splits(training, development)


def test_camp_unit_identity_includes_root_and_split() -> None:
    training = camp_unit_ids("training", "source-root", 96)
    development = camp_unit_ids("public_validation", "source-root", 16)
    test_a = camp_unit_ids("public_validation", TEST_ROOTS[0], 16)
    test_b = camp_unit_ids("public_validation", TEST_ROOTS[1], 16)
    assert training.isdisjoint(development)
    assert test_a.isdisjoint(training | development)
    assert test_b.isdisjoint(test_a)


def test_structured_comparator_uses_public_fixed_mode_basis_and_prior_history() -> None:
    rows = [_row("H24", 0), _row("H72", 1)]
    features = np.vstack([to_feature_row(row)[0] for row in rows])
    split = SplitData(
        "public_validation",
        "public-root",
        "caller_supplied_public",
        2,
        1,
        features,
        np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=np.float64),
        np.asarray([24, 72], dtype=np.int64),
        np.asarray([0, 0], dtype=np.int64),
        {field: frozenset() for field in ROW_KEY_FIELDS},
        "0" * 64,
        0.0,
    )
    structured, names = structured_features(split, 0, include_prior=True)
    no_history, no_history_names = structured_features(split, 0, include_prior=False)
    assert structured.shape == (2, 31)
    assert no_history.shape == (2, 19)
    assert any(name.startswith("fixed_24h:") for name in names)
    assert any(name.startswith("fixed_84h:") for name in names)
    assert any(name.startswith("prior_episode[") for name in names)
    assert not any(name.startswith("prior_episode[") for name in no_history_names)
    assert not set(names).intersection(ROW_KEY_FIELDS)
    assert not any("label." in name or "target_time" in name for name in names)
    public_load = normalized_load_vector(
        {field: cast(float, rows[0][f"index_exposure.{field}"]) for field, _ in EXPOSURE_SUPPORTS}
    )
    np.testing.assert_allclose(structured[0, :7], np.asarray(public_load) * math.exp(-1.0))


def test_registered_scorer_skips_missing_labels_independently() -> None:
    horizons = np.repeat(np.asarray([24, 48, 72], dtype=np.int64), 3)
    targets = np.arange(18, dtype=np.float64).reshape(9, 2) + 1.0
    predictions = np.zeros_like(targets)
    targets[0, 0] = np.nan
    values = cell_values_from_arrays(horizons, targets, predictions)
    force_h24 = next(item for item in values if item.cell == CELLS[0])
    impulse_h24 = next(item for item in values if item.cell == CELLS[1])
    assert len(force_h24.observations) == 2
    assert len(impulse_h24.observations) == 3
    result = score_predictions(
        SplitData(
            "public_validation",
            "root",
            "caller_supplied_public",
            9,
            1,
            np.zeros((9, len(RIDGE_FEATURE_NAMES))),
            targets,
            horizons,
            np.zeros(9, dtype=np.int64),
            {field: frozenset() for field in ROW_KEY_FIELDS},
            "0" * 64,
            0.0,
        ),
        predictions,
    )
    assert math.isfinite(cast(float, result["mean_six_cell_nrmse"]))


def test_nonfinite_observed_labels_and_zero_sd_cells_are_rejected() -> None:
    horizons = np.repeat(np.asarray([24, 48, 72], dtype=np.int64), 3)
    targets = np.arange(18, dtype=np.float64).reshape(9, 2) + 1.0
    predictions = np.zeros_like(targets)
    targets[0, 0] = math.inf
    with pytest.raises(ValueError, match="non-finite observed"):
        cell_values_from_arrays(horizons, targets, predictions)

    targets = np.ones((9, 2), dtype=np.float64)
    split = SplitData(
        "public_validation",
        "root",
        "caller_supplied_public",
        9,
        1,
        np.zeros((9, len(RIDGE_FEATURE_NAMES))),
        targets,
        horizons,
        np.zeros(9, dtype=np.int64),
        {field: frozenset() for field in ROW_KEY_FIELDS},
        "0" * 64,
        0.0,
    )
    with pytest.raises(MetricInputError, match="zero truth standard deviation"):
        score_predictions(split, predictions)


def test_ridge_fit_is_deterministic_and_scales_from_training_rows_only() -> None:
    features = np.asarray([[0.0, 2.0], [1.0, 4.0], [2.0, 6.0], [3.0, 8.0]])
    targets = [1.0, 2.0, 3.0, 4.0]
    names = ("x1", "x2")
    first = fit_cell_model(features, targets, names, alpha=0.1)
    second = fit_cell_model(features.copy(), targets, names, alpha=0.1)
    assert first == second
    assert first.feature_means == (1.5, 5.0)
    assert np.isfinite(first.predict(features, names)).all()


def test_camp_bootstrap_is_paired_and_keeps_duplicate_models_identical() -> None:
    horizons = np.tile(np.repeat(np.asarray([24, 48, 72], dtype=np.int64), 2), 16)
    camps = np.repeat(np.arange(16, dtype=np.int64), 6)
    targets = np.empty((len(horizons), 2), dtype=np.float64)
    for index, (camp, horizon) in enumerate(zip(camps, horizons, strict=True)):
        targets[index] = (0.03 * camp + 0.001 * horizon, 0.002 * camp + 0.0001 * horizon)
    predictions = np.zeros_like(targets)
    data = SplitData(
        "public_validation",
        "caller-root",
        "caller_supplied_public",
        len(horizons),
        16,
        np.zeros((len(horizons), len(RIDGE_FEATURE_NAMES)), dtype=np.float64),
        targets,
        horizons,
        camps,
        {field: frozenset() for field in ROW_KEY_FIELDS},
        "0" * 64,
        0.0,
    )
    result = camp_bootstrap_intervals(
        data,
        {"zero_innovation": predictions, "duplicate": predictions.copy()},
    )
    model_intervals = cast(dict[str, object], result["models"])
    duplicate = cast(dict[str, object], model_intervals["duplicate"])
    assert result["represented_camps"] == 16
    assert duplicate["valid_replicates"] == BOOTSTRAP_REPLICATES
    assert duplicate["paired_nrmse_delta_vs_zero_95_percentile_interval"] == [0.0, 0.0]


def test_test_roots_and_bootstrap_protocol_are_frozen_and_research_only() -> None:
    protocol = protocol_record()
    assert len(TEST_ROOTS) == 3 and len(set(TEST_ROOTS)) == 3
    assert protocol["test_roots"] == list(TEST_ROOTS)
    assert BOOTSTRAP_REPLICATES == 5_000
    assert protocol["registered_metric"] == "six_cell_mean_cellwise_normalized_rmse"
    assert POST_EXPOSURE_RESEARCH_EVALUATION.category is MetricCategory.RESEARCH_DIAGNOSTIC
