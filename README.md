# multi-agent-prod-reference

A production-shaped reference implementation for **evaluating and operating multi-agent LLM systems**. Built-in failure cases, traces, and regression evals included.

This is not a chatbot demo. It is a compact, framework-agnostic system that shows what happens to a multi-agent architecture *after* the demo works: how it fails silently, how you measure whether it is actually working, and how you operate it once it is in front of users.

Companion artifact for the Deep Dive talk *Beyond the Demo: Deploying Multi-Agent Systems at Scale*.

## What this repo demonstrates

- A realistic multi-agent workflow: a support-ticket assistant that classifies, retrieves, drafts, checks policy, and escalates.
- The failure modes that demos hide: wrong routing, plausible-but-useless answers, prompt injection, missing context, judge blind spots, and cost blowups.
- A real evaluation harness: offline evals, regression evals, and LLM-as-judge (including where the judge gets fooled).
- Observability: per-step traces you can open and read, so "the dashboard is green" and "the system did the right thing" stop being the same claim.

## Architecture

```
Incoming ticket
      |
      v
  Router / Planner Agent
      |
      v
  Specialist Agents
      |-- Retrieval Agent
      |-- Solver Agent
      |-- Guardrail Agent
      |-- Critic / Evaluator
      |
      v
  Finalizer Agent  -> resolve or escalate
```

See [docs/architecture.md](docs/architecture.md) for detail.

## Quickstart

```bash
make setup      # installs deps, creates .env
make run-demo   # runs one ticket end to end (works offline, no API key)
```

`run-demo` uses a mock LLM by default so it runs with no key and no network. To use a real provider, set `MOCK_MODE=0` and your provider/model/key in `.env`.

## Run the agent on other scenarios

```bash
python -m app.main examples/ambiguous_ticket.json   # watch it misroute
python -m app.main examples/malicious_prompt_injection.json  # watch the guardrail catch it
```

## Run the evals

```bash
make eval
```

Prints a summary and writes a full report to `evals/reports/`. Runs against a fixed dataset in mock mode, so results are reproducible.

## Inspect traces

```bash
make traces
```

Open `traces/examples/sample_bad_route_trace.json`. Every metric passed and the answer looked fine, but the trace shows the router chose the wrong specialist. That gap is the whole point.

## Known failure modes

| Failure | What it demonstrates | Reproduce with |
|---|---|---|
| Wrong route | Nondeterministic routing | `examples/ambiguous_ticket.json` |
| Plausible but useless answer | Quality degradation | `examples/missing_context.json` |
| Prompt injection | Guardrail failure | `examples/malicious_prompt_injection.json` |
| Missing context | Retrieval failure | `examples/missing_context.json` |
| Conflicting docs | Evaluation difficulty | `examples/conflicting_documents.json` |
| Judge fooled | LLM-as-judge weakness | `examples/bad_llm_judge_case.json` |
| Too many agent calls | Cost / latency blowup | `examples/expensive_route.json` |

See [docs/failure_modes.md](docs/failure_modes.md).

## Production lessons

The short version lives in [docs/production_checklist.md](docs/production_checklist.md). The long version is the talk.

## Further reading

The practices here are documented across the major vendors and standards bodies, not invented for this repo. [docs/references.md](docs/references.md) maps each concept in the code to authoritative sources, spanning LangChain/LangGraph, OpenAI, Anthropic, Google, IBM, OWASP, and OpenTelemetry. A few to start with:

- Anthropic, [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) and [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- OpenAI, [Graders](https://developers.openai.com/api/docs/guides/graders) (see "grader hacking", the LLM-as-judge failure this repo reproduces)
- Anthropic, [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) and LangChain, [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
- OWASP, [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- OpenTelemetry, [GenAI Semantic Conventions](https://github.com/open-telemetry/semantic-conventions-genai)

## Talk mapping

| Talk segment | Code |
|---|---|
| Architecture for scale | `agents/`, `app/main.py` |
| The part nobody shows: evaluation | `evals/` |
| Operating it | `traces/`, `docs/production_checklist.md` |

## License

MIT. All data, docs, and policies in this repo are invented for illustration.
