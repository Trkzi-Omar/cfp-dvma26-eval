"""Central configuration.

One place that reads the environment and exposes typed settings to the rest of
the system. The most important switch here is MOCK_MODE: when it is on (the
default), no network call is ever made and every LLM response comes from
llm/mock.py. That is what lets `make run-demo` and `make eval` run offline, with
no API key, and produce reproducible numbers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so we stay dependency-free. Values already present in
    the real environment win; .env only fills in what is missing."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(_ENV_PATH)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Per-token prices in USD. These are illustrative and only used to compute the
# estimated cost shown in traces and eval reports. The mock model is priced so
# that the "expensive_route" scenario visibly costs more than the happy path.
PRICES: dict[str, dict[str, float]] = {
    "mock-1": {"input": 0.0000005, "output": 0.0000015},
    "claude-sonnet-5": {"input": 0.000003, "output": 0.000015},
    "gpt-generic": {"input": 0.000005, "output": 0.000015},
}


@dataclass(frozen=True)
class Config:
    mock_mode: bool = True
    provider: str = "mock"
    model: str = "mock-1"
    api_key: str = ""

    # Behaviour thresholds. Kept here so the talk can point at a single place
    # where "how the system decides" lives.
    critic_pass_threshold: float = 0.70
    max_retries: int = 2

    prices: dict[str, dict[str, float]] = field(default_factory=lambda: dict(PRICES))

    def price(self, kind: str) -> float:
        table = self.prices.get(self.model, self.prices["mock-1"])
        return table[kind]


def load_config() -> Config:
    """Build a Config from environment variables (see .env.example)."""
    mock_mode = _as_bool(os.getenv("MOCK_MODE"), default=True)
    provider = os.getenv("LLM_PROVIDER", "mock" if mock_mode else "anthropic")
    model = os.getenv("LLM_MODEL", "mock-1" if mock_mode else "claude-sonnet-5")
    api_key = os.getenv("LLM_API_KEY", "")

    return Config(
        mock_mode=mock_mode,
        provider=provider,
        model=model,
        api_key=api_key,
    )


CONFIG = load_config()
