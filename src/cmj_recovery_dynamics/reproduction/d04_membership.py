"""Replay D04 public split/query membership without generating scientific values."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from cmj_recovery_dynamics.reproduction.rich_history import PublicSplitName, opaque_key, seed_from

_D04_SPLIT_PARAMETERS: dict[
    PublicSplitName,
    tuple[
        int,
        float,
        float,
        tuple[float, float, float],
        tuple[float, float],
        tuple[float, float],
    ],
] = {
    "public_train": (
        512,
        0.55,
        0.55,
        (0.33, 0.34, 0.33),
        (0.7, 0.3),
        (0.40, 0.60),
    ),
    "public_validation": (
        128,
        0.50,
        0.60,
        (0.30, 0.40, 0.30),
        (0.6, 0.4),
        (0.45, 0.55),
    ),
}
_D04_KEY_NAMESPACE = "public-v3"
_PARTICIPANTS_PER_CAMP = 8
_ORIGINS_PER_PARTICIPANT = 2
_ORIGINS_PER_CAMP = _PARTICIPANTS_PER_CAMP * _ORIGINS_PER_PARTICIPANT
_HORIZONS: tuple[Literal["H72", "D7"], Literal["H72", "D7"]] = ("H72", "D7")


@dataclass(frozen=True, slots=True)
class D04MembershipRow:
    split_name: PublicSplitName
    camp_index: int
    participant_index: int
    origin_index: int
    horizon: Literal["H72", "D7"]
    horizon_presence: tuple[bool, bool]
    participant_key: str
    origin_key: str
    query_key: str


def _choice(rng: np.random.Generator, probabilities: tuple[float, ...], size: int) -> None:
    weights = np.asarray(probabilities, dtype=float)
    weights /= weights.sum()
    rng.choice(len(weights), size=size, p=weights)


def _d04_horizon_presence(
    split_name: PublicSplitName,
    camp_index: int,
    root_seed: str,
    split_parameters: tuple[
        int,
        float,
        float,
        tuple[float, float, float],
        tuple[float, float],
        tuple[float, float],
    ],
) -> NDArray[np.bool_]:
    _, p_quality_high, p_dense, intensity_probs, heterogeneity_probs, last_age_probs = (
        split_parameters
    )
    rng = np.random.default_rng(seed_from(root_seed, split_name, "camp", camp_index))

    quality_high = bool(rng.random() < p_quality_high)
    dense = bool(rng.random() < p_dense)
    intensity = np.asarray(intensity_probs, dtype=float)
    heterogeneity = np.asarray(heterogeneity_probs, dtype=float)
    rng.choice(3, p=intensity / np.sum(intensity))
    rng.choice(2, p=heterogeneity / np.sum(heterogeneity))
    monitor_probability = 0.9 if quality_high else 0.6
    n = _ORIGINS_PER_CAMP

    # Consume D04 participant-prior draws on the one shared camp Generator.
    rng.uniform(1.0, 12.0, size=_PARTICIPANTS_PER_CAMP)
    rng.normal(0.0, 1.0, size=_PARTICIPANTS_PER_CAMP)
    rng.normal(0.0, 1.0, size=(_PARTICIPANTS_PER_CAMP, 7))
    rng.uniform(0.20, 0.40, size=_PARTICIPANTS_PER_CAMP)
    rng.integers(0, 9, size=_PARTICIPANTS_PER_CAMP)

    k_low, k_high = (5, 6) if dense else (3, 4)
    exposure_counts = rng.integers(k_low, k_high + 1, size=n)
    windows = rng.uniform(504.0, 672.0, size=n)
    age_bands = np.asarray(((16.0, 44.0), (48.0, 220.0)))
    age_band_weights = np.asarray(last_age_probs, dtype=float)
    age_band_weights /= age_band_weights.sum()
    age_band_indices = rng.choice(len(age_bands), size=n, p=age_band_weights)
    latest_ages = rng.uniform(age_bands[age_band_indices, 0], age_bands[age_band_indices, 1])

    for origin in range(n):
        exposure_count = int(exposure_counts[origin])
        if exposure_count > 1:
            rng.uniform(
                -windows[origin] + 24.0,
                -latest_ages[origin] - 48.0,
                size=exposure_count - 1,
            )
        _choice(rng, (0.6, 0.3, 0.1), exposure_count)
        rng.uniform(0.5, 1.5, size=exposure_count)
        for _ in range(exposure_count):
            if rng.random() < monitor_probability:
                rng.uniform(14.0, 40.0)
            if rng.random() < monitor_probability:
                rng.uniform(60.0, 84.0)
        rng.uniform(0.0, 24.0)
        rng.uniform(-windows[origin], -6.0)

    trial_low, trial_high = (2, 3) if quality_high else (1, 3)
    rng.integers(trial_low, trial_high + 1, size=(n, 14))
    _choice(rng, (0.7, 0.3), n)
    rng.uniform(0.6, 1.4, size=n)
    plan_counts = rng.integers(0, 4, size=n)
    for plan_count in plan_counts:
        count = int(plan_count)
        if count:
            rng.uniform(24.0, 160.0, size=count)
            rng.uniform(0.5, 1.4, size=count)
            _choice(rng, (0.85, 0.15), count)
            rng.uniform(0.92, 1.0, size=count)

    # D04's observation draws advance the shared Generator; their values are not replayed.
    rng.normal(0.0, 0.02, size=(n, 14))
    rng.normal(0.0, 1.0, size=(n, 14))
    rng.normal(0.0, 1.0, size=(n, 14))
    rng.random((n, 14))
    rng.uniform(0.75, 0.92, size=(n, 14))
    rng.random((n, 14))
    rng.uniform(66.0, 78.0, size=n)
    rng.uniform(156.0, 180.0, size=n)
    rng.normal(0.0, 0.006, size=(n, 2))
    rng.normal(0.0, 1.0, size=(n, 2))
    rng.normal(0.0, 1.0, size=(n, 2))

    single_horizon = rng.random(n) < 0.15
    dropped_horizon = rng.integers(0, 2, size=n)
    present = np.ones((n, 2), dtype=bool)
    present[single_horizon, dropped_horizon[single_horizon]] = False
    return present


def replay_d04_membership(
    split_name: PublicSplitName, *, root_seed: str
) -> Iterator[D04MembershipRow]:
    """Yield only D04 camp, participant, origin, mask, and ordered query-key membership."""
    if not root_seed:
        raise ValueError("D04 public membership replay requires its public root seed")
    try:
        split_parameters = _D04_SPLIT_PARAMETERS[split_name]
    except KeyError as exc:
        raise ValueError(f"unknown D04 public split: {split_name}") from exc

    camp_count, *_ = split_parameters
    for camp_index in range(camp_count):
        presence = _d04_horizon_presence(split_name, camp_index, root_seed, split_parameters)
        for participant_index in range(_PARTICIPANTS_PER_CAMP):
            participant_key = opaque_key(
                _D04_KEY_NAMESPACE, "participant", split_name, camp_index, participant_index
            )
            for origin_index in range(_ORIGINS_PER_PARTICIPANT):
                origin_position = participant_index * _ORIGINS_PER_PARTICIPANT + origin_index
                horizon_presence = (
                    bool(presence[origin_position, 0]),
                    bool(presence[origin_position, 1]),
                )
                origin_key = opaque_key(
                    _D04_KEY_NAMESPACE,
                    "origin",
                    split_name,
                    camp_index,
                    participant_index,
                    origin_index,
                )
                for horizon_index, horizon in enumerate(_HORIZONS):
                    if horizon_presence[horizon_index]:
                        yield D04MembershipRow(
                            split_name,
                            camp_index,
                            participant_index,
                            origin_index,
                            horizon,
                            horizon_presence,
                            participant_key,
                            origin_key,
                            opaque_key(
                                _D04_KEY_NAMESPACE,
                                "query",
                                split_name,
                                camp_index,
                                participant_index,
                                origin_index,
                                horizon,
                            ),
                        )


def d04_membership_fingerprint(split_name: PublicSplitName, *, root_seed: str) -> str:
    """Hash canonical ordered public keys and horizons, without row values."""
    digest = hashlib.sha256()
    for row in replay_d04_membership(split_name, root_seed=root_seed):
        canonical_row = json.dumps(
            (row.participant_key, row.origin_key, row.query_key, row.horizon),
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest.update(canonical_row)
        digest.update(b"\n")
    return digest.hexdigest()


__all__ = ["D04MembershipRow", "d04_membership_fingerprint", "replay_d04_membership"]
