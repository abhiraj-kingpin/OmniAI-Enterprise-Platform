"""Anthropic Claude adapter for the AI service layer.

Translates the normalized types in app/providers/types.py to and from the
Anthropic SDK's wire format. Nothing outside this file (and factory.py,
which constructs it) should import `anthropic` directly.
"""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

import anthropic

from app.providers.base import AIProvider, ToolExecutor
from app.providers.exceptions import ProviderUnavailableError
from app.providers.types import AIMessage, AIResponse, ImagePart, TextPart, ToolCall, ToolDefinition
from app.schemas import StreamChunk

DEFAULT_SYSTEM = "You are a helpful, concise AI assistant."
MAX_TOOL_ROUNDS = 5


def _content_to_anthropic(content: str | list[TextPart | ImagePart]) -> Any:
    if isinstance(content, str):
        return content
    blocks: list[dict[str, Any]] = []
    for part in content:
        if isinstance(part, TextPart):
            blocks.append({"type": "text", "text": part.text})
        else:
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": part.media_type,
                        "data": _b64(part.data),
                    },
                }
            )
    return blocks


def _b64(data: bytes) -> str:
    import base64

    return base64.standard_b64encode(data).decode("ascii")


def _message_to_anthropic(msg: AIMessage) -> dict[str, Any]:
    if msg.tool_results:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": r.tool_call_id,
                    "content": r.content,
                    "is_error": r.is_error,
                }
                for r in msg.tool_results
            ],
        }

    content = _content_to_anthropic(msg.content)
    if msg.tool_calls:
        blocks = content if isinstance(content, list) else ([{"type": "text", "text": content}] if content else [])
        blocks += [{"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input} for tc in msg.tool_calls]
        return {"role": msg.role, "content": blocks}

    return {"role": msg.role, "content": content}


def _tools_to_anthropic(tools: list[ToolDefinition] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in tools]


@lru_cache(maxsize=1)
def _client() -> anthropic.AsyncAnthropic:
    # Constructed lazily and cached — once per process, on first use — so
    # the SDK's env-var credential resolution always sees a fully loaded
    # .env (see app/core/env.py), and every AnthropicProvider instance
    # shares one connection pool.
    try:
        return anthropic.AsyncAnthropic()
    except Exception as exc:
        raise ProviderUnavailableError(f"Anthropic client could not be constructed: {exc}") from exc


class AnthropicProvider(AIProvider):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or "claude-opus-5"

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict | None = None,
    ) -> AIResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system or DEFAULT_SYSTEM,
            "messages": [_message_to_anthropic(m) for m in messages],
        }
        anthropic_tools = _tools_to_anthropic(tools)
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools
        if response_schema:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": response_schema}}

        try:
            response = await _client().messages.create(**kwargs)
        except anthropic.APIError as exc:
            raise ProviderUnavailableError(f"Anthropic request failed: {exc}") from exc

        text = "".join(b.text for b in response.content if b.type == "text")
        calls = [
            ToolCall(id=b.id, name=b.name, input=b.input) for b in response.content if b.type == "tool_use"
        ]
        stop_reason = "tool_use" if response.stop_reason == "tool_use" else "refusal" if response.stop_reason == "refusal" else "max_tokens" if response.stop_reason == "max_tokens" else "end_turn"
        return AIResponse(
            text=text,
            tool_calls=calls,
            stop_reason=stop_reason,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        )

    async def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        execute_tool: ToolExecutor | None = None,
    ) -> AsyncIterator[StreamChunk]:
        conversation: list[dict[str, Any]] = [_message_to_anthropic(m) for m in messages]
        anthropic_tools = _tools_to_anthropic(tools)

        for _ in range(MAX_TOOL_ROUNDS):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system or DEFAULT_SYSTEM,
                "messages": conversation,
            }
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools

            try:
                async with _client().messages.stream(**kwargs) as stream:
                    async for text in stream.text_stream:
                        yield StreamChunk(type="text", content=text)
                    final = await stream.get_final_message()
            except anthropic.APIError as exc:
                yield StreamChunk(type="error", message=f"Anthropic request failed: {exc}")
                return

            if final.stop_reason == "refusal":
                yield StreamChunk(type="error", message="The model declined to respond to this request.")
                return

            conversation.append({"role": "assistant", "content": final.content})
            yield StreamChunk(
                type="usage",
                usage={"input_tokens": final.usage.input_tokens, "output_tokens": final.usage.output_tokens},
            )

            if final.stop_reason != "tool_use":
                return

            tool_results: list[dict[str, Any]] = []
            for block in final.content:
                if block.type != "tool_use":
                    continue
                yield StreamChunk(type="tool_use", name=block.name, input=block.input)
                output = execute_tool(block.name, block.input) if execute_tool else "No tool executor configured."
                yield StreamChunk(type="tool_result", name=block.name, content=output)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            conversation.append({"role": "user", "content": tool_results})

        yield StreamChunk(type="error", message="Stopped after too many tool round-trips.")

    async def count_tokens(self, messages: list[AIMessage], *, system: str | None = None) -> int:
        try:
            result = await _client().messages.count_tokens(
                model=self.model,
                system=system or DEFAULT_SYSTEM,
                messages=[_message_to_anthropic(m) for m in messages],
            )
        except anthropic.APIError as exc:
            raise ProviderUnavailableError(f"Anthropic token count failed: {exc}") from exc
        return result.input_tokens
