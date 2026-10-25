"""Synthetic artifacts only: safe loading, exact execution and contract rejection."""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pytest

# PyTorch is an optional inference dependency; the base package stays NumPy-only.
torch = pytest.importorskip("torch")

from cmj_recovery_dynamics.model_reproduction.checkpoint_inference import (  # noqa: E402
    FAMILY,
    TARGET_TRANSFORM,
    TARGETS,
    load_gate7_m0,
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (  # noqa: E402
    GATE7_FEATURE_NAMES,
)
from cmj_recovery_dynamics.observations.public_builder import (  # noqa: E402
    generate_gate7_fixture_v1,
)


def _artifacts(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    config: dict[str, Any] = {
        "family": FAMILY,
        "candidate": "M0",
        "seed_identity": {"candidate": "M0", "repeat": 0},
        "raw_feature_count": 39,
        "data": {"feature_names": list(GATE7_FEATURE_NAMES), "target_order": TARGETS},
        "target_order": TARGETS,
        "target_representation": "innovation",
        "target_transform": TARGET_TRANSFORM,
        "raw_transform": "train-only mean/std standardization",
        "preprocessor": {"raw_mean": [1.0] * 39, "raw_scale": [2.0] * 39},
    }
    config_path, weights_path = tmp_path / "config.json", tmp_path / "weights.pt"
    config_path.write_text(json.dumps(config))
    # Nonzero synthetic weights catch wrong matrix orientation and skipped scaling.
    state = {
        "raw_small.0.weight": torch.arange(32 * 39).reshape(32, 39).float() / 100000,
        "raw_small.0.bias": torch.linspace(-0.5, 0.5, 32),
        "raw_small.2.weight": torch.arange(64).reshape(2, 32).float() / 100,
        "raw_small.2.bias": torch.tensor([0.25, -0.25]),
    }
    torch.save(state, weights_path)
    return config_path, weights_path, config


def _load(config: Path, weights: Path):
    return load_gate7_m0(
        config,
        weights,
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        repeat=0,
    )


def test_exact_forward_and_determinism(tmp_path: Path) -> None:
    config, weights, _ = _artifacts(tmp_path)
    rng = torch.random.get_rng_state().clone()
    predictor = _load(config, weights)
    assert torch.equal(rng, torch.random.get_rng_state())
    matrix = np.concatenate(
        [generate_gate7_fixture_v1(split).matrix() for split in ("training", "public_validation")]
    )
    assert matrix.shape == (24, 39)
    raw = torch.from_numpy(((matrix - 1) / 2).astype(np.float32))
    state = torch.load(weights, weights_only=True)
    hidden = torch.nn.functional.gelu(
        torch.nn.functional.linear(raw, state["raw_small.0.weight"], state["raw_small.0.bias"]),
        approximate="none",
    )
    expected = torch.nn.functional.linear(
        hidden, state["raw_small.2.weight"], state["raw_small.2.bias"]
    ).numpy()
    actual = predictor.predict(matrix)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual, predictor.predict(matrix))
    assert actual.dtype == np.float64 and np.isfinite(actual).all()
    assert not predictor.model.training
    assert sum(p.numel() for p in predictor.model.parameters()) == 1346
    for malformed in (np.zeros((1, 38)), np.full((1, 39), np.nan), np.full((1, 39), 1e300)):
        with pytest.raises(ValueError):
            predictor.predict(malformed)


@pytest.mark.parametrize(
    "field,value",
    [("candidate", "M1"), ("target_transform", "scaled"), ("target_order", TARGETS[::-1])],
)
def test_config_contract_rejection(tmp_path: Path, field: str, value: object) -> None:
    path, weights, config = _artifacts(tmp_path)
    config[field] = value
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        _load(path, weights)


def test_scaler_repeat_and_hash_rejection(tmp_path: Path) -> None:
    path, weights, config = _artifacts(tmp_path)
    for value in (0, -1, float("nan")):
        config["preprocessor"]["raw_scale"][0] = value
        path.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="preprocessing"):
            _load(path, weights)
    config["seed_identity"]["repeat"] = 1
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        _load(path, weights)
    with pytest.raises(ValueError, match="SHA-256"):
        load_gate7_m0(path, weights, config_sha256="0" * 64, checkpoint_sha256="0" * 64, repeat=0)


def test_tensor_contract_rejection(tmp_path: Path) -> None:
    config, weights, _ = _artifacts(tmp_path)
    state = torch.load(weights, weights_only=True)
    for value in (torch.zeros(1), torch.zeros(32, dtype=torch.float64), torch.full((32,), np.nan)):
        state["raw_small.0.bias"] = value
        torch.save(state, weights)
        with pytest.raises(ValueError, match="tensor"):
            _load(config, weights)
    torch.save({"other": torch.zeros(1)}, weights)
    with pytest.raises(ValueError, match="state dict"):
        _load(config, weights)


class _UnsafePayload:
    def __reduce__(self) -> tuple[object, tuple[()]]:
        return eval, ()


def test_unsafe_globals_rejected_without_fallback(tmp_path: Path) -> None:
    config, weights, _ = _artifacts(tmp_path)
    torch.save(_UnsafePayload(), weights)
    with pytest.raises(pickle.UnpicklingError, match="Weights only load failed"):
        _load(config, weights)


def test_loader_always_requests_weights_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, weights, _ = _artifacts(tmp_path)
    calls: list[dict[str, object]] = []

    def rejected(*args: object, **kwargs: object) -> object:
        calls.append(kwargs)
        raise pickle.UnpicklingError("rejected")

    monkeypatch.setattr(torch, "load", rejected)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights)
    assert calls == [{"map_location": "cpu", "weights_only": True}]
