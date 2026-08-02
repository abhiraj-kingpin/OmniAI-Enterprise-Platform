"""Example Airflow DAG: nightly forecast refresh against the OmniAI backend.

Needs a real Airflow scheduler + webserver to run (`pip install apache-
airflow`, then drop this file in $AIRFLOW_HOME/dags) — not something this
repo can execute on its own. Included as a correct, working orchestration
example for the Forecasting + MLOps modules, using Airflow's TaskFlow API.

Pipeline: pull the latest sales CSV -> upload to the Data Analyst dataset
store -> run an ETS forecast -> log the run to MLflow.
"""

from __future__ import annotations

import datetime

import requests
from airflow.decorators import dag, task

OMNIAI_API_BASE = "http://omniai-backend/api"  # k8s in-cluster service DNS
SOURCE_CSV_URL = "https://example-data-warehouse.internal/exports/sales_daily.csv"


@dag(
    dag_id="omniai_forecast_pipeline",
    schedule="0 3 * * *",  # 03:00 daily
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": datetime.timedelta(minutes=5)},
    tags=["omniai", "forecasting"],
)
def omniai_forecast_pipeline():
    @task
    def fetch_source_csv() -> bytes:
        resp = requests.get(SOURCE_CSV_URL, timeout=60)
        resp.raise_for_status()
        return resp.content

    @task
    def upload_dataset(csv_bytes: bytes) -> str:
        resp = requests.post(
            f"{OMNIAI_API_BASE}/data-analyst/upload",
            files={"file": ("sales_daily.csv", csv_bytes, "text/csv")},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["dataset_id"]

    @task
    def run_forecast(dataset_id: str) -> dict:
        resp = requests.post(
            f"{OMNIAI_API_BASE}/forecasting/forecast",
            json={
                "dataset_id": dataset_id,
                "date_col": "date",
                "value_col": "sales",
                "horizon": 14,
                "method": "ets",
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    @task
    def log_to_mlflow(forecast_result: dict) -> None:
        requests.post(
            f"{OMNIAI_API_BASE}/mlops/runs",
            json={
                "experiment_name": "daily-sales-forecast",
                "params": {"method": forecast_result["method"], "horizon": str(forecast_result["horizon"])},
                "metrics": {"history_points": forecast_result["history_points"]},
                "tags": {"pipeline": "airflow-nightly"},
            },
            timeout=30,
        )

    dataset_id = upload_dataset(fetch_source_csv())
    forecast_result = run_forecast(dataset_id)
    log_to_mlflow(forecast_result)


omniai_forecast_pipeline()
