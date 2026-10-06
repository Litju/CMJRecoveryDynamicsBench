"""Recovered information-boundary contracts used by the benchmark formulations."""

from cmj_recovery_dynamics.observations.camp_history import CAMP_HISTORY_OBSERVATION
from cmj_recovery_dynamics.observations.episode_summary import EPISODE_SUMMARY_OBSERVATION
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
    compute_net_impulse,
)
from cmj_recovery_dynamics.observations.rich_monitoring import RICH_MONITORING_OBSERVATION

OBSERVATION_CONTRACTS = (
    CAMP_HISTORY_OBSERVATION,
    RICH_MONITORING_OBSERVATION,
    EPISODE_SUMMARY_OBSERVATION,
    PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION,
)

__all__ = [
    "CAMP_HISTORY_OBSERVATION",
    "EPISODE_SUMMARY_OBSERVATION",
    "OBSERVATION_CONTRACTS",
    "PHASE_CONSISTENT_FORCE_IMPULSE_OBSERVATION",
    "RICH_MONITORING_OBSERVATION",
    "compute_net_impulse",
]
