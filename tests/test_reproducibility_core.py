from __future__ import annotations

import json
import socket
from collections.abc import Sequence
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from cmj_recovery_dynamics.contracts import (
    CalibrationReferenceStatus,
    EvaluationImplementation,
    ProductionAcceptance,
)
from cmj_recovery_dynamics.lineage.contracts import SplitRole as LineageSplitRole
from cmj_recovery_dynamics.lineage.registry import get_benchmark_lineage
from cmj_recovery_dynamics.metrics.catalog import ALL_EVALUATION_DEFINITIONS
from cmj_recovery_dynamics.metrics.scoring import (
    BenchmarkScoreResult,
    MetricInputError,
    TargetMetricValue,
)
from cmj_recovery_dynamics.model_reproduction.contracts import (
    CheckpointState,
    ModelConfigurationStatus,
    ModelReproductionStatus,
)
from cmj_recovery_dynamics.model_reproduction.registry import get_model_reproduction
from cmj_recovery_dynamics.provenance.public_roots import get_public_root_authority
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY
from cmj_recovery_dynamics.reproducibility import (
    ArtifactManifest,
    CalibrationReference,
    DigestReference,
    DigestRole,
    IntegrityError,
    IntervalResultValue,
    ManifestEntry,
    ManifestKind,
    ReproductionResult,
    ReproductionValue,
    ResultOrigin,
    RuntimeAccounting,
    RuntimeFingerprint,
    ScalarResultValue,
    SeedIdentity,
    SeedKind,
    build_provenance_record,
    capture_runtime_fingerprint,
    create_reproduction_spec,
    get_configuration_manifest,
    get_historical_data_manifest,
    get_metric_implementation,
    get_model_execution_contract,
    get_public_dataset_interface,
    get_reproducibility_profile,
    get_reproducibility_profiles,
    get_source_manifest,
    manifest_bytes,
    manifest_sha256,
    require_executable_model,
    sha256_bytes,
    sha256_file,
    verify_sha256_bytes,
    verify_sha256_file,
)
from cmj_recovery_dynamics.reproduction.audit import (
    FormulationReproducibility,
    get_final_reproduction_status,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    MaterializationState,
    ReproductionStatus,
    SplitRole,
)
from cmj_recovery_dynamics.reproduction.registry import get_reproduction_contract
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    ProtocolCompleteness,
    ResultAuthority,
)
from cmj_recovery_dynamics.study_reconstruction.registry import get_experiment_reconstruction

_HASH_A = sha256_bytes(b"artifact-a")
_HASH_B = sha256_bytes(b"artifact-b")


def _entry(
    identity: str,
    path: str | None,
    digest: str = _HASH_A,
    role: DigestRole = DigestRole.OSS_ARTIFACT,
) -> ManifestEntry:
    return ManifestEntry(identity, digest, role, "test authority", path)


def _sample_digest(rows: Sequence[object]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=True)
    return sha256_bytes(payload.encode("utf-8"))


def test_sha256_helpers_stream_and_fail_closed(tmp_path: Path) -> None:
    data = b"abc"
    digest = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert sha256_bytes(data) == digest
    assert verify_sha256_bytes(data, digest) == digest
    with pytest.raises(IntegrityError):
        verify_sha256_bytes(data, _HASH_A)
    with pytest.raises(ValueError):
        verify_sha256_bytes(data, "A" * 64)

    path = tmp_path / "large.bin"
    path.write_bytes(b"first chunk" * 200_000)
    file_digest = sha256_file(path)
    assert verify_sha256_file(path, file_digest) == file_digest
    with pytest.raises(IntegrityError):
        verify_sha256_file(path, _HASH_B)
    with pytest.raises(FileNotFoundError):
        sha256_file(tmp_path / "missing.bin")
    with pytest.raises(IsADirectoryError):
        sha256_file(tmp_path)
    with pytest.raises(ValueError):
        verify_sha256_file(path, "abc")


