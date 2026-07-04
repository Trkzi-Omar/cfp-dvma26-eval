"""Metric: answer relevance.

How much of the customer's question does the sent answer actually engage with?
Heuristic: overlap between the answer's terms and the ticket's terms. This
rewards answers that stay on the customer's topic. Note it does NOT catch the
ambiguous case well: a fluent login answer overlaps with a ticket that mentions
login, even when the real problem was billing. That blind spot is intentional and
is why relevance alone is insufficient.
"""

from __future__ import annotations

from typing import Any

from evals.metrics._text import terms


def score_one(result: dict[str, Any]) -> float | None:
    if not result.get("answer"):
        return None  # escalated; nothing was sent
    ticket_terms = terms(result["subject"] + " " + result["body"])
    answer_terms = terms(result["answer"])
    if not ticket_terms:
        return 0.0
    overlap = ticket_terms & answer_terms
    return round(len(overlap) / len(ticket_terms), 4)


def evaluate(results: list[dict[str, Any]]) -> dict[str, Any]:
    per = {r["id"]: score_one(r) for r in results}
    scored = [v for v in per.values() if v is not None]
    avg = round(sum(scored) / len(scored), 4) if scored else 0.0
    return {"name": "answer_relevance", "value": avg, "per_ticket": per}
