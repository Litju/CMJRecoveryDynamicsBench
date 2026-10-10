"""Evidence-bounded scientific synthesis for the recovered program."""

from cmj_recovery_dynamics.synthesis.contracts import (
    BenchmarkCharacterization,
    ComparativeEvidence,
    ConclusionStatus,
    ModelRoleEvidence,
    ProgramSynthesis,
    ScientificSynthesisClaim,
    StudyCharacterization,
    SynthesisAxis,
    SynthesisScope,
)
from cmj_recovery_dynamics.synthesis.registry import (
    BENCHMARK_CHARACTERIZATIONS,
    PROGRAM_SYNTHESIS,
    STUDY_CHARACTERIZATIONS,
    SYNTHESIS_CLAIMS,
    build_comparative_evidence,
    get_benchmark_characterization,
    get_program_synthesis,
    get_study_characterization,
    get_synthesis_claim,
    get_synthesis_claims,
    validate_synthesis_claim,
)

__all__ = [
    "BENCHMARK_CHARACTERIZATIONS",
    "PROGRAM_SYNTHESIS",
    "STUDY_CHARACTERIZATIONS",
    "SYNTHESIS_CLAIMS",
    "BenchmarkCharacterization",
    "ComparativeEvidence",
    "ConclusionStatus",
    "ModelRoleEvidence",
    "ProgramSynthesis",
    "ScientificSynthesisClaim",
    "StudyCharacterization",
    "SynthesisAxis",
    "SynthesisScope",
    "build_comparative_evidence",
    "get_benchmark_characterization",
    "get_program_synthesis",
    "get_study_characterization",
    "get_synthesis_claim",
    "get_synthesis_claims",
    "validate_synthesis_claim",
]
