# Frontend — OmniAI Enterprise Platform

Next.js (App Router) + TypeScript + Tailwind UI for all 16 OmniAI modules.

## Layout

```
app/
  layout.tsx        # Sidebar + content shell
  page.tsx           # Dashboard — links to every module
  chat/               rag/                data-analyst/
  research/           forecasting/        recommendations/
  coding/             vision/             speech/
  browser-agent/      finetune/           mlops/
  image-gen/          video-gen/          distributed/
components/
  Sidebar.tsx        # Nav
  ui.tsx              # Shared Card/Button/FileInput/etc.
  Chat.tsx, MessageBubble.tsx, ModelSelector.tsx   # Module 1
lib/
  backend.ts         # apiGet/apiPost/apiUpload helpers
  api.ts, types.ts    # Module 1's SSE streaming client
```

Each module page is a client component calling the backend directly via
`lib/backend.ts` — no separate state management library, just `useState`.

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Runs on `http://localhost:3000`. Requires the backend running on
`http://localhost:8000` (see `../backend/README.md`), or set
`NEXT_PUBLIC_API_BASE` in `.env.local` to point elsewhere.

Verified: `tsc --noEmit`, `next build`, and a real headless-Chromium pass
over every route (zero console errors) — see the root `README.md` for the
full verification log.
