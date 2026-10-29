"""Synthetic M5 parameters only; original checkpoints and observations stay private."""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from cmj_recovery_dynamics.model_reproduction.checkpoint_inference import (  # noqa: E402
    FAMILY,
    TARGET_TRANSFORM,
    TARGETS,
    load_gate7_m5,
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (  # noqa: E402
    GATE7_FEATURE_NAMES,
    GATE7_HISTORY_FEATURE_NAMES,
    project_gate7_history_v1,
)
from cmj_recovery_dynamics.observations.public_builder import (  # noqa: E402
    generate_gate7_fixture_v1,
)

SHAPES = {
    "raw_backbone.0.weight": (64, 39),
    "raw_backbone.0.bias": (64,),
    "raw_backbone.2.weight": (64, 64),
    "raw_backbone.2.bias": (64,),
    "history_gru.weight_ih_l0": (96, 4),
    "history_gru.weight_hh_l0": (96, 32),
    "history_gru.bias_ih_l0": (96,),
    "history_gru.bias_hh_l0": (96,),
    "horizon_embedding.weight": (2, 8),
    "head.weight": (2, 136),
    "head.bias": (2,),
}
pytestmark = pytest.mark.parametrize("repeat", (0, 1))


def _artifacts(tmp_path: Path, repeat: int) -> tuple[Path, Path, dict[str, Any]]:
    config: dict[str, Any] = {
        "family": FAMILY,
        "candidate": "M5",
        "seed_identity": {"candidate": "M5", "repeat": repeat},
        "raw_feature_count": 39,
        "hidden_width": 64,
        "history_width": 32,
        "history_tokens": 4,
        "history_token_features": list(GATE7_HISTORY_FEATURE_NAMES),
        "gru_layers": 1,
        "dropout": 0.10,
        "data": {"feature_names": list(GATE7_FEATURE_NAMES), "target_order": list(TARGETS)},
        "target_order": list(TARGETS),
        "target_representation": "innovation",
        "target_transform": TARGET_TRANSFORM,
        "raw_transform": "train-only mean/std standardization",
        "preprocessor": {
            "raw_mean": [1.0] * 39,
            "raw_scale": [2.0] * 39,
            "history_mean": [-100.0, 20.0, 2.0, 0.3],
            "history_scale": [60.0, 2.0, 0.2, 0.1],
        },
    }
    path, weights = tmp_path / "config.json", tmp_path / "weights.pt"
    path.write_text(json.dumps(config))
    state = {
        name: torch.linspace(-0.03, 0.04, int(np.prod(shape))).reshape(shape)
        for name, shape in SHAPES.items()
    }
    state["head.bias"] = torch.tensor([0.25 + repeat, -0.25 - repeat])
    torch.save(state, weights)
    return path, weights, config


def _load(config: Path, weights: Path, repeat: int):
    return load_gate7_m5(
        config,
        weights,
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        repeat=repeat,
    )


def _inputs() -> tuple[
    np.ndarray[Any, np.dtype[np.float64]],
    np.ndarray[Any, np.dtype[np.float64]],
    np.ndarray[Any, np.dtype[np.int64]],
]:
    builders = [generate_gate7_fixture_v1(split) for split in ("training", "public_validation")]
    return (
        np.concatenate([b.matrix() for b in builders]),
        np.concatenate(
            [project_gate7_history_v1(item.row for item in b.inputs()) for b in builders]
        ),
        np.asarray(
            [0 if item.row.horizon.label == "H72" else 1 for b in builders for item in b.inputs()],
            dtype=np.int64,
        ),
    )


def test_forward_gate_equations_and_all_branches(tmp_path: Path, repeat: int) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat)
    rng = torch.random.get_rng_state().clone()
    predictor = _load(config, weights, repeat)
    assert torch.equal(rng, torch.random.get_rng_state())
    raw, history, horizon = _inputs()
    state = torch.load(weights, weights_only=True)
    r = torch.from_numpy(((raw - 1) / 2).astype(np.float32))
    tokens = torch.from_numpy(
        ((history - predictor.history_mean) / predictor.history_scale).astype(np.float32)
    )
    for layer in ("raw_backbone.0", "raw_backbone.2"):
        r = torch.nn.functional.gelu(
            torch.nn.functional.linear(r, state[layer + ".weight"], state[layer + ".bias"]),
            approximate="none",
        )
    # Independent reset/update/new gate calculation checks order and all four time steps.
    hidden = torch.zeros(24, 32)
    outputs: list[Any] = []
    for token in tokens.unbind(dim=1):
        ir, iz, inn = torch.nn.functional.linear(
            token, state["history_gru.weight_ih_l0"], state["history_gru.bias_ih_l0"]
        ).chunk(3, dim=1)
        hr, hz, hn = torch.nn.functional.linear(
            hidden, state["history_gru.weight_hh_l0"], state["history_gru.bias_hh_l0"]
        ).chunk(3, dim=1)
        reset, update = torch.sigmoid(ir + hr), torch.sigmoid(iz + hz)
        new = torch.tanh(inn + reset * hn)
        hidden = (1 - update) * new + update * hidden
        outputs.append(hidden)
    sequence = torch.stack(outputs, dim=1)
    embedded = state["horizon_embedding.weight"][torch.from_numpy(horizon)]
    features = torch.cat((r, sequence.mean(dim=1), sequence[:, -1], embedded), dim=1)
    expected = torch.nn.functional.linear(features, state["head.weight"], state["head.bias"])
    actual = predictor.predict(raw, history, horizon)
    # This bounds manual unfused gate arithmetic; historical tolerances are separate.
    np.testing.assert_allclose(actual, expected.numpy(), rtol=1e-6, atol=1e-7)
    np.testing.assert_array_equal(actual, predictor.predict(raw, history, horizon))
    predictor.model.train()
    np.testing.assert_array_equal(actual, predictor.predict(raw, history, horizon))
    assert predictor.repeat == repeat and not predictor.model.training
    assert actual.shape == (24, 2) and actual.dtype == np.float64 and np.isfinite(actual).all()
    assert all(not p.requires_grad for p in predictor.model.parameters())
    assert {k: tuple(t.shape) for k, t in predictor.model.state_dict().items()} == SHAPES
    assert all(torch.equal(t, state[k]) for k, t in predictor.model.state_dict().items())
    assert sum(p.numel() for p in predictor.model.parameters()) == 10658
    gru = predictor.model.history_gru
    assert (gru.input_size, gru.hidden_size, gru.num_layers, gru.batch_first) == (4, 32, 1, True)
    assert gru.bias and not gru.bidirectional and gru.dropout == 0.0
    assert predictor.model.dropout.p == 0.10
    assert all(
        m.approximate == "none" for m in predictor.model.modules() if isinstance(m, torch.nn.GELU)
    )
    assert not any(
        isinstance(m, (torch.nn.LSTM, torch.nn.MultiheadAttention, torch.nn.LayerNorm))
        for m in predictor.model.modules()
    )
    changed = history.copy()
    changed[:, 0, 1] += 1
    paired = raw.copy()
    paired[:, 7:23] = changed.reshape(24, 16)
    assert not np.array_equal(actual, predictor.predict(paired, changed, horizon))
    paired = raw.copy()
    paired[:, 0] += 10
    assert not np.array_equal(actual, predictor.predict(paired, history, horizon))
    # Isolate the separately consumed embedding, independent of the raw horizon indicators.
    with torch.no_grad():
        predictor.model.horizon_embedding.weight[1].add_(1)
    changed_output = predictor.predict(raw, history, horizon)
    np.testing.assert_array_equal(actual[horizon == 0], changed_output[horizon == 0])
    assert not np.array_equal(actual[horizon == 1], changed_output[horizon == 1])


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate", "M3"),
        ("family", "other"),
        ("hidden_width", 32),
        ("history_width", 64),
        ("history_tokens", 3),
        ("gru_layers", 2),
        ("gru_layers", True),
        ("dropout", 0.0),
        ("raw_feature_count", 38),
        ("history_token_features", list(GATE7_HISTORY_FEATURE_NAMES)[::-1]),
        ("target_order", TARGETS[::-1]),
        ("target_transform", "scaled"),
        ("target_representation", "absolute"),
        ("raw_transform", "none"),
    ],
)
def test_wrong_config(tmp_path: Path, repeat: int, field: str, value: object) -> None:
    config, weights, data = _artifacts(tmp_path, repeat)
    data[field] = value
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="contract"):
        _load(config, weights, repeat)


