"""Critic / Evaluator agent.

Scores the draft and can request a retry. This is the in-loop quality gate. It is
also a cautionary tale: the critic here passes the misrouted answer and the
ungrounded answer, because both read well. A quality gate that only checks whether
an answer *sounds* good is not the same as one that checks whether it is *right*.
That gap is precisely why the offline evals in evals/ exist.
"""

from __future__ import annotations

import re

from agents.base import State, TraceStep
from agents.prompts import load_prompt
from app.config import CONFIG
from llm.client import call_llm


def _parse_score(text: str) -> float:
    match = re.search(r"Score:\s*([0-9]*\.?[0-9]+)", text)
    if match:
        try:
            return max(0.0, min(1.0, float(match.group(1))))
        except ValueError:
            return 0.0
    return 0.0


class CriticAgent:
    name = "critic"

    def run(self, state: State) -> State:
        user = (
            f"Ticket ID: {state.ticket.get('id')}\n"
            f"Subject: {state.ticket.get('subject', '')}\n"
            f"Body: {state.ticket.get('body', '')}\n\n"
            f"Proposed response:\n{state.draft or ''}"
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a critic. Score the proposed response from 0.0 to 1.0 "
                    "for how well it resolves the ticket. Reply as 'Score: <x>' and a "
                    "one-line reason.\n\n" + load_prompt("solver")
                ),
            },
            {"role": "user", "content": user},
        ]
        resp = call_llm(messages, purpose="critic")
        score = _parse_score(resp.text)
        state.scores["critic"] = score

        below_bar = score < CONFIG.critic_pass_threshold
        can_retry = state.retry_count < CONFIG.max_retries
        # Do not retry a response the guardrail has already flagged; that goes
        # straight to a human.
        blocked = bool(state.guardrail_flags)
        state.retry_requested = below_bar and can_retry and not blocked

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={"ticket_id": state.ticket.get("id"), "attempt": state.retry_count + 1},
                outputs={
                    "score": score,
                    "threshold": CONFIG.critic_pass_threshold,
                    "retry_requested": state.retry_requested,
                    "raw": resp.text,
                },
                latency_s=resp.latency_s,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                cost_usd=resp.cost_usd,
            )
        )
        return state
