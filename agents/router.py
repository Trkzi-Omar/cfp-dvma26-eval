"""Router / Planner agent.

Classifies the ticket into a category that decides which documents the retrieval
agent will pull. This is the first place production systems fail quietly: a wrong
route sends a correct-looking pipeline at the wrong problem. The ambiguous ticket
in examples/ is engineered to be misrouted here so that failure is reproducible.
"""

from __future__ import annotations

import re

from agents.base import State, TraceStep
from agents.prompts import load_prompt
from llm.client import call_llm

VALID_ROUTES = {"billing", "technical", "account", "general"}


def _format_ticket(ticket: dict) -> str:
    return (
        f"Ticket ID: {ticket.get('id', 'unknown')}\n"
        f"Subject: {ticket.get('subject', '')}\n"
        f"Body: {ticket.get('body', '')}\n"
        f"Customer tier: {ticket.get('customer_tier', 'unknown')}"
    )


def _parse_route(text: str) -> str:
    match = re.search(r"Route:\s*([a-zA-Z]+)", text)
    if match:
        candidate = match.group(1).lower()
        if candidate in VALID_ROUTES:
            return candidate
    # Fallback: pick any category mentioned, else general.
    for route in VALID_ROUTES:
        if route in text.lower():
            return route
    return "general"


class RouterAgent:
    name = "router"

    def run(self, state: State) -> State:
        messages = [
            {"role": "system", "content": load_prompt("router")},
            {"role": "user", "content": _format_ticket(state.ticket)},
        ]
        resp = call_llm(messages, purpose="router")
        route = _parse_route(resp.text)
        state.route = route

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={"ticket_id": state.ticket.get("id")},
                outputs={"route": route, "raw": resp.text},
                latency_s=resp.latency_s,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                cost_usd=resp.cost_usd,
            )
        )
        return state
