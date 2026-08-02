from typing import Literal

from pydantic import BaseModel


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    source: str
    chunk_index: int
    text: str


class UploadResponse(BaseModel):
    doc_id: str
    source: str
    chunks_indexed: int


class RetrievedChunk(BaseModel):
    chunk: Chunk
    bm25_score: float
    dense_score: float
    fused_score: float
    rerank_score: float | None = None


class QueryRequest(BaseModel):
    collection: str = "default"
    query: str
    top_k: int = 5
    rerank: bool = True
    answer: bool = True


class QueryResponse(BaseModel):
    query: str
    retrieved: list[RetrievedChunk]
    answer: str | None = None


class CollectionInfo(BaseModel):
    name: str
    documents: int
    chunks: int


class GraphNode(BaseModel):
    id: str
    label: str
    kind: Literal["entity"] = "entity"


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class GraphResponse(BaseModel):
    collection: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
