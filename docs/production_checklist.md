# Production checklist

An opinionated list to run through before putting a multi-agent system in front of
users. It is short on purpose. Each item maps to something in this repo so you can
see what "done" looks like.

## Evaluation

- [ ] **Evals run in CI, and a regression gate blocks the merge.** Not a notebook
      someone runs by hand. See `evals/run_evals.py` and the `--baseline`
      comparison. A prompt, model, or agent change that moves a metric should fail
      the build, not surprise you in production.
- [ ] **You measure more than one thing.** Route accuracy, groundedness, policy
      compliance, and cost each catch a different failure, and the two most
      trusted in-loop signals (an in-loop critic and an LLM-as-judge) catch the
      least. No single number is a green light. See `evals/metrics/`.
- [ ] **Your LLM-as-judge is validated against ground truth.** A judge you have
      not tried to fool is a judge that is fooling you. Keep a set of known
      hard cases (`examples/bad_llm_judge_case.json`) and track how often the
      judge disagrees with the golden answers.
- [ ] **The eval dataset is fixed and reproducible.** Same input, same numbers.
      If your evals are nondeterministic you cannot tell a real regression from
      noise. This repo runs evals in mock mode for exactly this reason.

## Observability

- [ ] **Every request emits a full trace: per-step inputs, outputs, latency,
      tokens, and cost.** See `agents/base.py` (`TraceStep`) and the committed
      examples in `traces/examples/`. "The dashboard is green" and "the system
      did the right thing" must be separately checkable.
- [ ] **You can open a single request and read what happened.** When something
      looks wrong, the trace should show which agent decided what, not just an
      aggregate.

## Guardrails and safety

- [ ] **Guardrails are defence in depth, not model-only.** A deterministic layer
      plus a policy layer, either of which can block. See `agents/guardrail.py`.
      The ticket body is untrusted input, never instructions.
- [ ] **There is a human escalation path, and it is the default when unsure.**
      Flagged content, quality below the bar after retries, and doc/policy
      conflicts all escalate rather than auto-resolve. See `agents/finalizer.py`
      and `data/policies/policy_escalation.md`.

## Cost and reliability

- [ ] **Every request has a cost and retry budget, and you alert when it is
      exceeded.** Retries multiply every downstream call. See the budget check in
      `evals/metrics/cost_latency.py` and the `expensive_route` scenario.
- [ ] **Failures degrade to a human, not to a confident wrong answer.** The worst
      outcome is not an error; it is a plausible answer to the wrong problem that
      no one notices.

## Change management

- [ ] **Prompt and model changes go through the same regression gate as code.**
      A prompt is code. Treat a prompt edit like a deploy: run the evals, compare
      to baseline, review the delta.
