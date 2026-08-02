from pydantic import BaseModel


class LogRunRequest(BaseModel):
    experiment_name: str
    run_name: str | None = None
    params: dict[str, str] = {}
    metrics: dict[str, float] = {}
    tags: dict[str, str] = {}


class RunSummary(BaseModel):
    run_id: str
    run_name: str | None
    status: str
    start_time: str | None
    params: dict[str, str]
    metrics: dict[str, float]


class ExperimentSummary(BaseModel):
    experiment_id: str
    name: str
    run_count: int


class LogRunResponse(BaseModel):
    run_id: str
    experiment_id: str
    tracking_uri: str
