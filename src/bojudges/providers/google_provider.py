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
    "gemini-2.5-pro": (1.25, 5.0),
    "gemini-2.5-flash": (0.075, 0.3),
    "gemini-2.0-flash": (0.075, 0.3),
}


class GoogleProvider(Provider):
    """Google Gemini provider. Requires `google-genai` package."""

    name = "google"

    def __init__(self, api_key: str | None = None) -> None:
        try:
            from google import genai
        except ImportError as e:
            raise ImportError(
                "google-genai not installed. `pip install google-genai`"
            ) from e

        key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY / GEMINI_API_KEY not set")
        self._client = genai.Client(api_key=key)

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
        from google.genai import types as genai_types

        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        contents: list[Any] = []
        for m in messages:
            if m.role == "system":
                continue
            role = "user" if m.role == "user" else "model"
            contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=m.content)]))

        config = genai_types.GenerateContentConfig(
            system_instruction=system_text or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
            seed=seed,
            tools=self._to_genai_tools(tools),
            tool_config=self._to_genai_tool_config(tool_choice),
        )

        resp = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        text = getattr(resp, "text", None)
        tool_calls: list[ToolCall] = []
        try:
            for cand in resp.candidates or []:
                for part in cand.content.parts or []:
                    fn = getattr(part, "function_call", None)
                    if fn:
                        tool_calls.append(
                            ToolCall(id="", name=fn.name, input=dict(fn.args or {}))
                        )
        except Exception:
            pass

        usage = getattr(resp, "usage_metadata", None)
        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason="",
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0 if usage else 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0 if usage else 0,
            cache_read_tokens=getattr(usage, "cached_content_token_count", 0) or 0 if usage else 0,
            model_id=model,
        )

    def cost_usd(self, response: LLMResponse) -> float:
        in_rate, out_rate = _PRICES_PER_MTOK.get(response.model_id, (1.0, 3.0))
        cached = response.cache_read_tokens
        billable_in = max(response.input_tokens - cached, 0)
        return (
            billable_in * in_rate / 1_000_000
            + response.output_tokens * out_rate / 1_000_000
            + cached * in_rate * 0.25 / 1_000_000
        )

    @staticmethod
    def _to_genai_tools(tools: list[ToolDefinition] | None):
        if not tools:
            return None
        from google.genai import types as genai_types

        decls = [
            genai_types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters=t.input_schema,
            )
            for t in tools
        ]
        return [genai_types.Tool(function_declarations=decls)]

    @staticmethod
    def _to_genai_tool_config(choice: str | dict[str, Any] | None):
        if choice is None:
            return None
        from google.genai import types as genai_types

        if choice == "any":
            return genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(mode="ANY")
            )
        if isinstance(choice, str) and choice != "auto":
            return genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode="ANY", allowed_function_names=[choice]
                )
            )
        return genai_types.ToolConfig(
            function_calling_config=genai_types.FunctionCallingConfig(mode="AUTO")
        )
