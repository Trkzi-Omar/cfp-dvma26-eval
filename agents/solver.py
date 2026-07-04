"""Solver agent.

Drafts a response from the retrieved context. Because the mock keys its draft on
the ticket, the quality of each draft mirrors what really happens: when retrieval
found nothing, the draft is confident but ungrounded; when the route was wrong,
the draft cleanly answers the wrong question.
"""

from __future__ import annotations

from agents.base import State, TraceStep
from agents.prompts import load_prompt
from llm.client import call_llm


def _format_context(state: State) -> str:
    if not state.retrieved_context:
        return "(no documents were retrieved)"
    parts = []
    for item in state.retrieved_context:
        parts.append(f"[{item['kind']}: {item['source']}]\n{item.get('content', '')}")
    return "\n\n".join(parts)


class SolverAgent:
    name = "solver"

    def run(self, state: State) -> State:
        user = (
            f"Ticket ID: {state.ticket.get('id')}\n"
            f"Subject: {state.ticket.get('subject', '')}\n"
            f"Body: {state.ticket.get('body', '')}\n\n"
            f"Retrieved context:\n{_format_context(state)}"
        )
        messages = [
            {"role": "system", "content": load_prompt("solver")},
            {"role": "user", "content": user},
        ]
        resp = call_llm(messages, purpose="solver")
        state.draft = resp.text

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={
                    "ticket_id": state.ticket.get("id"),
                    "retrieved_count": len(state.retrieved_context),
                    "attempt": state.retry_count + 1,
                },
                outputs={"draft": resp.text},
                latency_s=resp.latency_s,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                cost_usd=resp.cost_usd,
            )
        )
        return state
