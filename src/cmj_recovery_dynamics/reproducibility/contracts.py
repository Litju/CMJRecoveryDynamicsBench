"""Immutable publication-safe contracts for new OSS reproduction runs."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING

from cmj_recovery_dynamics.reproducibility.hashing import validate_sha256

if TYPE_CHECKING:
    from cmj_recovery_dynamics.model_reproduction.contracts import ModelUseReproduction
    from cmj_recovery_dynamics.reproduction.audit import BenchmarkReproductionAudit
    from cmj_recovery_dynamics.reproduction.contracts import (
        BenchmarkReproductionContract,
        SplitReproductionAuthority,
    )
    from cmj_recovery_dynamics.study_reconstruction.contracts import (
        ExperimentReconstruction,
        StudyReconstruction,
    )

_PRIVATE_PATH = re.compile(r"(^|[\s=:])(/home/|/Users/|[A-Za-z]:\\)", re.IGNORECASE)
_ABSOLUTE_PATH = re.compile(r"(^|[\s=:])(?:/|~/|[A-Za-z]:[\\/]|\\\\)")


class DigestRole(StrEnum):
    HISTORICAL_REFERENCE = "historical_reference"
    OSS_ARTIFACT = "oss_artifact"
    REPRODUCTION_OUTPUT = "reproduction_output"


class ManifestKind(StrEnum):
    SOURCE = "source"
    DATA = "data"
    CONFIGURATION = "configuration"


@dataclass(frozen=True, slots=True)
class DigestReference:
    digest: str
    role: DigestRole

    def __post_init__(self) -> None:
        validate_sha256(self.digest)
        if type(self.role) is not DigestRole:
            raise TypeError("digest role must be a DigestRole")


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    identity: str
    digest: str
    digest_role: DigestRole
    authority: str
    path: str | None = None
    size: int | None = None

    def __post_init__(self) -> None:
        _validate_public_text(self.identity, "manifest identity")
        _validate_public_text(self.authority, "manifest authority")
        validate_sha256(self.digest)
        if type(self.digest_role) is not DigestRole:
            raise TypeError("manifest digest role must be a DigestRole")
        if self.path is not None:
            _validate_relative_path(self.path)
        if self.size is not None and (type(self.size) is not int or self.size < 0):
            raise ValueError("manifest size must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    kind: ManifestKind
    entries: tuple[ManifestEntry, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not ManifestKind:
            raise TypeError("manifest kind must be a ManifestKind")
        entries = tuple(self.entries)
        if any(type(entry) is not ManifestEntry for entry in entries):
            raise TypeError("manifest entries must be ManifestEntry values")
        if len({entry.identity for entry in entries}) != len(entries):
            raise ValueError("manifest identities must be unique")
        paths = tuple(entry.path for entry in entries if entry.path is not None)
        if len(set(paths)) != len(paths):
            raise ValueError("manifest paths must be unique")
        if self.kind is ManifestKind.SOURCE and any(
            entry.digest_role is not DigestRole.OSS_ARTIFACT for entry in entries
        ):
            raise ValueError("source manifest entries must use the OSS_ARTIFACT digest role")
        if self.kind is ManifestKind.DATA and any(
            entry.digest_role is not DigestRole.HISTORICAL_REFERENCE for entry in entries
        ):
            raise ValueError("historical data manifests must use reference digests")
        if self.kind is ManifestKind.CONFIGURATION and any(
            entry.digest_role is not DigestRole.OSS_ARTIFACT for entry in entries
        ):
            raise ValueError("configuration manifest entries must use the OSS_ARTIFACT role")
        object.__setattr__(
            self,
            "entries",
            tuple(sorted(entries, key=lambda entry: (entry.identity, entry.path or ""))),
        )


def _validate_public_text(value: str, label: str) -> None:
    if not value or "\x00" in value:
        raise ValueError(f"{label} must be a non-empty publication-safe string")
    if _PRIVATE_PATH.search(value) or _ABSOLUTE_PATH.search(value):
        raise ValueError(f"{label} must not expose a private absolute path")


def _validate_relative_path(value: str) -> None:
    if (
        not value
        or "\\" in value
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
    ):
        raise ValueError("manifest paths must be publication-safe relative POSIX paths")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in value.split("/")) or path.as_posix() != value:
        raise ValueError("manifest paths must be normalized and may not escape their root")
    if path.parts and path.parts[0].lower() in {"home", "users", ".ssh", ".aws"}:
        raise ValueError("manifest path may expose a private artifact location")


def manifest_bytes(manifest: ArtifactManifest) -> bytes:
    record = {
        "entries": [
            {
                "authority": entry.authority,
                "digest": entry.digest,
                "digest_role": entry.digest_role.value,
                "identity": entry.identity,
                "path": entry.path,
                "size": entry.size,
            }
            for entry in manifest.entries
        ],
        "kind": manifest.kind.value,
        "schema_version": 1,
    }
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def manifest_sha256(manifest: ArtifactManifest) -> str:
    from cmj_recovery_dynamics.reproducibility.hashing import sha256_bytes

    return sha256_bytes(manifest_bytes(manifest))


class SeedKind(StrEnum):
    HISTORICAL_RECOVERED = "historical_recovered"
    OSS_CLEAN_ROOM = "oss_clean_room"
    CALLER_SUPPLIED_PUBLIC = "caller_supplied_public"


class CalibrationReferenceKind(StrEnum):
    OSS_SUPPLIED = "oss_supplied"


@dataclass(frozen=True, slots=True)
class SeedIdentity:
    kind: SeedKind
    value: int | str | None

    def __post_init__(self) -> None:
        if type(self.kind) is not SeedKind:
            raise TypeError("seed kind must be a SeedKind")
        if self.value is not None:
            if type(self.value) is int:
                return
            if type(self.value) is str:
                _validate_public_text(self.value, "seed identity")
                return
            raise TypeError("seed identity must be an integer, string, or native default")
        if self.kind is not SeedKind.OSS_CLEAN_ROOM:
            raise ValueError("only a clean-room seed may use the native generator default")


@dataclass(frozen=True, slots=True)
class CalibrationReference:
    reference_progress: float
    authority: str
    kind: CalibrationReferenceKind = CalibrationReferenceKind.OSS_SUPPLIED

    def __post_init__(self) -> None:
        if (
            isinstance(self.reference_progress, bool)
            or not math.isfinite(self.reference_progress)
            or not 0.0 < self.reference_progress < 1.0
        ):
            raise ValueError("calibration reference progress must be finite and inside (0, 1)")
        _validate_public_text(self.authority, "calibration authority")
        if type(self.kind) is not CalibrationReferenceKind:
            raise ValueError("calibration references must remain caller-supplied OSS authorities")


@dataclass(frozen=True, slots=True)
class RuntimeFingerprint:
    python_version: str
    python_implementation: str
    os_family: str
    architecture: str
    numpy_version: str
    package_version: str
    accelerator: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "python_version",
            "python_implementation",
            "os_family",
            "architecture",
            "numpy_version",
            "package_version",
        ):
            _validate_public_text(getattr(self, name), name.replace("_", " "))
        if self.accelerator is not None:
            _validate_public_text(self.accelerator, "accelerator description")


@dataclass(frozen=True, slots=True)
class RuntimeAccounting:
    elapsed_seconds: float
    accelerator: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.elapsed_seconds, bool)
            or not math.isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0.0
        ):
            raise ValueError("elapsed runtime must be finite and nonnegative")
        if self.accelerator is not None:
            _validate_public_text(self.accelerator, "runtime accelerator")
        if self.notes is not None:
            _validate_public_text(self.notes, "runtime notes")


@dataclass(frozen=True, slots=True)
class ScalarResultValue:
    value: float
    units: str
    sample_count: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not math.isfinite(self.value):
            raise ValueError("result scalar must be finite")
        _validate_public_text(self.units, "result units")
        _validate_sample_count(self.sample_count)


@dataclass(frozen=True, slots=True)
class IntervalResultValue:
    lower: float
    upper: float
    units: str
    sample_count: int | None = None

    def __post_init__(self) -> None:
        if any(
            isinstance(value, bool) or not math.isfinite(value)
            for value in (self.lower, self.upper)
        ):
            raise ValueError("result interval endpoints must be finite")
        if self.lower > self.upper:
            raise ValueError("result interval endpoints must be ordered")
        _validate_public_text(self.units, "result units")
        _validate_sample_count(self.sample_count)


@dataclass(frozen=True, slots=True)
class ReproductionValue:
    identity: str
    value: ScalarResultValue | IntervalResultValue
    cell_identity: str | None = None

    def __post_init__(self) -> None:
        _validate_public_text(self.identity, "result value identity")
        if self.cell_identity is not None:
            _validate_public_text(self.cell_identity, "result cell identity")


def _validate_sample_count(value: int | None) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("sample count must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    run_spec_sha256: str
    source_manifest_sha256: str
    configuration_manifest_sha256: str
    runtime_fingerprint: RuntimeFingerprint
    m2_contract: BenchmarkReproductionContract
    m2_audit: BenchmarkReproductionAudit
    m3_model_use: ModelUseReproduction | None = None
    m4_study_reconstructions: tuple[StudyReconstruction, ...] = ()
    m4_experiment_reconstructions: tuple[ExperimentReconstruction, ...] = ()
    output_digest: DigestReference | None = None

    def __post_init__(self) -> None:
        validate_sha256(self.run_spec_sha256)
        validate_sha256(self.source_manifest_sha256)
        validate_sha256(self.configuration_manifest_sha256)
        object.__setattr__(self, "m4_study_reconstructions", tuple(self.m4_study_reconstructions))
        object.__setattr__(
            self, "m4_experiment_reconstructions", tuple(self.m4_experiment_reconstructions)
        )
        if self.m2_audit.contract != self.m2_contract:
            raise ValueError(
                "provenance M2 audit must reference the matching reproduction contract"
            )
        if self.output_digest is not None and (
            self.output_digest.role is not DigestRole.REPRODUCTION_OUTPUT
        ):
            raise ValueError("provenance output digest must use the reproduction-output role")


@dataclass(frozen=True, slots=True)
class RunSpec:
    benchmark_name: str
    split_name: str
    configuration_manifest: ArtifactManifest
    seed_identity: SeedIdentity
    model_name: str | None = None
    evaluation_name: str | None = None
    calibration_reference: CalibrationReference | None = None

    def __post_init__(self) -> None:
        from cmj_recovery_dynamics.reproducibility.registry import validate_reproduction_spec

        validate_reproduction_spec(self)

    @property
    def digest(self) -> str:
        from cmj_recovery_dynamics.reproducibility.execution import reproduction_spec_sha256

        return reproduction_spec_sha256(self)

    @property
    def split_authority(self) -> SplitReproductionAuthority:
        from cmj_recovery_dynamics.reproducibility.registry import get_public_dataset_interface

        return get_public_dataset_interface(self.benchmark_name).split_authority(self.split_name)

    def iter_rows(self, *, limit: int | None = None) -> Iterator[Mapping[str, object]]:
        from cmj_recovery_dynamics.reproducibility.registry import iter_spec_rows

        return iter_spec_rows(self, limit=limit)


class ResultOrigin(StrEnum):
    OSS_REPRODUCTION = "oss_reproduction"


@dataclass(frozen=True, slots=True)
class ReproductionResult:
    run_spec: RunSpec
    values: tuple[ReproductionValue, ...]
    provenance: ProvenanceRecord
    runtime: RuntimeAccounting
    origin: ResultOrigin = ResultOrigin.OSS_REPRODUCTION

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))
        if self.origin is not ResultOrigin.OSS_REPRODUCTION:
            raise ValueError("new reproduction results cannot claim historical result identity")
        if not self.values:
            raise ValueError("reproduction result must contain at least one value")
        if len({value.identity for value in self.values}) != len(self.values):
            raise ValueError("result value identities must be unique")
        if self.provenance.run_spec_sha256 != self.run_spec.digest:
            raise ValueError("result provenance must bind the exact run specification")
        if self.provenance.m2_contract.benchmark != self.run_spec.benchmark_name:
            raise ValueError("result provenance M2 contract must match the run benchmark")
        from cmj_recovery_dynamics.reproducibility.manifests import manifest_sha256

        if self.provenance.configuration_manifest_sha256 != manifest_sha256(
            self.run_spec.configuration_manifest
        ):
            raise ValueError("result provenance must bind the exact configuration manifest")
        from cmj_recovery_dynamics.reproducibility.registry import (
            require_executable_configuration,
        )

        require_executable_configuration(self.run_spec)
        if self.run_spec.model_name is not None:
            if self.provenance.m3_model_use is None:
                raise ValueError("model result provenance requires its M3 model-use authority")
            if self.provenance.m3_model_use.model_name != self.run_spec.model_name:
                raise ValueError("result provenance M3 model use must match the run specification")
            if self.provenance.m3_model_use.benchmark_name != self.run_spec.benchmark_name:
                raise ValueError("result provenance M3 use must match the run benchmark")
            from cmj_recovery_dynamics.reproducibility.execution import require_executable_model

            require_executable_model(self.run_spec.model_name, self.run_spec.benchmark_name)
        if self.run_spec.evaluation_name is not None:
            from cmj_recovery_dynamics.reproducibility.execution import (
                MetricBindingStatus,
                get_metric_implementation,
            )

            evaluation = get_metric_implementation(self.run_spec.evaluation_name)
            if evaluation.status is MetricBindingStatus.NATIVE_COMPONENTS:
                raise NotImplementedError(
                    "result cannot claim an evaluation without a common native aggregate"
                )
            if (
                evaluation.requires_calibration_reference
                and self.run_spec.calibration_reference is None
            ):
                raise ValueError(
                    "new results with locked calibrated evaluations require an explicit "
                    "OSS calibration reference"
                )
