"""Historical rules and adjudications preserved by M1 evidence."""

from types import MappingProxyType

from cmj_recovery_dynamics.lineage.contracts import ScientificDisposition
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    HistoricalDecisionRule,
    HistoricalGateOutcome,
    HistoricalGateState,
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
    (
        "full multidimensional exposure versus best scalar/learned "
        "one-dimensional exposure relative progress loss"
    ),
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    (
        "Historical SP06 minimum practical separation required for the full multidimensional "
        "exposure representation relative to the best scalar/one-dimensional exposure "
        "representation; its gate outcome did not override the terminal runtime/scorer status."
    ),
    ("ALI-507 final receipt comment 3a075bcb-f4da-4ebb-81b0-63e15f54158a",),
    True,
    True,
)
_FIXED_GATE_SOURCE = (
    "ALI-518 frozen decision criteria",
    "ALI-518-002 result comment 060ee8be-98f8-4152-be0f-b00ff6a1dc26",
)
FIXED_HISTORY_LOSS_RULE = HistoricalDecisionRule(
    "fixed_mode_history_loss_minimum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "relative progress loss when history is removed",
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    "Historical SP08 HISTORY_LOAD_BEARING practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    False,
    paired_uncertainty_requirement=(
        "The frozen protocol requires a paired uncertainty check; its acceptance predicate "
        "is not stated in the preserved public issue or receipt."
    ),
)
FIXED_POPULATION_LEARNING_RULE = HistoricalDecisionRule(
    "fixed_mode_population_learning_minimum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "relative gain of POPULATION_PLUS_HISTORY over HISTORY_ONLY",
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    "Historical SP08 POPULATION_LEARNING_LOAD_BEARING practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    True,
    paired_uncertainty_requirement=(
        "The frozen protocol requires a paired uncertainty check; its acceptance predicate "
        "is not stated in the preserved public issue or receipt."
    ),
)
FIXED_VALIDATION_SUBSTITUTION_RULE = HistoricalDecisionRule(
    "fixed_mode_validation_substitution_maximum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "pooled validation adaptation gain",
    0.10,
    RuleDirection.LESS_THAN,
    "Historical SP08 VALIDATION_SUBSTITUTION practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    False,
)
FIXED_GENERIC_HEADROOM_RULE = HistoricalDecisionRule(
    "fixed_mode_generic_headroom_minimum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "best generic-to-O1 SRE gap",
    0.02,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    "Historical SP08 GENERIC_ML_HEADROOM practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    False,
    paired_uncertainty_requirement=(
        "The receipt preserves the paired 95% BEST_GENERIC_MINUS_O1 CI as gate evidence; "
        "no separate CI acceptance predicate is published."
    ),
)
FIXED_LOCAL_RATIO_RULE = HistoricalDecisionRule(
    "fixed_mode_local_ratio_maximum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "local-to-empirical progress ratio",
    0.90,
    RuleDirection.LESS_THAN_OR_EQUAL,
    "Historical SP08 KNOWN_LAW_LOCAL_RECONSTRUCTABILITY program gate.",
    _FIXED_GATE_SOURCE,
    True,
    True,
    paired_uncertainty_requirement=(
        "The frozen protocol requires a paired-CI check with the <= 0.90 ratio rule; its "
        "acceptance predicate is not stated in the preserved public issue or receipt."
    ),
)
FIXED_STRUCTURED_HEADROOM_RULE = HistoricalDecisionRule(
    "fixed_mode_structured_baseline_headroom_minimum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "structured relative progress loss versus generic MLP",
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    "Historical SP08 STRUCTURED_BASELINE_HEADROOM practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    True,
    paired_uncertainty_requirement=(
        "The receipt states that the wholly negative structured-minus-MLP CI shows the "
        "structured predictor outperformed MLP and removes the required headroom."
    ),
)
FIXED_MULTIDIMENSIONAL_RULE = HistoricalDecisionRule(
    "fixed_mode_multidimensional_advantage_minimum",
    "fixed_mode_completed_headroom_and_reconstruction_study",
    "full-versus-best-learned-1D relative progress loss",
    0.05,
    RuleDirection.GREATER_THAN_OR_EQUAL,
    "Historical SP08 MULTIDIMENSIONAL_LOAD_BEARING practical-effect gate.",
    _FIXED_GATE_SOURCE,
    True,
    True,
    paired_uncertainty_requirement=(
        "The frozen protocol requires a paired-CI direction check with the >= 0.05 "
        "multidimensional rule; its acceptance direction is not stated in the preserved "
        "public issue or receipt."
    ),
)


HISTORICAL_RULES = (
    CORRELATED_RATIO_RULE,
    CORRELATED_SCALAR_RULE,
    FIXED_HISTORY_LOSS_RULE,
    FIXED_POPULATION_LEARNING_RULE,
    FIXED_VALIDATION_SUBSTITUTION_RULE,
    FIXED_GENERIC_HEADROOM_RULE,
    FIXED_LOCAL_RATIO_RULE,
    FIXED_STRUCTURED_HEADROOM_RULE,
    FIXED_MULTIDIMENSIONAL_RULE,
)
RULES_BY_EXPERIMENT = MappingProxyType(
    {
        "correlated_exposure_corrected_survivability": (
            CORRELATED_RATIO_RULE,
            CORRELATED_SCALAR_RULE,
        ),
        "fixed_mode_completed_headroom_and_reconstruction_study": (
            FIXED_HISTORY_LOSS_RULE,
            FIXED_POPULATION_LEARNING_RULE,
            FIXED_VALIDATION_SUBSTITUTION_RULE,
            FIXED_GENERIC_HEADROOM_RULE,
            FIXED_LOCAL_RATIO_RULE,
            FIXED_STRUCTURED_HEADROOM_RULE,
            FIXED_MULTIDIMENSIONAL_RULE,
        ),
        "fixed_mode_owner_pivot_adjudication": (
            FIXED_POPULATION_LEARNING_RULE,
            FIXED_LOCAL_RATIO_RULE,
            FIXED_STRUCTURED_HEADROOM_RULE,
            FIXED_MULTIDIMENSIONAL_RULE,
        ),
    }
)

