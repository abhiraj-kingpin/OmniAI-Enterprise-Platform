"""In-memory hybrid index (BM25 + dense) per collection, persisted to disk.

Not a real vector database (no ANN index, linear-scan cosine similarity) —
correct and fast enough for a demo-scale corpus (thousands of chunks), and
the place to swap in Qdrant once corpus size demands an ANN index.
"""

import json
import uuid
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from app.config import settings
from app.modules.rag.models import embed_texts, tokenize
from app.modules.rag.schemas import Chunk

_STORE_DIR = Path(settings.data_dir) / "rag"


class Collection:
    def __init__(self, name: str) -> None:
        self.name = name
        self.chunks: list[Chunk] = []
        self.embeddings: np.ndarray = np.zeros((0, 384), dtype=np.float32)
        self._bm25: BM25Okapi | None = None
        self._load()

    # --- persistence -----------------------------------------------------

    @property
    def _dir(self) -> Path:
        d = _STORE_DIR / self.name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load(self) -> None:
        chunks_path = self._dir / "chunks.json"
        emb_path = self._dir / "embeddings.npy"
        if chunks_path.exists() and emb_path.exists():
            data = json.loads(chunks_path.read_text(encoding="utf-8"))
            self.chunks = [Chunk(**c) for c in data]
            self.embeddings = np.load(emb_path)
            self._rebuild_bm25()

    def _save(self) -> None:
        (self._dir / "chunks.json").write_text(
            json.dumps([c.model_dump() for c in self.chunks]), encoding="utf-8"
        )
        np.save(self._dir / "embeddings.npy", self.embeddings)

    # --- indexing ----------------------------------------------------------

    def _rebuild_bm25(self) -> None:
        corpus = [tokenize(c.text) for c in self.chunks]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def add_document(self, doc_id: str, source: str, chunk_texts: list[str]) -> int:
        if not chunk_texts:
            return 0

        new_vecs = embed_texts(chunk_texts)

        start_index = len(self.chunks)
        for i, text in enumerate(chunk_texts):
            self.chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    doc_id=doc_id,
                    source=source,
                    chunk_index=start_index + i,
                    text=text,
                )
            )

        self.embeddings = (
            np.vstack([self.embeddings, new_vecs])
            if self.embeddings.size
            else np.array(new_vecs, dtype=np.float32)
        )
        self._rebuild_bm25()
        self._save()
        return len(chunk_texts)

    # --- search --------------------------------------------------------

    def bm25_scores(self, query: str) -> np.ndarray:
        if self._bm25 is None:
            return np.zeros(len(self.chunks))
        return np.array(self._bm25.get_scores(tokenize(query)))

    def dense_scores(self, query: str) -> np.ndarray:
        if not self.chunks:
            return np.zeros(0)
        query_vec = embed_texts([query])[0]
        return self.embeddings @ query_vec

    def document_count(self) -> int:
        return len({c.doc_id for c in self.chunks})


_collections: dict[str, Collection] = {}


def get_collection(name: str) -> Collection:
    if name not in _collections:
        _collections[name] = Collection(name)
    return _collections[name]


def list_collections() -> list[Collection]:
    # Pick up collections that exist on disk from a previous run but
    # haven't been touched yet this process.
    if _STORE_DIR.exists():
        for d in _STORE_DIR.iterdir():
            if d.is_dir() and d.name not in _collections:
                get_collection(d.name)
    return list(_collections.values())
