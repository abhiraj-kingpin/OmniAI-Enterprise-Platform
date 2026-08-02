from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas import ChatMessage, StreamChunk


class LLMProvider(ABC):
    """Common interface every model provider streams chat turns through.

    Add a new provider (Gemini, a local vLLM endpoint, ...) by subclassing
    this and implementing stream_chat, then register it in registry.py.
    """

    @abstractmethod
    def stream_chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        use_tools: bool = True,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a full assistant turn (including any tool round-trips)."""
        raise NotImplementedError
