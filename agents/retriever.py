"""Retrieval agent.

Pulls documentation and policy relevant to the ticket. It searches only within
the category the router chose, so a wrong route retrieves the wrong corpus, and a
question with no matching docs retrieves nothing at all. Both are on purpose: the
downstream answer is only as good as what this step surfaces.
"""

from __future__ import annotations

from agents.base import State, TraceStep
from tools.policy_lookup import policy_lookup
from tools.search_docs import search_docs


class RetrieverAgent:
    name = "retriever"

    def run(self, state: State) -> State:
        query = f"{state.ticket.get('subject', '')} {state.ticket.get('body', '')}"

        docs = search_docs(query, route=state.route, top_k=2)
        policies = policy_lookup(query, top_k=2)

        context = [{"kind": "doc", **d} for d in docs] + [
            {"kind": "policy", **p} for p in policies
        ]
        state.retrieved_context = context

        tool_calls = [
            {"tool": "search_docs", "route": state.route, "hits": len(docs)},
            {"tool": "policy_lookup", "hits": len(policies)},
        ]

        state.add_step(
            TraceStep(
                agent=self.name,
                inputs={"query": query, "route": state.route},
                outputs={
                    "doc_hits": [d["source"] for d in docs],
                    "policy_hits": [p["source"] for p in policies],
                    "retrieved_count": len(context),
                    "tool_calls": tool_calls,
                },
            )
        )
        return state
