"""Job tracking for fine-tuning runs, on top of app/core/jobs.py's
generic background-job store."""

from app.core.jobs import JobStore
from app.modules.finetune.lora_pipeline import run_lora_finetune
from app.modules.finetune.schemas import JobStatus, TrainingExample

_store: JobStore[JobStatus] = JobStore()


def start_job(
    base_model: str,
    examples: list[TrainingExample],
    epochs: int,
    learning_rate: float,
    lora_r: int,
    lora_alpha: int,
) -> str:
    def _run(status: JobStatus) -> None:
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

    return _store.start(
        lambda job_id: JobStatus(job_id=job_id, status="queued", base_model=base_model, epochs=epochs, log=[]),
        _run,
    )


def get_job(job_id: str) -> JobStatus | None:
    return _store.get(job_id)


def list_jobs() -> list[JobStatus]:
    return _store.list()
