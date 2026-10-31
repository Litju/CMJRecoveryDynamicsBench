"""Regression-first references for the two statistical review findings only."""

import hashlib
import itertools
import json
import math
from dataclasses import asdict, replace

import numpy as np
import pytest
import test_native_analysis as analysis_tests
from test_native_analysis import AUTHORITY, SPLITS, invented_records, locked_plan, run

from cmj_recovery_dynamics.metrics.native_analysis import (
    EXACT_SIGN_FLIP_MAX_GROUPS,
    CandidatePredictions,
    FrozenConstantBaseline,
    _sign_flip_p,  # pyright: ignore[reportPrivateUsage]
    fit_synthetic_constant_baseline,
    holm_adjust,
)
from cmj_recovery_dynamics.metrics.native_research import NativeObservation, NativePrediction


def enumeration_reference(losses: list[float]) -> float:
    observed = math.fsum(losses)
    tolerance = 8 * float(np.finfo(float).eps) * len(losses) * math.fsum(abs(x) for x in losses)
    allocations = list(itertools.product((-1, 1), repeat=len(losses)))
    return sum(
        math.fsum(sign * loss for sign, loss in zip(signs, losses, strict=True))
        >= observed - tolerance
        for signs in allocations
    ) / len(allocations)


def training_records() -> list[NativeObservation]:
    _, observations = invented_records()
    return [
        replace(
            row,
            query=replace(
                row.query,
                participant="training",
                origin="training-origin",
                query=f"training-{row.query.horizon}",
                input_identity=f"training-input-{row.query.horizon}",
            ),
        )
        for row in observations[:4]
    ]


def test_f1_six_clusters_must_use_complete_null_distribution() -> None:
    losses = [1.0] * 6
    signs = np.random.default_rng(581).choice(np.array([-1, 1]), size=(10_000, 6))
    assert _sign_flip_p(np.asarray(losses), signs) == enumeration_reference(losses) == 1 / 64


def test_f2_substituted_rehashed_baseline_needs_an_independent_pin() -> None:
    artifact = fit_synthetic_constant_baseline(
        training_records(),
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )
    substituted = replace(artifact, values=(9.0, 9.0, 9.0, 9.0))
    old_content = (
        substituted.version,
        asdict(substituted.source_authority),
        substituted.training_identity_sha256,
        substituted.training_participants,
        substituted.values,
    )
    forged = replace(
        substituted,
        artifact_sha256=hashlib.sha256(
            json.dumps(old_content, sort_keys=True, allow_nan=False).encode()
        ).hexdigest(),
    )
    candidates, observations = invented_records()
    with pytest.raises(ValueError, match="BASELINE_PIN"):
        run(candidates, observations, constant_baseline=forged)


@pytest.mark.parametrize("groups", [3, 6, 7, 10])
def test_exact_reference_discreteness_and_seed_independence(groups: int) -> None:
    for losses in (
        [1.0] * groups,
        [0.0] * groups,
        [1.0, -1.0, *([0.0] * (groups - 2))],
        [1.0, -2.0, *([0.0] * (groups - 2))],
        [0.25 + i / 4 * (-1 if i % 3 == 0 else 1) for i in range(groups)],
    ):
        expected = enumeration_reference(losses)
        for seed in (1, 581, 20261031):
            sampled = np.random.default_rng(seed).choice(np.array([-1, 1]), size=(10000, groups))
            actual = _sign_flip_p(np.asarray(losses), sampled)
            assert actual == expected
            assert actual * (2**groups) == round(actual * (2**groups))
    assert _sign_flip_p(np.ones(groups), None) == 1 / 2**groups


def test_exact_boundary_and_larger_monte_carlo_reference() -> None:
    assert EXACT_SIGN_FLIP_MAX_GROUPS == 16
    assert _sign_flip_p(np.ones(16), None) == 1 / 65536
    groups = 17
    losses = np.arange(1, groups + 1, dtype=np.float64)
    signs = np.random.default_rng(17).choice(np.array([-1, 1]), size=(10000, groups))
    expected = (1 + sum(all(x == 1 for x in row) for row in signs)) / 10001
    assert _sign_flip_p(losses, signs) == expected
    with pytest.raises(ValueError, match="ALLOCATIONS_REQUIRED"):
        _sign_flip_p(losses, None)


@pytest.mark.parametrize("groups", [3, 6, 7, 10])
def test_four_cell_holm_at_exact_minimum(groups: int) -> None:
    minimum = _sign_flip_p(np.ones(groups), None)
    assert minimum == 1 / 2**groups
    adjusted = holm_adjust([minimum] * 4)
    assert adjusted == (4 / 2**groups,) * 4
    assert all(p <= 0.05 for p in adjusted) is (groups >= 7)
    if groups == 6:
        assert adjusted == (0.0625,) * 4


