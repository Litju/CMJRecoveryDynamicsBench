from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from math import erfc, exp, pi, sin, sqrt
from typing import Any, Literal, cast

import numpy as np
import pytest

import cmj_recovery_dynamics.dynamics.biexponential_episode_response as response_module
from cmj_recovery_dynamics.dynamics.biexponential_episode_response import (
    BASE_FAST_INTERACTIONS,
    BASE_FAST_LINEAR_WEIGHTS,
    BASE_SLOW_INTERACTIONS,
    BASE_SLOW_LINEAR_WEIGHTS,
    CORRELATED_RESPONSE_BASIS_INTERACTIONS,
    CORRELATED_RESPONSE_BASIS_WEIGHTS,
    FAST_AMPLITUDE_SUPPORT,
    FAST_TAU_SUPPORT_HOURS,
    SLOW_AMPLITUDE_SUPPORT,
    SLOW_TAU_SUPPORT_HOURS,
    BiexponentialEpisodeParameters,
    CampEffects,
    ResponseEffects,
    episode_response,
    response_parameters_for_exposure,
    sample_camp_effects,
    sample_participant_context,
)
from cmj_recovery_dynamics.dynamics.correlated_exposure_response import (
    BASE_EXPOSURE_PARAMETERS,
    CORRELATED_EXPOSURE_PARAMETERS,
    CORRELATED_EXPOSURE_SPECIFICATION,
    CORRELATED_SOURCE_ARCHETYPE_NAMES,
    EXPOSURE_THRESHOLD_SEMANTICS,
    LATENT_FACTOR_AXES,
    ExposureArchetype,
    ExposureSample,
    is_high_load,
    mixture_for,
    normalized_load_vector,
    sample_correlated_exposure,
    sample_preliminary_exposure,
)
from cmj_recovery_dynamics.observations.episode_summary import (
    EPISODE_SUMMARY_OBSERVATION,
    assessment_error_sd_fraction,
    draw_episode_discrepancy,
    measure_scalar_assessment,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    CONCENTRIC_DURATION_SUPPORT_SECONDS,
    GRAVITATIONAL_ACCELERATION_M_PER_S2,
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    TRACE_NODE_COUNT,
    compute_net_impulse,
    measure_phase_consistent_assessment,
    realize_concentric_trial,
)
from cmj_recovery_dynamics.reproduction.contracts import ReproductionStatus as Status
from cmj_recovery_dynamics.reproduction.single_exposure import (
    BASELINE_FIELDS,
    BASELINE_PRE_EXPOSURE_HOURS,
    CURRENT_EPISODE_EXPOSURES,
    CURRENT_EXPOSURE_TIME_HOURS,
    EXACTNESS_BOUNDARIES,
    EXPOSURE_FIELDS,
    EXPOSURE_SUPPORTS,
    FORMULATIONS,
    HORIZONS,
    NO_ADDITIONAL_EXPOSURE_THROUGH_H72,
    PARTICIPANT_FIELDS,
    PREDICTOR_BLOCK_GEOMETRY,
    PREDICTOR_FIELDS,
    PRIOR_COMPLETE_EPISODES,
    PUBLIC_ROOT_SEED,
    REFERENCE_DATASET_HASHES,
    RNG_VERSION,
    ROW_KEY_FIELDS,
    ROW_ORDERING_STATUS,
    SOURCE_CLOSURES,
    SPLIT_GEOMETRY,
    TARGET_FIELDS,
    TARGET_UNITS,
    TARGETS_PER_ROW,
    TRANSITIONS,
    KeyedRandomStreams,
    PublicExposure,
    generate_episode,
    iter_public_members,
    project_episode,
)


def test_source_closures_and_benchmark_transitions() -> None:
    assert {
        name: (
            item.response_world,
            item.observation,
            item.dataset,
            item.task,
            item.representation,
        )
        for name, item in FORMULATIONS.items()
    } == {
        "preliminary_post_exposure_recovery": (
            "base_biexponential",
            "preliminary",
            "preliminary",
            "single_exposure_innovation",
            "82_predictor_fields",
        ),
        "phase_consistent_post_exposure_recovery": (
            "base_biexponential",
            "phase_consistent_force_impulse",
            "phase_consistent",
            "single_exposure_innovation",
            "82_predictor_fields",
        ),
        "correlated_exposure_recovery": (
            "correlated_exposure",
            "phase_consistent_force_impulse",
            "correlated",
            "single_exposure_innovation",
            "82_predictor_fields",
        ),
    }
    assert {item.response_family for item in FORMULATIONS.values()} == {
        "biexponential_episode_response"
    }
    assert {name: item.response_mapping for name, item in FORMULATIONS.items()} == {
        "preliminary_post_exposure_recovery": "base_seven_primitive",
        "phase_consistent_post_exposure_recovery": "base_seven_primitive",
        "correlated_exposure_recovery": "correlated_four_basis",
    }
    assert [(edge.changed, edge.unchanged) for edge in TRANSITIONS] == [
        (("observation", "dataset"), ("response_world", "task", "representation")),
        (("response_world", "dataset"), ("observation", "task", "representation")),
    ]
    assert REFERENCE_DATASET_HASHES["preliminary"] != REFERENCE_DATASET_HASHES["phase_consistent"]
    assert REFERENCE_DATASET_HASHES["phase_consistent"] != REFERENCE_DATASET_HASHES["correlated"]
    assert [
        (closure.parameter_authority, closure.source_commit, closure.task_tree)
        for closure in SOURCE_CLOSURES.values()
    ] == [
        (
            "source_parameters_1.0.0",
            "da3fa115838b177f5ba2bd055a5c3465654c4e22",
            "e11c1140b362c52d40942463bb0714171ae165f8",
        ),
        (
            "source_parameters_1.1.0",
            "04e9db465a481a88f18e8fc062e317269204dce8",
            "5ef8ad267d3e57f8fa73dd3b82967937291b20ca",
        ),
        (
            "source_parameters_1.2.0",
            "144d283f7b43e6c1a2972b8b58cfc3e4e05b384a",
            "7dbd339858555e11065f9a022820708d8c012f96",
        ),
    ]
    assert all(
        not path.startswith("/")
        for closure in SOURCE_CLOSURES.values()
        for path in closure.source_paths
    )


