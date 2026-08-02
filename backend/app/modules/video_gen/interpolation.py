"""Frame Interpolation, genuinely real and running: classical dense optical
flow (Farneback, OpenCV) rather than a learned interpolator (RIFE, DAIN —
both PyTorch). Given two frames, estimate motion both directions and warp
each frame partway along it for every intermediate timestep, blending the
two warped results — the standard bidirectional-flow interpolation approach
predating deep-learned interpolators, and still a reasonable result for
moderate motion between frames.
"""

import cv2
import numpy as np
from PIL import Image


def _decode(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Couldn't decode image")
    return img


def _warp(img: np.ndarray, flow: np.ndarray, t: float) -> np.ndarray:
    h, w = flow.shape[:2]
    grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (grid_x + flow[..., 0] * t).astype(np.float32)
    map_y = (grid_y + flow[..., 1] * t).astype(np.float32)
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def interpolate(
    frame_a_bytes: bytes, frame_b_bytes: bytes, n_intermediate: int, output_path: str, fps: int = 8
) -> int:
    frame_a = _decode(frame_a_bytes)
    frame_b = _decode(frame_b_bytes)
    frame_b = cv2.resize(frame_b, (frame_a.shape[1], frame_a.shape[0]))

    gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

    flow_ab = cv2.calcOpticalFlowFarneback(gray_a, gray_b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    flow_ba = cv2.calcOpticalFlowFarneback(gray_b, gray_a, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    frames = [frame_a]
    for i in range(1, n_intermediate + 1):
        t = i / (n_intermediate + 1)
        warped_a = _warp(frame_a, flow_ab, t)
        warped_b = _warp(frame_b, flow_ba, 1 - t)
        blended = cv2.addWeighted(warped_a, 1 - t, warped_b, t, 0)
        frames.append(blended)
    frames.append(frame_b)

    h, w = frame_a.shape[:2]
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames:
        writer.write(f)
    writer.release()

    return len(frames)


def frames_to_gif(frame_a_bytes: bytes, frame_b_bytes: bytes, n_intermediate: int, output_path: str) -> int:
    """Same interpolation, saved as an animated GIF instead of mp4 — easier
    to preview inline without a video player."""
    frame_a = _decode(frame_a_bytes)
    frame_b = _decode(frame_b_bytes)
    frame_b = cv2.resize(frame_b, (frame_a.shape[1], frame_a.shape[0]))

    gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
    flow_ab = cv2.calcOpticalFlowFarneback(gray_a, gray_b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    flow_ba = cv2.calcOpticalFlowFarneback(gray_b, gray_a, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    pil_frames = [Image.fromarray(cv2.cvtColor(frame_a, cv2.COLOR_BGR2RGB))]
    for i in range(1, n_intermediate + 1):
        t = i / (n_intermediate + 1)
        warped_a = _warp(frame_a, flow_ab, t)
        warped_b = _warp(frame_b, flow_ba, 1 - t)
        blended = cv2.addWeighted(warped_a, 1 - t, warped_b, t, 0)
        pil_frames.append(Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)))
    pil_frames.append(Image.fromarray(cv2.cvtColor(frame_b, cv2.COLOR_BGR2RGB)))

    pil_frames[0].save(
        output_path, save_all=True, append_images=pil_frames[1:], duration=120, loop=0
    )
    return len(pil_frames)
