"""M4 study reconstructions derived from the M1 lineage registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cmj_recovery_dynamics.contracts import StudyType
from cmj_recovery_dynamics.lineage.contracts import StudyLineage
from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    ExperimentReconstruction,
    ProtocolCompleteness,
    ResultAuthority,
    ResultAuthorityBinding,
    SourceClosure,
    StudyClassification,
    StudyReconstruction,
)
from cmj_recovery_dynamics.study_reconstruction.decisions import (
    GATE_OUTCOMES_BY_EXPERIMENT,
    HISTORICAL_RULES,
    RULES_BY_EXPERIMENT,
    STUDY_DECISIONS,
)


@dataclass(frozen=True, slots=True)
class _Metadata:
    classification: StudyClassification
    completeness: ProtocolCompleteness
    authority: ResultAuthority
    conclusion: str
    downstream_action: str
    missing: tuple[str, ...] = ()
    source_commit: tuple[str, ...] = ()
    task_tree: tuple[str, ...] = ()
    protocol_source: tuple[str, ...] = ()
    runner_source: tuple[str, ...] = ()
    result_source: tuple[str, ...] = ()
    evaluation_source: tuple[str, ...] = ()
    bootstrap_source: tuple[str, ...] = ()
    environment_runtime_source: tuple[str, ...] = ()


_METADATA: Mapping[str, _Metadata] = MappingProxyType(
    {
        "rich_history_headroom_reconstruction": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.DIRECT_RESULT,
            (
                "Public and original hidden-bank progress results are separate evidence on "
                "different target banks/splits under the same formulation. They are "
                "comparable with caveat, must not be pooled, and do not establish public "
                "recovery of hidden dataset bytes."
            ),
            (
                "Retain the within-formulation headroom result; make no hidden-data recovery "
                "or retirement-cause claim."
            ),
            (
                "Complete model configurations and the hidden-bank bytes are not publicly "
                "established.",
                "Exact historical result commit, task tree, runner, and runtime closure are "
                "not established in the public registry.",
            ),
        ),
        "rich_history_gpu_frontier_reconstruction": _Metadata(
            StudyClassification.AUDIT,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.RECONSTRUCTED_ARITHMETIC,
            (
                "Historical GPU scores are reanchored only through the explicit compatibility "
                "transform; reanchoring is not benchmark scoring or cross-specimen alignment."
            ),
            "Keep reanchored values as compatibility evidence only.",
            (
                (
                    "Exact historical GPU model configuration and an accepted V3 retirement "
                    "decision are unresolved."
                ),
                "The public registry does not bind the exact GPU source commit/task tree or "
                "runner environment.",
            ),
            evaluation_source=("RES-367: explicit piecewise-linear score-reanchoring transform",),
        ),
        "rich_history_final_expert_frontier_protocol": _Metadata(
            StudyClassification.PROPOSED_REDESIGN,
            ProtocolCompleteness.PROTOCOL_ONLY,
            ResultAuthority.PROTOCOL_ONLY,
            (
                "The amended expert-frontier protocol was not run; no amended result or V3 "
                "retirement rationale is established."
            ),
            "Keep the protocol proposed and unrun; do not infer a retirement reason.",
            ("No amended expert result or adjudication exists.",),
        ),
        "phase_consistent_adversarial_survivability": _Metadata(
            StudyClassification.FALSIFIER,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.DIRECT_RESULT,
            (
                "The preserved research SRE6 is negative for the phase-consistent specimen: "
                "ridge outperformed the restricted empirical frontier. This does not "
                "adjudicate later correlated or fixed-mode formulations, and the unknown "
                "frontier architecture remains unknown."
            ),
            (
                "Keep the completed negative result bound to the phase-consistent specimen; "
                "do not generalize its six-cell research score."
            ),
            (
                (
                    "Exact frontier architecture and seed/repetition/bootstrap authority are "
                    "unresolved."
                ),
                "The public source closure does not identify the exact runner/runtime commit "
                "or task tree.",
            ),
        ),
        "correlated_exposure_corrected_survivability": _Metadata(
            StudyClassification.FALSIFIER,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.DIRECT_RESULT,
            (
                "The direct result rows retain the local/frontier ratio, paired SRE6 "
                "interval, and scalar loss below the historical 5% program rule. The terminal "
                "interpretation remains RUNTIME_SCORER_REPAIR_REQUIRED, not benchmark PASS or "
                "FAIL. This specimen is not directly comparable with fixed mode."
            ),
            (
                "Repair the runtime scorer before any benchmark-level adjudication; preserve "
                "the correlated scientific rows."
            ),
            (
                (
                    "Full model configurations and complete row-level SRE6 scores are not "
                    "published in the lineage result registry."
                ),
            ),
            source_commit=("aa04398223b91449956f3b5ec62360d1682eefbc",),
            task_tree=("86719bed657e2a1c23b4d670f70ff0cb5163b8d3",),
            protocol_source=("ALI-507 corrected SP06 protocol; D07 public validation",),
            result_source=("ALI-507 final receipt comment 3a075bcb-f4da-4ebb-81b0-63e15f54158a",),
            evaluation_source=("RES-367: research SRE6 and progress-gate definitions",),
        ),
        "threshold_response_proposed_protocol": _Metadata(
            StudyClassification.PROPOSED_REDESIGN,
            ProtocolCompleteness.PROTOCOL_ONLY,
            ResultAuthority.PROTOCOL_ONLY,
            (
                "The participant-weighted threshold-response design remains a proposed "
                "alternate; no result, acceptance, or rejection adjudication exists."
            ),
            "Retain the proposal as unresolved and unrun.",
            ("Accepted evaluation and acceptance/rejection decision are absent.",),
            source_commit=("059f42ebc7396662dba04f0b0021d834e4e1aa79",),
            task_tree=("d6758ab6f75262121bc6b6df1eb995cb32567386",),
            protocol_source=("SP07 C1 proposed 12-cell protocol; D08 proposed sample",),
        ),
        "threshold_response_implementation_reference_attempt": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.OPERATIONAL_ONLY,
            ResultAuthority.PROTOCOL_ONLY,
            (
                "A reference implementation/training attempt completed, but no accepted "
                "benchmark result or acceptance/rejection adjudication survives."
            ),
            (
                "Preserve the attempt as implementation evidence without accepting or "
                "rejecting the alternate."
            ),
            (
                (
                    "Accepted score and adjudication are absent; later branch drift was not "
                    "reconciled to the frozen protocol."
                ),
            ),
            source_commit=("059f42ebc7396662dba04f0b0021d834e4e1aa79",),
            task_tree=("d6758ab6f75262121bc6b6df1eb995cb32567386",),
            protocol_source=("SP07 C1 implementation/reference attempt; no accepted result",),
        ),
        "fixed_mode_public_dataset_qualification": _Metadata(
            StudyClassification.AUDIT,
            ProtocolCompleteness.COMPLETE,
            ResultAuthority.DIRECT_RESULT,
            (
                "D09 public source/data qualification passed. This is not a scientific "
                "benchmark performance PASS, and no hidden challenge was materialized."
            ),
            "Use the qualified public validation only within its separately reconstructed study.",
            ("No hidden challenge dataset was materialized.",),
            result_source=("RES-366: Candidate H D09 qualification receipt",),
        ),
        "fixed_mode_partial_headroom_attempt": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.OPERATIONAL_ONLY,
            ResultAuthority.PARTIAL_OUTPUT_EXCLUDED,
            (
                "Two result-bearing runtime attempts stopped before final scores, paired "
                "bootstrap, validation substitutions, and scientific adjudication. Partial "
                "outputs do not supply a final study result."
            ),
            "Exclude both partial attempts from the completed-study result set.",
            (
                (
                    "No final score table, bootstrap, validation-substitution audit, or "
                    "scientific adjudication exists for these attempts."
                ),
                "The public lineage does not bind a complete source commit/task tree or "
                "runtime environment for either attempt.",
            ),
            runner_source=("ALI-517 preserved incomplete run-state and attempt records",),
        ),
        "fixed_mode_stopped_replay": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.OPERATIONAL_ONLY,
            ResultAuthority.PARTIAL_OUTPUT_EXCLUDED,
            (
                "This replay was stopped and canceled; it is separate from both the "
                "incomplete ALI-517 runtime attempts and the later completed ALI-518 study."
            ),
            "Keep the stopped replay canceled and exclude it from completed-study results.",
            (
                "No final result table or study decision exists for the stopped replay.",
                "The public lineage does not bind a complete replay commit/task tree or "
                "runtime environment.",
            ),
            runner_source=(
                "ALI-518 attempt 001 stop comment 286b8a52-9db3-443b-82a6-866c6044ca4c",
            ),
        ),
        "fixed_mode_completed_headroom_and_reconstruction_study": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.DIRECT_RESULT,
            (
                "The completed D09 research study records local reconstruction at the "
                "empirical frontier and weaker one-dimensional and generic MLP diagnostics. "
                "Its row-level results and paired-camp protocol are distinct from the earlier "
                "incomplete/stopped attempts; it supports a program pivot, not benchmark "
                "failure."
            ),
            (
                "Retain the completed research result and its historical protocol; keep the "
                "production scorer and expert qualification unresolved."
            ),
            (
                (
                    "Additional model-family rows do not all have public scalar values; "
                    "production scoring remains unimplemented."
                ),
                "The preserved result receipt does not provide a publication-safe runtime "
                "environment manifest.",
            ),
            source_commit=("62eb1d7714a04721429a7f4f385caad745e51c66",),
            task_tree=("d9a12bed9c1ca4bc686bbbab1a06ba125f8b4e6d",),
            protocol_source=("ALI-518-002: D09 public validation; 16 validation camps",),
            runner_source=(
                "ALI-518-002 runner in task tree d9a12bed9c1ca4bc686bbbab1a06ba125f8b4e6d",
            ),
            result_source=("ALI-518-002 result comment 060ee8be-98f8-4152-be0f-b00ff6a1dc26",),
            bootstrap_source=(
                "ALI-518-002: 5,000 paired camp resamples over 16 camps; PCG64 seed 49505000",
            ),
        ),
        "fixed_mode_production_scorer_status": _Metadata(
            StudyClassification.AUDIT,
            ProtocolCompleteness.OPERATIONAL_ONLY,
            ResultAuthority.PROTOCOL_ONLY,
            (
                "The fixed-mode production scorer is unimplemented and blocked; research SRE6 "
                "is not a production benchmark score."
            ),
            "Keep production scoring fail-closed until an accepted scorer exists.",
            ("Accepted production scorer implementation and score are absent.",),
        ),
        "fixed_mode_expert_reference_qualification": _Metadata(
            StudyClassification.PROPOSED_REDESIGN,
            ProtocolCompleteness.PROTOCOL_ONLY,
            ResultAuthority.PROTOCOL_ONLY,
            "The expert/reference qualification was not run and no production expert was trained.",
            "Keep the reference qualification unrun; do not substitute a research attacker.",
            ("No trained production expert/reference or accepted production evaluation exists.",),
        ),
        "fixed_mode_owner_pivot_adjudication": _Metadata(
            StudyClassification.AUDIT,
            ProtocolCompleteness.COMPLETE,
            ResultAuthority.DIRECT_RESULT,
            (
                "The owner decision applies the completed historical research protocol and "
                "pivots the forward program to posterior system identification. It is a "
                "program decision, not benchmark failure; fixed mode remains ACTIVE_CANDIDATE "
                "with benchmark success unresolved."
            ),
            (
                "Pivot to posterior system-identification research and stop the forward "
                "redesign program; do not mark the benchmark or Candidate-H as failed."
            ),
            ("The decision does not supply an accepted production scorer.",),
        ),
        "manufactured_parameter_system_identification": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.COMPLETE,
            ResultAuthority.DIRECT_RESULT,
            (
                "The manufactured four-coordinate posterior study ends NOT_ML_TASK for this "
                "posterior-inference proposal. It is not recovery forecasting and does not "
                "falsify T02 or establish biological validity."
            ),
            "Stop this posterior-inference ML proposal; make no recovery point-forecast claim.",
            (
                (
                    "Some exact training/runtime configuration detail remains outside the "
                    "published result rows."
                ),
                "The public closure does not bind an exact source commit/task tree or execution "
                "environment for the preserved SYSID output.",
            ),
            evaluation_source=("RES-367: posterior energy and raw-coordinate RMSE definitions",),
        ),
        "white_waveform_feasibility_boundary": _Metadata(
            StudyClassification.EXPERIMENT,
            ProtocolCompleteness.PARTIAL,
            ResultAuthority.DIRECT_RESULT,
            (
                "The adjacent White waveform task reports unstable model rankings and "
                "insufficient independent validation N. This is not recovery-benchmark "
                "validation."
            ),
            (
                "Retain only as adjacent waveform feasibility evidence; make no T01/T02 "
                "validity or rights claim."
            ),
            (
                (
                    "No T01/T02 source, split, or scorer crosswalk exists; rights authority "
                    "remains with M7."
                ),
                "The waveform result closure does not establish an exact public run commit or "
                "task tree.",
            ),
            protocol_source=(
                "ALI-536 P0C waveform task: 45 training and 9 public-validation participants",
            ),
            result_source=("ALI-536 P0C waveform result and receipt",),
        ),
        "white_recovery_grounding_crosswalk": _Metadata(
            StudyClassification.AUDIT,
            ProtocolCompleteness.UNKNOWN,
            ResultAuthority.UNKNOWN,
            (
                "No evidence binds the empirical waveform source/split/scorer to the T01/T02 "
                "recovery targets; the crosswalk remains UNKNOWN and NON_COMPARABLE."
            ),
            (
                "Keep real-data recovery grounding unresolved; make no recovery-validation or "
                "rights decision."
            ),
            (
                (
                    "Recovery target mapping, split identity, scorer identity, and rights "
                    "decision remain unresolved."
                ),
            ),
        ),
    }
)


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _make_reconstruction(name: str, metadata: _Metadata) -> ExperimentReconstruction:
    lineage = LINEAGE_REGISTRY.experiment_view(name)
    result_sources = _unique(
        tuple(source for result in lineage.results for source in result.evidence.sources)
    )
    model_sources = _unique(
        tuple(source for model in lineage.models for source in model.evidence.sources)
    )
    decision = STUDY_DECISIONS.get(name)
    source_closure = SourceClosure(
        source_commit=metadata.source_commit,
        task_tree=metadata.task_tree,
        protocol_source=_unique(lineage.experiment.evidence.sources + metadata.protocol_source),
        runner_source=metadata.runner_source,
        model_source=model_sources,
        evaluation_source=metadata.evaluation_source,
        result_source=_unique(result_sources + metadata.result_source),
        decision_source=() if decision is None else decision.source,
        bootstrap_source=metadata.bootstrap_source,
        environment_runtime_source=metadata.environment_runtime_source,
    )
    comparability = tuple(
        comparison
        for comparison in LINEAGE_REGISTRY.comparisons.values()
        if name
        in {
            result.experiment_name
            for result_name in (*comparison.left_result_names, *comparison.right_result_names)
            if (result := LINEAGE_REGISTRY.results.get(result_name)) is not None
        }
    )
    bindings = tuple(
        ResultAuthorityBinding(result.name, metadata.authority) for result in lineage.results
    )
    return ExperimentReconstruction(
        lineage=lineage,
        classification=metadata.classification,
        protocol_completeness=metadata.completeness,
        result_authority=metadata.authority,
        result_authorities=bindings,
        historical_decision_rules=RULES_BY_EXPERIMENT.get(name, ()),
        historical_gate_outcomes=GATE_OUTCOMES_BY_EXPERIMENT.get(name, ()),
        decision=decision,
        conclusion=metadata.conclusion,
        downstream_action=metadata.downstream_action,
        missing_authority=metadata.missing,
        source_closure=source_closure,
        comparability=comparability,
    )


EXPERIMENT_RECONSTRUCTIONS: Mapping[str, ExperimentReconstruction] = MappingProxyType(
    {name: _make_reconstruction(name, metadata) for name, metadata in _METADATA.items()}
)


def _study(
    name: str,
    study_type: StudyType | None,
    question: str,
    experiment_names: tuple[str, ...],
    conclusion: str,
) -> StudyReconstruction:
    lineage: StudyLineage | None = None
    if study_type is not None:
        lineage = LINEAGE_REGISTRY.studies[study_type.value]
    sources = (
        _unique(
            tuple(
                source
                for experiment_name in experiment_names
                for source in EXPERIMENT_RECONSTRUCTIONS[experiment_name].protocol_evidence.sources
            )
        )
        if lineage is None
        else lineage.evidence.sources
    )
    return StudyReconstruction(
        name,
        study_type,
        lineage,
        question,
        experiment_names,
        conclusion,
        sources,
    )


STUDY_RECONSTRUCTIONS: Mapping[str, StudyReconstruction] = MappingProxyType(
    {
        "predictive_headroom": _study(
            "predictive_headroom",
            StudyType.PREDICTIVE_HEADROOM,
            (
                "What structured predictive headroom is visible within each recovered "
                "specimen and evaluation bank?"
            ),
            (
                "rich_history_headroom_reconstruction",
                "rich_history_gpu_frontier_reconstruction",
                "rich_history_final_expert_frontier_protocol",
                "fixed_mode_partial_headroom_attempt",
                "fixed_mode_stopped_replay",
                "fixed_mode_completed_headroom_and_reconstruction_study",
                "fixed_mode_production_scorer_status",
                "fixed_mode_expert_reference_qualification",
            ),
            (
                "Rich-history and fixed-mode headroom remain within-specimen research "
                "evidence; the fixed-mode owner pivot is not benchmark failure."
            ),
        ),
        "observability": _study(
            "observability",
            StudyType.OBSERVABILITY,
            "Which target-relevant distinctions can be inferred from available histories?",
            (
                "phase_consistent_adversarial_survivability",
                "correlated_exposure_corrected_survivability",
                "fixed_mode_completed_headroom_and_reconstruction_study",
            ),
            (
                "These local-history attacks are scored on forecast outcomes and bound "
                "predictive reconstruction risk; they are not direct latent-truth labels or "
                "proof of biological state observability."
            ),
        ),
        "reconstructability": _study(
            "reconstructability",
            StudyType.RECONSTRUCTABILITY,
            "Can preserved public inputs and outputs reconstruct a response or measurement law?",
            (
                "rich_history_headroom_reconstruction",
                "phase_consistent_adversarial_survivability",
                "correlated_exposure_corrected_survivability",
                "fixed_mode_completed_headroom_and_reconstruction_study",
            ),
            (
                "Results stay bound to their own specimen and result authority; correlated "
                "and fixed-mode scores are NON_COMPARABLE."
            ),
        ),
        "falsification": _study(
            "falsification",
            None,
            (
                "Which historical falsification claims survive source, specimen, and "
                "terminal-status reconstruction?"
            ),
            (
                "phase_consistent_adversarial_survivability",
                "correlated_exposure_corrected_survivability",
                "fixed_mode_completed_headroom_and_reconstruction_study",
            ),
            (
                "The phase result is COMPLETED_NEGATIVE on its specimen; correlated "
                "scientific rows survive a runtime-repair terminal status; fixed mode ends in "
                "a program pivot, not benchmark failure."
            ),
        ),
        "system_identification": _study(
            "system_identification",
            StudyType.SYSTEM_IDENTIFICATION,
            (
                "Can a posterior over four statistical sensitivity coordinates be identified "
                "from complete noisy episodes, and does neural amortization improve classical "
                "inference?"
            ),
            ("manufactured_parameter_system_identification",),
            (
                "The manufactured posterior proposal ends NOT_ML_TASK and remains separate "
                "from recovery point forecasting."
            ),
        ),
        "real_data_grounding": _study(
            "real_data_grounding",
            StudyType.REAL_DATA_GROUNDING,
            (
                "Do empirical waveform records bind to recovery histories, splits, and "
                "force/impulse innovation targets?"
            ),
            ("white_waveform_feasibility_boundary", "white_recovery_grounding_crosswalk"),
            (
                "White waveform feasibility is adjacent empirical evidence; the recovery "
                "crosswalk remains UNKNOWN and NON_COMPARABLE."
            ),
        ),
    }
)


def get_experiment_reconstruction(name: str) -> ExperimentReconstruction:
    """Return the M4 reconstruction linked to an M1 experiment identity."""
    return EXPERIMENT_RECONSTRUCTIONS[name]


def get_study_reconstruction(name: str) -> StudyReconstruction:
    """Return a reconstructed M1 study lineage or explicit cross-cutting audit family."""
    return STUDY_RECONSTRUCTIONS[name]


__all__ = [
    "EXPERIMENT_RECONSTRUCTIONS",
    "HISTORICAL_RULES",
    "STUDY_RECONSTRUCTIONS",
    "get_experiment_reconstruction",
    "get_study_reconstruction",
]
