"""Hybrid search: BM25 (keyword) + dense (embedding) retrieval fused with
Reciprocal Rank Fusion, with an optional cross-encoder re-ranking pass.
"""

import numpy as np

from app.modules.rag.models import get_reranker
from app.modules.rag.schemas import RetrievedChunk
from app.modules.rag.store import Collection

RRF_K = 60
CANDIDATE_POOL = 20


def _ranks(scores: np.ndarray) -> np.ndarray:
    """1-indexed rank per item, descending by score (rank 1 = best)."""
    order = np.argsort(-scores)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(order) + 1)
    return ranks


def hybrid_search(
    collection: Collection,
    query: str,
    top_k: int = 5,
    rerank: bool = True,
) -> list[RetrievedChunk]:
    if not collection.chunks:
        return []

    bm25 = collection.bm25_scores(query)
    dense = collection.dense_scores(query)

    bm25_ranks = _ranks(bm25)
    dense_ranks = _ranks(dense)
    fused = 1.0 / (RRF_K + bm25_ranks) + 1.0 / (RRF_K + dense_ranks)

    pool_size = min(len(collection.chunks), max(top_k, CANDIDATE_POOL))
    candidate_idx = np.argsort(-fused)[:pool_size]

    results = [
        RetrievedChunk(
            chunk=collection.chunks[i],
            bm25_score=float(bm25[i]),
            dense_score=float(dense[i]),
            fused_score=float(fused[i]),
        )
        for i in candidate_idx
    ]

    if rerank and results:
        reranker = get_reranker()
        documents = [r.chunk.text for r in results]
        scores = list(reranker.rerank(query, documents))
        for r, s in zip(results, scores):
            r.rerank_score = float(s)
        results.sort(key=lambda r: r.rerank_score, reverse=True)
    else:
        results.sort(key=lambda r: r.fused_score, reverse=True)

    return results[:top_k]
