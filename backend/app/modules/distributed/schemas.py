from typing import Any

from pydantic import BaseModel


class ParallelMapRequest(BaseModel):
    items: list[str]


class ParallelMapResponse(BaseModel):
    results: list[dict[str, Any]]
    wall_time_seconds: float
    workers_used: int


class TaskSubmitRequest(BaseModel):
    text: str


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    broker: str


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None


class ComponentStatus(BaseModel):
    component: str
    available: bool
    detail: str
