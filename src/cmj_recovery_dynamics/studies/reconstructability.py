"""Generator-reconstructability study class without copied results."""

from cmj_recovery_dynamics.contracts import StudyDefinition, StudyType

RECONSTRUCTABILITY_STUDY = StudyDefinition(
    name="reconstructability",
    study_type=StudyType.RECONSTRUCTABILITY,
    research_question=(
        "Can the generating response law or measurement process be reconstructed from the "
        "declared public inputs and observed outputs?"
    ),
)
