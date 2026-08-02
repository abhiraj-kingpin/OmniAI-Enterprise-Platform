from typing import Literal

from pydantic import BaseModel


class FeatureRequest(BaseModel):
    dataset_id: str
    date_col: str
    value_col: str


class FeatureRow(BaseModel):
    date: str
    value: float | None
    lag_1: float | None
    lag_7: float | None
    rolling_mean_7: float | None
    day_of_week: int
    month: int


class FeatureResponse(BaseModel):
    dataset_id: str
    rows: list[FeatureRow]


class ForecastRequest(BaseModel):
    dataset_id: str
    date_col: str
    value_col: str
    horizon: int = 14
    method: Literal["ets", "arima", "prophet"] = "ets"


class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower: float | None = None
    upper: float | None = None


class ForecastResponse(BaseModel):
    dataset_id: str
    method: str
    horizon: int
    history_points: int
    forecast: list[ForecastPoint]
