from dataclasses import replace
from datetime import date

import pytest

from cmj_recovery_dynamics.lineage.registry import LINEAGE_REGISTRY
from cmj_recovery_dynamics.model_reproduction import (
    MODEL_ARTIFACT_RIGHTS,
    OWNER_MODEL_ATTESTATION,
    ModelArtifactReleaseStatus,
    ModelArtifactRightsDecision,
    ModelDistributionTermsStatus,
    ModelOwnershipStatus,
    PublicationAuthorityStatus,
    get_model_artifact_rights,
)


def test_owner_attestation_is_dated_scoped_and_excludes_unlicensed_material() -> None:
    assert OWNER_MODEL_ATTESTATION.attestation_date == date(2026, 10, 22)
    assert "Gate7 M0-M8" in OWNER_MODEL_ATTESTATION.scope
    assert any("Apache-2.0" in exclusion for exclusion in OWNER_MODEL_ATTESTATION.exclusions)
    assert any("White-derived" in exclusion for exclusion in OWNER_MODEL_ATTESTATION.exclusions)
    assert any(
        "confidential third-party" in exclusion for exclusion in OWNER_MODEL_ATTESTATION.exclusions
    )


def test_first_party_recovery_rights_are_owner_controlled_not_external_license_review() -> None:
    required_artifacts = {
        *(f"Gate7 M{index}" for index in range(9)),
        "Initial-preseason public M0 reference",
        "Gate5 OLS fitted JSON",
        "P8L6 S00",
        "P8L6 S01",
        "P8L6 S02",
        "V3.1 R1-AKN reference ensemble",
        "V3 strong HistGradientBoosting parameters",
        "V3 strong residual MLP parameters",
        "Preseason early untuned GBT pickle",
        "V3 headroom proof GBT pickle",
        "V3 untuned GBT pickle",
    }
    decisions = {decision.artifact_name: decision for decision in MODEL_ARTIFACT_RIGHTS}
    assert required_artifacts <= decisions.keys()

    for name in required_artifacts:
        decision = decisions[name]
        assert decision.ownership_status is ModelOwnershipStatus.OWNER_ATTESTED_FIRST_PARTY
        assert decision.publication_authority is PublicationAuthorityStatus.OWNER_CONTROL_CONFIRMED
        assert (
            decision.distribution_terms
            is ModelDistributionTermsStatus.OWNER_CONTROLLED_NO_PUBLIC_LICENSE
        )
        assert decision.release_status is ModelArtifactReleaseStatus.NOT_RELEASED


def test_unmatched_and_out_of_scope_models_stay_private_and_fail_closed() -> None:
    unresolved = get_model_artifact_rights("SP07 C1 structure-aware distillation parameters")
    assert unresolved.ownership_status is ModelOwnershipStatus.IDENTITY_UNRESOLVED
    assert unresolved.publication_authority is PublicationAuthorityStatus.NOT_ESTABLISHED
    assert unresolved.distribution_terms is ModelDistributionTermsStatus.UNRESOLVED
    assert unresolved.release_status is ModelArtifactReleaseStatus.PRIVATE_ARCHIVE_ONLY

    g4 = get_model_artifact_rights("ALI544 G4 synthetic-data attack checkpoints")
    assert g4.ownership_status is ModelOwnershipStatus.OUTSIDE_ATTESTATION_SCOPE
    assert g4.release_status is ModelArtifactReleaseStatus.PRIVATE_ARCHIVE_ONLY
    assert "no allowlist or unsafe fallback" in g4.note

    with pytest.raises(ValueError, match="owner publication authority requires"):
        replace(
            unresolved, publication_authority=PublicationAuthorityStatus.OWNER_CONTROL_CONFIRMED
        )


def test_owner_attestation_does_not_clear_white_derived_empirical_material() -> None:
    dataset = LINEAGE_REGISTRY.datasets["restricted_empirical_grounding_source"]
    assert dataset.redistribution.value == "PROHIBITED"

    initial_reference = LINEAGE_REGISTRY.model_families["initial_public_reference_model"]
    assert initial_reference.checkpoint is not None
    assert initial_reference.checkpoint.redistribution.value == "ALLOWED"
    assert initial_reference.checkpoint.rights_decision_reference is not None
    assert "2026-10-22" in initial_reference.checkpoint.rights_decision_reference


def test_model_rights_decision_cannot_restore_blanket_external_review_for_owner_artifact() -> None:
    decision = get_model_artifact_rights("Gate7 M0")
    with pytest.raises(ValueError, match="must not inherit external licensing status"):
        ModelArtifactRightsDecision(
            artifact_name=decision.artifact_name,
            artifact_scope=decision.artifact_scope,
            ownership_status=decision.ownership_status,
            publication_authority=decision.publication_authority,
            distribution_terms=ModelDistributionTermsStatus.UNRESOLVED,
            release_status=decision.release_status,
            evidence_sources=decision.evidence_sources,
            note=decision.note,
        )
