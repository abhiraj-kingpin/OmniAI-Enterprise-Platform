from fastapi import APIRouter, HTTPException, Response

from app.core.availability import AvailabilityResponse, check_availability
from app.modules.image_gen.jobs import get_job, list_jobs, start_generate_job
from app.modules.image_gen.pipeline import check_available
from app.modules.image_gen.schemas import GenerateRequest, JobStatus

router = APIRouter()


@router.get("/availability", response_model=AvailabilityResponse)
async def availability() -> AvailabilityResponse:
    return check_availability(check_available)


@router.post("/generate", response_model=JobStatus)
async def generate(req: GenerateRequest) -> JobStatus:
    job_id = start_generate_job(
        req.prompt,
        req.negative_prompt,
        req.width,
        req.height,
        req.steps,
        req.guidance_scale,
        req.lora_path,
        req.seed,
    )
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


@router.get("/jobs/{job_id}/image")
async def job_image(job_id: str) -> Response:
    job = get_job(job_id)
    if job is None or job.image_path is None:
        raise HTTPException(404, "Image not ready or job not found")
    with open(job.image_path, "rb") as f:
        return Response(content=f.read(), media_type="image/png")
