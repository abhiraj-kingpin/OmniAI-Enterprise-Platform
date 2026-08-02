from fastapi import APIRouter

from app.modules.mlops.schemas import (
    ExperimentSummary,
    LogRunRequest,
    LogRunResponse,
    RunSummary,
)
from app.modules.mlops.tracking import get_tracking_uri, list_experiments, list_runs, log_run

router = APIRouter()


@router.post("/runs", response_model=LogRunResponse)
async def create_run(req: LogRunRequest) -> LogRunResponse:
    run_id, experiment_id = log_run(
        req.experiment_name, req.run_name, req.params, req.metrics, req.tags
    )
    return LogRunResponse(run_id=run_id, experiment_id=experiment_id, tracking_uri=get_tracking_uri())


@router.get("/experiments", response_model=list[ExperimentSummary])
async def experiments() -> list[ExperimentSummary]:
    return list_experiments()


@router.get("/experiments/{experiment_name}/runs", response_model=list[RunSummary])
async def runs(experiment_name: str) -> list[RunSummary]:
    return list_runs(experiment_name)
