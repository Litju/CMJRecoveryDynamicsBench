"""Small adapters over existing public generators, metrics, and model contracts."""

from __future__ import annotations

import json
import math
import platform
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version
from itertools import islice
from typing import TYPE_CHECKING, cast

import numpy as np

from cmj_recovery_dynamics.contracts import (
    EvaluationDefinition,
    EvaluationImplementation,
)
from cmj_recovery_dynamics.lineage.contracts import (
    ModelFamily,
    SplitIdentity,
)
from cmj_recovery_dynamics.metrics import compatibility, probabilistic, scoring
from cmj_recovery_dynamics.model_reproduction.baselines import (
    fit_linear_public_baseline,
    predict_linear_public_baseline,
    predict_reference_m0,
    zero_innovation_prediction,
)
from cmj_recovery_dynamics.model_reproduction.contracts import (
    EvaluationReproduction,
    ModelConfigurationStatus,
    ModelReproduction,
    ModelReproductionStatus,
    ModelUseReproduction,
)
from cmj_recovery_dynamics.model_reproduction.evaluation import get_evaluation_reproduction
from cmj_recovery_dynamics.model_reproduction.registry import (
    get_model_reproduction,
    get_model_use_reproduction,
)
from cmj_recovery_dynamics.provenance.public_roots import (
    PublicRootAuthority,
)
from cmj_recovery_dynamics.provenance.public_roots import (
    get_public_root_authority as _get_public_root_authority,
)
from cmj_recovery_dynamics.reproducibility.contracts import (
    CalibrationReference,
    RunSpec,
    RuntimeFingerprint,
    SeedIdentity,
    SeedKind,
)
from cmj_recovery_dynamics.reproduction.audit import (
    BenchmarkReproductionAudit,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    BenchmarkReproductionContract,
    SplitReproductionAuthority,
    SplitRole,
)

if TYPE_CHECKING:
    from cmj_recovery_dynamics.reproducibility.contracts import (
        IntervalResultValue,
        ScalarResultValue,
    )

type ModelCallable = Callable[..., object] | tuple[Callable[..., object], ...]


