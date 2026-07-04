"""Finalizer agent.

Turns the accumulated state into a decision: auto-resolve and send the response,
or escalate to a human. Escalation happens when the guardrail raised a flag, or
when the critic could not get the draft above the quality bar within the retry
budget. It writes the outcome back to the (fake) ticket system so the run has a
real side effect to observe.
"""

from __future__ import annotations

from agents.base import State, TraceStep
from app.config import CONFIG
from tools.ticket_system import update_ticket


class FinalizerAgent:
    name = "finalizer"

    def run(self, state: State) -> State:
        ticket_id = str(state.ticket.get("id", "unknown"))
        critic_score = state.scores.get("critic", 0.0)

        if state.guardrail_flags:
            state.decision = "escalate"
            state.escalation_reason = "guardrail_flagged"
            state.final_response = None
        elif critic_score < CONFIG.critic_pass_threshold:
            state.decision = "escalate"
            state.escalation_reason = "quality_below_threshold_after_retries"
            state.final_response = None
        else:
            state.decision = "auto_resolve"
            state.final_response = state.draft

        if state.decision == "auto_resolve":
            record = update_ticket(
                ticket_id, status="resolved", resolution=state.final_response or ""
            )
        else:
            record = update_ticket(
                ticket_id,
                status="escalated",
                resolution=f"Escalated: {state.escalation_reason}",
            )

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={"ticket_id": ticket_id, "critic_score": critic_score},
                outputs={
                    "decision": state.decision,
                    "escalation_reason": state.escalation_reason,
                    "ticket_update": record,
                    "tool_calls": [{"tool": "update_ticket", "status": record["status"]}],
                },
            )
        )
        return state
