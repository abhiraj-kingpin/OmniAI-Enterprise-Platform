# Backend — OmniAI Enterprise Platform

FastAPI service implementing all 16 OmniAI modules. See the root `README.md` for the platform-level picture; this file covers backend code layout, setup, and module-specific dependencies.

## Layout

```
app/
  main.py              Application assembly: middleware, exception handlers, routers
  config.py            Settings (environment-driven, see root README's Configuration section)
  core/                 Cross-cutting concerns, used by every module:
    security.py           JWT issuing/verification, OAuth2 dependency
    rbac.py                Role-based access control
    users.py               User store (in-memory demo implementation)
    rate_limit.py           Per-IP rate limiting middleware
    audit.py                Request audit logging middleware
    exceptions.py           Domain exceptions + global error handlers
    logging.py               Logging configuration
    jobs.py                   Generic background-job tracker
    env.py                    Loads .env before module imports that need it at import time
  api/                  Chat and auth routes (not module-scoped)
  providers/             The AI service layer — see below
  modules/
    rag/                data_analyst/       research_assistant/
    forecasting/         recommendations/    coding_assistant/
    vision/               speech/             browser_agent/
    finetune/             mlops/              image_gen/
    video_gen/            distributed/
tests/                 pytest suite
```

Each module directory is self-contained: `schemas.py` (Pydantic request/response models), one or more logic modules, and `router.py` (the `APIRouter` `main.py` mounts under `/api/<module>`).

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # then set AI_PROVIDER and that provider's API key — see AI Service Layer below
uvicorn app.main:app --reload --port 8000
```

The API listens on `http://localhost:8000`. Check `GET /api/health`. Interactive docs at `/docs`.

For development (tests, linting), install `requirements-dev.txt` instead — it pulls in `requirements.txt` plus `pytest`, `httpx2`, and `ruff`:

```bash
pip install -r requirements-dev.txt
pytest                # 21 tests, no external services required
ruff check .           # lint
```

### Module-specific local dependencies

| Requirement | Module(s) | Setup |
|---|---|---|
| Chromium | Browser Agent | `playwright install chromium` |
| Redis server | Distributed (Celery integration) | any local or containerized Redis reachable at `REDIS_URL` |
| Kafka broker | Distributed (Kafka example) | see `docker-compose.yml`'s `kafka` service |
| Java runtime | Distributed (Spark example) | a JDK on `PATH` |
| PyTorch + Transformers + Diffusers + PEFT | Fine-Tuning, Image/Video Generation | included in `requirements.txt`; on Windows, verify these import successfully in your environment (`python -c "import torch"`) — see the platform note below |

