from typing import Any, Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = "claude-opus-5"
    message: str
    system: str | None = None
    use_tools: bool = True


class StreamChunk(BaseModel):
    """One SSE event sent to the frontend while a turn is streaming."""

    type: Literal["text", "tool_use", "tool_result", "usage", "done", "error"]
    content: str = ""
    name: str | None = None
    input: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    message: str | None = None


class TokenCountRequest(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    model: str = "claude-opus-5"
    messages: list[ChatMessage]
    system: str | None = None
