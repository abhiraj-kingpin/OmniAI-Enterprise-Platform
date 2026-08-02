from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FaceDetectionResponse(BaseModel):
    faces: list[BoundingBox]


class EdgeDetectionResponse(BaseModel):
    contour_count: int
    image_base64_png: str


class OcrResponse(BaseModel):
    text: str


class CaptionResponse(BaseModel):
    caption: str


class ClassifyRequest(BaseModel):
    categories: list[str]


class ClassifyResponse(BaseModel):
    category: str
    confidence_note: str


class DetectObjectsResponse(BaseModel):
    objects: list[str]
    detail: str


class IndexImageResponse(BaseModel):
    image_id: str
    catalog: str
    total_images: int


class ProductSearchRequest(BaseModel):
    catalog: str
    query_text: str
    top_k: int = 5


class ProductMatch(BaseModel):
    image_id: str
    filename: str
    similarity: float


class ProductSearchResponse(BaseModel):
    query_text: str
    matches: list[ProductMatch]
