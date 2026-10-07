"""Dataset, split, representation, and benchmark-transition lineage."""

from cmj_recovery_dynamics.benchmarks import BENCHMARK_DEFINITIONS
from cmj_recovery_dynamics.lineage.contracts import (
    ArtifactAvailability,
    BenchmarkLineage,
    BenchmarkTransition,
    ChangeClass,
    DatasetIdentity,
    DatasetKind,
    EvidenceConfidence,
    EvidenceReference,
    EvidenceStatus,
    RedistributionStatus,
    RepresentationIdentity,
    ScientificDisposition,
    SplitIdentity,
    SplitRole,
    SplitUnit,
)


def _evidence(*sources: str, note: str = "") -> EvidenceReference:
    return EvidenceReference(EvidenceStatus.DIRECT, tuple(sources), EvidenceConfidence.HIGH, note)


_DATA_AUTHORITY = "RES-365: dataset and split registry"
_GENEALOGY_AUTHORITY = "RES-364: scientific specimen genealogy"
_DATASET_ARTIFACT_STATUS = ArtifactAvailability.PRESERVED_PRIVATELY
_REDISTRIBUTION = RedistributionStatus.UNRESOLVED

REPRESENTATIONS = (
    RepresentationIdentity(
        "camp_history_prediction_query",
        "Camp history and planned exposure inputs with H72 and D7 query rows.",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    RepresentationIdentity(
        "rich_monitoring_prediction_query",
        "Richer monitoring history with variable assessment quality and schedule context.",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    RepresentationIdentity(
        "single_exposure_episode_query",
        (
            "Baseline, participant context, one current exposure, and "
            "four prior episodes; three horizon rows per episode."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
)


DATASETS = (
    DatasetIdentity(
        "initial_preseason_camp_public_sample",
        DatasetKind.SYNTHETIC,
        "event_time_adaptation_recovery_world",
        "camp_history",
        (
            "initial_camp_training",
            "initial_camp_public_validation",
            "initial_camp_hidden_test",
        ),
        ("initial_preseason_camp_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        "initial_generator_fixture",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "canonical_preseason_camp_horizon_sample",
        DatasetKind.SYNTHETIC,
        "event_time_adaptation_recovery_world",
        "camp_history",
        (
            "canonical_camp_training",
            "canonical_camp_public_validation",
            "canonical_camp_hidden_test",
        ),
        ("canonical_preseason_camp_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        "initial_preseason_camp_public_sample",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "rich_history_camp_sample",
        DatasetKind.SYNTHETIC,
        "rich_history_fitness_fatigue_world",
        "rich_monitoring",
        (
            "rich_history_training",
            "rich_history_public_validation",
            "rich_history_original_hidden_bank",
        ),
        ("rich_history_camp_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        None,
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "preliminary_episode_measurement_sample",
        DatasetKind.SYNTHETIC,
        "participant_conditioned_episode_recovery_world",
        "episode_summary",
        (
            "preliminary_episode_training",
            "preliminary_episode_public_validation",
            "preliminary_episode_hidden_test",
        ),
        ("preliminary_post_exposure_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        None,
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "phase_consistent_episode_sample",
        DatasetKind.SYNTHETIC,
        "participant_conditioned_episode_recovery_world",
        "phase_consistent_force_impulse",
        (
            "phase_consistent_episode_training",
            "phase_consistent_episode_public_validation",
            "phase_consistent_episode_hidden_test",
        ),
        ("phase_consistent_post_exposure_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        "preliminary_episode_measurement_sample",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "correlated_exposure_recovery_sample",
        DatasetKind.SYNTHETIC,
        "correlated_exposure_world",
        "phase_consistent_force_impulse",
        (
            "correlated_exposure_training",
            "correlated_exposure_public_validation",
            "correlated_exposure_hidden_test",
        ),
        ("correlated_exposure_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        "phase_consistent_episode_sample",
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "threshold_response_proposed_sample",
        DatasetKind.SYNTHETIC,
        "threshold_response_world",
        "phase_consistent_force_impulse",
        (
            "threshold_response_training",
            "threshold_response_public_validation",
            "threshold_response_hidden_design",
        ),
        ("threshold_response_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        None,
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    DatasetIdentity(
        "fixed_mode_recovery_candidate_sample",
        DatasetKind.SYNTHETIC,
        "fixed_mode_discrepancy_world",
        "phase_consistent_force_impulse",
        ("fixed_mode_training", "fixed_mode_public_validation", "fixed_mode_hidden_test"),
        ("fixed_mode_discrepancy_recovery",),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        "correlated_exposure_recovery_sample",
        _evidence(
            _GENEALOGY_AUTHORITY,
            _DATA_AUTHORITY,
            note=(
                "The active manifest, qualification receipt, and data hashes bind this sample. "
                "An older README names the correlated-exposure sample hashes and is stale."
            ),
        ),
    ),
    DatasetIdentity(
        "initial_generator_fixture",
        DatasetKind.SYNTHETIC,
        "event_time_adaptation_recovery_world",
        "camp_history",
        ("generator_fixture_training", "generator_fixture_validation"),
        (),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        None,
        _evidence(
            _GENEALOGY_AUTHORITY, _DATA_AUTHORITY, note="Fixture only; not a benchmark state."
        ),
    ),
    DatasetIdentity(
        "manufactured_parameter_identification_histories",
        DatasetKind.MANUFACTURED,
        "manufactured_linear_gaussian_identification_world",
        "complete_noisy_episode_history",
        (
            "identification_training_histories",
            "identification_heldout_history_regimes",
        ),
        (),
        _DATASET_ARTIFACT_STATUS,
        _REDISTRIBUTION,
        None,
        _evidence(
            "RES-361: preserved manufactured identification evidence",
            "RES-366: study and result registry",
        ),
    ),
    DatasetIdentity(
        "white_cmj_waveform_grounding_source",
        DatasetKind.EMPIRICAL,
        None,
        "variable_length_ground_reaction_force_waveforms",
        (
            "waveform_training_participants",
            "waveform_public_validation_participants",
            "waveform_future_hidden_participants",
        ),
        (),
        ArtifactAvailability.PRESERVED_PRIVATELY,
        RedistributionStatus.UNRESOLVED,
        None,
        _evidence(
            "RES-363: task-linked real-data authority",
            "RES-366: grounding boundary study",
            note=(
                "The separate waveform task reports 67 participants across 45 train, 9 public-"
                "validation, and 13 future-hidden participants."
            ),
        ),
    ),
)


def _split(
    name: str,
    dataset_name: str,
    role: SplitRole,
    split_unit: SplitUnit,
    rows: int | None,
    *,
    participants: int | None = None,
    camps: int | None = None,
    origins: int | None = None,
    status: ArtifactAvailability = _DATASET_ARTIFACT_STATUS,
    labels: bool | None = True,
    notes: str = "",
    source: str = _DATA_AUTHORITY,
) -> SplitIdentity:
    return SplitIdentity(
        name,
        dataset_name,
        role,
        split_unit,
        rows,
        participants,
        camps,
        origins,
        status,
        labels,
        notes,
        _evidence(source),
    )


SPLITS = (
    _split(
        "initial_camp_training",
        "initial_preseason_camp_public_sample",
        SplitRole.TRAINING,
        SplitUnit.PARTICIPANT,
        4096,
        participants=1024,
        origins=2048,
        notes="Query rows, not participants; two origins and two horizon rows per participant.",
    ),
    _split(
        "initial_camp_public_validation",
        "initial_preseason_camp_public_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.PARTICIPANT,
        512,
        participants=128,
        origins=256,
        notes="Query rows, not participants; public validation labels are available.",
    ),
    _split(
        "initial_camp_hidden_test",
        "initial_preseason_camp_public_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes=(
            "A hidden-128 fixture label exists, but its unit, row "
            "count, and materialization are unresolved."
        ),
    ),
    _split(
        "canonical_camp_training",
        "canonical_preseason_camp_horizon_sample",
        SplitRole.TRAINING,
        SplitUnit.PARTICIPANT_ORIGIN,
        4096,
        participants=1024,
        origins=2048,
        notes="Two horizon rows per origin; groups are disjoint from validation.",
    ),
    _split(
        "canonical_camp_public_validation",
        "canonical_preseason_camp_horizon_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.PARTICIPANT_ORIGIN,
        512,
        participants=128,
        origins=256,
    ),
    _split(
        "canonical_camp_hidden_test",
        "canonical_preseason_camp_horizon_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="No hidden challenge rows or hash are bound to the public manifest.",
    ),
    _split(
        "rich_history_training",
        "rich_history_camp_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP,
        15182,
        participants=4096,
        camps=512,
        origins=8192,
        notes="Rows, participant counts, camp counts, and origins are distinct units.",
    ),
    _split(
        "rich_history_public_validation",
        "rich_history_camp_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP,
        3795,
        participants=1024,
        camps=128,
        origins=2048,
    ),
    _split(
        "rich_history_original_hidden_bank",
        "rich_history_camp_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.CAMP,
        None,
        participants=1152,
        camps=144,
        origins=2304,
        status=ArtifactAvailability.NOT_RECOVERED,
        labels=None,
        notes=(
            "Historical result reproduction exists; hidden design "
            "counts do not prove public materialization."
        ),
        source="RES-365: hidden-bank design limits; RES-366: public/hidden result registry",
    ),
    _split(
        "preliminary_episode_training",
        "preliminary_episode_measurement_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        72000,
        participants=24000,
        camps=96,
        origins=24000,
        notes="Three horizon rows per current episode; four prior episodes are embedded.",
    ),
    _split(
        "preliminary_episode_public_validation",
        "preliminary_episode_measurement_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        12000,
        participants=4000,
        camps=16,
        origins=4000,
    ),
    _split(
        "preliminary_episode_hidden_test",
        "preliminary_episode_measurement_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="No hidden file or hash is bound to the public manifest.",
    ),
    _split(
        "phase_consistent_episode_training",
        "phase_consistent_episode_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        72000,
        participants=24000,
        camps=96,
        origins=24000,
        notes="Three horizon rows per episode; force and impulse derive from the same phase trace.",
    ),
    _split(
        "phase_consistent_episode_public_validation",
        "phase_consistent_episode_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        12000,
        participants=4000,
        camps=16,
        origins=4000,
    ),
    _split(
        "phase_consistent_episode_hidden_test",
        "phase_consistent_episode_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="Private test materialization is not bound.",
    ),
    _split(
        "correlated_exposure_training",
        "correlated_exposure_recovery_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        72000,
        participants=24000,
        camps=96,
        origins=24000,
        notes="Train/validation archetype mixture differs within the same primitive support.",
    ),
    _split(
        "correlated_exposure_public_validation",
        "correlated_exposure_recovery_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        12000,
        participants=4000,
        camps=16,
        origins=4000,
    ),
    _split(
        "correlated_exposure_hidden_test",
        "correlated_exposure_recovery_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="No hidden rows or hash are bound.",
    ),
    _split(
        "threshold_response_training",
        "threshold_response_proposed_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        72000,
        participants=24000,
        camps=96,
        origins=24000,
        notes="Proposed alternate; public split is identified.",
    ),
    _split(
        "threshold_response_public_validation",
        "threshold_response_proposed_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        12000,
        participants=4000,
        camps=16,
        origins=4000,
    ),
    _split(
        "threshold_response_hidden_design",
        "threshold_response_proposed_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.CAMP,
        None,
        participants=5250,
        camps=21,
        origins=5250,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="Design only; source configuration is not evidence of a materialized hidden split.",
    ),
    _split(
        "fixed_mode_training",
        "fixed_mode_recovery_candidate_sample",
        SplitRole.TRAINING,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        72000,
        participants=24000,
        camps=96,
        origins=24000,
        notes="Within-support archetype-mixture shift relative to validation.",
    ),
    _split(
        "fixed_mode_public_validation",
        "fixed_mode_recovery_candidate_sample",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.CAMP_PARTICIPANT_EPISODE,
        12000,
        participants=4000,
        camps=16,
        origins=4000,
        notes="Labels support model selection and shift diagnosis, not fitting.",
    ),
    _split(
        "fixed_mode_hidden_test",
        "fixed_mode_recovery_candidate_sample",
        SplitRole.HIDDEN_TEST,
        SplitUnit.UNKNOWN,
        None,
        status=ArtifactAvailability.NOT_MATERIALIZED,
        labels=False,
        notes="The active manifest states no hidden or private challenge was materialized.",
    ),
    _split(
        "generator_fixture_training",
        "initial_generator_fixture",
        SplitRole.GENERATION_FIXTURE,
        SplitUnit.PARTICIPANT_ORIGIN,
        48,
        origins=24,
        notes="Fixture only; not a benchmark sample.",
    ),
    _split(
        "generator_fixture_validation",
        "initial_generator_fixture",
        SplitRole.GENERATION_FIXTURE,
        SplitUnit.PARTICIPANT_ORIGIN,
        16,
        origins=8,
        notes="Fixture only; not a benchmark sample.",
    ),
    _split(
        "identification_training_histories",
        "manufactured_parameter_identification_histories",
        SplitRole.TRAINING,
        SplitUnit.SYNTHETIC_HISTORY,
        16384,
        notes="Neural posterior training histories; separate from recovery forecast datasets.",
        source="RES-366: system-identification protocol",
    ),
    _split(
        "identification_heldout_history_regimes",
        "manufactured_parameter_identification_histories",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.SYNTHETIC_HISTORY,
        12288,
        notes="Three held-out history regimes with 4,096 histories each; K=2, 4, and 8.",
        source="RES-361: preserved identification result output; RES-366: result registry",
    ),
    _split(
        "waveform_training_participants",
        "white_cmj_waveform_grounding_source",
        SplitRole.TRAINING,
        SplitUnit.EMPIRICAL_PARTICIPANT,
        45,
        participants=45,
        labels=True,
        notes="Waveform study split; no recovery-task crosswalk.",
        source="RES-366: real-data boundary study",
    ),
    _split(
        "waveform_public_validation_participants",
        "white_cmj_waveform_grounding_source",
        SplitRole.PUBLIC_VALIDATION,
        SplitUnit.EMPIRICAL_PARTICIPANT,
        9,
        participants=9,
        labels=True,
        notes="Small participant-level validation split; not a recovery benchmark split.",
        source="RES-366: real-data boundary study",
    ),
    _split(
        "waveform_future_hidden_participants",
        "white_cmj_waveform_grounding_source",
        SplitRole.HIDDEN_TEST,
        SplitUnit.EMPIRICAL_PARTICIPANT,
        13,
        participants=13,
        status=ArtifactAvailability.UNKNOWN,
        labels=None,
        notes="Future-hidden split was declared for the separate waveform task.",
        source="RES-366: real-data boundary study",
    ),
)


_DISPOSITIONS = {
    "initial_preseason_camp_recovery": ScientificDisposition.SUPERSEDED,
    "canonical_preseason_camp_recovery": ScientificDisposition.SUPERSEDED,
    "rich_history_camp_recovery": ScientificDisposition.RETIRED_RATIONALE_UNKNOWN,
    "preliminary_post_exposure_recovery": ScientificDisposition.SUPERSEDED,
    "phase_consistent_post_exposure_recovery": ScientificDisposition.SUPERSEDED,
    "correlated_exposure_recovery": ScientificDisposition.SUPERSEDED,
    "threshold_response_recovery": ScientificDisposition.PROPOSED_ALTERNATE,
    "fixed_mode_discrepancy_recovery": ScientificDisposition.ACTIVE_CANDIDATE,
}


_REPRESENTATIONS = {
    "camp_history": "camp_history_prediction_query",
    "rich_monitoring": "rich_monitoring_prediction_query",
    "episode_summary": "single_exposure_episode_query",
    "phase_consistent_force_impulse": "single_exposure_episode_query",
}


def _world(benchmark_name: str) -> str:
    return {
        "initial_preseason_camp_recovery": "event_time_adaptation_recovery_world",
        "canonical_preseason_camp_recovery": "event_time_adaptation_recovery_world",
        "rich_history_camp_recovery": "rich_history_fitness_fatigue_world",
        "preliminary_post_exposure_recovery": "participant_conditioned_episode_recovery_world",
        "phase_consistent_post_exposure_recovery": "participant_conditioned_episode_recovery_world",
        "correlated_exposure_recovery": "correlated_exposure_world",
        "threshold_response_recovery": "threshold_response_world",
        "fixed_mode_discrepancy_recovery": "fixed_mode_discrepancy_world",
    }[benchmark_name]


_BENCHMARK_DATASETS = {
    "initial_preseason_camp_recovery": "initial_preseason_camp_public_sample",
    "canonical_preseason_camp_recovery": "canonical_preseason_camp_horizon_sample",
    "rich_history_camp_recovery": "rich_history_camp_sample",
    "preliminary_post_exposure_recovery": "preliminary_episode_measurement_sample",
    "phase_consistent_post_exposure_recovery": "phase_consistent_episode_sample",
    "correlated_exposure_recovery": "correlated_exposure_recovery_sample",
    "threshold_response_recovery": "threshold_response_proposed_sample",
    "fixed_mode_discrepancy_recovery": "fixed_mode_recovery_candidate_sample",
}

_BENCHMARK_EVALUATIONS = {
    benchmark.name: benchmark.evaluation_identity.name for benchmark in BENCHMARK_DEFINITIONS
}


def _benchmark_splits(name: str) -> tuple[str, ...]:
    return tuple(split.name for split in SPLITS if split.dataset_name == _BENCHMARK_DATASETS[name])


BENCHMARK_LINEAGE = tuple(
    BenchmarkLineage(
        benchmark_name=name,
        dataset_name=dataset_name,
        split_names=_benchmark_splits(name),
        generator_identity=_world(name),
        observation_identity=next(
            dataset.observation_identity for dataset in DATASETS if dataset.name == dataset_name
        )
        or "UNKNOWN",
        representation_name=_REPRESENTATIONS[
            next(
                dataset.observation_identity for dataset in DATASETS if dataset.name == dataset_name
            )
            or ""
        ],
        evaluation_name=_BENCHMARK_EVALUATIONS[name],
        disposition=_DISPOSITIONS[name],
        evidence=_evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    )
    for name, dataset_name in _BENCHMARK_DATASETS.items()
)


BENCHMARK_TRANSITIONS = (
    BenchmarkTransition(
        "initial_to_canonical_camp_sample",
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
        (ChangeClass.DATASET_SPLIT_CHANGE,),
        True,
        (
            "The world, observation, and task remain fixed; the "
            "manifest-bound public sample and query surface change."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    BenchmarkTransition(
        "rich_history_camp_redesign",
        None,
        "rich_history_camp_recovery",
        (
            ChangeClass.WORLD_CHANGE,
            ChangeClass.OBSERVATION_CHANGE,
            ChangeClass.DATASET_SPLIT_CHANGE,
            ChangeClass.EVALUATION_CHANGE,
        ),
        False,
        (
            "The rich-history state has a distinct generator, "
            "observation contract, sample, and 24-cell evaluation; "
            "direct parentage remains unknown."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    BenchmarkTransition(
        "scalar_to_phase_consistent_measurement",
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        (ChangeClass.OBSERVATION_CHANGE, ChangeClass.DATASET_SPLIT_CHANGE),
        True,
        (
            "The phase-consistent repair derives force and impulse from "
            "the same onset-to-takeoff trace; the 82-field predictor "
            "schema is retained."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    BenchmarkTransition(
        "phase_consistent_to_correlated_exposure_world",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        (ChangeClass.WORLD_CHANGE, ChangeClass.DATASET_SPLIT_CHANGE),
        True,
        (
            "The correlated four-factor and four-archetype exposure "
            "distribution changes the world and public split."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    BenchmarkTransition(
        "correlated_to_threshold_alternate",
        "correlated_exposure_recovery",
        "threshold_response_recovery",
        (ChangeClass.WORLD_CHANGE, ChangeClass.DATASET_SPLIT_CHANGE, ChangeClass.EVALUATION_CHANGE),
        False,
        (
            "Threshold response is a proposed alternate with a proposed "
            "12-cell scorer, not an accepted successor."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
    BenchmarkTransition(
        "correlated_to_fixed_mode_candidate",
        "correlated_exposure_recovery",
        "fixed_mode_discrepancy_recovery",
        (ChangeClass.WORLD_CHANGE, ChangeClass.DATASET_SPLIT_CHANGE),
        False,
        (
            "The fixed-mode response law replaces correlated-exposure "
            "kinetics while retaining the task and observation "
            "contract."
        ),
        _evidence(_GENEALOGY_AUTHORITY, _DATA_AUTHORITY),
    ),
)


__all__ = [
    "BENCHMARK_LINEAGE",
    "BENCHMARK_TRANSITIONS",
    "DATASETS",
    "REPRESENTATIONS",
    "SPLITS",
]
