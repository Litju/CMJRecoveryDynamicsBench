"""Synthetic M3/M4 artifacts and observation histories only; no recovered parameters."""

import hashlib
import json
import pickle
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from cmj_recovery_dynamics.model_reproduction.checkpoint_inference import (  # noqa: E402
    FAMILY,
    TARGET_TRANSFORM,
    TARGETS,
    load_gate7_m3,
    load_gate7_m4,
)
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (  # noqa: E402
    GATE7_FEATURE_NAMES,
    GATE7_HISTORY_FEATURE_NAMES,
    GATE7_HISTORY_SCHEMA_V1,
    project_gate7_history_v1,
)
from cmj_recovery_dynamics.observations.public_builder import (  # noqa: E402
    generate_gate7_fixture_v1,
)
from cmj_recovery_dynamics.reproduction.camp_history import (  # noqa: E402
    AssessmentAvailability,
)

SHAPES = {
    "raw_backbone.0.weight": (64, 39),
    "raw_backbone.0.bias": (64,),
    "raw_backbone.2.weight": (64, 64),
    "raw_backbone.2.bias": (64,),
    "history_encoder.0.weight": (32, 4),
    "history_encoder.0.bias": (32,),
    "head.weight": (2, 128),
    "head.bias": (2,),
}
M4_SHAPES = {k: v for k, v in SHAPES.items() if not k.startswith("history_encoder")}
M4_SHAPES.update(
    {
        "history_gru.weight_ih_l0": (96, 4),
        "history_gru.weight_hh_l0": (96, 32),
        "history_gru.bias_ih_l0": (96,),
        "history_gru.bias_hh_l0": (96,),
    }
)
pytestmark = [
    pytest.mark.parametrize("repeat", (0, 1)),
    pytest.mark.parametrize("candidate", ("M3", "M4")),
]


def _shapes(candidate: str) -> dict[str, tuple[int, ...]]:
    return SHAPES if candidate == "M3" else M4_SHAPES


def _loader(candidate: str):
    return {"M3": load_gate7_m3, "M4": load_gate7_m4}[candidate]


def _artifacts(tmp_path: Path, repeat: int, candidate: str) -> tuple[Path, Path, dict[str, Any]]:
    config: dict[str, Any] = {
        "family": FAMILY,
        "candidate": candidate,
        "seed_identity": {"candidate": candidate, "repeat": repeat},
        "raw_feature_count": 39,
        "hidden_width": 64,
        "history_width": 32,
        "history_tokens": 4,
        "gru_layers": 1,
        "history_token_features": list(GATE7_HISTORY_FEATURE_NAMES),
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
        for name, shape in _shapes(candidate).items()
    }
    state["head.bias"] = torch.tensor([0.25 + repeat, -0.25 - repeat])
    torch.save(state, weights)
    return path, weights, config


def _load(config: Path, weights: Path, repeat: int, candidate: str):
    return _loader(candidate)(
        config,
        weights,
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        repeat=repeat,
    )


def _inputs() -> tuple[
    np.ndarray[Any, np.dtype[np.float64]], np.ndarray[Any, np.dtype[np.float64]]
]:
    builders = [generate_gate7_fixture_v1(split) for split in ("training", "public_validation")]
    raw = np.concatenate([builder.matrix() for builder in builders])
    history = np.concatenate(
        [project_gate7_history_v1(item.row for item in builder.inputs()) for builder in builders]
    )
    return raw, history


