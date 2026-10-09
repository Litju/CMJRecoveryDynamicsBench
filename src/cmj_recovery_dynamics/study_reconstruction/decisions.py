"""Historical rules and adjudications preserved by M1 evidence."""

from types import MappingProxyType

from cmj_recovery_dynamics.lineage.contracts import ScientificDisposition
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    HistoricalDecisionRule,
    RuleDirection,
    StudyDecision,
    StudyDecisionOutcome,
)

CORRELATED_RATIO_RULE = HistoricalDecisionRule(
    "correlated_local_ratio_maximum",
    "correlated_exposure_corrected_survivability",
    "local-to-empirical progress ratio",
    0.90,
    RuleDirection.LESS_THAN_OR_EQUAL,
    (
        "Historical SP06/A4R falsification gate for local reconstruction against the "
        "empirical frontier. Its gate outcome did not override the terminal runtime/scorer "
        "status."
    ),
    ("ALI-507 final receipt comment 3a075bcb-f4da-4ebb-81b0-63e15f54158a",),
    True,
    True,
)
CORRELATED_SCALAR_RULE = HistoricalDecisionRule(
    "correlated_scalar_progress_minimum",
    "correlated_exposure_corrected_survivability",
    "full-to-best-scalar relative progress loss",
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    (
        "Historical SP06 minimum separation required to retain the full history over "
        "the best scalar predictor; its gate outcome did not override the terminal "
        "runtime/scorer status."
    ),
    ("ALI-507 final receipt comment 3a075bcb-f4da-4ebb-81b0-63e15f54158a",),
    True,
    True,
)
FIXED_LOCAL_RATIO_RULE = HistoricalDecisionRule(
    "fixed_mode_local_ratio_maximum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "local-to-empirical progress ratio",
    0.90,
    RuleDirection.LESS_THAN_OR_EQUAL,
    "Historical SP08 known-law/local-reconstruction program gate used by the owner adjudication.",
    ("ALI-518-002 result comment 060ee8be-98f8-4152-be0f-b00ff6a1dc26",),
    True,
    True,
)


HISTORICAL_RULES = (
    CORRELATED_RATIO_RULE,
    CORRELATED_SCALAR_RULE,
    FIXED_LOCAL_RATIO_RULE,
)
RULES_BY_EXPERIMENT = MappingProxyType(
    {
        "correlated_exposure_corrected_survivability": (
            CORRELATED_RATIO_RULE,
            CORRELATED_SCALAR_RULE,
        ),
        "fixed_mode_completed_headroom_and_reconstruction_study": (FIXED_LOCAL_RATIO_RULE,),
        "fixed_mode_owner_pivot_adjudication": (FIXED_LOCAL_RATIO_RULE,),
    }
)


STUDY_DECISIONS = MappingProxyType(
    {
        "correlated_exposure_corrected_survivability": StudyDecision(
            "correlated_exposure_runtime_terminal_interpretation",
            "correlated_exposure_corrected_survivability",
            (
                "The local/empirical and full-versus-scalar research gates were not satisfied; "
                "the scientific result rows remain available."
            ),
            (CORRELATED_RATIO_RULE.name, CORRELATED_SCALAR_RULE.name),
            StudyDecisionOutcome.RUNTIME_SCORER_REPAIR_REQUIRED,
            "Repair the runtime scorer before any benchmark-level adjudication.",
            None,
            ("ALI-507 final receipt comment 3a075bcb-f4da-4ebb-81b0-63e15f54158a",),
        ),
        "fixed_mode_public_dataset_qualification": StudyDecision(
            "fixed_mode_public_data_qualification_decision",
            "fixed_mode_public_dataset_qualification",
            (
                "The D09 public source and split passed source, support, geometry, "
                "measurement, determinism, and group-disjointness qualification."
            ),
            (),
            StudyDecisionOutcome.SOURCE_DATA_QUALIFIED,
            (
                "Use the qualified public data for the separately reconstructed study; infer "
                "no benchmark performance verdict."
            ),
            None,
            ("RES-366: Candidate H D09 public data qualification",),
        ),
        "fixed_mode_owner_pivot_adjudication": StudyDecision(
            "fixed_mode_owner_program_pivot",
            "fixed_mode_owner_pivot_adjudication",
            (
                "The completed D09 research protocol found local reconstruction at the "
                "empirical frontier and failed historical learnability/headroom gates."
            ),
            (FIXED_LOCAL_RATIO_RULE.name,),
            StudyDecisionOutcome.PROGRAM_PIVOT,
            (
                "Pivot to posterior system-identification research and stop the forward "
                "redesign program."
            ),
            ScientificDisposition.ACTIVE_CANDIDATE,
            ("ALI-518 owner adjudication comment 7ba831dc-2512-4abd-8012-2f72e88d6dba",),
        ),
        "manufactured_parameter_system_identification": StudyDecision(
            "manufactured_sysid_not_ml_task_decision",
            "manufactured_parameter_system_identification",
            (
                "The neural posterior had a worse energy score than the exact analytic "
                "posterior across the configured history regimes in this manufactured inverse "
                "problem."
            ),
            (),
            StudyDecisionOutcome.NOT_ML_TASK,
            (
                "Do not continue the posterior-inference ML proposal on this manufactured "
                "setup; make no recovery-forecasting claim."
            ),
            None,
            ("SYSID-P0 preserved research result and evidence",),
        ),
        "white_waveform_feasibility_boundary": StudyDecision(
            "white_waveform_feasibility_boundary_decision",
            "white_waveform_feasibility_boundary",
            (
                "The ranking was unstable and the preserved terminal interpretation was "
                "insufficient independent N."
            ),
            (),
            StudyDecisionOutcome.NOT_BENCHMARK_VALIDATION,
            (
                "Retain as adjacent empirical waveform feasibility evidence; do not use it to "
                "validate T01/T02 recovery targets."
            ),
            None,
            ("ALI-536 P0C waveform result and receipt", "RES-366: White / real-CMJ boundary"),
        ),
    }
)


__all__ = ["HISTORICAL_RULES", "RULES_BY_EXPERIMENT", "STUDY_DECISIONS"]