def test_pins_repeat_and_orders(tmp_path: Path, repeat: int) -> None:
    config, weights, data = _artifacts(tmp_path, repeat)
    for field in ("feature_names", "target_order"):
        data["data"][field].reverse()
        config.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, repeat)
        data["data"][field].reverse()
    data["seed_identity"]["repeat"] = bool(repeat)
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="contract"):
        _load(config, weights, repeat)
    config, weights, _ = _artifacts(tmp_path, repeat)
    for invalid in (-1, 2, True, 1 - repeat):
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, invalid)
    for cp, wp in (
        ("0" * 64, hashlib.sha256(weights.read_bytes()).hexdigest()),
        (hashlib.sha256(config.read_bytes()).hexdigest(), "0" * 64),
    ):
        with pytest.raises(ValueError, match="SHA-256"):
            load_gate7_m5(config, weights, config_sha256=cp, checkpoint_sha256=wp, repeat=repeat)
    other = tmp_path / "other"
    other.mkdir()
    other_config, other_weights, _ = _artifacts(other, 1 - repeat)
    with pytest.raises(ValueError, match="SHA-256"):
        load_gate7_m5(
            config,
            other_weights,
            config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
            checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
            repeat=repeat,
        )
    assert not np.array_equal(
        _load(config, weights, repeat).predict(*_inputs()),
        _load(other_config, other_weights, 1 - repeat).predict(*_inputs()),
    )


