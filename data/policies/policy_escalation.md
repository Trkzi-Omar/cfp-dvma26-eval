# Support policy: escalation to a human

Escalate to a human agent, and do not auto-resolve, when any of these hold:

- The guardrail flags a prompt-injection attempt or a data leak.
- The response quality stays below the quality bar after the retry budget.
- Documentation and policy conflict and the correct answer is not clear.
- The request involves account deletion, legal, or a security incident.
- The customer is on the Enterprise tier and explicitly asks for a human.
