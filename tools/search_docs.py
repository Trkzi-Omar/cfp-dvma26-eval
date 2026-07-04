"""Tool: retrieve product documentation from data/docs.

Deliberately simple: keyword overlap, no embeddings. Retrieval quality is not the
point of this repo. Retrieval *failure* is. Docs are filtered by the route's
category first (filenames are prefixed with the category), so a wrong route
retrieves the wrong document set, which is exactly the failure the ambiguous and
missing-context scenarios demonstrate.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "docs"

_STOP = {
    "the", "a", "an", "to", "of", "and", "or", "is", "are", "i", "my", "me",
    "how", "do", "can", "you", "your", "for", "in", "on", "it", "this", "that",
    "with", "was", "am", "not", "but", "please", "help", "hi", "hello",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 2]


def search_docs(query: str, route: str | None = None, top_k: int = 2) -> list[dict[str, Any]]:
    """Return up to top_k docs relevant to the query, filtered by route category.

    An empty result is a valid and important outcome: it means the retrieval
    layer found nothing, which downstream shows up as an ungrounded answer.
    """
    query_tokens = set(_tokens(query))
    results: list[dict[str, Any]] = []

    for path in sorted(DOCS_DIR.glob("*.md")):
        category = path.stem.split("_", 1)[0]
        if route and category != route:
            continue
        text = path.read_text(encoding="utf-8")
        doc_tokens = set(_tokens(text))
        overlap = query_tokens & doc_tokens
        if not overlap:
            continue
        score = round(len(overlap) / max(1, len(query_tokens)), 3)
        results.append(
            {
                "source": path.name,
                "category": category,
                "score": score,
                "matched_terms": sorted(overlap),
                "snippet": text.strip().splitlines()[0][:200] if text.strip() else "",
                "content": text.strip(),
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]
