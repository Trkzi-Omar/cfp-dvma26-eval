"""Metric: cost and latency aggregation.

Averages cost, latency, and tool-call count across the dataset, and flags any
ticket that blew past a per-request budget. The expensive-route case is the one
that trips the budget: retries multiply every downstream call. Operating an agent
system without a per-request cost and retry budget is how a quiet regression turns
into a large invoice.
"""

from __future__ import annotations

from typing import Any

COST_BUDGET_USD = 0.0015
TOOL_CALL_BUDGET = 4


def evaluate(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results) or 1
    avg_cost = round(sum(r["cost"] for r in results) / total, 6)
    avg_latency = round(sum(r["latency"] for r in results) / total, 3)
    avg_tools = round(sum(r["tool_calls"] for r in results) / total, 2)

    over_budget = [
        r["id"]
        for r in results
        if r["cost"] > COST_BUDGET_USD or r["tool_calls"] > TOOL_CALL_BUDGET
    ]

    return {
        "name": "cost_latency",
        "avg_cost_usd": avg_cost,
        "avg_latency_s": avg_latency,
        "avg_tool_calls": avg_tools,
        "cost_budget_usd": COST_BUDGET_USD,
        "over_budget": over_budget,
    }