def test_manifests_are_immutable_ordered_versioned_and_role_specific() -> None:
    first = _entry("source:b.py", "b.py")
    second = _entry("source:a.py", "a.py", _HASH_B)
    left = ArtifactManifest(ManifestKind.SOURCE, (first, second))
    right = ArtifactManifest(ManifestKind.SOURCE, (second, first))
    assert left.entries == (second, first)
    assert manifest_bytes(left) == manifest_bytes(right)
    assert manifest_sha256(left) == manifest_sha256(right)
    assert b'"schema_version":1' in manifest_bytes(left)
    assert manifest_bytes(left).endswith(b"}")
    assert b"\n" not in manifest_bytes(left)
    changed = ArtifactManifest(
        ManifestKind.SOURCE,
        (replace(second, authority="changed authority"), first),
    )
    assert manifest_sha256(changed) != manifest_sha256(left)
    with pytest.raises(FrozenInstanceError):
        left.kind = ManifestKind.DATA  # type: ignore[misc]

    historical = ArtifactManifest(
        ManifestKind.DATA,
        (_entry("benchmark/training", None, _HASH_A, DigestRole.HISTORICAL_REFERENCE),),
    )
    assert historical.entries[0].digest_role is DigestRole.HISTORICAL_REFERENCE
    with pytest.raises(ValueError):
        ArtifactManifest(ManifestKind.DATA, (first,))
    with pytest.raises(ValueError):
        ArtifactManifest(
            ManifestKind.SOURCE,
            (_entry("duplicate", "same.py"), _entry("duplicate", "other.py")),
        )
    with pytest.raises(ValueError):
        ArtifactManifest(
            ManifestKind.SOURCE,
            (_entry("first", "same.py"), _entry("second", "same.py")),
        )


@pytest.mark.parametrize(
    "path",
    ("/tmp/private.bin", "../private.bin", "a/../private.bin", "C:\\data\\private.bin"),
)
def test_manifest_paths_reject_escape_and_absolute_forms(path: str) -> None:
    with pytest.raises(ValueError):
        _entry("unsafe", path)


@pytest.mark.parametrize(
    "notes",
    (
        "ran from (/home/litju/private)",
        "artifact='/tmp/private/output'",
        "artifact[C:\\Users\\Julio\\secret]",
        "artifact(C:/Users/Julio/secret)",
        r"source=\\server\share\secret",
        "generated from '~/private/result'",
        "source=file:///home/litju/private",
    ),
)
def test_runtime_notes_reject_embedded_private_paths(notes: str) -> None:
    with pytest.raises(ValueError):
        RuntimeAccounting(1.0, notes=notes)


def test_public_text_contracts_reject_embedded_paths() -> None:
    with pytest.raises(ValueError):
        CalibrationReference(0.5, "source='/Users/alice/private/reference'")
    with pytest.raises(ValueError):
        ManifestEntry(
            "public-source",
            _HASH_A,
            DigestRole.OSS_ARTIFACT,
            "generated from (/var/tmp/private)",
        )
    with pytest.raises(ValueError):
        _entry("artifact='/home/litju/private'", None)
    with pytest.raises(ValueError):
        RuntimeFingerprint("3.12", "CPython", "Linux", "x86_64", "2", "1", "GPU (/tmp/private)")
    with pytest.raises(ValueError):
        SeedIdentity(SeedKind.CALLER_SUPPLIED_PUBLIC, "seed from (/home/litju/private)")
    with pytest.raises(ValueError):
        ReproductionValue("result (/tmp/private)", ScalarResultValue(1.0, "N/kg"))
    with pytest.raises(ValueError):
        ReproductionValue("result", ScalarResultValue(1.0, "N/kg"), "cell (/tmp/private)")


def test_public_urls_and_scientific_slash_text_remain_valid() -> None:
    RuntimeAccounting(
        1.0,
        notes="reference https://github.com/Litju/CMJRecoveryDynamicsBench",
    )
    ManifestEntry(
        "public-source",
        _HASH_A,
        DigestRole.OSS_ARTIFACT,
        "https://example.org/docs/a/b",
    )
    for units in ("N/kg", "m/s", "m/s²", "force/impulse", "H24/H48/H72"):
        ScalarResultValue(1.0, units)
    SeedIdentity(SeedKind.CALLER_SUPPLIED_PUBLIC, "train/public-validation")
    SeedIdentity(SeedKind.CALLER_SUPPLIED_PUBLIC, "doi:10.1234/example")
    SeedIdentity(SeedKind.CALLER_SUPPLIED_PUBLIC, "ratio <= 0.90")


