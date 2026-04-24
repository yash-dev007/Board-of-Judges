from __future__ import annotations

from bojudges.providers.base import Provider


def get_provider(name: str, **kwargs) -> Provider:
    """Instantiate a provider by short name. Lazy-imports optional deps."""
    name = name.lower()
    if name == "mock":
        from bojudges.providers.mock import MockProvider
        return MockProvider(**kwargs)
    if name == "anthropic":
        from bojudges.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(**kwargs)
    if name in ("google", "gemini"):
        from bojudges.providers.google_provider import GoogleProvider
        return GoogleProvider(**kwargs)
    if name in ("openai", "codex"):
        from bojudges.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(**kwargs)
    raise ValueError(f"Unknown provider: {name!r}. Known: mock, anthropic, google, openai")


def resolve_model_provider(model_id: str) -> str:
    """Heuristic: map a model ID to a provider name."""
    m = model_id.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini"):
        return "google"
    if m.startswith("gpt") or m.startswith("o1") or m.startswith("o3") or "codex" in m:
        return "openai"
    if m == "mock":
        return "mock"
    raise ValueError(f"Cannot infer provider from model_id={model_id!r}")
