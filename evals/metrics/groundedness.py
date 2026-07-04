"""Metric: groundedness.

Is the sent answer actually supported by the documents that were retrieved?
Heuristic: fraction of the answer's content terms that appear in the retrieved
context. A confident answer built on nothing (the missing-context case) or on
empty superlatives (the fooled-judge case) scores low here even when the
LLM-as-judge is happy with it. Groundedness is the metric that most often
disagrees with a naive judge, which is exactly the point.
"""

from __future__ import annotations

from typing import Any

from evals.metrics._text import terms


def score_one(result: dict[str, Any]) -> float | None:
    if not result.get("answer"):
        return None
    answer_terms = terms(result["answer"])
    context_terms = terms(result.get("retrieved_text", ""))
    if not answer_terms:
        return 0.0
    supported = answer_terms & context_terms
    return round(len(supported) / len(answer_terms), 4)


def evaluate(results: list[dict[str, Any]]) -> dict[str, Any]:
    per = {r["id"]: score_one(r) for r in results}
    scored = [v for v in per.values() if v is not None]
    avg = round(sum(scored) / len(scored), 4) if scored else 0.0
    return {"name": "groundedness", "value": avg, "per_ticket": per}
