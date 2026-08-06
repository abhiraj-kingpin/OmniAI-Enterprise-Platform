"use client";

import { motion } from "framer-motion";
import {
  MessagesSquare,
  Search,
  Eye,
  Mic,
  Sparkles,
  TrendingUp,
  Code2,
  BarChart3,
  BookOpen,
  Image as ImageIcon,
  Film,
  Globe,
  SlidersHorizontal,
  Gauge,
  Network,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import { MODULES } from "@/lib/modules";
import Reveal from "./Reveal";

const ICONS: LucideIcon[] = [
  MessagesSquare,
  Search,
  Eye,
  Mic,
  Sparkles,
  TrendingUp,
  Code2,
  BarChart3,
  BookOpen,
  ImageIcon,
  Film,
  Globe,
  SlidersHorizontal,
  Gauge,
  Network,
];

export default function Features() {
  return (
    <section id="features" className="relative py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Sixteen modules. One backend.
          </h2>
          <p className="mt-4 text-balance text-lg text-neutral-400">
            Every module is a self-contained FastAPI router with its own schemas and logic — mounted
            under one app, sharing one auth layer.
          </p>
        </Reveal>

        <div className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod, i) => {
            const Icon = ICONS[i % ICONS.length];
            return (
              <Reveal key={mod.href} delay={(i % 3) * 0.08}>
                <motion.a
                  href={mod.href}
                  whileHover={{ y: -4 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="group relative block h-full overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-sm transition-colors hover:border-blue-500/40 hover:bg-white/[0.06]"
                >
                  <div
                    className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                    style={{
                      background:
                        "radial-gradient(400px circle at var(--x, 50%) var(--y, 50%), rgba(59,130,246,0.12), transparent 60%)",
                    }}
                  />
                  <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-blue-300">
                    <Icon size={18} />
                  </div>
                  <h3 className="relative mt-4 text-sm font-semibold text-white">{mod.name}</h3>
                  <p className="relative mt-2 text-sm leading-relaxed text-neutral-400">
                    {mod.description}
                  </p>
                  <div className="relative mt-4 flex flex-wrap gap-1.5">
                    {mod.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-neutral-400"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </motion.a>
              </Reveal>
            );
          })}

          <Reveal delay={0.08}>
            <div className="group relative block h-full overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-sm">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-blue-300">
                <ShieldCheck size={18} />
              </div>
              <h3 className="relative mt-4 text-sm font-semibold text-white">Security</h3>
              <p className="relative mt-2 text-sm leading-relaxed text-neutral-400">
                Cross-cutting, not a module of its own: JWT/OAuth2 auth, role-based access control,
                per-IP rate limiting, and structured audit logging on every request.
              </p>
              <div className="relative mt-4 flex flex-wrap gap-1.5">
                {["JWT", "RBAC", "Rate Limiting"].map((s) => (
                  <span
                    key={s}
                    className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-neutral-400"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
