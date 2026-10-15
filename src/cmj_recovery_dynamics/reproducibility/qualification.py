"""Clean-room execution and evidence-bounded M8 reproduction receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from numbers import Real
from typing import cast

import numpy as np

from cmj_recovery_dynamics.contracts import (
    EvaluationDefinition,
    ForecastHorizon,
    OutcomeVariable,
    TargetCell,
)
from cmj_recovery_dynamics.lineage.contracts import ResultDefinition
from cmj_recovery_dynamics.lineage.contracts import SplitRole as LineageSplitRole
from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY, get_benchmark_lineage
from cmj_recovery_dynamics.metrics.scoring import (
    RICH_HISTORY_CELLS,
    CellValues,
    RichHistoryAssessment,
    rich_history_target_cell,
)
from cmj_recovery_dynamics.model_reproduction.contracts import ResultReproductionStatus
from cmj_recovery_dynamics.model_reproduction.registry import (
    get_model_reproduction,
    get_result_reproduction,
)
from cmj_recovery_dynamics.reproducibility.contracts import (
    DigestReference,
    DigestRole,
    ReproductionResult,
    ReproductionValue,
    RunSpec,
    RuntimeAccounting,
    ScalarResultValue,
)
from cmj_recovery_dynamics.reproducibility.execution import (
    capture_runtime_fingerprint,
    get_metric_implementation,
    get_model_execution_contract,
    result_value_number,
)
from cmj_recovery_dynamics.reproducibility.hashing import sha256_bytes
from cmj_recovery_dynamics.reproducibility.registry import (
    ReproducibilityProfile,
    build_provenance_record,
    create_reproduction_spec,
    get_reproducibility_profiles,
)
from cmj_recovery_dynamics.synthesis.registry import SYNTHESIS_CLAIMS


class ReproducibilityQualificationStatus(StrEnum):
    EXACTLY_REPRODUCIBLE = "EXACTLY_REPRODUCIBLE"
    PARTIALLY_REPRODUCIBLE = "PARTIALLY_REPRODUCIBLE"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"
    HISTORICAL_EVIDENCE_ONLY = "HISTORICAL_EVIDENCE_ONLY"


@dataclass(frozen=True, slots=True)
class SplitSummary:
    row_count: int
    expected_rows: int | None
    row_count_matches_authority: bool
    target_value_count: int
    missing_target_values: int
    non_finite_target_values: int
    all_present_targets_finite: bool
    top_level_fields: tuple[str, ...]
    row_schema_sha256: str
    row_output_sha256: str
    target_summaries: dict[str, dict[str, float | int]]


def _historical_result_status(
    result_records: Sequence[Mapping[str, object]],
) -> ReproducibilityQualificationStatus:
    replays = tuple(
        (item.get("status"), item.get("numerically_replayed")) for item in result_records
    )
    if any(
        status == ResultReproductionStatus.EXACT_REPLAYABLE.value and replayed
        for status, replayed in replays
    ):
        return ReproducibilityQualificationStatus.EXACTLY_REPRODUCIBLE
    if any(replayed for _, replayed in replays):
        return ReproducibilityQualificationStatus.PARTIALLY_REPRODUCIBLE
    if any(item.get("expected_values") for item in result_records):
        return ReproducibilityQualificationStatus.HISTORICAL_EVIDENCE_ONLY
    return ReproducibilityQualificationStatus.NOT_REPRODUCIBLE


def _result_values(result: ResultDefinition) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for value in result.values:
        record: dict[str, object] = {"measure": value.measure, "units": value.unit}
        for field, raw in (
            ("value", value.value),
            ("interval", value.interval),
            ("value_range", value.value_range),
            ("sample_count", value.sample_count),
            ("stratum", value.stratum),
        ):
            if raw is not None:
                record[field] = raw
        output.append(record)
    return output


def _matrix_result_records(benchmark_name: str) -> list[dict[str, object]]:
    lineage = get_benchmark_lineage(benchmark_name)
    public_validation = {
        split.name for split in lineage.splits if split.role is LineageSplitRole.PUBLIC_VALIDATION
    }
    experiment_names = {
        item.name
        for item in LINEAGE_REGISTRY.experiments.values()
        if item.benchmark_name == benchmark_name
    }
    records: list[dict[str, object]] = []
    for result in LINEAGE_REGISTRY.results.values():
        if (
            result.experiment_name not in experiment_names
            or result.split_name not in public_validation
            or "restricted" in result.name.casefold()
            or any("restricted" in name.casefold() for name in result.model_names)
        ):
            continue
        try:
            reproduction = get_result_reproduction(result.name)
        except KeyError:
            status = ResultReproductionStatus.UNRESOLVED.value
            numerically_replayed = False
        else:
            status = reproduction.status.value
            numerically_replayed = reproduction.numerically_replayed
        records.append(
            {
                "identity": result.name,
                "evaluation": result.evaluation_name,
                "comparability": result.comparability.value,
                "status": status,
                "numerically_replayed": numerically_replayed,
                "expected_values": _result_values(result),
            }
        )
    return records


def _model_records(benchmark_name: str) -> list[dict[str, object]]:
    lineage = get_benchmark_lineage(benchmark_name)
    records: list[dict[str, object]] = []
    for family in lineage.models:
        try:
            reproduction = get_model_reproduction(family.name)
        except KeyError:
            continue
        for use in reproduction.uses:
            if use.benchmark_name != benchmark_name or "restricted" in family.name.casefold():
                continue
            execution = get_model_execution_contract(
                family.name, benchmark_name, use.experiment.name
            )
            records.append(
                {
                    "identity": family.name,
                    "experiment": use.experiment.name,
                    "implementation_status": use.implementation_status.value,
                    "configuration_status": use.configuration_status.value,
                    "checkpoint_state": use.checkpoint_state.value,
                    "seed_identities": list(use.seed_identities or ()),
                    "adapter_executable": execution.executable,
                    "checkpoint_auto_loaded": execution.checkpoint_auto_loaded,
                    "execution_reason": execution.reason,
                }
            )
    return records


def _evaluation_records(profile: ReproducibilityProfile) -> list[dict[str, object]]:
    views = profile.evaluation_implementations
    records: list[dict[str, object]] = []
    for view in views:
        evaluation = view.evaluation
        implementation = view.implementation
        definition = (
            evaluation if isinstance(evaluation, EvaluationDefinition) else evaluation.definition
        )
        records.append(
            {
                "identity": evaluation.name,
                "execution_status": view.execution_status,
                "implementation_id": (
                    None if implementation is None else implementation.implementation_id
                ),
                "production_acceptance": (
                    None if definition is None else definition.production_acceptance.value
                ),
                "calibration_reference_status": None
                if definition is None
                else definition.calibration_reference_status.value,
            }
        )
    return records


def build_reproducibility_matrix() -> dict[str, object]:
    """Join public M1–M6 evidence without promoting historical results to replays."""
    benchmarks: list[dict[str, object]] = []
    for profile in get_reproducibility_profiles():
        name = profile.benchmark.name
        lineage = get_benchmark_lineage(name)
        interface = profile.public_dataset_interface
        historical_results = _matrix_result_records(name)
        result_status = _historical_result_status(historical_results)
        audit_status = profile.final_reproduction_audit.overall_status.value
        reproduction_status = (
            ReproducibilityQualificationStatus.PARTIALLY_REPRODUCIBLE
            if interface.supported_splits == ("training", "public_validation")
            else result_status
        )
        claim_names = sorted(
            claim.name for claim in SYNTHESIS_CLAIMS.values() if name in claim.benchmark_names
        )
        models = _model_records(name)
        metrics = _evaluation_records(profile)
        split_records = [
            {
                "identity": split.name,
                "role": split.role.value,
                "rows": split.rows,
                "planned_rows": split.planned_rows,
                "assignment_status": split.assignment_status.value,
                "materialization_state": split.materialization_state.value,
                "materialization_status": split.materialization_status.value,
                "historical_reference_sha256": (
                    None if split.reference_hash is None else split.reference_hash.digest
                ),
            }
            for split in profile.reproduction_contract.splits
        ]
        seed_identities = {
            split: {
                "kind": create_reproduction_spec(name, split).seed_identity.kind.value,
                "value": create_reproduction_spec(name, split).seed_identity.value,
            }
            for split in interface.supported_splits
        }
        benchmarks.append(
            {
                "benchmark": name,
                "reproducibility_status": reproduction_status.value,
                "historical_result_status": result_status.value,
                "m2_formulation_status": audit_status,
                "dataset": {
                    "identity": lineage.dataset.name,
                    "kind": lineage.dataset.kind.value,
                    "generator_identity": interface.generator_identity,
                    "public_splits": list(interface.supported_splits),
                    "split_authorities": split_records,
                },
                "seeds": {
                    "clean_room_defaults": seed_identities,
                    "randomness_authority": {
                        "algorithm": profile.reproduction_contract.randomness.algorithm,
                        "state": profile.reproduction_contract.randomness.state,
                        "seed": profile.reproduction_contract.randomness.seed,
                        "stream_construction": (
                            profile.reproduction_contract.randomness.stream_construction
                        ),
                        "draw_order": profile.reproduction_contract.randomness.draw_order,
                        "substream_strategy": (
                            profile.reproduction_contract.randomness.substream_strategy
                        ),
                    },
                },
                "model_implementations": models,
                "evaluations": metrics,
                "expected_historical_results": historical_results,
                "m6_synthesis_claims": claim_names,
                "missing_evidence": {
                    "m2_unresolved_dimensions": [
                        item.value
                        for item in profile.final_reproduction_audit.unresolved_dimensions
                    ],
                    "non_executable_model_uses": [
                        item["identity"] for item in models if not item["adapter_executable"]
                    ],
                    "unavailable_evaluations": [
                        item["identity"]
                        for item in metrics
                        if item["execution_status"] != "implemented"
                    ],
                    "historical_score_replay": result_status.value,
                },
            }
        )
    return {
        "schema_version": 1,
        "status_scope": {
            "reproducibility_status": (
                "The public dataset generation and registered result chain, together."
            ),
            "historical_result_status": (
                "Whether M1 numeric performance results have been numerically replayed."
            ),
            "exactness_rule": (
                "EXACTLY_REPRODUCIBLE requires exact historical data, model, evaluation, and "
                "result authority; a fresh deterministic clean-room sample is not an exact "
                "historical replay."
            ),
        },
        "m6_public_claim_count": len(SYNTHESIS_CLAIMS),
        "m6_program_claims": sorted(
            claim.name for claim in SYNTHESIS_CLAIMS.values() if claim.scope.value == "PROGRAM"
        ),
        "benchmarks": benchmarks,
    }


def _json_safe(value: object) -> object:
    if isinstance(value, np.generic):
        return _json_safe(cast(object, value.item()))
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, Mapping):
        values = cast(Mapping[object, object], value)
        return {str(key): _json_safe(item) for key, item in values.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in cast(Sequence[object], value)]
    return value


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        _json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _label_items(row: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    label = row.get("label")
    if isinstance(label, Mapping):
        items = tuple(cast(Mapping[str, object], label).items())
    else:
        items = tuple((key, value) for key, value in row.items() if key.startswith("label."))
    if len(items) != 2:
        raise ValueError("each public row must expose exactly two target values")
    return items


def _summarize_rows(
    rows: Iterable[Mapping[str, object]], *, expected_rows: int | None = None
) -> SplitSummary:
    digest = hashlib.sha256()
    row_count = 0
    target_values: dict[str, list[float]] = defaultdict(list)
    missing_targets = 0
    non_finite_targets = 0
    schema: tuple[str, ...] | None = None
    target_schema: tuple[str, ...] | None = None
    for row in rows:
        keys = tuple(sorted(row))
        if schema is None:
            schema = keys
        elif schema != keys:
            raise ValueError("public rows must have a stable top-level schema")
        digest.update(_json_bytes(row))
        digest.update(b"\n")
        row_count += 1
        labels = _label_items(row)
        names = tuple(sorted(name for name, _ in labels))
        if target_schema is None:
            target_schema = names
        elif target_schema != names:
            raise ValueError("public rows must expose a stable target schema")
        for name, raw in labels:
            if raw is None:
                missing_targets += 1
                continue
            value = cast(object, raw.item()) if isinstance(raw, np.generic) else raw
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"target {name} must be a real numeric value")
            numeric = float(value)
            if not math.isfinite(numeric):
                non_finite_targets += 1
            else:
                target_values[name].append(numeric)
    if row_count == 0 or schema is None:
        raise ValueError("public split generation returned no rows")
    return SplitSummary(
        row_count=row_count,
        expected_rows=expected_rows,
        row_count_matches_authority=expected_rows is None or row_count == expected_rows,
        target_value_count=row_count * 2,
        missing_target_values=missing_targets,
        non_finite_target_values=non_finite_targets,
        all_present_targets_finite=non_finite_targets == 0,
        top_level_fields=schema,
        row_schema_sha256=sha256_bytes(_json_bytes(schema)),
        row_output_sha256=digest.hexdigest(),
        target_summaries={
            name: {
                "count": len(values),
                "mean": math.fsum(values) / len(values),
                "minimum": min(values),
                "maximum": max(values),
            }
            for name, values in sorted(target_values.items())
            if values
        },
    )


def _probe_digest(spec: RunSpec) -> tuple[int, str]:
    rows = spec.iter_rows(limit=3)
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        digest.update(_json_bytes(row))
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def _rows_for_split(
    spec: RunSpec, *, retain: bool, retained_rows: list[Mapping[str, object]]
) -> Iterator[Mapping[str, object]]:
    for row in spec.iter_rows():
        if retain:
            retained_rows.append(row)
        yield row


def _result_record(result: ReproductionResult) -> dict[str, object]:
    provenance = result.provenance
    model_use = provenance.m3_model_use
    return {
        "origin": result.origin.value,
        "run_spec": {
            "benchmark": result.run_spec.benchmark_name,
            "split": result.run_spec.split_name,
            "seed": {
                "kind": result.run_spec.seed_identity.kind.value,
                "value": result.run_spec.seed_identity.value,
            },
            "model": result.run_spec.model_name,
            "evaluation": result.run_spec.evaluation_name,
            "sha256": result.run_spec.digest,
        },
        "values": [
            {
                "identity": item.identity,
                "value": result_value_number(item.value),
                "units": item.value.units,
                "sample_count": item.value.sample_count,
            }
            for item in result.values
        ],
        "provenance": {
            "source_manifest_sha256": provenance.source_manifest_sha256,
            "configuration_manifest_sha256": provenance.configuration_manifest_sha256,
            "output_sha256": (
                None if provenance.output_digest is None else provenance.output_digest.digest
            ),
            "m2_formulation_status": provenance.m2_audit.overall_status.value,
            "m2_unresolved_dimensions": [
                item.value for item in provenance.m2_audit.unresolved_dimensions
            ],
            "m3_model_use_status": (
                None if model_use is None else model_use.implementation_status.value
            ),
            "m3_configuration_status": (
                None if model_use is None else model_use.configuration_status.value
            ),
        },
        "runtime": {
            "elapsed_seconds": result.runtime.elapsed_seconds,
            "python_version": provenance.runtime_fingerprint.python_version,
            "numpy_version": provenance.runtime_fingerprint.numpy_version,
            "package_version": provenance.runtime_fingerprint.package_version,
        },
    }


def _target_label_items(row: Mapping[str, object]) -> Mapping[str, object]:
    label = row.get("label")
    if not isinstance(label, Mapping):
        raise ValueError("rich-history row must expose a label mapping")
    return cast(Mapping[str, object], label)


def _rich_history_cells(rows: Sequence[Mapping[str, object]]) -> tuple[CellValues, ...]:
    model = get_model_execution_contract(
        "rich_history_zero_baseline",
        "rich_history_camp_recovery",
        "rich_history_headroom_reconstruction",
    )
    implementation = model.implementation
    if not model.executable or implementation is None or isinstance(implementation, tuple):
        raise ValueError("registered rich-history zero baseline is not executable")
    predictions = np.asarray(implementation(len(rows), len(OutcomeVariable)), dtype=np.float64)
    if predictions.shape != (len(rows), len(OutcomeVariable)):
        raise ValueError("rich-history zero baseline returned an unexpected prediction shape")

    columns = (
        "label.relative_mean_concentric_force_innovation",
        "label.relative_concentric_net_impulse_innovation",
    )
    buckets: dict[TargetCell, tuple[list[float], list[float]]] = {}
    for row_index, row in enumerate(rows):
        raw_features = row.get("features")
        if not isinstance(raw_features, Mapping):
            raise ValueError("rich-history row must expose a feature mapping")
        features = cast(Mapping[str, object], raw_features)
        horizon = ForecastHorizon[str(features["horizon"])]
        exposure_times = tuple(
            _optional_numeric(features.get(f"history_exposure[{index}].time_from_origin_hours"))
            for index in range(6)
        )
        assessments = tuple(
            RichHistoryAssessment(
                time_from_origin_hours=_optional_numeric(
                    features.get(f"history_assessment[{index}].time_from_origin_hours")
                ),
                validity_state=str(features[f"history_assessment[{index}].validity_state"]),
                trial_count=_optional_numeric(
                    features.get(f"history_assessment[{index}].n_trials")
                ),
            )
            for index in range(14)
        )
        labels = _target_label_items(row)
        for outcome_index, (outcome, column) in enumerate(
            zip(OutcomeVariable, columns, strict=True)
        ):
            cell = rich_history_target_cell(horizon, outcome, exposure_times, assessments)
            target = labels[column]
            if target is None:
                continue
            if (
                isinstance(target, bool)
                or not isinstance(target, Real)
                or not math.isfinite(float(target))
            ):
                raise ValueError(f"rich-history target {column} must be finite")
            prediction = float(predictions[row_index, outcome_index])
            prediction_values, observations = buckets.setdefault(cell, ([], []))
            prediction_values.append(prediction)
            observations.append(float(target))
    return tuple(
        CellValues(cell, tuple(buckets[cell][0]), tuple(buckets[cell][1]))
        for cell in RICH_HISTORY_CELLS
        if cell in buckets
    )


def _optional_numeric(value: object) -> float | None:
    if value is None or value == "<MISSING>":
        return None
    if isinstance(value, np.generic):
        value = cast(object, value.item())
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("rich-history stratum inputs must be numeric or missing")
    result = float(value)
    return result if math.isfinite(result) else None


def run_public_qualification() -> dict[str, object]:
    """Execute both public split generators and one complete registered model/metric path."""
    started = time.perf_counter()
    runtime_fingerprint = capture_runtime_fingerprint()
    matrix = build_reproducibility_matrix()
    result_records: list[dict[str, object]] = []
    rich_validation_rows: list[Mapping[str, object]] = []
    rich_validation_summary: SplitSummary | None = None

    for profile in get_reproducibility_profiles():
        benchmark_name = profile.benchmark.name
        for split_name in ("training", "public_validation"):
            spec = create_reproduction_spec(benchmark_name, split_name)
            started_split = time.perf_counter()
            authority = spec.split_authority
            retained = (
                benchmark_name == "rich_history_camp_recovery" and split_name == "public_validation"
            )
            rows: list[Mapping[str, object]] = []
            summary = _summarize_rows(
                _rows_for_split(spec, retain=retained, retained_rows=rows),
                expected_rows=authority.rows,
            )
            elapsed = time.perf_counter() - started_split
            first_probe = _probe_digest(spec)
            repeated_probe = _probe_digest(spec)
            if first_probe != repeated_probe:
                raise RuntimeError(
                    f"deterministic row probe changed for {benchmark_name}/{split_name}"
                )
            digest = summary.row_output_sha256
            values = (
                ReproductionValue(
                    "generated_row_count",
                    ScalarResultValue(float(summary.row_count), "rows"),
                ),
                ReproductionValue(
                    "finite_target_value_count",
                    ScalarResultValue(
                        float(
                            summary.target_value_count
                            - summary.missing_target_values
                            - summary.non_finite_target_values
                        ),
                        "target values",
                    ),
                ),
                ReproductionValue(
                    "missing_target_value_count",
                    ScalarResultValue(float(summary.missing_target_values), "target values"),
                ),
                ReproductionValue(
                    "non_finite_target_value_count",
                    ScalarResultValue(float(summary.non_finite_target_values), "target values"),
                ),
            )
            result = ReproductionResult(
                spec,
                values,
                build_provenance_record(
                    spec,
                    runtime_fingerprint,
                    output_digest=DigestReference(digest, DigestRole.REPRODUCTION_OUTPUT),
                ),
                RuntimeAccounting(elapsed, notes="Public synthetic split generation."),
            )
            result_records.append(
                {
                    "kind": "public_split_generation",
                    **_result_record(result),
                    "numerical_checks": {
                        "matches_m2_historical_row_count": summary.row_count_matches_authority,
                        "all_present_targets_finite": summary.all_present_targets_finite,
                        "target_value_count_is_two_per_row": (
                            summary.target_value_count == 2 * summary.row_count
                        ),
                        "stable_row_schema": True,
                        "deterministic_three_row_probe": True,
                    },
                    "dataset_output": {
                        "row_count": summary.row_count,
                        "m2_historical_row_count": summary.expected_rows,
                        "matches_m2_historical_row_count": summary.row_count_matches_authority,
                        "target_value_count": summary.target_value_count,
                        "missing_target_values": summary.missing_target_values,
                        "non_finite_target_values": summary.non_finite_target_values,
                        "all_present_targets_finite": summary.all_present_targets_finite,
                        "top_level_fields": list(summary.top_level_fields),
                        "row_schema_sha256": summary.row_schema_sha256,
                        "row_output_sha256": summary.row_output_sha256,
                        "determinism_probe_rows": first_probe[0],
                        "determinism_probe_sha256": first_probe[1],
                        "target_summaries": summary.target_summaries,
                    },
                }
            )
            if retained:
                rich_validation_rows = rows
                rich_validation_summary = summary

    if rich_validation_summary is None or not rich_validation_rows:
        raise RuntimeError("rich-history public validation output was not materialized")

    rich_spec = create_reproduction_spec(
        "rich_history_camp_recovery",
        "public_validation",
        model_name="rich_history_zero_baseline",
        evaluation_name="rich_history_raw_progress_diagnostic",
    )
    started_model = time.perf_counter()
    cells = _rich_history_cells(rich_validation_rows)
    if {item.cell for item in cells} != set(RICH_HISTORY_CELLS):
        raise ValueError("rich-history validation did not materialize every registered score cell")
    binding = get_metric_implementation("rich_history_raw_progress_diagnostic")
    raw_progress = binding.evaluate(cells)
    if isinstance(raw_progress, bool) or not isinstance(raw_progress, Real):
        raise ValueError("rich-history raw-progress metric did not return a scalar")
    raw_progress = float(raw_progress)
    if not math.isfinite(raw_progress):
        raise ValueError("rich-history raw-progress metric returned a non-finite result")
    model_elapsed = time.perf_counter() - started_model
    rich_output_digest = sha256_bytes(
        _json_bytes(
            {
                "dataset_sha256": rich_validation_summary.row_output_sha256,
                "model": rich_spec.model_name,
                "evaluation": rich_spec.evaluation_name,
                "raw_progress": raw_progress,
            }
        )
    )
    rich_result = ReproductionResult(
        rich_spec,
        (
            ReproductionValue(
                "raw_progress", ScalarResultValue(raw_progress, "dimensionless progress")
            ),
        ),
        build_provenance_record(
            rich_spec,
            runtime_fingerprint,
            output_digest=DigestReference(rich_output_digest, DigestRole.REPRODUCTION_OUTPUT),
        ),
        RuntimeAccounting(model_elapsed),
    )
    expected = next(
        item
        for benchmark in cast(list[dict[str, object]], matrix["benchmarks"])
        if benchmark["benchmark"] == "rich_history_camp_recovery"
        for item in cast(list[dict[str, object]], benchmark["expected_historical_results"])
        if item["identity"] == "rich_history_zero_baseline_result"
    )
    expected_values = cast(list[dict[str, object]], expected["expected_values"])
    expected_progress = next(
        cast(float, item["value"])
        for item in expected_values
        if item["measure"] == "raw progress" and item.get("value") is not None
    )
    result_records.append(
        {
            "kind": "registered_model_metric_execution",
            **_result_record(rich_result),
            "dataset_output_sha256": rich_validation_summary.row_output_sha256,
            "historical_comparison": {
                "identity": expected["identity"],
                "recorded_value": expected_progress,
                "match_within_absolute_tolerance_1e-12": math.isclose(
                    raw_progress, expected_progress, rel_tol=0.0, abs_tol=1e-12
                ),
                "authority": "M1 evidence only; this clean-room output is not an exact replay.",
            },
        }
    )

    status_counts = {
        status.value: sum(
            item["reproducibility_status"] == status.value
            for item in cast(list[dict[str, object]], matrix["benchmarks"])
        )
        for status in ReproducibilityQualificationStatus
    }
    historical_status_counts = {
        status.value: sum(
            item["historical_result_status"] == status.value
            for item in cast(list[dict[str, object]], matrix["benchmarks"])
        )
        for status in ReproducibilityQualificationStatus
    }
    return {
        "schema_version": 1,
        "study": "public_synthetic_benchmark_reproduction_qualification",
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "command": "python -m cmj_recovery_dynamics.reproducibility.qualification",
        "environment": {
            "isolated_virtual_environment": sys.prefix != sys.base_prefix,
            "python_version": runtime_fingerprint.python_version,
            "python_implementation": runtime_fingerprint.python_implementation,
            "numpy_version": runtime_fingerprint.numpy_version,
            "package_version": runtime_fingerprint.package_version,
            "os_family": runtime_fingerprint.os_family,
            "architecture": runtime_fingerprint.architecture,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "reproducibility_status_counts": status_counts,
        "historical_result_status_counts": historical_status_counts,
        "matrix": matrix,
        "runs": result_records,
        "scientific_scope": (
            "Synthetic generator qualification plus one registered rich-history baseline "
            "diagnostic. No empirical dataset, private checkpoint, or hidden test split was used."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix-only",
        action="store_true",
        help="emit the evidence matrix without generating benchmark rows",
    )
    args = parser.parse_args()
    receipt = build_reproducibility_matrix() if args.matrix_only else run_public_qualification()
    json.dump(receipt, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
    sys.stdout.write("\n")
    if args.matrix_only:
        return 0
    runs = cast(Sequence[Mapping[str, object]], receipt["runs"])
    checks_failed = False
    for run in runs:
        raw_checks = run.get("numerical_checks")
        if not isinstance(raw_checks, Mapping):
            continue
        checks = cast(Mapping[str, object], raw_checks)
        checks_failed = checks_failed or any(
            checks.get(name) is False
            for name in (
                "all_present_targets_finite",
                "target_value_count_is_two_per_row",
            )
        )
    return int(checks_failed)


if __name__ == "__main__":
    raise SystemExit(main())
