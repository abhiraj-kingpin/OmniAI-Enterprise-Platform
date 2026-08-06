# OmniAI Enterprise Platform

A modular AI platform combining LLM chat, retrieval-augmented generation, computer vision, speech processing, forecasting, recommendations, and MLOps tooling behind a single FastAPI backend and Next.js frontend.

## System Architecture

```
┌─────────────────────┐        ┌──────────────────────────────────────┐
│   Next.js Frontend   │  HTTP  │            FastAPI Backend            │
│   (17 routes, TS)    │ ─────► │  Auth · Rate Limiting · Audit Logging │
└─────────────────────┘        │  ┌──────────────────────────────────┐  │
                                │  │  16 module routers under /api/*  │  │
                                │  └──────────────────────────────────┘  │
                                └──────────────┬─────────────────────────┘
                                               │
                  ┌────────────────────────────┼────────────────────────────┐
                  ▼                            ▼                            ▼
          Anthropic / OpenAI          ONNX Runtime (local)          Redis · Kafka · Ray
          (chat, agents, LoRA)   (embeddings, OCR, ASR, vision)   (Celery, streaming, distributed)
```

Every module is a self-contained package under `backend/app/modules/<name>/` with its own request/response schemas, business logic, and router; `app/main.py` mounts each under `/api/<name>`. Cross-cutting concerns (authentication, rate limiting, audit logging, structured error handling) are implemented once as middleware and exception handlers, not per module.

## Features

- JWT/OAuth2 authentication with role-based access control
- Per-IP rate limiting and structured audit logging on every request
- Streaming chat with tool use across two LLM providers
- Hybrid (BM25 + dense) retrieval with cross-encoder reranking for RAG
- Local, GPU-free inference for embeddings, OCR, speech-to-text, and vision via ONNX Runtime
- Background job tracking for long-running work (fine-tuning, image generation)
- Live capability reporting for distributed-systems components (Ray, Celery, Kafka, Spark)

## AI Modules

| Module | Path prefix | Summary |
|---|---|---|
| Multi-LLM Chat | `/api/chat`, `/api/tokens` | Streaming chat across Anthropic and OpenAI, tool-use loop, token counting |
| Enterprise RAG | `/api/rag` | Document ingestion (PDF/DOCX/PPTX/XLSX/images), hybrid search, cross-encoder reranking, cited Q&A |
| Computer Vision | `/api/vision` | Face/edge detection (OpenCV), CLIP-based image search |
| Speech AI | `/api/speech` | Text-to-speech and speech-to-text (Whisper via CTranslate2) |
| Recommendation System | `/api/recommendations` | Matrix-factorization collaborative filtering |
| Forecasting | `/api/forecasting` | ETS/ARIMA time-series forecasting |
| AI Coding Assistant | `/api/coding` | AST-based static analysis, GitHub repository indexing and search |
| AI Data Analyst | `/api/data-analyst` | CSV/Excel ingestion, SQL execution via DuckDB, chart generation |
| AI Research Assistant | `/api/research` | arXiv search with a multi-step search agent |
| AI Image Generator | `/api/image-gen` | Stable Diffusion text-to-image, inpainting, ControlNet, LoRA-adapted generation |
| AI Video Generator | `/api/video-gen` | Optical-flow frame interpolation; diffusion text-to-video |
| Autonomous Browser Agent | `/api/browser-agent` | Headless-browser automation (Playwright) driven by an LLM tool loop |
| Fine-Tuning | `/api/finetune` | LoRA fine-tuning (PEFT + Transformers) with background job tracking |
| MLOps Dashboard | `/api/mlops` | Experiment tracking (MLflow) |
| Distributed AI Infrastructure | `/api/distributed` | Ray task execution, Celery/Redis task queue, live component health |
| Security | cross-cutting | JWT/OAuth2, RBAC, rate limiting, audit logging |

## Technology Stack

**Backend** — FastAPI, Pydantic v2, PyJWT, bcrypt, Anthropic SDK, OpenAI SDK, ONNX Runtime, `fastembed`, `faster-whisper`, `rapidocr-onnxruntime`, OpenCV, DuckDB, pandas, statsmodels, PyTorch + Transformers + PEFT + Diffusers, Ray, Celery, kafka-python, PySpark, MLflow, Playwright.

**Frontend** — Next.js 15 (App Router), TypeScript (strict mode), Tailwind CSS. The landing page additionally uses Framer Motion, GSAP (ScrollTrigger), Three.js, Lenis (smooth scroll), and Lucide icons — see `frontend/README.md`'s Landing page section.

**Infrastructure** — Docker, Kubernetes manifests, Airflow DAG, DVC pipeline, GitHub Actions CI.

There is no relational database in this stack — module state is either stateless per request, held in local files under `backend/data/` (uploads, model outputs, the MLflow SQLite database), or delegated to Redis for the task queue.

## Installation

Prerequisites: Python 3.12+, Node.js 18+, and (optionally) Docker.

```bash
git clone https://github.com/abhiraj-kingpin/OmniAI-Enterprise-Platform.git
cd OmniAI-Enterprise-Platform

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env            # then set ANTHROPIC_API_KEY / OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

The frontend runs at `http://localhost:3000` and expects the backend at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_BASE`). See `backend/README.md` for module-specific setup and `frontend/README.md` for the frontend's structure.