def _scaffold(
    lag: float, fast_amplitude: float, slow_amplitude: float, fast_tau: float, slow_tau: float
) -> float:
    return episode_response(
        lag,
        BiexponentialEpisodeParameters(fast_amplitude, slow_amplitude, fast_tau, slow_tau),
    )


def test_base_equation_p1_corner_values_and_p2_monotone_recovery() -> None:
    minimum = BiexponentialEpisodeParameters(0.01, 0.0, 12.0, 48.0)
    maximum = BiexponentialEpisodeParameters(0.08, 0.08, 36.0, 120.0)
    expected_pct = {
        24.0: (0.135, 10.657),
        48.0: (0.018, 7.471),
        72.0: (0.002, 5.473),
    }
    for horizon, bounds in expected_pct.items():
        assert 100 * abs(episode_response(horizon, minimum)) == pytest.approx(bounds[0], abs=0.0006)
        assert 100 * abs(episode_response(horizon, maximum)) == pytest.approx(bounds[1], abs=0.0006)

    assert episode_response(0.0, minimum) == pytest.approx(-0.01)
    assert episode_response(24.0, minimum) == pytest.approx(
        -minimum.fast_amplitude * exp(-24.0 / minimum.fast_time_constant_hours)
    )
    for fast_amp in FAST_AMPLITUDE_SUPPORT:
        for slow_amp in SLOW_AMPLITUDE_SUPPORT:
            for fast_tau in FAST_TAU_SUPPORT_HOURS:
                for slow_tau in SLOW_TAU_SUPPORT_HOURS:
                    values = [
                        episode_response(
                            index / 10,
                            BiexponentialEpisodeParameters(fast_amp, slow_amp, fast_tau, slow_tau),
                        )
                        for index in range(721)
                    ]
                    assert all(np.isfinite(values))
                    assert all(
                        right >= left for left, right in zip(values, values[1:], strict=False)
                    )
                    assert values[-1] <= 0.0
    assert abs(episode_response(72, minimum)) < 0.0001
    assert abs(episode_response(72, maximum)) > 0.054


def test_base_midpoint_sensitivities_and_generic_parameter_validation() -> None:
    expected = {
        "fast_amplitude": (2.58, 0.95, 0.35),
        "slow_amplitude": (6.01, 4.52, 3.39),
        "fast_tau": (1.70, 1.10, 0.60),
        "slow_tau": (0.85, 1.21, 1.30),
    }
    actual: dict[str, list[float]] = {name: [] for name in expected}
    expected_midpoint_pct = (4.661, 2.868, 1.922)
    for index, (_horizon, lag) in enumerate(HORIZONS):
        assert 100 * abs(_scaffold(lag, 0.045, 0.040, 24.0, 84.0)) == pytest.approx(
            expected_midpoint_pct[index], abs=0.0006
        )
        actual["fast_amplitude"].append(
            100
            * abs(_scaffold(lag, 0.08, 0.04, 24.0, 84.0) - _scaffold(lag, 0.01, 0.04, 24.0, 84.0))
        )
        actual["slow_amplitude"].append(
            100
            * abs(_scaffold(lag, 0.045, 0.08, 24.0, 84.0) - _scaffold(lag, 0.045, 0.0, 24.0, 84.0))
        )
        actual["fast_tau"].append(
            100
            * abs(_scaffold(lag, 0.045, 0.04, 36.0, 84.0) - _scaffold(lag, 0.045, 0.04, 12.0, 84.0))
        )
        actual["slow_tau"].append(
            100
            * abs(
                _scaffold(lag, 0.045, 0.04, 24.0, 120.0) - _scaffold(lag, 0.045, 0.04, 24.0, 48.0)
            )
        )
    for name, values in actual.items():
        assert values == pytest.approx(expected[name], abs=0.006)

    generic = BiexponentialEpisodeParameters(0.0, 0.081, 2.0, 200.0)
    assert (
        generic.fast_amplitude,
        generic.slow_amplitude,
        generic.fast_time_constant_hours,
        generic.slow_time_constant_hours,
    ) == (0.0, 0.081, 2.0, 200.0)
    with pytest.raises(ValueError, match="amplitudes must be non-negative"):
        BiexponentialEpisodeParameters(-0.001, 0.04, 24.0, 84.0)
    with pytest.raises(ValueError, match="time constants must be positive"):
        BiexponentialEpisodeParameters(0.04, 0.04, 0.0, 84.0)
    with pytest.raises(ValueError, match="lag"):
        episode_response(-1.0, BiexponentialEpisodeParameters(0.04, 0.04, 24.0, 84.0))


