"""Uncalibrated per-cell errors and participant separation checks for research.

These contracts do not authenticate data, grant permission, or implement the
historical calibrated Gate7 score. A caller must establish those independently.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from cmj_recovery_dynamics.contracts import TargetCell
from cmj_recovery_dynamics.metrics.scoring import (
    INITIAL_CAMP_CELLS,
    CellValues,
    MetricInputError,
    cellwise_normalized_rmse,
)


@dataclass(frozen=True, slots=True)
class ResearchCellErrors:
    """Native-unit errors; signed bias is prediction minus observation."""

    cell: TargetCell
    row_count: int
    rmse: float
    mae: float
    signed_bias: float


def validate_participant_splits(splits: Mapping[str, Sequence[object]]) -> None:
    """Reject empty, malformed, or intersecting training/validation/test groups.

    Identifiers must come from a separately authenticated common identity system;
    this check cannot detect aliases or establish independent sampling.
    """
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("exactly train, validation and test splits are required")
    groups: list[set[str]] = []
    for name in ("train", "validation", "test"):
        values = splits[name]
        if isinstance(values, (str, bytes)) or not values:
            raise ValueError("each split must contain participant identifiers")
        group: set[str] = set()
        for value in values:
            if not isinstance(value, str) or not value or value.strip() != value:
                raise ValueError("participant identifiers must be nonempty canonical strings")
            group.add(value)
        if any(group & previous for previous in groups):
            raise ValueError("participant groups overlap across splits")
        groups.append(group)


def four_cell_research_errors(values: Sequence[CellValues]) -> tuple[ResearchCellErrors, ...]:
    """Return RMSE, MAE and signed bias for exactly the four camp cells.

    Values must be matched observations and predictions in the cell's native
    units. This calculation does not produce or re-anchor a benchmark score.
    """
    validated = cellwise_normalized_rmse(values, INITIAL_CAMP_CELLS)
    by_cell = {item.cell: item for item in values}
    results: list[ResearchCellErrors] = []
    for metric in validated:
        item = by_cell[metric.cell]
        scale = max(max(map(abs, item.predictions)), max(map(abs, item.observations)))
        if scale == 0:
            mae = bias = 0.0
        else:
            errors = tuple(
                prediction / scale - observation / scale
                for prediction, observation in zip(item.predictions, item.observations, strict=True)
            )
            mae = scale * (math.fsum(abs(error) for error in errors) / len(errors))
            bias = scale * (math.fsum(errors) / len(errors))
        if not math.isfinite(mae) or not math.isfinite(bias):
            raise MetricInputError("native-unit error overflowed its finite range")
        results.append(
            ResearchCellErrors(
                metric.cell, metric.row_count, metric.root_mean_square_error, mae, bias
            )
        )
    return tuple(results)
