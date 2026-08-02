"""OCR via RapidOCR (ONNX Runtime) — not Tesseract.

Tesseract needs a separate native binary installed on the host; on this
machine the installer requires interactive UAC elevation this environment
can't grant (same story as the PyTorch/Smart App Control situation — see
app/modules/rag/models.py). RapidOCR runs PaddleOCR's detection+recognition
models through onnxruntime, the same Microsoft-signed, pip-installable
runtime already used for RAG embeddings and Speech transcription — no
external binary, no PATH setup, no elevation.
"""

import io
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _get_engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def extract_text(image_bytes: bytes) -> str:
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    result, _elapsed = _get_engine()(np.array(image))
    if not result:
        return ""
    return "\n".join(line[1] for line in result)
