"""Artifact-specific rights decisions for recovered historical models."""

from __future__ import annotations

from datetime import date
from types import MappingProxyType

from .contracts import (
    ModelArtifactReleaseStatus,
    ModelArtifactRightsDecision,
    ModelDistributionTermsStatus,
    ModelOwnershipStatus,
    OwnerModelAttestation,
    PublicationAuthorityStatus,
)

OWNER_MODEL_ATTESTATION = OwnerModelAttestation(
    "Owner declaration dated 2026-10-22",
    attestation_date=date(2026, 10, 22),
    scope=(
        "The owner independently authored the historical Preseason research models, "
        "trained their checkpoints using data they were entitled to use, did not "
        "produce them as contracted deliverables assigned elsewhere, and retains "
        "publication authority over original research artifacts, explicitly including "
        "Gate7 M0-M8."
    ),
    exclusions=(
        "Apache-2.0 applies to original repository software only; checkpoint weights, "
        "parameter artifacts, and datasets are not assigned that license.",
        "The attestation does not alter White-derived empirical-material restrictions, "
        "confidential third-party data terms, or any other third-party rights decision.",
        "The attestation records ownership and publication authority; it does not "
        "release checkpoint bytes, establish inference qualification, or authorize a "
        "technical integration.",
        "Unrelated artifacts and model identities that cannot be matched to the "
        "attested Preseason scope are excluded.",
    ),
)

_OWNER_SOURCES = (
    OWNER_MODEL_ATTESTATION.reference,
    "RES-545 recovered model inventory and source/result index",
)
_UNRESOLVED_SOURCES = (
    "RES-545 recovered model inventory",
    "RES-362 artifact classification",
)


def _owner_attested(name: str, scope: str, note: str) -> ModelArtifactRightsDecision:
    return ModelArtifactRightsDecision(
        artifact_name=name,
        artifact_scope=scope,
        ownership_status=ModelOwnershipStatus.OWNER_ATTESTED_FIRST_PARTY,
        publication_authority=PublicationAuthorityStatus.OWNER_CONTROL_CONFIRMED,
        distribution_terms=ModelDistributionTermsStatus.OWNER_CONTROLLED_NO_PUBLIC_LICENSE,
        release_status=ModelArtifactReleaseStatus.NOT_RELEASED,
        evidence_sources=_OWNER_SOURCES,
        note=note,
    )


def _unresolved(
    name: str,
    scope: str,
    ownership: ModelOwnershipStatus,
    note: str,
) -> ModelArtifactRightsDecision:
    return ModelArtifactRightsDecision(
        artifact_name=name,
        artifact_scope=scope,
        ownership_status=ownership,
        publication_authority=PublicationAuthorityStatus.NOT_ESTABLISHED,
        distribution_terms=ModelDistributionTermsStatus.UNRESOLVED,
        release_status=ModelArtifactReleaseStatus.PRIVATE_ARCHIVE_ONLY,
        evidence_sources=_UNRESOLVED_SOURCES,
        note=note,
    )


