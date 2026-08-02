from fastapi import APIRouter, HTTPException

from app.modules.browser_agent.agent import run_agent
from app.modules.browser_agent.schemas import RunRequest, RunResponse

router = APIRouter()


@router.post("/run", response_model=RunResponse)
async def run(req: RunRequest) -> RunResponse:
    try:
        return await run_agent(
            task=req.task,
            start_url=req.start_url,
            max_steps=req.max_steps,
            headless=req.headless,
        )
    except Exception as exc:
        raise HTTPException(500, f"Browser agent run failed: {exc}") from exc
