"""Generic in-memory background-job tracker.

Several modules (Fine-Tuning, Image Generation) run CPU-bound work that's
too slow for a request/response cycle, so they kick it off on a thread and
expose a "start, then poll status" API — the same shape a real job queue
(Celery, Ray, a managed training service) presents, without the
infrastructure. This used to be re-implemented per module; `JobStore`
centralizes the bookkeeping (id generation, thread spawn, capturing an
unhandled exception as a failed job) so each module only supplies its own
status schema and work function.
"""

import threading
import uuid
from collections.abc import Callable
from typing import Protocol


class TrackedJob(Protocol):
    job_id: str
    status: str
    error: str | None


class JobStore[JobT: TrackedJob]:
    """Registry of background jobs, keyed by id. One instance per module."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobT] = {}

    def start(self, make_status: Callable[[str], JobT], run: Callable[[JobT], None]) -> str:
        """Register a new job and run `run(status)` on a daemon thread.

        `run` must mutate `status` in place as work progresses, including
        setting `status.status = "completed"` on success — this only
        guarantees the "running" transition and that an exception raised
        inside `run` is captured as a failed job instead of crashing the
        thread silently.
        """
        job_id = str(uuid.uuid4())
        status = make_status(job_id)
        self._jobs[job_id] = status

        def _execute() -> None:
            status.status = "running"
            try:
                run(status)
            except Exception as exc:
                status.error = str(exc)
                status.status = "failed"

        threading.Thread(target=_execute, daemon=True).start()
        return job_id

    def get(self, job_id: str) -> JobT | None:
        return self._jobs.get(job_id)

    def list(self) -> list[JobT]:
        return list(self._jobs.values())
