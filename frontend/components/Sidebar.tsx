"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const MODULES = [
  { href: "/", label: "Dashboard" },
  { href: "/chat", label: "Multi-LLM Chat" },
  { href: "/rag", label: "Enterprise RAG" },
  { href: "/vision", label: "Computer Vision" },
  { href: "/speech", label: "Speech AI" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/forecasting", label: "Forecasting" },
  { href: "/coding", label: "Coding Assistant" },
  { href: "/data-analyst", label: "Data Analyst" },
  { href: "/research", label: "Research Assistant" },
  { href: "/image-gen", label: "Image Generator" },
  { href: "/video-gen", label: "Video Generator" },
  { href: "/browser-agent", label: "Browser Agent" },
  { href: "/finetune", label: "Fine-Tuning" },
  { href: "/mlops", label: "MLOps Dashboard" },
  { href: "/distributed", label: "Distributed Infra" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex h-screen w-56 shrink-0 flex-col border-r border-neutral-800 bg-neutral-950 p-3">
      <div className="mb-4 px-2 py-2">
        <p className="text-sm font-bold text-neutral-100">OmniAI</p>
        <p className="text-[11px] text-neutral-500">Enterprise Platform</p>
      </div>
      <div className="flex-1 space-y-0.5 overflow-y-auto">
        {MODULES.map((m) => {
          const active = pathname === m.href;
          return (
            <Link
              key={m.href}
              href={m.href}
              className={`block rounded-md px-3 py-1.5 text-[13px] transition-colors ${
                active
                  ? "bg-blue-600/20 text-blue-300"
                  : "text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
              }`}
            >
              {m.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
