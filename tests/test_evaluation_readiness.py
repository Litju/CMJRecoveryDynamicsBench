"""These examples are synthetic, not empirical performance results."""

import math

import pytest

from cmj_recovery_dynamics.metrics.evaluation_readiness import (
    four_cell_research_errors,
    validate_participant_splits,
)
from cmj_recovery_dynamics.metrics.scoring import INITIAL_CAMP_CELLS, CellValues, MetricInputError


def test_synthetic_four_cell_errors_and_direction() -> None:
    values = tuple(CellValues(cell, (2.0, 0.0), (0.0, 1.0)) for cell in INITIAL_CAMP_CELLS)
    result = four_cell_research_errors(values)
    assert tuple(item.cell for item in result) == INITIAL_CAMP_CELLS
    assert all(item.row_count == 2 for item in result)
    assert all(item.rmse == pytest.approx(math.sqrt(2.5)) for item in result)
    assert all(
        item.mae == pytest.approx(1.5) and item.signed_bias == pytest.approx(0.5) for item in result
    )


def test_synthetic_cells_reject_missing_mismatched_and_nonfinite() -> None:
    values = tuple(CellValues(cell, (0.0,), (0.0,)) for cell in INITIAL_CAMP_CELLS)
    with pytest.raises(MetricInputError):
        four_cell_research_errors(values[:-1])
    with pytest.raises(MetricInputError):
        four_cell_research_errors(values + (values[0],))
    with pytest.raises(MetricInputError):
        four_cell_research_errors(
            values[:-1] + (CellValues(INITIAL_CAMP_CELLS[-1], (float("nan"),), (0.0,)),)
        )
    with pytest.raises(MetricInputError):
        four_cell_research_errors(
            values[:-1] + (CellValues(INITIAL_CAMP_CELLS[-1], (0.0, 1.0), (0.0,)),)
        )


def test_synthetic_participant_groups_reject_leakage_and_missing_splits() -> None:
    valid = {
        "train": ["participant-a", "participant-a"],
        "validation": ["participant-b"],
        "test": ["participant-c"],
    }
    validate_participant_splits(valid)
    with pytest.raises(ValueError, match="overlap"):
        validate_participant_splits({**valid, "test": ["participant-a"]})
    with pytest.raises(ValueError):
        validate_participant_splits({"train": ["participant-a"], "test": ["participant-b"]})
    with pytest.raises(ValueError):
        validate_participant_splits({**valid, "test": [" participant-c"]})
    with pytest.raises(ValueError):
        validate_participant_splits({**valid, "test": []})

    with pytest.raises(ValueError):
        validate_participant_splits({**valid, "test": [42]})
