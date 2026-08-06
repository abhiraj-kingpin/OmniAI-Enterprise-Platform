# Frontend — OmniAI Enterprise Platform

Next.js (App Router) + TypeScript + Tailwind UI for all 16 OmniAI modules.

## Layout

```
app/
  layout.tsx        Sidebar + content shell
  page.tsx           Dashboard — links to every module
  chat/               rag/                data-analyst/
  research/           forecasting/        recommendations/
  coding/              vision/              speech/
  browser-agent/       finetune/            mlops/
  image-gen/            video-gen/           distributed/
components/
  Sidebar.tsx         Navigation
  ui.tsx               Shared Card/Button/FileInput/etc. components
  Chat.tsx, MessageBubble.tsx, ModelSelector.tsx   Chat module components
lib/
  backend.ts          apiGet/apiPost/apiUpload helpers, shared error handling
  api.ts, types.ts     Chat module's SSE streaming client
```

Each module page is a client component calling the backend directly via `lib/backend.ts` — there is no separate state management library; component-local `useState` is sufficient given each page owns one module's UI independently.

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Runs on `http://localhost:3000`. Requires the backend running on `http://localhost:8000` (see `../backend/README.md`), or set `NEXT_PUBLIC_API_BASE` in `.env.local` to point elsewhere.

## Scripts

```bash
npm run dev         # development server
npm run build        # production build
npm run start         # serve a production build
npm run lint            # ESLint (eslint-config-next)
npm run typecheck        # tsc --noEmit
```

## Error handling

`lib/backend.ts`'s `handle()` parses the backend's structured error envelope (`{"error": {"code", "message"}}`, see `backend/app/core/exceptions.py`) and throws an `ApiError` with the human-readable message, so module pages can surface a clean error string without knowing the wire format.
