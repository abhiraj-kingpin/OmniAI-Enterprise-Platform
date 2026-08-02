import threading
import uuid
from pathlib import Path

from app.config import settings
from app.modules.video_gen.diffusion_pipeline import generate_video
from app.modules.video_gen.schemas import JobStatus

_jobs: dict[str, JobStatus] = {}
_OUTPUT_DIR = Path(settings.data_dir) / "video_gen" / "outputs"


def start_generate_job(prompt: str, num_frames: int, fps: int) -> str:
    job_id = str(uuid.uuid4())
    status = JobStatus(job_id=job_id, status="queued", prompt=prompt)
    _jobs[job_id] = status

    def _run() -> None:
        status.status = "running"
        try:
            output_path = str(_OUTPUT_DIR / f"{job_id}.mp4")
            status.video_path = generate_video(prompt, num_frames, fps, output_path)
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
