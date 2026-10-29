"""Synthetic M6 test artifacts; no recovered checkpoints or observations."""

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
    M6_BASIS_CONSTANTS,
    M6_BASIS_NAMES,
    TARGET_TRANSFORM,
    TARGETS,
    load_gate7_m6,
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
    "basis_projection.0.weight": (16, 2),
    "basis_projection.0.bias": (16,),
    "head.weight": (2, 152),
    "head.bias": (2,),
}
pytestmark = pytest.mark.parametrize("repeat", (0, 1))


def artifacts(tmp_path: Path, repeat: int) -> tuple[Path, Path, dict[str, Any]]:
    config: dict[str, Any] = {
        "family": FAMILY,
        "candidate": "M6",
        "seed_identity": {"candidate": "M6", "repeat": repeat},
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
        "basis_transform": "train-only mean/std standardization",
        "basis_names": list(M6_BASIS_NAMES),
        "basis_constants": dict(M6_BASIS_CONSTANTS),
        "preprocessor": {
            "raw_mean": [1.0] * 39,
            "raw_scale": [2.0] * 39,
            "history_mean": [-100.0, 20.0, 2.0, 0.3],
            "history_scale": [60.0, 2.0, 0.2, 0.1],
            "basis_mean": [0.2] * 5,
            "basis_scale": [0.5] * 5,
        },
    }
    cp, wp = tmp_path / "config.json", tmp_path / "weights.pt"
    cp.write_text(json.dumps(config))
    state = {
        k: torch.linspace(-0.03, 0.04, int(np.prod(shape))).reshape(shape)
        for k, shape in SHAPES.items()
    }
    state["head.bias"] = torch.tensor([0.25 + repeat, -0.25 - repeat])
    torch.save(state, wp)
    return cp, wp, config


def load(cp: Path, wp: Path, repeat: int):
    return load_gate7_m6(
        cp,
        wp,
        config_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256(wp.read_bytes()).hexdigest(),
        repeat=repeat,
    )


def inputs() -> tuple[Any, Any, Any, Any]:
    builders = [generate_gate7_fixture_v1(split) for split in ("training", "public_validation")]
    raw = np.concatenate([b.matrix() for b in builders])
    history = np.concatenate(
        [project_gate7_history_v1(x.row for x in b.inputs()) for b in builders]
    )
    horizon = np.asarray(
        [0 if x.row.horizon.label == "H72" else 1 for b in builders for x in b.inputs()],
        dtype=np.int64,
    )
    basis = np.linspace(0.05, 1.0, 24 * 5).reshape(24, 5)
    return raw, history, horizon, basis


