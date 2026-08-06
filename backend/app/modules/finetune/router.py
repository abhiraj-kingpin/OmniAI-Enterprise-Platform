from fastapi import APIRouter, HTTPException

from app.core.availability import AvailabilityResponse, check_availability
from app.modules.finetune.jobs import get_job, list_jobs, start_job
from app.modules.finetune.lora_pipeline import check_available
from app.modules.finetune.schemas import JobStatus, RlhfConceptsResponse, StartJobRequest

router = APIRouter()


@router.get("/availability", response_model=AvailabilityResponse)
async def availability() -> AvailabilityResponse:
    return check_availability(check_available)


@router.post("/jobs", response_model=JobStatus)
async def create_job(req: StartJobRequest) -> JobStatus:
    if not req.examples:
        raise HTTPException(400, "Provide at least one training example")
    job_id = start_job(
        req.base_model, req.examples, req.epochs, req.learning_rate, req.lora_r, req.lora_alpha
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


@router.get("/rlhf-concepts", response_model=RlhfConceptsResponse)
async def rlhf_concepts() -> RlhfConceptsResponse:
    return RlhfConceptsResponse(
        summary=(
            "RLHF (Reinforcement Learning from Human Feedback) fine-tunes a "
            "model to match human preferences rather than just imitate "
            "training text — used to make base LLMs into aligned chat "
            "assistants."
        ),
        stages=[
            {
                "stage": "Supervised Fine-Tuning (SFT)",
                "description": "Fine-tune the base model on high-quality demonstration data (prompt/response pairs) — exactly what this module's LoRA pipeline does.",
            },
            {
                "stage": "Reward Modeling",
                "description": "Train a second model to score responses, using human-labeled pairwise preferences (A is better than B) as training data.",
            },
            {
                "stage": "RL Fine-Tuning (PPO)",
                "description": "Fine-tune the SFT model further, using the reward model's score as the RL signal — the policy is updated to maximize expected reward while a KL penalty keeps it close to the SFT model.",
            },
        ],
        why_not_implemented_here=(
            "RLHF needs three models in memory at once (policy, reference, "
            "reward) plus an RL training loop (e.g. TRL's PPOTrainer) — "
            "substantially heavier than the single-model LoRA case this "
            "module implements, and impractical without a GPU. The stages "
            "above are what a GPU-backed training pipeline would run."
        ),
    )