@pytest.mark.parametrize(
    "path", ("metadata/.ssh/id_rsa", "exports/.aws/credentials", "foo/bar/.ssh/key")
)
def test_manifest_paths_reject_sensitive_components_anywhere(path: str) -> None:
    with pytest.raises(ValueError):
        _entry("unsafe", path)


def test_manifest_paths_allow_harmless_ssh_and_aws_names() -> None:
    assert _entry("ssh notes", "docs/ssh_notes.txt").path == "docs/ssh_notes.txt"
    assert _entry("aws report", "reports/aws_summary.py").path == "reports/aws_summary.py"


def test_all_eight_profiles_reference_m2_without_upgrading_authority() -> None:
    profiles = get_reproducibility_profiles()
    assert len(profiles) == 8
    assert len(BENCHMARK_REGISTRY) == 8
    assert {profile.benchmark.name for profile in profiles} == set(BENCHMARK_REGISTRY)

    for profile in profiles:
        name = profile.benchmark.name
        contract = get_reproduction_contract(name)
        assert profile.reproduction_contract is contract
        assert profile.final_reproduction_audit is get_final_reproduction_status(name)
        assert (
            profile.final_reproduction_audit.overall_status is not FormulationReproducibility.EXACT
        )
        split_views = {item.split_name: item for item in profile.historical_splits}
        public_hashes = {item.split_name: item for item in contract.reference_hashes}
        for split_name in ("training", "public_validation"):
            reference = split_views[split_name]
            assert reference.reference_digest is not None
            assert reference.reference_digest.role is DigestRole.HISTORICAL_REFERENCE
            assert reference.reference_digest.digest == public_hashes[split_name].digest
            assert reference.authority.materialization_status is ReproductionStatus.PARTIAL
        assert all(
            entry.digest_role is DigestRole.HISTORICAL_REFERENCE
            for entry in profile.historical_data_manifest.entries
        )

    initial = get_reproducibility_profile("initial_preseason_camp_recovery")
    canonical = get_reproducibility_profile("canonical_preseason_camp_recovery")
    assert initial.final_reproduction_audit.overall_status is (
        FormulationReproducibility.PARTIALLY_REPRODUCIBLE
    )
    assert canonical.final_reproduction_audit.overall_status is (
        FormulationReproducibility.PARTIALLY_REPRODUCIBLE
    )
    assert all(
        split.assignment_status is ReproductionStatus.PARTIAL
        for profile in (initial, canonical)
        for split in profile.historical_splits
        if split.split_role in {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}
    )
    rich = get_reproducibility_profile("rich_history_camp_recovery")
    assert rich.final_reproduction_audit.overall_status is (
        FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
    )
    assert all(
        split.assignment_status is ReproductionStatus.EXACT
        for split in rich.historical_splits
        if split.split_role in {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}
    )

    threshold_hidden = next(
        item
        for item in get_reproducibility_profile("threshold_response_recovery").historical_splits
        if item.split_role is SplitRole.HIDDEN_TEST
    )
    assert threshold_hidden.assignment_status is ReproductionStatus.PARTIAL
    assert threshold_hidden.planned_row_count == 15750
    assert threshold_hidden.materialization_state is MaterializationState.UNKNOWN
    assert threshold_hidden.reference_digest is None
    fixed_hidden = next(
        item
        for item in get_reproducibility_profile("fixed_mode_discrepancy_recovery").historical_splits
        if item.split_role is SplitRole.HIDDEN_TEST
    )
    assert fixed_hidden.materialization_state is MaterializationState.NOT_MATERIALIZED
    assert fixed_hidden.materialization_status is ReproductionStatus.NOT_APPLICABLE
    rich_hidden = next(
        item for item in rich.historical_splits if item.split_role is SplitRole.HIDDEN_TEST
    )
    assert rich_hidden.materialization_state is MaterializationState.NOT_RECOVERED
    assert rich_hidden.reference_digest is None


