"""Planning + Tool Calling: the model decides which browser action to take
next, sees the result, and decides the next one — the same tool-use-loop
shape as the Chat and Research Assistant modules, applied to a live
browser instead of a fixed toolset or a search API. Provider-agnostic via
app/providers/factory.py.
"""

from app.modules.browser_agent.browser import BrowserSession
from app.modules.browser_agent.schemas import AgentAction, RunResponse
from app.providers.factory import get_provider
from app.providers.types import AIMessage, ToolCall, ToolDefinition, ToolResult

_TOOLS = [
    ToolDefinition(
        name="navigate",
        description="Go to a URL.",
        input_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    ),
    ToolDefinition(
        name="click",
        description="Click the first element matching a CSS selector.",
        input_schema={"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]},
    ),
    ToolDefinition(
        name="type_text",
        description="Type text into an input matching a CSS selector, optionally pressing Enter.",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "submit": {"type": "boolean", "description": "Press Enter after typing"},
            },
            "required": ["selector", "text"],
        },
    ),
    ToolDefinition(
        name="extract_text",
        description=(
            "Read the visible text of elements matching a CSS selector "
            "(default 'body' for the whole page). Use this to see what's on "
            "the page before deciding the next action."
        ),
        input_schema={"type": "object", "properties": {"selector": {"type": "string"}}, "required": []},
    ),
    ToolDefinition(
        name="finish",
        description="Call this once the task is complete, with the final answer.",
        input_schema={"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
    ),
]

SYSTEM_PROMPT = (
    "You are a browser automation agent. You control a real Chromium browser "
    "through tools: navigate, click, type_text, extract_text. Plan your steps: "
    "usually navigate first, then extract_text to see what's on the page "
    "before clicking or typing — selectors must exist on the current page. "
    "When you have the answer to the task, call finish with it. Don't guess "
    "at content you haven't extracted."
)


async def run_agent(task: str, start_url: str | None, max_steps: int, headless: bool) -> RunResponse:
    provider = get_provider()
    session = BrowserSession(headless=headless)
    await session.start()

    actions: list[AgentAction] = []
    initial_message = task if not start_url else f"{task}\n\n(Start at: {start_url})"
    conversation: list[AIMessage] = [AIMessage(role="user", content=initial_message)]

    try:
        for _step in range(max_steps):
            response = await provider.complete(
                messages=conversation, system=SYSTEM_PROMPT, max_tokens=1024, tools=_TOOLS
            )
            conversation.append(AIMessage(role="assistant", content=response.text, tool_calls=response.tool_calls))

            if response.stop_reason != "tool_use":
                return RunResponse(task=task, answer=response.text, actions=actions, status="completed")

            tool_results: list[ToolResult] = []
            finished_answer = None
            for call in response.tool_calls:
                try:
                    result = await _dispatch(session, call)
                    is_error = False
                except Exception as exc:
                    result = f"Error: {exc}"
                    is_error = True

                actions.append(AgentAction(tool=call.name, input=call.input, result=result))
                tool_results.append(ToolResult(tool_call_id=call.id, content=result, is_error=is_error))
                if call.name == "finish":
                    finished_answer = call.input.get("answer", "")

            if finished_answer is not None:
                return RunResponse(task=task, answer=finished_answer, actions=actions, status="completed")

            conversation.append(AIMessage(role="user", content="", tool_results=tool_results))

        return RunResponse(
            task=task, answer="Reached the step limit before finishing.", actions=actions, status="max_steps_reached"
        )
    finally:
        await session.close()


async def _dispatch(session: BrowserSession, call: ToolCall) -> str:
    if call.name == "navigate":
        return await session.navigate(call.input["url"])
    if call.name == "click":
        return await session.click(call.input["selector"])
    if call.name == "type_text":
        return await session.type_text(call.input["selector"], call.input["text"], call.input.get("submit", False))
    if call.name == "extract_text":
        return await session.extract_text(call.input.get("selector", "body"))
    if call.name == "finish":
        return "Task marked finished."
    return f"Unknown tool: {call.name}"
