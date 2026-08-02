import threading
import uuid
from pathlib import Path

from app.config import settings
from app.modules.image_gen.pipeline import generate_image
from app.modules.image_gen.schemas import JobStatus

_jobs: dict[str, JobStatus] = {}
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
    job_id = str(uuid.uuid4())
    status = JobStatus(job_id=job_id, status="queued", prompt=prompt)
    _jobs[job_id] = status

    def _run() -> None:
        status.status = "running"
        try:
            output_path = str(_OUTPUT_DIR / f"{job_id}.png")
            status.image_path = generate_image(
                prompt,
                negative_prompt,
                width,
                height,
                steps,
                guidance_scale,
                lora_path,
                seed,
                output_path,
            )
            status.status = "completed"
        except Exception as exc:
            status.error = str(exc)
            status.status = "failed"

    threading.Thread(target=_run, daemon=True).start()
    return job_id


def get_job(job_id: str) -> JobStatus | None:
    return _jobs.get(job_id)


def list_jobs() -> list[JobStatus]:
    return list(_jobs.values())
