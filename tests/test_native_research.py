"""Synthetic-only examples for the native research contract, not empirical results."""

from dataclasses import replace
from typing import Any

import pytest

from cmj_recovery_dynamics.metrics.native_research import (
    NATIVE_SOURCE_V1,
    NativeAuthority,
    NativeCellRMSE,
    NativeHorizon,
    NativeObservation,
    NativePrediction,
    NativeQuery,
    NativeTarget,
    synthetic_native_rmse_v1,
)

AUTHORITY = NativeAuthority("synthetic-source-authority", "a" * 64)
SPLITS = {"train": ["train-person"], "validation": ["validation-person"], "test": ["test-person"]}


def fixture() -> tuple[list[NativePrediction], list[NativeObservation]]:
    predictions: list[NativePrediction] = []
    observations: list[NativeObservation] = []
    for horizon, at in ((NativeHorizon.H72, 72.0), (NativeHorizon.D7, 168.0)):
        query = NativeQuery(
            "synthetic-dataset",
            "test-person",
            "origin-1",
            f"query-{horizon}",
            f"input-{horizon}",
            horizon,
            ("assessment-1", "assessment-2"),
            (-120.0, -48.0),
            (3, 3),
        )
        for target, unit, value in (
            (NativeTarget.FORCE, "N/kg", 2.0),
            (NativeTarget.IMPULSE, "m/s", 0.4),
        ):
            predictions.append(NativePrediction(query, target, unit, value))
            observations.append(
                NativeObservation(query, target, unit, 0.0, at, 3, f"target-{horizon}")
            )
    return predictions, observations


def run(
    predictions: list[NativePrediction], observations: list[NativeObservation], **kwargs: object
) -> tuple[NativeCellRMSE, ...]:
    args: dict[str, Any] = dict(
        source_contract=NATIVE_SOURCE_V1,
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )
    args.update(kwargs)
    return synthetic_native_rmse_v1(predictions, observations, **args)


def test_synthetic_four_native_cells_and_units() -> None:
    predictions, observations = fixture()
    result = run(predictions, list(reversed(observations)))
    assert [(x.horizon, x.target, x.unit, x.rmse) for x in result] == [
        (NativeHorizon.H72, NativeTarget.FORCE, "N/kg", 2.0),
        (NativeHorizon.H72, NativeTarget.IMPULSE, "m/s", 0.4),
        (NativeHorizon.D7, NativeTarget.FORCE, "N/kg", 2.0),
        (NativeHorizon.D7, NativeTarget.IMPULSE, "m/s", 0.4),
    ]


def test_pairing_and_all_four_cells_are_required() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="pair exactly"):
        run(p, o[:-1])
    with pytest.raises(ValueError, match="both native targets"):
        run(p[:-1], o[:-1])
    with pytest.raises(ValueError, match="four native"):
        run(p[:2], o[:2])
    with pytest.raises(ValueError, match="duplicate"):
        run(p + [p[0]], o)
    with pytest.raises(ValueError, match="pairing mismatch"):
        run(p, [replace(o[0], query=replace(o[0].query, input_identity="other")), *o[1:]])
    with pytest.raises(ValueError, match="pairing mismatch"):
        run(p, [replace(o[0], query=replace(o[0].query, origin="other")), *o[1:]])


def test_source_and_dataset_authority_are_not_inferred() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="source contract"):
        run(p, o, source_contract=replace(NATIVE_SOURCE_V1, force_measurement="peak force"))
    with pytest.raises(ValueError, match="source authority"):
        run(p, o, source_authority=replace(AUTHORITY, source_sha256="b" * 64))
    with pytest.raises(ValueError, match="source authority"):
        run(
            p,
            o,
            source_authority=replace(AUTHORITY, source_sha256="bad"),
            expected_authority=replace(AUTHORITY, source_sha256="bad"),
        )
    with pytest.raises(ValueError, match="synthetic"):
        run(p, o, dataset_kind="empirical")


