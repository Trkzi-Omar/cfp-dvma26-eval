"""Metric: routing accuracy.

Compares the route the router chose against the expected route from
evals/datasets/expected_routes.jsonl. Routing is the cheapest thing to get wrong
and the easiest to miss, because a wrong route still produces a confident answer.
"""

from __future__ import annotations

from typing import Any


def evaluate(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    misroutes = [r["id"] for r in results if r["route"] != r["expected_route"]]
    correct = total - len(misroutes)
    return {
        "name": "route_accuracy",
        "value": round(correct / total, 4) if total else 0.0,
        "correct": correct,
        "total": total,
        "misroutes": misroutes,
    }
