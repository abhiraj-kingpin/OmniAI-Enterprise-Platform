"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Activity } from "lucide-react";
import type { MouseEvent } from "react";

import { MODULES } from "@/lib/modules";
import Reveal from "./Reveal";

const PREVIEW_MODULES = MODULES.slice(0, 6);

export default function DashboardPreview() {
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);
  const springRotateX = useSpring(rotateX, { stiffness: 150, damping: 20 });
  const springRotateY = useSpring(rotateY, { stiffness: 150, damping: 20 });

  function handleMove(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    rotateY.set(px * 6);
    rotateX.set(py * -6);
  }

  function handleLeave() {
    rotateX.set(0);
    rotateY.set(0);
  }

  return (
    <section className="relative py-28">
      <div className="mx-auto max-w-5xl px-6">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            The real dashboard, not a mockup
          </h2>
          <p className="mt-4 text-balance text-lg text-neutral-400">
            What you land on after clicking &ldquo;Launch app&rdquo; — every card below links to a
            module that actually runs.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <div style={{ perspective: 1200 }}>
            <motion.div
              onMouseMove={handleMove}
              onMouseLeave={handleLeave}
              style={{ rotateX: springRotateX, rotateY: springRotateY, transformStyle: "preserve-3d" }}
              className="relative overflow-hidden rounded-2xl border border-white/10 bg-neutral-900/60 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.6)] backdrop-blur-xl"
            >
              <div className="flex items-center gap-1.5 border-b border-white/10 bg-white/[0.03] px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
                <span className="ml-3 rounded-md bg-white/5 px-3 py-1 text-[11px] text-neutral-400">
                  omniai.app/dashboard
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">
                {PREVIEW_MODULES.map((mod) => (
                  <div
                    key={mod.href}
                    className="rounded-xl border border-white/10 bg-white/[0.03] p-4 transition-colors hover:border-blue-500/40"
                  >
                    <p className="text-xs font-semibold text-white">{mod.name}</p>
                    <p className="mt-1.5 text-[11px] leading-relaxed text-neutral-500">
                      {mod.description}
                    </p>
                  </div>
                ))}
                <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-4 text-neutral-500">
                  <Activity size={16} />
                  <p className="text-[11px]">+10 more modules</p>
                </div>
              </div>
            </motion.div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
