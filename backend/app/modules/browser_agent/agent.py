"""Planning + Tool Calling: Claude decides which browser action to take
next, sees the result, and decides the next one — the same tool-use-loop
shape as the chat and research-assistant modules, applied to a live browser
instead of a fixed toolset or a search API.
"""

from typing import Any

import anthropic

from app.modules.browser_agent.browser import BrowserSession
from app.modules.browser_agent.schemas import AgentAction, RunResponse

_TOOLS = [
    {
        "name": "navigate",
        "description": "Go to a URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "click",
        "description": "Click the first element matching a CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
        },
    },
    {
        "name": "type_text",
        "description": "Type text into an input matching a CSS selector, optionally pressing Enter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "submit": {"type": "boolean", "description": "Press Enter after typing"},
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "extract_text",
        "description": (
            "Read the visible text of elements matching a CSS selector "
            "(default 'body' for the whole page). Use this to see what's on "
            "the page before deciding the next action."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "finish",
        "description": "Call this once the task is complete, with the final answer.",
        "input_schema": {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
    },
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
    client = anthropic.AsyncAnthropic()
    session = BrowserSession(headless=headless)
    await session.start()

    actions: list[AgentAction] = []
    initial_message = task if not start_url else f"{task}\n\n(Start at: {start_url})"
    conversation: list[dict[str, Any]] = [{"role": "user", "content": initial_message}]

    try:
        for _step in range(max_steps):
            response = await client.messages.create(
                model="claude-opus-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=_TOOLS,
                messages=conversation,
            )
            conversation.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                text = next((b.text for b in response.content if b.type == "text"), "")
                return RunResponse(task=task, answer=text, actions=actions, status="completed")

            tool_results = []
            finished_answer = None
            for block in response.content:
                if block.type != "tool_use":
                    continue

                try:
                    result = await _dispatch(session, block.name, block.input)
                    is_error = False
                except Exception as exc:
                    result = f"Error: {exc}"
                    is_error = True

                actions.append(AgentAction(tool=block.name, input=block.input, result=result))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                        "is_error": is_error,
                    }
                )
                if block.name == "finish":
                    finished_answer = block.input.get("answer", "")

            if finished_answer is not None:
                return RunResponse(
                    task=task, answer=finished_answer, actions=actions, status="completed"
                )

            conversation.append({"role": "user", "content": tool_results})

        return RunResponse(
            task=task,
            answer="Reached the step limit before finishing.",
            actions=actions,
            status="max_steps_reached",
        )
    finally:
        await session.close()


async def _dispatch(session: BrowserSession, name: str, tool_input: dict[str, Any]) -> str:
    if name == "navigate":
        return await session.navigate(tool_input["url"])
    if name == "click":
        return await session.click(tool_input["selector"])
    if name == "type_text":
        return await session.type_text(
            tool_input["selector"], tool_input["text"], tool_input.get("submit", False)
        )
    if name == "extract_text":
        return await session.extract_text(tool_input.get("selector", "body"))
    if name == "finish":
        return "Task marked finished."
    return f"Unknown tool: {name}"
