"""Job tracking for image-generation runs, on top of app/core/jobs.py's
generic background-job store."""

from pathlib import Path

from app.config import settings
from app.core.jobs import JobStore
from app.modules.image_gen.pipeline import generate_image
from app.modules.image_gen.schemas import JobStatus

_store: JobStore[JobStatus] = JobStore()
_OUTPUT_DIR = Path(settings.data_dir) / "image_gen" / "outputs"


def start_generate_job(
    prompt: str,
    negative_prompt: str | None,
    width: int,
    height: int,
    steps: int,
    guidance_scale: float,
    lora_path: str | None,
    seed: int | None,
) -> str:
    def _run(status: JobStatus) -> None:
        output_path = str(_OUTPUT_DIR / f"{status.job_id}.png")
        status.image_path = generate_image(
            prompt, negative_prompt, width, height, steps, guidance_scale, lora_path, seed, output_path
        )
        status.status = "completed"

    return _store.start(lambda job_id: JobStatus(job_id=job_id, status="queued", prompt=prompt), _run)


def get_job(job_id: str) -> JobStatus | None:
    return _store.get(job_id)


def list_jobs() -> list[JobStatus]:
    return _store.list()
