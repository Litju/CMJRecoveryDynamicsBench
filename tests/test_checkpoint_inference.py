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
    load_gate7_m1,
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (  # noqa: E402
    GATE7_FEATURE_NAMES,
)
from cmj_recovery_dynamics.observations.public_builder import (  # noqa: E402
    generate_gate7_fixture_v1,
)

pytestmark = pytest.mark.parametrize("candidate", ("M0", "M1"))


def _artifacts(
    tmp_path: Path, repeat: int = 0, *, candidate: str
) -> tuple[Path, Path, dict[str, Any]]:
    width = 32 if candidate == "M0" else 64
    prefix = "raw_small" if candidate == "M0" else "raw_wide"
    config: dict[str, Any] = {
        "family": FAMILY,
        "candidate": candidate,
        "seed_identity": {"candidate": candidate, "repeat": repeat},
        "raw_feature_count": 39,
        "hidden_width": 64,
        "data": {"feature_names": list(GATE7_FEATURE_NAMES), "target_order": list(TARGETS)},
        "target_order": list(TARGETS),
        "target_representation": "innovation",
        "target_transform": TARGET_TRANSFORM,
        "raw_transform": "train-only mean/std standardization",
        "preprocessor": {"raw_mean": [1.0] * 39, "raw_scale": [2.0] * 39},
    }
    config_path, weights_path = (
        tmp_path / f"config-r{repeat}.json",
        tmp_path / f"weights-r{repeat}.pt",
    )
    config_path.write_text(json.dumps(config))
    # Nonzero synthetic weights catch wrong matrix orientation and skipped scaling.
    state = {
        f"{prefix}.0.weight": torch.arange(width * 39).reshape(width, 39).float() / 100000,
        f"{prefix}.0.bias": torch.linspace(-0.5, 0.5, width),
        f"{prefix}.2.weight": torch.arange(2 * width).reshape(2, width).float() / 100,
        f"{prefix}.2.bias": torch.tensor([0.25 + repeat, -0.25 - repeat]),
    }
    torch.save(state, weights_path)
    return config_path, weights_path, config


def _load(config: Path, weights: Path, repeat: int = 0, *, candidate: str):
    loader = load_gate7_m0 if candidate == "M0" else load_gate7_m1
    return loader(
        config,
        weights,
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        repeat=repeat,
    )


@pytest.mark.parametrize("repeat", (0, 1))
def test_exact_forward_and_determinism(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    rng = torch.random.get_rng_state().clone()
    predictor = _load(config, weights, repeat, candidate=candidate)
    assert predictor.repeat == repeat
    assert torch.equal(rng, torch.random.get_rng_state())
    matrix = np.concatenate(
        [generate_gate7_fixture_v1(split).matrix() for split in ("training", "public_validation")]
    )
    assert matrix.shape == (24, 39)
    raw = torch.from_numpy(((matrix - 1) / 2).astype(np.float32))
    state = torch.load(weights, weights_only=True)
    prefix = "raw_small" if candidate == "M0" else "raw_wide"
    hidden = torch.nn.functional.gelu(
        torch.nn.functional.linear(raw, state[f"{prefix}.0.weight"], state[f"{prefix}.0.bias"]),
        approximate="none",
    )
    expected = torch.nn.functional.linear(
        hidden, state[f"{prefix}.2.weight"], state[f"{prefix}.2.bias"]
    ).numpy()
    actual = predictor.predict(matrix)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual, predictor.predict(matrix))
    assert actual.dtype == np.float64 and np.isfinite(actual).all()
    assert not predictor.model.training
    assert sum(p.numel() for p in predictor.model.parameters()) == (
        1346 if candidate == "M0" else 2690
    )
    for malformed in (np.zeros((1, 38)), np.full((1, 39), np.nan), np.full((1, 39), 1e300)):
        with pytest.raises(ValueError):
            predictor.predict(malformed)


@pytest.mark.parametrize(
    "field,value",
    [("candidate", "M8"), ("target_transform", "scaled"), ("target_order", TARGETS[::-1])],
)
@pytest.mark.parametrize("repeat", (0, 1))
def test_config_contract_rejection(
    tmp_path: Path, field: str, value: object, candidate: str, repeat: int
) -> None:
    path, weights, config = _artifacts(tmp_path, repeat, candidate=candidate)
    config[field] = value
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        _load(path, weights, repeat, candidate=candidate)


@pytest.mark.parametrize("repeat", (0, 1))
def test_scaler_repeat_and_hash_rejection(tmp_path: Path, candidate: str, repeat: int) -> None:
    path, weights, config = _artifacts(tmp_path, repeat, candidate=candidate)
    for value in (0, -1, float("nan")):
        config["preprocessor"]["raw_scale"][0] = value
        path.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="preprocessing"):
            _load(path, weights, repeat, candidate=candidate)
    config["seed_identity"]["repeat"] = 1 - repeat
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        _load(path, weights, repeat, candidate=candidate)
    with pytest.raises(ValueError, match="SHA-256"):
        loader = load_gate7_m0 if candidate == "M0" else load_gate7_m1
        loader(path, weights, config_sha256="0" * 64, checkpoint_sha256="0" * 64, repeat=0)


