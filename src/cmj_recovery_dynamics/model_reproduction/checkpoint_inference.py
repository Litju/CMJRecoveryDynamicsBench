"""Explicit private Gate7 M0 execution; importing this module requires PyTorch.

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
from typing import cast

import numpy as np
import torch
from numpy.typing import ArrayLike, NDArray
from torch import nn

from cmj_recovery_dynamics.model_reproduction.baselines import (
    ModelInputError,
    _matrix,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import GATE7_FEATURE_NAMES

FAMILY = "LCMJ-G6-public-sequence-hybrid-M0-M8-v1"
TARGETS = ["relative_mean_concentric_force", "relative_concentric_net_impulse"]
TARGET_TRANSFORM = "none; loss/evaluation uses train-only cell standard deviations"


def _verified_bytes(path: Path, expected: str) -> bytes:
    payload = path.read_bytes()
    if len(expected) != 64 or hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError("artifact SHA-256 mismatch")
    return payload


@dataclass(frozen=True)
class Gate7M0Predictor:
    """CPU float32 Gate7 M0, distinct from the initial-preseason reference identity."""

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


def load_gate7_m0(
    config_path: Path,
    checkpoint_path: Path,
    *,
    config_sha256: str,
    checkpoint_sha256: str,
    repeat: int,
) -> Gate7M0Predictor:
    """Load only an inventory-pinned M0 pair, with no deserialization fallback.

    Hashes authenticate bytes against the caller's evidence, not against a public
    model registry. Pair association must be established in that private evidence.
    """
    config = json.loads(_verified_bytes(config_path, config_sha256))
    payload = _verified_bytes(checkpoint_path, checkpoint_sha256)
    if (
        type(repeat) is not int
        or repeat not in (0, 1)
        or config["family"] != FAMILY
        or config["candidate"] != "M0"
        or config["seed_identity"]["candidate"] != "M0"
        or config["seed_identity"]["repeat"] != repeat
        or config["raw_feature_count"] != 39
        or config["data"]["feature_names"] != list(GATE7_FEATURE_NAMES)
        or config["target_order"] != TARGETS
        or config["data"]["target_order"] != TARGETS
        or config["target_representation"] != "innovation"
        or config["target_transform"] != TARGET_TRANSFORM
        or config["raw_transform"] != "train-only mean/std standardization"
    ):
        raise ValueError("config does not match the Gate7 M0 repeat/input/output contract")
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
        "raw_small.0.weight": (32, 39),
        "raw_small.0.bias": (32,),
        "raw_small.2.weight": (2, 32),
        "raw_small.2.bias": (2,),
    }
    if not isinstance(loaded, dict) or set(cast(dict[str, object], loaded)) != set(shapes):
        raise ValueError("checkpoint is not an exact Gate7 M0 state dict")
    state = cast(dict[str, torch.Tensor], loaded)
    for key, shape in shapes.items():
        value = state[key]
        if (
            type(value) is not torch.Tensor
            or tuple(value.shape) != shape
            or value.dtype != torch.float32
            or not bool(torch.isfinite(value).all())
        ):
            raise ValueError("checkpoint contains an invalid Gate7 M0 tensor")
    # Preserve the caller's RNG state; initialization is overwritten by fitted weights.
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        model = nn.Sequential(
            nn.Linear(39, 32, device="cpu", dtype=torch.float32),
            nn.GELU(approximate="none"),
            nn.Linear(32, 2, device="cpu", dtype=torch.float32),
        )
    model.load_state_dict({key.removeprefix("raw_small."): value for key, value in state.items()})
    model.eval().requires_grad_(False)
    mean.setflags(write=False)
    scale.setflags(write=False)
    return Gate7M0Predictor(repeat, mean, scale, model)
