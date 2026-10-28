"""Explicit private Gate7 M0/M1/M2 execution; importing this module requires PyTorch.

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
from cmj_recovery_dynamics.model_reproduction.gate7_projection import GATE7_FEATURE_NAMES

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
