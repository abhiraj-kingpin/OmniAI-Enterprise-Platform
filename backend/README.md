# Backend — OmniAI Enterprise Platform

FastAPI service powering all 16 OmniAI modules. See the root `README.md`
for the full picture (what's genuinely verified vs. honestly blocked, and
why); this file is about the backend's code layout.

## Layout

```
app/
  main.py              # mounts every module router + cross-cutting middleware
  config.py            # Settings (env-driven)
  core/                # Security: JWT, RBAC, rate limiting, audit logging
  api/                 # Module 1 (chat) + auth routes
  providers/           # Module 1's LLM provider abstraction
  modules/
    rag/                data_analyst/       research_assistant/
    forecasting/        recommendations/    coding_assistant/
    vision/              speech/            browser_agent/
    finetune/            mlops/             image_gen/
    video_gen/           distributed/
tests/                 # pytest suite — auth/RBAC, AST parsing, chunking, MF
```

Each module directory is self-contained: `schemas.py` (Pydantic models),
one or more logic modules, and `router.py` (the FastAPI `APIRouter`
`main.py` mounts under `/api/<module>`).

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill in ANTHROPIC_API_KEY (required for most modules)
uvicorn app.main:app --reload --port 8000
```

The API listens on `http://localhost:8000`. Check `GET /api/health`.

Some modules need extra local setup beyond `pip install`:

| Need | Module(s) | Install |
|---|---|---|
| Chromium browser | Browser Agent | `playwright install chromium` |
| Redis server | Distributed (Celery) | see below |
| Java runtime | Distributed (Spark) | `winget install Microsoft.OpenJDK.21` |

OCR (RAG image ingest, Vision) needs no separate install — it runs on
`rapidocr-onnxruntime`, pulled in by `pip install -r requirements.txt`, not
the Tesseract binary. See app/modules/vision/ocr.py for why.

Run the test suite: `pytest` (21 tests, all dependency-free — no API key
or external service needed).

## A note on what's real vs. blocked

Every module was built and exercised against this exact machine — not just
written and assumed to work. Two constraints turned out to matter more than
GPU availability:

1. **Windows Smart App Control blocks PyTorch's DLLs** (unsigned to
   "Enterprise" level). RAG, Vision, and Speech route around this with
   ONNX-based equivalents (`fastembed`, `faster-whisper`, `opencv` +
   `onnxruntime`) that pass the same policy and stay fully local. Fine-Tuning
   and Image/Video *generation* (diffusion) have no such escape hatch — they
   contain real, correct `transformers`/`peft`/`diffusers` code, gated by an
   `check_available()` that explains why it can't run here rather than
   failing confusingly. This is a Windows-host policy, not a platform
   limitation — the Linux container in this dir's `Dockerfile` doesn't have
   it.
2. **No GPU on this machine at all** — separate from (1). vLLM and
   TensorRT-LLM need one; that's a hardware fact this environment can't work
   around either way.

`GET /api/distributed/components` reports live, per-component availability
rather than a static claim.

## Extending

- New provider (chat): implement `LLMProvider.stream_chat`, register in
  `app/providers/registry.py`.
- New module: create `app/modules/<name>/{schemas,router}.py`, mount it in
  `app/main.py`.
- Protecting a route: `Depends(require_role(Role.ADMIN))` from
  `app.core.rbac` (see `app/api/auth.py` for the pattern).
