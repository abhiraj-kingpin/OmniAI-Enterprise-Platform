"""CLIP skill / "product search": real CLIP embeddings (ONNX, via fastembed)
for images and text in the same vector space, so a text query can retrieve
visually-matching images — the classic "search products by description"
pattern, entirely local.
"""

import uuid
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.config import settings
from app.modules.vision.schemas import ProductMatch

_STORE_DIR = Path(settings.data_dir) / "vision" / "catalogs"


@lru_cache(maxsize=1)
def _image_model():
    from fastembed import ImageEmbedding

    return ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision")


@lru_cache(maxsize=1)
def _text_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name="Qdrant/clip-ViT-B-32-text")


class Catalog:
    def __init__(self, name: str) -> None:
        self.name = name
        self.image_ids: list[str] = []
        self.filenames: list[str] = []
        self.embeddings = np.zeros((0, 512), dtype=np.float32)
        self._load()

    @property
    def _dir(self) -> Path:
        d = _STORE_DIR / self.name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load(self) -> None:
        meta_path = self._dir / "meta.npy"
        emb_path = self._dir / "embeddings.npy"
        if meta_path.exists() and emb_path.exists():
            meta = np.load(meta_path, allow_pickle=True).item()
            self.image_ids, self.filenames = meta["image_ids"], meta["filenames"]
            self.embeddings = np.load(emb_path)

    def _save(self) -> None:
        np.save(
            self._dir / "meta.npy",
            {"image_ids": self.image_ids, "filenames": self.filenames},
        )
        np.save(self._dir / "embeddings.npy", self.embeddings)

    def add_image(self, filename: str, image_path: str) -> str:
        vec = np.array(list(_image_model().embed([image_path])), dtype=np.float32)
        norm = np.linalg.norm(vec, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        vec = vec / norm

        image_id = str(uuid.uuid4())
        self.image_ids.append(image_id)
        self.filenames.append(filename)
        self.embeddings = np.vstack([self.embeddings, vec]) if self.embeddings.size else vec
        self._save()
        return image_id

    def search_by_text(self, query: str, top_k: int) -> list[ProductMatch]:
        if not self.image_ids:
            return []
        text_vec = np.array(list(_text_model().embed([query])), dtype=np.float32)[0]
        text_vec = text_vec / (np.linalg.norm(text_vec) or 1.0)

        sims = self.embeddings @ text_vec
        order = np.argsort(-sims)[:top_k]
        return [
            ProductMatch(
                image_id=self.image_ids[i], filename=self.filenames[i], similarity=float(sims[i])
            )
            for i in order
        ]


_catalogs: dict[str, Catalog] = {}


def get_catalog(name: str) -> Catalog:
    if name not in _catalogs:
        _catalogs[name] = Catalog(name)
    return _catalogs[name]
