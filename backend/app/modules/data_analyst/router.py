from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from app.modules.data_analyst.charts import render_chart, suggest_charts
from app.modules.data_analyst.insights import build_insights
from app.modules.data_analyst.schemas import (
    ChartRequest,
    ChartSpec,
    ColumnInfo,
    DashboardResponse,
    DatasetInfo,
    InsightsResponse,
    SqlQueryRequest,
    SqlQueryResponse,
    UploadResponse,
)
from app.modules.data_analyst.sql import run_sql
from app.modules.data_analyst.store import get_dataset, list_datasets, register_dataset

router = APIRouter()


def _require_dataset(dataset_id: str):
    entry = get_dataset(dataset_id)
    if entry is None:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")
    return entry


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    try:
        dataset_id, df = register_dataset(file.filename or "dataset", content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    columns = [
        ColumnInfo(
            name=col,
            dtype=str(df[col].dtype),
            non_null=int(df[col].notna().sum()),
            unique=int(df[col].nunique()),
        )
        for col in df.columns
    ]
    return UploadResponse(
        dataset_id=dataset_id, filename=file.filename or dataset_id, rows=len(df), columns=columns
    )


@router.get("/datasets", response_model=list[DatasetInfo])
async def datasets() -> list[DatasetInfo]:
    return [
        DatasetInfo(dataset_id=did, filename=fname, rows=len(df), columns=len(df.columns))
        for did, fname, df in list_datasets()
    ]


@router.post("/query", response_model=SqlQueryResponse)
async def query(req: SqlQueryRequest) -> SqlQueryResponse:
    _, df = _require_dataset(req.dataset_id)
    try:
        return run_sql(df, req.sql)
    except Exception as exc:
        raise HTTPException(400, f"SQL error: {exc}") from exc


@router.get("/{dataset_id}/insights", response_model=InsightsResponse)
async def insights(dataset_id: str) -> InsightsResponse:
    _, df = _require_dataset(dataset_id)
    return await build_insights(dataset_id, df)


@router.post("/chart")
async def chart(req: ChartRequest) -> Response:
    _, df = _require_dataset(req.dataset_id)
    try:
        png_bytes = render_chart(df, req)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{dataset_id}/dashboard", response_model=DashboardResponse)
async def dashboard(dataset_id: str) -> DashboardResponse:
    _, df = _require_dataset(dataset_id)
    specs = [ChartSpec(**s) for s in suggest_charts(df)]
    ins = await build_insights(dataset_id, df)
    return DashboardResponse(dataset_id=dataset_id, suggested_charts=specs, insights=ins)
