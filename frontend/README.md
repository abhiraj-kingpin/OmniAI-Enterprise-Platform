# Frontend — OmniAI Enterprise Platform

Next.js (App Router) + TypeScript + Tailwind UI: a marketing landing page at `/`, and the 16-module internal app behind it.

## Layout

```
app/
  layout.tsx           Root layout: html/body shell only
  page.tsx               The landing page ("/") — see Landing page below
  (app)/
    layout.tsx            Sidebar + content shell, wraps every route below
    dashboard/              Module grid — what "Launch app" links to
    chat/                    rag/                data-analyst/
    research/                forecasting/        recommendations/
    coding/                   vision/              speech/
    browser-agent/            finetune/            mlops/
    image-gen/                 video-gen/           distributed/
components/
  Sidebar.tsx           Internal app navigation
  ui.tsx                 Shared Card/Button/FileInput/etc. components
  Chat.tsx, MessageBubble.tsx, ModelSelector.tsx   Chat module components
  landing/                Landing page sections (see below)
lib/
  backend.ts            apiGet/apiPost/apiUpload helpers, shared error handling
  modules.ts              The 16-module list — single source shared by the
                            dashboard, Sidebar, and the landing page's Features section
  api.ts, types.ts         Chat module's SSE streaming client; shared API types
```

`(app)` is a route group — it doesn't appear in the URL, it just scopes the Sidebar layout to every module page and the dashboard, keeping the landing page at `/` free of it. Each module page is a client component calling the backend directly via `lib/backend.ts` — there is no separate state management library; component-local `useState` is sufficient given each page owns one module's UI independently.

## Landing page

`app/page.tsx` assembles `components/landing/*` into the sections below. All content is either genuinely accurate about this project (module list, stats, deployment options) or clearly a design/decoration element (the node-network visual, the aurora background) — there are no fabricated customer logos, testimonials, or pricing tiers, since this project has neither customers nor a commercial pricing model.

| Component | Role |
|---|---|
| `Navbar` | Sticky glass nav, scroll-progress bar, mobile menu |
| `Hero` | Full-viewport intro, mouse-parallax 3D scene, staggered headline reveal |
| `HeroScene` | The 3D node-network visual — plain Three.js, not React Three Fiber (see below) |
| `BuiltWith` | Real technology stack, not a fabricated "trusted by" customer list |
| `Features` | The 16-module grid, sourced from `lib/modules.ts` |
| `ArchitectureViz` | Scroll-scrubbed SVG diagram (GSAP ScrollTrigger) of the real request flow |
| `DashboardPreview` | A styled preview of the actual `/dashboard`, not a separate mockup |
| `Stats` | Real counts (modules, routes, tests, providers) — no invented metrics |
| `GetStarted` | Deployment options (Local / Docker / Kubernetes) in place of pricing tiers |
| `FAQ` | Accurate answers about API key requirements, local vs. hosted inference, auth |
| `Reveal`, `MagneticButton`, `Counter`, `AuroraBackground`, `SmoothScroll` | Shared motion primitives used across the sections above |

**Why plain Three.js, not `@react-three/fiber`:** R3F v8 (the last major supporting React 18) implements its own React reconciler targeting React 18.0–18.2 internals, and throws (`ReactCurrentOwner` undefined) against React 18.3, which this project is pinned to; R3F v9 requires React 19. The hero scene is simple enough that a plain `WebGLRenderer` driven by `requestAnimationFrame` inside a `useEffect` avoids that version coupling entirely rather than forcing a project-wide React 19 upgrade for one component.

**Lenis + GSAP ScrollTrigger:** `SmoothScroll.tsx` drives Lenis off GSAP's own ticker (`gsap.ticker.add`) rather than a separate `requestAnimationFrame` loop, and calls `ScrollTrigger.update()` on Lenis's `scroll` event — the standard integration pattern, needed because two independent RAF loops would otherwise drift out of sync and desync ScrollTrigger's progress from what's actually on screen. `ArchitectureViz`'s scrub animation deliberately does not use ScrollTrigger's `pin: true` — pinning correctly under Lenis's virtual scroll needs a scroller-proxy configuration this page doesn't set up, and an unpinned scrub achieves the same "animation progress tracks scroll position" effect without that dependency.

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

## Known issue

`npm audit` reports 3 high-severity advisories in `postcss`/`sharp`, both bundled transitively by Next.js 15 itself. They're fixable only by upgrading to Next 16 (a breaking change across all 18 routes), which hasn't been done here — see the root README's Technology Stack section.
