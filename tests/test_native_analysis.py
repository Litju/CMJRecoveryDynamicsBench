"""Independent numerical references and refusal controls, using invented values only."""

import hashlib
import json
from dataclasses import asdict, replace
from typing import Any

import numpy as np
import pytest

from cmj_recovery_dynamics.metrics.native_analysis import (
    CELLS,
    STAGES,
    AnalysisPlan,
    CandidatePredictions,
    CellRule,
    fit_synthetic_constant_baseline,
    holm_adjust,
    synthetic_native_analysis_v1,
)
from cmj_recovery_dynamics.metrics.native_research import (
    NativeAuthority,
    NativeHorizon,
    NativeObservation,
    NativePrediction,
    NativeQuery,
    NativeTarget,
)

AUTHORITY = NativeAuthority("invented-analysis-authority", "a" * 64)
SPLITS = {"train": ["training"], "validation": ["validation"], "test": ["p0", "p1", "p2"]}


def locked_plan() -> AnalysisPlan:
    return AnalysisPlan(
        "synthetic-hypothetical-plan",
        "M0",
        tuple(
            CellRule(h, t, "N/kg" if t is NativeTarget.FORCE else "m/s", 0.01, 10.0, 10.0, 10.0, 2)
            for h, t in CELLS
        ),
        "query_weighted_participant_cluster",
        "percentile_linear_95",
        tuple(f"{h.value}/{t.value}" for h, t in CELLS),
        "participant_sign_flip_squared_error",
        "independent_participant_clusters_symmetric_paired_loss_null",
        10_000,
        581,
        0.05,
        True,
        (),
        True,
    )


def invented_records() -> tuple[list[CandidatePredictions], list[NativeObservation]]:
    observations: list[NativeObservation] = []
    for participant, origin_count in enumerate((1, 2, 3)):
        for origin in range(origin_count):
            for h in NativeHorizon:
                query = NativeQuery(
                    "invented-dataset",
                    f"p{participant}",
                    f"p{participant}-o{origin}",
                    f"p{participant}-o{origin}-{h}",
                    f"input-{participant}-{origin}-{h}",
                    h,
                    ("b1", "b2"),
                    (-72.0, -24.0),
                    (3, 3),
                )
                for target in NativeTarget:
                    value = (participant + 1) * (
                        1 if target is NativeTarget.FORCE else 0.1
                    ) + origin * 0.02
                    observations.append(
                        NativeObservation(
                            query,
                            target,
                            "N/kg" if target is NativeTarget.FORCE else "m/s",
                            value,
                            72.0 if h is NativeHorizon.H72 else 168.0,
                            3,
                            f"assessment-{participant}-{origin}-{h}",
                        )
                    )
    candidates = [
        CandidatePredictions(
            f"M{model}",
            repeat,
            tuple(
                NativePrediction(
                    o.query,
                    o.target,
                    o.unit,
                    o.value
                    + (0.1 + model * 0.1 + repeat * 0.03) * (int(o.query.participant[1:]) + 1),
                )
                for o in observations
            ),
        )
        for model in range(2)
        for repeat in (0, 1)
    ]
    return candidates, observations


