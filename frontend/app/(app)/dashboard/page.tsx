"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/backend";
import { MODULES } from "@/lib/modules";

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
