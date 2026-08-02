import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.modules.recommendations.demo_data import generate_demo_interactions
from app.modules.recommendations.mf import MatrixFactorizationModel
from app.modules.recommendations.ranking import recommend_for_user
from app.modules.recommendations.schemas import (
    RecommendResponse,
    SimilarItemsResponse,
    TrainRequest,
    TrainResponse,
    UploadResponse,
)
from app.modules.recommendations.store import (
    get_interactions,
    get_model,
    register_interactions,
    set_model,
)

router = APIRouter()

REQUIRED_COLUMNS = {"user_id", "item_id", "rating"}


def _register(df: pd.DataFrame) -> UploadResponse:
    if not REQUIRED_COLUMNS.issubset(df.columns):
        raise HTTPException(400, f"CSV must have columns: {sorted(REQUIRED_COLUMNS)}")
    dataset_id = register_interactions(df)
    return UploadResponse(
        dataset_id=dataset_id,
        users=df["user_id"].nunique(),
        items=df["item_id"].nunique(),
        interactions=len(df),
    )


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, f"Couldn't parse CSV: {exc}") from exc
    return _register(df)


@router.post("/demo-dataset", response_model=UploadResponse)
async def demo_dataset() -> UploadResponse:
    """Generates a synthetic user/item interaction dataset with real latent
    structure, so recommend/similar-items give non-trivial results without
    requiring the caller to bring their own data."""
    df = generate_demo_interactions()
    return _register(df)


@router.post("/train", response_model=TrainResponse)
async def train(req: TrainRequest) -> TrainResponse:
    df = get_interactions(req.dataset_id)
    if df is None:
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found")

    model = MatrixFactorizationModel(factors=req.factors)
    rmse = model.fit(
        df,
        epochs=req.epochs,
        lr=req.learning_rate,
        reg=req.regularization,
    )
    set_model(req.dataset_id, model)

    return TrainResponse(
        dataset_id=req.dataset_id, factors=req.factors, epochs=req.epochs, final_rmse=rmse
    )


@router.get("/{dataset_id}/recommend/{user_id}", response_model=RecommendResponse)
async def recommend(dataset_id: str, user_id: str, top_k: int = 10) -> RecommendResponse:
    model = get_model(dataset_id)
    if model is None:
        raise HTTPException(404, f"No trained model for dataset '{dataset_id}'. Call /train first.")
    if not model.has_user(user_id):
        raise HTTPException(404, f"Unknown user '{user_id}'")

    recs = recommend_for_user(model, user_id, top_k=top_k)
    return RecommendResponse(dataset_id=dataset_id, user_id=user_id, recommendations=recs)


@router.get("/{dataset_id}/similar-items/{item_id}", response_model=SimilarItemsResponse)
async def similar_items(dataset_id: str, item_id: str, top_k: int = 10) -> SimilarItemsResponse:
    model = get_model(dataset_id)
    if model is None:
        raise HTTPException(404, f"No trained model for dataset '{dataset_id}'. Call /train first.")
    if not model.has_item(item_id):
        raise HTTPException(404, f"Unknown item '{item_id}'")

    results = model.similar_items(item_id, top_k=top_k)
    return SimilarItemsResponse(
        dataset_id=dataset_id,
        item_id=item_id,
        similar_items=[{"item_id": i, "similarity": s} for i, s in results],
    )