def test_public_interfaces_are_eight_public_only_m2_and_m4_views() -> None:
    profiles = get_reproducibility_profiles()
    assert len({profile.public_dataset_interface.benchmark_name for profile in profiles}) == 8
    for profile in profiles:
        interface = profile.public_dataset_interface
        assert interface.supported_splits == ("training", "public_validation")
        assert interface.reproduction_contract is profile.reproduction_contract
        assert interface.split_authority("training").role is SplitRole.TRAINING
        assert len(interface.split_geometry) == 2
        assert all(
            split.role in {LineageSplitRole.TRAINING, LineageSplitRole.PUBLIC_VALIDATION}
            for split in interface.split_geometry
        )
        with pytest.raises(ValueError):
            interface.iter_rows("hidden_test")

    fixed = get_public_dataset_interface("fixed_mode_discrepancy_recovery")
    fixed_validation = next(
        split for split in fixed.split_geometry if split.role is LineageSplitRole.PUBLIC_VALIDATION
    )
    assert fixed_validation is next(
        split
        for split in get_benchmark_lineage("fixed_mode_discrepancy_recovery").splits
        if split.role is LineageSplitRole.PUBLIC_VALIDATION
    )
    assert fixed.split_authority("public_validation").assignment_status is (
        get_reproduction_contract("fixed_mode_discrepancy_recovery").splits[1].assignment_status
    )
    rich = get_public_dataset_interface("rich_history_camp_recovery")
    assert rich.split_authority("training").assignment_status is ReproductionStatus.EXACT
    assert (
        rich.reproduction_audit.overall_status
        is FormulationReproducibility.SEMANTICALLY_REPRODUCIBLE
    )

    with pytest.raises(KeyError):
        get_reproducibility_profile("manufactured_parameter_identification_histories")
    with pytest.raises(KeyError):
        get_reproducibility_profile("white_cmj_waveform_grounding_source")
    fixed_profile = get_reproducibility_profile("fixed_mode_discrepancy_recovery")
    related = {
        study.study_type.value for study in fixed_profile.related_studies if study.study_type
    }
    assert {"system_identification", "real_data_grounding"} <= related
    threshold = get_reproducibility_profile("threshold_response_recovery")
    threshold_protocol = next(
        experiment
        for experiment in threshold.related_experiments
        if experiment.experiment.name == "threshold_response_proposed_protocol"
    )
    assert threshold_protocol is get_experiment_reconstruction(
        "threshold_response_proposed_protocol"
    )
    assert threshold_protocol.protocol_completeness is ProtocolCompleteness.PROTOCOL_ONLY
    assert threshold_protocol.result_authority is ResultAuthority.PROTOCOL_ONLY
    fixed_reconstruction = next(
        experiment
        for experiment in fixed_profile.related_experiments
        if experiment.experiment.name == "fixed_mode_completed_headroom_and_reconstruction_study"
    )
    assert fixed_reconstruction.protocol_completeness is ProtocolCompleteness.PARTIAL
    assert fixed_reconstruction.historical_gate_outcomes
    rich_profile = get_reproducibility_profile("rich_history_camp_recovery")
    raw_progress = next(
        view
        for view in rich_profile.evaluation_implementations
        if view.evaluation.name == "rich_history_raw_progress_diagnostic"
    )
    assert raw_progress.execution_status == "implemented"
    assert raw_progress.implementation is not None


def test_public_generation_is_deterministic_seeded_and_bounded() -> None:
    for benchmark_name in BENCHMARK_REGISTRY:
        sample_spec = create_reproduction_spec(benchmark_name, "training")
        sample_rows = list(sample_spec.iter_rows(limit=2))
        repeated_rows = list(sample_spec.iter_rows(limit=2))
        assert len(sample_rows) == 2
        assert _sample_digest(sample_rows) == _sample_digest(repeated_rows)

    first = create_reproduction_spec("preliminary_post_exposure_recovery", "training")
    repeated = create_reproduction_spec("preliminary_post_exposure_recovery", "training")
    changed = create_reproduction_spec(
        "preliminary_post_exposure_recovery", "training", seed="caller-root-2"
    )
    first_rows = list(first.iter_rows(limit=3))
    repeated_rows = list(repeated.iter_rows(limit=3))
    changed_rows = list(changed.iter_rows(limit=3))
    assert _sample_digest(first_rows) == _sample_digest(repeated_rows)
    assert _sample_digest(first_rows) != _sample_digest(changed_rows)
    assert first.seed_identity.kind is SeedKind.OSS_CLEAN_ROOM
    assert first.seed_identity.value == "cmj-v2-oss-clean-room-root"
    assert changed.seed_identity.kind is SeedKind.CALLER_SUPPLIED_PUBLIC

    interface = get_public_dataset_interface("rich_history_camp_recovery")
    historic_seed = interface.make_seed_identity("training", "l05-public-train-v3")
    assert historic_seed.kind is SeedKind.HISTORICAL_RECOVERED
    spec = create_reproduction_spec(
        "rich_history_camp_recovery", "training", seed="l05-public-train-v3"
    )
    assert spec.seed_identity.kind is SeedKind.HISTORICAL_RECOVERED
    with pytest.raises(ValueError):
        replace(spec, seed_identity=SeedIdentity(SeedKind.HISTORICAL_RECOVERED, "not-authorized"))


