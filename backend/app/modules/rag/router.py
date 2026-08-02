import uuid

import anthropic
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.modules.rag.chunking import chunk_text
from app.modules.rag.graph import build_graph
from app.modules.rag.ingest import UnsupportedFileType, extract_text, extract_text_from_url
from app.modules.rag.retrieval import hybrid_search
from app.modules.rag.schemas import (
    CollectionInfo,
    GraphResponse,
    QueryRequest,
    QueryResponse,
    UploadResponse,
)
from app.modules.rag.store import get_collection, list_collections

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    collection: str = Form("default"),
) -> UploadResponse:
    content = await file.read()
    try:
        text = extract_text(file.filename or "upload", content)
    except UnsupportedFileType as exc:
        raise HTTPException(400, str(exc)) from exc

    chunks = chunk_text(text)
    doc_id = str(uuid.uuid4())
    col = get_collection(collection)
    n = col.add_document(doc_id, file.filename or doc_id, chunks)

    return UploadResponse(doc_id=doc_id, source=file.filename or doc_id, chunks_indexed=n)


@router.post("/upload-url", response_model=UploadResponse)
async def upload_url(url: str = Form(...), collection: str = Form("default")) -> UploadResponse:
    try:
        text = extract_text_from_url(url)
    except Exception as exc:
        raise HTTPException(400, f"Failed to fetch/parse URL: {exc}") from exc

    chunks = chunk_text(text)
    doc_id = str(uuid.uuid4())
    col = get_collection(collection)
    n = col.add_document(doc_id, url, chunks)

    return UploadResponse(doc_id=doc_id, source=url, chunks_indexed=n)


@router.get("/collections", response_model=list[CollectionInfo])
async def collections() -> list[CollectionInfo]:
    return [
        CollectionInfo(name=c.name, documents=c.document_count(), chunks=len(c.chunks))
        for c in list_collections()
    ]


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    col = get_collection(req.collection)
    retrieved = hybrid_search(col, req.query, top_k=req.top_k, rerank=req.rerank)

    answer = None
    if req.answer and retrieved:
        context = "\n\n---\n\n".join(
            f"[Source: {r.chunk.source}]\n{r.chunk.text}" for r in retrieved
        )
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            system=(
                "Answer the user's question using only the provided context. "
                "Cite sources by name inline. If the context doesn't contain "
                "the answer, say so plainly instead of guessing."
            ),
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {req.query}",
                }
            ],
        )
        answer = next(b.text for b in response.content if b.type == "text")
    elif req.answer:
        answer = "No documents in this collection matched the query."

    return QueryResponse(query=req.query, retrieved=retrieved, answer=answer)


@router.get("/collections/{collection}/graph", response_model=GraphResponse)
async def graph(collection: str) -> GraphResponse:
    col = get_collection(collection)
    if not col.chunks:
        raise HTTPException(404, f"Collection '{collection}' is empty or doesn't exist")
    return await build_graph(col, collection)
