"""Typed contracts for recovered scientific study classes; no results are reproduced."""

from cmj_recovery_dynamics.studies.observability import OBSERVABILITY_STUDY
from cmj_recovery_dynamics.studies.predictive_headroom import PREDICTIVE_HEADROOM_STUDY
from cmj_recovery_dynamics.studies.real_data_grounding import REAL_DATA_GROUNDING_STUDY
from cmj_recovery_dynamics.studies.reconstructability import RECONSTRUCTABILITY_STUDY
from cmj_recovery_dynamics.studies.system_identification import SYSTEM_IDENTIFICATION_STUDY

STUDY_DEFINITIONS = (
    PREDICTIVE_HEADROOM_STUDY,
    OBSERVABILITY_STUDY,
    RECONSTRUCTABILITY_STUDY,
    SYSTEM_IDENTIFICATION_STUDY,
    REAL_DATA_GROUNDING_STUDY,
)

__all__ = [
    "OBSERVABILITY_STUDY",
    "PREDICTIVE_HEADROOM_STUDY",
    "REAL_DATA_GROUNDING_STUDY",
    "RECONSTRUCTABILITY_STUDY",
    "STUDY_DEFINITIONS",
    "SYSTEM_IDENTIFICATION_STUDY",
]
