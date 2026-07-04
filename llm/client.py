"""Provider-agnostic LLM interface.

This is the ONLY module in the repository that knows how to talk to an LLM
provider. Every agent and every eval goes through `call_llm`. Swapping providers,
adding retries, or changing how cost is measured happens here and nowhere else.

In mock mode (the default) this delegates to llm/mock.py and never touches the
network, which is what makes the demo and the evals reproducible and offline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import CONFIG, Config
from llm import mock


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    model: str
    latency_s: float

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def approx_tokens(text: str) -> int:
    """Rough token estimate. Deterministic on purpose so mock-mode cost and
    token counts are reproducible across runs."""
    return max(1, len(text) // 4)


def _estimate_cost(cfg: Config, prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        prompt_tokens * cfg.price("input") + completion_tokens * cfg.price("output"),
        6,
    )


def call_llm(
    messages: list[dict[str, str]],
    *,
    purpose: str = "general",
    cfg: Config | None = None,
) -> LLMResponse:
    """Call an LLM with a list of {role, content} messages.

    `purpose` names the calling agent (router, solver, guardrail, critic, judge).
    Real providers ignore it; the mock uses it to pick the right canned response,
    and it makes traces readable.
    """
    cfg = cfg or CONFIG
    prompt_text = "\n".join(m.get("content", "") for m in messages)
    prompt_tokens = approx_tokens(prompt_text)

    if cfg.mock_mode:
        text, latency_s = mock.respond(messages, purpose=purpose)
        completion_tokens = approx_tokens(text)
        return LLMResponse(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=_estimate_cost(cfg, prompt_tokens, completion_tokens),
            model=cfg.model,
            latency_s=latency_s,
        )

    # Real provider path. Kept deliberately thin and optional so the repo runs
    # with zero third-party dependencies in its default (mock) configuration.
    start = time.perf_counter()
    text = _call_real_provider(cfg, messages)
    latency_s = round(time.perf_counter() - start, 3)
    completion_tokens = approx_tokens(text)
    return LLMResponse(
        text=text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=_estimate_cost(cfg, prompt_tokens, completion_tokens),
        model=cfg.model,
        latency_s=latency_s,
    )


def _call_real_provider(cfg: Config, messages: list[dict[str, str]]) -> str:
    """Opt-in real provider call. Imports the SDK lazily so it is never required
    in mock mode. This is intentionally minimal: the point of the repo is the
    evaluation and observability around the model, not the provider wiring."""
    if not cfg.api_key:
        raise RuntimeError(
            "MOCK_MODE is off but no LLM_API_KEY is set. "
            "Set MOCK_MODE=1 to run offline, or provide credentials in .env."
        )

    if cfg.provider == "anthropic":
        try:
            import anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional path
            raise RuntimeError(
                "Install the 'anthropic' package to use the real provider, "
                "or run in mock mode (MOCK_MODE=1)."
            ) from exc
        client = anthropic.Anthropic(api_key=cfg.api_key)
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        user_msgs = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model=cfg.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": m["role"], "content": m["content"]} for m in user_msgs],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    raise RuntimeError(f"Unknown provider '{cfg.provider}'. Use mock mode or add wiring here.")
