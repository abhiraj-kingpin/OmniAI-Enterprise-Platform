from pydantic import BaseModel


class UploadResponse(BaseModel):
    dataset_id: str
    users: int
    items: int
    interactions: int


class TrainRequest(BaseModel):
    dataset_id: str
    factors: int = 20
    epochs: int = 30
    learning_rate: float = 0.01
    regularization: float = 0.02


class TrainResponse(BaseModel):
    dataset_id: str
    factors: int
    epochs: int
    final_rmse: float


class RecommendationItem(BaseModel):
    item_id: str
    predicted_rating: float
    popularity: float
    final_score: float


class RecommendResponse(BaseModel):
    dataset_id: str
    user_id: str
    recommendations: list[RecommendationItem]


class SimilarItem(BaseModel):
    item_id: str
    similarity: float


class SimilarItemsResponse(BaseModel):
    dataset_id: str
    item_id: str
    similar_items: list[SimilarItem]
