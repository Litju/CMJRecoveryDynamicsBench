"""Non-production evaluation identities needed to bind recovered results."""

from cmj_recovery_dynamics.contracts import MetricCategory, StudyType
from cmj_recovery_dynamics.lineage.contracts import (
    EvaluationBinding,
    EvidenceStatus,
)

EVALUATION_BINDINGS = (
    EvaluationBinding(
        "unresolved_initial_camp_platform_metric",
        MetricCategory.UNIMPLEMENTED_EVALUATION,
        ("initial_preseason_camp_recovery",),
        (),
        False,
        EvidenceStatus.UNKNOWN,
        (
            "Historical initial-camp score identity is unresolved; the "
            "negative conclusion is retained without treating the label "
            "as a recovered scorer."
        ),
    ),
    EvaluationBinding(
        "public_synthetic_dataset_qualification",
        MetricCategory.QUALIFICATION_STATISTIC,
        (
            "initial_preseason_camp_recovery",
            "fixed_mode_discrepancy_recovery",
            "correlated_exposure_recovery",
        ),
        (),
        False,
        EvidenceStatus.DIRECT,
        (
            "Source, support, geometry, measurement, determinism, and "
            "split-disjointness checks; not a prediction score."
        ),
    ),
    EvaluationBinding(
        "rich_history_raw_progress_diagnostic",
        MetricCategory.RESEARCH_DIAGNOSTIC,
        ("rich_history_camp_recovery",),
        (StudyType.PREDICTIVE_HEADROOM, StudyType.RECONSTRUCTABILITY),
        False,
        EvidenceStatus.RECONSTRUCTED,
        (
            "Historical raw-progress output used for headroom and "
            "hidden-bank descriptions; it is not the calibrated "
            "production score."
        ),
    ),
    EvaluationBinding(
        "manufactured_posterior_parameter_point_rmse",
        MetricCategory.RESEARCH_DIAGNOSTIC,
        (),
        (StudyType.SYSTEM_IDENTIFICATION,),
        False,
        EvidenceStatus.DIRECT,
        (
            "Root mean squared error over the four raw statistical "
            "sensitivity coordinates; exact source/result/config "
            "association resolved."
        ),
    ),
    EvaluationBinding(
        "white_waveform_participant_mean_rmse",
        MetricCategory.RESEARCH_DIAGNOSTIC,
        (),
        (StudyType.REAL_DATA_GROUNDING,),
        False,
        EvidenceStatus.DIRECT,
        (
            "Participant-mean waveform RMSE in body-weight units for "
            "the separate empirical waveform task."
        ),
    ),
    EvaluationBinding(
        "owner_program_adjudication",
        MetricCategory.QUALIFICATION_STATISTIC,
        ("fixed_mode_discrepancy_recovery",),
        (),
        False,
        EvidenceStatus.DIRECT,
        (
            "Owner decision applying the frozen study thresholds; "
            "categorical program disposition, not a benchmark score."
        ),
    ),
    EvaluationBinding(
        "real_data_recovery_crosswalk_status",
        MetricCategory.QUALIFICATION_STATISTIC,
        (),
        (StudyType.REAL_DATA_GROUNDING,),
        False,
        EvidenceStatus.UNKNOWN,
        (
            "Whether empirical waveform records can be aligned to the "
            "synthetic recovery target and split; no completed "
            "crosswalk is preserved."
        ),
    ),
)


__all__ = ["EVALUATION_BINDINGS"]
