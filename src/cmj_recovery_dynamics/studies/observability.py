"""Observability study class without copied results."""

from cmj_recovery_dynamics.contracts import StudyDefinition, StudyType

OBSERVABILITY_STUDY = StudyDefinition(
    name="observability",
    study_type=StudyType.OBSERVABILITY,
    research_question=(
        "Which dynamic states or distinctions can be inferred from the available "
        "measurements and history at the stated observation boundary?"
    ),
)
