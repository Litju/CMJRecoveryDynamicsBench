"""Synthetic-only native analysis; caller declarations never authorize empirical execution."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.metrics.native_research import (
    NATIVE_SOURCE_V1,
    NativeAuthority,
    NativeHorizon,
    NativeObservation,
    NativePrediction,
    NativeTarget,
    synthetic_native_rmse_v1,
)

VERSION = "gate7_native_analysis_v1"
CELLS = tuple((horizon, target) for horizon in NativeHorizon for target in NativeTarget)
STAGES = (
    "metadata",
    "structural",
    "measurement_authority",
    "participant_independence",
    "data_use_authorization",
    "result_generation_authorization",
    "result_disclosure_authorization",
)


@dataclass(frozen=True, slots=True)
class CellRule:
    horizon: NativeHorizon
    target: NativeTarget
    unit: str
    improvement_margin: float
    max_rmse: float
    max_mae: float
    max_abs_bias: float
    minimum_participants: int


@dataclass(frozen=True, slots=True)
class AnalysisPlan:
    identity: str
    primary_candidate: str
    rules: tuple[CellRule, ...]
    analysis_unit: str
    ci_method: str
    multiplicity_family: tuple[str, ...]
    test_method: str
    test_assumption: str
    resamples: int
    seed: int
    alpha: float
    locked: bool
    exclusions: tuple[str, ...]
    hypothetical_thresholds: bool


@dataclass(frozen=True, slots=True)
class CandidatePredictions:
    model_id: str
    repeat: int
    predictions: tuple[NativePrediction, ...]


@dataclass(frozen=True, slots=True)
class FrozenConstantBaseline:
    version: str
    artifact_sha256: str
    source_authority: NativeAuthority
    training_identity_sha256: str
    training_participants: tuple[str, ...]
    values: tuple[float, ...]


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _synthetic(dataset_kind: str) -> None:
    if dataset_kind != "synthetic":
        raise ValueError(
            "EMPIRICAL_EXECUTION_BLOCKED: this implementation qualifies synthetic data only"
        )


def _finite_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def cell_identity(horizon: NativeHorizon, target: NativeTarget) -> str:
    return f"{horizon.value}/{target.value}"


def validate_analysis_plan(plan: AnalysisPlan) -> None:
    """Require investigator decisions rather than inventing scientific thresholds."""
    if (
        type(plan) is not AnalysisPlan
        or plan.locked is not True
        or not plan.identity.strip()
        or not plan.primary_candidate.strip()
        or plan.analysis_unit != "query_weighted_participant_cluster"
        or plan.ci_method != "percentile_linear_95"
        or plan.test_method != "participant_sign_flip_squared_error"
        or plan.test_assumption != "independent_participant_clusters_symmetric_paired_loss_null"
        or plan.multiplicity_family != tuple(cell_identity(*cell) for cell in CELLS)
        or type(plan.resamples) is not int
        or plan.resamples < 10_000
        or type(plan.seed) is not int
        or plan.seed < 0
        or type(plan.alpha) is not float
        or plan.alpha != 0.05
        or type(plan.hypothetical_thresholds) is not bool
        or type(plan.exclusions) is not tuple
        or any(type(item) is not str or not item.strip() for item in plan.exclusions)
    ):
        raise ValueError("LOCKED_PLAN_REQUIRED: incomplete or unsupported prespecified methods")
    if len(plan.rules) != 4 or {(r.horizon, r.target) for r in plan.rules} != set(CELLS):
        raise ValueError("FOUR_CELL_RULES_REQUIRED")
    units = {NativeTarget.FORCE: "N/kg", NativeTarget.IMPULSE: "m/s"}
    for rule in plan.rules:
        if (
            type(rule.horizon) is not NativeHorizon
            or type(rule.target) is not NativeTarget
            or rule.unit != units[rule.target]
            or not all(
                _finite_nonnegative(value)
                for value in (
                    rule.improvement_margin,
                    rule.max_rmse,
                    rule.max_mae,
                    rule.max_abs_bias,
                )
            )
            or type(rule.minimum_participants) is not int
            or rule.minimum_participants < 2
        ):
            raise ValueError("NATIVE_CELL_THRESHOLDS_REQUIRED: margins, bounds, units and groups")


def holm_adjust(p_values: Sequence[float]) -> tuple[float, ...]:
    """Step-down Holm adjusted p values, retaining input order."""
    if not p_values or any(not _finite_nonnegative(p) or p > 1 for p in p_values):
        raise ValueError("p values must be finite probabilities")
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(order)
    maximum = 0.0
    for rank, index in enumerate(order):
        maximum = max(maximum, min(1.0, (len(order) - rank) * p_values[index]))
        adjusted[index] = maximum
    return tuple(adjusted)


def fit_synthetic_constant_baseline(
    observations: Sequence[NativeObservation],
    *,
    source_authority: NativeAuthority,
    expected_authority: NativeAuthority,
    participant_splits: Mapping[str, Sequence[object]],
    dataset_kind: str,
) -> FrozenConstantBaseline:
    """Freeze four training-only constants. Validation/test labels are rejected."""
    _synthetic(dataset_kind)
    validation_splits = {
        "train": participant_splits["validation"],
        "validation": participant_splits["test"],
        "test": participant_splits["train"],
    }
    synthetic_native_rmse_v1(
        [NativePrediction(row.query, row.target, row.unit, 0.0) for row in observations],
        observations,
        source_contract=NATIVE_SOURCE_V1,
        source_authority=source_authority,
        expected_authority=expected_authority,
        participant_splits=validation_splits,
        dataset_kind=dataset_kind,
    )
    values = tuple(
        math.fsum(row.value for row in observations if (row.query.horizon, row.target) == cell)
        / sum((row.query.horizon, row.target) == cell for row in observations)
        for cell in CELLS
    )
    identities = sorted(
        (row.query.participant, row.query.query, row.target.value) for row in observations
    )
    identity = _digest(identities)
    training_participants = tuple(sorted({row.query.participant for row in observations}))
    content = (
        "gate7_train_constant_v1",
        asdict(source_authority),
        identity,
        training_participants,
        values,
    )
    return FrozenConstantBaseline(
        "gate7_train_constant_v1",
        _digest(content),
        source_authority,
        identity,
        training_participants,
        values,
    )


def _constant_valid(
    artifact: FrozenConstantBaseline,
    authority: NativeAuthority,
    participant_splits: Mapping[str, Sequence[object]],
) -> None:
    content = (
        artifact.version,
        asdict(artifact.source_authority),
        artifact.training_identity_sha256,
        artifact.training_participants,
        artifact.values,
    )
    if (
        artifact.version != "gate7_train_constant_v1"
        or artifact.source_authority != authority
        or not artifact.training_participants
        or not set(artifact.training_participants) <= set(participant_splits["train"])
        or set(artifact.training_participants)
        & (set(participant_splits["test"]) | set(participant_splits["validation"]))
        or len(artifact.values) != 4
        or not all(math.isfinite(x) for x in artifact.values)
        or artifact.artifact_sha256 != _digest(content)
    ):
        raise ValueError("FROZEN_TRAINING_ARTIFACT_REQUIRED")


def _summary(errors: NDArray[np.float64]) -> NDArray[np.float64]:
    result = np.array(
        [np.sqrt(np.mean(errors**2)), np.mean(np.abs(errors)), np.mean(errors)], dtype=np.float64
    )
    if not np.isfinite(result).all():
        raise ValueError("NATIVE_ERROR_OVERFLOW")
    return result


def _bootstrap(
    errors: NDArray[np.float64],
    group_indices: NDArray[np.int64],
    draws: NDArray[np.int64],
) -> NDArray[np.float64]:
    # Repeated participant draws retain every row once per draw, including unequal cluster sizes.
    counts = np.bincount(group_indices, minlength=draws.shape[1]).astype(np.float64)
    denominator = counts[draws].sum(axis=1)
    sums = np.stack(
        [
            np.bincount(group_indices, weights=weights, minlength=len(counts))
            for weights in (errors**2, np.abs(errors), errors)
        ]
    )
    means = sums[:, draws].sum(axis=2) / denominator
    means[0] = np.sqrt(means[0])
    if not np.isfinite(means).all():
        raise ValueError("NATIVE_BOOTSTRAP_OVERFLOW")
    return means.T


def _interval(values: NDArray[np.float64]) -> list[float]:
    return [float(x) for x in np.quantile(values, [0.025, 0.975], method="linear")]


def _sign_flip_p(paired_cluster_loss: NDArray[np.float64], signs: NDArray[np.int64]) -> float:
    observed = float(paired_cluster_loss.sum())
    if not math.isfinite(observed) or not np.isfinite(paired_cluster_loss).all():
        raise ValueError("PAIRED_LOSS_OVERFLOW")
    if observed <= 0:
        return 1.0
    randomized = (signs * paired_cluster_loss).sum(axis=1)
    tolerance = (
        8
        * np.finfo(np.float64).eps
        * len(paired_cluster_loss)
        * float(np.abs(paired_cluster_loss).sum())
    )
    # Plus-one Monte Carlo correction includes the observed allocation; no zero p values.
    return float((1 + np.count_nonzero(randomized >= observed - tolerance)) / (len(signs) + 1))


def synthetic_native_analysis_v1(
    candidates: Sequence[CandidatePredictions],
    observations: Sequence[NativeObservation],
    *,
    plan: AnalysisPlan,
    admission_stages: Mapping[str, bool],
    admission_receipt_sha256: str,
    admission_receipt: Mapping[str, object],
    source_authority: NativeAuthority,
    expected_authority: NativeAuthority,
    participant_splits: Mapping[str, Sequence[object]],
    dataset_kind: str,
    constant_baseline: FrozenConstantBaseline | None = None,
) -> dict[str, Any]:
    """Analyze invented records only; even asserted empirical approvals cannot unlock this API.

    CI contrasts are candidate-minus-comparator errors, except RMSE improvement
    (comparator-minus-candidate). Holm tests the zero-improvement paired MSE null;
    a separate bootstrap bound must beat the prespecified native-unit RMSE margin.
    """
    _synthetic(dataset_kind)
    validate_analysis_plan(plan)
    if set(admission_stages) != set(STAGES) or any(
        admission_stages[name] is not True for name in STAGES
    ):
        raise ValueError("ELIGIBILITY_AUTHORITY_REQUIRED: all preflight decisions must pass")
    if len(admission_receipt_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in admission_receipt_sha256
    ):
        raise ValueError("PREFLIGHT_RECEIPT_PIN_REQUIRED")
    if (
        _digest(dict(admission_receipt)) != admission_receipt_sha256
        or admission_receipt.get("version") != "gate7_analysis_admission_v1"
        or admission_receipt.get("dataset_kind") != "synthetic"
        or admission_receipt.get("stages") != dict(admission_stages)
        or admission_receipt.get("source_authority") != asdict(source_authority)
        or admission_receipt.get("participant_splits_sha256") != _digest(dict(participant_splits))
        or admission_receipt.get("observations_sha256")
        != _digest([asdict(row) for row in observations])
        or not observations
        or admission_receipt.get("dataset_identity") != observations[0].query.dataset
        or not isinstance(admission_receipt.get("preflight_payload_sha256"), str)
        or len(str(admission_receipt.get("preflight_payload_sha256"))) != 64
        or any(
            c not in "0123456789abcdef"
            for c in str(admission_receipt.get("preflight_payload_sha256"))
        )
    ):
        raise ValueError("ADMISSION_INPUT_BINDING: receipt does not qualify these exact inputs")
    by_model: dict[str, dict[int, CandidatePredictions]] = {}
    for candidate in candidates:
        if (
            not candidate.model_id.strip()
            or candidate.model_id in {"zero_innovation", "train_constant"}
            or type(candidate.repeat) is not int
            or candidate.repeat not in (0, 1)
            or candidate.repeat in by_model.setdefault(candidate.model_id, {})
        ):
            raise ValueError("CANDIDATE_REPEAT_IDENTITY_INVALID")
        by_model[candidate.model_id][candidate.repeat] = candidate
        synthetic_native_rmse_v1(
            candidate.predictions,
            observations,
            source_contract=NATIVE_SOURCE_V1,
            source_authority=source_authority,
            expected_authority=expected_authority,
            participant_splits=participant_splits,
            dataset_kind=dataset_kind,
        )
    if plan.primary_candidate not in by_model or any(set(r) != {0, 1} for r in by_model.values()):
        raise ValueError("PRIMARY_CANDIDATE_AND_BOTH_REPEATS_REQUIRED")
    obs_by_key = {(row.query.query, row.target): row for row in observations}
    origins = {(r.query.dataset, r.query.origin) for r in observations}
    if any(
        {r.query.horizon for r in observations if (r.query.dataset, r.query.origin) == origin}
        != set(NativeHorizon)
        for origin in origins
    ):
        raise ValueError("INCOMPLETE_ORIGIN_HORIZONS")
    participants = sorted({row.query.participant for row in observations})
    rng = np.random.default_rng(plan.seed)
    draws = rng.integers(
        0, len(participants), size=(plan.resamples, len(participants)), dtype=np.int64
    )
    signs = rng.choice(np.array([-1, 1], dtype=np.int64), size=draws.shape)
    participant_index = {p: i for i, p in enumerate(participants)}
    predictions = {
        (candidate.model_id, candidate.repeat): {
            (row.query.query, row.target): row.value for row in candidate.predictions
        }
        for candidate in candidates
    }
    if constant_baseline is not None:
        _constant_valid(constant_baseline, source_authority, participant_splits)
    rules = {(r.horizon, r.target): r for r in plan.rules}
    cells: list[dict[str, Any]] = []
    raw_p: list[float] = []
    decisions: list[dict[str, Any]] = []
    for cell_index, cell in enumerate(CELLS):
        keys = sorted(k for k, row in obs_by_key.items() if (row.query.horizon, row.target) == cell)
        labels = np.array([obs_by_key[k].value for k in keys], dtype=np.float64)
        groups = np.array(
            [participant_index[obs_by_key[k].query.participant] for k in keys], dtype=np.int64
        )
        if len(set(groups.tolist())) != len(participants):
            raise ValueError("PARTICIPANT_FOUR_CELL_COVERAGE_REQUIRED")
        errors = {
            key: np.array([values[k] for k in keys], dtype=np.float64) - labels
            for key, values in predictions.items()
        }
        baseline_errors = {"zero_innovation": -labels}
        if constant_baseline is not None:
            baseline_errors["train_constant"] = constant_baseline.values[cell_index] - labels
        scores = {key: _summary(error) for key, error in errors.items()}
        boot = {key: _bootstrap(error, groups, draws) for key, error in errors.items()}
        baseline_scores = {key: _summary(error) for key, error in baseline_errors.items()}
        baseline_boot = {
            key: _bootstrap(error, groups, draws) for key, error in baseline_errors.items()
        }

        def comparisons_for(
            score: NDArray[np.float64],
            samples: NDArray[np.float64],
            baseline_scores: dict[str, NDArray[np.float64]] = baseline_scores,
            baseline_boot: dict[str, NDArray[np.float64]] = baseline_boot,
        ) -> dict[str, Any]:
            comparisons: dict[str, Any] = {}
            for baseline, base_score in baseline_scores.items():
                diff = score - base_score
                diff_boot = samples - baseline_boot[baseline]
                comparisons[baseline] = {
                    "candidate_minus_baseline": dict(
                        zip(("rmse", "mae", "signed_bias"), diff.tolist(), strict=True)
                    ),
                    "contrast_ci95": {
                        name: _interval(diff_boot[:, i])
                        for i, name in enumerate(("rmse", "mae", "signed_bias"))
                    },
                    "rmse_improvement": float(-diff[0]),
                    "rmse_improvement_ci95": _interval(-diff_boot[:, 0]),
                }
            return comparisons

        model_results: list[dict[str, Any]] = []
        for model_id in sorted(by_model):
            family = np.mean([scores[(model_id, repeat)] for repeat in (0, 1)], axis=0)
            family_boot = np.mean([boot[(model_id, repeat)] for repeat in (0, 1)], axis=0)
            comparisons = comparisons_for(family, family_boot)
            model_results.append(
                {
                    "model_id": model_id,
                    "repeats": [
                        {
                            "repeat": repeat,
                            "comparisons": comparisons_for(
                                scores[(model_id, repeat)], boot[(model_id, repeat)]
                            ),
                            **dict(
                                zip(
                                    ("rmse", "mae", "signed_bias"),
                                    scores[(model_id, repeat)].tolist(),
                                    strict=True,
                                )
                            ),
                            "ci95": {
                                name: _interval(boot[(model_id, repeat)][:, i])
                                for i, name in enumerate(("rmse", "mae", "signed_bias"))
                            },
                        }
                        for repeat in (0, 1)
                    ],
                    "family_metric_mean_of_repeat_metrics": dict(
                        zip(("rmse", "mae", "signed_bias"), family.tolist(), strict=True)
                    ),
                    "family_ci95": {
                        name: _interval(family_boot[:, i])
                        for i, name in enumerate(("rmse", "mae", "signed_bias"))
                    },
                    "repeat_metric_absolute_disagreement": dict(
                        zip(
                            ("rmse", "mae", "signed_bias"),
                            np.abs(scores[(model_id, 0)] - scores[(model_id, 1)]).tolist(),
                            strict=True,
                        )
                    ),
                    "comparisons": comparisons,
                }
            )
        primary = next(
            model for model in model_results if model["model_id"] == plan.primary_candidate
        )
        paired_loss = np.mean(
            [errors[(plan.primary_candidate, repeat)] ** 2 for repeat in (0, 1)], axis=0
        )
        losses = baseline_errors["zero_innovation"] ** 2 - paired_loss
        cluster_loss = np.bincount(groups, weights=losses, minlength=len(participants))
        p_value = _sign_flip_p(cluster_loss, signs)
        raw_p.append(p_value)
        rule = rules[cell]
        ci = primary["family_ci95"]
        decisions.append(
            {
                "cell": cell_identity(*cell),
                "minimum_participants_met": len(participants) >= rule.minimum_participants,
                "rmse_margin_met": primary["comparisons"]["zero_innovation"][
                    "rmse_improvement_ci95"
                ][0]
                > rule.improvement_margin,
                "rmse_harm_bound_met": ci["rmse"][1] <= rule.max_rmse,
                "mae_harm_bound_met": ci["mae"][1] <= rule.max_mae,
                "bias_bound_met": max(abs(x) for x in ci["signed_bias"]) <= rule.max_abs_bias,
                "unadjusted_p": p_value,
                "rule": asdict(rule),
            }
        )
        cells.append(
            {
                "horizon": cell[0],
                "target": cell[1],
                "unit": rule.unit,
                "participant_count": len(participants),
                "query_count": len(keys),
                "models": model_results,
                "baselines": {
                    name: dict(zip(("rmse", "mae", "signed_bias"), value.tolist(), strict=True))
                    for name, value in baseline_scores.items()
                },
            }
        )
    for decision, adjusted in zip(decisions, holm_adjust(raw_p), strict=True):
        decision["holm_adjusted_p"] = adjusted
        decision["multiplicity_met"] = adjusted <= plan.alpha
        decision["passed"] = all(
            decision[key]
            for key in (
                "minimum_participants_met",
                "rmse_margin_met",
                "rmse_harm_bound_met",
                "mae_harm_bound_met",
                "bias_bound_met",
                "multiplicity_met",
            )
        )
    result: dict[str, Any] = {
        "version": VERSION,
        "dataset_kind": "synthetic",
        "scope": "engineering rehearsal only; no empirical or clinical validity",
        "source_contract": asdict(NATIVE_SOURCE_V1),
        "source_authority": asdict(source_authority),
        "admission_stages": dict(admission_stages),
        "admission_receipt_sha256": admission_receipt_sha256,
        "admission_receipt": dict(admission_receipt),
        "plan": asdict(plan),
        "plan_sha256": _digest(asdict(plan)),
        "dataset_identity": observations[0].query.dataset,
        "input_sha256": _digest([asdict(row) for row in observations]),
        "predictions_sha256": _digest([asdict(row) for row in candidates]),
        "group_count": len(participants),
        "query_count": len({row.query.query for row in observations}),
        "methods": {
            "error_sign": "prediction minus observation",
            "resampling": (
                "participant draws with replacement; "
                "all rows/repeats/candidates/baselines jointly retained"
            ),
            "draws_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
            "bit_generator": "PCG64",
            "numpy_version": np.__version__,
            "family_estimate": "arithmetic mean of two per-repeat metrics; not prediction ensemble",
            "test_null": (
                "zero paired squared-error improvement under "
                "symmetric participant-cluster loss differences"
            ),
            "test_margin_scope": (
                "Holm test is at zero improvement; RMSE margin is assessed "
                "separately with paired bootstrap CI"
            ),
            "p_value": "one-sided sign-flip Monte Carlo; plus-one correction",
            "ci": (
                "two-sided 95% percentile, NumPy linear quantile; marginal CIs are not simultaneous"
            ),
        },
        "constant_baseline": None if constant_baseline is None else asdict(constant_baseline),
        "exclusions": list(plan.exclusions),
        "cells": cells,
        "decisions": decisions,
        "synthetic_decision": "criteria_met"
        if all(d["passed"] for d in decisions)
        else "criteria_not_met",
        "empirical_execution_authorized": False,
    }
    result["receipt_sha256"] = _digest(result)
    return result
