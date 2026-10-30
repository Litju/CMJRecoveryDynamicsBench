"""Local service and source-admission tests use synthetic data only."""

import http.client
import json
import multiprocessing
import socket
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytest.importorskip("torch")

from cmj_recovery_dynamics import research_lab as lab  # noqa: E402

TOKEN = "abcdefghijklmnopqrstuvwxyz0123456789"


def request(
    candidate: str = "M0", *, mode: str = "synthetic_demo", observation: str = "training-0"
) -> dict[str, object]:
    return {
        "version": lab.VERSION,
        "candidate": candidate,
        "repeat": 0,
        "observation_id": observation,
        "mode": mode,
    }


def with_basis(item: lab.ObservationGrant) -> lab.ObservationGrant:
    raw, history, horizon = lab._inputs(item)  # pyright: ignore[reportPrivateUsage]
    basis = (0.1, 0.2, 0.3, 0.4, 0.5)
    pin = lab.row_digest(
        item.builder.expected_observations_sha256, item.origin_id, raw, history, horizon, basis
    )
    return replace(item, basis=lab.BasisGrant(basis, pin, "independent-test-authority"))


def test_all_candidates_route_real_synthetic_inference() -> None:
    observation = with_basis(lab.fixture_observations()[0])
    app = lab.ResearchLab((observation,))
    for i in range(9):
        for repeat in (0, 1):
            candidate_request = {**request(f"M{i}"), "repeat": repeat}
            result = app.predict(candidate_request)
            assert result["kind"] == "synthetic_demo"
            assert result["cuda_evidence"] == "not_applicable"
            outputs: Any = result["outputs"]
            assert [entry["unit"] for entry in outputs] == ["N/kg", "m/s"]
            assert all(np.isfinite(entry["value"]) for entry in outputs)
            assert app.predict(candidate_request) == result


def test_authority_and_request_refusals(monkeypatch: pytest.MonkeyPatch) -> None:
    observation = lab.fixture_observations()[0]
    app = lab.ResearchLab((observation,))
    with pytest.raises(lab.Refusal, match="No authorized model") as caught:
        app.predict(request(mode="original"))
    assert caught.value.code == "MODEL_UNAVAILABLE"
    with pytest.raises(lab.Refusal) as caught:
        app.predict(request(observation="other"))
    assert caught.value.code == "SOURCE_UNAUTHORIZED"
    with pytest.raises(lab.Refusal) as caught:
        app.predict({**request(), "checkpoint_path": "ignored"})
    assert caught.value.code == "MALFORMED_REQUEST"
    with pytest.raises(lab.Refusal) as caught:
        app.predict({**request(), "repeat": True})
    assert caught.value.code == "MALFORMED_REQUEST"
    with pytest.raises(lab.Refusal) as caught:
        app.predict(request("M6"))
    assert caught.value.code == "BASIS_AUTHORITY_UNAVAILABLE"
    paired = with_basis(observation)
    assert paired.basis is not None
    wrong = replace(paired, basis=replace(paired.basis, row_sha256="0" * 64))
    with pytest.raises(lab.Refusal) as caught:
        lab.ResearchLab((wrong,)).predict(request("M7"))
    assert caught.value.code == "BASIS_AUTHORITY_UNAVAILABLE"
    real = replace(observation, source="authorized", authority="owner-authorization")
    with pytest.raises(lab.Refusal) as caught:
        lab.ResearchLab((real,)).predict(request())
    assert caught.value.code == "SOURCE_UNAUTHORIZED"

    def bad_source(_: lab.ObservationGrant) -> None:
        raise ValueError("private detail")

    monkeypatch.setattr(lab, "_inputs", bad_source)
    with pytest.raises(lab.Refusal) as caught:
        app.predict(request())
    assert caught.value.code == "SOURCE_UNAUTHORIZED" and "private" not in caught.value.message


def test_candidate_loader_dispatch_and_explicit_grants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def loader(*args: Any, **kwargs: Any) -> object:
        calls.append((args, kwargs))
        return object()

    for i in range(9):
        module = lab.ci if i < 7 else lab.m7 if i == 7 else lab.m8
        monkeypatch.setattr(module, f"load_gate7_m{i}", loader)
        grant = lab.ModelGrant(
            f"M{i}",
            1,
            tmp_path / "config",
            tmp_path / "weights",
            "a" * 64,
            "b" * 64,
            "source",
            "association",
            "model",
        )
        grant.config_path.touch()
        grant.checkpoint_path.touch()
        lab._original(grant)  # pyright: ignore[reportPrivateUsage]
        assert calls[-1][0] == (grant.config_path, grant.checkpoint_path)
        assert calls[-1][1] == {
            "config_sha256": "a" * 64,
            "checkpoint_sha256": "b" * 64,
            "repeat": 1,
        }
    assert len(calls) == 9


def test_future_observation_rejected() -> None:
    builder = lab.generate_gate7_fixture_v1()
    with pytest.raises(ValueError):
        replace(builder.origins[0], available_at_origin_hours=1.0)


def _exchange(
    port: int, method: str, path: str, body: bytes = b"", *, headers: dict[str, str]
) -> tuple[int, dict[str, Any]]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, path, body=body if method == "POST" else None, headers=headers)
        response = conn.getresponse()
        return response.status, json.loads(response.read())
    finally:
        conn.close()


def test_loopback_http_and_end_to_end_synthetic_fixture() -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=lab.serve,
        args=(lab.ResearchLab(lab.fixture_observations()), TOKEN),
        kwargs={"port": port},
        daemon=False,
    )
    process.start()
    try:
        for _ in range(100):
            try:
                status, _ = _exchange(port, "GET", "/v1/health", headers={"X-Lab-Token": TOKEN})
                if status == 200:
                    break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("service did not start")
        headers = {
            "X-Lab-Token": TOKEN,
            "Origin": "http://127.0.0.1:3000",
            "Content-Type": "application/json",
        }
        status, result = _exchange(
            port, "POST", "/v1/predict", json.dumps(request()).encode(), headers=headers
        )
        assert (
            status == 200
            and result["kind"] == "synthetic_demo"
            and result["outputs"][0]["unit"] == "N/kg"
        )
        status, result = _exchange(
            port, "POST", "/v1/predict", b'{"version":"a","version":"b"}', headers=headers
        )
        assert status == 400 and result["error"]["code"] == "MALFORMED_REQUEST"
        status, result = _exchange(
            port, "POST", "/v1/predict", b"x" * (lab.MAX_BODY + 1), headers=headers
        )
        assert status == 400 and result["error"]["code"] == "MALFORMED_REQUEST"
        status, _ = _exchange(port, "GET", "/v1/capabilities", headers={"X-Lab-Token": "wrong"})
        assert status == 403
        status, _ = _exchange(
            port,
            "GET",
            "/v1/capabilities",
            headers={"X-Lab-Token": TOKEN, "Origin": "https://example.invalid"},
        )
        assert status == 403
        status, _ = _exchange(
            port,
            "GET",
            "/v1/capabilities",
            headers={"X-Lab-Token": TOKEN, "Host": "attacker.invalid"},
        )
        assert status == 403
    finally:
        process.terminate()
        process.join(timeout=5)
