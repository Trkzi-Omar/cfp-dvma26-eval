"""Routing tests.

These lock in both the correct behaviour (easy ticket routes to account) and the
deliberate failure (the ambiguous ticket misroutes). The misroute test is not a
bug we forgot to fix; it is a guarantee that the demonstrable failure stays
demonstrable.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import run_pipeline

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _ticket(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_easy_ticket_routes_correctly():
    state = run_pipeline(_ticket("easy_ticket.json"))
    assert state.route == "account"


def test_ambiguous_ticket_misroutes_on_purpose():
    ticket = _ticket("ambiguous_ticket.json")
    state = run_pipeline(ticket)
    # The real category is billing; the router latches onto the login symptom.
    assert ticket["expected_route"] == "billing"
    assert state.route == "technical"
    assert state.route != ticket["expected_route"]


def test_injection_ticket_routes_general():
    state = run_pipeline(_ticket("malicious_prompt_injection.json"))
    assert state.route == "general"


def test_route_is_always_valid():
    from agents.router import VALID_ROUTES

    for name in ["easy_ticket.json", "conflicting_documents.json", "expensive_route.json"]:
        state = run_pipeline(_ticket(name))
        assert state.route in VALID_ROUTES
