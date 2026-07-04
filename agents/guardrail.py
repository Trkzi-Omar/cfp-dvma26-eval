"""Guardrail agent.

Two layers, on purpose. A cheap deterministic pass catches known
prompt-injection patterns in the incoming ticket and obvious leaks in the draft.
A second LLM pass provides a policy-aware judgement. Either layer can raise a
flag. When a flag is raised the pipeline escalates instead of auto-resolving.

Defence in depth matters here because relying on the model alone to police the
model is exactly the gap the talk warns about.
"""

from __future__ import annotations

import re

from agents.base import State, TraceStep
from agents.prompts import load_prompt
from llm.client import call_llm

# Known injection / exfiltration signals. Not exhaustive; representative.
_INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|earlier) (instructions|rules)",
    r"disregard .{0,20}(instructions|policy|rules)",
    r"reveal .{0,20}(system prompt|instructions)",
    r"you are now",
    r"admin token",
    r"override .{0,20}policy",
]

# Signals that the DRAFT itself is unsafe to send.
_LEAK_PATTERns = [
    r"admin[-_ ]?\d{3,}",
    r"internal .{0,20}token",
    r"other customers'? (emails|data)",
]


def _scan(text: str, patterns: list[str]) -> list[str]:
    found = []
    lowered = text.lower()
    for pat in patterns:
        if re.search(pat, lowered):
            found.append(pat)
    return found


class GuardrailAgent:
    name = "guardrail"

    def run(self, state: State) -> State:
        ticket_text = f"{state.ticket.get('subject', '')} {state.ticket.get('body', '')}"
        draft = state.draft or ""

        flags: list[str] = []
        for pat in _scan(ticket_text, _INJECTION_PATTERNS):
            flags.append(f"injection_in_ticket:{pat}")
        for pat in _scan(draft, _LEAK_PATTERns):
            flags.append(f"leak_in_draft:{pat}")

        # LLM policy pass.
        user = (
            f"Ticket ID: {state.ticket.get('id')}\n"
            f"Incoming ticket: {ticket_text}\n\n"
            f"Drafted response: {draft}"
        )
        messages = [
            {"role": "system", "content": load_prompt("guardrail")},
            {"role": "user", "content": user},
        ]
        resp = call_llm(messages, purpose="guardrail")
        if resp.text.strip().upper().startswith("BLOCK"):
            flags.append(f"policy_block:{resp.text.strip()}")

        state.guardrail_flags = flags

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={"ticket_id": state.ticket.get("id")},
                outputs={"flags": flags, "verdict": resp.text, "blocked": bool(flags)},
                latency_s=resp.latency_s,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                cost_usd=resp.cost_usd,
            )
        )
        return state
