"""D04 split membership is replayed independently from the SP03 scientific generator."""

from collections import defaultdict
from dataclasses import fields

from cmj_recovery_dynamics.reproduction import (
    D04MembershipRow,
    d04_membership_fingerprint,
    replay_d04_membership,
)
from cmj_recovery_dynamics.reproduction.rich_history import (
    D04_DATA_PRODUCER_COMMIT,
    D04_DATA_PRODUCER_TASK_TREE,
    D04_MANIFEST_BLOB_OID,
    D04_TRAIN_PARQUET_BLOB_OID,
    D04_VALIDATION_PARQUET_BLOB_OID,
    RICH_HISTORY_REPRODUCTION_METADATA,
    SP03_SOURCE_TREE,
    PublicSplitName,
)

_SPLITS: dict[PublicSplitName, tuple[int, int, int, int]] = {
    "public_train": (15182, 4096, 512, 8192),
    "public_validation": (3795, 1024, 128, 2048),
}


def test_d04_public_membership_geometry_and_masks() -> None:
    split_keys: dict[str, tuple[set[str], set[str], set[str]]] = {}
    for split_name, expected in _SPLITS.items():
        rows = list(replay_d04_membership(split_name))
        participants = {row.participant_key for row in rows}
        origins = {row.origin_key for row in rows}
        queries = {row.query_key for row in rows}
        participant_camps: dict[str, int] = {}
        participant_origins: dict[str, set[str]] = defaultdict(set)
        camp_participants: dict[int, set[str]] = defaultdict(set)
        origin_masks: dict[tuple[str, str], tuple[bool, bool]] = {}
        origin_horizons: dict[tuple[str, str], set[str]] = defaultdict(set)
        order: list[tuple[int, int, int, int]] = []
        for row in rows:
            participant_camps.setdefault(row.participant_key, row.camp_index)
            assert participant_camps[row.participant_key] == row.camp_index
            camp_participants[row.camp_index].add(row.participant_key)
            participant_origins[row.participant_key].add(row.origin_key)
            origin = (row.participant_key, row.origin_key)
            if origin in origin_masks:
                assert origin_masks[origin] == row.horizon_presence
            origin_masks[origin] = row.horizon_presence
            origin_horizons[origin].add(row.horizon)
            assert row.horizon_presence[0] or row.horizon_presence[1]
            order.append(
                (
                    row.camp_index,
                    row.participant_index,
                    row.origin_index,
                    0 if row.horizon == "H72" else 1,
                )
            )

        assert (len(rows), len(participants), len(camp_participants), len(origins)) == expected
        assert len(queries) == len(rows)
        assert len(origin_masks) == expected[3]
        assert all(len(value) == 2 for value in participant_origins.values())
        assert all(len(value) == 8 for value in camp_participants.values())
        for origin, mask in origin_masks.items():
            expected_horizons = {
                horizon for horizon, present in zip(("H72", "D7"), mask, strict=True) if present
            }
            assert origin_horizons[origin] == expected_horizons
        assert order == sorted(order)
        split_keys[split_name] = (participants, origins, queries)

    training, validation = split_keys["public_train"], split_keys["public_validation"]
    assert all(not training[index] & validation[index] for index in range(3))


def test_d04_ordered_membership_fingerprints_and_dual_authority() -> None:
    assert {field.name for field in fields(D04MembershipRow)} == {
        "split_name",
        "camp_index",
        "participant_index",
        "origin_index",
        "horizon",
        "horizon_presence",
        "participant_key",
        "origin_key",
        "query_key",
    }
    assert D04_DATA_PRODUCER_COMMIT == RICH_HISTORY_REPRODUCTION_METADATA.d04_materialization_commit
    assert D04_DATA_PRODUCER_TASK_TREE == (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_materialization_task_tree
    )
    assert D04_DATA_PRODUCER_TASK_TREE != SP03_SOURCE_TREE
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_materialization_repository_tree == (
        "c3c65d118cab0a368aafc7c1681a5660cd039bee"
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_manifest_blob_oid == D04_MANIFEST_BLOB_OID
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_train_parquet_blob_oid == (
        D04_TRAIN_PARQUET_BLOB_OID
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.d04_validation_parquet_blob_oid == (
        D04_VALIDATION_PARQUET_BLOB_OID
    )
    assert d04_membership_fingerprint("public_train") == (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_training_membership_sha256
    )
    assert d04_membership_fingerprint("public_validation") == (
        RICH_HISTORY_REPRODUCTION_METADATA.d04_public_validation_membership_sha256
    )
    assert RICH_HISTORY_REPRODUCTION_METADATA.split_assignment == "EXACT"
    assert RICH_HISTORY_REPRODUCTION_METADATA.row_ordering == "EXACT"
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_rng_algorithm == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.historical_rng_state == "PARTIAL"
    assert RICH_HISTORY_REPRODUCTION_METADATA.serialization == "SEMANTICALLY_EQUIVALENT"
    assert RICH_HISTORY_REPRODUCTION_METADATA.dataset_hash == "PARTIAL"
