"""Run the evaluation harness over the fixed dataset.

    python -m evals.run_evals                 # run offline evals, write a report
    python -m evals.run_evals --baseline      # also save this run as the regression baseline

Three eval types, all in mock mode so the numbers are reproducible:

- Offline evals: route accuracy, answer relevance, groundedness, policy
  compliance, cost, latency, tool calls, over the dataset.
- LLM-as-judge: scores each answer, then we compare its verdict against the
  golden `should_pass` to surface the cases where the judge was fooled.
- Regression: if a baseline report exists, print the delta so a prompt, model, or
  agent change that silently moved a metric is visible before "deploy".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.main import run_pipeline
from evals.judges.llm_as_judge import judge_answer
from evals.metrics import (
    answer_relevance,
    cost_latency,
    groundedness,
    policy_compliance,
    route_accuracy,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS = REPO_ROOT / "evals" / "datasets"
REPORTS = REPO_ROOT / "evals" / "reports"
BASELINE = REPORTS / "baseline.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _build_results() -> list[dict[str, Any]]:
    tickets = _load_jsonl(DATASETS / "support_tickets.jsonl")
    expected_routes = {r["id"]: r["expected_route"] for r in _load_jsonl(DATASETS / "expected_routes.jsonl")}
    golden = {g["id"]: g for g in _load_jsonl(DATASETS / "golden_answers.jsonl")}

    results: list[dict[str, Any]] = []
    for ticket in tickets:
        state = run_pipeline(ticket)
        g = golden.get(ticket["id"], {})
        answer = state.final_response
        judged = judge_answer(ticket, answer)
        retrieved_text = " ".join(c.get("content", "") for c in state.retrieved_context)

        results.append(
            {
                "id": ticket["id"],
                "subject": ticket.get("subject", ""),
                "body": ticket.get("body", ""),
                "route": state.route,
                "expected_route": expected_routes.get(ticket["id"]),
                "answer": answer,
                "decision": state.decision,
                "expected_decision": g.get("expected_decision"),
                "should_pass": g.get("should_pass"),
                "guardrail_flags": state.guardrail_flags,
                "retrieved_text": retrieved_text,
                "cost": state.total_cost_usd,
                "latency": state.total_latency_s,
                "tool_calls": state.tool_call_count,
                "retries": state.retry_count,
                "judge_verdict": judged["verdict"],
                "judge_score": judged["score"],
            }
        )
    return results


def _fooled_judge_cases(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A judge is 'fooled' when it PASSes an answer the golden data says should
    not pass, or FAILs one that should pass."""
    fooled = []
    for r in results:
        if r["should_pass"] is None:
            continue
        judge_pass = r["judge_verdict"] == "PASS"
        if judge_pass != r["should_pass"]:
            fooled.append(
                {
                    "id": r["id"],
                    "judge_verdict": r["judge_verdict"],
                    "judge_score": r["judge_score"],
                    "should_pass": r["should_pass"],
                    "groundedness": groundedness.score_one(r),
                    "why": "judge passed a bad answer" if judge_pass else "judge failed a good answer",
                }
            )
    return fooled


def _failed_cases(results: list[dict[str, Any]], metrics: dict[str, Any]) -> list[str]:
    """A case counts as failed if it deviates from the golden outcome in any way:
    wrong route, wrong decision, or a policy violation."""
    failed = set(metrics["route_accuracy"]["misroutes"])
    failed.update(metrics["policy_compliance"]["violations"].keys())
    for r in results:
        if r["expected_decision"] and r["decision"] != r["expected_decision"]:
            failed.add(r["id"])
    return sorted(failed)


def compute_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = {
        "route_accuracy": route_accuracy.evaluate(results),
        "answer_relevance": answer_relevance.evaluate(results),
        "groundedness": groundedness.evaluate(results),
        "policy_compliance": policy_compliance.evaluate(results),
        "cost_latency": cost_latency.evaluate(results),
    }
    fooled = _fooled_judge_cases(results)
    failed = _failed_cases(results, metrics)
    return {
        "metrics": metrics,
        "fooled_judge_cases": fooled,
        "failed_cases": failed,
        "results": results,
    }


