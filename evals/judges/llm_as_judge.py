"""LLM-as-judge.

Scores an answer with the judge prompt and returns a verdict. This is the most
seductive eval to build and the easiest to trust too much. It is included here
precisely so its failures are visible: on the ambiguous, missing-context,
conflicting, and reliability cases it returns PASS for answers that are wrong,
ungrounded, or empty. Compare its verdict against `should_pass` from the golden
dataset to find where it was fooled. See notebooks/eval_analysis.ipynb.

The naive rubric lives in prompts/judge.md. A stricter rubric that checks
groundedness and penalises verbosity lives in judges/judge_prompts/strict_judge.md.
Swapping between them is a good live demo of how much the rubric matters.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llm.client import call_llm

JUDGE_PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "judge.md").read_text(
    encoding="utf-8"
)


def _parse(text: str) -> dict[str, Any]:
    verdict_match = re.search(r"Verdict:\s*(PASS|FAIL)", text, re.IGNORECASE)
    score_match = re.search(r"Score:\s*([0-9]*\.?[0-9]+)", text)
    return {
        "verdict": verdict_match.group(1).upper() if verdict_match else "FAIL",
        "score": float(score_match.group(1)) if score_match else 0.0,
        "raw": text.strip(),
    }


def judge_answer(ticket: dict[str, Any], answer: str | None) -> dict[str, Any]:
    if not answer:
        # Nothing was sent to the customer (escalated). Treat as a non-answer.
        return {"verdict": "FAIL", "score": 0.0, "raw": "no answer (escalated)"}

    user = (
        f"Ticket ID: {ticket.get('id')}\n"
        f"Ticket: {ticket.get('subject', '')} {ticket.get('body', '')}\n\n"
        f"Proposed response: {answer}"
    )
    resp = call_llm(
        [
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": user},
        ],
        purpose="judge",
    )
    return _parse(resp.text)
