"""CPU inference for the original Gate7 M7 checkpoint family."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import torch
from numpy.typing import ArrayLike, NDArray
from torch import nn

from cmj_recovery_dynamics.model_reproduction.baselines import ModelInputError, _matrix  # pyright: ignore[reportPrivateUsage]
from cmj_recovery_dynamics.model_reproduction.checkpoint_inference import (
    FAMILY,
    M6_BASIS_CONSTANTS,
    M6_BASIS_NAMES,
    TARGET_TRANSFORM,
    TARGETS,
    _verified_bytes,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    GATE7_FEATURE_NAMES,
    GATE7_HISTORY_FEATURE_NAMES,
)

M7_BASIS_NAMES = M6_BASIS_NAMES
M7_BASIS_CONSTANTS = M6_BASIS_CONSTANTS


class _Gate7M7Model(nn.Module):
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
            nn.Linear(5, 16, device="cpu", dtype=torch.float32), nn.GELU(approximate="none")
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
                self.basis_projection(basis),
            ),
            dim=1,
        )
        return self.head(self.dropout(features))


@dataclass(frozen=True)
class Gate7M7Predictor:
    """Source-faithful CPU M7; pass raw features and explicit unscaled history.

    History uses gate7_history_projection_v1: four chronological pre-origin
    assessments in hours, N/kg, m/s and m. No padding, masks or imputation.
    Horizon indices are int64 (H72=0, D7=1). Basis is the unscaled five-value
    source-defined vector; M7 consumes all five standardized basis values.
    Callers must independently authenticate basis construction and row pairing.
    """

    repeat: int
    feature_mean: NDArray[np.float64]
    feature_scale: NDArray[np.float64]
    history_mean: NDArray[np.float64]
    history_scale: NDArray[np.float64]
    basis_mean: NDArray[np.float64]
    basis_scale: NDArray[np.float64]
    model: _Gate7M7Model

    def predict(
        self, features: ArrayLike, history: ArrayLike, horizon: ArrayLike, basis: ArrayLike
    ) -> NDArray[np.float64]:
        if any(np.ma.isMaskedArray(value) for value in (features, history, horizon, basis)):
            raise ModelInputError("Gate7 M7 inputs cannot contain masks")
        raw = _matrix(features, name="Gate7 raw features", columns=39)
        indices = np.asarray(horizon)
        if (
            indices.shape != (len(raw),)
            or indices.dtype != np.int64
            or not np.isin(indices, (0, 1)).all()
        ):
            raise ModelInputError("Gate7 M7 horizon must be int64 (N,), H72=0 or D7=1")
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


def load_gate7_m7(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M7Predictor:
    """Load an independently associated and pinned original M7 final repeat.

    Digest pins prove bytes, not provenance or config/checkpoint pairing. Establish
    those associations against the private inventory before calling this loader.
    """
    config = json.loads(_verified_bytes(config_path, config_sha256))
    payload = _verified_bytes(checkpoint_path, checkpoint_sha256)
    if (
        type(repeat) is not int
        or repeat not in (0, 1)
        or config["family"] != FAMILY
        or config["candidate"] != "M7"
        or config["seed_identity"]["candidate"] != "M7"
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
        or config["basis_names"] != list(M7_BASIS_NAMES)
        or config["basis_constants"] != dict(M7_BASIS_CONSTANTS)
    ):
        raise ValueError("config does not match the Gate7 M7 repeat/input/output contract")
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
        "basis_projection.0.weight": (16, 5),
        "basis_projection.0.bias": (16,),
        "head.weight": (2, 152),
        "head.bias": (2,),
    }
    loaded: object = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    if not isinstance(loaded, dict) or set(cast(dict[str, object], loaded)) != set(shapes):
        raise ValueError("checkpoint is not an exact Gate7 M7 state dict")
    state = cast(dict[str, torch.Tensor], loaded)
    for key, shape in shapes.items():
        value = state[key]
        if (
            type(value) is not torch.Tensor
            or tuple(value.shape) != shape
            or value.dtype != torch.float32
            or not bool(torch.isfinite(value).all())
        ):
            raise ValueError("checkpoint contains an invalid Gate7 M7 tensor")
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        model = _Gate7M7Model()
    model.load_state_dict(state)
    model.eval().requires_grad_(False)
    return Gate7M7Predictor(
        repeat,
        statistics[0],
        statistics[1],
        statistics[2],
        statistics[3],
        statistics[4],
        statistics[5],
        model,
    )