@dataclass(frozen=True, slots=True)
class PublicDatasetInterface:
    benchmark_name: str
    generator_identity: str
    reproduction_contract: BenchmarkReproductionContract
    reproduction_audit: BenchmarkReproductionAudit
    split_authorities: tuple[SplitReproductionAuthority, ...]
    seed_authority: object
    public_root_authority: PublicRootAuthority

    @property
    def supported_splits(self) -> tuple[str, ...]:
        return tuple(split.name for split in self.split_authorities)

    split_geometry: tuple[SplitIdentity, ...]

    def split_authority(self, split_name: str) -> SplitReproductionAuthority:
        if split_name not in self.supported_splits:
            raise ValueError("only public training and public-validation splits are supported")
        return next(split for split in self.split_authorities if split.name == split_name)

    def make_seed_identity(self, split_name: str, value: int | str | None = None) -> SeedIdentity:
        authority = self.split_authority(split_name)
        if value is None:
            return SeedIdentity(
                SeedKind.OSS_CLEAN_ROOM,
                _native_default_seed(self.benchmark_name, split_name),
            )
        camp_generator = self.benchmark_name in {
            "initial_preseason_camp_recovery",
            "canonical_preseason_camp_recovery",
        }
        if camp_generator and type(value) is not int:
            raise TypeError("camp-history generators require an integer seed")
        if not camp_generator and type(value) is not str:
            raise TypeError("public-root generators require a string seed")
        if _is_recovered_root(self.public_root_authority, authority, value):
            return SeedIdentity(SeedKind.HISTORICAL_RECOVERED, value)
        return SeedIdentity(SeedKind.CALLER_SUPPLIED_PUBLIC, value)

    def iter_rows(
        self,
        split_name: str,
        *,
        seed_identity: SeedIdentity | None = None,
        limit: int | None = None,
    ) -> Iterator[Mapping[str, object]]:
        authority = self.split_authority(split_name)
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("row limit must be a nonnegative integer")
        seed = seed_identity or self.make_seed_identity(split_name)
        validate_seed_identity(self, authority, seed)
        if limit == 0:
            return iter(())

        if self.benchmark_name in {
            "initial_preseason_camp_recovery",
            "canonical_preseason_camp_recovery",
        }:
            from cmj_recovery_dynamics.reproduction.camp_history import generate_camp_sample

            seed_value = seed.value
            if seed_value is None:
                sample = generate_camp_sample(
                    self.benchmark_name,
                    split_name=split_name,
                    participant_count=_camp_participant_limit(limit, authority),
                )
            else:
                if type(seed_value) is not int:
                    raise TypeError("camp-history generators require an integer seed")
                sample = generate_camp_sample(
                    self.benchmark_name,
                    split_name=split_name,
                    seed=seed_value,
                    participant_count=_camp_participant_limit(limit, authority),
                )
            return iter(_camp_rows(sample, limit))

        if self.benchmark_name == "rich_history_camp_recovery":
            from cmj_recovery_dynamics.reproduction.rich_history import (
                iter_rich_history_public_split,
            )

            native_split = "public_train" if split_name == "training" else "public_validation"
            rows = iter_rich_history_public_split(
                native_split,
                root_seed=cast(str | None, seed.value),
            )
            projected = (_rich_row(row) for row in rows)
            return projected if limit is None else islice(projected, limit)

        if self.benchmark_name in {
            "preliminary_post_exposure_recovery",
            "phase_consistent_post_exposure_recovery",
            "correlated_exposure_recovery",
        }:
            from cmj_recovery_dynamics.reproduction.single_exposure import (
                OSS_ROOT_SEED,
                iter_public_episodes,
                project_episode,
            )

            native_split = "train" if split_name == "training" else "validation"
            root_seed = OSS_ROOT_SEED if seed.value is None else cast("str", seed.value)

            def single_rows() -> Iterator[Mapping[str, object]]:
                source = iter_public_episodes(
                    native_split,
                    benchmark_name=self.benchmark_name,
                    root_seed=root_seed,
                )
                count = 0
                for episode in source:
                    for row in project_episode(episode):
                        yield cast(Mapping[str, object], row)
                        count += 1
                        if limit is not None and count >= limit:
                            return

            return single_rows()

        if self.benchmark_name in {
            "threshold_response_recovery",
            "fixed_mode_discrepancy_recovery",
        }:
            from cmj_recovery_dynamics.reproduction.later_single_exposure import (
                LaterFormulation,
                generate_later_episode,
                project_later_episode,
            )
            from cmj_recovery_dynamics.reproduction.single_exposure import (
                OSS_ROOT_SEED,
                SPLIT_GEOMETRY,
                iter_public_members,
            )

            native_split = "train" if split_name == "training" else "validation"
            root_seed = OSS_ROOT_SEED if seed.value is None else cast("str", seed.value)

            def later_rows() -> Iterator[Mapping[str, object]]:
                count = 0
                for camp_index, participant_index in iter_public_members(native_split):
                    episode = generate_later_episode(
                        benchmark_name=cast(LaterFormulation, self.benchmark_name),
                        split=native_split,
                        camp_index=camp_index,
                        participant_index=participant_index,
                        root_seed=root_seed,
                    )
                    for row in project_later_episode(episode):
                        yield cast(Mapping[str, object], row)
                        count += 1
                        if limit is not None and count >= limit:
                            return

            if native_split not in SPLIT_GEOMETRY:
                raise ValueError("unsupported public split")
            return later_rows()

        raise RuntimeError(f"no public generator adapter for {self.benchmark_name}")


