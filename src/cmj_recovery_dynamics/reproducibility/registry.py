"""Views that compose M2-M4 authority for public OSS reproductions."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from cmj_recovery_dynamics.contracts import (
    BenchmarkDefinition,
    CalibrationReferenceStatus,
    EvaluationDefinition,
    EvaluationImplementation,
)
from cmj_recovery_dynamics.lineage.registry import get_benchmark_lineage
from cmj_recovery_dynamics.model_reproduction.contracts import (
    EvaluationReproduction,
    ModelUseReproduction,
)
from cmj_recovery_dynamics.model_reproduction.evaluation import EVALUATION_REPRODUCTIONS
from cmj_recovery_dynamics.model_reproduction.registry import (
    get_model_reproduction,
    get_model_use_reproduction,
)
from cmj_recovery_dynamics.registry import BENCHMARK_REGISTRY, EVALUATION_REGISTRY, get_benchmark
from cmj_recovery_dynamics.reproducibility.contracts import (
    ArtifactManifest,
    CalibrationReference,
    DigestReference,
    DigestRole,
    ManifestEntry,
    ManifestKind,
    ProvenanceRecord,
    RunSpec,
    RuntimeFingerprint,
)
from cmj_recovery_dynamics.reproducibility.execution import (
    MetricExecutionBinding,
    ModelExecutionContract,
    PublicDatasetInterface,
    capture_runtime_fingerprint,
    get_metric_implementation,
    get_model_execution_contract,
    get_public_root_authority,
    validate_seed_identity,
)
from cmj_recovery_dynamics.reproducibility.hashing import sha256_bytes, sha256_file
from cmj_recovery_dynamics.reproducibility.manifests import manifest_sha256
from cmj_recovery_dynamics.reproduction.audit import (
    BenchmarkReproductionAudit,
    get_final_reproduction_status,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    BenchmarkReproductionContract,
    MaterializationState,
    ReproductionStatus,
    SplitReproductionAuthority,
    SplitRole,
)
from cmj_recovery_dynamics.reproduction.registry import get_reproduction_contract
from cmj_recovery_dynamics.study_reconstruction.contracts import (
    ExperimentReconstruction,
    StudyReconstruction,
)
from cmj_recovery_dynamics.study_reconstruction.registry import (
    get_experiment_reconstruction,
    get_study_reconstruction,
)

_SOURCE_DIRECTORIES = (
    "benchmarks",
    "dynamics",
    "lineage",
    "metrics",
    "model_reproduction",
    "observations",
    "reproduction",
    "reproducibility",
    "study_reconstruction",
    "tasks",
)
_SOURCE_FILES = (
    "cmj_recovery_dynamics/contracts.py",
    "cmj_recovery_dynamics/registry.py",
    "cmj_recovery_dynamics/provenance/public_roots.py",
)


@dataclass(frozen=True, slots=True)
class HistoricalSplitReference:
    authority: SplitReproductionAuthority
    reference_digest: DigestReference | None

    def __post_init__(self) -> None:
        if self.reference_digest is not None:
            if self.reference_digest.role is not DigestRole.HISTORICAL_REFERENCE:
                raise ValueError("M2 split digests must remain historical references")
            if (
                self.authority.reference_hash is None
                or self.reference_digest.digest != self.authority.reference_hash.digest
            ):
                raise ValueError("historical digest must come directly from M2 split authority")

    @property
    def split_name(self) -> str:
        return self.authority.name

    @property
    def split_role(self) -> SplitRole:
        return self.authority.role

    @property
    def row_count(self) -> int | None:
        return self.authority.rows

    @property
    def planned_row_count(self) -> int | None:
        return self.authority.planned_rows

    @property
    def assignment_status(self) -> ReproductionStatus:
        return self.authority.assignment_status

    @property
    def materialization_state(self) -> MaterializationState:
        return self.authority.materialization_state

    @property
    def materialization_status(self) -> ReproductionStatus:
        return self.authority.materialization_status


@dataclass(frozen=True, slots=True)
class EvaluationExecutionView:
    evaluation: EvaluationDefinition | EvaluationReproduction
    implementation: MetricExecutionBinding | None
    execution_status: str


@dataclass(frozen=True, slots=True)
class ReproducibilityProfile:
    benchmark: BenchmarkDefinition
    reproduction_contract: BenchmarkReproductionContract
    final_reproduction_audit: BenchmarkReproductionAudit
    public_dataset_interface: PublicDatasetInterface
    historical_data_manifest: ArtifactManifest
    historical_splits: tuple[HistoricalSplitReference, ...]
    evaluation_implementations: tuple[EvaluationExecutionView, ...]
    executable_model_uses: tuple[ModelExecutionContract, ...]
    related_studies: tuple[StudyReconstruction, ...]
    related_experiments: tuple[ExperimentReconstruction, ...]


def get_public_dataset_interface(benchmark_name: str) -> PublicDatasetInterface:
    benchmark = get_benchmark(benchmark_name)
    contract = get_reproduction_contract(benchmark_name)
    audit = get_final_reproduction_status(benchmark_name)
    public_splits = tuple(
        split
        for split in contract.splits
        if split.role in {SplitRole.TRAINING, SplitRole.PUBLIC_VALIDATION}
    )
    if tuple(split.name for split in public_splits) != ("training", "public_validation"):
        raise ValueError("M2 must declare exactly training and public-validation public splits")
    lineage = get_benchmark_lineage(benchmark_name)
    dataset = lineage.dataset
    if dataset.generator_identity is None:
        raise ValueError("public benchmark dataset has no registered generator identity")
    public_geometry = tuple(
        split for split in lineage.splits if split.role.value in {"TRAINING", "PUBLIC_VALIDATION"}
    )
    if len(public_geometry) != 2:
        raise ValueError("M4 must preserve geometry for both public splits")
    return PublicDatasetInterface(
        benchmark_name=benchmark.name,
        generator_identity=dataset.generator_identity,
        reproduction_contract=contract,
        reproduction_audit=audit,
        split_authorities=public_splits,
        split_geometry=public_geometry,
        seed_authority=contract.randomness,
        public_root_authority=get_public_root_authority(benchmark_name),
    )


def get_configuration_manifest(benchmark_name: str) -> ArtifactManifest:
    interface = get_public_dataset_interface(benchmark_name)
    entry_identity = f"configuration:{benchmark_name}"
    config_record = {
        "benchmark": benchmark_name,
        "generator_identity": interface.generator_identity,
        "schema_version": 1,
    }
    config_digest = sha256_bytes(
        json.dumps(
            config_record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    return ArtifactManifest(
        ManifestKind.CONFIGURATION,
        (
            ManifestEntry(
                identity=entry_identity,
                digest=config_digest,
                digest_role=DigestRole.OSS_ARTIFACT,
                authority=interface.generator_identity,
            ),
        ),
    )


def get_historical_split_references(benchmark_name: str) -> tuple[HistoricalSplitReference, ...]:
    contract = get_reproduction_contract(benchmark_name)
    return tuple(
        HistoricalSplitReference(
            split,
            None
            if split.reference_hash is None
            else DigestReference(
                split.reference_hash.digest,
                DigestRole.HISTORICAL_REFERENCE,
            ),
        )
        for split in contract.splits
    )


def get_historical_data_manifest(benchmark_name: str) -> ArtifactManifest:
    references = get_historical_split_references(benchmark_name)
    return ArtifactManifest(
        ManifestKind.DATA,
        tuple(
            ManifestEntry(
                identity=f"{benchmark_name}/{item.split_name}",
                digest=item.reference_digest.digest,
                digest_role=DigestRole.HISTORICAL_REFERENCE,
                authority=item.authority.reference_hash.authority,
            )
            for item in references
            if item.reference_digest is not None and item.authority.reference_hash is not None
        ),
    )


def get_source_manifest() -> ArtifactManifest:
    source_root = Path(__file__).resolve().parents[2]
    package_root = source_root / "cmj_recovery_dynamics"
    relative_paths: set[str] = set(_SOURCE_FILES)
    for directory in _SOURCE_DIRECTORIES:
        relative_paths.update(
            path.relative_to(source_root).as_posix()
            for path in (package_root / directory).glob("*.py")
        )
    entries = tuple(
        ManifestEntry(
            identity=f"source:{relative_path}",
            path=relative_path,
            digest=sha256_file(source_root / relative_path),
            digest_role=DigestRole.OSS_ARTIFACT,
            authority="current OSS reproduction source",
            size=(source_root / relative_path).stat().st_size,
        )
        for relative_path in sorted(relative_paths)
    )
    return ArtifactManifest(ManifestKind.SOURCE, entries)


def create_reproduction_spec(
    benchmark_name: str,
    split_name: str,
    *,
    seed: int | str | None = None,
    model_name: str | None = None,
    evaluation_name: str | None = None,
    calibration_reference: CalibrationReference | None = None,
) -> RunSpec:
    interface = get_public_dataset_interface(benchmark_name)
    seed_identity = interface.make_seed_identity(split_name, seed)
    return RunSpec(
        benchmark_name=benchmark_name,
        split_name=split_name,
        configuration_manifest=get_configuration_manifest(benchmark_name),
        seed_identity=seed_identity,
        model_name=model_name,
        evaluation_name=evaluation_name,
        calibration_reference=calibration_reference,
    )


def get_reproducibility_profile(benchmark_name: str) -> ReproducibilityProfile:
    benchmark = get_benchmark(benchmark_name)
    lineage = get_benchmark_lineage(benchmark_name)
    contract = get_reproduction_contract(benchmark_name)
    audit = get_final_reproduction_status(benchmark_name)
    interface = get_public_dataset_interface(benchmark_name)
    evaluation_names = {
        definition.name
        for definition in EVALUATION_REGISTRY.values()
        if benchmark_name in definition.compatible_benchmarks
    }
    evaluation_names.add(benchmark.evaluation_identity.name)
    evaluation_names.update(
        name
        for name, evaluation in EVALUATION_REPRODUCTIONS.items()
        if benchmark_name in evaluation.compatible_benchmarks
    )
    evaluation_views: list[EvaluationExecutionView] = []
    for name in sorted(evaluation_names):
        definition = EVALUATION_REGISTRY.get(name)
        if definition is None:
            evaluation = EVALUATION_REPRODUCTIONS.get(name)
            if evaluation is None:
                continue
            try:
                binding = get_metric_implementation(name)
            except NotImplementedError:
                evaluation_views.append(
                    EvaluationExecutionView(evaluation, None, "no_common_execution_binding")
                )
            else:
                evaluation_views.append(EvaluationExecutionView(evaluation, binding, "implemented"))
            continue
        if definition.implementation_status is EvaluationImplementation.NOT_IMPLEMENTED:
            evaluation_views.append(EvaluationExecutionView(definition, None, "not_implemented"))
        else:
            try:
                binding = get_metric_implementation(name)
            except NotImplementedError:
                evaluation_views.append(
                    EvaluationExecutionView(definition, None, "no_common_execution_binding")
                )
            else:
                evaluation_views.append(EvaluationExecutionView(definition, binding, "implemented"))

    executable_uses: list[ModelExecutionContract] = []
    for family in lineage.models:
        reproduction = get_model_reproduction(family.name)
        for use in reproduction.uses:
            if use.benchmark_name == benchmark_name:
                model_contract = get_model_execution_contract(
                    family.name, benchmark_name, use.experiment.name
                )
                if model_contract.executable:
                    executable_uses.append(model_contract)

    related_studies = tuple(
        get_study_reconstruction(study.study_type.value) for study in lineage.adjacent_studies
    )
    experiment_names = {
        experiment.name for experiment in (*lineage.experiments, *lineage.adjacent_experiments)
    }
    related_experiments: list[ExperimentReconstruction] = []
    for experiment_name in sorted(experiment_names):
        try:
            related_experiments.append(get_experiment_reconstruction(experiment_name))
        except KeyError:
            continue
    return ReproducibilityProfile(
        benchmark=benchmark,
        reproduction_contract=contract,
        final_reproduction_audit=audit,
        public_dataset_interface=interface,
        historical_data_manifest=get_historical_data_manifest(benchmark_name),
        historical_splits=get_historical_split_references(benchmark_name),
        evaluation_implementations=tuple(evaluation_views),
        executable_model_uses=tuple(executable_uses),
        related_studies=related_studies,
        related_experiments=tuple(related_experiments),
    )


def get_reproducibility_profiles() -> tuple[ReproducibilityProfile, ...]:
    return tuple(get_reproducibility_profile(name) for name in BENCHMARK_REGISTRY)


def validate_reproduction_spec(spec: RunSpec) -> None:
    interface = get_public_dataset_interface(spec.benchmark_name)
    interface.split_authority(spec.split_name)
    entry = spec.configuration_manifest
    if entry.kind is not ManifestKind.CONFIGURATION or len(entry.entries) != 1:
        raise ValueError("run specifications require one registered configuration manifest entry")
    config_entry = entry.entries[0]
    if (
        config_entry.identity != f"configuration:{spec.benchmark_name}"
        or config_entry.authority != interface.generator_identity
        or config_entry.digest_role is not DigestRole.OSS_ARTIFACT
    ):
        raise ValueError("configuration manifest does not bind the benchmark generator identity")
    validate_seed_identity(
        interface, interface.split_authority(spec.split_name), spec.seed_identity
    )

    if spec.model_name is not None:
        model = get_model_reproduction(spec.model_name).model_family
        if spec.benchmark_name not in model.applicability.benchmark_names:
            raise ValueError("model is not registered as applicable to this benchmark")
    if spec.evaluation_name is not None:
        definition = EVALUATION_REGISTRY.get(spec.evaluation_name)
        if definition is None:
            try:
                evaluation_authority = EVALUATION_REPRODUCTIONS[spec.evaluation_name]
            except KeyError as exc:
                raise ValueError("evaluation is not registered") from exc
            if spec.benchmark_name not in evaluation_authority.compatible_benchmarks:
                raise ValueError("M3 evaluation is not compatible with this benchmark")
            if evaluation_authority.implementation_id is None:
                raise NotImplementedError("evaluation has no executable implementation")
            if spec.calibration_reference is not None:
                raise ValueError("custom M3 evaluations do not accept calibration references")
        else:
            if spec.benchmark_name not in definition.compatible_benchmarks:
                raise ValueError("evaluation is not registered as compatible with this benchmark")
            if (
                spec.calibration_reference is not None
                and definition.calibration_reference_status
                is not CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
            ):
                raise ValueError("calibration references only bind locked calibrated evaluations")
    elif spec.calibration_reference is not None:
        raise ValueError("calibration reference requires a registered evaluation identity")
    if spec.model_name is not None and spec.evaluation_name is not None:
        model_uses = tuple(
            use
            for use in get_model_reproduction(spec.model_name).uses
            if use.benchmark_name == spec.benchmark_name
        )
        if model_uses and not any(
            spec.evaluation_name in use.evaluation_names for use in model_uses
        ):
            raise ValueError("M3 does not bind this model and evaluation for the benchmark")


def require_executable_configuration(spec: RunSpec) -> None:
    if manifest_sha256(spec.configuration_manifest) != manifest_sha256(
        get_configuration_manifest(spec.benchmark_name)
    ):
        raise NotImplementedError(
            "this generator adapter only executes its registered default config"
        )


def iter_spec_rows(spec: RunSpec, *, limit: int | None = None) -> Iterator[Mapping[str, object]]:
    require_executable_configuration(spec)
    interface = get_public_dataset_interface(spec.benchmark_name)
    return interface.iter_rows(
        spec.split_name,
        seed_identity=spec.seed_identity,
        limit=limit,
    )


def build_provenance_record(
    spec: RunSpec,
    runtime_fingerprint: RuntimeFingerprint | None = None,
    *,
    output_digest: DigestReference | None = None,
) -> ProvenanceRecord:
    model_use: ModelUseReproduction | None = None
    if spec.model_name is not None:
        try:
            model_use = get_model_use_reproduction(spec.model_name, spec.benchmark_name)
        except KeyError:
            model_use = None
    profile = get_reproducibility_profile(spec.benchmark_name)
    return ProvenanceRecord(
        run_spec_sha256=spec.digest,
        source_manifest_sha256=manifest_sha256(get_source_manifest()),
        configuration_manifest_sha256=manifest_sha256(spec.configuration_manifest),
        runtime_fingerprint=runtime_fingerprint or capture_runtime_fingerprint(),
        m2_contract=get_reproduction_contract(spec.benchmark_name),
        m2_audit=get_final_reproduction_status(spec.benchmark_name),
        m3_model_use=model_use,
        m4_study_reconstructions=profile.related_studies,
        m4_experiment_reconstructions=profile.related_experiments,
        output_digest=output_digest,
    )