def test_run_specs_bind_semantic_identity_and_reject_unknown_authority() -> None:
    spec = create_reproduction_spec(
        "initial_preseason_camp_recovery",
        "training",
        model_name="linear_public_baseline",
        evaluation_name="four_cell_training_scale_normalized_rmse_selection_metric",
    )
    assert (
        spec.digest
        == create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "training",
            model_name="linear_public_baseline",
            evaluation_name="four_cell_training_scale_normalized_rmse_selection_metric",
        ).digest
    )
    assert (
        spec.digest
        != create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "training",
            seed=20261008,
            model_name="linear_public_baseline",
            evaluation_name="four_cell_training_scale_normalized_rmse_selection_metric",
        ).digest
    )
    assert (
        spec.digest
        != create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "public_validation",
            model_name="linear_public_baseline",
            evaluation_name="four_cell_training_scale_normalized_rmse_selection_metric",
        ).digest
    )
    assert (
        spec.digest
        != create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "training",
            model_name="initial_public_reference_model",
            evaluation_name="four_cell_training_scale_normalized_rmse_selection_metric",
        ).digest
    )

    changed_entry = replace(
        spec.configuration_manifest.entries[0],
        digest=sha256_bytes(b"changed config"),
    )
    changed_manifest = ArtifactManifest(ManifestKind.CONFIGURATION, (changed_entry,))
    changed_config = replace(spec, configuration_manifest=changed_manifest)
    assert changed_config.digest != spec.digest
    with pytest.raises(NotImplementedError):
        list(changed_config.iter_rows(limit=1))

    calibration = CalibrationReference(0.4, "caller supplied reference")
    locked_a = create_reproduction_spec(
        "initial_preseason_camp_recovery",
        "training",
        evaluation_name="initial_camp_population_normalized_rmse_score",
        calibration_reference=calibration,
    )
    locked_b = create_reproduction_spec(
        "initial_preseason_camp_recovery",
        "training",
        evaluation_name="initial_camp_population_normalized_rmse_score",
        calibration_reference=CalibrationReference(0.5, "caller supplied reference"),
    )
    assert locked_a.digest != locked_b.digest

    with pytest.raises(KeyError):
        create_reproduction_spec("sysid", "training")
    with pytest.raises(ValueError):
        create_reproduction_spec("initial_preseason_camp_recovery", "hidden_test")
    with pytest.raises(KeyError):
        create_reproduction_spec(
            "initial_preseason_camp_recovery", "training", model_name="missing"
        )
    with pytest.raises(ValueError):
        create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "training",
            evaluation_name="missing",
        )
    with pytest.raises(ValueError):
        create_reproduction_spec(
            "initial_preseason_camp_recovery",
            "training",
            evaluation_name="threshold_response_12_cell_normalized_rmse_score",
        )


