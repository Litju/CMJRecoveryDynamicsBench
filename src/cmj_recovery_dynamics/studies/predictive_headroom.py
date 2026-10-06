"""Predictive-headroom study class without copied results."""

from cmj_recovery_dynamics.contracts import StudyDefinition, StudyType

PREDICTIVE_HEADROOM_STUDY = StudyDefinition(
    name="predictive_headroom",
    study_type=StudyType.PREDICTIVE_HEADROOM,
    research_question=(
        "How much predictive performance remains attainable from the declared public "
        "information under a fixed task, benchmark formulation, and evaluation protocol?"
    ),
)
