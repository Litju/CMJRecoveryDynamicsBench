"""Immutable contracts for evidence-bounded program synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cmj_recovery_dynamics.contracts import ComparabilityStatus
from cmj_recovery_dynamics.lineage.contracts import ModelRole
from cmj_recovery_dynamics.model_reproduction.contracts import (
    ResultReproduction,
    SpecimenModelLadder,
)
from cmj_recovery_dynamics.reproducibility.registry import ReproducibilityProfile
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    ExperimentReconstruction,
    StudyReconstruction,
)


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be an immutable tuple")


class SynthesisAxis(StrEnum):
    PREDICTIVE_PERFORMANCE = "PREDICTIVE_PERFORMANCE"
    SAMPLE_EFFICIENCY = "SAMPLE_EFFICIENCY"
    COMPUTE_EFFICIENCY = "COMPUTE_EFFICIENCY"
    ROBUSTNESS = "ROBUSTNESS"
    OBSERVABILITY_RECONSTRUCTABILITY = "OBSERVABILITY_RECONSTRUCTABILITY"
    TASK_DESIGN_SENSITIVITY = "TASK_DESIGN_SENSITIVITY"
    NEGATIVE_RESULTS = "NEGATIVE_RESULTS"
    STRUCTURED_VS_LEARNED = "STRUCTURED_VS_LEARNED"
    BENCHMARK_QUALITY = "BENCHMARK_QUALITY"


class ConclusionStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_WITH_CAVEAT = "SUPPORTED_WITH_CAVEAT"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SynthesisScope(StrEnum):
    PROGRAM = "PROGRAM"
    BENCHMARK = "BENCHMARK"
    STUDY = "STUDY"
    EXPERIMENT = "EXPERIMENT"


@dataclass(frozen=True, slots=True)
class ModelRoleEvidence:
    model_name: str
    roles: tuple[ModelRole, ...]

    def __post_init__(self) -> None:
        _require_tuple("model roles", self.roles)
        if not self.model_name or not self.roles:
            raise ValueError("model-role evidence needs a model identity and registered roles")
        if len(self.roles) != len(set(self.roles)):
            raise ValueError("model roles must be unique")
        if any(type(role) is not ModelRole for role in self.roles):
            raise TypeError("model-role evidence must use registered ModelRole values")


@dataclass(frozen=True, slots=True)
class ComparativeEvidence:
    """A validated M1 comparison or a proof of shared scoring identity."""

    result_names: tuple[str, ...]
    status: ComparabilityStatus
    comparison_name: str | None = None
    shared_identity: tuple[str, str, str, str] | None = None
    result_statuses: tuple[tuple[str, ComparabilityStatus], ...] = ()

    def __post_init__(self) -> None:
        _require_tuple("comparative result identities", self.result_names)
        _require_tuple("result comparability statuses", self.result_statuses)
        if self.shared_identity is not None:
            _require_tuple("shared scoring identity", self.shared_identity)
        if len(self.result_names) < 2 or len(self.result_names) != len(set(self.result_names)):
            raise ValueError("comparative evidence needs at least two unique result identities")
        if type(self.status) is not ComparabilityStatus:
            raise TypeError("comparability must use the registered ComparabilityStatus enum")
        if self.status in {ComparabilityStatus.NON_COMPARABLE, ComparabilityStatus.UNKNOWN}:
            raise ValueError(
                "non-comparable or unknown results cannot support a quantitative comparison"
            )
        if self.comparison_name is None and self.shared_identity is None:
            raise ValueError(
                "comparative evidence must bind a comparison or shared scoring identity"
            )
        if self.shared_identity is not None and (
            len(self.shared_identity) != 4 or any(not item for item in self.shared_identity)
        ):
            raise ValueError("shared identity must bind experiment, dataset, split, and evaluation")
        if self.result_statuses:
            if any(type(item) is not tuple for item in self.result_statuses):
                raise TypeError("result comparability bindings must be immutable tuples")
            names = tuple(name for name, _ in self.result_statuses)
            if names != self.result_names:
                raise ValueError("result comparability statuses must match the bound result order")
            if any(type(status) is not ComparabilityStatus for _, status in self.result_statuses):
                raise TypeError("result comparability statuses must use the registered enum")
        if (
            self.status is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
            and self.comparison_name is None
            and not any(
                status is ComparabilityStatus.COMPARABLE_WITH_CAVEAT
                for _, status in self.result_statuses
            )
        ):
            raise ValueError("caveated comparisons need a caveated authority binding")


@dataclass(frozen=True, slots=True)
class ScientificSynthesisClaim:
    name: str
    axis: SynthesisAxis
    scope: SynthesisScope
    status: ConclusionStatus
    statement: str
    benchmark_names: tuple[str, ...] = ()
    result_names: tuple[str, ...] = ()
    experiment_names: tuple[str, ...] = ()
    study_names: tuple[str, ...] = ()
    comparison_names: tuple[str, ...] = ()
    comparative_evidence: tuple[ComparativeEvidence, ...] = ()
    model_roles: tuple[ModelRoleEvidence, ...] = ()
    historical_rule_names: tuple[str, ...] = ()
    gate_names: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, value in (
            ("benchmark identities", self.benchmark_names),
            ("result identities", self.result_names),
            ("experiment identities", self.experiment_names),
            ("study identities", self.study_names),
            ("comparison identities", self.comparison_names),
            ("comparative evidence", self.comparative_evidence),
            ("model roles", self.model_roles),
            ("historical rules", self.historical_rule_names),
            ("historical gates", self.gate_names),
            ("limitations", self.limitations),
        ):
            _require_tuple(label, value)
        if not self.name or not self.statement.strip():
            raise ValueError("a synthesis claim needs a unique identity and non-empty statement")
        if type(self.axis) is not SynthesisAxis or type(self.scope) is not SynthesisScope:
            raise TypeError("synthesis axis and scope must use their registered enums")
        if type(self.status) is not ConclusionStatus:
            raise TypeError("synthesis status must use the strict ConclusionStatus enum")
        for label, values in (
            ("benchmark", self.benchmark_names),
            ("result", self.result_names),
            ("experiment", self.experiment_names),
            ("study", self.study_names),
            ("comparison", self.comparison_names),
            ("historical rule", self.historical_rule_names),
            ("gate", self.gate_names),
        ):
            if len(values) != len(set(values)) or any(not value for value in values):
                raise ValueError(f"{label} evidence identities must be unique and non-empty")
        if not any(
            (
                self.benchmark_names,
                self.result_names,
                self.experiment_names,
                self.study_names,
                self.model_roles,
            )
        ):
            raise ValueError("a synthesis claim must bind existing scientific authority")
        if (
            self.status
            in {
                ConclusionStatus.SUPPORTED_WITH_CAVEAT,
                ConclusionStatus.UNRESOLVED,
            }
            and not self.limitations
        ):
            raise ValueError("caveated and unresolved claims must state their limitations")
        if any(not limitation.strip() for limitation in self.limitations):
            raise ValueError("claim limitations must be non-empty")
        if any(
            not set(binding.result_names).issubset(self.result_names)
            for binding in self.comparative_evidence
        ):
            raise ValueError("comparative evidence results must be explicitly bound by the claim")
        if any(
            binding.comparison_name is not None
            and binding.comparison_name not in self.comparison_names
            for binding in self.comparative_evidence
        ):
            raise ValueError("comparative evidence conclusions must be named by the claim")
        if self.scope is SynthesisScope.BENCHMARK and len(self.benchmark_names) != 1:
            raise ValueError("benchmark-scoped claims must bind exactly one benchmark")
        if self.scope is SynthesisScope.STUDY and not self.study_names:
            raise ValueError("study-scoped claims must bind a registered study")
        if self.scope is SynthesisScope.EXPERIMENT and not self.experiment_names:
            raise ValueError("experiment-scoped claims must bind a registered experiment")

    @property
    def model_family_names(self) -> tuple[str, ...]:
        return tuple(item.model_name for item in self.model_roles)


@dataclass(frozen=True, slots=True)
class BenchmarkCharacterization:
    benchmark_name: str
    reproducibility_profile: ReproducibilityProfile
    model_ladder: SpecimenModelLadder
    result_reproductions: tuple[ResultReproduction, ...]
    claim_names: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_tuple("M3 result replays", self.result_reproductions)
        _require_tuple("benchmark claim identities", self.claim_names)
        if self.benchmark_name != self.reproducibility_profile.benchmark.name:
            raise ValueError("benchmark characterization must retain the exact M5 profile identity")
        if self.benchmark_name != self.model_ladder.benchmark_name:
            raise ValueError("benchmark characterization must retain the exact M3 model ladder")
        if any(item.benchmark_name != self.benchmark_name for item in self.result_reproductions):
            raise ValueError("M3 result replays must remain bound to their benchmark")
        if len(self.claim_names) != len(set(self.claim_names)):
            raise ValueError("benchmark claim identities must be unique")


@dataclass(frozen=True, slots=True)
class StudyCharacterization:
    study_name: str
    reconstruction: StudyReconstruction
    experiment_reconstructions: tuple[ExperimentReconstruction, ...]
    claim_names: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_tuple("M4 experiment reconstructions", self.experiment_reconstructions)
        _require_tuple("study claim identities", self.claim_names)
        if self.study_name != self.reconstruction.name:
            raise ValueError("study characterization must preserve the M4 study identity")
        if len(self.claim_names) != len(set(self.claim_names)):
            raise ValueError("study claim identities must be unique")
        if any(
            item.experiment.benchmark_name is not None for item in self.experiment_reconstructions
        ):
            raise ValueError("adjacent-study experiments must remain outside benchmark objects")


@dataclass(frozen=True, slots=True)
class ProgramSynthesis:
    benchmark_names: tuple[str, ...]
    study_names: tuple[str, ...]
    claims: tuple[ScientificSynthesisClaim, ...]

    def __post_init__(self) -> None:
        _require_tuple("program benchmark identities", self.benchmark_names)
        _require_tuple("program study identities", self.study_names)
        _require_tuple("program synthesis claims", self.claims)
        if len(self.benchmark_names) != 8 or len(self.benchmark_names) != len(
            set(self.benchmark_names)
        ):
            raise ValueError("program synthesis must expose exactly eight benchmark identities")
        if not self.claims or len({claim.name for claim in self.claims}) != len(self.claims):
            raise ValueError("program synthesis claim identities must be non-empty and unique")


__all__ = [
    "BenchmarkCharacterization",
    "ComparativeEvidence",
    "ConclusionStatus",
    "ModelRoleEvidence",
    "ProgramSynthesis",
    "ScientificSynthesisClaim",
    "StudyCharacterization",
    "SynthesisAxis",
    "SynthesisScope",
]
