import pandas as pd
from fastapi import APIRouter, HTTPException

from app.modules.data_analyst.store import get_dataset
from app.modules.forecasting.features import engineer_features
from app.modules.forecasting.forecast import run_forecast
from app.modules.forecasting.schemas import (
    FeatureRequest,
    FeatureResponse,
    FeatureRow,
    ForecastRequest,
    ForecastResponse,
)

router = APIRouter()


def _require_dataset(dataset_id: str):
    entry = get_dataset(dataset_id)
    if entry is None:
        raise HTTPException(
            404,
            f"Dataset '{dataset_id}' not found. Upload it via "
            "POST /api/data-analyst/upload first — Forecasting shares the "
            "Data Analyst module's dataset store.",
        )
    return entry


@router.post("/features", response_model=FeatureResponse)
async def features(req: FeatureRequest) -> FeatureResponse:
    _, df = _require_dataset(req.dataset_id)
    try:
        engineered = engineer_features(df, req.date_col, req.value_col)
    except KeyError as exc:
        raise HTTPException(400, f"Column not found: {exc}") from exc

    def _clean(value) -> float | None:
        return None if pd.isna(value) else float(value)

    rows = [
        FeatureRow(
            date=row[req.date_col].date().isoformat(),
            value=_clean(row[req.value_col]),
            lag_1=_clean(row["lag_1"]),
            lag_7=_clean(row["lag_7"]),
            rolling_mean_7=_clean(row["rolling_mean_7"]),
            day_of_week=int(row["day_of_week"]),
            month=int(row["month"]),
        )
        for _, row in engineered.iterrows()
    ]
    return FeatureResponse(dataset_id=req.dataset_id, rows=rows)


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(req: ForecastRequest) -> ForecastResponse:
    _, df = _require_dataset(req.dataset_id)
    try:
        points, history_points = run_forecast(
            df, req.date_col, req.value_col, req.horizon, req.method
        )
    except KeyError as exc:
        raise HTTPException(400, f"Column not found: {exc}") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc)) from exc

    return ForecastResponse(
        dataset_id=req.dataset_id,
        method=req.method,
        horizon=req.horizon,
        history_points=history_points,
        forecast=points,
    )
