"""System-identification study class without copied results."""

from cmj_recovery_dynamics.contracts import StudyDefinition, StudyType

SYSTEM_IDENTIFICATION_STUDY = StudyDefinition(
    name="system_identification",
    study_type=StudyType.SYSTEM_IDENTIFICATION,
    research_question=(
        "Which response parameters or dynamic laws are identifiable under the specified "
        "exposure design, observation boundary, and noise assumptions?"
    ),
)
