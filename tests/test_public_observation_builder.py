"""Independent origin ingestion, all-column goldens and adversarial availability checks."""

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256
from typing import cast

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.dynamics.event_time_adaptation_recovery import ExposureComponent
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_FEATURE_NAMES,
    GATE7_FEATURE_UNITS,
    Gate7RoutineSource,
    Gate7RoutineState,
    project_gate7_v1,
)
from cmj_recovery_dynamics.observations.public_builder import (
    Gate7ObservationBuilderV1,
    Gate7OriginObservation,
    fixture_receipt_v1,
    gate7_observation_payload_v1,
    gate7_origin_from_mapping,
    generate_gate7_fixture_v1,
)
from cmj_recovery_dynamics.reproduction.camp_history import (
    AssessmentAvailability,
    AssessmentObservation,
    CampExposure,
    CriterionTrial,
    InformationLeakageError,
    PlannedExposure,
    generate_canonical_camp_sample,
)


def _minutes(value: float) -> tuple[ExposureComponent, ...]:
    return (ExposureComponent("duration_minutes", value, "minutes", 100),)


def _origin() -> Gate7OriginObservation:
    # Authorized test observations, independently specified; no fixture-generator dependency.
    history = tuple(
        AssessmentObservation(
            f"assessment-{index}",
            time,
            AssessmentAvailability.VALID,
            tuple(
                CriterionTrial(force + shift, impulse + shift / 10, depth)
                for shift in (-0.3, 0, 0.3)
            ),
        )
        for index, (time, force, impulse, depth) in enumerate(
            (
                (-240, 20, 2, 0.25),
                (-72, 22, 2.25, 0.25),
                (-48, 23, 2.5, 0.375),
                (-24, 24, 2.75, 0.5),
            )
        )
    )
    return Gate7OriginObservation(
        "independent-participant",
        "independent-origin",
        0,
        tuple(reversed(history)),
        (CampExposure("prior", -96, "training", _minutes(123.5)),),
        CampExposure("index", 0, "match", _minutes(80)),
        (
            PlannedExposure("plan-120", 120, "training", _minutes(110.75)),
            PlannedExposure("plan-48", 48, "training", _minutes(95.25)),
        ),
    )


def _routine(payload: bytes) -> Gate7RoutineSource:
    return Gate7RoutineSource(payload, sha256(payload).hexdigest())


def _builder() -> Gate7ObservationBuilderV1:
    origin = _origin()
    source = "independent-authorized-test-source"
    payload = gate7_observation_payload_v1(source, (origin,))
    return Gate7ObservationBuilderV1(
        source,
        (origin,),
        sha256(payload).hexdigest(),
        _routine(b'[["independent-origin",true,"TRIAL_INVALID",0]]'),
    )


def _values(origin: Gate7OriginObservation) -> dict[str, object]:
    return {field.name: getattr(origin, field.name) for field in fields(origin)}


