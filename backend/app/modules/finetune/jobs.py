"""In-memory job tracker for fine-tuning runs.

Training is synchronous/CPU-bound, so each job runs in a background thread
(not the event loop) and reports progress via a simple log list the API
polls — the same "start job, poll status" shape a real training service
(SageMaker, Vertex, a Ray job) exposes, just without the cluster underneath.
"""

import threading
import uuid

from app.modules.finetune.lora_pipeline import run_lora_finetune
from app.modules.finetune.schemas import JobStatus, TrainingExample

_jobs: dict[str, JobStatus] = {}


def start_job(
    base_model: str,
    examples: list[TrainingExample],
    epochs: int,
    learning_rate: float,
    lora_r: int,
    lora_alpha: int,
) -> str:
    job_id = str(uuid.uuid4())
    status = JobStatus(job_id=job_id, status="queued", base_model=base_model, epochs=epochs, log=[])
    _jobs[job_id] = status

    def _run() -> None:
        status.status = "running"
        try:
            before, after = run_lora_finetune(
                base_model,
                examples,
                epochs,
                learning_rate,
                lora_r,
                lora_alpha,
                log=lambda msg: status.log.append(msg),
            )
            status.eval_loss_before = before
            status.eval_loss_after = after
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
