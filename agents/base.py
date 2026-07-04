"""Shared agent interface and shared state.

No framework. The whole multi-agent contract is: agents read and write one
`State` object and each appends a `TraceStep`. That is enough to demonstrate
handoff, shared state, retries, and end-to-end observability, and it keeps the
architecture legible from a single slide.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Protocol


@dataclass
class TraceStep:
    """One agent's contribution to the trace: what it did, and what it cost.

    The presence of latency/tokens/cost on every step is deliberate. It is what
    turns 'the dashboard is green' into something you can actually inspect."""
    agent: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    latency_s: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class State:
    """The single object passed between every agent."""
    ticket: dict[str, Any]

    route: str | None = None
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    draft: str | None = None
    scores: dict[str, float] = field(default_factory=dict)
    guardrail_flags: list[str] = field(default_factory=list)
    decision: str | None = None          # "auto_resolve" or "escalate"
    final_response: str | None = None
    escalation_reason: str | None = None

    retry_count: int = 0
    retry_requested: bool = False

    trace: list[TraceStep] = field(default_factory=list)

    def add_step(self, step: TraceStep) -> None:
        self.trace.append(step)

    # --- Aggregates used by traces and evals ---------------------------------
    @property
    def total_cost_usd(self) -> float:
        return round(sum(s.cost_usd for s in self.trace), 6)

    @property
    def total_latency_s(self) -> float:
        return round(sum(s.latency_s for s in self.trace), 3)

    @property
    def total_tokens(self) -> int:
        return sum(s.prompt_tokens + s.completion_tokens for s in self.trace)

    @property
    def tool_call_count(self) -> int:
        return sum(len(s.outputs.get("tool_calls", [])) for s in self.trace)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket": self.ticket,
            "route": self.route,
            "retrieved_context": self.retrieved_context,
            "draft": self.draft,
            "scores": self.scores,
            "guardrail_flags": self.guardrail_flags,
            "decision": self.decision,
            "final_response": self.final_response,
            "escalation_reason": self.escalation_reason,
            "retry_count": self.retry_count,
            "totals": {
                "cost_usd": self.total_cost_usd,
                "latency_s": self.total_latency_s,
                "tokens": self.total_tokens,
                "tool_calls": self.tool_call_count,
            },
            "trace": [asdict(s) for s in self.trace],
        }


class Agent(Protocol):
    """Minimal interface. Every agent takes state and returns updated state."""

    name: str

    def run(self, state: State) -> State: ...
