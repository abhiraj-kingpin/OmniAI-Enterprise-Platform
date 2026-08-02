from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.providers.base import LLMProvider
from app.schemas import ChatMessage, StreamChunk

DEFAULT_SYSTEM = "You are a helpful, concise AI assistant."


class OpenAIProvider(LLMProvider):
    """Second provider behind the same interface, to keep the chat module
    genuinely multi-LLM. No tool-calling here yet — see AnthropicProvider
    for the reference tool-use loop to extend this with.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        self.client = AsyncOpenAI()
        self.model = model

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        use_tools: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        oai_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system or DEFAULT_SYSTEM}
        ]
        oai_messages += [{"role": m.role, "content": m.content} for m in messages]

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield StreamChunk(type="text", content=delta)
