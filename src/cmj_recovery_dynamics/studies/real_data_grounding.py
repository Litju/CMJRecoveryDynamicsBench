"""Real-data-grounding study class without copied results."""

from cmj_recovery_dynamics.contracts import StudyDefinition, StudyType

REAL_DATA_GROUNDING_STUDY = StudyDefinition(
    name="real_data_grounding",
    study_type=StudyType.REAL_DATA_GROUNDING,
    research_question=(
        "How do the synthetic outcomes, measurement assumptions, and forecasting claims "
        "relate to available empirical countermovement-jump data?"
    ),
)
