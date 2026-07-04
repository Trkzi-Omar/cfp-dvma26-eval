"""Eval-harness tests.

Assert the report has the expected shape, that metrics stay in range, and that the
fooled-judge cases we rely on for the talk are actually surfaced. If a change to a
prompt or metric quietly stopped fooling the judge, this test fails, which is the
regression signal the eval harness exists to provide.
"""

from __future__ import annotations

from evals.run_evals import _build_results, compute_report


def test_report_has_expected_shape():
    report = compute_report(_build_results())
    for key in ["metrics", "fooled_judge_cases", "failed_cases", "results"]:
        assert key in report
    for name in [
        "route_accuracy",
        "answer_relevance",
        "groundedness",
        "policy_compliance",
        "cost_latency",
    ]:
        assert name in report["metrics"]


def test_metric_values_in_range():
    report = compute_report(_build_results())
    for name in ["route_accuracy", "answer_relevance", "groundedness", "policy_compliance"]:
        value = report["metrics"][name]["value"]
        assert 0.0 <= value <= 1.0


def test_judge_is_fooled_on_expected_cases():
    report = compute_report(_build_results())
    fooled_ids = {c["id"] for c in report["fooled_judge_cases"]}
    # These are the cases the talk demonstrates; they must stay fooled.
    for tid in ["ambiguous-001", "missing-001", "badjudge-001"]:
        assert tid in fooled_ids


def test_groundedness_flags_ungrounded_answers():
    report = compute_report(_build_results())
    per = report["metrics"]["groundedness"]["per_ticket"]
    # The confident-but-invented answer must score low on groundedness.
    assert per["missing-001"] is not None and per["missing-001"] < 0.3


def test_expensive_route_exceeds_budget():
    report = compute_report(_build_results())
    assert "expensive-001" in report["metrics"]["cost_latency"]["over_budget"]
