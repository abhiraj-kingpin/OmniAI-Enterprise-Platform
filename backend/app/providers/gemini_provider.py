"""Google Gemini adapter for the AI service layer.

Translates the normalized types in app/providers/types.py to and from the
`google-genai` SDK's wire format. Nothing outside this file (and factory.py,
which constructs it) should import `google.genai` directly.

Not live-verified against the real Gemini API in this environment (no
Gemini API key configured here) — written against the documented SDK
shape and exercised only via this module's own type/flow logic. Treat a
first real run as the actual verification.
"""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from app.providers.base import AIProvider, ToolExecutor
from app.providers.exceptions import ProviderUnavailableError
from app.providers.types import AIMessage, AIResponse, ImagePart, TextPart, ToolCall, ToolDefinition
from app.schemas import StreamChunk

DEFAULT_SYSTEM = "You are a helpful, concise AI assistant."
MAX_TOOL_ROUNDS = 5


def _content_to_parts(content: str | list[TextPart | ImagePart]) -> list[types.Part]:
    if isinstance(content, str):
        return [types.Part(text=content)] if content else []
    parts: list[types.Part] = []
    for part in content:
        if isinstance(part, TextPart):
            parts.append(types.Part(text=part.text))
        else:
            parts.append(types.Part.from_bytes(data=part.data, mime_type=part.media_type))
    return parts


def _message_to_content(msg: AIMessage) -> types.Content:
    # Gemini has no per-call id — function_call/function_response pairs
    # correlate by function name alone. `ToolCall.id` is set to the
    # function's own name below (in complete()/stream()) specifically so
    # that convention round-trips correctly here; it isn't a real id for
    # this provider the way it is for Anthropic/OpenAI.
    if msg.tool_results:
        return types.Content(
            role="user",
            parts=[
                types.Part(function_response=types.FunctionResponse(name=r.tool_call_id, response={"result": r.content}))
                for r in msg.tool_results
            ],
        )

    role = "model" if msg.role == "assistant" else "user"
    parts = _content_to_parts(msg.content)
    if msg.tool_calls:
        parts += [types.Part(function_call=types.FunctionCall(name=tc.id, args=tc.input)) for tc in msg.tool_calls]
    return types.Content(role=role, parts=parts)


def _tools_to_gemini(tools: list[ToolDefinition] | None) -> list[types.Tool] | None:
    if not tools:
        return None
    declarations = [
        types.FunctionDeclaration(name=t.name, description=t.description, parameters=t.input_schema) for t in tools
    ]
    return [types.Tool(function_declarations=declarations)]


def _finish_reason_to_stop_reason(reason: Any) -> str:
    name = getattr(reason, "name", str(reason))
    if name == "MAX_TOKENS":
        return "max_tokens"
    if name in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST"):
        return "refusal"
    return "end_turn"


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    from app.config import settings

    if not settings.gemini_api_key:
        raise ProviderUnavailableError("GEMINI_API_KEY is not set.")
    try:
        return genai.Client(api_key=settings.gemini_api_key)
    except Exception as exc:
        raise ProviderUnavailableError(f"Gemini client could not be constructed: {exc}") from exc


class GeminiProvider(AIProvider):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or "gemini-2.5-flash"

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict | None = None,
    ) -> AIResponse:
        config = types.GenerateContentConfig(
            system_instruction=system or DEFAULT_SYSTEM,
            max_output_tokens=max_tokens,
            tools=_tools_to_gemini(tools),
            response_mime_type="application/json" if response_schema else None,
            response_schema=response_schema,
        )
        try:
            response = await _client().aio.models.generate_content(
                model=self.model, contents=[_message_to_content(m) for m in messages], config=config
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini request failed: {exc}") from exc

        text = response.text or ""
        calls = [
            ToolCall(id=fc.name, name=fc.name, input=dict(fc.args or {})) for fc in (response.function_calls or [])
        ]
        candidate = response.candidates[0] if response.candidates else None
        stop_reason = "tool_use" if calls else _finish_reason_to_stop_reason(candidate.finish_reason if candidate else None)
        usage = response.usage_metadata
        return AIResponse(
            text=text,
            tool_calls=calls,
            stop_reason=stop_reason,
            usage={
                "input_tokens": usage.prompt_token_count or 0 if usage else 0,
                "output_tokens": usage.candidates_token_count or 0 if usage else 0,
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
        conversation = [_message_to_content(m) for m in messages]
        config = types.GenerateContentConfig(
            system_instruction=system or DEFAULT_SYSTEM,
            max_output_tokens=max_tokens,
            tools=_tools_to_gemini(tools),
        )

        for _ in range(MAX_TOOL_ROUNDS):
            text_parts: list[str] = []
            calls: list[types.FunctionCall] = []
            usage: dict[str, int] = {}

            try:
                stream = await _client().aio.models.generate_content_stream(
                    model=self.model, contents=conversation, config=config
                )
                async for chunk in stream:
                    if chunk.text:
                        text_parts.append(chunk.text)
                        yield StreamChunk(type="text", content=chunk.text)
                    if chunk.function_calls:
                        calls.extend(chunk.function_calls)
                    if chunk.usage_metadata:
                        usage = {
                            "input_tokens": chunk.usage_metadata.prompt_token_count or 0,
                            "output_tokens": chunk.usage_metadata.candidates_token_count or 0,
                        }
            except Exception as exc:
                yield StreamChunk(type="error", message=f"Gemini request failed: {exc}")
                return

            if usage:
                yield StreamChunk(type="usage", usage=usage)

            assistant_text = "".join(text_parts)
            model_parts: list[types.Part] = ([types.Part(text=assistant_text)] if assistant_text else []) + [
                types.Part(function_call=fc) for fc in calls
            ]
            conversation.append(types.Content(role="model", parts=model_parts))

            if not calls:
                return

            response_parts: list[types.Part] = []
            for call in calls:
                tool_input = dict(call.args or {})
                yield StreamChunk(type="tool_use", name=call.name, input=tool_input)
                output = execute_tool(call.name, tool_input) if execute_tool else "No tool executor configured."
                yield StreamChunk(type="tool_result", name=call.name, content=output)
                response_parts.append(
                    types.Part(function_response=types.FunctionResponse(name=call.name, response={"result": output}))
                )
            conversation.append(types.Content(role="user", parts=response_parts))

        yield StreamChunk(type="error", message="Stopped after too many tool round-trips.")

    async def count_tokens(self, messages: list[AIMessage], *, system: str | None = None) -> int:
        try:
            result = await _client().aio.models.count_tokens(
                model=self.model, contents=[_message_to_content(m) for m in messages]
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini token count failed: {exc}") from exc
        return result.total_tokens or 0
