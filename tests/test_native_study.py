"""Invented fixtures and approvals only; no real cohort or protected predictions."""

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("torch")

from cmj_recovery_dynamics import native_study as study  # noqa: E402
from cmj_recovery_dynamics.metrics.native_analysis import (  # noqa: E402
    _digest,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.metrics.native_rehearsal import rehearsal_plan  # noqa: E402
from cmj_recovery_dynamics.observations.native_preflight import (  # noqa: E402
    dataset_manifest_sha256,
    synthetic_preflight_fixture,
    synthetic_trusted_reviews,
)
from cmj_recovery_dynamics.research_lab import (  # noqa: E402
    ModelGrant,
    _demo,  # pyright: ignore[reportPrivateUsage]
)


def invented_case(kind: str = "synthetic") -> dict[str, Any]:
    data = synthetic_preflight_fixture(3)
    data["dataset_kind"] = kind
    for review in data["reviews"].values():
        review["dataset_sha256"] = dataset_manifest_sha256(data)
    reviews = synthetic_trusted_reviews(data)
    plan = replace(rehearsal_plan(), hypothetical_thresholds=kind == "synthetic")
    plan = replace(plan, rules=tuple(replace(rule, minimum_participants=3) for rule in plan.rules))
    grants = tuple(
        ModelGrant(
            f"M{i}",
            r,
            Path("invented-config"),
            Path("invented-weight"),
            "a" * 64,
            "b" * 64,
            "invented-source",
            "invented-pair",
            f"M{i}-r{r}",
        )
        for i in range(9)
        for r in (0, 1)
    )
    auth = {
        "version": "gate7_offline_study_authorization_v1",
        "approved_at": "2020-01-01T00:00:00+00:00",
        "expires_at": "2099-01-01T00:00:00+00:00",
        "dataset_sha256": _digest(data),
        "plan_sha256": _digest(asdict(plan)),
        "models_sha256": _digest(study.model_identities(grants)),
        "trusted_reviews_sha256": _digest(reviews),
        "runtime_sha256": _digest(study.study_runtime_identity()),
        "registered_participants": 3,
        "registered_origins": 3,
        "minimum_retention_fraction": 0.8,
        "decisions": {
            scope: {
                "decision": "approved",
                "authority": "invented-test-authority",
                "reference": "invented-test-only-not-a-human-approval",
            }
            for scope in study.AUTHORIZATION_SCOPES
        },
    }
    return dict(
        payload=data,
        plan=plan,
        grants=grants,
        authorization=auth,
        expected_authorization_sha256=_digest(auth),
        trusted_reviews=reviews,
    )


@pytest.mark.parametrize("kind", ("synthetic", "empirical"))
def test_complete_offline_path_on_invented_records(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    case = invented_case(kind)
    calls: list[tuple[str, int]] = []

    def load(grant: ModelGrant) -> Any:
        calls.append((grant.candidate, grant.repeat))
        return _demo(grant.candidate, grant.repeat)

    monkeypatch.setattr(study, "_original", load)
    result = study.execute_native_study(**case)
    assert len(set(calls)) == 18
    assert len(result["cells"]) == 4
    assert all(len(cell["models"]) == 9 for cell in result["cells"])
    assert result["group_count"] == 3 and result["query_count"] == 6
    assert len(result["offline_study"]["models"]) == 18
    assert "predictions" not in result
    assert result["empirical_execution_authorized"] == (kind == "empirical")
    # The empirical marker is a test of the future path, never an actual cohort.
    assert result == study.execute_native_study(**case)


@pytest.mark.parametrize(
    "change",
    (
        "pin",
        "dataset",
        "plan",
        "model",
        "reviews",
        "runtime",
        "expiry",
        "scope",
        "retention",
        "hypothetical",
        "basis",
        "overlap",
        "missing_repeat",
    ),
)
def test_refuses_before_model_execution(monkeypatch: pytest.MonkeyPatch, change: str) -> None:
    case = invented_case("empirical")
    auth = case["authorization"]
    if change == "pin":
        case["expected_authorization_sha256"] = "0" * 64
    elif change == "dataset":
        case["payload"]["queries"][0]["targets"]["relative_mean_concentric_force"] += 1
    elif change == "plan":
        case["plan"] = replace(case["plan"], seed=99)
    elif change == "model":
        case["grants"] = (
            replace(case["grants"][0], checkpoint_sha256="e" * 64),
            *case["grants"][1:],
        )
    elif change == "reviews":
        case["trusted_reviews"]["measurement_authority"] = "e" * 64
    elif change == "runtime":
        auth["runtime_sha256"] = "e" * 64
    elif change == "expiry":
        auth["expires_at"] = "2021-01-01T00:00:00+00:00"
    elif change == "scope":
        del auth["decisions"]["ethics_determination"]
    elif change == "retention":
        auth["registered_origins"] = 100
    elif change == "hypothetical":
        case["plan"] = replace(case["plan"], hypothetical_thresholds=True)
        auth["plan_sha256"] = _digest(asdict(case["plan"]))
    elif change in ("basis", "overlap"):
        if change == "basis":
            case["payload"]["queries"][0]["basis"][0] += 1
        else:
            case["payload"]["participant_splits"]["test"].append("invented-train")
        for review in case["payload"]["reviews"].values():
            review["dataset_sha256"] = dataset_manifest_sha256(case["payload"])
        case["trusted_reviews"] = synthetic_trusted_reviews(case["payload"])
        auth["dataset_sha256"] = _digest(case["payload"])
        auth["trusted_reviews_sha256"] = _digest(case["trusted_reviews"])
    elif change == "missing_repeat":
        case["grants"] = case["grants"][:-1]
    if change not in ("pin", "dataset", "plan", "model", "reviews"):
        case["expected_authorization_sha256"] = _digest(auth)
    calls: list[object] = []

    def refused_load(grant: ModelGrant) -> None:
        calls.append(grant)

    monkeypatch.setattr(study, "_original", refused_load)
    with pytest.raises(ValueError):
        study.execute_native_study(**case)
    assert calls == []


def test_model_failure_never_produces_partial_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(grant: ModelGrant) -> Any:
        raise OSError("private path and protected details")

    monkeypatch.setattr(study, "_original", fail)
    with pytest.raises(ValueError, match="STUDY_MODEL_EXECUTION_FAILED") as error:
        study.execute_native_study(**invented_case())
    assert "private path" not in str(error.value)