def test_source_response_builder_fails_closed_outside_frozen_supports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exposure = PublicExposure(90.0, 9000.0, 1500.0, 300.0, 30, 120, 8.0, 720.0)
    no_effects = ResponseEffects(((0.0, 0.0), (0.0, 0.0)), ((0.0, 0.0), (0.0, 0.0)))
    no_camp_effects = CampEffects(((0.0, 0.0), (0.0, 0.0)))
    worlds: tuple[Literal["base_biexponential"], Literal["correlated_exposure"]] = (
        "base_biexponential",
        "correlated_exposure",
    )
    supports = (
        FAST_AMPLITUDE_SUPPORT,
        SLOW_AMPLITUDE_SUPPORT,
        FAST_TAU_SUPPORT_HOURS,
        SLOW_TAU_SUPPORT_HOURS,
    )
    for world in worlds:
        parameters = response_parameters_for_exposure(
            exposure, no_effects, no_camp_effects, "force", world=world
        )
        assert all(
            low <= value <= high
            for value, (low, high) in zip(
                (
                    parameters.fast_amplitude,
                    parameters.slow_amplitude,
                    parameters.fast_time_constant_hours,
                    parameters.slow_time_constant_hours,
                ),
                supports,
                strict=True,
            )
        )

    def out_of_range_sigmoid(_value: float) -> float:
        return 2.0

    monkeypatch.setitem(response_module.__dict__, "_sigmoid", out_of_range_sigmoid)
    for world in worlds:
        with pytest.raises(ValueError, match="single-exposure parameters escaped"):
            response_parameters_for_exposure(
                exposure, no_effects, no_camp_effects, "force", world=world
            )


def test_base_feature_maps_and_participant_camp_effects_are_source_bound() -> None:
    exposure = PublicExposure(90.0, 9000.0, 1500.0, 300.0, 30, 120, 8.0, 720.0)
    vector = normalized_load_vector(exposure)
    assert len(vector) == 7
    assert BASE_FAST_LINEAR_WEIGHTS == (0.14, 0.14, 0.16, 0.16, 0.14, 0.12, 0.14)
    assert BASE_FAST_INTERACTIONS == ((2, 3, 0.60), (4, 5, 0.35), (0, 6, 0.20))
    assert BASE_SLOW_LINEAR_WEIGHTS == (0.18, 0.18, 0.13, 0.10, 0.12, 0.12, 0.17)
    assert BASE_SLOW_INTERACTIONS == ((0, 1, 0.45), (6, 4, 0.25), (2, 5, 0.20))
    participant_zero = ResponseEffects(((0.0, 0.0), (0.0, 0.0)), ((0.0, 0.0), (0.0, 0.0)))
    camp_zero = CampEffects(((0.0, 0.0), (0.0, 0.0)))
    params = response_parameters_for_exposure(exposure, participant_zero, camp_zero, "force")
    score_fast = sum(x * w for x, w in zip(vector, BASE_FAST_LINEAR_WEIGHTS, strict=True)) - 0.5
    score_fast += sum(c * (vector[i] * vector[j] - 0.25) for i, j, c in BASE_FAST_INTERACTIONS)
    score_slow = sum(x * w for x, w in zip(vector, BASE_SLOW_LINEAR_WEIGHTS, strict=True)) - 0.5
    score_slow += sum(c * (vector[i] * vector[j] - 0.25) for i, j, c in BASE_SLOW_INTERACTIONS)

    def sigmoid(value: float) -> float:
        return 1.0 / (1.0 + exp(-value))

    assert params.fast_amplitude == pytest.approx(0.01 + 0.07 * sigmoid(score_fast))
    assert params.slow_amplitude == pytest.approx(0.08 * sigmoid(score_slow))
    assert (params.fast_time_constant_hours, params.slow_time_constant_hours) == (24.0, 84.0)

    participant_effect = replace(participant_zero, amplitude_logits=((1.0, 1.0), (0.0, 0.0)))
    camp_effect = replace(camp_zero, amplitude_logit_offsets=((1.0, 1.0), (0.0, 0.0)))
    changed_participant = response_parameters_for_exposure(
        exposure, participant_effect, camp_zero, "force"
    )
    changed_camp = response_parameters_for_exposure(
        exposure, participant_zero, camp_effect, "force"
    )
    assert changed_participant.fast_amplitude != params.fast_amplitude
    assert changed_participant.fast_time_constant_hours == params.fast_time_constant_hours
    assert changed_camp.slow_amplitude != params.slow_amplitude
    assert changed_camp.slow_time_constant_hours == params.slow_time_constant_hours

    context_streams = KeyedRandomStreams("lcmj-v2", "context-check")
    context = sample_participant_context(context_streams)
    strength_fraction = (context.strength_index + 1.0) / 2.0
    force_noise = context_streams.generator("participant_baseline_force", "context").uniform()
    impulse_noise = context_streams.generator("participant_baseline_impulse", "context").uniform()
    assert context.baseline_force_n_per_kg == pytest.approx(
        18.0 + 12.0 * (0.75 * strength_fraction + 0.25 * force_noise)
    )
    assert context.baseline_impulse_m_per_s == pytest.approx(
        2.0 + 2.0 * (0.40 * strength_fraction + 0.60 * impulse_noise)
    )
    assert 0.5 <= context.training_age_years <= 18.0
    assert sample_camp_effects(KeyedRandomStreams("lcmj-v2", "camp-check")) == sample_camp_effects(
        KeyedRandomStreams("lcmj-v2", "camp-check")
    )


