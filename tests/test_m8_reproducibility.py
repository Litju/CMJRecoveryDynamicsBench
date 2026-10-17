from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from cmj_recovery_dynamics.reproducibility.qualification import (
    ReproducibilityQualificationStatus as Status,
)
from cmj_recovery_dynamics.reproducibility.qualification import (
    _summarize_rows,  # pyright: ignore[reportPrivateUsage]
    build_reproducibility_matrix,
)


def test_m8_matrix_separates_generator_runs_from_historical_result_replay() -> None:
    matrix = build_reproducibility_matrix()
    benchmarks = cast(list[dict[str, object]], matrix["benchmarks"])

    assert len(benchmarks) == 8
    assert matrix["m6_public_claim_count"] == 34
    assert {item["reproducibility_status"] for item in benchmarks} == {
        Status.PARTIALLY_REPRODUCIBLE.value
    }
    assert {item["historical_result_status"] for item in benchmarks} == {
        Status.HISTORICAL_EVIDENCE_ONLY.value,
        Status.NOT_REPRODUCIBLE.value,
    }
    assert not any(
        item["reproducibility_status"] == Status.EXACTLY_REPRODUCIBLE.value for item in benchmarks
    )
    assert all(
        cast(Mapping[str, object], item["dataset"])["public_splits"]
        == ["training", "public_validation"]
        for item in benchmarks
    )
    assert all(
        "restricted" not in cast(str, result["identity"])
        for benchmark in benchmarks
        for result in cast(list[dict[str, object]], benchmark["expected_historical_results"])
    )


def test_split_summary_hashes_ordered_rows_and_counts_missing_targets() -> None:
    rows = (
        {"row": 1, "features": {"missing": float("nan")}, "label": {"force": 1.0, "impulse": None}},
        {"row": 2, "features": {"missing": 0.0}, "label": {"force": 3.0, "impulse": 2.0}},
    )
    summary = _summarize_rows(rows, expected_rows=3)
    repeated = _summarize_rows(rows, expected_rows=3)
    reordered = _summarize_rows(tuple(reversed(rows)), expected_rows=3)

    assert summary.row_count == 2
    assert summary.expected_rows == 3
    assert not summary.row_count_matches_authority
    assert summary.target_value_count == 4
    assert summary.missing_target_values == 1
    assert summary.non_finite_target_values == 0
    assert summary.target_summaries["force"]["mean"] == 2.0
    assert summary.row_output_sha256 == repeated.row_output_sha256
    assert summary.row_output_sha256 != reordered.row_output_sha256


def test_split_summary_counts_non_finite_targets_without_serializing_invalid_json() -> None:
    summary = _summarize_rows(
        ({"label": {"force": float("inf"), "impulse": 0.0}},),
    )

    assert summary.non_finite_target_values == 1
    assert not summary.all_present_targets_finite
