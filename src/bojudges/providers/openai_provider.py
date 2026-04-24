from __future__ import annotations

import json
import os
import uuid
from typing import Any

from bojudges.providers.base import (
    LLMResponse,
    Message,
    Provider,
    ToolCall,
    ToolDefinition,
)

_PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "o1-mini": (3.0, 12.0),
    "o3-mini": (1.1, 4.4),
}


class OpenAIProvider(Provider):
    """OpenAI / Codex-backed provider. Requires `openai` package."""

    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("openai SDK not installed. `pip install openai`") from e

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")

        kwargs: dict[str, Any] = {"api_key": key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)

    def supports_prompt_cache(self) -> bool:
        return True

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
        chat_messages: list[dict[str, Any]] = []
        for m in messages:
            chat_messages.append({"role": m.role, "content": m.content})

        req: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if seed is not None:
            req["seed"] = seed
        if tools:
            req["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema,
                    },
                }
                for t in tools
            ]
        if tool_choice is not None:
            req["tool_choice"] = self._build_tool_choice(tool_choice)

        raw = self._client.chat.completions.create(**req)
        choice = raw.choices[0]
        msg = choice.message

        text = msg.content
        tool_calls: list[ToolCall] = []
        for tc in getattr(msg, "tool_calls", None) or []:
            try:
                input_obj = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                input_obj = {}
            tool_calls.append(
                ToolCall(
                    id=getattr(tc, "id", "") or str(uuid.uuid4()),
                    name=tc.function.name,
                    input=input_obj,
                )
            )

        usage = raw.usage
        cached = 0
        try:
            cached = getattr(usage, "prompt_tokens_details", None).cached_tokens or 0
        except (AttributeError, TypeError):
            cached = 0

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason=str(choice.finish_reason or ""),
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cache_read_tokens=cached,
            model_id=raw.model or model,
        )

    def cost_usd(self, response: LLMResponse) -> float:
        in_rate, out_rate = _PRICES_PER_MTOK.get(response.model_id, (2.0, 8.0))
        cached = response.cache_read_tokens
        billable_in = max(response.input_tokens - cached, 0)
        return (
            billable_in * in_rate / 1_000_000
            + response.output_tokens * out_rate / 1_000_000
            + cached * in_rate * 0.5 / 1_000_000
        )

    @staticmethod
    def _build_tool_choice(choice: str | dict[str, Any]) -> Any:
        if isinstance(choice, dict):
            return choice
        if choice in ("auto", "required", "none"):
            return choice
        return {"type": "function", "function": {"name": choice}}
