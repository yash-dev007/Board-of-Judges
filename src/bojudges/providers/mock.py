from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from bojudges.providers.base import (
    LLMResponse,
    Message,
    Provider,
    ToolCall,
    ToolDefinition,
)


@dataclass
class ScriptedResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 100
    output_tokens: int = 50
    stop_reason: str = "end_turn"


class MockProvider(Provider):
    """Deterministic, offline LLM for tests and eval-harness dry runs.

    Lookup order on every call:
      1. handler (callable) if set — fully custom
      2. responses_by_prefix: first matching prompt-hash prefix
      3. default_response

    Never calls the network. Tracks call count.
    """

    name = "mock"

    def __init__(
        self,
        default_response: ScriptedResponse | None = None,
        responses_by_prefix: dict[str, ScriptedResponse] | None = None,
        handler: Callable[[list[Message], str], ScriptedResponse] | None = None,
    ) -> None:
        self.default = default_response or ScriptedResponse(text="mock response")
        self.by_prefix = responses_by_prefix or {}
        self.handler = handler
        self.calls: list[tuple[list[Message], str]] = []

    @staticmethod
    def prompt_hash(messages: list[Message]) -> str:
        blob = "||".join(f"{m.role}:{m.content}" for m in messages)
        return hashlib.sha256(blob.encode()).hexdigest()

    def generate(
        self,
        messages: list[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        tools: list[ToolDefinition] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        self.calls.append((messages, model))

        if self.handler is not None:
            scripted = self.handler(messages, model)
        else:
            digest = self.prompt_hash(messages)
            scripted = self.default
            for prefix, resp in self.by_prefix.items():
                if digest.startswith(prefix):
                    scripted = resp
                    break

        return LLMResponse(
            text=scripted.text,
            tool_calls=list(scripted.tool_calls),
            stop_reason=scripted.stop_reason,
            input_tokens=scripted.input_tokens,
            output_tokens=scripted.output_tokens,
            model_id=model,
        )

    def cost_usd(self, response: LLMResponse) -> float:
        return 0.0

    def supports_prompt_cache(self) -> bool:
        return True
