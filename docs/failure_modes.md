# Failure modes

Every failure below is built in on purpose and reproducible. Each scenario in
`examples/` actually triggers its failure when you run it; it is not just
documented. Run any of them with:

```bash
python -m app.main examples/<scenario>.json
```

| Scenario file | Failure it triggers | What to look for |
|---|---|---|
| `examples/easy_ticket.json` | none (happy path) | correct route, grounded answer, auto-resolved |
| `examples/ambiguous_ticket.json` | wrong route | routes to `technical`, expected `billing`; every in-loop check passes and it auto-resolves a clean answer to the wrong problem |
| `examples/missing_context.json` | retrieval gap, plausible-but-useless answer | retrieval finds little; the draft invents settings paths; critic still passes it |
| `examples/malicious_prompt_injection.json` | guardrail must catch | guardrail raises flags for both the injection in the ticket and the leak in the draft; escalates, sends nothing |
| `examples/conflicting_documents.json` | evaluation ambiguity | docs say 30 days, policy says 14; the answer follows the doc and auto-approves, tripping the policy-compliance check |
| `examples/bad_llm_judge_case.json` | judge passes a bad answer | verbose, confident, ungrounded answer; LLM-as-judge scores it high, groundedness scores it low |
| `examples/expensive_route.json` | excessive agent/tool calls, cost/latency spike | critic keeps rejecting; the loop retries to the budget; cost, latency, and tool-call count balloon, then it escalates anyway |

## The through-line

The point is not that any one of these is hard to fix in isolation. It is that
each one produces output that *looks fine*:

- The misrouted ticket gets a fluent, confident answer.
- The missing-context ticket gets specific, step-by-step instructions.
- The verbose empty answer reads as thorough and warm.

A green dashboard, a passing in-loop critic, and a happy LLM-as-judge can all
agree that the system worked while the trace shows it did not. Closing that gap is
what the evaluation harness (`evals/`) and the traces (`traces/`) are for.

## Where each failure is caught (and not caught)

| Failure | Caught by | Missed by |
|---|---|---|
| Wrong route | route-accuracy eval, the trace | critic, LLM-as-judge, answer-relevance |
| Missing context | groundedness eval, the trace | critic, LLM-as-judge |
| Prompt injection | guardrail (deterministic + policy) | a naive setup with no guardrail |
| Conflicting docs | policy-compliance eval | groundedness (the answer *is* grounded, just in the wrong source) |
| Judge fooled | golden-answer comparison, groundedness | the LLM-as-judge itself |
| Cost blowup | cost/latency budget in the eval | any check that ignores cost |

Notice that no single metric catches everything, and the two most trusted
in-loop signals (the critic and the LLM-as-judge) catch the least. That is the
argument.

The LLM-as-judge failure is not unique to this repo. OpenAI documents it directly
as "grader hacking" in their [Graders](https://developers.openai.com/api/docs/guides/graders)
guide, and LangSmith's [LLM-as-a-judge](https://docs.langchain.com/langsmith/llm-as-judge)
docs cover configuring and, crucially, validating a judge. The lesson both share,
and the one `evals/judges/llm_as_judge.py` makes concrete: a judge you have not
tried to fool is a judge that is fooling you. For the broader risk taxonomy,
prompt injection is [OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).
See [references.md](references.md) for the full source list.