def test_metric_bindings_reuse_native_code_and_keep_calibration_authority() -> None:
    implemented = tuple(
        definition
        for definition in ALL_EVALUATION_DEFINITIONS
        if definition.implementation_status is EvaluationImplementation.IMPLEMENTED
    )
    assert implemented
    assert all(
        get_metric_implementation(definition.name).implementation_id for definition in implemented
    )

    raw = get_metric_implementation("predictive_progress_over_cell_mean_baseline")
    assert raw.evaluate(0.75) == pytest.approx(0.25)
    initial = get_metric_implementation("initial_camp_population_normalized_rmse_score")
    assert initial.requires_calibration_reference
    assert initial.m3_authority is not None
    assert initial.m3_authority.definition is not None
    assert initial.m3_authority.definition.calibration_reference_status is (
        CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
    )
    with pytest.raises(ValueError, match="explicit OSS calibration"):
        initial.evaluate(())
    score = initial.evaluate(
        (
            TargetMetricValue(
                name="cell",
                value=0.5,
                floor=1.0,
                perfect=0.0,
                weight=1.0,
            ),
        ),
        calibration_reference=CalibrationReference(0.5, "caller supplied reference"),
    )
    assert isinstance(score, BenchmarkScoreResult)
    assert score.score == pytest.approx(0.5)

    proposed = get_metric_implementation("threshold_response_12_cell_normalized_rmse_score")
    assert proposed.evaluation is not None
    assert proposed.evaluation.production_acceptance is ProductionAcceptance.PROPOSED_UNRESOLVED
    with pytest.raises(NotImplementedError):
        get_metric_implementation("preliminary_post_exposure_production_evaluation")

    composite = get_metric_implementation("posterior_marginal_and_joint_coverage")
    assert composite.status.value == "native_components"
    with pytest.raises(NotImplementedError):
        composite.evaluate(())
    raw_rich = get_metric_implementation("rich_history_raw_progress_diagnostic")
    assert raw_rich.evaluation is None
    assert raw_rich.implementation_id == "rich_history_raw_progress"
    with pytest.raises(MetricInputError):
        raw_rich.evaluate(())
    with pytest.raises(NotImplementedError):
        get_metric_implementation("public_synthetic_dataset_qualification")


def test_model_execution_reuses_m3_and_never_loads_private_checkpoints() -> None:
    linear = require_executable_model(
        "linear_public_baseline",
        "initial_preseason_camp_recovery",
        "initial_linear_public_baseline_evaluation",
    )
    assert linear.executable
    assert linear.reproduction.status is ModelReproductionStatus.RESULT_EVIDENCE_ONLY
    assert linear.use is not None
    assert linear.use.implementation_status is ModelReproductionStatus.SEMANTIC_IMPLEMENTATION
    assert linear.use.configuration_status is ModelConfigurationStatus.EXACT

    m0 = require_executable_model(
        "initial_public_reference_model",
        "initial_preseason_camp_recovery",
        "initial_public_reference_selection",
    )
    assert m0.executable
    assert m0.use is not None
    assert m0.use.checkpoint_state is CheckpointState.PRESERVED_PRIVATELY
    assert m0.checkpoint_auto_loaded is False

    zero = require_executable_model(
        "rich_history_zero_baseline",
        "rich_history_camp_recovery",
        "rich_history_headroom_reconstruction",
    )
    assert zero.executable
    assert zero.use is not None
    assert zero.use.implementation_status is ModelReproductionStatus.EXACT_IMPLEMENTATION

    evidence_only = get_model_execution_contract(
        "rich_history_reference_predictor",
        "rich_history_camp_recovery",
        "rich_history_headroom_reconstruction",
    )
    assert evidence_only.reproduction.status is ModelReproductionStatus.RESULT_EVIDENCE_ONLY
    with pytest.raises(ValueError):
        require_executable_model(
            "rich_history_reference_predictor",
            "rich_history_camp_recovery",
            "rich_history_headroom_reconstruction",
        )
    with pytest.raises(ValueError):
        require_executable_model(
            "canonical_campaign_predictor_unresolved",
            "canonical_preseason_camp_recovery",
            "canonical_camp_public_campaign",
        )
    with pytest.raises(KeyError):
        get_model_reproduction("not-a-model")