def test_native_units_time_criteria_and_finiteness_fail_closed() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="unit"):
        run([replace(p[0], unit="m/s"), *p[1:]], o)
    with pytest.raises(ValueError, match="finite"):
        run([replace(p[0], value=float("nan")), *p[1:]], o)
    with pytest.raises(ValueError, match="target window"):
        run(
            p,
            [replace(o[0], observed_at_hours=65.0), replace(o[1], observed_at_hours=65.0), *o[2:]],
        )
    with pytest.raises(ValueError, match="three valid"):
        run(p, [replace(o[0], valid_trial_count=5), *o[1:]])
    with pytest.raises(ValueError, match="share an assessment"):
        run(p, [replace(o[0], observed_at_hours=73.0), *o[1:]])
    bad_query = replace(p[0].query, baseline_offsets_hours=(-120.0, -1.0))
    with pytest.raises(ValueError, match="baseline"):
        run([replace(p[0], query=bad_query), *p[1:]], o)


def test_participant_separation_and_test_membership() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="overlap"):
        run(p, o, participant_splits={**SPLITS, "train": ["test-person"]})
    with pytest.raises(ValueError, match="not in the test split"):
        run(p, o, participant_splits={**SPLITS, "test": ["other-person"]})


def test_query_and_assessment_identity_mutations_are_rejected() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="share an assessment"):
        run(p, [replace(o[0], assessment_identity="other"), *o[1:]])
    wrong = replace(p[0].query, baseline_valid_trial_counts=(3, 5))
    with pytest.raises(ValueError, match="baseline"):
        run([replace(p[0], query=wrong), *p[1:]], o)
    duplicate = replace(p[0].query, query="another-query")
    with pytest.raises(ValueError, match="duplicate origin and horizon"):
        run([*p, replace(p[0], query=duplicate)], o)
    with pytest.raises(ValueError, match="finite"):
        run([replace(p[0], value=True), *p[1:]], o)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        run([replace(p[0], value=10**1000), *p[1:]], o)


def test_source_target_type_and_windows_are_not_silently_substituted() -> None:
    p, o = fixture()
    with pytest.raises(ValueError, match="source contract"):
        run(p, o, source_contract=replace(NATIVE_SOURCE_V1, units=("m/s", "N/kg")))
    with pytest.raises(ValueError, match="source contract"):
        run(
            p,
            o,
            source_contract=replace(
                NATIVE_SOURCE_V1,
                windows=((NativeHorizon.H72, 72, 60, 78), *NATIVE_SOURCE_V1.windows[1:]),
            ),
        )
    with pytest.raises(ValueError, match="unit"):
        run([replace(p[0], target="relative_mean_concentric_force"), *p[1:]], o)  # type: ignore[arg-type]


def test_synthetic_rmse_aggregates_paired_rows_without_canonical_mapping() -> None:
    predictions, observations = fixture()
    other_predictions = [
        replace(
            row,
            query=replace(row.query, origin="origin-2", query=f"other-{row.query.horizon}"),
            value=0.0,
        )
        for row in predictions
    ]
    other_observations = [
        replace(
            row, query=replace(row.query, origin="origin-2", query=f"other-{row.query.horizon}")
        )
        for row in observations
    ]
    result = run(predictions + other_predictions, observations + other_observations)
    assert all(cell.row_count == 2 for cell in result)
    assert result[0].rmse == pytest.approx(2.0 / 2**0.5)
    assert result[1].rmse == pytest.approx(0.4 / 2**0.5)
    assert result[2].rmse == pytest.approx(2.0 / 2**0.5)
    assert result[3].rmse == pytest.approx(0.4 / 2**0.5)


def test_horizons_cannot_silently_change_origin_baseline() -> None:
    p, o = fixture()
    wrong = replace(p[2].query, baseline_assessment_ids=("different", "assessment-2"))
    with pytest.raises(ValueError, match="origin baseline identity"):
        run([*p[:2], replace(p[2], query=wrong), *p[3:]], o)
    with pytest.raises(ValueError, match="target assessment cannot be a baseline"):
        run(
            p,
            [
                replace(o[0], assessment_identity="assessment-1"),
                replace(o[1], assessment_identity="assessment-1"),
                *o[2:],
            ],
        )
