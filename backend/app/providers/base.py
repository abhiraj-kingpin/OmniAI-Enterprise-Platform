"""The AI service layer's provider interface.

Every supported provider (Anthropic, OpenAI, Gemini, Ollama) implements
this. Nothing outside app/providers/ should import a provider SDK directly
or reference a model name like "claude-opus-5" — see factory.py to obtain a
configured instance selected by the AI_PROVIDER environment variable.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.providers.types import AIMessage, AIResponse, ToolDefinition
from app.schemas import StreamChunk

ToolExecutor = Callable[[str, dict[str, Any]], str]


class AIProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict | None = None,
    ) -> AIResponse:
        """One non-streaming completion.

        `response_schema`, if given, is a JSON Schema the response text must
        conform to — each adapter uses its provider's native structured-output
        feature where one exists, and falls back to prompting for JSON and
        parsing the result where it doesn't.
        """
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        execute_tool: ToolExecutor | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a full assistant turn, including any tool round-trips —
        used by the Multi-LLM Chat module.

        `execute_tool(name, input) -> result` is supplied by the caller and
        run for each tool call the model makes; the provider drives the
        round-trip loop but never decides what a tool does — that keeps this
        layer generic instead of coupled to any one module's toolset
        (see app/tools.py, the Chat module's tool registry).
        """
        raise NotImplementedError

    @abstractmethod
    async def count_tokens(self, messages: list[AIMessage], *, system: str | None = None) -> int:
        """Best-effort token count for the given conversation: exact where
        the provider has a real counting endpoint (Anthropic, Gemini), an
        approximation otherwise (see each adapter's docstring)."""
        raise NotImplementedError
