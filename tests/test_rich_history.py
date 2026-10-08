"""SP03 source closure, public geometry, R02, O02, and E02 contracts."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from cmj_recovery_dynamics.contracts import OutcomeVariable
from cmj_recovery_dynamics.metrics.scoring import (
    RICH_HISTORY_CELLS,
    CellValues,
    MetricInputError,
    RichHistoryAssessment,
    rich_history_stratum,
)
from cmj_recovery_dynamics.observations.rich_monitoring import (
    RICH_MONITORING_OBSERVATION,
    AssessmentValidity,
    MeasurementModel,
    MonitoringAssessment,
    observe_assessments,
    observe_target,
    protocol_baseline,
)
from cmj_recovery_dynamics.reproduction import rich_history
from cmj_recovery_dynamics.reproduction.contracts import (
    CalibrationReferenceStatus,
    MaterializationState,
    ReproductionDimension,
    ReproductionStatus,
    SplitRole,
)
from cmj_recovery_dynamics.reproduction.registry import get_reproduction_contract
from cmj_recovery_dynamics.reproduction.rich_history import (
    ALI490_RNG_CHANNELIZATION_COMMIT,
    CATEGORICAL_FIELDS,
    D04_DATA_PRODUCER_COMMIT,
    D04_DATA_PRODUCER_REPOSITORY_TREE,
    D04_DATA_PRODUCER_TASK_TREE,
    D04_MANIFEST_BLOB_OID,
    D04_TRAIN_PARQUET_BLOB_OID,
    D04_VALIDATION_PARQUET_BLOB_OID,
    DEFAULT,
    F2_LEVELS,
    F3_LEVELS,
    HISTORICAL_HIDDEN_DESIGN,
    HORIZON_TARGET_COLUMNS,
    PUBLIC_GROUPING_COLUMNS,
    PUBLIC_SPLITS,
    R02_FIELD_BLOCKS,
    R02_FIELD_NAMES,
    RICH_HISTORY_REPRODUCTION_METADATA,
    SCHEMA_DIGEST,
    SP03_SOURCE_CLOSURE,
    SP03_SOURCE_TREE,
    STREAM_CHANNELS,
    CampRegime,
    CampSchedule,
    GroupingMetadata,
    PublicSplitName,
    RandomStreams,
    admitted_horizons,
    draw_participants,
    draw_schedule,
    flatten_r02_record,
    iter_rich_history_public_split,
    parameterize_participants,
    project_public_record,
    public_grouping_keys,
    rich_history_native_progress,
)


def test_selected_source_closure_and_m21_claim_boundary() -> None:
    assert SP03_SOURCE_TREE == "e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b"
    assert D04_DATA_PRODUCER_COMMIT == "6947771c8567438bba4cea8b5bb28d8f7992b307"
    assert D04_DATA_PRODUCER_REPOSITORY_TREE == "c3c65d118cab0a368aafc7c1681a5660cd039bee"
    assert D04_DATA_PRODUCER_TASK_TREE == "88e0cf68aa7fda864505a2a7e353e0487187919e"
    assert D04_DATA_PRODUCER_TASK_TREE != SP03_SOURCE_TREE
    assert D04_MANIFEST_BLOB_OID == "03864b433e678e582da3d50d66468443a77cba71"
    assert D04_TRAIN_PARQUET_BLOB_OID == "8b789399f8b40feef3a02aff98eb9a86d193f335"
    assert D04_VALIDATION_PARQUET_BLOB_OID == "d2987e1e349986319eeb01cc46972e0bae9c158c"
    assert ALI490_RNG_CHANNELIZATION_COMMIT == "ad5e48a1dc9c1fd1e27ecd314940a9be1b4fd50a"
    required_paths = {
        "environment/Dockerfile",
        "data_generation/src/lcmj_v3/core.py",
        "data_generation/src/lcmj_v3/families.py",
        "data_generation/src/lcmj_v3/measurement.py",
        "data_generation/src/lcmj_v3/params.py",
        "data_generation/src/lcmj_v3/projection.py",
        "data_generation/src/lcmj_v3/rng.py",
        "data_generation/src/lcmj_v3/schedule.py",
        "data_generation/src/lcmj_v3/splits.py",
        "data_generation/authority/parameters_v3.json",
        "data_generation/tests/test_ali488_source_repair.py",
        "data_generation/tests/test_ali490_rng_channels.py",
        "data_generation/tests/test_pipeline_v3.py",
        "data/canonical_v3.py",
        "data/public/manifest.json",
    }
    assert set(SP03_SOURCE_CLOSURE) == required_paths
    assert all(not Path(path).is_absolute() for path in SP03_SOURCE_CLOSURE)

    source_path = rich_history.__file__
    assert source_path is not None
    source = Path(source_path)
    syntax_tree = ast.parse(source.read_text())
    imported_modules: set[str] = set()
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
    prohibited = (
        "historical_aliases",
        "predictive_headroom",
        "headroom_proof",
        "strong_mlp",
        "strong_hgb",
        "reference_S",
        "gpu",
    )
    assert not any(any(term in module for term in prohibited) for module in imported_modules)
    runtime_check = (
        "import sys; "
        "import cmj_recovery_dynamics.reproduction.rich_history; "
        "blocked = ('cmj_recovery_dynamics.provenance.historical_aliases', "
        "'cmj_recovery_dynamics.metrics.provenance', "
        "'cmj_recovery_dynamics.metrics.compatibility', "
        "'cmj_recovery_dynamics.metrics.catalog', "
        "'cmj_recovery_dynamics.studies.predictive_headroom', "
        "'cmj_recovery_dynamics.reproduction.camp_history', "
        "'cmj_recovery_dynamics.benchmarks.preseason_camp_recovery', "
        "'cmj_recovery_dynamics.lineage.registry', "
        "'cmj_recovery_dynamics.lineage.models', "
        "'cmj_recovery_dynamics.lineage.results'); "
        "assert not set(blocked).intersection(sys.modules)"
    )
    subprocess.run([sys.executable, "-c", runtime_check], check=True, capture_output=True)

    contract = get_reproduction_contract("rich_history_camp_recovery")
    expected = {
        ReproductionDimension.WORLD_LAW: ReproductionStatus.EXACT,
        ReproductionDimension.COMPLETE_GENERATOR: ReproductionStatus.SEMANTICALLY_EQUIVALENT,
        ReproductionDimension.RNG_ALGORITHM: ReproductionStatus.PARTIAL,
        ReproductionDimension.RNG_STATE: ReproductionStatus.PARTIAL,
        ReproductionDimension.SEED_AUTHORITY: ReproductionStatus.EXACT,
        ReproductionDimension.RNG_STREAM_CONSTRUCTION: ReproductionStatus.EXACT,
        ReproductionDimension.RNG_DRAW_ORDER: ReproductionStatus.EXACT,
        ReproductionDimension.RNG_SUBSTREAM_STRATEGY: ReproductionStatus.EXACT,
        ReproductionDimension.OBSERVATION: ReproductionStatus.EXACT,
        ReproductionDimension.SCHEMA: ReproductionStatus.EXACT,
        ReproductionDimension.SPLIT_ASSIGNMENT: ReproductionStatus.PARTIAL,
        ReproductionDimension.ROW_ORDERING: ReproductionStatus.UNKNOWN,
        ReproductionDimension.SERIALIZATION: ReproductionStatus.SEMANTICALLY_EQUIVALENT,
        ReproductionDimension.DATASET_HASH: ReproductionStatus.PARTIAL,
        ReproductionDimension.EVALUATION: ReproductionStatus.PARTIAL,
        ReproductionDimension.MODEL_CONFIGURATION: ReproductionStatus.DEFERRED_OUT_OF_SCOPE,
        ReproductionDimension.HISTORICAL_RESULT: ReproductionStatus.DEFERRED_OUT_OF_SCOPE,
    }
    assert {claim.dimension: claim.status for claim in contract.claims} == expected
    assert "not RNG stream keys" in contract.randomness.substream_strategy
    assert "simulate-camp" in contract.randomness.stream_construction
    assert "local participant index" in contract.randomness.stream_construction
    assert RICH_HISTORY_REPRODUCTION_METADATA.split_assignment == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_rng_algorithm == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_rng_state == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.generator_claim == "SEMANTICALLY_EQUIVALENT"
    assert RICH_HISTORY_REPRODUCTION_METADATA.source_tree == SP03_SOURCE_TREE
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_data_producer_commit == D04_DATA_PRODUCER_COMMIT
    assert (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_data_producer_task_tree
        == D04_DATA_PRODUCER_TASK_TREE
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_manifest_blob_oid == D04_MANIFEST_BLOB_OID
    assert (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_train_parquet_blob_oid == D04_TRAIN_PARQUET_BLOB_OID
    )
    assert (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_validation_parquet_blob_oid
        == D04_VALIDATION_PARQUET_BLOB_OID
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_seed_construction == (
        "roots l05-public-train-v3/l05-public-validation-v3; SHA-256 of compact JSON string "
        "parts, first 8 bytes big-endian; np.random.default_rng(seed)"
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_rng_topology == (
        "one shared Generator per camp, consumed sequentially through horizon admission"
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_horizon_presence_draws == (
        "random(n) < 0.15, then integers(0, 2, n), from that same camp Generator"
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_runtime_authority == (
        "Dockerfile base tag runtime-ml-core-py313-local only; exact Python build, NumPy version, "
        "and BitGenerator unbound"
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.later_rng_channelization_commit == (
        ALI490_RNG_CHANNELIZATION_COMMIT
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.row_ordering == "UNKNOWN"
    assert RICH_HISTORY_REPRODUCTION_METADATA.serialization == "SEMANTICALLY_EQUIVALENT"
    assert RICH_HISTORY_REPRODUCTION_METADATA.dataset_hash == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_calibration_reference == "UNAVAILABLE"
    split_claim = contract.claim(ReproductionDimension.SPLIT_ASSIGNMENT)
    assert split_claim.status is ReproductionStatus.PARTIAL
    assert D04_DATA_PRODUCER_COMMIT in split_claim.rationale
    assert SP03_SOURCE_TREE in split_claim.rationale
    assert "named child streams" in split_claim.rationale
    assert "not historical runtime authority" in split_claim.rationale
    assert contract.evaluation.production_scorer == "rich_history_24_cell_normalized_rmse_score"
    assert (
        contract.evaluation.calibration_reference_status
        is CalibrationReferenceStatus.LOCKED_NOT_PUBLIC
    )
    assert contract.evaluation.calibration_reference_value is None

    hidden = next(split for split in contract.splits if split.role is SplitRole.HIDDEN_TEST)
    assert hidden.materialization_state is MaterializationState.NOT_RECOVERED
    assert hidden.rows is None and hidden.planned_rows is None and hidden.reference_hash is None
    assert HISTORICAL_HIDDEN_DESIGN.participants == 1152
    assert HISTORICAL_HIDDEN_DESIGN.camps == 144
    assert HISTORICAL_HIDDEN_DESIGN.origins == 2304
    assert HISTORICAL_HIDDEN_DESIGN.materialization == "NOT_RECOVERED"
    assert not hasattr(HISTORICAL_HIDDEN_DESIGN, "rows")
    assert not hasattr(HISTORICAL_HIDDEN_DESIGN, "sha256")
    public_splits = tuple(
        split for split in contract.splits if split.role is not SplitRole.HIDDEN_TEST
    )
    assert all(split.assignment_status is ReproductionStatus.PARTIAL for split in public_splits)
    assert all(
        any(
            "horizon-presence" in item or "query membership" in item
            for item in split.missing_assignment
        )
        for split in public_splits
    )


def test_r02_semantic_fields_and_source_blocks_are_exact() -> None:
    assert DEFAULT.schema.horizons == ("H72", "D7")
    assert DEFAULT.schema.target_windows == ((66.0, 78.0), (156.0, 180.0))
    assert HORIZON_TARGET_COLUMNS == (
        "label.relative_mean_concentric_force_innovation",
        "label.relative_concentric_net_impulse_innovation",
    )
    assert len(R02_FIELD_NAMES) == 135
    assert len(set(R02_FIELD_NAMES)) == 135
    assert tuple(field for block in R02_FIELD_BLOCKS for field in block.fields) == R02_FIELD_NAMES
    assert tuple(block.name for block in R02_FIELD_BLOCKS) == (
        "query_and_baseline",
        "participant_context",
        "assessment_count",
        "assessment_slots",
        "exposure_count",
        "prior_exposure_slots",
        "index_exposure",
        "known_plan_count",
        "known_plan_slots",
    )
    assert tuple(len(block.fields) for block in R02_FIELD_BLOCKS) == (6, 3, 1, 84, 1, 24, 3, 1, 12)
    assert R02_FIELD_NAMES[:6] == (
        "horizon",
        "target_time_hours",
        "target_window_low",
        "target_window_high",
        "baseline_force",
        "baseline_impulse",
    )
    assert "history_assessment[13].validity_state" in CATEGORICAL_FIELDS
    assert "history_exposure[5].event_kind" in CATEGORICAL_FIELDS
    assert "known_plan[2].event_kind" in CATEGORICAL_FIELDS
    assert not set(PUBLIC_GROUPING_COLUMNS).intersection(R02_FIELD_NAMES)
    assert not set(HORIZON_TARGET_COLUMNS).intersection(R02_FIELD_NAMES)
    assert SCHEMA_DIGEST == "ea8cd5c370c894b0b3175a2b263e405f490a46421517d4f3130cc8cc53d0b2ba"


def test_r02_missing_slots_and_nested_projection_keep_keys_and_labels_separate() -> None:
    row = flatten_r02_record(
        {
            "horizon": "H72",
            "target_time_hours": 72.0,
            "target_window_hours": {"low": 66.0, "high": 78.0},
            "baseline": {
                "relative_mean_concentric_force": 25.0,
                "relative_concentric_net_impulse": 2.7,
            },
            "public_features": {
                "participant": {
                    "training_age_years": 4.0,
                    "strength_index": -0.2,
                    "bouts_prior_4wk": 3.0,
                },
                "history_assessments": [
                    {
                        "time_from_origin_hours": -48.0,
                        "relative_mean_concentric_force": 24.5,
                        "relative_concentric_net_impulse": 2.6,
                        "depth_m": 0.31,
                        "n_trials": 2,
                        "validity_state": "valid",
                    }
                ],
                "history_exposures": [
                    {
                        "time_from_origin_hours": -72.0,
                        "event_kind": "match",
                        "duration_minutes": 100.0,
                        "c_context": 1.0,
                    }
                ],
                "index_exposure": {
                    "event_kind": "match",
                    "duration_minutes": 100.0,
                    "c_context": 1.0,
                },
                "known_plan": [],
            },
        }
    )
    assert len(row) == 135
    assert row["n_assessments"] == 1.0
    assert row["history_assessment[1].validity_state"] == "<MISSING>"
    assert math.isnan(cast(float, row["history_assessment[1].time_from_origin_hours"]))
    assert row["n_history_exposures"] == 1.0
    assert row["n_plan"] == 0.0
    assert row["known_plan[0].event_kind"] == "<MISSING>"


def test_o02_contract_marks_target_depth_and_latent_state_hidden() -> None:
    observation = RICH_MONITORING_OBSERVATION
    assert observation.forbidden_variables.status.value == "specified"
    assert "target-time depth" in observation.hidden_variables.variables
    assert "future outcomes" in observation.hidden_variables.variables
    assert "grouping/query keys as predictors" in observation.forbidden_variables.variables
    assert "five valid standardized-depth trials" in observation.measurement_construction
    assert "does not change force or impulse" in observation.measurement_construction


def test_rng_hierarchy_and_new_numpy_runtime_metadata_stay_separate() -> None:
    assert PUBLIC_SPLITS["public_train"].root_seed == "l05-public-train-v3"
    assert PUBLIC_SPLITS["public_validation"].root_seed == "l05-public-validation-v3"
    assert PUBLIC_SPLITS["public_train"].key_namespace == "public-v3"
    assert PUBLIC_SPLITS["public_validation"].key_namespace == "public-v3"
    assert PUBLIC_SPLITS["public_train"].camps == 512
    assert PUBLIC_SPLITS["public_validation"].camps == 128
    assert len(STREAM_CHANNELS) == 36 and len(set(STREAM_CHANNELS)) == 36

    first = RandomStreams("l05-public-train-v3", "public_train", "camp", 7)
    repeat = RandomStreams("l05-public-train-v3", "public_train", "camp", 7)
    assert np.array_equal(
        first.generator("exposure_count").random(16),
        repeat.generator("exposure_count").random(16),
    )
    assert first.root_seed == repeat.root_seed
    with pytest.raises(KeyError, match="unregistered RNG channel"):
        first.generator("not-a-source-channel")
    assert RICH_HISTORY_REPRODUCTION_METADATA.oss_numpy_version == np.__version__
    assert (
        RICH_HISTORY_REPRODUCTION_METADATA.oss_default_rng_bit_generator
        == np.random.default_rng(0).bit_generator.__class__.__name__
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_rng_algorithm == "PARTIAL"


def test_participant_kinetics_preserve_source_correlations_and_clips() -> None:
    errors = np.asarray([[1.0, -2.0, 0.5, 1.5, -1.0, 2.0, -0.5]])
    traits = parameterize_participants(
        np.asarray([8.0]),
        np.asarray([0.25]),
        1.15,
        errors,
        preferred_depth=np.asarray([0.32]),
        bouts_prior_4wk=np.asarray([4.0]),
    )
    assert traits.level_force[0] == pytest.approx(25 + 1.5 * 0.25 + 3.5 * 1.0)
    assert traits.level_impulse[0] == pytest.approx(
        2.7 + 0.12 * 0.25 + 0.25 * (0.6 * 1.0 + 0.8 * -2.0)
    )
    amp_force = 1.25 * math.exp(0.15 * 0.25 + 0.30 * 1.15 * 0.5)
    assert traits.amplitude_force[0] == pytest.approx(amp_force)
    assert traits.amplitude_impulse[0] == pytest.approx(amp_force * (0.075 + 0.015 * 1.5))
    assert 1.5 <= traits.response_ratio[0] <= 5.0
    assert 36.0 <= traits.tau_fast[0] <= 110.0
    assert 100.0 <= traits.tau_slow[0] <= 260.0
    assert traits.preferred_depth[0] == 0.32
    assert traits.bouts_prior_4wk[0] == 4.0
    sampled = draw_participants(RandomStreams("participant-bounds"), 32, 1.15)
    assert np.all((sampled.training_age >= 1.0) & (sampled.training_age <= 12.0))
    assert np.all((sampled.bouts_prior_4wk >= 0) & (sampled.bouts_prior_4wk <= 8))
    assert np.all(sampled.bouts_prior_4wk == np.floor(sampled.bouts_prior_4wk))
    assert np.all((sampled.preferred_depth >= 0.20) & (sampled.preferred_depth <= 0.40))

    extreme = parameterize_participants(
        np.asarray([1.0, 12.0]),
        np.asarray([-1.0, 1.0]),
        1.15,
        np.asarray(
            [
                [0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0],
                [0.0, 0.0, -100.0, -100.0, -100.0, -100.0, -100.0],
            ]
        ),
    )
    assert np.all((extreme.response_ratio >= 1.5) & (extreme.response_ratio <= 5.0))
    assert np.all((extreme.tau_fast >= 36.0) & (extreme.tau_fast <= 110.0))
    assert np.all((extreme.tau_slow >= 100.0) & (extreme.tau_slow <= 260.0))


def test_o02_baseline_uses_latest_two_valid_qualifying_assessments() -> None:
    boundary_pair = (
        MonitoringAssessment(-240.0, 10.0, 1.0, 0.25, 2, AssessmentValidity.VALID),
        MonitoringAssessment(-24.0, 30.0, 3.0, 0.30, 2, AssessmentValidity.VALID),
    )
    at_inclusive_bounds = protocol_baseline(boundary_pair, (-300.0, -84.0))
    assert at_inclusive_bounds is not None
    assert at_inclusive_bounds.force == 20.0 and at_inclusive_bounds.impulse == 2.0

    assessments = (
        MonitoringAssessment(-240.0, 10.0, 1.0, 0.25, 2, AssessmentValidity.VALID),
        MonitoringAssessment(-170.0, 100.0, 10.0, 0.27, 1, AssessmentValidity.INVALID),
        MonitoringAssessment(-120.0, 20.0, 2.0, 0.28, 2, AssessmentValidity.VALID),
        MonitoringAssessment(-80.0, 30.0, 3.0, 0.29, 3, AssessmentValidity.VALID),
        MonitoringAssessment(-24.0, 200.0, 20.0, 0.30, 2, AssessmentValidity.VALID),
    )
    baseline = protocol_baseline(assessments, (-300.0, -84.0))
    assert baseline is not None
    assert baseline.force == 110.0
    assert baseline.impulse == 11.0

    assert protocol_baseline(assessments[:1], (-300.0, -84.0)) is None
    too_early = (MonitoringAssessment(-24.0, 1.0, 1.0, 0.3, 2, AssessmentValidity.VALID),)
    assert protocol_baseline(too_early, (-48.0,)) is None
    exact_gap = (
        MonitoringAssessment(-84.0, 2.0, 0.2, 0.3, 2, AssessmentValidity.VALID),
        MonitoringAssessment(-24.0, 4.0, 0.4, 0.3, 2, AssessmentValidity.VALID),
    )
    exact = protocol_baseline(exact_gap, (-144.0, -84.0))
    assert exact is not None and exact.force == 3.0 and exact.impulse == pytest.approx(0.3)
    missing_pair = (
        MonitoringAssessment(-80.0, None, None, 0.3, 2, AssessmentValidity.MISSING_VALUES),
        MonitoringAssessment(-24.0, 4.0, 0.4, 0.3, 2, AssessmentValidity.VALID),
    )
    assert protocol_baseline(missing_pair, (-144.0, -84.0)) is None


def test_o02_monitoring_invalid_missing_depth_and_target_trial_behavior() -> None:
    present = np.asarray([[True, True], [True, False]])
    true_force = np.full((2, 2), 25.0)
    true_impulse = np.full((2, 2), 2.7)
    trials = np.asarray([[1, 3], [2, 0]])
    depths = np.asarray([0.22, 0.38])

    def measured(depth: np.ndarray, model: MeasurementModel, seed: int) -> Any:
        streams = RandomStreams("observation-test", seed)
        return observe_assessments(
            true_force,
            true_impulse,
            depth,
            present,
            trials,
            model,
            depth_rng=streams.generator("history_assessment_depth_context"),
            force_rng=streams.generator("history_assessment_force_noise"),
            impulse_rng=streams.generator("history_assessment_impulse_noise"),
            validity_rng=streams.generator("history_assessment_validity"),
            invalid_scale_rng=streams.generator("history_assessment_invalid_scale"),
            missing_rng=streams.generator("history_assessment_missingness"),
        )

    first = measured(depths, DEFAULT.measurement, 488101)
    second = measured(np.asarray([0.38, 0.22]), DEFAULT.measurement, 488101)
    assert np.any(first.depth[present] != second.depth[present])
    assert np.array_equal(first.force_raw, second.force_raw)
    assert np.array_equal(first.impulse_raw, second.impulse_raw)
    assert np.array_equal(first.validity, second.validity)
    assert np.isfinite(first.depth[present]).all()
    grid_values = np.asarray(first.depth[present], dtype=float) / DEFAULT.measurement.depth_grid_m
    assert np.allclose(
        grid_values,
        np.rint(grid_values),
    )
    assert set(first.validity[present]).issubset({"valid", "invalid", "missing_values"})

    invalid = measured(
        depths,
        replace(DEFAULT.measurement, invalid_rate=1.0, missing_rate=1.0),
        488102,
    )
    assert np.all(invalid.validity[present] == "invalid")
    assert not invalid.usable[present].any()
    missing = measured(
        depths,
        replace(DEFAULT.measurement, invalid_rate=0.0, missing_rate=1.0),
        488103,
    )
    assert np.all(missing.validity[present] == "missing_values")
    assert np.isnan(missing.force[present]).all() and np.isnan(missing.impulse[present]).all()

    assert DEFAULT.measurement.target_trials == 5
    target_streams_a = RandomStreams("target-measurement-test")
    target_streams_b = RandomStreams("target-measurement-test")
    target_a = observe_target(
        true_force,
        true_impulse,
        depths,
        DEFAULT.measurement,
        depth_rng=target_streams_a.generator("target_depth_context"),
        force_rng=target_streams_a.generator("target_force_noise"),
        impulse_rng=target_streams_a.generator("target_impulse_noise"),
    )
    target_b = observe_target(
        true_force,
        true_impulse,
        np.asarray([0.38, 0.22]),
        DEFAULT.measurement,
        depth_rng=target_streams_b.generator("target_depth_context"),
        force_rng=target_streams_b.generator("target_force_noise"),
        impulse_rng=target_streams_b.generator("target_impulse_noise"),
    )
    assert np.any(target_a.depth_context != target_b.depth_context)
    assert np.array_equal(target_a.force, target_b.force)
    assert np.array_equal(target_a.impulse, target_b.impulse)
    assert np.all((target_a.depth_context >= 0.15) & (target_a.depth_context <= 0.45))
    expected_streams = RandomStreams("target-measurement-test")
    expected_force = true_force + (
        expected_streams.generator("target_force_noise").normal(0.0, 1.0, (2, 2))
        * DEFAULT.measurement.trial_sd_force
        / math.sqrt(5)
    )
    assert np.array_equal(target_a.force, expected_force)


def test_camp_schedule_respects_source_geometry_and_observation_opportunities() -> None:
    regime = CampRegime(True, True, 1.0, 1.0, 0.9, (0.4, 0.6))
    schedule = draw_schedule(RandomStreams("schedule-high-quality"), 128, regime)
    parameters = DEFAULT.schedule
    assert set(np.unique(schedule.exposure_count)) <= {5, 6}
    assert np.all((schedule.window_h >= 504.0) & (schedule.window_h <= 672.0))
    assert np.all((schedule.assessment_count >= 2) & (schedule.assessment_count <= 14))
    assert np.all((schedule.plan_count >= 0) & (schedule.plan_count <= 3))

    for unit in range(len(schedule.exposure_count)):
        count = int(schedule.exposure_count[unit])
        exposures = schedule.exposure_times[unit, :count]
        assert np.all(np.diff(exposures) >= parameters.exposure_min_gap_h - 1e-9)
        assert np.all((-exposures >= 16.0) & (-exposures <= 672.0))
        assert 3 <= count <= 6
        assessments = schedule.assessment_times[unit, : int(schedule.assessment_count[unit])]
        assert np.all((-assessments >= 6.0) & (-assessments <= 672.0))
        assert np.all(np.diff(assessments) >= parameters.assess_min_gap_h - 1e-9)
        baseline_pair = schedule.baseline_opportunity_times[unit]
        assert np.all(np.isin(baseline_pair, assessments))
        for assessment_time in assessments:
            if np.any(np.isclose(assessment_time, baseline_pair)):
                continue
            assert any(
                event + 14.0 <= assessment_time <= event + 40.0
                or event + 60.0 <= assessment_time <= event + 84.0
                for event in exposures
            )
        assert baseline_pair[0] >= -240.0 and baseline_pair[1] <= -24.0
        assert baseline_pair[1] - baseline_pair[0] == pytest.approx(8.0)
        preceding = exposures[exposures < baseline_pair[0]][-1]
        assert baseline_pair[0] - preceding >= 60.0

        present_trials = schedule.assessment_trials[unit, : len(assessments)]
        allowed_trials = {2, 3}
        assert set(np.unique(present_trials)) <= allowed_trials
        plan_count = int(schedule.plan_count[unit])
        plan_times = schedule.plan_times[unit, :plan_count]
        assert np.all((plan_times >= 24.0) & (plan_times <= 160.0))
        assert np.all(np.diff(plan_times) >= 0)
        assert set(schedule.plan_kinds[unit, :plan_count]) <= {"training", "friendly"}
        assert np.all(
            (schedule.plan_execution[unit, :plan_count] >= 0.92)
            & (schedule.plan_execution[unit, :plan_count] <= 1.0)
        )
    low_quality = draw_schedule(
        RandomStreams("schedule-low-quality"),
        32,
        replace(regime, dense=False, quality_high=False, monitor_probability=0.6),
    )
    assert set(np.unique(low_quality.exposure_count)) <= {3, 4}
    assert set(np.unique(low_quality.assessment_trials[low_quality.assessment_present])) <= {
        1,
        2,
        3,
    }


def test_rng_channel_isolation_and_public_projection_do_not_leak_latents() -> None:
    identity = ("l05-public-train-v3", "public_train", "camp", 3)
    regime = CampRegime(True, True, 1.0, 1.0, 0.9, (0.4, 0.6))
    low_schedule = draw_schedule(
        RandomStreams(*identity), 16, replace(regime, monitor_probability=0.0)
    )
    high_schedule = draw_schedule(
        RandomStreams(*identity), 16, replace(regime, monitor_probability=1.0)
    )
    assert np.array_equal(low_schedule.exposure_times, high_schedule.exposure_times, equal_nan=True)
    assert np.array_equal(low_schedule.plan_times, high_schedule.plan_times, equal_nan=True)
    assert not np.array_equal(low_schedule.assessment_present, high_schedule.assessment_present)

    true_force = np.full((16, DEFAULT.schema.A_MAX), 25.0)
    true_impulse = np.full((16, DEFAULT.schema.A_MAX), 2.7)
    preferred_depth = np.linspace(0.22, 0.38, 16)
    target_force = np.full((16, 2), 25.0)
    target_impulse = np.full((16, 2), 2.7)
    low_streams = RandomStreams(*identity)
    high_streams = RandomStreams(*identity)

    def measure_history(streams: RandomStreams, schedule: CampSchedule) -> None:
        observe_assessments(
            true_force,
            true_impulse,
            preferred_depth,
            schedule.assessment_present,
            schedule.assessment_trials,
            DEFAULT.measurement,
            depth_rng=streams.generator("history_assessment_depth_context"),
            force_rng=streams.generator("history_assessment_force_noise"),
            impulse_rng=streams.generator("history_assessment_impulse_noise"),
            validity_rng=streams.generator("history_assessment_validity"),
            invalid_scale_rng=streams.generator("history_assessment_invalid_scale"),
            missing_rng=streams.generator("history_assessment_missingness"),
        )

    measure_history(low_streams, low_schedule)
    measure_history(high_streams, high_schedule)
    low_target = observe_target(
        target_force,
        target_impulse,
        preferred_depth,
        DEFAULT.measurement,
        depth_rng=low_streams.generator("target_depth_context"),
        force_rng=low_streams.generator("target_force_noise"),
        impulse_rng=low_streams.generator("target_impulse_noise"),
    )
    high_target = observe_target(
        target_force,
        target_impulse,
        preferred_depth,
        DEFAULT.measurement,
        depth_rng=high_streams.generator("target_depth_context"),
        force_rng=high_streams.generator("target_force_noise"),
        impulse_rng=high_streams.generator("target_impulse_noise"),
    )
    assert np.array_equal(low_target.force, high_target.force)
    assert np.array_equal(low_target.impulse, high_target.impulse)

    split = PUBLIC_SPLITS["public_train"]
    public_keys = public_grouping_keys(split, 0, 0, 0)

    def expected_key(namespace: str, kind: str, *parts: object) -> str:
        payload = json.dumps([str(part) for part in parts]).encode()
        digest = hashlib.sha256(
            ("lcmj-v3-key\0" + namespace + "\0" + kind + "\0").encode() + payload
        ).hexdigest()
        return f"{kind}-{digest[:32]}"

    assert public_keys == (
        expected_key("public-v3", "participant", "public_train", 0, 0),
        expected_key("public-v3", "origin", "public_train", 0, 0, 0),
        expected_key("public-v3", "query", "public_train", 0, 0, 0, "H72"),
        expected_key("public-v3", "query", "public_train", 0, 0, 0, "D7"),
    )

    # A present query still projects when its baseline and observed labels are missing.
    assert admitted_horizons(np.asarray([True, False])) == (0,)
    record: dict[str, Any] = {
        "participant_key": public_keys[0],
        "origin_key": public_keys[1],
        "query_key": public_keys[2],
        "horizon": "H72",
        "target_time_hours": 72.0,
        "target_window_hours": {"low": 66.0, "high": 78.0},
        "baseline": {
            "relative_mean_concentric_force": None,
            "relative_concentric_net_impulse": None,
        },
        "public_features": {
            "participant": {},
            "history_assessments": [],
            "history_exposures": [],
            "index_exposure": {},
            "known_plan": [],
        },
        "label": {
            "innovation": {
                "relative_mean_concentric_force": None,
                "relative_concentric_net_impulse": None,
            }
        },
    }
    row = project_public_record(
        record,
        GroupingMetadata("public_train", 0, 0, 0),
    )
    assert row.labels[HORIZON_TARGET_COLUMNS[0]] is None
    assert row.labels[HORIZON_TARGET_COLUMNS[1]] is None
    assert len(row.fields) == 135
    assert not set(PUBLIC_GROUPING_COLUMNS).intersection(row.fields)
    assert not set(HORIZON_TARGET_COLUMNS).intersection(row.fields)
    assert not {"target_time_depth", "latent_state", "latent_kinetics", "camp_effect"}.intersection(
        row.fields
    )
    public = row.public_mapping()
    assert tuple(public)[:3] == PUBLIC_GROUPING_COLUMNS
    assert tuple(public)[3 : 3 + 135] == R02_FIELD_NAMES
    assert tuple(public)[-2:] == HORIZON_TARGET_COLUMNS
    assert not {"camp_index", "participant_index", "origin_index"}.intersection(public)


def test_f2_f3_strata_boundaries_and_all_six_cells_are_reachable() -> None:
    six_clean = tuple(RichHistoryAssessment(-24.0, "valid", 2.0) for _ in range(6))
    one_after = (RichHistoryAssessment(-23.0, "valid", 2.0), *six_clean[1:])
    two_after = (
        RichHistoryAssessment(-23.0, "valid", 2.0),
        RichHistoryAssessment(-22.0, "valid", 3.0),
        *six_clean[2:],
    )
    assert rich_history_stratum((-24.0,), six_clean) == "L0|clean"
    assert rich_history_stratum((-24.0,), one_after) == "L1|clean"
    assert rich_history_stratum((-24.0,), two_after) == "L2|clean"
    invalid_low_trials = (*six_clean, RichHistoryAssessment(-1.0, "invalid", 1.0))
    assert rich_history_stratum((-24.0,), invalid_low_trials) == "L0|clean"
    degraded_l0 = (RichHistoryAssessment(-24.0, "valid", 1.0), *six_clean[1:])
    degraded_l1 = (RichHistoryAssessment(-23.0, "valid", 1.0), *six_clean[1:])
    degraded_l2 = (
        RichHistoryAssessment(-23.0, "valid", 1.0),
        RichHistoryAssessment(-22.0, "valid", 2.0),
        *six_clean[2:],
    )
    assert rich_history_stratum((-24.0,), degraded_l0) == "L0|degraded"
    assert rich_history_stratum((-24.0,), degraded_l1) == "L1|degraded"
    assert rich_history_stratum((-24.0,), degraded_l2) == "L2|degraded"
    valid_low_trials = (RichHistoryAssessment(-24.0, "valid", 1.0), *six_clean[1:])
    assert rich_history_stratum((-24.0,), valid_low_trials) == "L0|degraded"
    assert rich_history_stratum((-24.0,), six_clean[:5]) == "L0|degraded"

    expected = {f"{level}|{quality}" for level in F2_LEVELS for quality in F3_LEVELS}
    assert len(expected) == 6
    assert {
        rich_history_stratum((-24.0,), six_clean),
        rich_history_stratum((-24.0,), one_after),
        rich_history_stratum((-24.0,), two_after),
        rich_history_stratum((-24.0,), degraded_l0),
        rich_history_stratum((-24.0,), degraded_l1),
        rich_history_stratum((-24.0,), degraded_l2),
    } == expected


def test_d04_full_public_geometry_membership_and_admission() -> None:
    # The current e287/OSS replay is clean-room only; its counts are not historical D04 membership.
    expected_geometry: dict[PublicSplitName, tuple[int, int, int, int]] = {
        "public_train": (15112, 4096, 512, 8192),
        "public_validation": (3768, 1024, 128, 2048),
    }
    split_state: dict[str, tuple[set[str], set[str], set[str], set[int]]] = {}
    for split_name in PUBLIC_SPLITS:
        expected = expected_geometry[split_name]
        rows = 0
        participants: set[str] = set()
        origins: set[str] = set()
        queries: set[str] = set()
        camps: set[int] = set()
        participant_to_camp: dict[str, int] = {}
        participant_origins: dict[str, set[str]] = {}
        origin_participants: dict[str, str] = {}
        origin_horizons: dict[str, set[str]] = {}
        camp_participants: dict[int, set[str]] = {}
        strata: set[str] = set()
        for row in iter_rich_history_public_split(split_name):
            rows += 1
            participants.add(row.participant_key)
            origins.add(row.origin_key)
            queries.add(row.query_key)
            camp = row.grouping.camp_index
            camps.add(camp)
            participant_to_camp.setdefault(row.participant_key, camp)
            assert participant_to_camp[row.participant_key] == camp
            participant_origins.setdefault(row.participant_key, set()).add(row.origin_key)
            origin_participants.setdefault(row.origin_key, row.participant_key)
            assert origin_participants[row.origin_key] == row.participant_key
            origin_horizons.setdefault(row.origin_key, set()).add(str(row.fields["horizon"]))
            camp_participants.setdefault(camp, set()).add(row.participant_key)
            strata.add(row.stratum)
            assert len(row.fields) == 135
            assert set(row.fields) == set(R02_FIELD_NAMES)
            assert row.grouping.split == split_name
        assert (rows, len(participants), len(camps), len(origins)) == expected
        assert len(queries) == rows
        assert set(participant_to_camp) == participants
        assert all(len(value) == 2 for value in participant_origins.values())
        assert all(len(value) in (1, 2) for value in origin_horizons.values())
        assert all(len(value) == 8 for value in camp_participants.values())
        assert len(origin_horizons) == expected[3]
        assert strata == {f"{level}|{quality}" for level in F2_LEVELS for quality in F3_LEVELS}
        split_state[split_name] = (participants, origins, queries, camps)

    train, validation = split_state["public_train"], split_state["public_validation"]
    for index in range(3):
        assert not train[index].intersection(validation[index])
    assert PUBLIC_SPLITS["public_train"].participants_per_camp == 8
    assert PUBLIC_SPLITS["public_validation"].participants_per_camp == 8
    assert PUBLIC_SPLITS["public_train"].origins_per_participant == 2
    assert PUBLIC_SPLITS["public_validation"].origins_per_participant == 2
    historical = get_reproduction_contract("rich_history_camp_recovery").splits
    train_reference = next(split for split in historical if split.name == "training")
    validation_reference = next(split for split in historical if split.name == "public_validation")
    assert train_reference.rows == 15182
    assert validation_reference.rows == 3795
    assert expected_geometry["public_train"][0] != train_reference.rows
    assert expected_geometry["public_validation"][0] != validation_reference.rows
    assert RICH_HISTORY_REPRODUCTION_METADATA.split_assignment == "PARTIAL"
    assert (
        get_reproduction_contract("rich_history_camp_recovery")
        .claim(ReproductionDimension.SPLIT_ASSIGNMENT)
        .status
        is ReproductionStatus.PARTIAL
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.oss_numpy_version == "2.5.3"
    assert admitted_horizons(np.asarray([True, False])) == (0,)
    assert admitted_horizons(np.asarray([False, True])) == (1,)
    assert admitted_horizons(np.asarray([True, True])) == (0, 1)


def test_e02_uses_all_24_cells_and_returns_only_native_precalibration_progress() -> None:
    assert len(RICH_HISTORY_CELLS) == 2 * 2 * 6 == 24
    values = tuple(
        CellValues(
            cell,
            (0.0, 2.0)
            if cell.outcome is OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION
            else (0.0, 4.0),
            (0.0, 2.0),
        )
        for cell in RICH_HISTORY_CELLS
    )
    result = rich_history_native_progress(values)
    assert len(result.cells) == 24
    assert all(metric.row_count == 2 for metric in result.cells)
    assert result.outcome_progress == (
        (OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value, 1.0),
        (OutcomeVariable.NET_IMPULSE_INNOVATION.value, 0.0),
    )
    assert result.aggregate_progress == 0.5

    varying: list[CellValues] = []
    force_cell_count = 0
    for cell in RICH_HISTORY_CELLS:
        if cell.outcome is OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION:
            force_cell_count += 1
            error = 0.7 if force_cell_count == 12 else 0.1
        else:
            error = 1.2
        varying.append(CellValues(cell, (0.0, 2.0 + error * math.sqrt(2.0)), (0.0, 2.0)))
    unequal = rich_history_native_progress(tuple(varying))
    assert unequal.outcome_progress[0][1] == pytest.approx(0.85)
    assert unequal.outcome_progress[1][1] == 0.0
    assert unequal.aggregate_progress == pytest.approx(0.425)

    zero_sd_values = tuple(CellValues(cell, (3.0, 3.0), (2.0, 2.0)) for cell in RICH_HISTORY_CELLS)
    zero_sd = rich_history_native_progress(zero_sd_values)
    assert all(metric.observation_standard_deviation == 0.0 for metric in zero_sd.cells)
    assert all(metric.normalized_error == 1.0 and not metric.normalized for metric in zero_sd.cells)
    with pytest.raises(MetricInputError, match="requires at least 2 rows"):
        rich_history_native_progress(
            tuple(CellValues(cell, (0.0,), (0.0,)) for cell in RICH_HISTORY_CELLS)
        )
