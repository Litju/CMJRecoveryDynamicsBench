from __future__ import annotations

import math

import numpy as np

from cmj_recovery_dynamics.contracts import OutcomeVariable
from cmj_recovery_dynamics.reproduction.rich_history import (
    CATEGORICAL_FIELDS,
    MISSING,
    NUMERIC_FIELDS,
    R02_FIELD_NAMES,
    GroupingMetadata,
    RichHistoryRow,
)
from cmj_recovery_dynamics.studies.reference_model_study import (
    HORIZON_TARGET_COLUMNS,
    FeatureEncoder,
    build_cell_values,
    fit_feature_encoder,
    fit_ridge,
)


def _row(
    *,
    camp: int = 0,
    horizon: str = "H72",
    baseline_force: float = 0.0,
    target_time: float = 70.0,
    event_kind: str = MISSING,
    force_target: float | None = 0.1,
    impulse_target: float | None = 0.2,
) -> RichHistoryRow:
    fields: dict[str, object] = {
        name: float("nan") if name in NUMERIC_FIELDS else MISSING for name in R02_FIELD_NAMES
    }
    for field in CATEGORICAL_FIELDS:
        fields[field] = MISSING
    fields.update(
        {
            "horizon": horizon,
            "target_time_hours": target_time,
            "baseline_force": baseline_force,
            "n_assessments": 0.0,
            "n_history_exposures": 0.0,
            "n_plan": 0.0,
            "index_exposure.event_kind": event_kind,
        }
    )
    return RichHistoryRow(
        f"p-{camp}",
        f"o-{camp}",
        f"q-{camp}-{horizon}",
        fields,
        {
            HORIZON_TARGET_COLUMNS[0]: force_target,
            HORIZON_TARGET_COLUMNS[1]: impulse_target,
        },
        GroupingMetadata("public_train", camp, 0, 0),
    )


def test_feature_encoder_uses_training_statistics_and_reserved_unknowns() -> None:
    training = [
        _row(baseline_force=1.0, event_kind="run"),
        _row(camp=1, baseline_force=3.0, event_kind="lift"),
    ]
    encoder, encoded = fit_feature_encoder(training)
    assert isinstance(encoder, FeatureEncoder)
    assert "target_time_hours" not in encoder.feature_names
    assert "baseline_force__missing" in encoder.feature_names
    assert encoded.shape == (2, len(encoder.feature_names))

    unknown = _row(camp=2, event_kind="unseen")
    changed_target_time = _row(camp=3, event_kind="unseen", target_time=170.0)
    unknown_encoded = encoder.transform([unknown])
    assert np.array_equal(unknown_encoded, encoder.transform([changed_target_time]))
    assert bool(np.isfinite(unknown_encoded).all())
    unknown_column = encoder.feature_names.index("index_exposure.event_kind==<UNKNOWN>")
    assert unknown_encoded[0, unknown_column] > 0.0


def test_ridge_fit_is_finite_and_uses_an_unpenalized_intercept() -> None:
    features = np.asarray([[0.0], [1.0], [2.0], [3.0]], dtype=np.float64)
    targets = [2.0, 5.0, 8.0, 11.0]
    fit = fit_ridge(features, targets, alpha=0.01)
    prediction = fit.predict(features)
    assert fit.training_rows == 4
    assert bool(np.isfinite(prediction).all())
    assert np.max(np.abs(prediction - np.asarray(targets))) < 0.1


def test_cell_builder_skips_a_missing_outcome_without_dropping_the_other() -> None:
    row = _row(force_target=None, impulse_target=0.25)
    cells = build_cell_values([row], np.zeros((1, 2), dtype=np.float64))
    assert len(cells) == 1
    assert cells[0].cell.outcome is OutcomeVariable.NET_IMPULSE_INNOVATION
    assert cells[0].observations == (0.25,)
    assert math.isfinite(cells[0].observations[0])
