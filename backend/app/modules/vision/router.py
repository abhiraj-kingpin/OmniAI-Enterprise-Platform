import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.modules.vision import llm_vision
from app.modules.vision.classical import detect_edges, detect_faces
from app.modules.vision.clip_search import get_catalog
from app.modules.vision.ocr import extract_text
from app.modules.vision.schemas import (
    CaptionResponse,
    ClassifyResponse,
    DetectObjectsResponse,
    EdgeDetectionResponse,
    FaceDetectionResponse,
    IndexImageResponse,
    OcrResponse,
    ProductMatch,
    ProductSearchResponse,
)

router = APIRouter()


@router.post("/faces", response_model=FaceDetectionResponse)
async def faces(file: UploadFile = File(...)) -> FaceDetectionResponse:
    content = await file.read()
    try:
        return FaceDetectionResponse(faces=detect_faces(content))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/edges", response_model=EdgeDetectionResponse)
async def edges(file: UploadFile = File(...)) -> EdgeDetectionResponse:
    content = await file.read()
    try:
        contour_count, png_b64 = detect_edges(content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return EdgeDetectionResponse(contour_count=contour_count, image_base64_png=png_b64)


@router.post("/ocr", response_model=OcrResponse)
async def ocr(file: UploadFile = File(...)) -> OcrResponse:
    content = await file.read()
    try:
        return OcrResponse(text=extract_text(content))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/caption", response_model=CaptionResponse)
async def caption(file: UploadFile = File(...)) -> CaptionResponse:
    content = await file.read()
    media_type = file.content_type or "image/png"
    return CaptionResponse(caption=await llm_vision.caption(content, media_type))


@router.post("/classify", response_model=ClassifyResponse)
async def classify(file: UploadFile = File(...), categories: str = Form(...)) -> ClassifyResponse:
    """`categories` is a comma-separated list, e.g. 'cat,dog,bird,other'."""
    content = await file.read()
    media_type = file.content_type or "image/png"
    cats = [c.strip() for c in categories.split(",") if c.strip()]
    if not cats:
        raise HTTPException(400, "Provide at least one category")
    result = await llm_vision.classify(content, media_type, cats)
    return ClassifyResponse(category=result, confidence_note="Zero-shot via the configured LLM's vision, not a calibrated softmax score.")


@router.post("/detect-objects", response_model=DetectObjectsResponse)
async def detect_objects(file: UploadFile = File(...)) -> DetectObjectsResponse:
    """Object *enumeration* via a vision-capable LLM, not pixel-accurate
    bounding boxes — real YOLO needs PyTorch, which this host's Smart App
    Control policy blocks. See llm_vision.py for the full explanation."""
    content = await file.read()
    media_type = file.content_type or "image/png"
    objects, detail = await llm_vision.detect_objects(content, media_type)
    return DetectObjectsResponse(objects=objects, detail=detail)


@router.post("/catalog/{catalog}/index", response_model=IndexImageResponse)
async def index_image(catalog: str, file: UploadFile = File(...)) -> IndexImageResponse:
    content = await file.read()
    suffix = Path(file.filename or "image.png").suffix or ".png"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cat = get_catalog(catalog)
        image_id = cat.add_image(file.filename or "upload", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return IndexImageResponse(image_id=image_id, catalog=catalog, total_images=len(cat.image_ids))


@router.get("/catalog/{catalog}/search", response_model=ProductSearchResponse)
async def search_catalog(catalog: str, query: str, top_k: int = 5) -> ProductSearchResponse:
    cat = get_catalog(catalog)
    matches: list[ProductMatch] = cat.search_by_text(query, top_k=top_k)
    return ProductSearchResponse(query_text=query, matches=matches)