def test_independent_ingestion_projects_every_column_in_source_order_and_units() -> None:
    builder = _builder()
    assert gate7_origin_from_mapping(_values(_origin())) == _origin()
    expected = np.asarray(
        [
            [
                23.5,
                2.625,
                1,
                0,
                72,
                66,
                78,
                -240,
                20,
                2,
                0.25,
                -72,
                22,
                2.25,
                0.25,
                -48,
                23,
                2.5,
                0.375,
                -24,
                24,
                2.75,
                0.5,
                -96,
                123.5,
                0,
                80,
                0,
                80,
                48,
                95.25,
                0,
                0,
                1,
                0,
                0,
                0,
                1,
                0,
            ],
            [
                23.5,
                2.625,
                0,
                1,
                168,
                156,
                180,
                -240,
                20,
                2,
                0.25,
                -72,
                22,
                2.25,
                0.25,
                -48,
                23,
                2.5,
                0.375,
                -24,
                24,
                2.75,
                0.5,
                -96,
                123.5,
                0,
                80,
                0,
                80,
                48,
                95.25,
                120,
                110.75,
                1,
                0,
                0,
                0,
                1,
                0,
            ],
        ],
        dtype=np.float64,
    )
    matrix = builder.matrix()
    np.testing.assert_array_equal(matrix, expected)
    assert matrix.dtype == np.float64 and matrix.shape == (2, 39)
    assert np.isfinite(matrix).all()
    assert len(GATE7_FEATURE_NAMES) == 39
    assert tuple(unit.value for unit in GATE7_FEATURE_UNITS) == (
        "N/kg",
        "m/s",
        "dimensionless",
        "dimensionless",
        "h",
        "h",
        "h",
        *(unit for _ in range(4) for unit in ("h", "N/kg", "m/s", "m")),
        "h",
        "min",
        "h",
        "min",
        *(unit for _ in range(3) for unit in ("h", "min")),
        *("dimensionless" for _ in range(6)),
    )
    for index, horizon in enumerate((ForecastHorizon.H72, ForecastHorizon.D7)):
        value = builder.build("independent-origin", horizon)
        result = project_gate7_v1((value,), routine_source=builder.routine_source)
        assert result.matrix is not None
        np.testing.assert_array_equal(result.matrix[0], expected[index])
    first, second = builder.inputs()
    assert first.routine_assessment == second.routine_assessment
    assert first.row.baseline == second.row.baseline
    assert first.row.assessment_history == second.row.assessment_history
    assert first.row.exposure_history == second.row.exposure_history
    assert first.row.index_exposure == second.row.index_exposure
    assert len(first.row.known_plan) == 1 and len(second.row.known_plan) == 2


@pytest.mark.parametrize(
    "horizon,time",
    [
        (ForecastHorizon.H72, 66),
        (ForecastHorizon.H72, 78),
        (ForecastHorizon.D7, 156),
        (ForecastHorizon.D7, 180),
    ],
)
def test_query_bounds(horizon: ForecastHorizon, time: float) -> None:
    builder = _builder()
    value = builder.build("independent-origin", horizon, time)
    assert value.row.target_time_hours == time
    assert project_gate7_v1((value,), routine_source=builder.routine_source).matrix is not None


def test_freeze_generator_output_and_group_isolation() -> None:
    expected = {
        "training": (
            "cc9df5158b4ccd3100f42588a69ca79a4e0f04ed5685f2dddf76f80a94d354cf",
            "60f813fcc98bca2444c28ab94e07c74f042b5661e176fa5d7482399c586b5eed",
            "3404bd1c6c2988a76b33cebbeb40de9a5152f0881a5182d47a4248e3a213c8a6",
        ),
        "public_validation": (
            "979adc14bf17250dfaf38061e2ff1c962ad95a27da13692d4f612f62ef594726",
            "7fb7915f3d8e88e6487b9713ed759d9ada82cedb71763f78bfff040c8216c25b",
            "2d236629413f250697a6f21df66ff04bec56a6e8ddc760ae49c63d2dc6a6e147",
        ),
    }
    groups: list[set[str]] = []
    for split, hashes in expected.items():
        builder = generate_gate7_fixture_v1(split)
        receipt = fixture_receipt_v1(split)
        assert receipt == fixture_receipt_v1(split)
        assert (
            tuple(receipt[key] for key in ("observation_sha256", "routine_sha256", "matrix_sha256"))
            == hashes
        )
        assert receipt["historical_replay"] is False
        groups.append({origin.participant_key for origin in builder.origins})
        assert len(groups[-1]) == (4 if split == "training" else 2)
        assert all(
            sum(item.participant_key == key for item in builder.origins) == 2 for key in groups[-1]
        )
        assert builder.matrix().shape == (16 if split == "training" else 8, 39)
        for first, second in zip(builder.inputs()[::2], builder.inputs()[1::2], strict=True):
            assert first.routine_assessment == second.routine_assessment
            assert first.row.origin_id == second.row.origin_id
            assert first.row.participant_key == second.row.participant_key
    assert groups[0].isdisjoint(groups[1])