def test_exact_forward_and_architecture(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    rng = torch.random.get_rng_state().clone()
    predictor = _load(config, weights, repeat, candidate=candidate)
    assert torch.equal(rng, torch.random.get_rng_state())
    assert predictor.repeat == repeat
    raw, history = _inputs()
    assert raw.shape == (24, 39) and history.shape == (24, 4, 4)
    np.testing.assert_array_equal(raw[:, 7:23], history.reshape(24, 16))
    state = torch.load(weights, weights_only=True)

    def layer(values: Any, prefix: str):
        return torch.nn.functional.linear(
            values, state[f"{prefix}.weight"], state[f"{prefix}.bias"]
        )

    r = torch.from_numpy(((raw - 1) / 2).astype(np.float32))
    h = torch.from_numpy(
        ((history - predictor.history_mean) / predictor.history_scale).astype(np.float32)
    )
    r = torch.nn.functional.gelu(layer(r, "raw_backbone.0"), approximate="none")
    r = torch.nn.functional.gelu(layer(r, "raw_backbone.2"), approximate="none")
    if candidate == "M3":
        h = torch.nn.functional.gelu(layer(h, "history_encoder.0"), approximate="none")
    else:
        # Independently evaluate PyTorch's reset/update/new gate equations from zero h0.
        hidden = torch.zeros((len(raw), 32), dtype=torch.float32)
        encoded: list[Any] = []
        for token in h.unbind(dim=1):
            inputs = torch.nn.functional.linear(
                token, state["history_gru.weight_ih_l0"], state["history_gru.bias_ih_l0"]
            )
            recurrent = torch.nn.functional.linear(
                hidden, state["history_gru.weight_hh_l0"], state["history_gru.bias_hh_l0"]
            )
            ir, iz, inn = inputs.chunk(3, dim=1)
            hr, hz, hn = recurrent.chunk(3, dim=1)
            reset, update = torch.sigmoid(ir + hr), torch.sigmoid(iz + hz)
            proposed = torch.tanh(inn + reset * hn)
            hidden = (1 - update) * proposed + update * hidden
            encoded.append(hidden)
        h = torch.stack(encoded, dim=1)
    expected = layer(torch.cat((r, h.mean(dim=1), h[:, -1]), dim=1), "head").numpy()
    actual = predictor.predict(raw, history)
    if candidate == "M3":
        np.testing.assert_array_equal(actual, expected)
    else:
        np.testing.assert_allclose(actual, expected, atol=1e-6, rtol=1e-5)
    predictor.model.train()
    np.testing.assert_array_equal(actual, predictor.predict(raw, history))
    assert actual.dtype == np.float64 and actual.shape == (24, 2)
    assert np.isfinite(actual).all() and (actual != 0).any()
    assert not predictor.model.training
    assert all(not p.requires_grad for p in predictor.model.parameters())
    assert {k: tuple(v.shape) for k, v in predictor.model.state_dict().items()} == _shapes(
        candidate
    )
    assert (
        sum(p.numel() for p in predictor.model.parameters()) == {"M3": 7138, "M4": 10626}[candidate]
    )
    expected_modules = [
        "_Gate7M3Model",
        "Sequential",
        "Linear",
        "GELU",
        "Linear",
        "GELU",
        "Dropout",
        "Sequential",
        "Linear",
        "GELU",
        "Linear",
    ]
    if candidate == "M4":
        expected_modules = [
            "_Gate7M4Model",
            "Sequential",
            "Linear",
            "GELU",
            "Linear",
            "GELU",
            "Dropout",
            "GRU",
            "Linear",
        ]
    assert [type(m).__name__ for m in predictor.model.modules()] == expected_modules
    assert predictor.model.dropout.p == 0.10
    assert all(
        m.approximate == "none" for m in predictor.model.modules() if isinstance(m, torch.nn.GELU)
    )
    # The pool uses all tokens and the final token; neither branch can be skipped.
    changed = history.copy()
    changed[:, 0, 1] += 1
    paired = raw.copy()
    paired[:, 7:23] = changed.reshape(24, 16)
    assert not np.array_equal(actual, predictor.predict(paired, changed))
    paired = raw.copy()
    paired[:, 0] += 10
    assert not np.array_equal(actual, predictor.predict(paired, history))


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate", "M2"),
        ("family", "other"),
        ("hidden_width", 32),
        ("history_width", 64),
        ("history_tokens", 3),
        ("dropout", 0.0),
        ("raw_feature_count", 38),
        ("history_token_features", list(GATE7_HISTORY_FEATURE_NAMES)[::-1]),
        ("target_order", TARGETS[::-1]),
        ("target_transform", "scaled"),
        ("target_representation", "absolute"),
        ("raw_transform", "none"),
    ],
)
def test_wrong_config(
    tmp_path: Path, repeat: int, field: str, value: object, candidate: str
) -> None:
    config, weights, data = _artifacts(tmp_path, repeat, candidate=candidate)
    data[field] = value
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="contract"):
        _load(config, weights, repeat, candidate=candidate)


def test_order_repeat_and_pins(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, data = _artifacts(tmp_path, repeat, candidate=candidate)
    for field in ("feature_names", "target_order"):
        data["data"][field].reverse()
        config.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, repeat, candidate=candidate)
        data["data"][field].reverse()
    config.write_text(json.dumps(data))
    for bad_repeat in (1 - repeat, -1, 2, True):
        with pytest.raises(ValueError, match="contract"):
            _load(config, weights, bad_repeat, candidate=candidate)
    for config_pin, checkpoint_pin in (
        ("0" * 64, hashlib.sha256(weights.read_bytes()).hexdigest()),
        (hashlib.sha256(config.read_bytes()).hexdigest(), "0" * 64),
    ):
        with pytest.raises(ValueError, match="SHA-256"):
            _loader(candidate)(
                config,
                weights,
                config_sha256=config_pin,
                checkpoint_sha256=checkpoint_pin,
                repeat=repeat,
            )
    data["seed_identity"]["candidate"] = "M0"
    config.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="contract"):
        _load(config, weights, repeat, candidate=candidate)


