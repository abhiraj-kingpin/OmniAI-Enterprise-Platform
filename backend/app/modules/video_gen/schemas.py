from pydantic import BaseModel


class InterpolateResponse(BaseModel):
    frames_generated: int
    output_path: str
    fps: int


class GenerateVideoRequest(BaseModel):
    prompt: str
    num_frames: int = 24
    fps: int = 8


class JobStatus(BaseModel):
    job_id: str
    status: str
    prompt: str
    video_path: str | None = None
    error: str | None = None


class LipSyncConceptsResponse(BaseModel):
    summary: str
    pipeline: list[dict[str, str]]
    why_not_implemented_here: str