@pytest.mark.parametrize("repeat", (0, 1))
def test_tensor_contract_rejection(tmp_path: Path, candidate: str, repeat: int) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    state = torch.load(weights, weights_only=True)
    prefix = "raw_small" if candidate == "M0" else "raw_wide"
    width = 32 if candidate == "M0" else 64
    for value in (
        torch.zeros(1),
        torch.zeros(width, dtype=torch.float64),
        torch.full((width,), np.nan),
        torch.full((width,), np.inf),
        [0.0] * width,
    ):
        state[f"{prefix}.0.bias"] = value
        torch.save(state, weights)
        with pytest.raises(ValueError, match="tensor"):
            _load(config, weights, repeat, candidate=candidate)
    torch.save({"other": torch.zeros(1)}, weights)
    with pytest.raises(ValueError, match="state dict"):
        _load(config, weights, repeat, candidate=candidate)


class _UnsafePayload:
    def __reduce__(self) -> tuple[object, tuple[()]]:
        return eval, ()


@pytest.mark.parametrize("repeat", (0, 1))
def test_unsafe_globals_rejected_without_fallback(
    tmp_path: Path, candidate: str, repeat: int
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    torch.save(_UnsafePayload(), weights)
    with pytest.raises(pickle.UnpicklingError, match="Weights only load failed"):
        _load(config, weights, repeat, candidate=candidate)


@pytest.mark.parametrize("repeat", (0, 1))
def test_loader_always_requests_weights_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, candidate: str, repeat: int
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    calls: list[dict[str, object]] = []

    def rejected(*args: object, **kwargs: object) -> object:
        calls.append(kwargs)
        raise pickle.UnpicklingError("rejected")

    monkeypatch.setattr(torch, "load", rejected)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights, repeat, candidate=candidate)
    assert calls == [{"map_location": "cpu", "weights_only": True}]


def test_repeats_have_distinct_identities_and_outputs(tmp_path: Path, candidate: str) -> None:
    matrix = generate_gate7_fixture_v1().matrix()
    artifacts = [_artifacts(tmp_path, repeat, candidate=candidate) for repeat in (0, 1)]
    predictors = [
        _load(config, weights, repeat, candidate=candidate)
        for repeat, (config, weights, _) in enumerate(artifacts)
    ]
    assert tuple(p.repeat for p in predictors) == (0, 1)
    assert artifacts[0][0].read_bytes() != artifacts[1][0].read_bytes()
    assert artifacts[0][1].read_bytes() != artifacts[1][1].read_bytes()
    predictions = [p.predict(matrix) for p in predictors]
    assert not np.array_equal(predictions[0], predictions[1])
    for repeat, predictor in enumerate(predictors):
        np.testing.assert_array_equal(predictions[repeat], predictor.predict(matrix))
        config, weights, _ = artifacts[repeat]
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, 1 - repeat, candidate=candidate)


def test_target_order_is_immutable_and_json_compatible(candidate: str) -> None:
    assert type(TARGETS) is tuple
    assert TARGETS == ("relative_mean_concentric_force", "relative_concentric_net_impulse")
    assert json.loads(json.dumps(TARGETS)) == list(TARGETS)


@pytest.mark.parametrize("repeat", (0, 1))
def test_wrong_candidate_checkpoint_and_pinned_repeat_pair(
    tmp_path: Path, candidate: str, repeat: int
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    config_hash = hashlib.sha256(config.read_bytes()).hexdigest()
    checkpoint_hash = hashlib.sha256(weights.read_bytes()).hexdigest()
    loader = load_gate7_m0 if candidate == "M0" else load_gate7_m1
    _, wrong_repeat_weights, _ = _artifacts(tmp_path, 1 - repeat, candidate=candidate)
    with pytest.raises(ValueError, match="SHA-256"):
        loader(
            config,
            wrong_repeat_weights,
            config_sha256=config_hash,
            checkpoint_sha256=checkpoint_hash,
            repeat=repeat,
        )
    other = "M1" if candidate == "M0" else "M0"
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    _, wrong_candidate_weights, _ = _artifacts(other_dir, repeat, candidate=other)
    with pytest.raises(ValueError, match="state dict"):
        _load(config, wrong_candidate_weights, repeat, candidate=candidate)


@pytest.mark.parametrize("repeat", (0, 1))
@pytest.mark.parametrize("field", ("raw_mean", "raw_scale"))
@pytest.mark.parametrize("value", ([0.0], [float("inf")] * 39, [float("nan")] * 39))
def test_invalid_preprocessing_arrays(
    tmp_path: Path, candidate: str, repeat: int, field: str, value: list[float]
) -> None:
    config, weights, values = _artifacts(tmp_path, repeat, candidate=candidate)
    values["preprocessor"][field] = value
    config.write_text(json.dumps(values))
    with pytest.raises(ValueError, match="preprocessing"):
        _load(config, weights, repeat, candidate=candidate)


@pytest.mark.parametrize("repeat", (0, 1))
def test_nonfinite_network_output_rejected(tmp_path: Path, candidate: str, repeat: int) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    predictor = _load(config, weights, repeat, candidate=candidate)
    # Finite inputs and weights can still overflow during the network forward pass.
    with torch.no_grad():
        for parameter in predictor.model.parameters():
            parameter.fill_(torch.finfo(torch.float32).max)
    with pytest.raises(ValueError, match="predictions"):
        predictor.predict(np.full((1, 39), 2.0))


def test_m1_width_identity_rejected(tmp_path: Path, candidate: str) -> None:
    config, weights, values = _artifacts(tmp_path, candidate=candidate)
    if candidate == "M0":
        assert (
            sum(p.numel() for p in _load(config, weights, candidate=candidate).model.parameters())
            == 1346
        )
    else:
        values["hidden_width"] = 32
        config.write_text(json.dumps(values))
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, candidate=candidate)
