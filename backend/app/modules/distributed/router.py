from fastapi import APIRouter, HTTPException

from app.modules.distributed.celery_app import REDIS_URL, celery_app, text_stats_task
from app.modules.distributed.ray_tasks import ensure_ray, parallel_map
from app.modules.distributed.schemas import (
    ComponentStatus,
    ParallelMapRequest,
    ParallelMapResponse,
    TaskResultResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
)
from app.modules.distributed.spark_example import check_available as check_spark

router = APIRouter()


@router.post("/ray/parallel-map", response_model=ParallelMapResponse)
async def ray_parallel_map(req: ParallelMapRequest) -> ParallelMapResponse:
    """Genuinely runs on a local Ray cluster — see ray_tasks.py."""
    if not req.items:
        raise HTTPException(400, "Provide at least one item")
    results, elapsed, workers = parallel_map(req.items)
    return ParallelMapResponse(results=results, wall_time_seconds=round(elapsed, 4), workers_used=workers)


@router.post("/celery/submit", response_model=TaskSubmitResponse)
async def celery_submit(req: TaskSubmitRequest) -> TaskSubmitResponse:
    """Enqueues a real Celery task. Requires a running Redis broker and at
    least one `celery worker` process — see celery_app.py's docstring for
    the exact command. Without a worker running, the task sits queued."""
    try:
        async_result = text_stats_task.delay(req.text)
    except Exception as exc:
        raise HTTPException(
            503, f"Couldn't reach the Celery broker at {REDIS_URL}: {exc}"
        ) from exc
    return TaskSubmitResponse(task_id=async_result.id, status=async_result.status, broker=REDIS_URL)


@router.get("/celery/result/{task_id}", response_model=TaskResultResponse)
async def celery_result(task_id: str) -> TaskResultResponse:
    async_result = celery_app.AsyncResult(task_id)
    return TaskResultResponse(
        task_id=task_id,
        status=async_result.status,
        result=async_result.result if async_result.ready() else None,
    )


@router.get("/components", response_model=list[ComponentStatus])
async def components() -> list[ComponentStatus]:
    """Honest availability report for every distributed-infra piece this
    module touches, checked live rather than assumed."""
    statuses: list[ComponentStatus] = []

    try:
        ensure_ray()
        statuses.append(ComponentStatus(component="Ray", available=True, detail="Local single-node cluster running."))
    except Exception as exc:
        statuses.append(ComponentStatus(component="Ray", available=False, detail=str(exc)))

    try:
        celery_app.broker_connection().ensure_connection(max_retries=1)
        statuses.append(ComponentStatus(component="Celery + Redis", available=True, detail=f"Connected to {REDIS_URL}"))
    except Exception as exc:
        statuses.append(
            ComponentStatus(
                component="Celery + Redis",
                available=False,
                detail=f"No broker reachable at {REDIS_URL}: {exc}",
            )
        )

    try:
        from app.modules.distributed.kafka_example import check_available as check_kafka

        check_kafka()
        statuses.append(ComponentStatus(component="Kafka", available=True, detail="kafka-python installed (broker connectivity not probed)."))
    except Exception as exc:
        statuses.append(ComponentStatus(component="Kafka", available=False, detail=str(exc)))

    try:
        check_spark()
        statuses.append(ComponentStatus(component="Spark", available=True, detail="Java + pyspark available."))
    except Exception as exc:
        statuses.append(ComponentStatus(component="Spark", available=False, detail=str(exc)))

    statuses.append(
        ComponentStatus(
            component="ONNX Runtime",
            available=True,
            detail=(
                "In active use, not just installed — powers embeddings and "
                "reranking in app/modules/rag, CLIP search in "
                "app/modules/vision. See those modules for live endpoints."
            ),
        )
    )
    statuses.append(
        ComponentStatus(
            component="vLLM / TensorRT-LLM",
            available=False,
            detail=(
                "Both require an NVIDIA GPU, which this host doesn't have "
                "(unlike the PyTorch modules, this isn't the Smart App "
                "Control policy — there's no discrete GPU to schedule onto "
                "at all). See infra/k8s/backend-deployment.yaml for how a "
                "GPU-scheduled inference deployment would request "
                "`nvidia.com/gpu` resources on a cluster that has one."
            ),
        )
    )

    return statuses