OCR (used by RAG's image ingestion and the Vision module) runs on `rapidocr-onnxruntime`, an ONNX Runtime-based engine — no external OCR binary required.

## Windows platform note

`rapidocr-onnxruntime` depends on `opencv-python`, which conflicts with this project's pinned `opencv-python-headless<5` (both packages install into the same `cv2` namespace; opencv 5.x also drops the Haar cascade API the Vision module uses). If reinstalling dependencies on Windows, confirm afterward that:

```bash
python -c "import cv2; print(cv2.__version__, hasattr(cv2, 'CascadeClassifier'))"
```

prints a 4.x version and `True`. If it doesn't, `pip uninstall opencv-python` and reinstall `opencv-python-headless<5`.

Some Windows security policies (Smart App Control) block unsigned compiled extensions used by parts of this stack (historically PyTorch; more narrowly, scikit-learn's compiled metrics module, pulled in transitively by `transformers`). If Fine-Tuning or Image/Video Generation fail to import their dependencies, check `Microsoft-Windows-CodeIntegrity/Operational` in Event Viewer, and note that `scikit-learn` is not a required dependency of this project — `transformers` treats it as optional and degrades gracefully if it's absent (`pip uninstall scikit-learn`).

`GET /api/distributed/components` reports live availability for Ray, Celery/Redis, Kafka, Spark, ONNX Runtime, and GPU-dependent inference engines (vLLM/TensorRT-LLM) rather than a static claim — use it to check what's actually reachable in a given environment.

## AI service layer

Every module that calls an LLM goes through `app/providers/`, not a provider SDK directly — no file outside `app/providers/` imports `anthropic`, `openai`, or `google.genai`. Switching providers is an environment variable, not a code change.

```
app/providers/
  types.py          Provider-agnostic data shapes (AIMessage, ToolCall, AIResponse, ...)
  base.py            The AIProvider interface: complete(), stream(), count_tokens()
  exceptions.py       ProviderUnavailableError
  factory.py           get_provider(name=None, model=None) — the only place a
                         provider name maps to a concrete class
  anthropic_provider.py
  openai_provider.py
  gemini_provider.py
  ollama_provider.py    Reuses openai_provider.py's translation logic wholesale
                          against Ollama's own OpenAI-compatible endpoint
```

### Selecting a provider

Set `AI_PROVIDER` in `.env` to `anthropic`, `openai`, `gemini`, or `ollama`, plus that provider's API key (Ollama needs no key — just a running local server):

```bash
# Anthropic (default)
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=...

# Ollama (local — run `ollama serve` and `ollama pull llama3.1` first)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.1
```

`AI_PROVIDER` is the default for every module except **Multi-LLM Chat**, which lets a user pick a provider per conversation (the `provider` field on `POST /api/chat/stream` and `POST /api/tokens/count` — see `ChatRequest`/`TokenCountRequest` in `app/schemas.py`) — an explicit choice there overrides the environment default for that request only. `get_provider()` in `factory.py` handles both: called with no arguments, it reads `AI_PROVIDER`; called with a name, it uses that name instead.

An unknown provider name or a missing API key raises `ProviderUnavailableError` (HTTP 503) before any network call is made, with a message naming exactly what's misconfigured — not a stack trace from deep inside a provider SDK.

### Provider capability notes

- **Tool calling**: normalized in `types.ToolDefinition`/`ToolCall`/`ToolResult`; each adapter translates to its own wire format (Anthropic's content blocks, OpenAI's `tool_calls`, Gemini's `FunctionCall`/`FunctionResponse`). Ollama's support depends on the locally pulled model.
- **Vision**: `AIMessage.content` accepts a list of `TextPart`/`ImagePart` for any provider; whether a given model actually has vision depends on the model, not this layer.
- **Structured output** (`response_schema` on `complete()`): uses each provider's native JSON-schema-constrained output where one exists (Anthropic, OpenAI strict mode, Gemini). Not exercised for Ollama — support varies by model.
- **Token counting**: exact via a real endpoint for Anthropic and Gemini; a local `tiktoken` estimate for OpenAI and Ollama (documented as approximate in `openai_provider.py`).

Gemini and Ollama were implemented and their message/tool-construction logic verified directly (see `app/providers/gemini_provider.py`'s helpers), but not exercised against a live API in this environment — no Gemini key or local Ollama server was available here. Anthropic and OpenAI were verified against their real APIs (requests reach the provider and fail only on this repo's placeholder key, the same signal used throughout this project).

## Extending

- New module: create `app/modules/<name>/{schemas,router}.py`, add it to `_MODULE_ROUTERS` in `app/main.py`.
- New AI provider: implement `AIProvider` (`app/providers/base.py`) in a new `app/providers/<name>_provider.py`, register it in `factory.py`'s `_PROVIDERS` dict.
- New background job (start/poll pattern): use `app/core/jobs.JobStore`, following `app/modules/finetune/jobs.py` or `app/modules/image_gen/jobs.py`.
- Protecting a route: `Depends(require_role(Role.ADMIN))` from `app.core.rbac` (see `app/api/auth.py`).
- New error type: subclass `app.core.exceptions.AppError` with a `status_code` and `code`.