@pytest.mark.parametrize("groups", [3, 6, 7, 10, 17])
def test_engine_mode_receipt_and_four_cell_decisions(
    groups: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, prototype = invented_records()
    observations = [
        replace(
            row,
            query=replace(
                row.query,
                participant=f"p{i}",
                origin=f"p{i}-origin",
                query=f"p{i}-{row.query.horizon}",
                input_identity=f"p{i}-input-{row.query.horizon}",
            ),
        )
        for i in range(groups)
        for row in prototype[:4]
    ]
    candidates = [
        CandidatePredictions(
            "M0",
            repeat,
            tuple(
                NativePrediction(row.query, row.target, row.unit, row.value) for row in observations
            ),
        )
        for repeat in (0, 1)
    ]
    monkeypatch.setattr(
        analysis_tests, "SPLITS", {**SPLITS, "test": [f"p{i}" for i in range(groups)]}
    )
    for seed in (1, 581):
        result = run(candidates, observations, plan=replace(locked_plan(), seed=seed))
        method = result["methods"]["sign_flip"]
        if groups <= 16:
            assert method["mode"] == "exact"
            assert method["allocations"] == 2**groups and method["seed"] is None
            assert all(d["unadjusted_p"] == 1 / 2**groups for d in result["decisions"])
            assert all(d["holm_adjusted_p"] == 4 / 2**groups for d in result["decisions"])
            assert all(d["passed"] for d in result["decisions"]) is (groups >= 7)
        else:
            assert method["mode"] == "monte_carlo"
            assert method["allocations"] == 10000 and method["seed"] == seed
            assert "not an exact tail" in method["limitations"]


def rehash(artifact: FrozenConstantBaseline) -> FrozenConstantBaseline:
    content = (
        artifact.version,
        asdict(artifact.source_authority),
        artifact.training_identity_sha256,
        artifact.training_participants,
        artifact.values,
        artifact.fit_protocol,
        artifact.cell_order,
    )
    digest = hashlib.sha256(
        json.dumps(content, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    return replace(artifact, artifact_sha256=digest)


def fitted_baseline() -> FrozenConstantBaseline:
    return fit_synthetic_constant_baseline(
        training_records(),
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )


def test_rehashed_substitutions_cannot_replace_independently_pinned_baseline() -> None:
    artifact = fitted_baseline()
    assert rehash(artifact) == artifact
    candidates, observations = invented_records()
    for forged in (
        replace(artifact, values=(9.0,) * 4),
        replace(artifact, training_participants=("another-training-group",)),
        replace(artifact, training_identity_sha256="f" * 64),
        replace(artifact, source_authority=replace(AUTHORITY, reference="forged")),
        replace(artifact, fit_protocol="heldout_fit"),
        replace(artifact, cell_order=tuple(reversed(artifact.cell_order))),
    ):
        forged = rehash(forged)
        assert forged.artifact_sha256 != artifact.artifact_sha256
        with pytest.raises(ValueError, match="FROZEN_TRAINING"):
            run(
                candidates,
                observations,
                constant_baseline=forged,
                expected_constant_baseline_sha256=artifact.artifact_sha256,
            )
    for forged in (
        replace(artifact, training_participants=("another-training-group",)),
        replace(artifact, fit_protocol="heldout_fit"),
        replace(artifact, cell_order=tuple(reversed(artifact.cell_order))),
        replace(artifact, source_authority=replace(AUTHORITY, reference="forged")),
    ):
        forged = rehash(forged)
        with pytest.raises(ValueError, match="FROZEN_TRAINING"):
            run(
                candidates,
                observations,
                constant_baseline=forged,
                expected_constant_baseline_sha256=forged.artifact_sha256,
            )


def test_training_labels_and_full_observation_identity_are_bound() -> None:
    original = fitted_baseline()
    for rows in (
        [replace(row, value=row.value + 1) for row in training_records()],
        [replace(row, assessment_identity="changed-assessment") for row in training_records()],
    ):
        changed = fit_synthetic_constant_baseline(
            rows,
            source_authority=AUTHORITY,
            expected_authority=AUTHORITY,
            participant_splits=SPLITS,
            dataset_kind="synthetic",
        )
        assert changed.training_identity_sha256 != original.training_identity_sha256
        assert changed.artifact_sha256 != original.artifact_sha256
    with pytest.raises(ValueError, match="DESIGNATED_TRAINING"):
        fit_synthetic_constant_baseline(
            training_records(),
            source_authority=AUTHORITY,
            expected_authority=AUTHORITY,
            participant_splits={**SPLITS, "train": ["training", "unused-training"]},
            dataset_kind="synthetic",
        )
    candidates, observations = invented_records()
    with pytest.raises(ValueError, match="EMPIRICAL_EXECUTION_BLOCKED"):
        run(
            candidates,
            observations,
            constant_baseline=original,
            expected_constant_baseline_sha256=original.artifact_sha256,
            dataset_kind="empirical",
        )