def test_forward_with_independent_gru_equations(tmp_path: Path, repeat: int) -> None:
    cp, wp, _ = artifacts(tmp_path, repeat)
    rng = torch.random.get_rng_state().clone()
    model = load(cp, wp, repeat)
    assert torch.equal(rng, torch.random.get_rng_state())
    raw, history, horizon, basis = inputs()
    state = torch.load(wp, weights_only=True)

    def linear(x: Any, name: str) -> Any:
        return torch.nn.functional.linear(x, state[name + ".weight"], state[name + ".bias"])

    r = torch.from_numpy(((raw - model.feature_mean) / model.feature_scale).astype(np.float32))
    h = torch.from_numpy(((history - model.history_mean) / model.history_scale).astype(np.float32))
    b = torch.from_numpy(((basis - model.basis_mean) / model.basis_scale).astype(np.float32))
    r = torch.nn.functional.gelu(linear(r, "raw_backbone.0"), approximate="none")
    r = torch.nn.functional.gelu(linear(r, "raw_backbone.2"), approximate="none")
    hidden = torch.zeros(24, 32)
    sequence: list[Any] = []
    for token in h.unbind(dim=1):
        ir, iz, inn = torch.nn.functional.linear(
            token, state["history_gru.weight_ih_l0"], state["history_gru.bias_ih_l0"]
        ).chunk(3, 1)
        hr, hz, hn = torch.nn.functional.linear(
            hidden, state["history_gru.weight_hh_l0"], state["history_gru.bias_hh_l0"]
        ).chunk(3, 1)
        reset, update = torch.sigmoid(ir + hr), torch.sigmoid(iz + hz)
        new = torch.tanh(inn + reset * hn)
        hidden = (1 - update) * new + update * hidden
        sequence.append(hidden)
    seq = torch.stack(sequence, dim=1)
    encoded = torch.nn.functional.gelu(linear(b[:, :2], "basis_projection.0"), approximate="none")
    features = torch.cat(
        (
            r,
            seq.mean(1),
            seq[:, -1],
            state["horizon_embedding.weight"][torch.from_numpy(horizon)],
            encoded,
        ),
        1,
    )
    expected = linear(features, "head").numpy()
    actual = model.predict(raw, history, horizon, basis)
    np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=1e-6)
    np.testing.assert_array_equal(actual, model.predict(raw, history, horizon, basis))
    assert actual.shape == (24, 2) and actual.dtype == np.float64 and np.isfinite(actual).all()
    assert {k: tuple(v.shape) for k, v in model.model.state_dict().items()} == SHAPES
    assert all(torch.equal(t, state[k]) for k, t in model.model.state_dict().items())
    assert sum(x.numel() for x in model.model.parameters()) == 10738
    assert not model.model.training and all(not p.requires_grad for p in model.model.parameters())
    assert all(
        not x.flags.writeable
        for x in (
            model.feature_mean,
            model.feature_scale,
            model.history_mean,
            model.history_scale,
            model.basis_mean,
            model.basis_scale,
        )
    )
    gru = model.model.history_gru
    assert (
        gru.input_size,
        gru.hidden_size,
        gru.num_layers,
        gru.batch_first,
        gru.bidirectional,
        gru.dropout,
    ) == (4, 32, 1, True, False, 0.0)
    changed = basis.copy()
    changed[:, 2:] += 5
    np.testing.assert_array_equal(actual, model.predict(raw, history, horizon, changed))
    changed = basis.copy()
    changed[:, 0] += 5
    assert not np.array_equal(actual, model.predict(raw, history, horizon, changed))
    model.model.train()
    np.testing.assert_array_equal(actual, model.predict(raw, history, horizon, basis))


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate", "M5"),
        ("family", "other"),
        ("gru_layers", 2),
        ("gru_layers", True),
        ("hidden_width", 32),
        ("history_width", 16),
        ("history_tokens", 3),
        ("dropout", 0.0),
        ("target_representation", "absolute"),
        ("target_transform", "scaled"),
        ("basis_transform", "none"),
        ("basis_names", []),
        ("basis_constants", {}),
    ],
)
def test_bad_config(tmp_path: Path, repeat: int, field: str, value: object) -> None:
    cp, wp, config = artifacts(tmp_path, repeat)
    config[field] = value
    cp.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        load(cp, wp, repeat)


@pytest.mark.parametrize(
    "field", ("raw_mean", "raw_scale", "history_mean", "history_scale", "basis_mean", "basis_scale")
)
@pytest.mark.parametrize("bad", ("shape", "nan", "inf", "zero", "negative"))
def test_statistics(tmp_path: Path, repeat: int, field: str, bad: str) -> None:
    cp, wp, config = artifacts(tmp_path, repeat)
    values = config["preprocessor"][field]
    if bad == "shape":
        values.pop()
    else:
        values[0] = {"nan": float("nan"), "inf": float("inf"), "zero": 0, "negative": -1}[bad]
    cp.write_text(json.dumps(config))
    if bad in ("zero", "negative") and field.endswith("mean"):
        load(cp, wp, repeat)
    else:
        with pytest.raises(ValueError, match="preprocessing"):
            load(cp, wp, repeat)


class Unsafe:
    def __reduce__(self) -> tuple[object, tuple[()]]:
        return eval, ()


def test_weights_validation_and_pins(tmp_path: Path, repeat: int) -> None:
    cp, wp, _ = artifacts(tmp_path, repeat)
    state = torch.load(wp, weights_only=True)
    with pytest.raises(ValueError, match="SHA-256"):
        load_gate7_m6(
            cp,
            wp,
            config_sha256="0" * 64,
            checkpoint_sha256=hashlib.sha256(wp.read_bytes()).hexdigest(),
            repeat=repeat,
        )
    for invalid in (-1, 2, True, 1 - repeat):
        with pytest.raises(ValueError, match="contract"):
            load(cp, wp, invalid)
    for key, tensor in state.items():
        for bad in (
            torch.zeros(1),
            tensor.double(),
            torch.full_like(tensor, np.nan),
            torch.full_like(tensor, np.inf),
            tensor.tolist(),
        ):
            torch.save({**state, key: bad}, wp)
            with pytest.raises(ValueError, match="tensor"):
                load(cp, wp, repeat)
    for bad in ({}, {**state, "extra": torch.zeros(1)}):
        torch.save(bad, wp)
        with pytest.raises(ValueError, match="state dict"):
            load(cp, wp, repeat)
    torch.save(Unsafe(), wp)
    with pytest.raises(pickle.UnpicklingError):
        load(cp, wp, repeat)


