import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.config import settings
from app.core.availability import AvailabilityResponse, check_availability
from app.modules.video_gen.diffusion_pipeline import check_available
from app.modules.video_gen.interpolation import frames_to_gif, interpolate
from app.modules.video_gen.jobs import get_job, list_jobs, start_generate_job
from app.modules.video_gen.schemas import (
    GenerateVideoRequest,
    InterpolateResponse,
    JobStatus,
    LipSyncConceptsResponse,
)

router = APIRouter()

_INTERP_DIR = Path(settings.data_dir) / "video_gen" / "interpolated"


@router.post("/interpolate", response_model=InterpolateResponse)
async def interpolate_frames(
    frame_a: UploadFile = File(...),
    frame_b: UploadFile = File(...),
    n_intermediate: int = Form(6),
    fps: int = Form(8),
    format: str = Form("mp4"),
) -> InterpolateResponse:
    a_bytes, b_bytes = await frame_a.read(), await frame_b.read()
    _INTERP_DIR.mkdir(parents=True, exist_ok=True)

    output_id = uuid.uuid4().hex[:8]
    try:
        if format == "gif":
            output_path = str(_INTERP_DIR / f"{output_id}.gif")
            count = frames_to_gif(a_bytes, b_bytes, n_intermediate, output_path)
        else:
            output_path = str(_INTERP_DIR / f"{output_id}.mp4")
            count = interpolate(a_bytes, b_bytes, n_intermediate, output_path, fps=fps)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return InterpolateResponse(frames_generated=count, output_path=output_path, fps=fps)


@router.get("/interpolate/download")
async def download_interpolated(path: str) -> Response:
    resolved = Path(path).resolve()
    if _INTERP_DIR.resolve() not in resolved.parents:
        raise HTTPException(400, "Invalid path")
    if not resolved.exists():
        raise HTTPException(404, "File not found")
    media_type = "image/gif" if resolved.suffix == ".gif" else "video/mp4"
    return Response(content=resolved.read_bytes(), media_type=media_type)


@router.get("/availability", response_model=AvailabilityResponse)
async def availability() -> AvailabilityResponse:
    return check_availability(check_available)


@router.post("/generate", response_model=JobStatus)
async def generate(req: GenerateVideoRequest) -> JobStatus:
    job_id = start_generate_job(req.prompt, req.num_frames, req.fps)
    return get_job(job_id)


@router.get("/jobs", response_model=list[JobStatus])
async def jobs() -> list[JobStatus]:
    return list_jobs()


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str) -> JobStatus:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job


@router.get("/lip-sync-concepts", response_model=LipSyncConceptsResponse)
async def lip_sync_concepts() -> LipSyncConceptsResponse:
    return LipSyncConceptsResponse(
        summary=(
            "Lip sync generates or retimes mouth movement in a video to "
            "match a given audio track — used for dubbing and talking-head "
            "avatars."
        ),
        pipeline=[
            {"stage": "Audio analysis", "description": "Extract phoneme/viseme timing from the target audio (e.g. via forced alignment or a phoneme recognizer)."},
            {"stage": "Face landmark tracking", "description": "Detect and track the mouth region across video frames."},
            {"stage": "Mouth region synthesis", "description": "A trained model (Wav2Lip and similar) generates mouth frames conditioned on the audio features, composited back into the original video."},
        ],
        why_not_implemented_here=(
            "Every practical lip-sync model (Wav2Lip, SadTalker, etc.) is "
            "a separate PyTorch model family from this platform's "
            "text-to-video pipeline and isn't part of this module's "
            "dependency set. The Speech AI module's faster-whisper "
            "transcription (CTranslate2, not PyTorch) could feed word "
            "timing into stage 1 of this pipeline if stages 2-3 were added."
        ),
    )
