from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.memory import store
from app.providers.factory import get_provider
from app.providers.types import AIMessage
from app.schemas import ChatMessage, ChatRequest, StreamChunk
from app.tools import TOOL_DEFINITIONS, run_tool

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    store.append(req.session_id, ChatMessage(role="user", content=req.message))
    provider = get_provider(req.provider, req.model)
    history = [AIMessage(role=m.role, content=m.content) for m in store.get(req.session_id)]

    async def event_generator():
        assistant_text = ""
        try:
            async for chunk in provider.stream(
                messages=history,
                system=req.system,
                tools=TOOL_DEFINITIONS if req.use_tools else None,
                execute_tool=run_tool,
            ):
                if chunk.type == "text":
                    assistant_text += chunk.content
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as exc:  # surface provider/network errors to the client
            error = StreamChunk(type="error", message=str(exc))
            yield f"data: {error.model_dump_json()}\n\n"
        else:
            if assistant_text:
                store.append(
                    req.session_id, ChatMessage(role="assistant", content=assistant_text)
                )
        finally:
            yield f"data: {StreamChunk(type='done').model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/clear")
async def chat_clear(session_id: str) -> dict[str, bool]:
    store.clear(session_id)
    return {"cleared": True}
