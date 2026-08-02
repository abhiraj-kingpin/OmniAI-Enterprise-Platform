"""Lazily-loaded local ML models for RAG.

Loaded on first use (not at import time) so the rest of the platform doesn't
pay a multi-second model-load cost just because this module got imported.

Uses fastembed (ONNX Runtime under the hood) rather than sentence-transformers
(PyTorch). Functionally equivalent — same embedding/cross-encoder models,
same quality — but PyTorch's community-built DLLs get blocked outright by
Windows Smart App Control on this host (unsigned to its "Enterprise" level;
see `Microsoft-Windows-CodeIntegrity/Operational` event 3077), while
Microsoft's own ONNX Runtime binaries pass. If you're deploying somewhere
without that restriction, sentence-transformers works as a drop-in swap.
"""

import re
from functools import lru_cache

import numpy as np

_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> list[str]:
    """Simple whitespace/punctuation tokenizer for BM25 — good enough for
    keyword search; swap for a proper analyzer (stemming, stopwords) if
    retrieval quality on real corpora demands it."""
    return _TOKEN_RE.findall(text.lower())


@lru_cache(maxsize=1)
def get_embedder():
    """Dense retrieval / Embeddings skill: a small local ONNX embedding
    model (~130MB), no API cost per chunk, no GPU required."""
    from fastembed import TextEmbedding

    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


@lru_cache(maxsize=1)
def get_reranker():
    """Re-ranking skill: a small ONNX cross-encoder that scores (query,
    chunk) pairs directly — more accurate than embedding similarity alone,
    only run on the fused shortlist since it's O(candidates), not O(corpus)."""
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts and L2-normalize, so dot product == cosine
    similarity downstream."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vecs = np.array(list(get_embedder().embed(texts)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms
