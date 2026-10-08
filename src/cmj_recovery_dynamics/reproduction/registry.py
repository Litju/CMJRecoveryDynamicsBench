"""M1-backed reproduction claims for the eight public benchmark identities."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

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
    SerializationAuthority,
    SplitReproductionAuthority,
    SplitRole,
    SplitUnit,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionDimension as D,
)
from cmj_recovery_dynamics.reproduction.contracts import (
    ReproductionStatus as S,
)

_EXPECTED_BENCHMARKS = frozenset(
    {
        "initial_preseason_camp_recovery",
        "canonical_preseason_camp_recovery",
        "rich_history_camp_recovery",
        "preliminary_post_exposure_recovery",
        "phase_consistent_post_exposure_recovery",
        "correlated_exposure_recovery",
        "threshold_response_recovery",
        "fixed_mode_discrepancy_recovery",
    }
)
_AUTHORITY = ReproductionAuthority(
    ("RES-363", "RES-364", "RES-365", "RES-366", "RES-367", "RES-368"),
    (
        "Sealed task-linked M1 evidence only; adjacent posterior-inference and White "
        "waveform studies remain outside these benchmark identities."
    ),
)
_SP03_TREE_EVIDENCE = (
    "M1-selected SP03/D04 executable tree e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b"
)


def _claim(
    dimension: D,
    status: S,
    rationale: str,
    *evidence: str,
    missing: tuple[str, ...] = (),
    scope: tuple[str, ...] = (),
    owner: str | None = None,
) -> ReproductionClaim:
    return ReproductionClaim(dimension, status, rationale, tuple(evidence), missing, scope, owner)


def _profile(*parts: Mapping[D, ReproductionClaim]) -> tuple[ReproductionClaim, ...]:
    claims: dict[D, ReproductionClaim] = {}
    for part in parts:
        claims.update(part)
    if set(claims) != set(D):
        missing = set(D).difference(claims)
        extra = set(claims).difference(D)
        raise ValueError(
            f"reproduction profile dimensions differ: missing={missing}, extra={extra}"
        )
    return tuple(claims[dimension] for dimension in D)


def _hashes(train: str, validation: str) -> tuple[ReferenceHash, ...]:
    return (
        ReferenceHash("training", train, "RES-364: publication-safe dataset hash table"),
        ReferenceHash(
            "public_validation", validation, "RES-364: publication-safe dataset hash table"
        ),
    )


def _split(
    name: str,
    role: SplitRole,
    unit: SplitUnit,
    rows: int | None,
    assignment_status: S,
    materialization_state: MaterializationState,
    materialization_status: S,
    *,
    assignment: str,
    materialization: str,
    evidence: tuple[str, ...],
    reference_hash: ReferenceHash | None = None,
    missing_assignment: tuple[str, ...] = (),
    missing_materialization: tuple[str, ...] = (),
    planned_rows: int | None = None,
) -> SplitReproductionAuthority:
    return SplitReproductionAuthority(
        name,
        role,
        unit,
        assignment_status,
        assignment,
        materialization_state,
        materialization_status,
        materialization,
        evidence,
        rows,
        missing_assignment,
        missing_materialization,
        reference_hash,
        planned_rows,
    )


def _splits(
    *,
    train_rows: int,
    validation_rows: int,
    unit: SplitUnit,
    assignment_status: S,
    hashes: tuple[ReferenceHash, ...],
    hidden_state: MaterializationState,
    hidden_assignment_status: S = S.UNKNOWN,
    hidden_rows: int | None = None,
    hidden_planned_rows: int | None = None,
    hidden_unit: SplitUnit | None = None,
    assignment_rationale: str | None = None,
    assignment_missing: tuple[str, ...] | None = None,
) -> tuple[SplitReproductionAuthority, ...]:
    hash_map = {item.split_name: item for item in hashes}
    assignment = assignment_rationale or (
        "M1 preserves the grouping rule, disjointness, and public split seed authority."
        if assignment_status is S.EXACT
        else (
            "M1 preserves grouping and disjointness, but not enough seed authority "
            "to recreate membership."
        )
    )
    missing_assignment = assignment_missing or (
        ()
        if assignment_status is S.EXACT
        else ("exact public split root seed or membership mapping",)
    )
    public_evidence = ("RES-365: dataset and split registry", "RES-364: dataset hash table")
    public = tuple(
        _split(
            name,
            role,
            unit,
            rows,
            assignment_status,
            MaterializationState.MATERIALIZED,
            S.PARTIAL,
            assignment=assignment,
            materialization=(
                "The historical public artifact and expected digest are preserved; "
                "exact clean-room byte regeneration is not established."
            ),
            evidence=public_evidence,
            reference_hash=hash_map[name],
            missing_assignment=missing_assignment,
            missing_materialization=(
                "exact row order and serialization authority",
                "complete RNG and seed-to-byte authority",
            ),
        )
        for name, role, rows in (
            ("training", SplitRole.TRAINING, train_rows),
            ("public_validation", SplitRole.PUBLIC_VALIDATION, validation_rows),
        )
    )
    if hidden_state is MaterializationState.NOT_MATERIALIZED:
        hidden_materialization_status = S.NOT_APPLICABLE
        hidden_materialization = (
            "The active manifest explicitly records no private or hidden challenge materialization."
        )
        missing_hidden_materialization: tuple[str, ...] = ()
    else:
        hidden_materialization_status = S.UNKNOWN
        hidden_materialization = (
            "A hidden design or split label is not evidence that hidden bytes were materialized."
        )
        missing_hidden_materialization = (
            "materialized hidden rows and their expected hash are not established",
        )
    hidden_assignment = (
        "The hidden split assignment is not established by the public manifest."
        if hidden_assignment_status is S.UNKNOWN
        else "The source defines a hidden design, but membership authority is incomplete."
    )
    return public + (
        _split(
            "hidden_test",
            SplitRole.HIDDEN_TEST,
            hidden_unit or SplitUnit.UNKNOWN,
            hidden_rows,
            hidden_assignment_status,
            hidden_state,
            hidden_materialization_status,
            assignment=hidden_assignment,
            materialization=hidden_materialization,
            evidence=("RES-365: dataset and split registry",),
            missing_assignment=(
                ()
                if hidden_assignment_status is S.NOT_APPLICABLE
                else ("hidden membership, private root seed, or materialization authority",)
            ),
            missing_materialization=missing_hidden_materialization,
            planned_rows=hidden_planned_rows,
        ),
    )


_W01_TREE_EVIDENCE = "M1-selected W01 tree 037fd0510dec208d20d9af5eb10f4812ee423abf"
_CAMP_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The component-dose transform, Hill saturation, stretched-exponential "
            "recovery, fast fatigue, "
            "slow cumulative adaptation, event ordering, and parameter distributions are "
            "directly specified."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py, dynamics.py, exposure.py",
        f"{_W01_TREE_EVIDENCE}: kernels.py, state.py",
        "Same-tree tests: test_exposure_recovery_dynamics.py and test_world_generation.py",
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}
_CAMP_OBSERVATION_INITIAL = {
    D.OBSERVATION: _claim(
        D.OBSERVATION,
        S.PARTIAL,
        (
            "The early initial surface leaves assessment measurement details unresolved; "
            "the canonical three-trial contract does not retroactively freeze the initial "
            "sample."
        ),
        "RES-365: observation contract registry",
        missing=("early assessment trial and measurement authority",),
    ),
}
_CAMP_OBSERVATION_CANONICAL = {
    D.OBSERVATION: _claim(
        D.OBSERVATION,
        S.EXACT,
        (
            "The canonical L05/O01 contract fixes three valid trials per assessment, "
            "shared session deviation, independent baseline trial errors, arithmetic-mean "
            "assessment summaries, and the two latest qualifying pre-index summaries in "
            "the inclusive 24–240 hour window. Target trials use one query error and "
            "centered offsets."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and measurement.py",
        "Same-tree test: test_assessment_aggregation.py",
        "RES-365: canonical O01 observation contract",
        "M1-preserved L05 mechanics and measurement contract",
    ),
}
_CAMP_RNG = {
    D.RNG_ALGORITHM: _claim(
        D.RNG_ALGORITHM,
        S.EXACT,
        "The selected W01 source uses CPython random.Random version 2 and SHA-256 "
        "semantic-key namespaces.",
        f"{_W01_TREE_EVIDENCE}: worlds.py and replay_identity.json",
        "RES-365: world generator registry",
        "RES-365: preserved generator and RNG source",
    ),
    D.RNG_STATE: _claim(
        D.RNG_STATE,
        S.UNKNOWN,
        (
            "The selected W01 tree defines roots and semantic substreams, but its checked-in "
            "L05 manifest does not bind those roots to the D02/D03 reference hashes or "
            "serialize their initialized states."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: world generator and dataset/split registries",
        missing=("D02/D03 root binding and initialized state for each public substream",),
    ),
    D.RNG_STREAM_CONSTRUCTION: _claim(
        D.RNG_STREAM_CONSTRUCTION,
        S.EXACT,
        (
            "SHA-256 of canonical JSON semantic keys (first 16 bytes, unsigned big-endian) "
            "seeds random.Random version 2 using split, world, origin, cluster, entity, "
            "event/assessment, and purpose namespaces."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py",
        "RES-365: world generator registry",
    ),
    D.RNG_DRAW_ORDER: _claim(
        D.RNG_DRAW_ORDER,
        S.EXACT,
        (
            "The selected W01 source fixes one rounded uniform draw per separately keyed "
            "attribute/error value; D02/D03 root and state authority remains separate."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py",
        "RES-365: world generator registry",
        "RES-365: preserved generator and RNG source",
    ),
    D.RNG_SUBSTREAM_STRATEGY: _claim(
        D.RNG_SUBSTREAM_STRATEGY,
        S.EXACT,
        (
            "Each W01 value uses an independently seeded semantic-key stream rather than "
            "one shared sequential stream."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py",
        "RES-365: world generator registry",
    ),
}
_CAMP_SCHEMA_INITIAL = {
    D.SCHEMA: _claim(
        D.SCHEMA,
        S.PARTIAL,
        (
            "The semantic camp-history inputs and two outcomes are identified, but the "
            "early public surface has no exact schema freeze."
        ),
        "RES-365: observation and representation contracts",
        missing=("exact early column identities, order, and types",),
    ),
}
_CAMP_SCHEMA_CANONICAL = {
    D.SCHEMA: _claim(
        D.SCHEMA,
        S.EXACT,
        (
            "The canonical public interface fixes the camp-history information surface, "
            "horizon rows, grouping keys, and two target values."
        ),
        "RES-365: observation and representation contracts",
        "RES-364: canonical public representation record",
    ),
}
_CAMP_SEED = {
    D.SEED_AUTHORITY: _claim(
        D.SEED_AUTHORITY,
        S.UNKNOWN,
        (
            "W01 defines public_train/public_validation root strings, but its checked-in "
            "L05 output hashes differ from the D02/D03 reference hashes; those roots are "
            "not bound to these historical sample bytes."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: dataset and split registry",
        missing=("root seeds bound to the D02/D03 reference materializations",),
    ),
}
_CAMP_STREAMS = {
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.PARTIAL,
        (
            "The W01 law and L05 generator are recovered. The selected W01 manifest does "
            "not establish that its roots or generated membership are the D02/D03 sample."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: world, observation, and dataset/split registries",
        missing=("initial observation/schema contract", "D02/D03 root and membership binding"),
    ),
}
_CAMP_SPLIT_PARTIAL = {
    D.SPLIT_ASSIGNMENT: _claim(
        D.SPLIT_ASSIGNMENT,
        S.PARTIAL,
        (
            "The selected W01 source fixes its own public world keys, but its manifest does "
            "not bind those keys to D02/D03 reference materializations."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: dataset and split registry",
        missing=("D02/D03 train and validation membership binding",),
        scope=("training", "public_validation"),
    ),
}
_CAMP_ORDERING = {
    D.ROW_ORDERING: _claim(
        D.ROW_ORDERING,
        S.UNKNOWN,
        (
            "W01 specifies record_type/record_id ordering for its L05 output; the selected "
            "manifest does not bind that ordering to D02/D03 reference bytes."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: dataset and split registry",
        missing=("D02/D03 row ordering and stable tie-breaking binding",),
    ),
}
_CAMP_SERIALIZATION_INITIAL = {
    D.SERIALIZATION: _claim(
        D.SERIALIZATION,
        S.PARTIAL,
        (
            "The initial sample is identified as JSONL, but its early schema freeze and "
            "exact writer behavior are unresolved."
        ),
        "RES-365: observation and dataset/split registries",
        missing=("column order, JSON float formatting, and writer behavior",),
    ),
}
_CAMP_SERIALIZATION_CANONICAL = {
    D.SERIALIZATION: _claim(
        D.SERIALIZATION,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The canonical logical record and target structure can be re-expressed, while "
            "historical field encoding and writer details are not frozen."
        ),
        "RES-365: observation and dataset/split registries",
        missing=("historical writer implementation and byte-level JSON encoding",),
    ),
}

_POST_WORLD = {
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The recovered world, measurement contract, population geometry, and semantic "
            "schema support a clean-room generator at contract level; exact historical "
            "bytes remain a separate unresolved authority."
        ),
        "RES-365: world, observation, and dataset/split registries",
        missing=("historical RNG implementation state, row order, and writer byte semantics",),
    ),
}
_POST_OBSERVATION = {
    D.OBSERVATION: _claim(
        D.OBSERVATION,
        S.EXACT,
        (
            "Three valid 65-node half-sine force traces share a defined concentric "
            "interval; trapezoidal integration and the force/impulse equation are fixed, "
            "as are baseline, history, timing, and trial aggregation."
        ),
        "RES-365: observation contract registry",
    ),
}
_POST_SCHEMA = {
    D.SCHEMA: _claim(
        D.SCHEMA,
        S.EXACT,
        (
            "The 82 semantic predictors, three grouping/query keys, two labels, horizon "
            "rows, and target shape are fixed by the recovered representation contract."
        ),
        "RES-365: observation and representation contracts",
    ),
}
_POST_SPLIT = {
    D.SPLIT_ASSIGNMENT: _claim(
        D.SPLIT_ASSIGNMENT,
        S.EXACT,
        (
            "Public train and validation membership is camp/participant/episode grouped "
            "and bound to the recovered public roots; this claim is scoped to those "
            "materialized public splits."
        ),
        "RES-365: dataset and split registry",
        scope=("training", "public_validation"),
    ),
}
_POST_ORDERING = {
    D.ROW_ORDERING: _claim(
        D.ROW_ORDERING,
        S.UNKNOWN,
        (
            "M1 establishes deterministic split membership and query geometry, but does "
            "not freeze the exact order of rows in each output file."
        ),
        "RES-365: dataset and split registry",
        missing=("exact row sort key and stable tie-breaking rule",),
    ),
}
_POST_SERIALIZATION = {
    D.SERIALIZATION: _claim(
        D.SERIALIZATION,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The logical field and target representation is recoverable, but the "
            "historical writer, index handling, floating encoding, metadata, and "
            "compression details are not all frozen."
        ),
        "RES-365: observation, representation, and dataset/split registries",
        missing=("complete historical writer and byte-level serialization settings",),
    ),
}
_MODEL_DEFERRED = {
    D.MODEL_CONFIGURATION: _claim(
        D.MODEL_CONFIGURATION,
        S.DEFERRED_OUT_OF_SCOPE,
        (
            "RES-368 identifies model families and some private artifacts, but exact "
            "model/config/checkpoint reproduction belongs to M3."
        ),
        "RES-368: model and checkpoint lineage",
        missing=("complete architecture, training configuration, and checkpoint binding",),
        owner="M3",
    ),
}
_RESULT_M3 = {
    D.HISTORICAL_RESULT: _claim(
        D.HISTORICAL_RESULT,
        S.DEFERRED_OUT_OF_SCOPE,
        (
            "Historical numerical-result reproduction requires the later model and "
            "evaluation run; M2.1 classifies authority and does not rerun it."
        ),
        "RES-366: experiment and result lineage",
        "RES-368: model and checkpoint lineage",
        missing=("exact model/config/checkpoint and result-producing run",),
        owner="M3",
    ),
}
_RESULT_CAMP = {
    D.HISTORICAL_RESULT: _claim(
        D.HISTORICAL_RESULT,
        S.DEFERRED_OUT_OF_SCOPE,
        (
            "Initial and canonical numerical result families are non-comparable; "
            "reproducing either requires M3 model/config/checkpoint and task-locked "
            "evaluation authority."
        ),
        "RES-366: result comparability registry",
        "RES-367: evaluation and scorer registry",
        "RES-368: model and checkpoint lineage",
        missing=("complete model/config/checkpoint and public calibration value",),
        owner="M3",
    ),
}
_RESULT_M3_M4 = {
    D.HISTORICAL_RESULT: _claim(
        D.HISTORICAL_RESULT,
        S.DEFERRED_OUT_OF_SCOPE,
        (
            "Historical numerical-result reproduction and headroom/reconstructability "
            "result work belong to M3/M4; hidden-bank outputs remain bank-specific and "
            "are not public materialization claims."
        ),
        "RES-366: experiment and result lineage",
        "RES-368: model and checkpoint lineage",
        missing=("exact model/config/checkpoint and result-producing run",),
        owner="M3/M4",
    ),
}


def _evaluation(
    *,
    roles: tuple[EvaluationRole, ...],
    production_status: ProductionScorerStatus,
    scorer: str | None,
    rationale: str,
    calibration: CalibrationReferenceStatus = CalibrationReferenceStatus.NOT_APPLICABLE,
    research: tuple[str, ...] = (),
    qualification: tuple[str, ...] = (),
    selection: tuple[str, ...] = (),
) -> EvaluationAuthority:
    return EvaluationAuthority(
        roles,
        production_status,
        scorer,
        research,
        qualification,
        selection,
        calibration,
        None,
        rationale,
    )


def _evaluation_claim(rationale: str, *evidence: str) -> ReproductionClaim:
    return _claim(
        D.EVALUATION,
        S.PARTIAL,
        rationale,
        *evidence,
        missing=("one or more accepted production-evaluation authorities or calibration values",),
    )


_EVAL_CAMP_INITIAL = _evaluation(
    roles=(EvaluationRole.ACCEPTED_BENCHMARK_SCORER, EvaluationRole.MODEL_SELECTION_METRIC),
    production_status=ProductionScorerStatus.ACCEPTED,
    scorer="initial_camp_population_normalized_rmse_score",
    calibration=CalibrationReferenceStatus.LOCKED_NOT_PUBLIC,
    selection=("four_cell_training_scale_normalized_rmse_selection_metric",),
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "The accepted camp score and separate model-selection/qualification metrics "
        "are identified; "
        "the initial historical score binding and locked calibration value remain unavailable."
    ),
)
_EVAL_CAMP_CANONICAL = _evaluation(
    roles=(EvaluationRole.ACCEPTED_BENCHMARK_SCORER, EvaluationRole.MODEL_SELECTION_METRIC),
    production_status=ProductionScorerStatus.ACCEPTED,
    scorer="canonical_camp_population_normalized_rmse_score",
    calibration=CalibrationReferenceStatus.LOCKED_NOT_PUBLIC,
    selection=("four_cell_training_scale_normalized_rmse_selection_metric",),
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "The canonical accepted camp score and distinct selection/qualification metrics "
        "are identified; "
        "its task-locked calibration value is not public or recovered."
    ),
)
_EVAL_RICH = _evaluation(
    roles=(EvaluationRole.ACCEPTED_BENCHMARK_SCORER, EvaluationRole.RESEARCH_DIAGNOSTIC),
    production_status=ProductionScorerStatus.ACCEPTED,
    scorer="rich_history_24_cell_normalized_rmse_score",
    calibration=CalibrationReferenceStatus.LOCKED_NOT_PUBLIC,
    research=("rich_history_raw_progress_diagnostic",),
    rationale=(
        "The accepted 24-cell score and separate raw-progress research diagnostic are identified; "
        "the task-locked calibration value is not public or recovered."
    ),
)
_EVAL_UNIMPLEMENTED = _evaluation(
    roles=(EvaluationRole.UNIMPLEMENTED_EVALUATION,),
    production_status=ProductionScorerStatus.UNIMPLEMENTED,
    scorer=None,
    rationale="M1 establishes no implemented production scorer for this formulation.",
)
_EVAL_PHASE = _evaluation(
    roles=(EvaluationRole.UNIMPLEMENTED_EVALUATION, EvaluationRole.RESEARCH_DIAGNOSTIC),
    production_status=ProductionScorerStatus.UNIMPLEMENTED,
    scorer=None,
    research=("six_cell_mean_cellwise_normalized_rmse",),
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "Production scoring is unimplemented; the six-cell normalized error is "
        "a research diagnostic, "
        "not a benchmark score."
    ),
)
_EVAL_CORRELATED = _evaluation(
    roles=(EvaluationRole.UNIMPLEMENTED_EVALUATION, EvaluationRole.RESEARCH_DIAGNOSTIC),
    production_status=ProductionScorerStatus.UNIMPLEMENTED,
    scorer=None,
    research=("six_cell_mean_cellwise_normalized_rmse",),
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "Production scoring is unimplemented; corrected six-cell result families "
        "remain research diagnostics."
    ),
)
_EVAL_THRESHOLD = _evaluation(
    roles=(EvaluationRole.PROPOSED_BENCHMARK_SCORER, EvaluationRole.QUALIFICATION_STATISTIC),
    production_status=ProductionScorerStatus.PROPOSED,
    scorer="threshold_response_12_cell_normalized_rmse_score",
    calibration=CalibrationReferenceStatus.LOCKED_NOT_PUBLIC,
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "The 12-cell score is a proposed, unresolved evaluation; there is no "
        "acceptance decision or public calibration value."
    ),
)
_EVAL_FIXED = _evaluation(
    roles=(EvaluationRole.UNIMPLEMENTED_EVALUATION, EvaluationRole.RESEARCH_DIAGNOSTIC),
    production_status=ProductionScorerStatus.UNIMPLEMENTED,
    scorer=None,
    research=("six_cell_mean_cellwise_normalized_rmse",),
    qualification=("public_synthetic_dataset_qualification",),
    rationale=(
        "Production scoring is unimplemented; fixed-mode six-cell result families are "
        "research diagnostics only."
    ),
)


_OBS_PRELIMINARY = {
    D.OBSERVATION: _claim(
        D.OBSERVATION,
        S.PARTIAL,
        (
            "The dedicated baseline, three scalar trials, four prior episodes, and "
            "24/48/72-hour queries are recovered, but no common phase trace or "
            "force/impulse identity was frozen."
        ),
        "RES-365: observation contract registry",
        missing=("shared force-time phase and force/impulse coupling authority",),
    ),
}
_OBS_POST = {
    D.OBSERVATION: _POST_OBSERVATION[D.OBSERVATION],
}
_SCHEMA_POST = {D.SCHEMA: _POST_SCHEMA[D.SCHEMA]}
_RICH_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The selected W02 law sums Hill-scaled slow-positive and load/bout-adjusted "
            "fast-negative exposure modes, using correlated participant level effects, "
            "force/impulse amplitude construction, bounded participant kinetics, camp "
            "regimes, and the authored floor after summation at 0.38 of latent baseline."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/core.py, params.py, and schedule.py",
        f"{_SP03_TREE_EVIDENCE}: same-tree source tests",
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}
_RICH_COMPLETE_GENERATOR = {
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The selected executable tree and its binding tests define the complete public "
            "generator. Clean-room code preserves that law and public contract; unresolved "
            "historical PRNG state, row ordering, and writer bytes remain separate."
        ),
        f"{_SP03_TREE_EVIDENCE}: data_generation/src/lcmj_v3/",
        f"{_SP03_TREE_EVIDENCE}: parameters, projection, split manifests, and same-tree tests",
        missing=("historical initialized PRNG state, row ordering, and byte serialization",),
    ),
}
_RICH_SPLIT = {
    D.SPLIT_ASSIGNMENT: _claim(
        D.SPLIT_ASSIGNMENT,
        S.PARTIAL,
        (
            "D04's hierarchy and public bytes are fixed. The first M1-authorized commit that "
            "co-locates both D04 Parquet blobs and their hash-binding manifest is "
            "6947771c8567438bba4cea8b5bb28d8f7992b307, task tree "
            "88e0cf68aa7fda864505a2a7e353e0487187919e. That source uses one shared per-camp "
            "default_rng through the horizon-presence and dropped-index draws. Later ALI-490 "
            "commit ad5e48a1dc9c1fd1e27ecd314940a9be1b4fd50a (tree "
            "e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b) changes these to named child streams, "
            "including independent horizon-presence and dropped-index streams. A bounded replay "
            "of the producing source under the available OSS 2.5.3 runtime matches D04 query "
            "keys and masks, but the producing Dockerfile only identifies a py313 base tag and "
            "does not bind its NumPy version, exact Python build, or BitGenerator. Treat that "
            "replay as compatibility evidence, not historical runtime authority; the later "
            "e2871cc clean-room replay remains non-historical."
        ),
        "RES-361/M1: D04 producer commit 6947771c8567438bba4cea8b5bb28d8f7992b307, "
        "task tree 88e0cf68aa7fda864505a2a7e353e0487187919e, manifest blob "
        "03864b433e678e582da3d50d66468443a77cba71, train blob "
        "8b789399f8b40feef3a02aff98eb9a86d193f335, validation blob "
        "d2987e1e349986319eeb01cc46972e0bae9c158c",
        "RES-364/365: D04 hashes, geometry, public roots, generator version, and manifest mapping",
        "ALI-490 commit ad5e48a1dc9c1fd1e27ecd314940a9be1b4fd50a / task tree "
        "e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b: rng.py, core.py, schedule.py, and "
        "test_ali490_rng_channels.py",
        "D04 producer environment/Dockerfile: runtime-ml-core-py313-local base tag only; no "
        "NumPy pin or lock file",
        "RES-365: dataset and split registry",
        missing=(
            "the exact Python build, NumPy version, and BitGenerator/runtime used by the D04 "
            "producer's default_rng instances",
        ),
        scope=("training", "public_validation"),
    ),
}
_PRELIM_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The two negative-exponential response and bounded load/interaction mapping "
            "with participant and camp effects are specified, independently of the "
            "incomplete scalar observation law."
        ),
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}
_CORRELATED_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The two-exponential response is paired with the recovered correlated "
            "four-factor exposure law and split-specific four-archetype mixtures."
        ),
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}
_THRESHOLD_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The participant-weighted normalized load, threshold distribution, and "
            "softplus response hinge are specified; proposed status does not alter this "
            "mathematical law."
        ),
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}
_FIXED_WORLD = {
    D.WORLD_LAW: _claim(
        D.WORLD_LAW,
        S.EXACT,
        (
            "The response uses mathematical 24/84-hour modes, four participant "
            "sensitivity coordinates, and bounded shared smooth discrepancy; the modes "
            "are not biological compartments."
        ),
        "RES-364: scientific-state registry",
        "RES-365: world generator registry",
    ),
}


_CAMP_RANDOMNESS = RandomnessAuthority(
    "Python random.Random version 2",
    (
        "Semantic-keyed streams; exact sample state depends on a root seed not bound by "
        "the public manifests."
    ),
    "Symbolic fixture namespaces are preserved, but exact public sample roots are unknown.",
    (
        "SHA-256 semantic keys with separate athlete, event, measurement, assessment, and "
        "missingness namespaces."
    ),
    (
        "The preserved source fixes per-stream draw order; exact public root seeds are a "
        "separate unresolved authority."
    ),
    "Separate stable semantic-key namespaces; not one shared sequential stream.",
)
_RICH_HISTORY_RANDOMNESS = RandomnessAuthority(
    (
        "NumPy default_rng is used by the preserved source; its bit-generator/runtime "
        "binding is not fixed in M1."
    ),
    (
        "Public train/validation roots are named; serialized initial bit-generator states "
        "are not available."
    ),
    "Public train, validation, and hidden-design seed names are preserved.",
    (
        "Each camp uses one root identity (simulate-camp namespace, public split root, split "
        "name, camp index), then "
        "a separate named generator per stochastic channel. Kinetic and preferred-depth "
        "channels add the local participant index; other origin surfaces use fixed arrays "
        "in participant/origin order."
    ),
    (
        "The source fixes ordered channel calls and fixed array shapes; changing a channel's "
        "draws cannot advance another channel. The NumPy bit-generator/runtime binding "
        "remains separate."
    ),
    (
        "Random streams are camp-rooted and channel-keyed, with local participant keys "
        "only for kinetic and preferred-depth draws. Stable participant/origin/horizon "
        "opaque public keys are a separate projection hierarchy, not RNG stream keys."
    ),
)
_EPISODE_RANDOMNESS = RandomnessAuthority(
    (
        "Preserved RandomStreams source calls NumPy default_rng but does not pin its bit "
        "generator or runtime."
    ),
    "Public root seed is known, but exact initialized stream states are not preserved.",
    "The public generator root is preserved; no separate hidden file/hash is bound.",
    "Keyed camp, participant, episode/query, and measurement streams are identified.",
    (
        "Preserved source fixes draw order within each purpose-keyed stream; the PRNG "
        "runtime is a separate authority."
    ),
    (
        "The source hashes a registered root/split/entity/purpose identity into an "
        "independent generator."
    ),
)
_CORRELATED_RANDOMNESS = RandomnessAuthority(
    (
        "Preserved keyed RNG source calls NumPy default_rng but does not pin its bit "
        "generator or runtime."
    ),
    "The public root is known; initialized factor/archetype stream states are not serialized.",
    "The public root and split-specific mixture probabilities are preserved.",
    (
        "Correlated factor residuals, archetype assignment, feature residuals, "
        "participant/camp effects, and measurement have separate keyed inputs."
    ),
    (
        "Preserved source fixes draw order within every keyed stream; initialized state "
        "is a separate claim."
    ),
    (
        "Source derives independent generators from stable camp/participant/episode/query "
        "identities and registered channels."
    ),
)
_THRESHOLD_RANDOMNESS = RandomnessAuthority(
    (
        "Preserved keyed RNG source calls NumPy default_rng but does not pin its bit "
        "generator or runtime."
    ),
    (
        "Public stream state is not serialized; a separate private test seed source is "
        "named without a public materialization claim."
    ),
    (
        "The public root is preserved; the separate hidden test root is not established "
        "in public authority."
    ),
    (
        "Participant weights/thresholds, camp effects, episode discrepancy, and "
        "trial/session noise are separated conceptually."
    ),
    (
        "The preserved public generator fixes draw order; private test initialization "
        "remains unavailable."
    ),
    (
        "Public keyed streams are defined; private test root and initialized streams are "
        "not publication-safe authority."
    ),
)
_FIXED_MODE_RANDOMNESS = RandomnessAuthority(
    (
        "Preserved keyed RNG source calls NumPy default_rng but does not pin its bit "
        "generator or runtime."
    ),
    (
        "The public root and random-feature seed names are known; initialized stream "
        "states are not serialized."
    ),
    "The public generator root is preserved; M1 says no private/hidden challenge was materialized.",
    (
        "World discrepancy, episode discrepancy, participant effects, and phase-consistent "
        "trial/session noise use keyed inputs."
    ),
    (
        "The preserved generator source fixes draw order within named channels; the PRNG "
        "runtime remains separate."
    ),
    "The source fixes versioned key hashing, channel names, and child-stream construction.",
)


def _rng_claims(
    *,
    algorithm: S,
    state: S,
    seed: S,
    streams: S,
    draw: S,
    substreams: S,
    seed_rationale: str,
    seed_missing: tuple[str, ...],
    algorithm_rationale: str,
    stream_rationale: str,
    substream_rationale: str,
) -> dict[D, ReproductionClaim]:
    source = ("RES-365: world generator and dataset/split registries",)
    return {
        D.RNG_ALGORITHM: _claim(
            D.RNG_ALGORITHM,
            algorithm,
            algorithm_rationale,
            *source,
            "RES-365: preserved RNG source",
            missing=("exact PRNG bit generator or runtime binding",)
            if algorithm is not S.EXACT
            else (),
        ),
        D.RNG_STATE: _claim(
            D.RNG_STATE,
            state,
            (
                "M1 identifies seed and stream design but does not preserve initialized "
                "state for every generated substream."
            ),
            *source,
            missing=("serialized initial state for every stream",),
        ),
        D.SEED_AUTHORITY: _claim(
            D.SEED_AUTHORITY,
            seed,
            seed_rationale,
            *source,
            missing=seed_missing,
            scope=("training", "public_validation"),
        ),
        D.RNG_STREAM_CONSTRUCTION: _claim(
            D.RNG_STREAM_CONSTRUCTION,
            streams,
            stream_rationale,
            *source,
            "RES-365: preserved generator and RNG source",
            missing=("full source-stable substream derivation",) if streams is not S.EXACT else (),
        ),
        D.RNG_DRAW_ORDER: _claim(
            D.RNG_DRAW_ORDER,
            draw,
            (
                "The preserved generator source fixes ordered draws within each keyed "
                "stream; stream-state authority is independent."
            ),
            *source,
            "RES-365: preserved generator source",
            missing=("complete per-stream ordered draw schedule",) if draw is not S.EXACT else (),
        ),
        D.RNG_SUBSTREAM_STRATEGY: _claim(
            D.RNG_SUBSTREAM_STRATEGY,
            substreams,
            substream_rationale,
            *source,
            "RES-365: preserved RNG source",
            missing=("exact substream key derivation and initialized state",)
            if substreams is not S.EXACT
            else (),
        ),
    }


def _hash_claim(rationale: str, *missing: str) -> dict[D, ReproductionClaim]:
    return {
        D.DATASET_HASH: _claim(
            D.DATASET_HASH,
            S.PARTIAL,
            rationale,
            "RES-364: publication-safe dataset hash table",
            "RES-365: dataset and split registry",
            missing=tuple(missing),
            scope=("training", "public_validation"),
        ),
    }


def _evaluation_part(rationale: str) -> dict[D, ReproductionClaim]:
    return {
        D.EVALUATION: _evaluation_claim(
            rationale,
            "RES-367: evaluation and scorer registry",
            "RES-366: result comparability registry",
        )
    }


def _public_split_part(
    status: S, *, rationale: str, missing: tuple[str, ...] = ()
) -> dict[D, ReproductionClaim]:
    return {
        D.SPLIT_ASSIGNMENT: _claim(
            D.SPLIT_ASSIGNMENT,
            status,
            rationale,
            "RES-365: dataset and split registry",
            missing=missing,
            scope=("training", "public_validation"),
        )
    }


_CAMP_COMMON = {
    **_CAMP_WORLD,
    **_CAMP_OBSERVATION_INITIAL,
    **_CAMP_RNG,
    **_CAMP_STREAMS,
    **_CAMP_SPLIT_PARTIAL,
    **_CAMP_ORDERING,
    D.RNG_ALGORITHM: _CAMP_RNG[D.RNG_ALGORITHM],
    D.SEED_AUTHORITY: _CAMP_SEED[D.SEED_AUTHORITY],
    D.SPLIT_ASSIGNMENT: _CAMP_SPLIT_PARTIAL[D.SPLIT_ASSIGNMENT],
    D.SERIALIZATION: _CAMP_SERIALIZATION_INITIAL[D.SERIALIZATION],
    **_hash_claim(
        (
            "The D02 hashes are known. The selected W01 L05 manifest has different public "
            "output hashes, so its seeds, membership, ordering, and writer cannot be assigned "
            "to D02."
        ),
        "binding from the selected W01 output to D02 materialization",
    ),
    **_MODEL_DEFERRED,
    **_RESULT_CAMP,
}

_CANONICAL_CAMP_COMMON = {
    **_CAMP_WORLD,
    **_CAMP_RNG,
    **_CAMP_STREAMS,
    **_CAMP_SPLIT_PARTIAL,
    **_CAMP_ORDERING,
    D.OBSERVATION: _CAMP_OBSERVATION_CANONICAL[D.OBSERVATION],
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.PARTIAL,
        (
            "The resolved W01 law and canonical observation are known, but the selected "
            "W01 L05 manifest does not bind its roots or output membership to D03."
        ),
        f"{_W01_TREE_EVIDENCE}: worlds.py and data/manifest.json",
        "RES-365: world, observation, and dataset/split registries",
        missing=("binding from the selected W01 output to D03 materialization",),
    ),
    D.SCHEMA: _CAMP_SCHEMA_CANONICAL[D.SCHEMA],
    D.SEED_AUTHORITY: _CAMP_SEED[D.SEED_AUTHORITY],
    D.SPLIT_ASSIGNMENT: _CAMP_SPLIT_PARTIAL[D.SPLIT_ASSIGNMENT],
    D.SERIALIZATION: _CAMP_SERIALIZATION_CANONICAL[D.SERIALIZATION],
    **_hash_claim(
        (
            "The D03 hashes are known. The selected W01 L05 manifest records different "
            "public output hashes, so its roots, membership, ordering, and writer cannot be "
            "assigned to D03."
        ),
        "binding from the selected W01 output to D03 materialization",
    ),
    **_MODEL_DEFERRED,
    **_RESULT_CAMP,
}

_RICH_CLAIMS = {
    **_RICH_WORLD,
    **_RICH_COMPLETE_GENERATOR,
    D.RNG_ALGORITHM: _claim(
        D.RNG_ALGORITHM,
        S.PARTIAL,
        (
            "The preserved source uses keyed NumPy default_rng streams for schedule, "
            "kinetics, dose, validity, and measurement but does not pin the "
            "bit-generator/runtime."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/rng.py",
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/params.py and same-tree RNG tests",
        f"{_SP03_TREE_EVIDENCE}: environment/Dockerfile does not pin a NumPy package version",
        missing=("exact NumPy bit generator and runtime binding",),
    ),
    D.RNG_STATE: _claim(
        D.RNG_STATE,
        S.PARTIAL,
        (
            "Public split seed names are preserved, but initialized NumPy states for each "
            "stream are not."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/rng.py and public split manifest",
        "RES-365: world generator and dataset/split registries",
        missing=("serialized initial state for every stream",),
    ),
    D.SEED_AUTHORITY: _claim(
        D.SEED_AUTHORITY,
        S.EXACT,
        (
            "Public train and validation root seed names and values are fixed in the "
            "selected split specification. Hidden design counts do not imply a public "
            "hidden materialization."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/params.py and data/public/manifest.json",
        "RES-365: dataset and split registry",
    ),
    D.RNG_STREAM_CONSTRUCTION: _claim(
        D.RNG_STREAM_CONSTRUCTION,
        S.EXACT,
        (
            "The source hashes a simulate-camp-prefixed root identity, then derives one "
            "generator per channel; optional local participant indices key two trait channels."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/rng.py and core.py",
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/splits.py",
    ),
    D.RNG_DRAW_ORDER: _claim(
        D.RNG_DRAW_ORDER,
        S.EXACT,
        (
            "The selected source fixes channel call order, fixed maximum array shapes, and "
            "participant/origin array order within each camp."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/core.py, schedule.py, and measurement.py",
        f"{_SP03_TREE_EVIDENCE}: same-tree RNG channel tests",
    ),
    D.RNG_SUBSTREAM_STRATEGY: _claim(
        D.RNG_SUBSTREAM_STRATEGY,
        S.EXACT,
        (
            "Named streams are isolated below the camp root; kinetic and preferred-depth "
            "draws use local participant indices. Origin rows occupy fixed positions in "
            "camp-shaped arrays. Opaque origin/query keys are a separate projection layer."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/rng.py, core.py, schedule.py, and projection.py",
    ),
    D.OBSERVATION: _claim(
        D.OBSERVATION,
        S.EXACT,
        (
            "The selected observation code fixes the two-assessment baseline rule, schedule "
            "opportunities, valid/invalid/missing states, participant covariates, and five "
            "valid target trials. Its depth is contextual only; a stale parameter JSON "
            "entry is superseded by executable measurement code and its regression test."
        ),
        f"{_SP03_TREE_EVIDENCE}: lcmj_v3/measurement.py and params.py",
        f"{_SP03_TREE_EVIDENCE}: test_ali488_source_repair.py",
    ),
    D.SCHEMA: _claim(
        D.SCHEMA,
        S.EXACT,
        (
            "The rich monitoring representation fixes its semantic fields, variable "
            "history geometry, and H72/D7 query shape."
        ),
        f"{_SP03_TREE_EVIDENCE}: data/canonical_v3.py, projection.py, "
        "and data/public/manifest.json",
        "RES-365: observation and representation contracts",
    ),
    **_RICH_SPLIT,
    **_POST_ORDERING,
    **_POST_SERIALIZATION,
    **_hash_claim(
        (
            "Expected public train/validation hashes are published; clean-room hash "
            "reproduction lacks exact bit-generator state, row order, and writer "
            "semantics. The original hidden bank remains an unknown materialization, not "
            "a public data claim."
        ),
        "exact RNG bit-generator/runtime state",
        "exact row ordering and serializer behavior",
        "hidden-bank materialization and expected hash",
    ),
    **_evaluation_part(
        (
            "The accepted 24-cell scorer is defined, but its task-locked calibration "
            "value is unavailable; hidden-bank evaluation remains bank-specific."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3_M4,
}

_PRELIMINARY_CLAIMS = {
    **_PRELIM_WORLD,
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.PARTIAL,
        (
            "The response law, load ranges, sample geometry, and public root are "
            "recovered, but the scalar measurement contract does not define a shared "
            "force/impulse phase operation."
        ),
        "RES-365: world, observation, and dataset/split registries",
        missing=("complete force/impulse observation law",),
    ),
    **_rng_claims(
        algorithm=S.PARTIAL,
        state=S.PARTIAL,
        seed=S.EXACT,
        streams=S.EXACT,
        draw=S.EXACT,
        substreams=S.EXACT,
        seed_rationale=(
            "The public generator root and camp→participant→episode/query "
            "key hierarchy are preserved."
        ),
        seed_missing=(),
        algorithm_rationale=(
            "Preserved RandomStreams source calls NumPy default_rng "
            "but does not pin its bit generator or runtime."
        ),
        stream_rationale=(
            "M1 identifies keyed camp, participant, episode/query, and measurement streams."
        ),
        substream_rationale=(
            "The preserved source fixes key hashing and independent "
            "camp/participant/episode/query generator construction."
        ),
    ),
    **_OBS_PRELIMINARY,
    **_SCHEMA_POST,
    **_POST_SPLIT,
    **_POST_ORDERING,
    D.SERIALIZATION: _claim(
        D.SERIALIZATION,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The Parquet logical representation is recoverable; historical writer, index, "
            "float, metadata, and compression settings are not frozen."
        ),
        "RES-365: observation, representation, and dataset/split registries",
        missing=("historical writer, index handling, float encoding, metadata, and compression",),
    ),
    **_hash_claim(
        (
            "Public train/validation hashes and the root seed are known, but incomplete "
            "PRNG state, row-order, and writer authority prevents an exact hash claim."
        ),
        "exact PRNG and initialized state",
        "exact row ordering and serialization authority",
    ),
    **_evaluation_part(
        (
            "No production scorer is recovered for this formulation; a production result "
            "cannot be reproduced from the available evaluation authority."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3,
}

_PHASE_CLAIMS = {
    **_PRELIM_WORLD,
    **_POST_WORLD,
    **_rng_claims(
        algorithm=S.PARTIAL,
        state=S.PARTIAL,
        seed=S.EXACT,
        streams=S.EXACT,
        draw=S.EXACT,
        substreams=S.EXACT,
        seed_rationale=(
            "The public generator root and camp→participant→episode/query "
            "key hierarchy are preserved."
        ),
        seed_missing=(),
        algorithm_rationale=(
            "Preserved RandomStreams source calls NumPy default_rng "
            "but does not pin its bit generator or runtime."
        ),
        stream_rationale=(
            "M1 identifies keyed camp, participant, episode/query, and measurement streams."
        ),
        substream_rationale=(
            "The preserved source fixes key hashing and independent "
            "camp/participant/episode/query generator construction."
        ),
    ),
    **_OBS_POST,
    **_SCHEMA_POST,
    **_POST_SPLIT,
    **_POST_ORDERING,
    **_POST_SERIALIZATION,
    **_hash_claim(
        (
            "Expected public train/validation hashes and the public root are known; exact "
            "generator RNG state, row order, and byte serialization are not."
        ),
        "exact PRNG and initialized state",
        "exact row ordering and serialization authority",
    ),
    **_evaluation_part(
        (
            "The phase-consistent measurement is defined, but production scoring is "
            "unimplemented; the six-cell normalized error is only a research diagnostic."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3,
}

_CORRELATED_CLAIMS = {
    **_CORRELATED_WORLD,
    **_POST_WORLD,
    **_rng_claims(
        algorithm=S.PARTIAL,
        state=S.PARTIAL,
        seed=S.EXACT,
        streams=S.EXACT,
        draw=S.EXACT,
        substreams=S.EXACT,
        seed_rationale=(
            "The public root, split-specific archetype mixtures, and "
            "disjoint grouping keys are preserved."
        ),
        seed_missing=(),
        algorithm_rationale=(
            "Preserved keyed RNG source uses NumPy default_rng but "
            "does not pin its bit generator or runtime."
        ),
        stream_rationale=(
            "Correlated factors, archetypes, participant/camp effects, "
            "episode noise, and measurement streams are distinguished."
        ),
        substream_rationale=(
            "The preserved source fixes factor/archetype and "
            "participant/episode keys for independent streams."
        ),
    ),
    **_OBS_POST,
    **_SCHEMA_POST,
    **_POST_SPLIT,
    **_POST_ORDERING,
    **_POST_SERIALIZATION,
    **_hash_claim(
        (
            "Expected public train/validation hashes and split-specific archetype "
            "proportions are known; exact RNG state, row order, and writer semantics are "
            "not."
        ),
        "exact PRNG and initialized state",
        "exact row ordering and serialization authority",
    ),
    **_evaluation_part(
        (
            "No production scorer is recovered; corrected six-cell numerical results "
            "remain research diagnostics."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3_M4,
}

_THRESHOLD_CLAIMS = {
    **_THRESHOLD_WORLD,
    **_POST_WORLD,
    D.COMPLETE_GENERATOR: _claim(
        D.COMPLETE_GENERATOR,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "The public generator contract is recoverable at the mathematical/semantic "
            "level; the separate hidden root and hidden materialization remain "
            "unresolved."
        ),
        "RES-365: world, observation, and dataset/split registries",
        missing=("private hidden-test root and hidden data bytes",),
        scope=("training", "public_validation"),
    ),
    **_rng_claims(
        algorithm=S.PARTIAL,
        state=S.PARTIAL,
        seed=S.EXACT,
        streams=S.EXACT,
        draw=S.EXACT,
        substreams=S.PARTIAL,
        seed_rationale=(
            "The public train/validation root is preserved; the separate "
            "private hidden-test root is scoped to an unresolved hidden "
            "design."
        ),
        seed_missing=(),
        algorithm_rationale=(
            "Preserved keyed RNG source uses NumPy default_rng but "
            "does not pin its bit generator or runtime."
        ),
        stream_rationale=(
            "Public participant/camp/trial streams are identified; "
            "hidden-test initialization is not established."
        ),
        substream_rationale=(
            "Public substream construction is source-defined; the "
            "separate private test root prevents whole-design "
            "exactness."
        ),
    ),
    **_OBS_POST,
    **_SCHEMA_POST,
    **_POST_SPLIT,
    **_POST_ORDERING,
    **_POST_SERIALIZATION,
    **_hash_claim(
        (
            "Public train/validation hashes are known, but exact PRNG state, row order, "
            "and writer semantics are incomplete."
        ),
        "exact PRNG state",
        "exact row ordering and serialization authority",
    ),
    **_evaluation_part(
        (
            "The 12-cell scorer remains proposed and unresolved, with no public "
            "calibration value or acceptance decision."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3,
}

_FIXED_CLAIMS = {
    **_FIXED_WORLD,
    **_POST_WORLD,
    **_rng_claims(
        algorithm=S.PARTIAL,
        state=S.PARTIAL,
        seed=S.EXACT,
        streams=S.EXACT,
        draw=S.EXACT,
        substreams=S.EXACT,
        seed_rationale=(
            "The public root and mathematical discrepancy seed are "
            "recorded; no hidden challenge was materialized."
        ),
        seed_missing=(),
        algorithm_rationale=(
            "M1 identifies keyed generator streams but not the exact PRNG bit generator/runtime."
        ),
        stream_rationale=(
            "World discrepancy, episode discrepancy, participant "
            "effects, and measurement streams are separated "
            "conceptually."
        ),
        substream_rationale=(
            "The versioned source fixes key hashing, channel names, and child-stream construction."
        ),
    ),
    **_OBS_POST,
    **_SCHEMA_POST,
    **_public_split_part(
        S.EXACT,
        rationale=(
            "M1 binds exact public train/validation roots, camp-group "
            "membership, and zero overlap; no hidden assignment is implied."
        ),
    ),
    **_POST_ORDERING,
    D.SERIALIZATION: _claim(
        D.SERIALIZATION,
        S.SEMANTICALLY_EQUIVALENT,
        (
            "M1 identifies the public Parquet artifacts and logical representation; exact "
            "writer version, row groups, metadata, and float encoding are not frozen."
        ),
        "RES-365: observation, representation, and dataset/split registries",
        missing=(
            "writer version, index handling, float encoding, metadata, compression, and row groups",
        ),
    ),
    **_hash_claim(
        (
            "M1 publishes fixed-mode train/validation hashes and a deterministic "
            "repeat-hash qualification, but exact clean-room hash reproduction lacks "
            "complete PRNG state, row order, and serialization authority."
        ),
        "exact PRNG and initialized state",
        "exact row ordering and byte-level Parquet settings",
    ),
    **_evaluation_part(
        (
            "The production scorer is unimplemented; fixed-mode six-cell results are "
            "research diagnostics, not production scores."
        ),
    ),
    **_MODEL_DEFERRED,
    **_RESULT_M3_M4,
}


_INITIAL_HASHES = _hashes(
    "6b26a9e74828fd9cf2b74a65edc39b77e25d71bfa525ce72049d39c49ba13fa9",
    "410bb30a7116d50c35cc723e3eedbb0f7ebe1b026b80627cd8e0e6cf07470545",
)
_CANONICAL_HASHES = _hashes(
    "bcddc1bf217033a54e8b88a1e18bd8677d030893e6cd39b7ad37dbe27185df2a",
    "16c132b2f398bad658f3dc9d29e609856d211e9c6d50b8934425288194f9968f",
)
_RICH_HASHES = _hashes(
    "78a6b86512d879b2af1a9c311616ce69ef30f63c087dbcf7319decc4fc4b5e47",
    "dc4da99b6b5c297e2dcbd5f051a0116027bb613a3311363bf72396cffa281b35",
)
_PRELIM_HASHES = _hashes(
    "3b15c95e0c3401f81b073ecd7133987c0220811a7c8876211dcc5f7a139d9471",
    "293d20551375c893577789c937ad6b86b2cf613f0e32caa8f3e2eab50a2038b4",
)
_PHASE_HASHES = _hashes(
    "c3a42297338a84e0dc9300a3d64100528c3e6d153ad6af6bd0837d0ecae27a4d",
    "b0db78f167cec78fe49992f71da187e2544c2c383adc2e9f1be37f1a577778f3",
)
_CORRELATED_HASHES = _hashes(
    "30f6ba1371908fde231b2f81ba989ccb7a141e1b4e19fe8c1f205b2d2b1a26cb",
    "018aa9885b7d9264170f0a413b815f4df6e5acbe3b9e8e10f3b99d9f0b979555",
)
_THRESHOLD_HASHES = _hashes(
    "f5d691156b19854224db9cf9f05ca1be1c149631ca2b451ad38979640f94ab60",
    "0fd0b288b306950187e39def57200f362758996107516899d6096ea1bdf552c6",
)
_FIXED_HASHES = _hashes(
    "7bcb327b3a391a1f6bcdf928b8f045edb8d4925e0b6d7d6e7261491766e0d5d3",
    "e2dbfc83b76ce240c013128582f58a34bd1d5b6e3092381a7223cf62ad10f00a",
)


def _make_splits(
    benchmark: str,
    hashes: tuple[ReferenceHash, ...],
    *,
    public_assignment: S,
    unit: SplitUnit,
    hidden_state: MaterializationState = MaterializationState.UNKNOWN,
    hidden_assignment: S = S.UNKNOWN,
    hidden_rows: int | None = None,
    hidden_planned_rows: int | None = None,
    hidden_unit: SplitUnit | None = None,
    assignment_rationale: str | None = None,
    assignment_missing: tuple[str, ...] | None = None,
) -> tuple[SplitReproductionAuthority, ...]:
    rows = {
        "initial_preseason_camp_recovery": (4096, 512),
        "canonical_preseason_camp_recovery": (4096, 512),
        "rich_history_camp_recovery": (15182, 3795),
        "preliminary_post_exposure_recovery": (72000, 12000),
        "phase_consistent_post_exposure_recovery": (72000, 12000),
        "correlated_exposure_recovery": (72000, 12000),
        "threshold_response_recovery": (72000, 12000),
        "fixed_mode_discrepancy_recovery": (72000, 12000),
    }
    if benchmark not in rows:
        raise ValueError(f"unknown benchmark identity: {benchmark}")
    train_rows, validation_rows = rows[benchmark]
    return _splits(
        train_rows=train_rows,
        validation_rows=validation_rows,
        unit=unit,
        assignment_status=public_assignment,
        hashes=hashes,
        hidden_state=hidden_state,
        hidden_assignment_status=hidden_assignment,
        hidden_rows=hidden_rows,
        hidden_planned_rows=hidden_planned_rows,
        hidden_unit=hidden_unit,
        assignment_rationale=assignment_rationale,
        assignment_missing=assignment_missing,
    )


def _serialization(file_format: str | None) -> SerializationAuthority:
    return SerializationAuthority(file_format, None, None, None, None, None, None)


def _contract(
    benchmark: str,
    claims: Mapping[D, ReproductionClaim],
    randomness: RandomnessAuthority,
    serialization: SerializationAuthority,
    splits: tuple[SplitReproductionAuthority, ...],
    hashes: tuple[ReferenceHash, ...],
    evaluation: EvaluationAuthority,
) -> BenchmarkReproductionContract:
    return BenchmarkReproductionContract(
        benchmark,
        _AUTHORITY,
        _profile(claims),
        randomness,
        serialization,
        splits,
        hashes,
        evaluation,
    )


def _registered_contracts() -> dict[str, BenchmarkReproductionContract]:
    contracts = {
        "initial_preseason_camp_recovery": _contract(
            "initial_preseason_camp_recovery",
            {
                **_CAMP_COMMON,
                D.SCHEMA: _CAMP_SCHEMA_INITIAL[D.SCHEMA],
                D.EVALUATION: _evaluation_claim(
                    (
                        "The accepted camp scorer is known, but the initial historical "
                        "score binding remains unresolved and the locked calibration "
                        "value is unavailable."
                    ),
                    "RES-367: evaluation and scorer registry",
                    "RES-366: result comparability registry",
                ),
            },
            _CAMP_RANDOMNESS,
            _serialization("JSONL"),
            _make_splits(
                "initial_preseason_camp_recovery",
                _INITIAL_HASHES,
                public_assignment=S.PARTIAL,
                unit=SplitUnit.PARTICIPANT,
                hidden_assignment=S.UNKNOWN,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _INITIAL_HASHES,
            _EVAL_CAMP_INITIAL,
        ),
        "canonical_preseason_camp_recovery": _contract(
            "canonical_preseason_camp_recovery",
            {
                **_CANONICAL_CAMP_COMMON,
                D.EVALUATION: _evaluation_claim(
                    (
                        "The accepted canonical camp scorer is identified, but its "
                        "task-locked calibration value is unavailable."
                    ),
                    "RES-367: evaluation and scorer registry",
                    "RES-366: result comparability registry",
                ),
            },
            _CAMP_RANDOMNESS,
            _serialization("JSONL"),
            _make_splits(
                "canonical_preseason_camp_recovery",
                _CANONICAL_HASHES,
                public_assignment=S.PARTIAL,
                unit=SplitUnit.PARTICIPANT_ORIGIN,
                hidden_assignment=S.UNKNOWN,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _CANONICAL_HASHES,
            _EVAL_CAMP_CANONICAL,
        ),
        "rich_history_camp_recovery": _contract(
            "rich_history_camp_recovery",
            _RICH_CLAIMS,
            _RICH_HISTORY_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "rich_history_camp_recovery",
                _RICH_HASHES,
                public_assignment=S.PARTIAL,
                unit=SplitUnit.CAMP,
                hidden_state=MaterializationState.NOT_RECOVERED,
                hidden_assignment=S.UNKNOWN,
                hidden_rows=None,
                hidden_unit=SplitUnit.CAMP,
                assignment_rationale=(
                    "Camp, participant, and origin grouping is source-defined, but the "
                    "historical per-origin H72/D7 presence mask cannot be replayed without "
                    "the original NumPy bit-generator/runtime binding."
                ),
                assignment_missing=(
                    "historical initialized NumPy state or bit-generator/runtime binding "
                    "for exact public query membership",
                ),
            ),
            _RICH_HASHES,
            _EVAL_RICH,
        ),
        "preliminary_post_exposure_recovery": _contract(
            "preliminary_post_exposure_recovery",
            _PRELIMINARY_CLAIMS,
            _EPISODE_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "preliminary_post_exposure_recovery",
                _PRELIM_HASHES,
                public_assignment=S.EXACT,
                unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _PRELIM_HASHES,
            _EVAL_UNIMPLEMENTED,
        ),
        "phase_consistent_post_exposure_recovery": _contract(
            "phase_consistent_post_exposure_recovery",
            _PHASE_CLAIMS,
            _EPISODE_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "phase_consistent_post_exposure_recovery",
                _PHASE_HASHES,
                public_assignment=S.EXACT,
                unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _PHASE_HASHES,
            _EVAL_PHASE,
        ),
        "correlated_exposure_recovery": _contract(
            "correlated_exposure_recovery",
            _CORRELATED_CLAIMS,
            _CORRELATED_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "correlated_exposure_recovery",
                _CORRELATED_HASHES,
                public_assignment=S.EXACT,
                unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _CORRELATED_HASHES,
            _EVAL_CORRELATED,
        ),
        "threshold_response_recovery": _contract(
            "threshold_response_recovery",
            _THRESHOLD_CLAIMS,
            _THRESHOLD_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "threshold_response_recovery",
                _THRESHOLD_HASHES,
                public_assignment=S.EXACT,
                unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
                hidden_assignment=S.PARTIAL,
                hidden_planned_rows=15750,
                hidden_unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
            ),
            _THRESHOLD_HASHES,
            _EVAL_THRESHOLD,
        ),
        "fixed_mode_discrepancy_recovery": _contract(
            "fixed_mode_discrepancy_recovery",
            _FIXED_CLAIMS,
            _FIXED_MODE_RANDOMNESS,
            _serialization("Parquet"),
            _make_splits(
                "fixed_mode_discrepancy_recovery",
                _FIXED_HASHES,
                public_assignment=S.EXACT,
                unit=SplitUnit.CAMP_PARTICIPANT_EPISODE,
                hidden_state=MaterializationState.NOT_MATERIALIZED,
                hidden_assignment=S.NOT_APPLICABLE,
                hidden_unit=SplitUnit.UNKNOWN,
            ),
            _FIXED_HASHES,
            _EVAL_FIXED,
        ),
    }
    if frozenset(contracts) != _EXPECTED_BENCHMARKS:
        raise ValueError(
            "reproduction registry must contain exactly the eight benchmark identities"
        )
    return contracts


REPRODUCTION_CONTRACTS: Mapping[str, BenchmarkReproductionContract] = MappingProxyType(
    _registered_contracts()
)


def get_reproduction_contract(name: str) -> BenchmarkReproductionContract:
    """Return the complete M1-backed reproduction authority for one benchmark."""
    return REPRODUCTION_CONTRACTS[name]
