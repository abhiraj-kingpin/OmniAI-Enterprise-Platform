from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    width: int = 512
    height: int = 512
    steps: int = 25
    guidance_scale: float = 7.5
    lora_path: str | None = None
    seed: int | None = None


class EditRequest(BaseModel):
    prompt: str
    steps: int = 25


class JobStatus(BaseModel):
    job_id: str
    status: str
    prompt: str
    image_path: str | None = None
    error: str | None = None
