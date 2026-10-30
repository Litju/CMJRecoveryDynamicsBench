"""Local, operator-authorized research inference over the recovered Gate7 models.

This module requires the optional inference extra. Network clients select only
operator-registered observations and model grants; they never provide paths,
preprocessing, source claims, basis values, or source pins.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import multiprocessing
import re
import secrets
import socket
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Final, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction import checkpoint_inference as ci
from cmj_recovery_dynamics.model_reproduction import checkpoint_m7 as m7
from cmj_recovery_dynamics.model_reproduction import checkpoint_m8_inference as m8
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    project_gate7_history_v1,
    project_gate7_v1,
)
from cmj_recovery_dynamics.observations.public_builder import (
    Gate7ObservationBuilderV1,
    generate_gate7_fixture_v1,
)

VERSION: Final = "gate7-lab-v1"
ALIAS = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
MAX_BODY = 8192


class Refusal(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _alias(value: str) -> bool:
    return type(value) is str and ALIAS.fullmatch(value) is not None


@dataclass(frozen=True)
class ModelGrant:
    """Operator-attested association, kept out of all network messages.

    The independent authority record, source identity, and hash association must
    be established outside this application before constructing this grant.
    """

    candidate: str
    repeat: int
    config_path: Path
    checkpoint_path: Path
    config_sha256: str
    checkpoint_sha256: str
    source_authority: str
    association_authority: str
    public_alias: str

    def __post_init__(self) -> None:
        if (
            self.candidate not in tuple(f"M{i}" for i in range(9))
            or type(self.repeat) is not int
            or self.repeat not in (0, 1)
            or not isinstance(cast(object, self.config_path), Path)
            or not isinstance(cast(object, self.checkpoint_path), Path)
            or not DIGEST.fullmatch(self.config_sha256)
            or not DIGEST.fullmatch(self.checkpoint_sha256)
            or not self.source_authority.strip()
            or not self.association_authority.strip()
            or not _alias(self.public_alias)
        ):
            raise ValueError("invalid operator model grant")


@dataclass(frozen=True)
class BasisGrant:
    """Operator-pinned basis and independently authorized row association."""

    values: tuple[float, float, float, float, float]
    row_sha256: str
    authority: str

    def __post_init__(self) -> None:
        if (
            type(self.values) is not tuple
            or len(self.values) != 5
            or any(type(x) not in (int, float) or not math.isfinite(x) for x in self.values)
            or not DIGEST.fullmatch(self.row_sha256)
            or not self.authority.strip()
        ):
            raise ValueError("invalid operator basis grant")


@dataclass(frozen=True)
class ObservationGrant:
    """A startup-registered query bound to an existing pinned observation builder."""

    id: str
    label: str
    origin_label: str
    builder: Gate7ObservationBuilderV1
    origin_id: str
    horizon: ForecastHorizon
    source: str
    authority: str
    basis: BasisGrant | None = None

    def __post_init__(self) -> None:
        if (
            not all(_alias(x) for x in (self.id, self.label, self.origin_label))
            or type(self.builder) is not Gate7ObservationBuilderV1
            or self.horizon not in (ForecastHorizon.H72, ForecastHorizon.D7)
            or self.source not in ("synthetic", "authorized")
            or not self.authority.strip()
        ):
            raise ValueError("invalid operator observation grant")
        self.builder.build(self.origin_id, self.horizon)


def row_digest(
    source_sha256: str,
    origin_id: str,
    raw: NDArray[np.float64],
    history: NDArray[np.float64],
    horizon: int,
    basis: tuple[float, float, float, float, float],
) -> str:
    """Canonical row identity; the expected digest must come from independent authority."""
    payload = json.dumps(
        [source_sha256, origin_id, raw.tolist(), history.tolist(), horizon, list(basis)],
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def fixture_observations() -> tuple[ObservationGrant, ...]:
    result: list[ObservationGrant] = []
    for split in ("training", "public_validation"):
        builder = generate_gate7_fixture_v1(split)
        for i, item in enumerate(builder.inputs()):
            result.append(
                ObservationGrant(
                    f"{split}-{i}",
                    f"Synthetic-{i + 1}",
                    f"Origin-{i // 2 + 1}",
                    builder,
                    item.row.origin_id,
                    item.row.horizon,
                    "synthetic",
                    "public-fixture-v1",
                )
            )
    return tuple(result)


def _inputs(grant: ObservationGrant) -> tuple[NDArray[np.float64], NDArray[np.float64], int]:
    item = grant.builder.build(grant.origin_id, grant.horizon)
    projection = project_gate7_v1((item,), routine_source=grant.builder.routine_source)
    if projection.matrix is None:
        raise Refusal("SOURCE_UNAUTHORIZED", "The observation source cannot be projected.")
    history = project_gate7_history_v1((item.row,))
    return projection.matrix, history, 0 if grant.horizon is ForecastHorizon.H72 else 1


def _demo(candidate: str, repeat: int) -> Any:
    """Deterministic synthetic parameters for a visibly labeled demonstration."""
    i = int(candidate[1:])
    with torch.random.fork_rng(devices=[]):  # pyright: ignore[reportUnknownMemberType]
        torch.manual_seed(1000 + i * 2 + repeat)  # pyright: ignore[reportUnknownMemberType]
        if i < 3:
            layers: list[nn.Module] = [nn.Linear(39, 32 if i == 0 else 64), nn.GELU()]
            if i == 2:
                layers.extend((nn.Linear(64, 64), nn.GELU()))
            layers.append(nn.Linear(32 if i == 0 else 64, 2))
            model: Any = nn.Sequential(*layers)
        else:
            factories = (
                ci._Gate7M3Model,  # pyright: ignore[reportPrivateUsage]
                ci._Gate7M4Model,  # pyright: ignore[reportPrivateUsage]
                ci._Gate7M5Model,  # pyright: ignore[reportPrivateUsage]
                ci._Gate7M6Model,  # pyright: ignore[reportPrivateUsage]
                m7._Gate7M7Model,  # pyright: ignore[reportPrivateUsage]
                m8._Gate7M8Model,  # pyright: ignore[reportPrivateUsage]
            )
            model = factories[i - 3]()
    raw_mean, raw_scale = np.zeros(39), np.ones(39)
    history_mean, history_scale = np.zeros(4), np.ones(4)
    if i < 3:
        cls = (ci.Gate7M0Predictor, ci.Gate7M1Predictor, ci.Gate7M2Predictor)[i]
        return cls(repeat, raw_mean, raw_scale, model)
    if i < 6:
        cls = (ci.Gate7M3Predictor, ci.Gate7M4Predictor, ci.Gate7M5Predictor)[i - 3]
        return cls(repeat, raw_mean, raw_scale, history_mean, history_scale, model)
    cls = (ci.Gate7M6Predictor, m7.Gate7M7Predictor, m8.Gate7M8Predictor)[i - 6]
    return cls(
        repeat, raw_mean, raw_scale, history_mean, history_scale, np.zeros(5), np.ones(5), model
    )


def _original(grant: ModelGrant) -> Any:
    if (
        grant.config_path.stat().st_size > 1_000_000
        or grant.checkpoint_path.stat().st_size > 8_000_000
    ):
        raise ValueError("artifact exceeds local limit")
    loaders = (
        ci.load_gate7_m0,
        ci.load_gate7_m1,
        ci.load_gate7_m2,
        ci.load_gate7_m3,
        ci.load_gate7_m4,
        ci.load_gate7_m5,
        ci.load_gate7_m6,
        m7.load_gate7_m7,
        m8.load_gate7_m8,
    )
    return loaders[int(grant.candidate[1:])](
        grant.config_path,
        grant.checkpoint_path,
        config_sha256=grant.config_sha256,
        checkpoint_sha256=grant.checkpoint_sha256,
        repeat=grant.repeat,
    )


class ResearchLab:
    def __init__(
        self, observations: tuple[ObservationGrant, ...], models: tuple[ModelGrant, ...] = ()
    ):
        if len(observations) > 256 or len(models) > 18:
            raise ValueError("too many registered entries")
        self.observations = {item.id: item for item in observations}
        self.models = {(item.candidate, item.repeat): item for item in models}
        if len(self.observations) != len(observations) or len(self.models) != len(models):
            raise ValueError("duplicate registered entries")

    def capabilities(self) -> dict[str, object]:
        observations: list[dict[str, object]] = []
        for x in self.observations.values():
            availability, basis_availability = "available", "unavailable"
            try:
                raw, history, horizon = _inputs(x)
                if x.basis is not None and hmac.compare_digest(
                    row_digest(
                        x.builder.expected_observations_sha256,
                        x.origin_id,
                        raw,
                        history,
                        horizon,
                        x.basis.values,
                    ),
                    x.basis.row_sha256,
                ):
                    basis_availability = "authorized"
            except Exception:
                availability = "unavailable"
            observations.append(
                {
                    "id": x.id,
                    "label": x.label,
                    "origin": x.origin_label,
                    "horizon": x.horizon.label,
                    "source": x.source,
                    "availability": availability,
                    "basis_availability": basis_availability,
                }
            )
        return {
            "version": VERSION,
            "observations": observations,
            "models": [
                {
                    "candidate": f"M{i}",
                    "repeat": rep,
                    "available": (f"M{i}", rep) in self.models,
                    "provenance": self.models[(f"M{i}", rep)].public_alias
                    if (f"M{i}", rep) in self.models
                    else None,
                    "qualification": "CPU_SOURCE_QUALIFIED",
                    "input_contract": (
                        "raw"
                        if i < 3
                        else "raw_history"
                        if i < 5
                        else "raw_history_horizon"
                        if i == 5
                        else "raw_history_horizon_basis"
                    ),
                }
                for i in range(9)
                for rep in (0, 1)
            ],
        }

    def predict(self, request: object) -> dict[str, object]:
        if not isinstance(request, dict):
            raise Refusal("MALFORMED_REQUEST", "Request fields do not match the contract.")
        values = cast(dict[str, object], request)
        if set(values) != {
            "version",
            "candidate",
            "repeat",
            "observation_id",
            "mode",
        }:
            raise Refusal("MALFORMED_REQUEST", "Request fields do not match the contract.")
        candidate, repeat, observation_id, mode = (
            values[k] for k in ("candidate", "repeat", "observation_id", "mode")
        )
        if (
            values["version"] != VERSION
            or type(candidate) is not str
            or candidate not in tuple(f"M{i}" for i in range(9))
            or type(repeat) is not int
            or repeat not in (0, 1)
            or type(observation_id) is not str
            or mode not in ("original", "synthetic_demo")
        ):
            raise Refusal("MALFORMED_REQUEST", "Request values do not match the contract.")
        observation = self.observations.get(observation_id)
        if observation is None:
            raise Refusal("SOURCE_UNAUTHORIZED", "Observation is not registered.", 403)
        if mode == "synthetic_demo" and observation.source != "synthetic":
            raise Refusal(
                "SOURCE_UNAUTHORIZED", "Demonstration requires synthetic observations.", 403
            )
        model_grant = self.models.get((candidate, repeat))
        if mode == "original" and model_grant is None:
            raise Refusal("MODEL_UNAVAILABLE", "No authorized model is registered.", 404)
        try:
            raw, history, horizon = _inputs(observation)
        except Refusal:
            raise
        except Exception as exc:
            raise Refusal(
                "SOURCE_UNAUTHORIZED", "The observation source cannot be projected.", 403
            ) from exc
        index = int(candidate[1:])
        args: list[Any] = [raw]
        if index >= 3:
            args.append(history)
        if index >= 5:
            args.append(np.asarray([horizon], dtype=np.int64))
        if index >= 6:
            basis = observation.basis
            if basis is None or not hmac.compare_digest(
                row_digest(
                    observation.builder.expected_observations_sha256,
                    observation.origin_id,
                    raw,
                    history,
                    horizon,
                    basis.values,
                ),
                basis.row_sha256,
            ):
                raise Refusal(
                    "BASIS_AUTHORITY_UNAVAILABLE",
                    "Basis authority is unavailable for this observation.",
                    403,
                )
            args.append(np.asarray([basis.values], dtype=np.float64))
        try:
            if mode == "synthetic_demo":
                predictor = _demo(candidate, repeat)
            else:
                assert model_grant is not None
                predictor = _original(model_grant)
            result: Any = predictor.predict(*args)
            if result.shape != (1, 2) or not np.isfinite(result).all():
                raise ValueError("invalid output")
        except Exception as exc:
            raise Refusal("INFERENCE_FAILED", "Inference could not be completed.", 422) from exc
        output = [float(result[0, 0]), float(result[0, 1])]
        source_binding: list[object] = [
            observation.builder.source_identity,
            observation.builder.expected_observations_sha256,
            observation.builder.routine_source.expected_sha256,
            observation.origin_id,
            observation.horizon.label,
            observation.authority,
        ]
        if index >= 6 and observation.basis is not None:
            source_binding.extend((observation.basis.row_sha256, observation.basis.authority))
        model_binding: list[object] = ["synthetic-weights-v1"]
        if model_grant is not None and mode == "original":
            model_binding = [
                model_grant.config_sha256,
                model_grant.checkpoint_sha256,
                model_grant.source_authority,
                model_grant.association_authority,
            ]
        identity = hashlib.sha256(
            json.dumps(
                [
                    VERSION,
                    candidate,
                    repeat,
                    observation.id,
                    mode,
                    source_binding,
                    model_binding,
                    output,
                ],
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest()
        return {
            "version": VERSION,
            "kind": "synthetic_demo" if mode == "synthetic_demo" else "original_checkpoint",
            "candidate": candidate,
            "repeat": repeat,
            "observation_id": observation.id,
            "origin": observation.origin_label,
            "horizon": observation.horizon.label,
            "outputs": [
                {"target": ci.TARGETS[0], "unit": "N/kg", "value": output[0]},
                {"target": ci.TARGETS[1], "unit": "m/s", "value": output[1]},
            ],
            "qualification": {
                "cpu_source": "not_applicable_synthetic_weights"
                if mode == "synthetic_demo"
                else "qualified",
                "cuda_comparison": "not_applicable_synthetic_weights"
                if mode == "synthetic_demo"
                else ("pass" if index < 4 else "failed"),
            },
            "cuda_evidence": "not_applicable"
            if mode == "synthetic_demo"
            else "cpu_vs_saved_cuda_not_gpu_replay",
            "identity": identity,
            "provenance": "synthetic-weights"
            if mode == "synthetic_demo"
            else (model_grant.public_alias if model_grant is not None else "unavailable"),
        }


def _worker(lab: ResearchLab, request: object, connection: Any) -> None:
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        connection.send((200, lab.predict(request)))
    except Refusal as exc:
        connection.send(
            (exc.status, {"version": VERSION, "error": {"code": exc.code, "message": exc.message}})
        )
    except Exception:
        connection.send(
            (
                500,
                {
                    "version": VERSION,
                    "error": {
                        "code": "INFERENCE_FAILED",
                        "message": "Inference could not be completed.",
                    },
                },
            )
        )
    finally:
        connection.close()


def _bounded_predict(lab: ResearchLab, request: object) -> tuple[int, dict[str, object]]:
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    worker = context.Process(target=_worker, args=(lab, request, child), daemon=True)
    try:
        worker.start()
        child.close()
        if not parent.poll(20):
            return 504, {
                "version": VERSION,
                "error": {
                    "code": "INFERENCE_TIMEOUT",
                    "message": "Inference exceeded its local time limit.",
                },
            }
        status, payload = cast(tuple[int, dict[str, object]], parent.recv())
        return status, payload
    except (EOFError, OSError):
        return 500, {
            "version": VERSION,
            "error": {"code": "INFERENCE_FAILED", "message": "Inference could not be completed."},
        }
    finally:
        parent.close()
        child.close()
        if worker.pid is not None:
            worker.join(timeout=0.2)
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=1)
            if worker.is_alive():
                worker.kill()
                worker.join()


def serve(
    lab: ResearchLab, token: str, *, port: int = 8765, allowed_origin: str = "http://127.0.0.1:3000"
) -> None:
    """Serve one request at a time on loopback; grants are set by the operator."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", token):
        raise ValueError("a secret token of at least 32 characters is required")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid port")
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", allowed_origin):
        raise ValueError("UI origin must be an explicit loopback HTTP origin")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self) -> None:
            super().setup()

            def expire() -> None:
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            self.deadline = threading.Timer(25, expire)
            self.deadline.daemon = True
            self.deadline.start()

        def finish(self) -> None:
            self.deadline.cancel()
            super().finish()

        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _reply(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            if self.headers.get("Origin") == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def _admit(self, authenticated: bool = True) -> bool:
            if self.headers.get_all("Host", []) != [f"127.0.0.1:{port}"]:
                self._reply(
                    403,
                    {
                        "version": VERSION,
                        "error": {"code": "ACCESS_DENIED", "message": "Access denied."},
                    },
                )
                return False
            if (
                len(self.headers.get_all("Origin", [])) > 1
                or len(self.headers.get_all("X-Lab-Token", [])) > 1
            ):
                self._reply(
                    403,
                    {
                        "version": VERSION,
                        "error": {"code": "ACCESS_DENIED", "message": "Access denied."},
                    },
                )
                return False
            origin = self.headers.get("Origin")
            if origin is not None and origin != allowed_origin:
                self._reply(
                    403,
                    {
                        "version": VERSION,
                        "error": {"code": "ACCESS_DENIED", "message": "Access denied."},
                    },
                )
                return False
            if authenticated and not secrets.compare_digest(
                self.headers.get("X-Lab-Token", ""), token
            ):
                self._reply(
                    403,
                    {
                        "version": VERSION,
                        "error": {"code": "ACCESS_DENIED", "message": "Access denied."},
                    },
                )
                return False
            return True

        def do_OPTIONS(self) -> None:
            if not self._admit(False):
                return
            if self.headers.get("Origin") != allowed_origin or self.path not in (
                "/v1/health",
                "/v1/capabilities",
                "/v1/predict",
            ):
                self._reply(
                    403,
                    {
                        "version": VERSION,
                        "error": {"code": "ACCESS_DENIED", "message": "Access denied."},
                    },
                )
                return
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Lab-Token")
            self.send_header("Vary", "Origin")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True

        def do_GET(self) -> None:
            if not self._admit():
                return
            if self.path == "/v1/health":
                self._reply(200, {"version": VERSION, "status": "ok"})
            elif self.path == "/v1/capabilities":
                self._reply(200, lab.capabilities())
            else:
                self._reply(
                    404,
                    {
                        "version": VERSION,
                        "error": {"code": "NOT_FOUND", "message": "Endpoint not found."},
                    },
                )

        def do_POST(self) -> None:
            if not self._admit():
                return
            if self.path != "/v1/predict":
                self._reply(
                    404,
                    {
                        "version": VERSION,
                        "error": {"code": "NOT_FOUND", "message": "Endpoint not found."},
                    },
                )
                return
            try:
                lengths = self.headers.get_all("Content-Length", [])
                if (
                    len(lengths) != 1
                    or not lengths[0].isdigit()
                    or int(lengths[0]) > MAX_BODY
                    or self.headers.get("Transfer-Encoding") is not None
                    or self.headers.get_content_type() != "application/json"
                ):
                    raise Refusal("MALFORMED_REQUEST", "Invalid request body.")
                body = self.rfile.read(int(lengths[0]))
                if len(body) != int(lengths[0]):
                    raise Refusal("MALFORMED_REQUEST", "Incomplete request body.")
                try:

                    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
                        result: dict[str, object] = {}
                        for key, value in pairs:
                            if key in result:
                                raise ValueError("duplicate key")
                            result[key] = value
                        return result

                    request: object = json.loads(body, object_pairs_hook=unique_object)
                except (ValueError, UnicodeDecodeError, RecursionError) as exc:
                    raise Refusal("MALFORMED_REQUEST", "Invalid JSON.") from exc
                status, response = _bounded_predict(lab, request)
                self._reply(status, response)
            except Refusal as exc:
                self._reply(
                    exc.status,
                    {"version": VERSION, "error": {"code": exc.code, "message": exc.message}},
                )
            except (TimeoutError, OSError):
                self.close_connection = True
            except Exception:
                self._reply(
                    500,
                    {
                        "version": VERSION,
                        "error": {
                            "code": "INFERENCE_FAILED",
                            "message": "Inference could not be completed.",
                        },
                    },
                )

    class LocalServer(HTTPServer):
        def handle_error(self, request: Any, client_address: Any) -> None:
            pass

        def get_request(self) -> tuple[socket.socket, Any]:
            request, address = super().get_request()
            request.settimeout(5.0)
            return request, address

    with LocalServer(("127.0.0.1", port), Handler) as server:
        server.serve_forever()


def main() -> None:
    import os

    token = os.environ.get("GATE7_LAB_TOKEN", "")
    try:
        serve(ResearchLab(fixture_observations()), token)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
