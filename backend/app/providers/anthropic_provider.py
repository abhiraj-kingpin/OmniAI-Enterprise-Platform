from collections.abc import AsyncIterator
from typing import Any

import anthropic

from app.providers.base import LLMProvider
from app.schemas import ChatMessage, StreamChunk
from app.tools import TOOL_DEFINITIONS, run_tool

DEFAULT_SYSTEM = "You are a helpful, concise AI assistant."
MAX_TOOL_ROUNDS = 5


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-opus-5") -> None:
        self.client = anthropic.AsyncAnthropic()
        self.model = model

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        use_tools: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        # The API is stateless — resend the whole conversation every turn.
        # Tool round-trips extend this list locally within the request;
        # only the final assistant text is persisted back to session memory.
        conversation: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": 4096,
                "system": system or DEFAULT_SYSTEM,
                "messages": conversation,
            }
            if use_tools:
                kwargs["tools"] = TOOL_DEFINITIONS

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(type="text", content=text)
                final = await stream.get_final_message()

            if final.stop_reason == "refusal":
                yield StreamChunk(
                    type="error",
                    message="The model declined to respond to this request.",
                )
                return

            conversation.append({"role": "assistant", "content": final.content})
            yield StreamChunk(
                type="usage",
                usage={
                    "input_tokens": final.usage.input_tokens,
                    "output_tokens": final.usage.output_tokens,
                },
            )

            if final.stop_reason != "tool_use":
                return

            tool_results: list[dict[str, Any]] = []
            for block in final.content:
                if block.type != "tool_use":
                    continue
                yield StreamChunk(type="tool_use", name=block.name, input=block.input)
                output = run_tool(block.name, block.input)
                yield StreamChunk(type="tool_result", name=block.name, content=output)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )
            conversation.append({"role": "user", "content": tool_results})

        yield StreamChunk(
            type="error",
            message="Stopped after too many tool round-trips.",
        )
