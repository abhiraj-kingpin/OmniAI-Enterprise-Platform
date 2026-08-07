"""OpenAI adapter for the AI service layer.

Translates the normalized types in app/providers/types.py to and from the
OpenAI SDK's wire format. Nothing outside this file (and factory.py, which
constructs it) should import `openai` directly.
"""

import base64
import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

import openai

from app.providers.base import AIProvider, ToolExecutor
from app.providers.exceptions import ProviderUnavailableError
from app.providers.types import AIMessage, AIResponse, ImagePart, TextPart, ToolCall, ToolDefinition
from app.schemas import StreamChunk

DEFAULT_SYSTEM = "You are a helpful, concise AI assistant."
MAX_TOOL_ROUNDS = 5


def _content_to_openai(content: str | list[TextPart | ImagePart]) -> Any:
    if isinstance(content, str):
        return content
    parts: list[dict[str, Any]] = []
    for part in content:
        if isinstance(part, TextPart):
            parts.append({"type": "text", "text": part.text})
        else:
            data = base64.standard_b64encode(part.data).decode("ascii")
            parts.append({"type": "image_url", "image_url": {"url": f"data:{part.media_type};base64,{data}"}})
    return parts


def _messages_to_openai(messages: list[AIMessage], system: str) -> list[dict[str, Any]]:
    """Flattens our normalized messages into OpenAI's list — unlike
    Anthropic's single tool_result-bearing user turn, OpenAI expects one
    `role: "tool"` message per tool result, so a single AIMessage can expand
    into several OpenAI messages."""
    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for msg in messages:
        if msg.tool_results:
            for r in msg.tool_results:
                out.append({"role": "tool", "tool_call_id": r.tool_call_id, "content": r.content})
            continue
        if msg.tool_calls:
            out.append(
                {
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.input)},
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            continue
        out.append({"role": msg.role, "content": _content_to_openai(msg.content)})
    return out


def _tools_to_openai(tools: list[ToolDefinition] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
        for t in tools
    ]


def _finish_reason_to_stop_reason(reason: str | None) -> str:
    return {"tool_calls": "tool_use", "length": "max_tokens", "content_filter": "refusal"}.get(reason or "", "end_turn")


@lru_cache(maxsize=4)
def _client(base_url: str | None, api_key: str | None) -> openai.AsyncOpenAI:
    # Parameterized (and cached per distinct base_url/api_key pair) so
    # OllamaProvider can reuse this whole file against a local,
    # OpenAI-compatible endpoint instead of duplicating every translation
    # helper below — Ollama's /v1 API is intentionally wire-compatible.
    try:
        return openai.AsyncOpenAI(base_url=base_url, api_key=api_key)
    except Exception as exc:
        raise ProviderUnavailableError(f"OpenAI-compatible client could not be constructed: {exc}") from exc


class OpenAIProvider(AIProvider):
    #: override in a subclass to point at an OpenAI-compatible endpoint
    #: other than api.openai.com (see OllamaProvider)
    base_url: str | None = None
    api_key: str | None = None

    def __init__(self, model: str | None = None) -> None:
        self.model = model or "gpt-4o"

    def _client(self) -> openai.AsyncOpenAI:
        return _client(self.base_url, self.api_key)

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
            "messages": _messages_to_openai(messages, system or DEFAULT_SYSTEM),
        }
        openai_tools = _tools_to_openai(tools)
        if openai_tools:
            kwargs["tools"] = openai_tools
        if response_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": response_schema, "strict": True},
            }

        try:
            response = await self._client().chat.completions.create(**kwargs)
        except openai.APIError as exc:
            raise ProviderUnavailableError(f"OpenAI request failed: {exc}") from exc

        choice = response.choices[0]
        calls = [
            ToolCall(id=tc.id, name=tc.function.name, input=json.loads(tc.function.arguments or "{}"))
            for tc in (choice.message.tool_calls or [])
        ]
        return AIResponse(
            text=choice.message.content or "",
            tool_calls=calls,
            stop_reason=_finish_reason_to_stop_reason(choice.finish_reason),
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
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
        conversation = _messages_to_openai(messages, system or DEFAULT_SYSTEM)
        openai_tools = _tools_to_openai(tools)

        for _ in range(MAX_TOOL_ROUNDS):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": conversation,
                "stream": True,
                "stream_options": {"include_usage": True},
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            text_parts: list[str] = []
            # tool_calls accumulate incrementally across chunks, keyed by index.
            pending_calls: dict[int, dict[str, Any]] = {}
            finish_reason: str | None = None
            usage: dict[str, int] = {}

            try:
                stream = await self._client().chat.completions.create(**kwargs)
                async for chunk in stream:
                    if chunk.usage:
                        usage = {
                            "input_tokens": chunk.usage.prompt_tokens,
                            "output_tokens": chunk.usage.completion_tokens,
                        }
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
                    delta = choice.delta
                    if delta.content:
                        text_parts.append(delta.content)
                        yield StreamChunk(type="text", content=delta.content)
                    for tc_delta in delta.tool_calls or []:
                        entry = pending_calls.setdefault(
                            tc_delta.index, {"id": "", "name": "", "arguments": ""}
                        )
                        if tc_delta.id:
                            entry["id"] = tc_delta.id
                        if tc_delta.function and tc_delta.function.name:
                            entry["name"] = tc_delta.function.name
                        if tc_delta.function and tc_delta.function.arguments:
                            entry["arguments"] += tc_delta.function.arguments
            except openai.APIError as exc:
                yield StreamChunk(type="error", message=f"OpenAI request failed: {exc}")
                return

            if usage:
                yield StreamChunk(type="usage", usage=usage)

            assistant_text = "".join(text_parts)
            if not pending_calls:
                conversation.append({"role": "assistant", "content": assistant_text})
                if finish_reason == "content_filter":
                    yield StreamChunk(type="error", message="The model declined to respond to this request.")
                return

            tool_calls_payload = [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
                for c in pending_calls.values()
            ]
            conversation.append(
                {"role": "assistant", "content": assistant_text or None, "tool_calls": tool_calls_payload}
            )

            for call in pending_calls.values():
                tool_input = json.loads(call["arguments"] or "{}")
                yield StreamChunk(type="tool_use", name=call["name"], input=tool_input)
                output = execute_tool(call["name"], tool_input) if execute_tool else "No tool executor configured."
                yield StreamChunk(type="tool_result", name=call["name"], content=output)
                conversation.append({"role": "tool", "tool_call_id": call["id"], "content": output})

        yield StreamChunk(type="error", message="Stopped after too many tool round-trips.")

    async def count_tokens(self, messages: list[AIMessage], *, system: str | None = None) -> int:
        # OpenAI has no live token-counting endpoint; tiktoken gives an
        # accurate-enough local estimate for chat-shaped input. Falls back to
        # a rough chars/4 heuristic if the model isn't in tiktoken's registry
        # yet (e.g. a very new model name) rather than failing the request.
        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                encoding = tiktoken.get_encoding("o200k_base")
            text = (system or DEFAULT_SYSTEM) + "".join(
                m.content if isinstance(m.content, str) else "".join(p.text for p in m.content if isinstance(p, TextPart))
                for m in messages
            )
            return len(encoding.encode(text))
        except ImportError:
            text = (system or DEFAULT_SYSTEM) + "".join(str(m.content) for m in messages)
            return max(1, len(text) // 4)
