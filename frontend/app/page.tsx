"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/backend";

interface ModuleCard {
  href: string;
  name: string;
  description: string;
  skills: string[];
}

const MODULES: ModuleCard[] = [
  { href: "/chat", name: "Multi-LLM Chat", description: "Streaming chat across Anthropic and OpenAI, with function calling and memory.", skills: ["LLMs", "Function Calling", "Streaming"] },
  { href: "/rag", name: "Enterprise RAG", description: "Upload documents, hybrid BM25 + dense search, cross-encoder reranking, cited Q&A.", skills: ["Hybrid Search", "Embeddings", "Re-ranking"] },
  { href: "/vision", name: "Computer Vision", description: "Face/edge detection, OCR, CLIP-based product search, Claude vision captioning.", skills: ["OpenCV", "CLIP", "OCR"] },
  { href: "/speech", name: "Speech AI", description: "Whisper transcription, offline text-to-speech, speaker comparison, emotion analysis.", skills: ["Whisper", "TTS", "Speaker ID"] },
  { href: "/recommendations", name: "Recommendation System", description: "Matrix factorization collaborative filtering with candidate ranking.", skills: ["Collaborative Filtering", "Embeddings"] },
  { href: "/forecasting", name: "Forecasting", description: "Time series forecasting with ETS/ARIMA and engineered lag features.", skills: ["Time Series", "Feature Engineering"] },
  { href: "/coding", name: "AI Coding Assistant", description: "AST analysis, GitHub repo indexing and search, code generation and tests.", skills: ["AST Parsing", "GitHub API"] },
  { href: "/data-analyst", name: "AI Data Analyst", description: "Upload spreadsheets, run real SQL via DuckDB, auto-generate charts and insights.", skills: ["Pandas", "SQL", "Charts"] },
  { href: "/research", name: "AI Research Assistant", description: "arXiv search, a self-directed multi-search agent, citation extraction.", skills: ["Agents", "Citation Extraction"] },
  { href: "/image-gen", name: "AI Image Generator", description: "Real Stable Diffusion pipeline (text-to-image, LoRA, inpainting, ControlNet).", skills: ["Diffusion Models", "LoRA"] },
  { href: "/video-gen", name: "AI Video Generator", description: "Real optical-flow frame interpolation, plus a text-to-video diffusion pipeline.", skills: ["Frame Interpolation", "Diffusion"] },
  { href: "/browser-agent", name: "Autonomous Browser Agent", description: "Claude drives a real headless Chromium browser via Playwright to complete tasks.", skills: ["Playwright", "Planning"] },
  { href: "/finetune", name: "Fine-Tuning", description: "Real LoRA fine-tuning pipeline (PEFT + Transformers) with job tracking.", skills: ["LoRA", "PEFT"] },
  { href: "/mlops", name: "MLOps Dashboard", description: "Real MLflow experiment tracking, plus Docker/K8s/Airflow/DVC/CI artifacts.", skills: ["MLflow", "CI/CD"] },
  { href: "/distributed", name: "Distributed AI Infrastructure", description: "Live Ray cluster, Celery/Redis, Kafka, Spark — honest per-component status.", skills: ["Ray", "Kafka", "Celery"] },
];

export default function Dashboard() {
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");

  useEffect(() => {
    apiGet<{ status: string }>("/api/health")
      .then(() => setHealth("up"))
      .catch(() => setHealth("down"));
  }, []);

  return (
    <div className="mx-auto max-w-5xl p-8">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">OmniAI Enterprise Platform</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Sixteen modules, one backend. Pick one from the sidebar or below.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-neutral-800 px-3 py-1 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              health === "up" ? "bg-green-500" : health === "down" ? "bg-red-500" : "bg-yellow-500"
            }`}
          />
          Backend {health === "checking" ? "checking..." : health}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map((m) => (
          <Link
            key={m.href}
            href={m.href}
            className="rounded-xl border border-neutral-800 bg-neutral-900/50 p-4 transition-colors hover:border-blue-600 hover:bg-neutral-900"
          >
            <h2 className="text-sm font-semibold text-neutral-100">{m.name}</h2>
            <p className="mt-1.5 text-xs leading-relaxed text-neutral-500">{m.description}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {m.skills.map((s) => (
                <span
                  key={s}
                  className="rounded-full bg-neutral-800 px-2 py-0.5 text-[10px] text-neutral-400"
                >
                  {s}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