def test_base_exposure_supports_and_scalar_split_mixtures() -> None:
    assert EXPOSURE_THRESHOLD_SEMANTICS == (
        ("high_speed_distance_m", ">5.5 m/s"),
        ("sprint_distance_m", ">=7.0 m/s"),
        ("high_intensity_accel_count", ">=+2.0 m/s²"),
        ("high_intensity_decel_count", "<=-2.0 m/s²"),
    )
    assert BASE_EXPOSURE_PARAMETERS.train_high_load_probability == 0.30
    assert BASE_EXPOSURE_PARAMETERS.validation_high_load_probability == 0.70
    assert BASE_EXPOSURE_PARAMETERS.prior_high_load_probability == 0.50
    assert not is_high_load(PublicExposure(45.0, 3000.0, 0.0, 0.0, 0, 0, 2.0, 90.0))
    assert is_high_load(PublicExposure(82.5, 8000.0, 1000.0, 300.0, 75, 75, 6.0, 495.0))
    streams = KeyedRandomStreams("w03-exposure", "fixture")
    for index in range(120):
        exposure = sample_preliminary_exposure(
            streams.child(index),
            high_load_probability=0.30,
            episode_key=f"current-{index}",
        )
        assert len(normalized_load_vector(exposure)) == 7
        assert is_high_load(exposure) in {True, False}
        assert exposure.session_rpe_load_au == exposure.duration_min * exposure.session_rpe_cr10
        for name, (low, high) in EXPOSURE_SUPPORTS:
            assert low <= exposure.as_dict()[name] <= high

    with pytest.raises(ValueError, match="outside its frozen supports"):
        normalized_load_vector(
            {
                **PublicExposure(82.5, 8000, 1000, 300, 75, 75, 6, 495).as_dict(),
                "duration_min": 44.0,
            }
        )
    with pytest.raises(ValueError, match="high-load probability"):
        sample_preliminary_exposure(streams, high_load_probability=1.01)


def test_preliminary_is_scalar_only_and_remains_partial() -> None:
    streams = KeyedRandomStreams("preliminary", "assessment")
    assessment = measure_scalar_assessment(24.0, 3.0, streams, assessment_key="baseline")
    assert len(assessment.force_trials) == len(assessment.impulse_trials) == 3
    assert assessment.force_mean == pytest.approx(sum(assessment.force_trials) / 3)
    assert assessment.impulse_mean == pytest.approx(sum(assessment.impulse_trials) / 3)
    assert set(assessment.__dataclass_fields__) == {"force_trials", "impulse_trials"}
    assert not hasattr(assessment, "time_seconds")
    assert not hasattr(assessment, "concentric_duration_seconds")
    assert EXACTNESS_BOUNDARIES["preliminary_post_exposure_recovery"].observation is Status.PARTIAL
    assert (
        EXACTNESS_BOUNDARIES["preliminary_post_exposure_recovery"].complete_generator
        is Status.PARTIAL
    )
    assert EPISODE_SUMMARY_OBSERVATION.measurement_construction.endswith(
        "freezes no shared force-time trace or force/impulse identity."
    )


def test_phase_consistent_trace_integrates_force_and_impulse() -> None:
    assert GRAVITATIONAL_ACCELERATION_M_PER_S2 == 9.80665
    assessment = measure_phase_consistent_assessment(
        24.0,
        3.0,
        KeyedRandomStreams("phase-consistent", "assessment"),
        assessment_key="baseline",
    )
    assert len(assessment.trials) == 3
    for trial in assessment.trials:
        assert (
            len(trial.time_seconds) == len(trial.vertical_force_n_per_kg) == TRACE_NODE_COUNT == 65
        )
        assert trial.time_seconds[0] == 0.0
        assert trial.time_seconds[-1] == pytest.approx(trial.concentric_duration_seconds)
        assert trial.vertical_force_n_per_kg[0] == pytest.approx(9.80665)
        assert trial.vertical_force_n_per_kg[-1] == pytest.approx(9.80665)
        assert trial.concentric_duration_seconds == pytest.approx(
            trial.net_impulse_m_per_s / (trial.mean_force_n_per_kg - 9.80665)
        )
        assert trial.net_impulse_m_per_s == pytest.approx(
            compute_net_impulse(trial.mean_force_n_per_kg, trial.concentric_duration_seconds),
            abs=2e-14,
        )
        shape = sin(pi / 64)
        normalized_shape = (trial.vertical_force_n_per_kg[1] - 9.80665) / (
            trial.mean_force_n_per_kg - 9.80665
        )
        assert normalized_shape == pytest.approx(shape / (2 / pi), abs=2e-3)
        assert (
            CONCENTRIC_DURATION_SUPPORT_SECONDS[0]
            <= trial.concentric_duration_seconds
            <= CONCENTRIC_DURATION_SUPPORT_SECONDS[1]
        )
    assert assessment.force_mean == pytest.approx(
        sum(t.mean_force_n_per_kg for t in assessment.trials) / 3
    )
    assert assessment.impulse_mean == pytest.approx(
        sum(t.net_impulse_m_per_s for t in assessment.trials) / 3
    )

    lower, upper = CONCENTRIC_DURATION_SUPPORT_SECONDS
    assert realize_concentric_trial(
        20.0, (20.0 - 9.80665) * lower
    ).concentric_duration_seconds == pytest.approx(lower)
    assert realize_concentric_trial(
        20.0, (20.0 - 9.80665) * upper
    ).concentric_duration_seconds == pytest.approx(upper)
    with pytest.raises(ValueError, match="escaped support"):
        realize_concentric_trial(20.0, (20.0 - 9.80665) * (lower - 1e-5))
    assert PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION.force_impulse_relationship is not None


