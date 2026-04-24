from __future__ import annotations

import os
from typing import Any

from bojudges.providers.base import (
    LLMResponse,
    Message,
    Provider,
    ToolCall,
    ToolDefinition,
)

_PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-4-7": (15.0, 75.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic SDK not installed. `pip install anthropic`"
            ) from e

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        kwargs: dict[str, Any] = {"api_key": key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = Anthropic(**kwargs)

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
        system_blocks = self._build_system_blocks(messages)
        chat_messages = self._build_chat_messages(messages)
        tool_defs = self._build_tool_defs(tools)

        req: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system_blocks:
            req["system"] = system_blocks
        if tool_defs:
            req["tools"] = tool_defs
        if tool_choice is not None:
            req["tool_choice"] = self._build_tool_choice(tool_choice)

        raw = self._client.messages.create(**req)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in raw.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=getattr(block, "id", ""),
                        name=getattr(block, "name", ""),
                        input=getattr(block, "input", {}) or {},
                    )
                )

        usage = getattr(raw, "usage", None)
        return LLMResponse(
            text="".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            stop_reason=str(getattr(raw, "stop_reason", "")),
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0 if usage else 0,
            cache_create_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0 if usage else 0,
            model_id=getattr(raw, "model", model),
            raw=None,
        )

    def cost_usd(self, response: LLMResponse) -> float:
        in_rate, out_rate = _PRICES_PER_MTOK.get(response.model_id, (3.0, 15.0))
        cached = response.cache_read_tokens
        billable_in = max(response.input_tokens - cached, 0)
        return (
            billable_in * in_rate / 1_000_000
            + response.output_tokens * out_rate / 1_000_000
            + cached * in_rate * 0.1 / 1_000_000
        )

    @staticmethod
    def _build_system_blocks(messages: list[Message]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for m in messages:
            if m.role != "system":
                continue
            block: dict[str, Any] = {"type": "text", "text": m.content}
            if m.cache:
                block["cache_control"] = {"type": "ephemeral"}
            blocks.append(block)
        return blocks

    @staticmethod
    def _build_chat_messages(messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                continue
            content: Any
            if m.cache:
                content = [
                    {
                        "type": "text",
                        "text": m.content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                content = m.content
            out.append({"role": m.role, "content": content})
        return out

    @staticmethod
    def _build_tool_defs(tools: list[ToolDefinition] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]

    @staticmethod
    def _build_tool_choice(choice: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(choice, dict):
            return choice
        if choice == "auto":
            return {"type": "auto"}
        if choice == "any":
            return {"type": "any"}
        return {"type": "tool", "name": choice}