## Configuration

Backend configuration is managed by `app/config.py` (Pydantic Settings), loaded from `backend/.env`.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes, for Claude-backed modules | — | Anthropic API key |
| `OPENAI_API_KEY` | Yes, for OpenAI-backed chat | — | OpenAI API key |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins, JSON array |
| `ENVIRONMENT` | No | `development` | `development` or `production`; controls error detail exposure |
| `LOG_LEVEL` | No | `INFO` | Python logging level |
| `JWT_SECRET` | Recommended in production | random per process start | HMAC signing secret for access tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token lifetime, minutes |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | Requests per client IP per minute |
| `DATA_DIR` | No | `data` | Local storage root (uploads, logs, model outputs) |
| `REDIS_URL` | Yes, for the Distributed module's Celery integration | `redis://localhost:6379/0` | Celery broker/result backend |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes, for the Kafka example producer/consumer | `localhost:9092` | Kafka broker address |
| `NEXT_PUBLIC_API_BASE` (frontend) | No | `http://localhost:8000` | Backend base URL |

If `JWT_SECRET` is left unset, a random secret is generated on process start — tokens issued before a restart stop validating. Set it explicitly for any deployment that needs to survive a restart.

## API Documentation

Interactive OpenAPI documentation is served by FastAPI at `/docs` (Swagger UI) and `/redoc` when the backend is running.

All API error responses use a consistent envelope:

```json
{"error": {"code": "not_found", "message": "Job 'xyz' not found"}}
```

Validation errors additionally include a `details` array with per-field errors. See `backend/app/core/exceptions.py`.

Authentication follows the OAuth2 password flow:

```
POST /api/auth/token       — obtain an access token (form: username, password)
GET  /api/auth/me          — current user
GET  /api/auth/admin-only  — example admin-only route
```

## Project Structure

```
backend/
  app/
    main.py              Application assembly: middleware, exception handlers, routers
    config.py             Settings (environment-driven)
    core/                 Auth, RBAC, rate limiting, audit logging, structured errors, job store
    api/                  Chat and auth routes
    providers/             LLM provider abstraction (Anthropic, OpenAI)
    modules/               One package per AI module (see table above)
  tests/                  pytest suite
frontend/
  app/                    page.tsx is the landing page; (app)/ holds the
                            Sidebar-wrapped dashboard and 15 module pages
  components/             Shared UI components; landing/ holds the landing
                            page's sections
  lib/                    API client, the shared module list, types
infra/
  k8s/                    Kubernetes manifests
  airflow/                Orchestration DAG
docker-compose.yml        Full local stack (backend, frontend, Redis, Kafka, MLflow UI)
dvc.yaml                  Data/model versioning pipeline
.github/workflows/ci.yml  Lint, test, build
```

## Deployment

### Docker

```bash
docker compose up --build
```

Brings up the backend, frontend, Redis, Kafka (with Zookeeper), and an MLflow UI. Set secrets in `backend/.env` before starting — `docker-compose.yml` loads it via `env_file`.

### Kubernetes

Manifests in `infra/k8s/` define a Deployment, Service, Ingress, and HorizontalPodAutoscaler for the backend. Apply with:

```bash
kubectl apply -f infra/k8s/
```

GPU-dependent modules (image/video generation at scale, LoRA training) should run on a node pool with `nvidia.com/gpu` scheduled — see the manifest for the resource request shape.

## Security

- **Authentication**: JWT (PyJWT) issued via the OAuth2 password grant; bcrypt password hashing.
- **Authorization**: Role-based access control via `require_role(...)` dependencies.
- **Rate limiting**: Fixed-window, per-client-IP, in-memory (single-process; swap for a Redis-backed limiter behind more than one worker).
- **Audit logging**: Every request logged as JSON (actor, method, path, status, latency) to a rotating file.
- **Secrets**: Provided via environment variables / `.env`, never committed. `backend/.env` is gitignored.
- **Demo accounts**: Two seeded accounts (`admin`/`admin123`, `demo`/`demo123`) exist for local development only — replace the in-memory user store (`app/core/users.py`) with a real identity provider before any non-local deployment.

## Performance

- LLM calls stream by default to minimize perceived latency.
- Local inference (embeddings, OCR, ASR, vision) runs on ONNX Runtime, avoiding network round-trips for those operations.
- Long-running work (fine-tuning, image generation) runs on background threads with a poll-based status API rather than blocking the request.
- `lru_cache` is used to avoid reloading local models on every request.

## Scaling

- The backend is stateless aside from in-memory rate-limit counters and the demo user store — both called out above as the first things to externalize (Redis, a real database) before running more than one instance.
- Celery workers scale horizontally against the shared Redis broker.
- Ray provides local multi-core parallelism; point it at a Ray cluster address for multi-node scaling without code changes.

## Development Guide

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
ruff check .          # lint
pytest                # test suite (21 tests, no external services required)

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Contributing

1. Branch from `main`.
2. Keep changes scoped to one module or concern per pull request.
3. Run the backend lint/test suite and the frontend lint/typecheck/build before opening a PR.
4. Follow the existing module structure (`schemas.py`, logic module(s), `router.py`) for new modules.

## License

No license file is currently included in this repository; all rights reserved by the copyright holder unless a license is added.
