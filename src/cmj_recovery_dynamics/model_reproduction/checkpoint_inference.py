"""Explicit private Gate7 M0/M1/M2/M3/M6 execution; importing this module requires PyTorch.

No artifacts are bundled or discovered. Callers must supply independently verified
config/checkpoint hash pairs from their private inventory. Outputs are innovations
in target order, with no inverse scaling or baseline addition.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import numpy as np
import torch
from numpy.typing import ArrayLike, NDArray
from torch import nn

from cmj_recovery_dynamics.model_reproduction.baselines import (
    ModelInputError,
    _matrix,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_FEATURE_NAMES,
    GATE7_HISTORY_FEATURE_NAMES,
)

FAMILY = "LCMJ-G6-public-sequence-hybrid-M0-M8-v1"
TARGETS: Final = ("relative_mean_concentric_force", "relative_concentric_net_impulse")
TARGET_TRANSFORM = "none; loss/evaluation uses train-only cell standard deviations"


def _verified_bytes(path: Path, expected: str) -> bytes:
    payload = path.read_bytes()
    if len(expected) != 64 or hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError("artifact SHA-256 mismatch")
    return payload


@dataclass(frozen=True)
class _Gate7RawPredictor:
    """Verified raw-only float32 inference shared by the recovered M0, M1 and M2."""

    repeat: int
    feature_mean: NDArray[np.float64]
    feature_scale: NDArray[np.float64]
    model: nn.Sequential

    def predict(self, features: ArrayLike) -> NDArray[np.float64]:
        raw = _matrix(features, name="Gate7 raw features", columns=39)
        with np.errstate(over="ignore", invalid="ignore"):
            standardized = ((raw - self.feature_mean) / self.feature_scale).astype(np.float32)
        if not np.isfinite(standardized).all():
            raise ModelInputError("Gate7 preprocessing produced non-finite float32 values")
        self.model.eval()
        with torch.inference_mode():
            tensor = torch.from_numpy(standardized)  # pyright: ignore[reportUnknownMemberType]
            prediction = self.model(tensor).numpy().astype(np.float64)
        if prediction.shape != (len(raw), 2) or not np.isfinite(prediction).all():
            raise ModelInputError("Gate7 produced non-finite or incorrectly shaped predictions")
        return prediction


@dataclass(frozen=True)
class Gate7M0Predictor(_Gate7RawPredictor):
    """CPU float32 Gate7 M0, distinct from the initial-preseason reference identity."""


@dataclass(frozen=True)
class Gate7M1Predictor(_Gate7RawPredictor):
    """CPU float32 Gate7 M1: source-verified 39→64→2 raw-only network."""


@dataclass(frozen=True)
class Gate7M2Predictor(_Gate7RawPredictor):
    """CPU float32 Gate7 M2: source-verified 39→64→64→2 raw-only network."""


def load_gate7_m0(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M0Predictor:
    """Load an independently pinned M0 pair with weights-only deserialization.

    Hashes pin bytes, not provenance or pair association. Establish the exact
    candidate/repeat/config/checkpoint association in private evidence first.
    """
    mean, scale, model = _load_gate7_raw_mlp(
        config_path,
        checkpoint_path,
        config_sha256=config_sha256,
        checkpoint_sha256=checkpoint_sha256,
        repeat=repeat,
        candidate="M0",
        width=32,
        prefix="raw_small",
    )
    return Gate7M0Predictor(repeat, mean, scale, model)


def load_gate7_m1(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M1Predictor:
    """Load an independently pinned M1 pair with weights-only deserialization.

    Hashes pin bytes, not provenance or pair association. Establish the exact
    candidate/repeat/config/checkpoint association in private evidence first.
    """
    mean, scale, model = _load_gate7_raw_mlp(
        config_path,
        checkpoint_path,
        config_sha256=config_sha256,
        checkpoint_sha256=checkpoint_sha256,
        repeat=repeat,
        candidate="M1",
        width=64,
        prefix="raw_wide",
    )
    return Gate7M1Predictor(repeat, mean, scale, model)


def load_gate7_m2(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M2Predictor:
    """Load an independently pinned M2 pair with weights-only deserialization.

    Establish candidate/repeat/config/checkpoint association against the private
    recovery inventory first. Digest pins alone do not establish provenance.
    M2 consumes only raw features; its original forward ignores other branches.
    """
    mean, scale, model = _load_gate7_raw_mlp(
        config_path,
        checkpoint_path,
        config_sha256=config_sha256,
        checkpoint_sha256=checkpoint_sha256,
        repeat=repeat,
        candidate="M2",
        width=64,
        prefix="raw_deep",
    )
    return Gate7M2Predictor(repeat, mean, scale, model)


def _load_gate7_raw_mlp(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
    candidate: str,
    width: int,
    prefix: str,
) -> tuple[NDArray[np.float64], NDArray[np.float64], nn.Sequential]:
    config = json.loads(_verified_bytes(config_path, config_sha256))
    payload = _verified_bytes(checkpoint_path, checkpoint_sha256)
    if (
        type(repeat) is not int
        or repeat not in (0, 1)
        or config["family"] != FAMILY
        or config["candidate"] != candidate
        or config["seed_identity"]["candidate"] != candidate
        or config["seed_identity"]["repeat"] != repeat
        or (candidate in ("M1", "M2") and config.get("hidden_width") != 64)
        or config["raw_feature_count"] != 39
        or config["data"]["feature_names"] != list(GATE7_FEATURE_NAMES)
        or config["target_order"] != list(TARGETS)
        or config["data"]["target_order"] != list(TARGETS)
        or config["target_representation"] != "innovation"
        or config["target_transform"] != TARGET_TRANSFORM
        or config["raw_transform"] != "train-only mean/std standardization"
    ):
        raise ValueError(
            f"config does not match the Gate7 {candidate} repeat/input/output contract"
        )
    mean = np.asarray(config["preprocessor"]["raw_mean"], dtype=np.float64)
    scale = np.asarray(config["preprocessor"]["raw_scale"], dtype=np.float64)
    if (
        mean.shape != (39,)
        or scale.shape != (39,)
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or (scale <= 0).any()
    ):
        raise ValueError("invalid fitted Gate7 raw preprocessing")
    loaded: object = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    shapes = {
        f"{prefix}.0.weight": (width, 39),
        f"{prefix}.0.bias": (width,),
        f"{prefix}.2.weight": (2, width),
        f"{prefix}.2.bias": (2,),
    }
    if candidate == "M2":
        shapes.update(
            {
                f"{prefix}.2.weight": (64, 64),
                f"{prefix}.2.bias": (64,),
                f"{prefix}.4.weight": (2, 64),
                f"{prefix}.4.bias": (2,),
            }
        )
    if not isinstance(loaded, dict) or set(cast(dict[str, object], loaded)) != set(shapes):
        raise ValueError(f"checkpoint is not an exact Gate7 {candidate} state dict")
    state = cast(dict[str, torch.Tensor], loaded)
    for key, shape in shapes.items():
        value = state[key]
        if (
            type(value) is not torch.Tensor
            or tuple(value.shape) != shape
            or value.dtype != torch.float32
            or not bool(torch.isfinite(value).all())
        ):
            raise ValueError(f"checkpoint contains an invalid Gate7 {candidate} tensor")
    # Preserve the caller's RNG state; initialization is overwritten by fitted weights.
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        if candidate == "M2":
            model = nn.Sequential(
                nn.Linear(39, 64, device="cpu", dtype=torch.float32),
                nn.GELU(approximate="none"),
                nn.Linear(64, 64, device="cpu", dtype=torch.float32),
                nn.GELU(approximate="none"),
                nn.Linear(64, 2, device="cpu", dtype=torch.float32),
            )
        else:
            model = nn.Sequential(
                nn.Linear(39, width, device="cpu", dtype=torch.float32),
                nn.GELU(approximate="none"),
                nn.Linear(width, 2, device="cpu", dtype=torch.float32),
            )
    model.load_state_dict({key.removeprefix(f"{prefix}."): value for key, value in state.items()})
    model.eval().requires_grad_(False)
    mean.setflags(write=False)
    scale.setflags(write=False)
    return mean, scale, model


class _Gate7M3Model(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.raw_backbone = nn.Sequential(
            nn.Linear(39, 64, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
            nn.Linear(64, 64, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
        )
        self.dropout = nn.Dropout(0.10)
        self.history_encoder = nn.Sequential(
            nn.Linear(4, 32, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
        )
        self.head = nn.Linear(128, 2, device="cpu", dtype=torch.float32)

    def forward(self, raw: torch.Tensor, history: torch.Tensor) -> torch.Tensor:
        raw_state = self.dropout(self.raw_backbone(raw))
        encoded = self.history_encoder(history)
        sequence_state = torch.cat((encoded.mean(dim=1), encoded[:, -1]), dim=1)
        return self.head(self.dropout(torch.cat((raw_state, sequence_state), dim=1)))


@dataclass(frozen=True)
class Gate7M3Predictor:
    """Source-faithful CPU M3; pass raw features and explicit unscaled history.

    History uses gate7_history_projection_v1: four chronological pre-origin
    assessments in hours, N/kg, m/s and m. No padding, masks or imputation.
    Separate horizon/basis tensors are unused by the original M3 forward.
    """

    repeat: int
    feature_mean: NDArray[np.float64]
    feature_scale: NDArray[np.float64]
    history_mean: NDArray[np.float64]
    history_scale: NDArray[np.float64]
    model: _Gate7M3Model

    def predict(self, features: ArrayLike, history: ArrayLike) -> NDArray[np.float64]:
        raw = _matrix(features, name="Gate7 raw features", columns=39)
        if np.ma.isMaskedArray(history) or np.ma.isMaskedArray(features):
            raise ModelInputError("Gate7 M3 inputs cannot contain masks")
        tokens = np.asarray(history, dtype=np.float64)
        if tokens.shape != (len(raw), 4, 4) or not np.isfinite(tokens).all():
            raise ModelInputError("Gate7 history must be finite (N,4,4); no masks or padding")
        if (tokens[:, :, 0] >= 0).any() or (np.diff(tokens[:, :, 0], axis=1) < 0).any():
            raise ModelInputError("Gate7 history must be chronological and strictly pre-origin")
        # Both source extractors read these same observations; reject mispaired rows.
        if not np.array_equal(raw[:, 7:23], tokens.reshape(len(raw), 16)):
            raise ModelInputError("Gate7 raw/history observation ordering mismatch")
        with np.errstate(over="ignore", invalid="ignore"):
            standardized = ((raw - self.feature_mean) / self.feature_scale).astype(np.float32)
            history_tensor = ((tokens - self.history_mean) / self.history_scale).astype(np.float32)
        if not np.isfinite(standardized).all() or not np.isfinite(history_tensor).all():
            raise ModelInputError("Gate7 preprocessing produced non-finite float32 values")
        self.model.eval()
        with torch.inference_mode():
            prediction = (
                self.model(
                    torch.from_numpy(standardized),  # pyright: ignore[reportUnknownMemberType]
                    torch.from_numpy(history_tensor),  # pyright: ignore[reportUnknownMemberType]
                )
                .numpy()
                .astype(np.float64)
            )
        if prediction.shape != (len(raw), 2) or not np.isfinite(prediction).all():
            raise ModelInputError("Gate7 produced non-finite or incorrectly shaped predictions")
        return prediction


def load_gate7_m3(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M3Predictor:
    """Load an independently associated and pinned original M3 final repeat.

    Digest pins prove bytes, not provenance or config/checkpoint pairing. Establish
    those associations against the private inventory before calling this loader.
    """
    config = json.loads(_verified_bytes(config_path, config_sha256))
    payload = _verified_bytes(checkpoint_path, checkpoint_sha256)
    if (
        type(repeat) is not int
        or repeat not in (0, 1)
        or config["family"] != FAMILY
        or config["candidate"] != "M3"
        or config["seed_identity"]["candidate"] != "M3"
        or config["seed_identity"]["repeat"] != repeat
        or config["raw_feature_count"] != 39
        or config["hidden_width"] != 64
        or config["history_width"] != 32
        or config["history_tokens"] != 4
        or config["history_token_features"] != list(GATE7_HISTORY_FEATURE_NAMES)
        or config["dropout"] != 0.10
        or config["data"]["feature_names"] != list(GATE7_FEATURE_NAMES)
        or config["target_order"] != list(TARGETS)
        or config["data"]["target_order"] != list(TARGETS)
        or config["target_representation"] != "innovation"
        or config["target_transform"] != TARGET_TRANSFORM
        or config["raw_transform"] != "train-only mean/std standardization"
    ):
        raise ValueError("config does not match the Gate7 M3 repeat/input/output contract")
    statistics: list[NDArray[np.float64]] = []
    for branch, width in (("raw", 39), ("history", 4)):
        mean = np.asarray(config["preprocessor"][f"{branch}_mean"], dtype=np.float64)
        scale = np.asarray(config["preprocessor"][f"{branch}_scale"], dtype=np.float64)
        if (
            mean.shape != (width,)
            or scale.shape != (width,)
            or not np.isfinite(mean).all()
            or not np.isfinite(scale).all()
            or (scale <= 0).any()
        ):
            raise ValueError(f"invalid fitted Gate7 {branch} preprocessing")
        mean.setflags(write=False)
        scale.setflags(write=False)
        statistics.extend((mean, scale))
    shapes = {
        "raw_backbone.0.weight": (64, 39),
        "raw_backbone.0.bias": (64,),
        "raw_backbone.2.weight": (64, 64),
        "raw_backbone.2.bias": (64,),
        "history_encoder.0.weight": (32, 4),
        "history_encoder.0.bias": (32,),
        "head.weight": (2, 128),
        "head.bias": (2,),
    }
    loaded: object = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    if not isinstance(loaded, dict) or set(cast(dict[str, object], loaded)) != set(shapes):
        raise ValueError("checkpoint is not an exact Gate7 M3 state dict")
    state = cast(dict[str, torch.Tensor], loaded)
    for key, shape in shapes.items():
        value = state[key]
        if (
            type(value) is not torch.Tensor
            or tuple(value.shape) != shape
            or value.dtype != torch.float32
            or not bool(torch.isfinite(value).all())
        ):
            raise ValueError("checkpoint contains an invalid Gate7 M3 tensor")
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        model = _Gate7M3Model()
    model.load_state_dict(state)
    model.eval().requires_grad_(False)
    return Gate7M3Predictor(
        repeat, statistics[0], statistics[1], statistics[2], statistics[3], model
    )


M6_BASIS_NAMES: Final = (
    "w2_fast_duration_weighted",
    "w2_slow_duration_weighted",
    "w3_total_dose",
    "w3_fast_increment_weighted",
    "w3_slow_increment_weighted",
)
M6_BASIS_CONSTANTS: Final = (
    ("w2_fast_hours", 36.0),
    ("w2_slow_hours", 120.0),
    ("w2_beta", 1.0),
    ("w3_kappa", 10.0),
    ("w3_delta", 1.0),
    ("w3_gamma", 1.0),
)


class _Gate7M6Model(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.raw_backbone = nn.Sequential(
            nn.Linear(39, 64, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
            nn.Linear(64, 64, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
        )
        self.dropout = nn.Dropout(0.10)
        self.history_gru = nn.GRU(
            4, 32, num_layers=1, batch_first=True, device="cpu", dtype=torch.float32
        )
        self.horizon_embedding = nn.Embedding(2, 8, device="cpu", dtype=torch.float32)
        self.basis_projection = nn.Sequential(
            nn.Linear(2, 16, device="cpu", dtype=torch.float32), nn.GELU(approximate="none")
        )
        self.head = nn.Linear(152, 2, device="cpu", dtype=torch.float32)

    def forward(
        self, raw: torch.Tensor, history: torch.Tensor, horizon: torch.Tensor, basis: torch.Tensor
    ) -> torch.Tensor:
        raw_state = self.dropout(self.raw_backbone(raw))
        encoded, _ = self.history_gru(history)
        sequence_state = torch.cat((encoded.mean(dim=1), encoded[:, -1]), dim=1)
        features = torch.cat(
            (
                raw_state,
                sequence_state,
                self.horizon_embedding(horizon),
                self.basis_projection(basis[:, :2]),
            ),
            dim=1,
        )
        return self.head(self.dropout(features))


@dataclass(frozen=True)
class Gate7M6Predictor:
    """Source-faithful CPU M6; pass raw features and explicit unscaled history.

    History uses gate7_history_projection_v1: four chronological pre-origin
    assessments in hours, N/kg, m/s and m. No padding, masks or imputation.
    Horizon indices are int64 (H72=0, D7=1). Basis is the unscaled five-value
    source-defined vector; M6 consumes its first two standardized W2 values.
    Callers must independently authenticate basis construction and row pairing.
    """

    repeat: int
    feature_mean: NDArray[np.float64]
    feature_scale: NDArray[np.float64]
    history_mean: NDArray[np.float64]
    history_scale: NDArray[np.float64]
    basis_mean: NDArray[np.float64]
    basis_scale: NDArray[np.float64]
    model: _Gate7M6Model

    def predict(
        self, features: ArrayLike, history: ArrayLike, horizon: ArrayLike, basis: ArrayLike
    ) -> NDArray[np.float64]:
        if any(np.ma.isMaskedArray(value) for value in (features, history, horizon, basis)):
            raise ModelInputError("Gate7 M6 inputs cannot contain masks")
        raw = _matrix(features, name="Gate7 raw features", columns=39)
        indices = np.asarray(horizon)
        if (
            indices.shape != (len(raw),)
            or indices.dtype != np.int64
            or not np.isin(indices, (0, 1)).all()
        ):
            raise ModelInputError("Gate7 M6 horizon must be int64 (N,), H72=0 or D7=1")
        if not np.array_equal(raw[:, 2:4], np.column_stack((indices == 0, indices == 1))):
            raise ModelInputError("Gate7 raw/horizon observation ordering mismatch")
        basis_values = _matrix(basis, name="Gate7 basis", columns=5)
        if len(basis_values) != len(raw):
            raise ModelInputError("Gate7 basis row count mismatch")
        tokens = np.asarray(history, dtype=np.float64)
        if tokens.shape != (len(raw), 4, 4) or not np.isfinite(tokens).all():
            raise ModelInputError("Gate7 history must be finite (N,4,4); no masks or padding")
        if (tokens[:, :, 0] >= 0).any() or (np.diff(tokens[:, :, 0], axis=1) < 0).any():
            raise ModelInputError("Gate7 history must be chronological and strictly pre-origin")
        # Both source extractors read these same observations; reject mispaired rows.
        if not np.array_equal(raw[:, 7:23], tokens.reshape(len(raw), 16)):
            raise ModelInputError("Gate7 raw/history observation ordering mismatch")
        with np.errstate(over="ignore", invalid="ignore"):
            standardized = ((raw - self.feature_mean) / self.feature_scale).astype(np.float32)
            history_tensor = ((tokens - self.history_mean) / self.history_scale).astype(np.float32)
            basis_tensor = ((basis_values - self.basis_mean) / self.basis_scale).astype(np.float32)
        if not all(np.isfinite(x).all() for x in (standardized, history_tensor, basis_tensor)):
            raise ModelInputError("Gate7 preprocessing produced non-finite float32 values")
        self.model.eval()
        with torch.inference_mode():
            prediction = (
                self.model(
                    torch.from_numpy(standardized),  # pyright: ignore[reportUnknownMemberType]
                    torch.from_numpy(history_tensor),  # pyright: ignore[reportUnknownMemberType]
                    torch.from_numpy(indices),  # pyright: ignore[reportUnknownMemberType]
                    torch.from_numpy(basis_tensor),  # pyright: ignore[reportUnknownMemberType]
                )
                .numpy()
                .astype(np.float64)
            )
        if prediction.shape != (len(raw), 2) or not np.isfinite(prediction).all():
            raise ModelInputError("Gate7 produced non-finite or incorrectly shaped predictions")
        return prediction


def load_gate7_m6(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M6Predictor:
    """Load an independently associated and pinned original M6 final repeat.

    Digest pins prove bytes, not provenance or config/checkpoint pairing. Establish
    those associations against the private inventory before calling this loader.
    """
    config = json.loads(_verified_bytes(config_path, config_sha256))
    payload = _verified_bytes(checkpoint_path, checkpoint_sha256)
    if (
        type(repeat) is not int
        or repeat not in (0, 1)
        or config["family"] != FAMILY
        or config["candidate"] != "M6"
        or config["seed_identity"]["candidate"] != "M6"
        or type(config["seed_identity"]["repeat"]) is not int
        or config["seed_identity"]["repeat"] != repeat
        or config["raw_feature_count"] != 39
        or config["hidden_width"] != 64
        or config["history_width"] != 32
        or type(config["gru_layers"]) is not int
        or config["gru_layers"] != 1
        or config["history_tokens"] != 4
        or config["history_token_features"] != list(GATE7_HISTORY_FEATURE_NAMES)
        or config["dropout"] != 0.10
        or config["data"]["feature_names"] != list(GATE7_FEATURE_NAMES)
        or config["target_order"] != list(TARGETS)
        or config["data"]["target_order"] != list(TARGETS)
        or config["target_representation"] != "innovation"
        or config["target_transform"] != TARGET_TRANSFORM
        or config["raw_transform"] != "train-only mean/std standardization"
        or config["basis_transform"] != "train-only mean/std standardization"
        or config["basis_names"] != list(M6_BASIS_NAMES)
        or config["basis_constants"] != dict(M6_BASIS_CONSTANTS)
    ):
        raise ValueError("config does not match the Gate7 M6 repeat/input/output contract")
    statistics: list[NDArray[np.float64]] = []
    for branch, width in (("raw", 39), ("history", 4), ("basis", 5)):
        mean = np.asarray(config["preprocessor"][f"{branch}_mean"], dtype=np.float64)
        scale = np.asarray(config["preprocessor"][f"{branch}_scale"], dtype=np.float64)
        if (
            mean.shape != (width,)
            or scale.shape != (width,)
            or not np.isfinite(mean).all()
            or not np.isfinite(scale).all()
            or (scale <= 0).any()
        ):
            raise ValueError(f"invalid fitted Gate7 {branch} preprocessing")
        mean.setflags(write=False)
        scale.setflags(write=False)
        statistics.extend((mean, scale))
    shapes = {
        "raw_backbone.0.weight": (64, 39),
        "raw_backbone.0.bias": (64,),
        "raw_backbone.2.weight": (64, 64),
        "raw_backbone.2.bias": (64,),
        "history_gru.weight_ih_l0": (96, 4),
        "history_gru.weight_hh_l0": (96, 32),
        "history_gru.bias_ih_l0": (96,),
        "history_gru.bias_hh_l0": (96,),
        "horizon_embedding.weight": (2, 8),
        "basis_projection.0.weight": (16, 2),
        "basis_projection.0.bias": (16,),
        "head.weight": (2, 152),
        "head.bias": (2,),
    }
    loaded: object = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    if not isinstance(loaded, dict) or set(cast(dict[str, object], loaded)) != set(shapes):
        raise ValueError("checkpoint is not an exact Gate7 M6 state dict")
    state = cast(dict[str, torch.Tensor], loaded)
    for key, shape in shapes.items():
        value = state[key]
        if (
            type(value) is not torch.Tensor
            or tuple(value.shape) != shape
            or value.dtype != torch.float32
            or not bool(torch.isfinite(value).all())
        ):
            raise ValueError("checkpoint contains an invalid Gate7 M6 tensor")
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        model = _Gate7M6Model()
    model.load_state_dict(state)
    model.eval().requires_grad_(False)
    return Gate7M6Predictor(
        repeat,
        statistics[0],
        statistics[1],
        statistics[2],
        statistics[3],
        statistics[4],
        statistics[5],
        model,
    )
