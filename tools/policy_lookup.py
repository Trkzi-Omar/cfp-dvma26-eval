"""Tool: retrieve support policies from data/policies.

Same keyword approach as search_docs, over the policy corpus. Policies are what
the guardrail and the conflicting-documents scenario lean on: note that the
refund policy (14 days) intentionally disagrees with the refund documentation
(30 days) so the conflicting-documents case has a real contradiction to expose.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

POLICIES_DIR = Path(__file__).resolve().parents[1] / "data" / "policies"

_STOP = {
    "the", "a", "an", "to", "of", "and", "or", "is", "are", "i", "my", "me",
    "how", "do", "can", "you", "your", "for", "in", "on", "it", "this", "that",
    "with", "was", "am", "not", "but", "please", "help",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 2]


def policy_lookup(query: str, top_k: int = 2) -> list[dict[str, Any]]:
    """Return up to top_k policies relevant to the query."""
    query_tokens = set(_tokens(query))
    results: list[dict[str, Any]] = []

    for path in sorted(POLICIES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        doc_tokens = set(_tokens(text))
        overlap = query_tokens & doc_tokens
        if not overlap:
            continue
        score = round(len(overlap) / max(1, len(query_tokens)), 3)
        results.append(
            {
                "source": path.name,
                "score": score,
                "matched_terms": sorted(overlap),
                "content": text.strip(),
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]