@pytest.mark.parametrize("field", ("raw_mean", "raw_scale", "history_mean", "history_scale"))
@pytest.mark.parametrize("invalid", ("shape", "nan", "inf", "zero", "negative"))
def test_preprocessing(tmp_path: Path, repeat: int, field: str, invalid: str) -> None:
    config, weights, data = _artifacts(tmp_path, repeat)
    values = data["preprocessor"][field]
    if invalid == "shape":
        values.pop()
    else:
        values[0] = {"nan": float("nan"), "inf": float("inf"), "zero": 0, "negative": -1}[invalid]
    config.write_text(json.dumps(data))
    if invalid in ("zero", "negative") and field.endswith("mean"):
        _load(config, weights, repeat)
    else:
        with pytest.raises(ValueError, match="preprocessing"):
            _load(config, weights, repeat)


def test_all_state_tensors_and_safe_deserialization(tmp_path: Path, repeat: int) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat)
    state = torch.load(weights, weights_only=True)
    for key, tensor in state.items():
        for bad in (
            torch.zeros(1),
            tensor.double(),
            torch.full_like(tensor, np.nan),
            torch.full_like(tensor, np.inf),
            tensor.tolist(),
        ):
            torch.save({**state, key: bad}, weights)
            with pytest.raises(ValueError, match="tensor"):
                _load(config, weights, repeat)
    malformed_states: tuple[object, ...] = ({}, {**state, "extra": torch.zeros(1)}, [])
    for bad in malformed_states:
        torch.save(bad, weights)
        with pytest.raises(ValueError, match="state dict"):
            _load(config, weights, repeat)
    torch.save(_UnsafePayload(), weights)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights, repeat)


class _UnsafePayload:
    def __reduce__(self) -> tuple[object, tuple[()]]:
        return eval, ()


def test_no_unsafe_fallback(tmp_path: Path, repeat: int, monkeypatch: pytest.MonkeyPatch) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat)
    calls: list[dict[str, object]] = []

    def rejected(*args: object, **kwargs: object) -> object:
        calls.append(kwargs)
        raise pickle.UnpicklingError("rejected")

    monkeypatch.setattr(torch, "load", rejected)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights, repeat)
    assert calls == [{"map_location": "cpu", "weights_only": True}]


def test_input_rejections_and_overflow(tmp_path: Path, repeat: int) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat)
    predictor = _load(config, weights, repeat)
    raw, history, horizon = _inputs()
    for bad in (
        history[:1],
        history[:, :3],
        history[:, :, :3],
        history[:, ::-1],
        history + 1000,
        np.full_like(history, np.nan),
        np.full_like(history, np.inf),
        np.ma.array(history, mask=True),
    ):
        with pytest.raises(ValueError):
            predictor.predict(raw, bad, horizon)
    for bad in (
        raw[:1],
        raw[:, :38],
        np.full_like(raw, np.nan),
        np.full_like(raw, np.inf),
        np.ma.array(raw, mask=True),
    ):
        with pytest.raises(ValueError):
            predictor.predict(bad, history, horizon)
    for bad in (
        horizon[:1],
        horizon[:, None],
        horizon.astype(np.float32),
        horizon.astype(bool),
        horizon.astype(np.int32),
        np.full_like(horizon, 2),
        1 - horizon,
        np.ma.array(horizon, mask=True),
    ):
        with pytest.raises(ValueError):
            predictor.predict(raw, history, bad)
    bad = raw.copy()
    bad[:, 7] += 1
    with pytest.raises(ValueError, match="ordering"):
        predictor.predict(bad, history, horizon)
    with pytest.raises(TypeError):
        predictor.predict(raw, history)  # pyright: ignore[reportCallIssue]
    with pytest.raises(TypeError):
        predictor.predict(raw, history, horizon, basis=np.zeros((24, 5)))  # pyright: ignore[reportCallIssue]
    raw[:, 0] = 1e300
    with pytest.raises(ValueError, match="preprocessing"):
        predictor.predict(raw, history, horizon)
    assert not any(
        s.flags.writeable
        for s in (
            predictor.feature_mean,
            predictor.feature_scale,
            predictor.history_mean,
            predictor.history_scale,
        )
    )
    with torch.no_grad():
        for parameter in predictor.model.parameters():
            parameter.fill_(torch.finfo(torch.float32).max)
    with pytest.raises(ValueError, match="predictions"):
        predictor.predict(*_inputs())


def test_history_standardization_overflow(tmp_path: Path, repeat: int) -> None:
    config, weights, data = _artifacts(tmp_path, repeat)
    data["preprocessor"]["history_mean"][0] = 1e308
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="preprocessing"):
        _load(config, weights, repeat).predict(*_inputs())
