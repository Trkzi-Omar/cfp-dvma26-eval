# Architecture

The system is a small, fixed graph of single-purpose agents that pass one shared
state object between them. There is no agent framework. The entire contract is:
each agent reads and writes `State` (see `agents/base.py`) and appends a
`TraceStep`. That is enough to demonstrate handoff, shared state, routing,
retries, tool use, and end-to-end observability, and it keeps the whole thing
legible from a single slide.

```
Incoming ticket
      |
      v
  Router / Planner Agent      -> classifies the ticket, decides the route
      |
      v
  Specialist Agents (run in sequence over the shared state)
      |-- Retrieval Agent      -> pulls relevant docs and policies
      |-- Solver Agent         -> drafts a proposed response
      |-- Guardrail Agent      -> checks policy, catches injection and leaks
      |-- Critic / Evaluator   -> scores the draft, can trigger a retry
      |
      v
  Finalizer Agent             -> auto-resolves or escalates to a human
```

The retrieve -> solve -> guardrail -> critic sequence runs in a loop. If the
critic scores the draft below the quality bar and the retry budget is not
exhausted, the loop runs again. This is where cost accumulates, which the
`expensive_route` scenario makes visible.

## The agents

**Router / Planner (`agents/router.py`).** Classifies the ticket into `billing`,
`technical`, `account`, or `general`. The route decides which document set the
retriever searches, so a wrong route sends a correct-looking pipeline at the
wrong problem. This is the first and quietest failure in production, which is why
the ambiguous scenario is engineered to misroute here.

**Retrieval (`agents/retriever.py`).** Searches `data/docs` (filtered by the
route's category) and `data/policies` with simple keyword overlap. Retrieval
quality is not the point; retrieval *failure* is. An empty or wrong-category
result is a valid outcome that shows up downstream as an ungrounded answer.

**Solver (`agents/solver.py`).** Drafts a response from the retrieved context.
When retrieval found the right material, the draft is grounded and correct. When
it did not, the draft is confident and wrong, which is exactly how it behaves in
the field.

**Guardrail (`agents/guardrail.py`).** Two layers: a deterministic scan for known
injection and leak patterns, and an LLM policy check. Either can raise a flag. A
flagged response is never sent; it escalates. Defence in depth matters because
relying on the model alone to police the model is the gap the talk warns about.

**Critic / Evaluator (`agents/critic.py`).** Scores the draft and can request a
retry. It is an in-loop quality gate, and a cautionary one: it passes the
misrouted answer and the ungrounded answer because both read well. A gate that
checks whether an answer *sounds* good is not the same as one that checks whether
it is *right*. That gap is why the offline evals exist.

**Finalizer (`agents/finalizer.py`).** Turns the accumulated state into a
decision: auto-resolve and send, or escalate to a human. It writes the outcome
back to the fake ticket system so each run has a real side effect to observe.

## The shared state

`agents/base.py` defines `State` (ticket, route, retrieved context, draft, scores,
guardrail flags, decision, final response, retry count, and the trace) and
`TraceStep` (agent, inputs, outputs, latency, tokens, cost). Every agent appends
one step, so the full trace of a request, including its cost and latency budget,
is available for inspection without any external tracing system.

## The LLM boundary

`llm/client.py` is the only module that knows how to call a provider. Everything
else calls `call_llm`. In mock mode (the default) it delegates to `llm/mock.py`,
which returns deterministic, canned responses keyed on the ticket. That is what
makes the demo and the evals reproducible and offline. Swapping in a real
provider is a one-file change behind the same interface, which is the point of
keeping the architecture framework-agnostic.
