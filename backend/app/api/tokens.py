"""Token-counting endpoint — lets the frontend show an estimated cost before
sending a turn. Uses the Anthropic count_tokens endpoint, never a third-party
tokenizer approximation (those undercount Claude tokens significantly).
"""

import anthropic
from fastapi import APIRouter

from app.schemas import TokenCountRequest

router = APIRouter()
_client = anthropic.AsyncAnthropic()


@router.post("/tokens/count")
async def count_tokens(req: TokenCountRequest) -> dict[str, int]:
    kwargs: dict = {
        "model": req.model,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
    }
    if req.system:
        kwargs["system"] = req.system

    result = await _client.messages.count_tokens(**kwargs)
    return {"input_tokens": result.input_tokens}
