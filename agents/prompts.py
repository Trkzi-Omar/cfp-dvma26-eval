"""Helper to load the markdown system prompts from prompts/.

Prompts live as markdown so they are readable in a slide and reviewable in a PR,
not buried in string literals.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