FIXED_MODE_GATE_OUTCOMES = (
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "PUBLIC_LEARNABILITY",
        HistoricalGateState.PASS,
        (),
        "Progress 0.358693; NEITHER-minus-best-empirical CI [0.368365, 0.390150].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "HISTORY_LOAD_BEARING",
        HistoricalGateState.PASS,
        (FIXED_HISTORY_LOSS_RULE.name,),
        "Relative loss without history 0.326100; NO_HISTORY-minus-FULL CI [0.071064, 0.084184].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "POPULATION_LEARNING_LOAD_BEARING",
        HistoricalGateState.FAIL,
        (FIXED_POPULATION_LEARNING_RULE.name,),
        "Relative gain over HISTORY_ONLY -0.508897; HISTORY_ONLY-minus-FULL SRE CI "
        "[-0.126576, -0.114962].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "VALIDATION_SUBSTITUTION",
        HistoricalGateState.PASS,
        (FIXED_VALIDATION_SUBSTITUTION_RULE.name,),
        "VA2 pooled gain 0.006677 (< 0.10); train-minus-pooled CI [0.001775, 0.002447].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "GENERIC_ML_HEADROOM",
        HistoricalGateState.PASS,
        (FIXED_GENERIC_HEADROOM_RULE.name,),
        "Best generic-to-O1 SRE gap 0.109476; BEST_GENERIC_MINUS_O1 paired CI "
        "[0.102289, 0.116044].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "KNOWN_LAW_LOCAL_RECONSTRUCTABILITY",
        HistoricalGateState.FAIL,
        (FIXED_LOCAL_RATIO_RULE.name,),
        "A3/local-to-empirical progress ratio 0.999835 (> 0.90); paired ratio CI "
        "[0.998542, 1.001165].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "STRUCTURED_BASELINE_HEADROOM",
        HistoricalGateState.FAIL,
        (FIXED_STRUCTURED_HEADROOM_RULE.name,),
        "Structured relative progress loss -0.509146 (< 0.05); structured-minus-MLP "
        "SRE CI [-0.126593, -0.115126]; BEST_STRUCTURED_OVER_FULL ratio CI "
        "[1.475162, 1.545666].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "MULTIDIMENSIONAL_LOAD_BEARING",
        HistoricalGateState.FAIL,
        (FIXED_MULTIDIMENSIONAL_RULE.name,),
        "Full-vs-best-1D relative loss -0.114598 (< 0.05); BEST_1D_MINUS_FULL SRE CI "
        "[-0.034592, -0.020563]; BEST_1D_OVER_FULL ratio CI "
        "[1.086457, 1.145019].",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "SHORTCUT_LEAKAGE",
        HistoricalGateState.PASS,
        (),
        "No exact reversible target feature; no blocking shortcut.",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "SHIFT_SUPPORT",
        HistoricalGateState.PASS,
        (),
        "All current/prior archetypes covered; no exposure support violations; "
        "domain-classifier AUC 0.703496.",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "STATISTICAL_ADEQUACY",
        HistoricalGateState.PASS,
        (),
        "5,000 resamples, 16 camps, all paired intervals finite.",
        _FIXED_GATE_SOURCE,
    ),
    HistoricalGateOutcome(
        "fixed_mode_completed_headroom_and_reconstruction_study",
        "RUNTIME_SEAL",
        HistoricalGateState.PASS,
        (),
        "Invariance and bad-output probes pass; companion-horizon batch attack detected.",
        _FIXED_GATE_SOURCE,
    ),
)
GATE_OUTCOMES_BY_EXPERIMENT = MappingProxyType(
    {"fixed_mode_completed_headroom_and_reconstruction_study": FIXED_MODE_GATE_OUTCOMES}
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
                "Public learnability passed. The completed ALI-518-002 replay failed "
                "population learning load-bearing, known-law local reconstructability, "
                "structured baseline headroom, and multidimensional load-bearing."
            ),
            (
                FIXED_POPULATION_LEARNING_RULE.name,
                FIXED_LOCAL_RATIO_RULE.name,
                FIXED_STRUCTURED_HEADROOM_RULE.name,
                FIXED_MULTIDIMENSIONAL_RULE.name,
            ),
            StudyDecisionOutcome.PROGRAM_PIVOT,
            "PIVOT_TO_SYSTEM_IDENTIFICATION; FORWARD_SYNTHETIC_RECOVERY_REDESIGN=STOP.",
            ScientificDisposition.ACTIVE_CANDIDATE,
            (
                "ALI-518-002 result comment 060ee8be-98f8-4152-be0f-b00ff6a1dc26",
                "ALI-518 owner adjudication comment 7ba831dc-2512-4abd-8012-2f72e88d6dba",
            ),
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


__all__ = [
    "FIXED_MODE_GATE_OUTCOMES",
    "GATE_OUTCOMES_BY_EXPERIMENT",
    "HISTORICAL_RULES",
    "RULES_BY_EXPERIMENT",
    "STUDY_DECISIONS",
]
