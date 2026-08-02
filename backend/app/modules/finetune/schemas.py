from typing import Literal

from pydantic import BaseModel


class TrainingExample(BaseModel):
    prompt: str
    completion: str


class StartJobRequest(BaseModel):
    base_model: str = "distilgpt2"
    examples: list[TrainingExample]
    epochs: int = 3
    learning_rate: float = 2e-4
    lora_r: int = 8
    lora_alpha: int = 16


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    base_model: str
    epochs: int
    log: list[str]
    eval_loss_before: float | None = None
    eval_loss_after: float | None = None
    error: str | None = None


class RlhfConceptsResponse(BaseModel):
    summary: str
    stages: list[dict[str, str]]
    why_not_implemented_here: str