@pytest.mark.parametrize("field", ("raw_mean", "raw_scale", "history_mean", "history_scale"))
@pytest.mark.parametrize("invalid", ("shape", "nan", "inf", "zero", "negative"))
def test_preprocessing(
    tmp_path: Path, repeat: int, field: str, invalid: str, candidate: str
) -> None:
    config, weights, data = _artifacts(tmp_path, repeat, candidate=candidate)
    values = data["preprocessor"][field]
    if invalid == "shape":
        values.pop()
    else:
        values[0] = {"nan": float("nan"), "inf": float("inf"), "zero": 0, "negative": -1}[invalid]
    config.write_text(json.dumps(data))
    if invalid in ("zero", "negative") and field.endswith("mean"):
        _load(config, weights, repeat, candidate=candidate)
    else:
        with pytest.raises(ValueError, match="preprocessing"):
            _load(config, weights, repeat, candidate=candidate)


def test_every_tensor_rejected(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    state = torch.load(weights, weights_only=True)
    for key, tensor in state.items():
        for invalid in (
            torch.zeros(1),
            tensor.double(),
            torch.full_like(tensor, np.nan),
            torch.full_like(tensor, np.inf),
            tensor.tolist(),
        ):
            torch.save({**state, key: invalid}, weights)
            with pytest.raises(ValueError, match="tensor"):
                _load(config, weights, repeat, candidate=candidate)
    for malformed in (
        {},
        {**state, "extra": torch.zeros(1)},
        {"raw_deep.0.weight": torch.zeros(64, 39)},
    ):
        torch.save(malformed, weights)
        with pytest.raises(ValueError, match="state dict"):
            _load(config, weights, repeat, candidate=candidate)


class _UnsafePayload:
    def __reduce__(self) -> tuple[object, tuple[()]]:
        return eval, ()


def test_weights_only_no_fallback(
    tmp_path: Path, repeat: int, monkeypatch: pytest.MonkeyPatch, candidate: str
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    torch.save(_UnsafePayload(), weights)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights, repeat, candidate=candidate)
    calls: list[dict[str, object]] = []

    def rejected(*args: object, **kwargs: object) -> object:
        calls.append(kwargs)
        raise pickle.UnpicklingError("rejected")

    monkeypatch.setattr(torch, "load", rejected)
    with pytest.raises(pickle.UnpicklingError):
        _load(config, weights, repeat, candidate=candidate)
    assert calls == [{"map_location": "cpu", "weights_only": True}]


def test_invalid_inputs_and_overflow(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    predictor = _load(config, weights, repeat, candidate=candidate)
    raw, history = _inputs()
    for malformed in (
        history[:, :3],
        history[:, :, :3],
        history[:1],
        np.full_like(history, np.nan),
        np.full_like(history, np.inf),
        history[:, ::-1],
        history + 1000,
        np.ma.array(history, mask=True),
    ):
        with pytest.raises(ValueError):
            predictor.predict(raw, malformed)
    for malformed in (
        raw[:, :38],
        raw[:1],
        np.full_like(raw, np.nan),
        np.full_like(raw, np.inf),
        np.ma.array(raw, mask=True),
    ):
        with pytest.raises(ValueError):
            predictor.predict(malformed, history)
    paired = raw.copy()
    paired[:, 7] += 1
    with pytest.raises(ValueError, match="ordering"):
        predictor.predict(paired, history)
    # Neither candidate consumes separate horizon or basis arguments.
    with pytest.raises(TypeError):
        predictor.predict(raw, history, horizon=np.zeros(24))  # pyright: ignore[reportCallIssue]
    with pytest.raises(TypeError):
        predictor.predict(raw, history, basis=np.zeros((24, 5)))  # pyright: ignore[reportCallIssue]
    raw[:, 0] = 1e300
    with pytest.raises(ValueError, match="preprocessing"):
        predictor.predict(raw, history)
    raw, history = _inputs()
    assert (
        not predictor.history_mean.flags.writeable and not predictor.history_scale.flags.writeable
    )
    with torch.no_grad():
        for parameter in predictor.model.parameters():
            parameter.fill_(torch.finfo(torch.float32).max)
    with pytest.raises(ValueError, match="predictions"):
        predictor.predict(raw, history)


def test_history_projection_and_missingness(repeat: int, candidate: str) -> None:
    row = generate_gate7_fixture_v1().inputs()[repeat].row
    row = replace(
        row,
        assessment_history=tuple(
            sorted(row.assessment_history, key=lambda a: a.time_from_origin_hours)
        ),
    )
    actual = project_gate7_history_v1((row,))
    assert GATE7_HISTORY_SCHEMA_V1 == "gate7_history_projection_v1"
    assert actual.shape == (1, 4, 4) and not actual.flags.writeable
    np.testing.assert_array_equal(
        actual,
        project_gate7_history_v1((replace(row, assessment_history=row.assessment_history[::-1]),)),
    )
    with pytest.raises(ValueError, match="four valid"):
        project_gate7_history_v1((replace(row, assessment_history=row.assessment_history[1:]),))
    missing = replace(
        row.assessment_history[0], availability=AssessmentAvailability.OBSERVED_MASKED, trials=()
    )
    with pytest.raises(ValueError, match="four valid"):
        project_gate7_history_v1(
            (replace(row, assessment_history=(missing, *row.assessment_history[1:])),)
        )
    assert project_gate7_history_v1(()).shape == (0, 4, 4)


def test_only_source_defined_construction(
    tmp_path: Path, repeat: int, monkeypatch: pytest.MonkeyPatch, candidate: str
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    linear = torch.nn.Linear
    calls: list[tuple[int, int]] = []

    def tracked(inputs: int, outputs: int, **kwargs: Any) -> Any:
        calls.append((inputs, outputs))
        return linear(inputs, outputs, **kwargs)

    monkeypatch.setattr(torch.nn, "Linear", tracked)
    _load(config, weights, repeat, candidate=candidate)
    assert calls == (
        [(39, 64), (64, 64), (4, 32), (128, 2)]
        if candidate == "M3"
        else [(39, 64), (64, 64), (128, 2)]
    )


def test_pinned_repeat_artifacts_are_not_interchangeable(
    tmp_path: Path, repeat: int, candidate: str
) -> None:
    config, weights, _ = _artifacts(tmp_path, repeat, candidate=candidate)
    other = tmp_path / "other"
    other.mkdir()
    other_config, other_weights, _ = _artifacts(other, 1 - repeat, candidate=candidate)
    pins = {
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "checkpoint_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
        "repeat": repeat,
    }
    with pytest.raises(ValueError, match="SHA-256"):
        _loader(candidate)(config, other_weights, **pins)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ValueError, match="SHA-256"):
        _loader(candidate)(other_config, weights, **pins)  # pyright: ignore[reportArgumentType]
    raw, history = _inputs()
    assert not np.array_equal(
        _load(config, weights, repeat, candidate=candidate).predict(raw, history),
        _load(other_config, other_weights, 1 - repeat, candidate=candidate).predict(raw, history),
    )


def test_history_float32_overflow(tmp_path: Path, repeat: int, candidate: str) -> None:
    config, weights, data = _artifacts(tmp_path, repeat, candidate=candidate)
    data["preprocessor"]["history_mean"][0] = 1e308
    config.write_text(json.dumps(data))
    predictor = _load(config, weights, repeat, candidate=candidate)
    with pytest.raises(ValueError, match="preprocessing"):
        predictor.predict(*_inputs())


def test_source_defined_gru_contract(
    tmp_path: Path, repeat: int, candidate: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, weights, data = _artifacts(tmp_path, repeat, candidate=candidate)
    constructor = torch.nn.GRU
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def tracked(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return constructor(*args, **kwargs)

    monkeypatch.setattr(torch.nn, "GRU", tracked)
    predictor = _load(config, weights, repeat, candidate=candidate)
    if candidate == "M3":
        assert calls == []
    else:
        assert calls == [
            (
                (4, 32),
                {"num_layers": 1, "batch_first": True, "device": "cpu", "dtype": torch.float32},
            )
        ]
        gru = next(m for m in predictor.model.modules() if isinstance(m, constructor))
        assert gru.num_layers == 1 and gru.batch_first and gru.bias
        assert not gru.bidirectional and gru.dropout == 0.0
        for invalid_layers in (0, 2):
            data["gru_layers"] = invalid_layers
            config.write_text(json.dumps(data))
            with pytest.raises(ValueError, match="contract"):
                _load(config, weights, repeat, candidate=candidate)