def test_result_values_provenance_and_runtime_are_typed_and_bound() -> None:
    spec = create_reproduction_spec("initial_preseason_camp_recovery", "training")
    runtime_a = capture_runtime_fingerprint(accelerator="A100")
    runtime_b = capture_runtime_fingerprint(accelerator="CPU")
    assert runtime_a.python_version
    assert runtime_a.python_implementation
    assert runtime_a.os_family
    assert runtime_a.architecture
    assert runtime_a.numpy_version
    assert runtime_a.package_version
    assert not hasattr(runtime_a, "hostname")
    assert not hasattr(runtime_a, "username")
    assert not hasattr(runtime_a, "cwd")
    assert socket.gethostname() not in repr(runtime_a)
    assert RuntimeAccounting(0.0).elapsed_seconds == 0.0
    with pytest.raises(ValueError):
        RuntimeAccounting(-0.1)
    with pytest.raises(ValueError):
        RuntimeAccounting(float("inf"))

    provenance_a = build_provenance_record(spec, runtime_a)
    provenance_b = build_provenance_record(spec, runtime_b)
    assert provenance_a.run_spec_sha256 == provenance_b.run_spec_sha256 == spec.digest
    output = DigestReference(_HASH_B, DigestRole.REPRODUCTION_OUTPUT)
    provenance = build_provenance_record(spec, runtime_a, output_digest=output)
    assert provenance.output_digest is output
    result = ReproductionResult(
        spec,
        (ReproductionValue("rmse", ScalarResultValue(0.25, "m/s", 16)),),
        provenance,
        RuntimeAccounting(1.25),
    )
    assert result.origin is ResultOrigin.OSS_REPRODUCTION
    assert result.run_spec.digest == provenance.run_spec_sha256
    assert result.provenance.m2_audit is get_final_reproduction_status(spec.benchmark_name)
    assert result.run_spec.digest == spec.digest

    with pytest.raises(ValueError):
        ScalarResultValue(float("nan"), "m/s")
    with pytest.raises(ValueError):
        IntervalResultValue(2.0, 1.0, "m/s")
    mismatched = replace(provenance, run_spec_sha256=_HASH_A)
    with pytest.raises(ValueError, match="exact run specification"):
        ReproductionResult(
            spec,
            (ReproductionValue("rmse", ScalarResultValue(0.25, "m/s")),),
            mismatched,
            RuntimeAccounting(1.0),
        )
    assert "HISTORICAL" not in ResultOrigin.__members__

    locked_spec = create_reproduction_spec(
        "initial_preseason_camp_recovery",
        "training",
        evaluation_name="initial_camp_population_normalized_rmse_score",
    )
    with pytest.raises(ValueError, match="OSS calibration"):
        ReproductionResult(
            locked_spec,
            (ReproductionValue("score", ScalarResultValue(0.5, "score")),),
            build_provenance_record(locked_spec),
            RuntimeAccounting(1.0),
        )


def test_runtime_provenance_has_no_private_machine_identity() -> None:
    fingerprint = capture_runtime_fingerprint()
    names = set(RuntimeFingerprint.__dataclass_fields__)
    assert names == {
        "python_version",
        "python_implementation",
        "os_family",
        "architecture",
        "numpy_version",
        "package_version",
        "accelerator",
    }
    assert get_source_manifest().kind is ManifestKind.SOURCE
    assert get_historical_data_manifest("initial_preseason_camp_recovery").kind is (
        ManifestKind.DATA
    )
    assert get_configuration_manifest("initial_preseason_camp_recovery").kind is (
        ManifestKind.CONFIGURATION
    )
    assert fingerprint.os_family == fingerprint.os_family.strip()


def test_source_data_config_and_output_digest_roles_cannot_be_confused() -> None:
    source = get_source_manifest()
    data = get_historical_data_manifest("initial_preseason_camp_recovery")
    config = get_configuration_manifest("initial_preseason_camp_recovery")
    assert source.kind is ManifestKind.SOURCE
    assert data.kind is ManifestKind.DATA
    assert config.kind is ManifestKind.CONFIGURATION
    assert manifest_sha256(source) != manifest_sha256(data)
    assert manifest_sha256(data) != manifest_sha256(config)
    assert manifest_sha256(source) != manifest_sha256(config)
    assert all(entry.digest_role is DigestRole.OSS_ARTIFACT for entry in source.entries)
    assert all(entry.digest_role is DigestRole.HISTORICAL_REFERENCE for entry in data.entries)
    output = DigestReference(_HASH_A, DigestRole.REPRODUCTION_OUTPUT)
    assert output.role is DigestRole.REPRODUCTION_OUTPUT


def test_seed_root_classification_comes_from_existing_public_root_authority() -> None:
    rich = get_public_dataset_interface("rich_history_camp_recovery")
    root = get_public_root_authority("rich_history_camp_recovery")
    assert rich.public_root_authority is root
    assert rich.make_seed_identity("training", root.training_root).kind is (
        SeedKind.HISTORICAL_RECOVERED
    )
    assert rich.make_seed_identity("public_validation", "caller-root").kind is (
        SeedKind.CALLER_SUPPLIED_PUBLIC
    )
    initial = get_public_dataset_interface("initial_preseason_camp_recovery")
    assert initial.make_seed_identity("training", 123).kind is SeedKind.CALLER_SUPPLIED_PUBLIC
    with pytest.raises(TypeError):
        initial.make_seed_identity("training", "a-string-seed")
