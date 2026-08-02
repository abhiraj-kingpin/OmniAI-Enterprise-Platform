"""Real MLflow tracking against a local SQLite store — no MLflow server
needed for this to work; `mlflow ui --backend-store-uri sqlite:///data/mlops/mlflow.db`
gives you the actual MLflow web dashboard against the same data this module
writes. (SQLite, not the plain filesystem store: recent MLflow versions put
the filesystem backend in maintenance mode and require a database backend
by default.)
"""

from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

from app.config import settings
from app.modules.mlops.schemas import ExperimentSummary, RunSummary

_TRACKING_DIR = Path(settings.data_dir) / "mlops"
_TRACKING_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = (_TRACKING_DIR / "mlflow.db").resolve()
_TRACKING_URI = f"sqlite:///{_DB_PATH.as_posix()}"

mlflow.set_tracking_uri(_TRACKING_URI)


def _client() -> MlflowClient:
    return MlflowClient(tracking_uri=_TRACKING_URI)


def log_run(
    experiment_name: str,
    run_name: str | None,
    params: dict[str, str],
    metrics: dict[str, float],
    tags: dict[str, str],
) -> tuple[str, str]:
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        for k, v in params.items():
            mlflow.log_param(k, v)
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        if tags:
            mlflow.set_tags(tags)
        return run.info.run_id, run.info.experiment_id


def list_experiments() -> list[ExperimentSummary]:
    client = _client()
    experiments = client.search_experiments()
    return [
        ExperimentSummary(
            experiment_id=e.experiment_id,
            name=e.name,
            run_count=len(client.search_runs([e.experiment_id])),
        )
        for e in experiments
    ]


def list_runs(experiment_name: str) -> list[RunSummary]:
    client = _client()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        return []
    runs = client.search_runs([experiment.experiment_id], order_by=["start_time DESC"])
    return [
        RunSummary(
            run_id=r.info.run_id,
            run_name=r.info.run_name,
            status=r.info.status,
            start_time=str(r.info.start_time) if r.info.start_time else None,
            params=dict(r.data.params),
            metrics=dict(r.data.metrics),
        )
        for r in runs
    ]


def get_tracking_uri() -> str:
    return _TRACKING_URI
