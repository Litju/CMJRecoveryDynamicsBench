"""Historical score reanchoring, isolated from every benchmark evaluator."""

from cmj_recovery_dynamics.metrics.provenance import (
    HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE,
    HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE,
)
from cmj_recovery_dynamics.metrics.scoring import compatibility_reanchor_score


def reanchor_historical_score(calibrated_score: float) -> float:
    """Map a preserved calibrated score onto the later progress reference curve."""
    return compatibility_reanchor_score(
        calibrated_score,
        old_reference_progress=HISTORICAL_REANCHOR_OLD_PROGRESS_AT_HALF_SCORE,
        new_reference_progress=HISTORICAL_REANCHOR_NEW_PROGRESS_AT_HALF_SCORE,
    )


__all__ = ["reanchor_historical_score"]
