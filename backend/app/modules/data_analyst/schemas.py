from typing import Any, Literal

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    non_null: int
    unique: int


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: list[ColumnInfo]


class DatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int


class SqlQueryRequest(BaseModel):
    dataset_id: str
    sql: str


class SqlQueryResponse(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class InsightsResponse(BaseModel):
    dataset_id: str
    describe: dict[str, dict[str, float | None]]
    missing_values: dict[str, int]
    correlations: dict[str, dict[str, float]]
    narrative: str


class ChartRequest(BaseModel):
    dataset_id: str
    chart_type: Literal["bar", "line", "scatter", "hist", "box"] = "bar"
    x: str
    y: str | None = None
    agg: Literal["sum", "mean", "count", "max", "min"] | None = "sum"
    title: str | None = None


class ChartSpec(BaseModel):
    chart_type: str
    x: str
    y: str | None
    title: str


class DashboardResponse(BaseModel):
    dataset_id: str
    suggested_charts: list[ChartSpec]
    insights: InsightsResponse