@pytest.mark.parametrize(
    "field",
    [
        "label",
        "target",
        "target_assessment",
        "scorer",
        "future_realized_exposures",
        "random_state",
        "anything",
    ],
)
def test_closed_ingestion_rejects_extra_information(field: str) -> None:
    with pytest.raises(InformationLeakageError):
        gate7_origin_from_mapping({**_values(_origin()), field: 42})


@pytest.mark.parametrize("time", [0, 1, 72, float("nan"), float("inf"), True])
def test_future_or_malformed_assessment_time(time: float) -> None:
    origin = _origin()
    with pytest.raises(ValueError):
        history = (
            replace(origin.assessment_history[0], time_from_origin_hours=time),
            *origin.assessment_history[1:],
        )
        replace(origin, assessment_history=history)


@pytest.mark.parametrize("time", [1, 72, float("nan"), float("inf"), True, -25])
def test_snapshot_availability_rejects_post_origin_or_inconsistent_times(time: float) -> None:
    with pytest.raises(ValueError):
        replace(_origin(), available_at_origin_hours=time)


@pytest.mark.parametrize("count", [0, 1, 3, 5])
def test_no_assessment_padding_or_truncation(count: int) -> None:
    origin = _origin()
    with pytest.raises(ValueError):
        replace(origin, assessment_history=(origin.assessment_history * 2)[:count])


def test_invalid_trials_history_and_plan_cardinality() -> None:
    origin = _origin()
    invalid = replace(
        origin.assessment_history[0], availability=AssessmentAvailability.TRIAL_INVALID, trials=()
    )
    with pytest.raises(ValueError):
        replace(origin, assessment_history=(invalid, *origin.assessment_history[1:]))
    for count in (1, 2, 4):
        with pytest.raises(ValueError):
            invalid = replace(
                origin.assessment_history[0],
                trials=(origin.assessment_history[0].trials * 2)[:count],
            )
            replace(origin, assessment_history=(invalid, *origin.assessment_history[1:]))
    for exposures in ((), origin.exposure_history * 2):
        with pytest.raises(ValueError):
            replace(origin, exposure_history=exposures)
    for plan in ((), origin.known_plan[:1], origin.known_plan * 2):
        with pytest.raises(ValueError):
            replace(origin, known_plan=plan)
    with pytest.raises(ValueError):
        replace(
            origin,
            known_plan=(
                replace(origin.known_plan[0], time_from_origin_hours=121),
                origin.known_plan[1],
            ),
        )
    with pytest.raises(ValueError):
        replace(
            origin,
            known_plan=(replace(origin.known_plan[0], known_at_origin=False), origin.known_plan[1]),
        )
    with pytest.raises(ValueError):
        replace(
            origin,
            exposure_history=(replace(origin.exposure_history[0], time_from_origin_hours=1),),
        )
    with pytest.raises(ValueError):
        replace(origin, index_exposure=replace(origin.index_exposure, time_from_origin_hours=1))
    with pytest.raises(ValueError):
        replace(origin, assessment_history=(origin.assessment_history[0],) * 4)


@pytest.mark.parametrize("position", ["prior", "index", "plan"])
@pytest.mark.parametrize(
    "changes",
    [
        {"units": "hours"},
        {"observed": False, "value": None},
        {"day_mask": False},
        {"event_mask": False},
        {"name": "other"},
        {"value": -1},
        {"value": float("nan")},
        {"value": True},
    ],
)
def test_duration_boundary(position: str, changes: dict[str, object]) -> None:
    origin = _origin()
    with pytest.raises((TypeError, ValueError)):
        component = replace(origin.index_exposure.components[0], **changes)
        if position == "prior":
            replace(
                origin,
                exposure_history=(replace(origin.exposure_history[0], components=(component,)),),
            )
        elif position == "index":
            replace(origin, index_exposure=replace(origin.index_exposure, components=(component,)))
        else:
            replace(
                origin,
                known_plan=(
                    replace(origin.known_plan[0], components=(component,)),
                    origin.known_plan[1],
                ),
            )


