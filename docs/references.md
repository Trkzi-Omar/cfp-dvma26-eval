# References and further reading

The ideas in this repo are not novel to it. Routing, retrieval, guardrails,
LLM-as-judge, groundedness, tracing, and per-request cost budgets are all
documented practice at the major vendors and standards bodies. This page collects
the authoritative sources behind each concept so you can go deeper than the talk.

This repo stays framework-agnostic on purpose (see the note at the bottom). The
links below span LangChain/LangGraph, OpenAI, Anthropic, Google, IBM, OWASP, and
OpenTelemetry precisely so the concepts read as portable, not tied to one stack.
All links were checked live; where a vendor consolidated or moved docs, the final
resolved URL is used.

## How this maps to the repo

| Concept in this repo | Where in the code | Start here |
|---|---|---|
| Multi-agent architecture, handoff | `agents/`, `docs/architecture.md` | Anthropic, "Building Effective AI Agents" |
| Offline / regression evals | `evals/`, `evals/run_evals.py` | Anthropic, "Define success criteria and build evaluations" |
| LLM-as-judge (and its blind spots) | `evals/judges/`, `prompts/judge.md` | OpenAI, "Graders" (see grader hacking) |
| Per-step traces | `agents/base.py`, `traces/` | OpenTelemetry GenAI semantic conventions |
| Guardrails, prompt injection | `agents/guardrail.py` | OWASP, "LLM01:2025 Prompt Injection" |
| Cost / latency budget | `evals/metrics/cost_latency.py` | LangSmith observability |

## Agent architecture and multi-agent systems

- [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) (Anthropic). Workflows versus agents, and five composable patterns. The router and specialist split in `agents/` follows this shape.
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic). An orchestrator-worker multi-agent system in production, including where it fails and what it costs.
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) (OpenAI). Agents, handoffs, guardrails, and tracing as first-class primitives.
- [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) (LangChain / LangGraph). Subagents, handoffs, and routing between agents.
- [Workflows: multi-agent, multi-node applications](https://adk.dev/workflows/) (Google Agent Development Kit). Multi-agent orchestration patterns.
- [IBM watsonx Orchestrate Agent Development Kit](https://developer.watson-orchestrate.ibm.com/) (IBM). Building and orchestrating agents on watsonx.

## Evaluation

- [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) (Anthropic). How to design strong empirical evals: success criteria, eval sets, and grading. This is the backbone idea behind `evals/`.
- [Working with evals](https://developers.openai.com/api/docs/guides/evals) (OpenAI). Building and running evals to test and improve model outputs.
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) (LangChain). Offline and online evaluation concepts, datasets, and regression testing, which is what `make eval --baseline` demonstrates in miniature.
- [Gen AI evaluation service overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview) (Google Vertex AI). Model-based and computation-based metrics for generative output.
- [Evaluating AI models](https://dataplatform.cloud.ibm.com/docs/content/wsj/model/getting-started.html?context=wx) (IBM watsonx.governance). Evaluating and monitoring generative models in production.

## LLM-as-judge

- [How to define an LLM-as-a-judge evaluator](https://docs.langchain.com/langsmith/llm-as-judge) (LangSmith). Configuring an LLM to grade another model's output.
- [Graders](https://developers.openai.com/api/docs/guides/graders) (OpenAI). Model-based graders and, importantly, "grader hacking": why a judge you have not stress-tested can be gamed. This is exactly the failure `evals/judges/llm_as_judge.py` reproduces.

## Observability and tracing

- [OpenTelemetry GenAI Semantic Conventions](https://github.com/open-telemetry/semantic-conventions-genai) (OpenTelemetry). The vendor-neutral spec for spans, metrics, and events across LLM, agent, and tool calls. The `TraceStep` fields in `agents/base.py` mirror this intent.
- [LangSmith Observability](https://docs.langchain.com/langsmith/observability) (LangChain). Tracing and production monitoring of LLM applications.
- [Tracing](https://openai.github.io/openai-agents-python/tracing/) (OpenAI Agents SDK). Built-in traces and spans for agent runs.

## Guardrails, prompt injection, and safety

- [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) (OWASP Gen AI Security Project). The canonical risk list for LLM apps.
- [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (OWASP). The number-one risk, and the one `examples/malicious_prompt_injection.json` and `agents/guardrail.py` are built around.
- [Safety best practices](https://developers.openai.com/api/docs/guides/safety-best-practices) (OpenAI). Moderation, red-teaming, human-in-the-loop, and input/output constraints.
- [Model Armor overview](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) (Google Cloud). Prompt-injection and jailbreak detection, and content filtering, as a platform guardrail layer.

## A note on staying framework-agnostic

Listing these does not make the repo a LangChain, OpenAI, or any-other-vendor
showcase, and it deliberately depends on none of them at runtime (the core runs on
the standard library alone). The point of citing across vendors is the opposite:
the evaluation and observability practices this repo argues for are convergent.
Different stacks name them differently, but they are the same practices, and they
are what separate a demo from a system you can operate.