def test_phase_consistent_depth_only_perturbation_does_not_change_mechanics() -> None:
    streams = KeyedRandomStreams("o04-depth-invariance", "same-assessment")
    shallow_depth, deep_depth = 0.15, 0.45
    shallow = measure_phase_consistent_assessment(
        24.0, 3.0, streams, assessment_key="criterion:H24"
    )
    deep = measure_phase_consistent_assessment(24.0, 3.0, streams, assessment_key="criterion:H24")
    assert shallow_depth != deep_depth
    assert shallow == deep
    assert "depth" not in measure_phase_consistent_assessment.__annotations__
    assert "depth_m" not in measure_phase_consistent_assessment.__annotations__


def test_single_exposure_generation_has_one_baseline_one_exposure_four_priors_and_six_targets() -> (
    None
):
    record = generate_episode(
        benchmark_name="phase_consistent_post_exposure_recovery",
        split="train",
        camp_index=0,
        participant_index=0,
    )
    assert BASELINE_PRE_EXPOSURE_HOURS == 2.0
    assert CURRENT_EXPOSURE_TIME_HOURS == 0.0
    assert CURRENT_EPISODE_EXPOSURES == (0.0,)
    assert NO_ADDITIONAL_EXPOSURE_THROUGH_H72
    assert len(record.prior_episodes) == PRIOR_COMPLETE_EPISODES == 4
    assert tuple(horizon for horizon, _force, _impulse in record.current.innovations) == tuple(
        horizon for horizon, _ in HORIZONS
    )
    assert len(record.current.innovations) * TARGETS_PER_ROW == 6
    assert record.current.exposure is not None
    assert len(record.current.exposure.as_dict()) == 8
    rows = project_episode(record)
    assert len(rows) == 3
    assert all(
        row[TARGET_FIELDS[0]] == record.current.innovation(row["horizon"], "force") for row in rows
    )
    assert all(
        row[TARGET_FIELDS[1]] == record.current.innovation(row["horizon"], "impulse")
        for row in rows
    )
    for prior in record.prior_episodes:
        assert tuple(horizon for horizon, _force, _impulse in prior.innovations) == tuple(
            horizon for horizon, _ in HORIZONS
        )

    correlated = generate_episode(
        benchmark_name="correlated_exposure_recovery",
        split="validation",
        camp_index=0,
        participant_index=0,
    )
    assert len(correlated.prior_episodes) == 4
    assert correlated.current.exposure.archetype_index in range(4)
    assert "archetype_index" not in correlated.current.exposure.as_dict()
    assert len(project_episode(correlated)) == 3


def test_82_field_schema_block_geometry_keys_and_no_future_label_leakage() -> None:
    assert len(PREDICTOR_FIELDS) == 82
    assert PREDICTOR_BLOCK_GEOMETRY == (1, 3, 2, 8, (17, 17, 17, 17))
    assert len(ROW_KEY_FIELDS) == 3
    assert len(TARGET_FIELDS) == 2
    assert TARGET_UNITS == {
        TARGET_FIELDS[0]: "N/kg",
        TARGET_FIELDS[1]: "m/s",
    }
    assert PREDICTOR_FIELDS[:1] == ("horizon",)
    assert PREDICTOR_FIELDS[1:4] == BASELINE_FIELDS
    assert PREDICTOR_FIELDS[4:6] == PARTICIPANT_FIELDS
    assert PREDICTOR_FIELDS[6:14] == tuple(f"index_exposure.{field}" for field in EXPOSURE_FIELDS)
    for prior_index in range(4):
        block = tuple(
            field
            for field in PREDICTOR_FIELDS
            if field.startswith(f"prior_episode[{prior_index}].")
        )
        assert len(block) == 17
        assert block[:3] == tuple(
            f"prior_episode[{prior_index}].{field}" for field in BASELINE_FIELDS
        )
        assert block[3:11] == tuple(
            f"prior_episode[{prior_index}].exposure.{field}" for field in EXPOSURE_FIELDS
        )
        assert (
            len(
                [
                    field
                    for field in block
                    if ".H24." in field or ".H48." in field or ".H72." in field
                ]
            )
            == 6
        )
    assert not set(TARGET_FIELDS).intersection(PREDICTOR_FIELDS)
    assert not any(
        field.startswith("current.") or field.startswith("label.") for field in PREDICTOR_FIELDS
    )

    row = project_episode(
        generate_episode(
            benchmark_name="preliminary_post_exposure_recovery",
            split="validation",
            camp_index=0,
            participant_index=0,
        )
    )[0]
    assert tuple(row) == (*ROW_KEY_FIELDS, *PREDICTOR_FIELDS, *TARGET_FIELDS)
    assert len(set(row).intersection(ROW_KEY_FIELDS)) == 3
    assert len(set(row).intersection(TARGET_FIELDS)) == 2
    assert not set(ROW_KEY_FIELDS).intersection(PREDICTOR_FIELDS)


