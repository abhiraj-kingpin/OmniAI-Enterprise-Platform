"""Real Celery app + task, Redis as broker and result backend.

Needs an actual Redis server reachable at REDIS_URL to do anything — Celery
itself doesn't have Ray's "just start a local cluster" mode; the broker is
a separate process by design (that's what lets multiple worker machines
share one queue). Run a worker against this module with:

    celery -A app.modules.distributed.celery_app worker --loglevel=info --pool=solo

(`--pool=solo` because Celery's default prefork pool needs os.fork, which
Windows doesn't have.)
"""

import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("omniai", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])


@celery_app.task(name="omniai.text_stats")
def text_stats_task(text: str) -> dict:
    words = text.split()
    return {
        "text_preview": text[:60],
        "word_count": len(words),
        "char_count": len(text),
    }
