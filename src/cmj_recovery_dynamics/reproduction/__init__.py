"""Per-benchmark reproduction authority and exactness classifications."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from cmj_recovery_dynamics.reproduction.audit import (
    FINAL_REPRODUCTION_STATUS,
    BenchmarkReproductionAudit,
    FormulationReproducibility,
    get_final_reproduction_status,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    BenchmarkReproductionContract,
    CalibrationReferenceStatus,
    EvaluationAuthority,
    EvaluationRole,
    MaterializationState,
    ProductionScorerStatus,
    RandomnessAuthority,
    ReferenceHash,
    ReproductionAuthority,
    ReproductionClaim,
    ReproductionDimension,
    ReproductionStatus,
    SerializationAuthority,
    SplitReproductionAuthority,
    SplitRole,
    SplitUnit,
)
from cmj_recovery_dynamics.reproduction.registry import (
    REPRODUCTION_CONTRACTS,
    get_reproduction_contract,
)

if TYPE_CHECKING:
    from cmj_recovery_dynamics.reproduction.camp_history import (
        OSS_CAMP_REPRODUCTION,
        CampPredictionRow,
        CampReproductionConfig,
        CampSample,
        CampSampleGeometry,
        CampSampleIdentity,
        CampTarget,
        InformationLeakageError,
        generate_camp_sample,
        generate_canonical_camp_sample,
        generate_initial_camp_sample,
        get_camp_reproduction_config,
    )
    from cmj_recovery_dynamics.reproduction.d04_membership import (
        D04MembershipRow,
        d04_membership_fingerprint,
        replay_d04_membership,
    )

_CAMP_HISTORY_EXPORTS = frozenset(
    {
        "OSS_CAMP_REPRODUCTION",
        "CampPredictionRow",
        "CampReproductionConfig",
        "CampSample",
        "CampSampleGeometry",
        "CampSampleIdentity",
        "CampTarget",
        "InformationLeakageError",
        "generate_camp_sample",
        "generate_canonical_camp_sample",
        "generate_initial_camp_sample",
        "get_camp_reproduction_config",
    }
)
_D04_MEMBERSHIP_EXPORTS = frozenset(
    {"D04MembershipRow", "d04_membership_fingerprint", "replay_d04_membership"}
)


def __getattr__(name: str) -> Any:
    if name in _D04_MEMBERSHIP_EXPORTS:
        return getattr(import_module("cmj_recovery_dynamics.reproduction.d04_membership"), name)
    if name in _CAMP_HISTORY_EXPORTS:
        return getattr(import_module("cmj_recovery_dynamics.reproduction.camp_history"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BenchmarkReproductionContract",
    "BenchmarkReproductionAudit",
    "D04MembershipRow",
    "CampPredictionRow",
    "CampReproductionConfig",
    "CampSample",
    "CampSampleGeometry",
    "CampSampleIdentity",
    "CampTarget",
    "CalibrationReferenceStatus",
    "EvaluationAuthority",
    "EvaluationRole",
    "FINAL_REPRODUCTION_STATUS",
    "FormulationReproducibility",
    "MaterializationState",
    "InformationLeakageError",
    "OSS_CAMP_REPRODUCTION",
    "ProductionScorerStatus",
    "RandomnessAuthority",
    "REPRODUCTION_CONTRACTS",
    "ReferenceHash",
    "ReproductionAuthority",
    "ReproductionClaim",
    "ReproductionDimension",
    "ReproductionStatus",
    "SerializationAuthority",
    "SplitReproductionAuthority",
    "SplitRole",
    "SplitUnit",
    "get_reproduction_contract",
    "get_final_reproduction_status",
    "d04_membership_fingerprint",
    "replay_d04_membership",
    "generate_camp_sample",
    "generate_canonical_camp_sample",
    "generate_initial_camp_sample",
    "get_camp_reproduction_config",
]