def test_weights_only_no_fallback(
    tmp_path: Path, repeat: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    cp, wp, _ = artifacts(tmp_path, repeat)
    calls: list[dict[str, object]] = []

    def reject(*args: object, **kwargs: object) -> object:
        calls.append(kwargs)
        raise pickle.UnpicklingError("rejected")

    monkeypatch.setattr(torch, "load", reject)
    with pytest.raises(pickle.UnpicklingError):
        load(cp, wp, repeat)
    assert calls == [{"map_location": "cpu", "weights_only": True}]


def test_invalid_inputs(tmp_path: Path, repeat: int) -> None:
    cp, wp, _ = artifacts(tmp_path, repeat)
    model = load(cp, wp, repeat)
    raw, history, horizon, basis = inputs()
    for bad in (
        history[:1],
        history[:, :3],
        history[:, :, :3],
        history[:, ::-1],
        history + 1000,
        np.full_like(history, np.nan),
        np.ma.array(history, mask=True),
    ):
        with pytest.raises(ValueError):
            model.predict(raw, bad, horizon, basis)
    for bad in (raw[:1], raw[:, :38], np.full_like(raw, np.inf), np.ma.array(raw, mask=True)):
        with pytest.raises(ValueError):
            model.predict(bad, history, horizon, basis)
    for bad in (
        horizon[:1],
        horizon[:, None],
        horizon.astype(np.float32),
        horizon.astype(bool),
        np.full_like(horizon, 2),
        1 - horizon,
        np.ma.array(horizon, mask=True),
    ):
        with pytest.raises(ValueError):
            model.predict(raw, history, bad, basis)
    for bad in (
        basis[:1],
        basis[:, :2],
        np.full_like(basis, np.nan),
        np.full_like(basis, np.inf),
        np.ma.array(basis, mask=True),
    ):
        with pytest.raises(ValueError):
            model.predict(raw, history, horizon, bad)
    mismatched = raw.copy()
    mismatched[:, 7] += 1
    with pytest.raises(ValueError, match="ordering"):
        model.predict(mismatched, history, horizon, basis)
    raw[:, 0] = 1e300
    with pytest.raises(ValueError, match="preprocessing"):
        model.predict(raw, history, horizon, basis)
    raw, history, horizon, basis = inputs()
    basis[:, 4] = 1e300
    with pytest.raises(ValueError, match="preprocessing"):
        model.predict(raw, history, horizon, basis)
    with torch.no_grad():
        for p in model.model.parameters():
            p.fill_(torch.finfo(torch.float32).max)
    with pytest.raises(ValueError, match="predictions"):
        model.predict(*inputs())


def test_config_order_and_checkpoint_pin(tmp_path: Path, repeat: int) -> None:
    cp, wp, config = artifacts(tmp_path, repeat)
    for name in ("feature_names", "target_order"):
        config["data"][name].reverse()
        cp.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="contract"):
            load(cp, wp, repeat)
        config["data"][name].reverse()
    config["history_token_features"].reverse()
    cp.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        load(cp, wp, repeat)
    config["history_token_features"].reverse()
    config["seed_identity"]["candidate"] = "M5"
    cp.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="contract"):
        load(cp, wp, repeat)
    cp, wp, _ = artifacts(tmp_path, repeat)
    with pytest.raises(ValueError, match="SHA-256"):
        load_gate7_m6(
            cp,
            wp,
            config_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),
            checkpoint_sha256="0" * 64,
            repeat=repeat,
        )
    other = tmp_path / "other"
    other.mkdir()
    _, other_wp, _ = artifacts(other, 1 - repeat)
    with pytest.raises(ValueError, match="SHA-256"):
        load_gate7_m6(
            cp,
            other_wp,
            config_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),
            checkpoint_sha256=hashlib.sha256(wp.read_bytes()).hexdigest(),
            repeat=repeat,
        )