def test_named_dataset_geometry_exact_split_membership_and_reference_hashes() -> None:
    expected = {
        "train": (96, 24000, 24000, 72000),
        "validation": (16, 4000, 4000, 12000),
    }
    for _dataset in ("preliminary", "phase_consistent", "correlated"):
        assert {
            split: (geometry.camps, geometry.participants, geometry.episodes, geometry.rows)
            for split, geometry in SPLIT_GEOMETRY.items()
        } == expected
    train_members = list(iter_public_members("train"))
    validation_members = list(iter_public_members("validation"))
    assert len(train_members) == 24000
    assert len(validation_members) == 4000
    assert train_members[:2] == [(0, 0), (0, 1)]
    assert train_members[-1] == (95, 249)
    assert validation_members[:2] == [(0, 0), (0, 1)]
    assert validation_members[-1] == (15, 249)
    assert ROW_ORDERING_STATUS is Status.UNKNOWN
    assert REFERENCE_DATASET_HASHES["preliminary"] == (
        "3b15c95e0c3401f81b073ecd7133987c0220811a7c8876211dcc5f7a139d9471",
        "293d20551375c893577789c937ad6b86b2cf613f0e32caa8f3e2eab50a2038b4",
    )
    assert REFERENCE_DATASET_HASHES["phase_consistent"] == (
        "c3a42297338a84e0dc9300a3d64100528c3e6d153ad6af6bd0837d0ecae27a4d",
        "b0db78f167cec78fe49992f71da187e2544c2c383adc2e9f1be37f1a577778f3",
    )
    assert REFERENCE_DATASET_HASHES["correlated"] == (
        "30f6ba1371908fde231b2f81ba989ccb7a141e1b4e19fe8c1f205b2d2b1a26cb",
        "018aa9885b7d9264170f0a413b815f4df6e5acbe3b9e8e10f3b99d9f0b979555",
    )
    train_camps = {
        KeyedRandomStreams("lcmj-v2", PUBLIC_ROOT_SEED, "train", "camp", index).opaque_key(
            "camp", "group"
        )
        for index in range(96)
    }
    validation_camps = {
        KeyedRandomStreams("lcmj-v2", PUBLIC_ROOT_SEED, "validation", "camp", index).opaque_key(
            "camp", "group"
        )
        for index in range(16)
    }
    assert len(train_camps) == 96 and len(validation_camps) == 16
    assert not train_camps.intersection(validation_camps)
    train_participants = {
        KeyedRandomStreams("lcmj-v2", PUBLIC_ROOT_SEED, "train", "camp", camp_index)
        .child("participant", participant_index)
        .opaque_key("participant", "group")
        for camp_index in range(96)
        for participant_index in range(250)
    }
    validation_participants = {
        KeyedRandomStreams("lcmj-v2", PUBLIC_ROOT_SEED, "validation", "camp", camp_index)
        .child("participant", participant_index)
        .opaque_key("participant", "group")
        for camp_index in range(16)
        for participant_index in range(250)
    }
    assert len(train_participants) == 24000
    assert len(validation_participants) == 4000
    assert not train_participants.intersection(validation_participants)


def test_correlated_exact_four_factor_covariance_archetypes_and_mixture_vectors() -> None:
    assert LATENT_FACTOR_AXES == ("volume", "speed", "change", "internal")
    assert tuple(ExposureArchetype) == (
        ExposureArchetype.LOW_DEMAND,
        ExposureArchetype.HIGH_SPEED_MODERATE,
        ExposureArchetype.HIGH_VOLUME_MODERATE,
        ExposureArchetype.SPEED_CHANGE_NEUROMUSCULAR,
    )
    assert CORRELATED_SOURCE_ARCHETYPE_NAMES == (
        "LOW_DEMAND",
        "HIGH_SPEED_MODERATE",
        "MATCH_HIGH_DEMAND",
        "SPEED_CHANGE_NEUROMUSCULAR",
    )
    assert CORRELATED_EXPOSURE_PARAMETERS.factor_sd == 0.60
    corr = np.asarray(CORRELATED_EXPOSURE_PARAMETERS.factor_correlation)
    chol = np.asarray(CORRELATED_EXPOSURE_PARAMETERS.factor_cholesky)
    assert np.allclose(chol @ chol.T, corr, rtol=0.0, atol=2e-15)
    assert np.allclose(
        CORRELATED_EXPOSURE_PARAMETERS.factor_covariance,
        0.60**2 * corr,
        rtol=0.0,
        atol=1e-15,
    )
    assert np.all(np.linalg.eigvalsh(corr) > 0.0)
    assert CORRELATED_EXPOSURE_PARAMETERS.archetype_means == (
        (-1.00, -1.00, -1.00, -0.80),
        (-0.30, 1.20, -0.40, 0.20),
        (0.90, 0.80, 0.60, 0.80),
        (-0.30, -0.20, 1.20, 0.40),
    )
    assert CORRELATED_EXPOSURE_PARAMETERS.feature_loadings == (
        (0.90, 0.10, 0.05, 0.05),
        (0.80, 0.30, 0.05, 0.05),
        (0.05, 0.95, 0.05, 0.05),
        (0.02, 0.98, 0.02, 0.02),
        (0.15, 0.05, 0.95, 0.05),
        (0.20, 0.05, 0.90, 0.05),
        (0.20, 0.15, 0.20, 0.85),
    )
    assert CORRELATED_EXPOSURE_PARAMETERS.feature_residual_sds == (
        0.50,
        0.45,
        0.50,
        0.55,
        0.50,
        0.50,
        0.55,
    )
    assert CORRELATED_EXPOSURE_PARAMETERS.train_probabilities == (0.40, 0.30, 0.20, 0.10)
    assert CORRELATED_EXPOSURE_PARAMETERS.validation_probabilities == (0.10, 0.20, 0.45, 0.25)
    assert CORRELATED_EXPOSURE_PARAMETERS.prior_probabilities == (0.25, 0.25, 0.25, 0.25)
    assert mixture_for("train") == (0.40, 0.30, 0.20, 0.10)
    assert mixture_for("validation") == (0.10, 0.20, 0.45, 0.25)
    assert mixture_for("train", prior=True) == (0.25, 0.25, 0.25, 0.25)
    assert tuple(item.sample for item in CORRELATED_EXPOSURE_SPECIFICATION.mixtures) == (
        ExposureSample.TRAINING,
        ExposureSample.VALIDATION,
        ExposureSample.PRIOR,
    )
    assert CORRELATED_EXPOSURE_SPECIFICATION.latent_factor_axes == LATENT_FACTOR_AXES
    assert CORRELATED_EXPOSURE_SPECIFICATION.archetypes == tuple(ExposureArchetype)
    assert (
        CORRELATED_EXPOSURE_SPECIFICATION.source_archetype_names
        == CORRELATED_SOURCE_ARCHETYPE_NAMES
    )


