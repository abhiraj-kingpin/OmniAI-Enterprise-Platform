"""FastAPI application assembly: middleware, exception handlers, and every
module router, mounted under /api.

Middleware order matters: Starlette applies middleware in the reverse of
the order it's added (last added = outermost), so CORS is added last to
sit outermost and handle preflight OPTIONS requests before rate limiting
or audit logging see them.
"""

import app.core.env  # noqa: F401, I001 — must load .env before importing modules below (some read env vars at import time, e.g. distributed/celery_app.py's REDIS_URL)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.tokens import router as tokens_router
from app.config import settings
from app.core.audit import AuditLogMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.modules.browser_agent.router import router as browser_agent_router
from app.modules.coding_assistant.router import router as coding_assistant_router
from app.modules.data_analyst.router import router as data_analyst_router
from app.modules.distributed.router import router as distributed_router
from app.modules.finetune.router import router as finetune_router
from app.modules.forecasting.router import router as forecasting_router
from app.modules.image_gen.router import router as image_gen_router
from app.modules.mlops.router import router as mlops_router
from app.modules.rag.router import router as rag_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.research_assistant.router import router as research_assistant_router
from app.modules.speech.router import router as speech_router
from app.modules.video_gen.router import router as video_gen_router
from app.modules.vision.router import router as vision_router

configure_logging()

app = FastAPI(title="OmniAI Enterprise Platform")

app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Module 1 (chat) and auth mount directly under /api; every other module
# gets its own /api/<slug> prefix, registered declaratively below so adding
# a module is a one-line addition instead of a repeated import+include pair.
app.include_router(chat_router, prefix="/api")
app.include_router(tokens_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

_MODULE_ROUTERS = (
    (rag_router, "rag"),
    (data_analyst_router, "data-analyst"),
    (research_assistant_router, "research"),
    (forecasting_router, "forecasting"),
    (recommendations_router, "recommendations"),
    (coding_assistant_router, "coding"),
    (vision_router, "vision"),
    (speech_router, "speech"),
    (browser_agent_router, "browser-agent"),
    (finetune_router, "finetune"),
    (mlops_router, "mlops"),
    (image_gen_router, "image-gen"),
    (video_gen_router, "video-gen"),
    (distributed_router, "distributed"),
)

for _router, _slug in _MODULE_ROUTERS:
    app.include_router(_router, prefix=f"/api/{_slug}", tags=[_slug])


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