MODEL_ARTIFACT_RIGHTS = (
    *(
        _owner_attested(
            f"Gate7 {candidate}",
            f"Recovered {candidate} candidate, including its recorded repeats.",
            "Owner-attested first-party model. The Gate7 M0 identity remains distinct "
            "from the public initial-preseason M0. Checkpoint files are not released "
            "and no public checkpoint license is assigned.",
        )
        for candidate in ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8")
    ),
    _owner_attested(
        "Initial-preseason public M0 reference",
        "The original public reference model registered separately from Gate7 M0.",
        "Owner-attested first-party model. Its existing public model identity is not "
        "a Gate7 checkpoint alias; no recovered checkpoint bytes or checkpoint license "
        "are added here.",
    ),
    _owner_attested(
        "Gate5 OLS fitted JSON",
        "The recovered fitted two-output linear baseline parameter artifact.",
        "Owner-attested first-party model. RES-362's PUBLIC_CANDIDATE classification "
        "is consistent with owner authority but is not an Apache-2.0 grant for the "
        "fitted parameters. The artifact remains unreleased.",
    ),
    *(
        _owner_attested(
            f"P8L6 {seed}",
            f"Recovered P8L6 neural candidate state for {seed}.",
            "Owner-attested first-party model. The seed's training-contract digest "
            "difference is a technical/comparability limitation, not an ownership "
            "finding. Checkpoint bytes remain unreleased.",
        )
        for seed in ("S00", "S01", "S02")
    ),
    _owner_attested(
        "V3.1 R1-AKN reference ensemble",
        "Recovered five-seed reference ensemble state.",
        "Owner-attested first-party Preseason model. Technical review is partial: "
        "validation data were pooled into final fitting, and no forward inference "
        "was qualified. The artifact remains unreleased.",
    ),
    _owner_attested(
        "V3 strong HistGradientBoosting parameters",
        "Recovered fitted parameter archive.",
        "Owner-attested first-party Preseason model. Safe array parsing did not qualify "
        "inference; the parameter archive remains unreleased.",
    ),
    _owner_attested(
        "V3 strong residual MLP parameters",
        "Recovered five-seed fitted parameter archive.",
        "Owner-attested first-party Preseason model. Safe array parsing did not qualify "
        "inference, and validation data were pooled into final fitting. The archive "
        "remains unreleased.",
    ),
    _owner_attested(
        "Preseason early untuned GBT pickle",
        "Recovered serialized fitted estimator.",
        "Owner-attested model ownership does not make pickle deserialization safe. "
        "The pickle remains unopened and unreleased.",
    ),
    _owner_attested(
        "V3 headroom proof GBT pickle",
        "Recovered serialized fitted estimator from the V3 headroom record.",
        "Owner-attested model ownership does not make pickle deserialization safe. "
        "The pickle remains unopened and unreleased.",
    ),
    _owner_attested(
        "V3 untuned GBT pickle",
        "Recovered serialized fitted estimator.",
        "Owner-attested model ownership does not make pickle deserialization safe. "
        "The pickle remains unopened and unreleased.",
    ),
    _unresolved(
        "SP07 C1 structure-aware distillation parameters",
        "Recovered NPZ parameter archive.",
        ModelOwnershipStatus.IDENTITY_UNRESOLVED,
        "The recovery identifies an SP07 C1 artifact but does not match its author "
        "and task identity to the attested historical Preseason model scope. No "
        "owner authority is inferred; the safe-parsed archive remains private and "
        "has no accepted evaluation binding.",
    ),
    _unresolved(
        "SP07 C1 MLP baseline parameters",
        "Recovered NPZ parameter archive.",
        ModelOwnershipStatus.IDENTITY_UNRESOLVED,
        "The recovery identifies an SP07 C1 artifact but does not match its author "
        "and task identity to the attested historical Preseason model scope. No "
        "owner authority is inferred; the safe-parsed archive remains private and "
        "has no accepted evaluation binding.",
    ),
    _unresolved(
        "SP07 C1 HGB baseline pickle",
        "Recovered serialized fitted estimator.",
        ModelOwnershipStatus.IDENTITY_UNRESOLVED,
        "The recovery identifies an SP07 C1 artifact but does not match its author "
        "and task identity to the attested historical Preseason model scope. The "
        "pickle remains unopened and private.",
    ),
    _unresolved(
        "SP07 C1 untuned GBT pickle",
        "Recovered serialized fitted estimator.",
        ModelOwnershipStatus.IDENTITY_UNRESOLVED,
        "The recovery identifies an SP07 C1 artifact but does not match its author "
        "and task identity to the attested historical Preseason model scope. The "
        "pickle remains unopened and private.",
    ),
    _unresolved(
        "ALI543 G3 frozen surrogate teacher",
        "Recovered joblib teacher reused in a separate attack study.",
        ModelOwnershipStatus.OUTSIDE_ATTESTATION_SCOPE,
        "This separate attack-study teacher is outside the historical Preseason model "
        "attestation. Its joblib serializer remains unopened and the artifact stays "
        "private archive only.",
    ),
    _unresolved(
        "ALI544 G4 synthetic-data attack checkpoints",
        "The recovered checkpoint set for the separate G4 attack study.",
        ModelOwnershipStatus.OUTSIDE_ATTESTATION_SCOPE,
        "These attack-study checkpoints are outside the historical Preseason model "
        "attestation and remain private archive only. Safe weights-only loading was "
        "rejected; no allowlist or unsafe fallback is authorized by this decision.",
    ),
)

_MODEL_ARTIFACT_RIGHTS_BY_NAME = MappingProxyType(
    {decision.artifact_name: decision for decision in MODEL_ARTIFACT_RIGHTS}
)

if len(_MODEL_ARTIFACT_RIGHTS_BY_NAME) != len(MODEL_ARTIFACT_RIGHTS):
    raise ValueError("model artifact rights identities must be unique")


def get_model_artifact_rights(artifact_name: str) -> ModelArtifactRightsDecision:
    """Return one model-artifact ownership, terms, and release decision."""
    return _MODEL_ARTIFACT_RIGHTS_BY_NAME[artifact_name]
