"""Classical CV via OpenCV — genuinely local, no model download beyond what
ships inside the opencv-python-headless wheel (the Haar cascade XML files)."""

import base64

import cv2
import numpy as np

from app.modules.vision.schemas import BoundingBox

_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _decode(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Couldn't decode image — is it a valid JPEG/PNG?")
    return img


def detect_faces(image_bytes: bytes) -> list[BoundingBox]:
    img = _decode(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return [BoundingBox(x=int(x), y=int(y), width=int(w), height=int(h)) for x, y, w, h in faces]


def detect_edges(image_bytes: bytes) -> tuple[int, str]:
    """Canny edge detection + contour count, returns the edge-map PNG as
    base64 so the caller can render it directly."""
    img = _decode(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    ok, buf = cv2.imencode(".png", edges)
    if not ok:
        raise ValueError("Failed to encode edge map")
    return len(contours), base64.b64encode(buf.tobytes()).decode("ascii")
