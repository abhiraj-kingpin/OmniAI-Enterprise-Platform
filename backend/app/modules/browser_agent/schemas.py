from typing import Any, Literal

from pydantic import BaseModel


class AgentAction(BaseModel):
    tool: str
    input: dict[str, Any]
    result: str


class RunRequest(BaseModel):
    task: str
    start_url: str | None = None
    max_steps: int = 12
    headless: bool = True


class RunResponse(BaseModel):
    task: str
    answer: str
    actions: list[AgentAction]
    status: Literal["completed", "max_steps_reached"]
