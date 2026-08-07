"""Token-counting endpoint — lets the frontend show an estimated cost before
sending a turn. Delegates to whichever provider the request specifies via
AIProvider.count_tokens(); see each provider adapter for how exact (real
endpoint) vs. approximate (local estimate) that count is.
"""

from fastapi import APIRouter

from app.providers.factory import get_provider
from app.providers.types import AIMessage
from app.schemas import TokenCountRequest

router = APIRouter()


@router.post("/tokens/count")
async def count_tokens(req: TokenCountRequest) -> dict[str, int]:
    provider = get_provider(req.provider, req.model)
    messages = [AIMessage(role=m.role, content=m.content) for m in req.messages]
    count = await provider.count_tokens(messages, system=req.system)
    return {"input_tokens": count}