def _camp_participant_limit(limit: int | None, authority: SplitReproductionAuthority) -> int | None:
    if limit is None:
        return None
    from cmj_recovery_dynamics.reproduction.camp_history import (
        ORIGINS_PER_PARTICIPANT,
    )

    if authority.rows is None:
        raise ValueError("camp public split geometry is not established by M2")
    rows_per_participant = ORIGINS_PER_PARTICIPANT * 2
    participants = math.ceil(limit / rows_per_participant)
    return min(authority.rows // rows_per_participant, max(1, participants))


def _native_default_seed(benchmark_name: str, split_name: str) -> int | str:
    if benchmark_name in {
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
    }:
        from cmj_recovery_dynamics.reproduction.camp_history import OSS_SEED

        return OSS_SEED
    if benchmark_name == "rich_history_camp_recovery":
        from cmj_recovery_dynamics.reproduction.rich_history import PUBLIC_SPLITS

        native_split = "public_train" if split_name == "training" else "public_validation"
        return PUBLIC_SPLITS[native_split].root_seed
    from cmj_recovery_dynamics.reproduction.single_exposure import OSS_ROOT_SEED

    return OSS_ROOT_SEED


def _camp_rows(sample: object, limit: int | None) -> Iterator[Mapping[str, object]]:
    from cmj_recovery_dynamics.contracts import OutcomeVariable
    from cmj_recovery_dynamics.reproduction.camp_history import CampSample

    camp_sample = cast(CampSample, sample)
    for index, (row, target) in enumerate(zip(camp_sample.rows, camp_sample.targets, strict=True)):
        if limit is not None and index >= limit:
            return
        yield {
            "query_id": row.query_id,
            "participant_key": row.participant_key,
            "origin_id": row.origin_id,
            "features": row.predictor_features(),
            "label": {
                OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION.value: (
                    target.force_innovation_n_per_kg
                ),
                OutcomeVariable.NET_IMPULSE_INNOVATION.value: target.net_impulse_innovation_m_s,
            },
            "split": camp_sample.split_name,
        }


def _rich_row(row: object) -> Mapping[str, object]:
    from cmj_recovery_dynamics.reproduction.rich_history import RichHistoryRow

    item = cast(RichHistoryRow, row)
    return {
        "participant_key": item.participant_key,
        "origin_key": item.origin_key,
        "query_key": item.query_key,
        "features": item.fields,
        "label": item.labels,
        "split": item.grouping.split,
    }


def _is_recovered_root(
    authority: PublicRootAuthority, split: SplitReproductionAuthority, value: int | str
) -> bool:
    from cmj_recovery_dynamics.reproduction.contracts import ReproductionStatus

    roots = authority
    if roots.status is not ReproductionStatus.EXACT or not isinstance(value, str):
        return False
    if roots.shared_root is not None:
        return value == roots.shared_root
    expected = roots.training_root if split.role is SplitRole.TRAINING else roots.validation_root
    return value == expected


def get_public_root_authority(benchmark_name: str) -> PublicRootAuthority:
    return _get_public_root_authority(benchmark_name)


def validate_seed_identity(
    interface: PublicDatasetInterface, split: SplitReproductionAuthority, seed: SeedIdentity
) -> None:
    if seed.kind is SeedKind.OSS_CLEAN_ROOM:
        if seed.value != _native_default_seed(interface.benchmark_name, split.name):
            raise ValueError("clean-room seed identity must use the native OSS default")
        return
    if seed.value is None:
        raise ValueError("explicit seed identities require a value")
    historical = _is_recovered_root(interface.public_root_authority, split, seed.value)
    if seed.kind is SeedKind.HISTORICAL_RECOVERED and not historical:
        raise ValueError("seed does not match an M2 recovered public-root authority")
    if seed.kind is SeedKind.CALLER_SUPPLIED_PUBLIC and historical:
        raise ValueError("an M2 recovered public root cannot be relabeled as caller supplied")
    if interface.benchmark_name in {
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
    }:
        if type(seed.value) is not int or seed.kind is SeedKind.HISTORICAL_RECOVERED:
            raise TypeError("camp-history seed identity must be an OSS or caller integer seed")
    elif not isinstance(seed.value, str):
        raise TypeError("public-root generators require string seed identities")


class MetricBindingStatus(StrEnum):
    NATIVE = "native"
    NATIVE_COMPONENTS = "native_components"


@dataclass(frozen=True, slots=True)
class MetricExecutionBinding:
    evaluation: EvaluationDefinition | None
    implementation: ModelCallable
    status: MetricBindingStatus
    m3_authority: EvaluationReproduction | None = None

    @property
    def implementation_id(self) -> str:
        implementation_id = (
            self.evaluation.implementation_id
            if self.evaluation is not None
            else None
            if self.m3_authority is None
            else self.m3_authority.implementation_id
        )
        if implementation_id is None:
            raise ValueError("implemented evaluation has no implementation identity")
        return implementation_id

    @property
    def evaluation_name(self) -> str:
        if self.evaluation is not None:
            return self.evaluation.name
        if self.m3_authority is None:
            raise ValueError("custom metric binding requires M3 evaluation authority")
        return self.m3_authority.name

    @property
    def requires_calibration_reference(self) -> bool:
        from cmj_recovery_dynamics.contracts import CalibrationReferenceStatus

        return self.evaluation is not None and (
            self.evaluation.calibration_reference_status
            is CalibrationReferenceStatus.LOCKED_VALUE_NOT_PUBLIC
        )

    def evaluate(
        self,
        *args: object,
        calibration_reference: CalibrationReference | None = None,
        **kwargs: object,
    ) -> object:
        if (
            self.evaluation is not None
            and self.evaluation.implementation_status is EvaluationImplementation.NOT_IMPLEMENTED
        ):
            raise NotImplementedError(f"evaluation is not implemented: {self.evaluation.name}")
        if isinstance(self.implementation, tuple):
            raise NotImplementedError(
                f"{self.evaluation_name} exposes native components without a common aggregate call"
            )
        call_kwargs = dict(kwargs)
        if self.requires_calibration_reference:
            if calibration_reference is None:
                raise ValueError(
                    "locked historical calibration is unavailable; supply an explicit "
                    "OSS calibration reference"
                )
            if self.implementation_id == "cellwise_normalized_rmse_then_calibrated_benchmark_score":
                if self.evaluation is None:
                    raise ValueError("threshold scorer definition is unavailable")
                call_kwargs.setdefault("expected_cells", self.evaluation.scoring_cells)
                if self.evaluation.normalization_floor is None:
                    raise ValueError("registered scorer normalization floor is unavailable")
                call_kwargs.setdefault("normalization_floor", self.evaluation.normalization_floor)
            call_kwargs["reference_progress"] = calibration_reference.reference_progress
        return self.implementation(*args, **call_kwargs)


def _metric_implementations() -> dict[str, ModelCallable]:
    return {
        "calibrated_benchmark_score": scoring.calibrated_benchmark_score,
        "rich_history_target_metrics_then_calibrated_benchmark_score": (
            scoring.rich_history_benchmark_score
        ),
        "rich_history_raw_progress": scoring.rich_history_raw_progress,
        "cellwise_normalized_rmse_then_calibrated_benchmark_score": (scoring.point_benchmark_score),
        "mean_cellwise_normalized_rmse": scoring.mean_cellwise_normalized_rmse,
        "predictive_progress": scoring.predictive_progress,
        "progress_ratio": scoring.progress_ratio,
        "relative_progress_loss": scoring.relative_progress_loss,
        "relative_progress_gain": scoring.relative_progress_gain,
        "mean_training_scale_normalized_rmse_and_two_seed_mean": (
            scoring.mean_training_scale_normalized_rmse,
            scoring.two_seed_mean,
        ),
        "mean_standardized_euclidean_error": probabilistic.mean_standardized_euclidean_error,
        "empirical_energy_score": probabilistic.empirical_energy_score,
        "mean_prior_whitened_energy_score": probabilistic.mean_prior_whitened_energy_score,
        "paired_score_difference": probabilistic.paired_score_difference,
        "prior_whitened_energy_score_regret": probabilistic.prior_whitened_energy_score_regret,
        "mean_prior_whitened_variogram_score": (probabilistic.mean_prior_whitened_variogram_score),
        "prior_whitened_variogram_score_regret": (
            probabilistic.prior_whitened_variogram_score_regret
        ),
        "parameter_root_mean_square_error": probabilistic.parameter_root_mean_square_error,
        "gaussian_kl_divergence": probabilistic.gaussian_kl_divergence,
        "marginal_interval_coverage_and_joint_ellipsoid_coverage": (
            probabilistic.marginal_interval_coverage,
            probabilistic.joint_ellipsoid_coverage,
        ),
        "normal_standardized_residual_diagnostics": (
            probabilistic.normal_standardized_residual_diagnostics
        ),
        "validate_two_target_covariance_and_mahalanobis_squared": (
            probabilistic.validate_two_target_covariance,
            probabilistic.mahalanobis_squared,
        ),
        "posterior_trace_ratio": probabilistic.posterior_trace_ratio,
        "binary_auc_and_mean_fold_auc": (probabilistic.binary_auc, probabilistic.mean_fold_auc),
        "compatibility_reanchor_score": compatibility.reanchor_historical_score,
    }


def get_metric_implementation(evaluation_name: str) -> MetricExecutionBinding:
    from cmj_recovery_dynamics.registry import EVALUATION_REGISTRY

    definition = EVALUATION_REGISTRY.get(evaluation_name)
    if (
        definition is not None
        and definition.implementation_status is EvaluationImplementation.NOT_IMPLEMENTED
    ):
        raise NotImplementedError(f"evaluation is not implemented: {evaluation_name}")
    try:
        reproduction = get_evaluation_reproduction(evaluation_name)
    except KeyError:
        if definition is None:
            raise
        reproduction = None
    if definition is None:
        if reproduction is None:
            raise KeyError(evaluation_name)
        implementation_id = reproduction.implementation_id
    else:
        implementation_id = definition.implementation_id
    if reproduction is not None and reproduction.implementation_id != implementation_id:
        raise RuntimeError("M3 evaluation authority differs from the registered definition")
    if implementation_id is None:
        raise NotImplementedError(f"evaluation has no native implementation: {evaluation_name}")
    try:
        implementation = _metric_implementations()[implementation_id]
    except KeyError as exc:
        raise NotImplementedError(f"no native execution binding for {implementation_id}") from exc
    status = (
        MetricBindingStatus.NATIVE_COMPONENTS
        if isinstance(implementation, tuple)
        else MetricBindingStatus.NATIVE
    )
    return MetricExecutionBinding(
        definition, cast(ModelCallable, implementation), status, reproduction
    )


@dataclass(frozen=True, slots=True)
class ModelExecutionContract:
    reproduction: ModelReproduction
    model: ModelFamily
    benchmark_name: str
    use: ModelUseReproduction | None
    implementation: ModelCallable | None
    executable: bool
    reason: str
    checkpoint_auto_loaded: bool = False


def _model_implementations() -> dict[str, ModelCallable]:
    return {
        "linear_public_baseline": (fit_linear_public_baseline, predict_linear_public_baseline),
        "initial_public_reference_model": predict_reference_m0,
        "rich_history_zero_baseline": zero_innovation_prediction,
    }


def get_model_execution_contract(
    model_name: str, benchmark_name: str, experiment_name: str | None = None
) -> ModelExecutionContract:
    reproduction = get_model_reproduction(model_name)
    model = reproduction.model_family
    if benchmark_name not in model.applicability.benchmark_names:
        raise ValueError(f"model {model_name} is not registered for {benchmark_name}")
    try:
        use = get_model_use_reproduction(model_name, benchmark_name, experiment_name)
    except KeyError:
        use = None
    implementation = _model_implementations().get(model_name)
    executable_statuses = {
        ModelReproductionStatus.EXACT_IMPLEMENTATION,
        ModelReproductionStatus.SEMANTIC_IMPLEMENTATION,
    }
    configuration_ready = use is not None and use.configuration_status in {
        ModelConfigurationStatus.EXACT,
        ModelConfigurationStatus.NOT_APPLICABLE,
    }
    executable = (
        implementation is not None
        and use is not None
        and use.implementation_status in executable_statuses
        and configuration_ready
    )
    if use is None:
        reason = "no M3 model-use authority binds this benchmark and experiment"
    elif implementation is None:
        reason = "M3 has no public implementation adapter for this model"
    elif use.implementation_status not in executable_statuses:
        reason = f"M3 model-use status is {use.implementation_status.value}"
    elif not configuration_ready:
        reason = f"M3 model configuration status is {use.configuration_status.value}"
    else:
        reason = "public implementation and M3 configuration are available"
    return ModelExecutionContract(
        reproduction, model, benchmark_name, use, implementation, executable, reason
    )


def require_executable_model(
    model_name: str, benchmark_name: str, experiment_name: str | None = None
) -> ModelExecutionContract:
    contract = get_model_execution_contract(model_name, benchmark_name, experiment_name)
    if not contract.executable:
        raise ValueError(f"model execution rejected: {contract.reason}")
    return contract


def reproduction_spec_sha256(spec: RunSpec) -> str:
    from cmj_recovery_dynamics.reproducibility.hashing import sha256_bytes
    from cmj_recovery_dynamics.reproducibility.manifests import manifest_sha256

    record = {
        "benchmark": spec.benchmark_name,
        "calibration_reference": (
            None
            if spec.calibration_reference is None
            else {
                "authority": spec.calibration_reference.authority,
                "kind": spec.calibration_reference.kind.value,
                "reference_progress": spec.calibration_reference.reference_progress,
            }
        ),
        "configuration_manifest_sha256": manifest_sha256(spec.configuration_manifest),
        "evaluation": spec.evaluation_name,
        "model": spec.model_name,
        "schema_version": 1,
        "seed": {"kind": spec.seed_identity.kind.value, "value": spec.seed_identity.value},
        "split": spec.split_name,
    }
    payload = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(payload)


def capture_runtime_fingerprint(*, accelerator: str | None = None) -> RuntimeFingerprint:
    try:
        package_version = version("cmj-recovery-dynamics")
    except PackageNotFoundError:
        package_version = "0.1.0"
    return RuntimeFingerprint(
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        os_family=platform.system(),
        architecture=platform.machine() or "unknown",
        numpy_version=np.__version__,
        package_version=package_version,
        accelerator=accelerator,
    )


def result_value_number(
    value: ScalarResultValue | IntervalResultValue,
) -> float | tuple[float, float]:
    from cmj_recovery_dynamics.reproducibility.contracts import IntervalResultValue

    if isinstance(value, IntervalResultValue):
        return value.lower, value.upper
    return value.value