def run(
    candidates: list[CandidatePredictions], observations: list[NativeObservation], **changes: Any
) -> dict[str, Any]:
    def digest(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()

    receipt = {
        "version": "gate7_analysis_admission_v1",
        "dataset_kind": "synthetic",
        "stages": dict.fromkeys(STAGES, True),
        "source_authority": asdict(AUTHORITY),
        "dataset_identity": observations[0].query.dataset,
        "participant_splits_sha256": digest(SPLITS),
        "observations_sha256": digest([asdict(row) for row in observations]),
        "preflight_payload_sha256": "e" * 64,
    }
    args: dict[str, Any] = dict(
        plan=locked_plan(),
        admission_stages=dict.fromkeys(STAGES, True),
        admission_receipt_sha256=digest(receipt),
        admission_receipt=receipt,
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )
    args.update(changes)
    return synthetic_native_analysis_v1(candidates, observations, **args)


def test_reference_metrics_cluster_resampling_and_repeat_family() -> None:
    candidates, observations = invented_records()
    result = run(candidates, observations)
    first = result["cells"][0]
    assert first["participant_count"] == 3 and first["query_count"] == 6
    model = first["models"][0]
    labels = [
        o.value
        for o in observations
        if o.query.horizon is NativeHorizon.H72 and o.target is NativeTarget.FORCE
    ]
    participants = [
        o.query.participant
        for o in observations
        if o.query.horizon is NativeHorizon.H72 and o.target is NativeTarget.FORCE
    ]
    order = sorted(range(len(labels)), key=lambda i: participants[i])
    labels = [labels[i] for i in order]
    participants = [participants[i] for i in order]
    errors = [[(0.1 + repeat * 0.03) * (int(p[1:]) + 1) for p in participants] for repeat in (0, 1)]
    expected_rmse = sum((sum(e * e for e in row) / len(row)) ** 0.5 for row in errors) / 2
    assert model["family_metric_mean_of_repeat_metrics"]["rmse"] == pytest.approx(expected_rmse)
    assert model["repeats"][0]["signed_bias"] == pytest.approx(sum(errors[0]) / 6)
    # Independent row-expansion implementation: a participant drawn twice contributes twice.
    rng = np.random.default_rng(581)
    draws = rng.integers(0, 3, size=(10_000, 3), dtype=np.int64)
    reference: list[float] = []
    for draw in draws:
        indices = [i for group in draw for i, p in enumerate(participants) if p == f"p{group}"]
        baseline = (sum(labels[i] ** 2 for i in indices) / len(indices)) ** 0.5
        family = (
            sum((sum(row[i] ** 2 for i in indices) / len(indices)) ** 0.5 for row in errors) / 2
        )
        reference.append(baseline - family)
    expected_ci = np.quantile(reference, [0.025, 0.975], method="linear").tolist()
    assert model["comparisons"]["zero_innovation"]["rmse_improvement_ci95"] == pytest.approx(
        expected_ci
    )
    signs = rng.choice(np.array([-1, 1], dtype=np.int64), size=draws.shape)
    # All cluster improvements are positive: only the all-positive sign allocation ties/exceeds.
    expected_p = (1 + int(np.all(signs == 1, axis=1).sum())) / 10_001
    assert all(result["decisions"][i]["unadjusted_p"] == pytest.approx(expected_p) for i in (0, 2))
    assert "zero_innovation" in model["repeats"][0]["comparisons"]
    assert result == run(candidates, observations)
    assert result["empirical_execution_authorized"] is False


def test_holm_known_reference_and_probability_validation() -> None:
    assert holm_adjust((0.01, 0.04, 0.03, 0.002)) == pytest.approx((0.03, 0.06, 0.06, 0.008))
    assert holm_adjust((0.5, 0.5, 0.5)) == (1.0, 1.0, 1.0)
    for bad in [(), (-0.1,), (float("nan"),), (1.1,)]:
        with pytest.raises(ValueError):
            holm_adjust(bad)


def test_all_authority_stages_and_empirical_execution_blocked() -> None:
    candidates, observations = invented_records()
    for stage in STAGES:
        with pytest.raises(ValueError, match="ELIGIBILITY_AUTHORITY"):
            run(
                candidates,
                observations,
                admission_stages={**dict.fromkeys(STAGES, True), stage: False},
            )
    with pytest.raises(ValueError, match="EMPIRICAL_EXECUTION_BLOCKED"):
        run(candidates, observations, dataset_kind="empirical")
    with pytest.raises(ValueError, match="PIN_REQUIRED"):
        run(candidates, observations, admission_receipt_sha256="")


@pytest.mark.parametrize(
    "changes",
    [
        {"locked": False},
        {"primary_candidate": ""},
        {"analysis_unit": "rows_independent"},
        {"ci_method": ""},
        {"multiplicity_family": ()},
        {"resamples": 9999},
        {"test_method": ""},
        {"test_assumption": ""},
        {"rules": ()},
        {"seed": -1},
        {"alpha": 0.1},
    ],
)
def test_missing_prespecification_rejected(changes: dict[str, Any]) -> None:
    candidates, observations = invented_records()
    with pytest.raises(ValueError):
        run(candidates, observations, plan=replace(locked_plan(), **changes))


def test_thresholds_and_minimum_groups_are_not_invented() -> None:
    candidates, observations = invented_records()
    plan = locked_plan()
    for changes in [
        {"improvement_margin": float("nan")},
        {"max_mae": -1},
        {"max_abs_bias": -1},
        {"max_rmse": -1},
        {"unit": "m"},
        {"minimum_participants": 1},
    ]:
        rules = (replace(plan.rules[0], **changes), *plan.rules[1:])
        with pytest.raises(ValueError):
            run(candidates, observations, plan=replace(plan, rules=rules))
    rules = tuple(replace(r, minimum_participants=20) for r in plan.rules)
    result = run(candidates, observations, plan=replace(plan, rules=rules))
    assert result["synthetic_decision"] == "criteria_not_met"
    assert all(not d["minimum_participants_met"] for d in result["decisions"])


def test_native_pairing_and_duplicate_repeat_controls() -> None:
    candidates, observations = invented_records()
    for candidate_list, label_list in [
        (candidates + [candidates[0]], observations),
        (candidates[:-1], observations),
        (candidates, observations[:-1]),
        (candidates, observations + [observations[0]]),
    ]:
        with pytest.raises(ValueError):
            run(candidate_list, label_list)
    with pytest.raises(ValueError, match="unit"):
        run(candidates, [replace(observations[0], unit="m/s"), *observations[1:]])
    wrong = replace(observations[0], query=replace(observations[0].query, participant="wrong"))
    with pytest.raises(ValueError):
        run(candidates, [wrong, *observations[1:]])


def test_train_only_frozen_constant_and_heldout_refusal() -> None:
    candidates, observations = invented_records()
    training = [
        replace(
            o,
            query=replace(
                o.query,
                participant="training",
                origin="training-origin",
                query=f"training-{o.query.horizon}",
                input_identity=f"training-input-{o.query.horizon}",
            ),
        )
        for o in observations[:4]
    ]
    artifact = fit_synthetic_constant_baseline(
        training,
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )
    assert artifact.training_participants == ("training",)
    result = run(candidates, observations, constant_baseline=artifact)
    assert all("train_constant" in cell["baselines"] for cell in result["cells"])
    with pytest.raises(ValueError, match="test split"):
        fit_synthetic_constant_baseline(
            observations,
            source_authority=AUTHORITY,
            expected_authority=AUTHORITY,
            participant_splits=SPLITS,
            dataset_kind="synthetic",
        )
    with pytest.raises(ValueError, match="FROZEN"):
        run(
            candidates,
            observations,
            constant_baseline=replace(artifact, values=(1.0, 1.0, 1.0, 1.0)),
        )
    other_splits = {**SPLITS, "train": ["different-training"]}
    with pytest.raises(ValueError, match="ADMISSION_INPUT_BINDING"):
        run(candidates, observations, constant_baseline=artifact, participant_splits=other_splits)


def test_admission_receipt_cannot_qualify_different_labels_source_or_groups() -> None:
    candidates, observations = invented_records()
    result = run(candidates, observations)
    receipt = result["admission_receipt"]
    pin = result["admission_receipt_sha256"]
    for changed in [
        {"observations_sha256": "f" * 64},
        {"dataset_identity": "another-file"},
        {"source_authority": {"reference": "another-authority", "source_sha256": "a" * 64}},
        {"participant_splits_sha256": "f" * 64},
        {"dataset_kind": "empirical"},
    ]:
        altered = {**receipt, **changed}
        recomputed = hashlib.sha256(
            json.dumps(altered, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
        for expected in (pin, recomputed):
            with pytest.raises(ValueError, match="ADMISSION_INPUT_BINDING"):
                run(
                    candidates,
                    observations,
                    admission_receipt=altered,
                    admission_receipt_sha256=expected,
                )
    with pytest.raises(ValueError, match="ADMISSION_INPUT_BINDING"):
        run(
            candidates,
            [replace(observations[0], value=999), *observations[1:]],
            admission_receipt=receipt,
            admission_receipt_sha256=pin,
        )


def test_malformed_runtime_inputs_are_clear_value_errors() -> None:
    candidates, observations = invented_records()
    unchecked_analysis: Any = synthetic_native_analysis_v1
    unchecked_fit: Any = fit_synthetic_constant_baseline
    unchecked_holm: Any = holm_adjust
    for probabilities in (None, 2, object()):
        with pytest.raises(ValueError):
            unchecked_holm(probabilities)
    result = run(candidates, observations)
    args: dict[str, Any] = dict(
        plan=locked_plan(),
        admission_stages=result["admission_stages"],
        admission_receipt_sha256=result["admission_receipt_sha256"],
        admission_receipt=result["admission_receipt"],
        source_authority=AUTHORITY,
        expected_authority=AUTHORITY,
        participant_splits=SPLITS,
        dataset_kind="synthetic",
    )
    plan_mutations: list[dict[str, Any]] = [
        {"identity": None},
        {"primary_candidate": None},
        {"rules": None},
        {"rules": (None,) * 4},
        {"rules": (replace(locked_plan().rules[0], target=[]),) * 4},
        {"rules": (replace(locked_plan().rules[0], max_mae=10**1000), *locked_plan().rules[1:])},
    ]
    for mutation in plan_mutations:
        with pytest.raises(ValueError):
            run(candidates, observations, plan=replace(locked_plan(), **mutation))
    for mutation in [
        {"admission_receipt_sha256": None},
        {"admission_receipt": None},
        {"source_authority": None},
        {"admission_stages": None},
        {"participant_splits": None},
        {"participant_splits": {**SPLITS, "test": 2}},
        {"constant_baseline": object()},
    ]:
        with pytest.raises(ValueError):
            unchecked_analysis(candidates, observations, **{**args, **mutation})
    for bad in [None, [None], [replace(observations[0], query=None)], []]:
        with pytest.raises(ValueError):
            unchecked_analysis(candidates, bad, **args)
    for bad in [
        None,
        [None],
        [replace(candidates[0], model_id=None)],
        [replace(candidates[0], predictions=None)],
    ]:
        with pytest.raises(ValueError):
            unchecked_analysis(bad, observations, **args)
    with pytest.raises(ValueError):
        unchecked_fit(
            [None],
            source_authority=AUTHORITY,
            expected_authority=AUTHORITY,
            participant_splits=SPLITS,
            dataset_kind="synthetic",
        )
