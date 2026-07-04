"""Regenerate the committed example traces.

`make traces` runs this. It executes the three canonical scenarios and writes
their full traces to traces/examples/ under stable names the talk refers to:

- sample_success_trace.json        the happy path
- sample_bad_route_trace.json      every check passed, but the router was wrong
- sample_guardrail_failure_trace.json  the guardrail caught an injection

It then prints a one-line summary of each so `make traces` shows something real.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import load_ticket, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "traces" / "examples"

SCENARIOS = [
    ("examples/easy_ticket.json", "sample_success_trace.json"),
    ("examples/ambiguous_ticket.json", "sample_bad_route_trace.json"),
    ("examples/malicious_prompt_injection.json", "sample_guardrail_failure_trace.json"),
]


def main() -> int:
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    for src, out_name in SCENARIOS:
        ticket = load_ticket(REPO_ROOT / src)
        state = run_pipeline(ticket)
        out = EXAMPLES / out_name
        out.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")

        route = state.route
        expected = state.ticket.get("expected_route")
        route_flag = " (MISROUTE)" if expected and route != expected else ""
        print(
            f"{out_name:<38} route={route}{route_flag} "
            f"decision={state.decision} "
            f"guardrail_flags={len(state.guardrail_flags)} "
            f"cost=${state.total_cost_usd:.4f}"
        )
    print(f"\nExample traces written to: {EXAMPLES.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
