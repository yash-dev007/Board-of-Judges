from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str
    cache: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_create_tokens: int = 0
    model_id: str = ""
    raw: dict[str, Any] | None = None


class Provider(ABC):
    """Minimal contract every LLM provider must implement.

    Designed to be thin. Adapters implement prompt-caching, tool-use, and
    usage accounting using their native SDK; the rest of bojudges never talks
    to a vendor SDK directly.
    """

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        tools: list[ToolDefinition] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    def cost_usd(self, response: LLMResponse) -> float: ...

    def supports_prompt_cache(self) -> bool:
        return False
