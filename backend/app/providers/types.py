"""Provider-agnostic data shapes for the AI service layer.

Every AIProvider implementation speaks these types at its boundary — callers
never see Anthropic's content blocks, OpenAI's delta objects, or Gemini's
Part/Content classes directly. Each provider adapter is responsible for
translating to and from its own SDK's wire format internally.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TextPart:
    text: str


@dataclass
class ImagePart:
    data: bytes
    media_type: str  # e.g. "image/png", "image/jpeg"


ContentPart = TextPart | ImagePart


@dataclass
class ToolCall:
    """An assistant turn asking to invoke a tool."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResult:
    """The result of executing a ToolCall, fed back on the following turn."""

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class AIMessage:
    """One turn of conversation.

    `content` is plain text for most turns, or a list of parts for a
    multimodal (text + image) user turn. An assistant turn that called a
    tool carries `tool_calls`; the following user turn carries the matching
    `tool_results` — each provider adapter maps that onto whatever
    role/shape it needs (Anthropic: a user-role message with tool_result
    blocks; OpenAI: one role="tool" message per result; Gemini: a
    function_response Part).
    """

    role: Literal["user", "assistant"]
    content: str | list[ContentPart] = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


@dataclass
class ToolDefinition:
    """Canonical tool schema, in Anthropic's shape — every other provider's
    function-calling format is a straightforward mapping of the same three
    fields (OpenAI wraps it in `{"type": "function", "function": {...}}`;
    Gemini's FunctionDeclaration takes the same fields under the same
    names)."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class AIResponse:
    """A single non-streaming completion."""

    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "refusal"] = "end_turn"
    usage: dict[str, int] = field(default_factory=dict)