def test_source_pins_origin_consistency_and_replacement_rejection() -> None:
    builder = _builder()
    with pytest.raises(ValueError, match="SHA-256"):
        replace(builder, source_identity="untrusted-replacement")
    with pytest.raises(ValueError, match="SHA-256"):
        replace(builder, origins=(replace(_origin(), participant_key="different"),))
    with pytest.raises(ValueError, match="unique"):
        replace(builder, origins=builder.origins * 2)
    with pytest.raises(ValueError, match="match exactly"):
        replace(builder, routine_source=_routine(b'[["different-origin",true,"TRIAL_INVALID",0]]'))
    with pytest.raises(InformationLeakageError):
        replace(
            builder, routine_source=_routine(b'[["independent-origin",true,"TRIAL_INVALID",1]]')
        )
    with pytest.raises(ValueError):
        _routine(b'[["independent-origin",false,"TRIAL_INVALID",0]]')
    with pytest.raises(ValueError):
        _routine(b'[["independent-origin",true,"UNKNOWN",0]]')
    with pytest.raises(ValueError):
        Gate7RoutineSource(builder.routine_source.payload, "0" * 64)
    with pytest.raises(FrozenInstanceError):
        builder.__setattr__("routine_source", _routine(b"[]"))
    first, second = builder.inputs()
    assert first.routine_assessment is not None
    assert (
        project_gate7_v1(
            (
                replace(
                    first, routine_assessment=replace(first.routine_assessment, origin_id="other")
                ),
            ),
            routine_source=builder.routine_source,
        ).matrix
        is None
    )
    changed = _routine(b'[["independent-origin",false,"UNSCHEDULED",0]]')
    injected = replace(second, routine_assessment=changed.records()[0])
    assert project_gate7_v1((injected,), routine_source=builder.routine_source).matrix is None
    with pytest.raises(TypeError):
        cast(Callable[..., object], builder.build)(
            "independent-origin",
            ForecastHorizon.H72,
            routine_source=changed,
        )


@pytest.mark.parametrize("state", list(Gate7RoutineState))
def test_all_origin_routine_states_project_consistently(state: Gate7RoutineState) -> None:
    payload = json.dumps(
        [["independent-origin", state is not Gate7RoutineState.UNSCHEDULED, state.value, 0]]
    ).encode()
    builder = replace(_builder(), routine_source=_routine(payload))
    matrix = builder.matrix()
    np.testing.assert_array_equal(matrix[0, 33:], matrix[1, 33:])
    assert matrix[0, 34:].sum() == 1


def test_historical_generator_remains_incompatible_and_separate() -> None:
    sample = generate_canonical_camp_sample(participant_count=1)
    row = sample.rows[0]
    with pytest.raises(ValueError):
        Gate7OriginObservation(
            row.participant_key,
            row.origin_id,
            0,
            row.assessment_history,
            row.exposure_history,
            row.index_exposure,
            row.known_plan,
        )


@pytest.mark.parametrize(
    "horizon,time",
    [(ForecastHorizon.H72, 79), (ForecastHorizon.D7, 155), (ForecastHorizon.H72, True)],
)
def test_invalid_query_time(horizon: ForecastHorizon, time: float) -> None:
    with pytest.raises(ValueError):
        _builder().build("independent-origin", horizon, time)


def test_unknown_origin_and_split_are_rejected() -> None:
    with pytest.raises(ValueError):
        _builder().build("unknown", ForecastHorizon.H72)
    with pytest.raises(ValueError):
        generate_gate7_fixture_v1("historical")
