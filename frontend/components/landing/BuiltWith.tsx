"use client";

import Reveal from "./Reveal";

const STACK = [
  "Anthropic Claude",
  "OpenAI",
  "FastAPI",
  "Next.js 15",
  "PyTorch",
  "ONNX Runtime",
  "DuckDB",
  "Ray",
  "MLflow",
  "Playwright",
];

export default function BuiltWith() {
  return (
    <section id="built-with" className="border-y border-white/5 bg-white/[0.02] py-12">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal>
          <p className="text-center text-xs uppercase tracking-[0.2em] text-neutral-500">
            Built on real, production-grade infrastructure
          </p>
        </Reveal>
        <Reveal delay={0.1}>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {STACK.map((name) => (
              <span key={name} className="text-sm font-medium text-neutral-500 transition-colors hover:text-neutral-300">
                {name}
              </span>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