def _pct(x: float) -> str:
    return f"{round(x * 100)}%"


def print_summary(report: dict[str, Any]) -> None:
    m = report["metrics"]
    cl = m["cost_latency"]
    print("=" * 60)
    print("EVAL SUMMARY (mock mode, reproducible)")
    print("-" * 60)
    print(f"Route accuracy:      {_pct(m['route_accuracy']['value'])}")
    print(f"Answer relevance:    {_pct(m['answer_relevance']['value'])}")
    print(f"Groundedness:        {_pct(m['groundedness']['value'])}")
    print(f"Policy compliance:   {_pct(m['policy_compliance']['value'])}")
    print(f"Avg latency:         {cl['avg_latency_s']}s")
    print(f"Avg cost/request:    ${cl['avg_cost_usd']:.4f}")
    print(f"Failed cases:        {len(report['failed_cases'])}  {report['failed_cases']}")
    print("-" * 60)
    print("LLM-as-judge: fooled cases (judge disagreed with ground truth):")
    if not report["fooled_judge_cases"]:
        print("  (none)")
    for c in report["fooled_judge_cases"]:
        print(
            f"  {c['id']:<16} judge={c['judge_verdict']} "
            f"(score {c['judge_score']})  groundedness={c['groundedness']}  "
            f"-> {c['why']}"
        )
    print("=" * 60)


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORTS.mkdir(exist_ok=True)
    json_path = REPORTS / "latest.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md_path = REPORTS / "latest.md"
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    m = report["metrics"]
    cl = m["cost_latency"]
    lines = ["# Eval report", "", "Run in mock mode. Reproducible.", "", "## Metrics", ""]
    lines += [
        "| Metric | Value |",
        "|---|---|",
        f"| Route accuracy | {_pct(m['route_accuracy']['value'])} |",
        f"| Answer relevance | {_pct(m['answer_relevance']['value'])} |",
        f"| Groundedness | {_pct(m['groundedness']['value'])} |",
        f"| Policy compliance | {_pct(m['policy_compliance']['value'])} |",
        f"| Avg latency | {cl['avg_latency_s']}s |",
        f"| Avg cost/request | ${cl['avg_cost_usd']:.4f} |",
        f"| Failed cases | {len(report['failed_cases'])} |",
        "",
        "## Fooled-judge cases",
        "",
        "| Ticket | Judge | Judge score | Groundedness | Why |",
        "|---|---|---|---|---|",
    ]
    for c in report["fooled_judge_cases"]:
        lines.append(
            f"| {c['id']} | {c['judge_verdict']} | {c['judge_score']} | "
            f"{c['groundedness']} | {c['why']} |"
        )
    lines += ["", "## Misroutes", "", ", ".join(m["route_accuracy"]["misroutes"]) or "(none)"]
    lines += ["", "## Policy violations", ""]
    for tid, v in m["policy_compliance"]["violations"].items():
        lines.append(f"- {tid}: {v}")
    return "\n".join(lines) + "\n"


def regression_check(report: dict[str, Any]) -> None:
    if not BASELINE.exists():
        print("\n[regression] No baseline found. Run with --baseline to create one.")
        return
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    print("\n[regression] Comparing against baseline:")
    keys = ["route_accuracy", "answer_relevance", "groundedness", "policy_compliance"]
    changed = False
    for k in keys:
        now = report["metrics"][k]["value"]
        was = baseline["metrics"][k]["value"]
        delta = round(now - was, 4)
        flag = "" if delta == 0 else ("  <-- CHANGED" if abs(delta) >= 0.0001 else "")
        if delta != 0:
            changed = True
        print(f"  {k:<20} {was} -> {now}  (delta {delta:+}){flag}")
    if not changed:
        print("  No metric changed. Safe to ship on these checks.")


def main(argv: list[str]) -> int:
    results = _build_results()
    report = compute_report(results)
    print_summary(report)
    json_path, md_path = write_report(report)
    print(f"\nReport written to: {json_path.relative_to(REPO_ROOT)} and {md_path.relative_to(REPO_ROOT)}")

    regression_check(report)

    if "--baseline" in argv:
        BASELINE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nBaseline saved to: {BASELINE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
