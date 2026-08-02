from dotenv import load_dotenv

# Must run before anything constructs an Anthropic/OpenAI client, so the SDKs'
# default env-var credential resolution (ANTHROPIC_API_KEY, OPENAI_API_KEY)
# picks up values from backend/.env.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.auth import router as auth_router  # noqa: E402
from app.api.chat import router as chat_router  # noqa: E402
from app.api.tokens import router as tokens_router  # noqa: E402
from app.config import settings  # noqa: E402
from app.core.audit import AuditLogMiddleware  # noqa: E402
from app.core.rate_limit import RateLimitMiddleware  # noqa: E402

app = FastAPI(title="OmniAI Enterprise Platform")

# Starlette runs middleware in the reverse order it's added (last added =
# outermost), so CORS is added last to sit outermost and handle preflight
# OPTIONS requests before rate limiting or audit logging see them.
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module 1: Multi-LLM Chat
app.include_router(chat_router, prefix="/api")
app.include_router(tokens_router, prefix="/api")

# Cross-cutting: Security (JWT / OAuth2 / RBAC)
app.include_router(auth_router, prefix="/api")

# Further modules register themselves here as they're built — see
# backend/app/modules/<name>/router.py for each.
from app.modules.rag.router import router as rag_router  # noqa: E402
from app.modules.data_analyst.router import router as data_analyst_router  # noqa: E402
from app.modules.research_assistant.router import router as research_router  # noqa: E402
from app.modules.forecasting.router import router as forecasting_router  # noqa: E402
from app.modules.recommendations.router import router as recommendations_router  # noqa: E402
from app.modules.coding_assistant.router import router as coding_router  # noqa: E402
from app.modules.vision.router import router as vision_router  # noqa: E402
from app.modules.speech.router import router as speech_router  # noqa: E402
from app.modules.browser_agent.router import router as browser_agent_router  # noqa: E402
from app.modules.finetune.router import router as finetune_router  # noqa: E402
from app.modules.mlops.router import router as mlops_router  # noqa: E402
from app.modules.image_gen.router import router as image_gen_router  # noqa: E402
from app.modules.video_gen.router import router as video_gen_router  # noqa: E402
from app.modules.distributed.router import router as distributed_router  # noqa: E402

app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(data_analyst_router, prefix="/api/data-analyst", tags=["data-analyst"])
app.include_router(research_router, prefix="/api/research", tags=["research"])
app.include_router(forecasting_router, prefix="/api/forecasting", tags=["forecasting"])
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(coding_router, prefix="/api/coding", tags=["coding"])
app.include_router(vision_router, prefix="/api/vision", tags=["vision"])
app.include_router(speech_router, prefix="/api/speech", tags=["speech"])
app.include_router(browser_agent_router, prefix="/api/browser-agent", tags=["browser-agent"])
app.include_router(finetune_router, prefix="/api/finetune", tags=["finetune"])
app.include_router(mlops_router, prefix="/api/mlops", tags=["mlops"])
app.include_router(image_gen_router, prefix="/api/image-gen", tags=["image-gen"])
app.include_router(video_gen_router, prefix="/api/video-gen", tags=["video-gen"])
app.include_router(distributed_router, prefix="/api/distributed", tags=["distributed"])


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
