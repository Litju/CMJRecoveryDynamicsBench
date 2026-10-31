"""The full native engineering rehearsal is deterministic and refuses corruptions."""

from cmj_recovery_dynamics.metrics.native_rehearsal import synthetic_rehearsal_v1


def test_all_eighteen_synthetic_routes_admit_analyze_and_refuse_corruptions() -> None:
    result = synthetic_rehearsal_v1()
    assert result == synthetic_rehearsal_v1()
    assert result["candidate_repeat_combinations"] == 18
    assert result["admission"]["eligible"]
    assert result["analysis"]["group_count"] == 6
    assert result["analysis"]["query_count"] == 12
    assert len(result["analysis"]["cells"]) == 4
    assert len(result["negative_controls"]) == 11
    assert all(result["negative_controls"].values())
    assert result["analysis"]["synthetic_decision"] == "criteria_not_met"
    assert not result["empirical_execution_authorized"]
    assert all(d["holm_adjusted_p"] > 0.05 for d in result["analysis"]["decisions"])
