"""Guardrail tests.

The injection scenario must always be caught and escalated, never auto-resolved.
This is the one failure mode where a silent miss is a security incident, so it
gets the strongest test.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import run_pipeline

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _ticket(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_injection_is_flagged_and_escalated():
    state = run_pipeline(_ticket("malicious_prompt_injection.json"))
    assert state.guardrail_flags, "expected the guardrail to raise at least one flag"
    assert state.decision == "escalate"
    assert state.escalation_reason == "guardrail_flagged"
    assert state.final_response is None, "a flagged response must never be sent"


def test_injection_detected_in_ticket_body():
    state = run_pipeline(_ticket("malicious_prompt_injection.json"))
    assert any(f.startswith("injection_in_ticket") for f in state.guardrail_flags)


def test_leak_detected_in_draft():
    state = run_pipeline(_ticket("malicious_prompt_injection.json"))
    assert any(f.startswith("leak_in_draft") for f in state.guardrail_flags)


def test_benign_ticket_is_not_flagged():
    state = run_pipeline(_ticket("easy_ticket.json"))
    assert state.guardrail_flags == []
    assert state.decision == "auto_resolve"
