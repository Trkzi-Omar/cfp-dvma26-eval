"""Entry point: run one support ticket end to end through the agent graph.

    python -m app.main                                  # easy_ticket.json (happy path)
    python -m app.main examples/ambiguous_ticket.json   # watch it misroute
    python -m app.main examples/malicious_prompt_injection.json  # guardrail catch

Prints the decision and a compact trace summary, and writes the full trace JSON to
traces/ so it can be opened and read. Runs in mock mode by default: no key, no
network, deterministic output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from agents.base import State
from agents.critic import CriticAgent
from agents.finalizer import FinalizerAgent
from agents.guardrail import GuardrailAgent
from agents.retriever import RetrieverAgent
from agents.router import RouterAgent
from agents.solver import SolverAgent
from app.config import CONFIG

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = REPO_ROOT / "traces"


def run_pipeline(ticket: dict[str, Any]) -> State:
    """Run the full router -> specialists -> finalizer graph, with retries."""
    state = State(ticket=ticket)

    RouterAgent().run(state)

    while True:
        RetrieverAgent().run(state)
        SolverAgent().run(state)
        GuardrailAgent().run(state)
        CriticAgent().run(state)

        if state.retry_requested:
            state.retry_count += 1
            state.retry_requested = False
            continue
        break

    FinalizerAgent().run(state)
    return state


def load_ticket(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def print_summary(state: State, example_path: Path) -> None:
    print("=" * 70)
    print(f"Scenario:   {example_path.name}")
    print(f"Ticket:     {state.ticket.get('id')}  |  {state.ticket.get('subject')}")
    print(f"Mode:       {'MOCK' if CONFIG.mock_mode else 'LIVE (' + CONFIG.model + ')'}")
    print("-" * 70)
    print("Trace:")
    for i, step in enumerate(state.trace, 1):
        key_out = _headline(step.agent, step.outputs)
        print(
            f"  {i}. {step.agent:<10} {key_out:<44} "
            f"{step.latency_s:>4}s  ${step.cost_usd:.4f}"
        )
    print("-" * 70)
    expected = state.ticket.get("expected_route")
    route_note = ""
    if expected and state.route != expected:
        route_note = f"  <-- expected '{expected}' (MISROUTE)"
    print(f"Route:            {state.route}{route_note}")
    print(f"Critic score:     {state.scores.get('critic')}")
    print(f"Guardrail flags:  {len(state.guardrail_flags)}")
    print(f"Retries:          {state.retry_count}")
    print(f"Decision:         {state.decision.upper()}"
          + (f" ({state.escalation_reason})" if state.escalation_reason else ""))
    print(f"Total cost:       ${state.total_cost_usd:.4f}")
    print(f"Total latency:    {state.total_latency_s}s")
    print(f"Tool calls:       {state.tool_call_count}")
    print("-" * 70)
    if state.final_response:
        print("Final response to customer:")
        print(f"  {state.final_response}")
    else:
        print(f"No auto-response. Escalated to a human ({state.escalation_reason}).")
    print("=" * 70)


def _headline(agent: str, outputs: dict[str, Any]) -> str:
    if agent == "router":
        return f"route={outputs.get('route')}"
    if agent == "retriever":
        return f"retrieved={outputs.get('retrieved_count')} docs"
    if agent == "solver":
        return "drafted response"
    if agent == "guardrail":
        return f"blocked={outputs.get('blocked')} flags={len(outputs.get('flags', []))}"
    if agent == "critic":
        return f"score={outputs.get('score')} retry={outputs.get('retry_requested')}"
    if agent == "finalizer":
        return f"decision={outputs.get('decision')}"
    return ""


def main(argv: list[str]) -> int:
    example_arg = argv[1] if len(argv) > 1 else "examples/easy_ticket.json"
    example_path = (REPO_ROOT / example_arg).resolve()
    if not example_path.exists():
        print(f"Example not found: {example_path}", file=sys.stderr)
        return 1

    ticket = load_ticket(example_path)
    state = run_pipeline(ticket)
    print_summary(state, example_path)

    TRACES_DIR.mkdir(exist_ok=True)
    out_path = TRACES_DIR / f"{state.ticket.get('id', 'ticket')}_trace.json"
    out_path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    print(f"\nFull trace written to: {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