def test_correlated_supports_prior_mixture_and_outcome_specific_response_map() -> None:
    for sample, split, prior in (
        ("train", "train", False),
        ("validation", "validation", False),
        ("prior", "train", True),
    ):
        probs = mixture_for(split, prior=prior)
        channel = "prior_episode_exposure" if prior else "current_exposure"
        for index in range(80):
            exposure = sample_correlated_exposure(
                KeyedRandomStreams("w04-support", sample, index),
                archetype_probabilities=probs,
                channel=channel,
                episode_key=f"episode-{index}",
            )
            assert exposure.archetype_index in range(4)
            assert len(normalized_load_vector(exposure)) == 7
            assert "archetype_index" not in exposure.as_dict()
            assert exposure.session_rpe_load_au == exposure.duration_min * exposure.session_rpe_cr10
            for name, (low, high) in EXPOSURE_SUPPORTS:
                assert low <= exposure.as_dict()[name] <= high
    with pytest.raises(ValueError, match="four finite values"):
        sample_correlated_exposure(
            KeyedRandomStreams("w04-bad-mixture"),
            archetype_probabilities=(0.5, 0.5, 0.5, 0.5),
        )

    assert CORRELATED_RESPONSE_BASIS_WEIGHTS == (
        (0.02, 0.68, 0.28, 0.02),
        (0.18, 0.03, 0.69, 0.10),
        (0.02, 0.63, 0.03, 0.32),
        (0.55, 0.03, 0.03, 0.39),
    )
    assert CORRELATED_RESPONSE_BASIS_INTERACTIONS == (
        (1, 2, 0.30),
        (0, 2, 0.25),
        (1, 3, 0.25),
        (0, 3, 0.30),
    )
    varied = PublicExposure(90.0, 9000.0, 1500.0, 300.0, 30, 120, 8.0, 720.0)
    zero = ResponseEffects(((0.0, 0.0), (0.0, 0.0)), ((0.0, 0.0), (0.0, 0.0)))
    no_camp = CampEffects(((0.0, 0.0), (0.0, 0.0)))
    force = response_parameters_for_exposure(
        varied, zero, no_camp, "force", world="correlated_exposure"
    )
    impulse = response_parameters_for_exposure(
        varied, zero, no_camp, "impulse", world="correlated_exposure"
    )
    assert force.fast_amplitude != impulse.fast_amplitude
    assert force.slow_amplitude != impulse.slow_amplitude
    vector = normalized_load_vector(varied)
    basis = (
        (vector[0] + vector[1]) / 2,
        (vector[2] + vector[3]) / 2,
        (vector[4] + vector[5]) / 2,
        vector[6],
    )
    for metric_index, parameters in enumerate((force, impulse)):
        amplitudes = (parameters.fast_amplitude, parameters.slow_amplitude)
        for component_index, actual_amplitude in enumerate(amplitudes):
            row_index = 2 * metric_index + component_index
            weights = CORRELATED_RESPONSE_BASIS_WEIGHTS[row_index]
            left, right, coefficient = CORRELATED_RESPONSE_BASIS_INTERACTIONS[row_index]
            score = sum(
                weight * (value - 0.5) for weight, value in zip(weights, basis, strict=True)
            )
            score += coefficient * (basis[left] * basis[right] - 0.25)
            low, high = ((0.01, 0.08), (0.0, 0.08))[component_index]
            expected_amplitude = low + (high - low) / (1 + exp(-score))
            assert actual_amplitude == pytest.approx(expected_amplitude)


