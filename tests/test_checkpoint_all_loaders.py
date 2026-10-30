"""All independently recovered inference entry points coexist."""

import inspect

import pytest

pytest.importorskip("torch")

from cmj_recovery_dynamics.model_reproduction import checkpoint_inference as inference  # noqa: E402


def test_all_gate7_loaders_and_predict_signatures() -> None:
    for index in range(7):
        assert callable(getattr(inference, f"load_gate7_m{index}"))
    for index, inputs in (
        (4, ("features", "history")),
        (5, ("features", "history", "horizon")),
        (6, ("features", "history", "horizon", "basis")),
    ):
        predictor = getattr(inference, f"Gate7M{index}Predictor")
        assert tuple(inspect.signature(predictor.predict).parameters)[1:] == inputs
