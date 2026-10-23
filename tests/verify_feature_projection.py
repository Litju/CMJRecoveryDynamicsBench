"""Rerun the preserved extractor locally; only synthetic fixtures/results leave this tool.

Supply an authorized original source file with --original-source. No source lookup,
checkpoint loading, or restricted dataset access is performed by this harness.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_FEATURE_CONTRACT,
    GATE7_FEATURE_NAMES,
    Gate7ExposureFeature,
    Gate7HistoryAssessment,
    Gate7PlanFeature,
    Gate7PublicFeatureRow,
    Gate7RoutineAssessment,
    Gate7RoutineState,
    Gate7RoutineTemporalAuthority,
    project_gate7_historical_v1,
)

SOURCE_SHA256 = "b414b8928396af65e716a15dd05ce200464b6e94431439bc077fdf4612e20adb"


def fixtures() -> list[dict[str, Any]]:
    """Independent literals; no production builder or existing golden vectors."""
    rows: list[dict[str, Any]] = []
    for horizon, time, window in (("H72", 71.5, [66, 78]), ("D7", 169.25, [156, 180])):
        for state in Gate7RoutineState:
            for ties in (False, True):
                rows.append(
                    {
                        "baseline": {
                            "relative_mean_concentric_force": 27.125,
                            "relative_concentric_net_impulse": 3.0625,
                        },
                        "horizon": horizon,
                        "target_time_hours": time,
                        "target_window_hours": window,
                        "public_features": {
                            "history_assessments": [
                                {
                                    "time_from_origin_hours": t,
                                    "relative_mean_concentric_force": f,
                                    "relative_concentric_net_impulse": i,
                                    "depth_m": d,
                                    "validity_state": "TRIAL_INVALID",
                                }
                                for t, f, i, d in (
                                    (-36, 28.5, 3.25, 0.42),
                                    (-192, 26.5, 2.75, 0.35),
                                    (-36 if ties else -84, 25.25, 2.875, 0.38),
                                    (-12, 29.75, 3.5, 0.46),
                                )
                            ],
                            "history_exposures": [
                                {"time_from_origin_hours": -90.5, "duration_minutes": 117.75}
                            ],
                            "index_exposure": {
                                "time_from_origin_hours": 0,
                                "duration_minutes": 73.125,
                            },
                            "known_plan": [
                                {"time_from_origin_hours": 36, "duration_minutes": 92.5},
                                {"time_from_origin_hours": 0, "duration_minutes": 73.125},
                                *(
                                    [
                                        {
                                            "time_from_origin_hours": 36 if ties else 132,
                                            "duration_minutes": 105.875,
                                        }
                                    ]
                                    if horizon == "D7"
                                    else []
                                ),
                            ],
                            "routine_assessment": {
                                "scheduled": state is not Gate7RoutineState.UNSCHEDULED,
                                "availability_state": state.value,
                            },
                        },
                    }
                )
    return rows


def public_row(row: dict[str, Any]) -> Gate7PublicFeatureRow:
    features = row["public_features"]
    routine = features["routine_assessment"]
    return Gate7PublicFeatureRow(
        row["baseline"]["relative_mean_concentric_force"],
        row["baseline"]["relative_concentric_net_impulse"],
        ForecastHorizon.H72 if row["horizon"] == "H72" else ForecastHorizon.D7,
        row["target_time_hours"],
        tuple(row["target_window_hours"]),
        tuple(Gate7HistoryAssessment(**item) for item in features["history_assessments"]),
        tuple(Gate7ExposureFeature(**item) for item in features["history_exposures"]),
        Gate7ExposureFeature(**features["index_exposure"]),
        tuple(Gate7PlanFeature(**item) for item in features["known_plan"]),
        Gate7RoutineAssessment(
            routine["scheduled"],
            Gate7RoutineState(routine["availability_state"]),
            Gate7RoutineTemporalAuthority.UNRESOLVED,
        ),
    )


def verify(source: Path) -> dict[str, Any]:
    source_bytes = source.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("original extractor source identity mismatch")
    # Execute the unmodified preserved module; none of its I/O/model helpers are called.
    original = runpy.run_path(str(source))
    assert original["FEATURE_NAMES"] == GATE7_FEATURE_NAMES
    rows = fixtures()
    fixture_bytes = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    differences: list[float] = []
    for row in rows:
        expected = original["feature_vector"](copy.deepcopy(row))
        actual = project_gate7_historical_v1((public_row(row),))[0]
        assert expected.shape == actual.shape == (39,)
        np.testing.assert_array_equal(actual, expected)
        differences.append(float(np.max(np.abs(actual - expected))))

    invalids: list[dict[str, Any]] = []
    for field in ("history_assessments", "history_exposures", "known_plan"):
        malformed = copy.deepcopy(rows[0])
        malformed["public_features"][field] = []
        invalids.append(malformed)
    for field in ("history_exposures", "index_exposure", "known_plan"):
        for value in (None, "malformed", float("nan"), float("inf")):
            malformed = copy.deepcopy(rows[0])
            target = malformed["public_features"][field]
            if isinstance(target, list):
                target = cast(list[dict[str, Any]], target)[0]
            target["duration_minutes"] = value
            invalids.append(malformed)

    def public_extract(value: dict[str, Any]) -> object:
        return project_gate7_historical_v1((public_row(value),))

    extractors: tuple[Callable[[dict[str, Any]], object], ...] = (
        original["feature_vector"],
        public_extract,
    )
    for row in invalids:
        for extract in extractors:
            try:
                extract(copy.deepcopy(row))
            except (ValueError, TypeError):
                pass
            else:
                raise AssertionError("invalid fixture accepted")
    return {
        "source_contract": GATE7_FEATURE_CONTRACT.version,
        "model_identity": GATE7_FEATURE_CONTRACT.model_identity,
        "source_module_sha256": SOURCE_SHA256,
        "fixture_identity": "independent_synthetic_projection_v1",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "method": "unmodified original feature_vector versus public historical projection",
        "column_count": 39,
        "valid_vectors": len(rows),
        "column_comparisons": len(rows) * 39,
        "invalid_vectors_rejected_by_both": len(invalids),
        "absolute_tolerance": 0.0,
        "relative_tolerance": 0.0,
        "max_absolute_difference": max(differences),
        "coverage": [
            "H72/D7",
            "stable assessment and plan ties",
            "two-plan zero padding",
            "three-plan preservation",
            "all five routine states",
            "raw minute durations",
            "missing records",
            "null/nonnumeric/nonfinite durations",
        ],
        "result": "PASS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-source", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().original_source), indent=2))
