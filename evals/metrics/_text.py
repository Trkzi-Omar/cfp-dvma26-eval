"""Shared tokenization for the heuristic metrics.

Kept tiny and dependency-free on purpose. These metrics are illustrative: they
show the *shape* of relevance and groundedness scoring, not a production-grade
implementation. In production you would use embeddings or a calibrated judge.
"""

from __future__ import annotations

import re

_STOP = {
    "the", "a", "an", "to", "of", "and", "or", "is", "are", "i", "my", "me",
    "how", "do", "can", "you", "your", "for", "in", "on", "it", "this", "that",
    "with", "was", "am", "not", "but", "please", "help", "hi", "hello", "we",
    "our", "us", "if", "so", "from", "at", "as", "be", "will", "have", "has",
}


def terms(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
        if t not in _STOP and len(t) > 2
    }