def test_correlated_zero_residual_draw_replays_factor_to_primitive_mapping() -> None:
    class FixedGenerator:
        def choice(self, _size: int, *, p: np.ndarray) -> int:
            assert tuple(p) == CORRELATED_EXPOSURE_PARAMETERS.train_probabilities
            return 2

        def normal(self, size: int | None = None) -> float | np.ndarray:
            return np.zeros(size) if size is not None else 0.0

    class FixedStreams:
        def __init__(self) -> None:
            self.channels: list[str] = []

        def generator(self, channel: str, *_keys: object) -> FixedGenerator:
            self.channels.append(channel)
            return FixedGenerator()

    streams = cast(Any, FixedStreams())
    exposure = sample_correlated_exposure(
        streams, archetype_probabilities=CORRELATED_EXPOSURE_PARAMETERS.train_probabilities
    )
    parameters = CORRELATED_EXPOSURE_PARAMETERS
    loadings = np.asarray(parameters.feature_loadings)
    correlation = np.asarray(parameters.factor_correlation)
    scales = np.sqrt(
        parameters.factor_sd**2 * np.einsum("ij,jk,ik->i", loadings, correlation, loadings)
        + np.square(parameters.feature_residual_sds)
    )
    factors = np.asarray(parameters.archetype_means[2])
    uniforms = [
        0.5 * erfc(-float(loadings[i] @ factors) / (float(scales[i]) * sqrt(2.0))) for i in range(7)
    ]
    expected = {
        "duration_min": 45.0 + uniforms[0] * 75.0,
        "total_distance_m": 3000.0 + uniforms[1] * 10000.0,
        "high_speed_distance_m": uniforms[2] * 2000.0,
        "sprint_distance_m": min(uniforms[3] * 600.0, uniforms[2] * 2000.0),
        "high_intensity_accel_count": round(uniforms[4] * 150),
        "high_intensity_decel_count": round(uniforms[5] * 150),
        "session_rpe_cr10": 2.0 + uniforms[6] * 8.0,
    }
    for name, value in expected.items():
        assert exposure.as_dict()[name] == pytest.approx(value)
    assert exposure.archetype_index == 2
    assert streams.channels == [
        "exposure_archetype_assignment",
        "exposure_factor_residual",
        *("exposure_feature_residual" for _ in range(7)),
    ]


def test_rng_exact_construction_does_not_upgrade_algorithm_or_state_claims() -> None:
    assert RNG_VERSION == "lcmj-v2-keyed-rng-1.0.0"
    assert PUBLIC_ROOT_SEED == "ALI-494-LCMJ-V2-PUBLIC-001"
    streams = KeyedRandomStreams("lcmj-v2", "root", "train", "camp", 0)
    identity = ("lcmj-v2", "root", "train", "camp", 0)
    channel = "trial_noise"
    keys = ("assessment", "force", 0)
    payload = json.dumps(
        [RNG_VERSION, identity, channel, keys],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(b"lcmj-v2-rng\0" + payload).digest()[:16], "big")
    expected = np.random.default_rng(seed).normal()
    assert streams.generator(channel, *keys).normal() == expected
    unrelated = streams.generator(channel, "assessment", "force", 0).normal()
    _ = streams.generator("exposure_factor_residual", "current_exposure", "current").normal(size=50)
    assert streams.generator(channel, "assessment", "force", 0).normal() == unrelated
    assert KeyedRandomStreams("same").opaque_key("query", "H24") == KeyedRandomStreams(
        "same"
    ).opaque_key("query", "H24")
    for boundary in EXACTNESS_BOUNDARIES.values():
        assert boundary.rng_algorithm is Status.PARTIAL
        assert boundary.rng_state is Status.PARTIAL
        assert boundary.seed_authority is Status.EXACT
        assert boundary.rng_stream_construction is Status.EXACT
        assert boundary.rng_draw_order is Status.EXACT
        assert boundary.rng_substream_strategy is Status.EXACT
        assert boundary.dataset_hash is Status.PARTIAL
        assert boundary.serialization is Status.SEMANTICALLY_EQUIVALENT
        assert boundary.evaluation is Status.PARTIAL
        assert boundary.production_scorer == "UNIMPLEMENTED"
        assert "research-only" in boundary.research_metric
    assert ROW_ORDERING_STATUS is Status.UNKNOWN
    assert assessment_error_sd_fraction("force") == pytest.approx(
        (0.0025**2 + 0.0060**2 / 3) ** 0.5
    )
    assert assessment_error_sd_fraction("impulse") == pytest.approx(
        (0.0035**2 + 0.0090**2 / 3) ** 0.5
    )
    discrepancy = draw_episode_discrepancy(
        KeyedRandomStreams("discrepancy"), "current", channel="current_discrepancy"
    )
    assert discrepancy == draw_episode_discrepancy(
        KeyedRandomStreams("discrepancy"), "current", channel="current_discrepancy"
    )
    assert set(discrepancy) == {horizon for horizon, _ in HORIZONS}
    assert all(
        0.005 <= abs(value) <= 0.015
        for per_horizon in discrepancy.values()
        for value in per_horizon.values()
    )


def test_exact_split_assignment_does_not_promote_hashes_or_observation_statuses() -> None:
    assert all(item.split_assignment is Status.EXACT for item in EXACTNESS_BOUNDARIES.values())
    assert all(item.dataset_hash is Status.PARTIAL for item in EXACTNESS_BOUNDARIES.values())
    assert EXACTNESS_BOUNDARIES["preliminary_post_exposure_recovery"].observation is Status.PARTIAL
    assert (
        EXACTNESS_BOUNDARIES["phase_consistent_post_exposure_recovery"].observation is Status.EXACT
    )
    assert EXACTNESS_BOUNDARIES["correlated_exposure_recovery"].observation is Status.EXACT
    assert all(
        not item.production_scorer == "IMPLEMENTED" for item in EXACTNESS_BOUNDARIES.values()
    )
    assert all(
        item.model_configuration is Status.DEFERRED_OUT_OF_SCOPE
        and item.historical_result is Status.DEFERRED_OUT_OF_SCOPE
        for item in EXACTNESS_BOUNDARIES.values()
    )
