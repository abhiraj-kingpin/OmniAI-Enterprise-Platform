"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

const NODE_W = 190;
const NODE_H = 64;

const NODES = [
  { id: "frontend", x: 10, y: 118, label: "Next.js Frontend", sub: "17 routes" },
  { id: "backend", x: 285, y: 118, label: "FastAPI Backend", sub: "Auth · Rate Limit · Audit" },
  { id: "llm", x: 560, y: 10, label: "Anthropic / OpenAI", sub: "Chat, agents, LoRA" },
  { id: "onnx", x: 560, y: 118, label: "ONNX Runtime", sub: "Embeddings, OCR, ASR, vision" },
  { id: "infra", x: 560, y: 226, label: "Redis · Kafka · Ray", sub: "Celery, streaming, distributed" },
];

const EDGES: [string, string][] = [
  ["frontend", "backend"],
  ["backend", "llm"],
  ["backend", "onnx"],
  ["backend", "infra"],
];

function nodeById(id: string) {
  return NODES.find((n) => n.id === id)!;
}

/** Scroll-scrubbed architecture diagram: connection lines draw themselves
 * and nodes fade up as the section scrolls through the viewport, keyed to
 * scroll progress via GSAP ScrollTrigger (scrub) rather than a one-shot
 * time-based animation — distinct from the fade/lift reveals the rest of
 * the page uses via Framer Motion. Deliberately not pinned: pinning a
 * ScrollTrigger correctly under Lenis's virtual scroll needs a scroller
 * proxy this page doesn't set up, and an unpinned scrub is simpler and
 * doesn't depend on that being wired correctly. */
export default function ArchitectureViz() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    let ctx: gsap.Context | undefined;

    import("gsap/ScrollTrigger").then(({ ScrollTrigger }) => {
      gsap.registerPlugin(ScrollTrigger);
      if (!sectionRef.current || !svgRef.current) return;

      ctx = gsap.context(() => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
            end: "top 15%",
            scrub: 0.6,
          },
        });

        tl.fromTo(".arch-edge", { strokeDashoffset: 1 }, { strokeDashoffset: 0, stagger: 0.25, ease: "none" })
          .fromTo(
            ".arch-node",
            { opacity: 0, scale: 0.85, y: 12 },
            { opacity: 1, scale: 1, y: 0, stagger: 0.15, ease: "power2.out" },
            "-=0.6",
          );
      }, sectionRef);
    });

    return () => ctx?.revert();
  }, []);

  return (
    <section id="architecture" ref={sectionRef} className="relative flex min-h-screen items-center overflow-hidden py-24">
      <div className="mx-auto w-full max-w-6xl px-6">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            One request, three real backends
          </h2>
          <p className="mt-4 text-balance text-lg text-neutral-400">
            Every module talks to genuine infrastructure — hosted LLM APIs, local ONNX inference, or the
            distributed-systems stack — not a mock behind the scenes.
          </p>
        </div>

        <svg ref={svgRef} viewBox="0 0 760 300" className="mx-auto w-full max-w-4xl overflow-visible">
          {EDGES.map(([from, to], i) => {
            const a = nodeById(from);
            const b = nodeById(to);
            const startX = a.x + NODE_W;
            const startY = a.y + NODE_H / 2;
            const endX = b.x;
            const endY = b.y + NODE_H / 2;
            const midX = (startX + endX) / 2;
            return (
              <path
                key={i}
                className="arch-edge"
                d={`M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`}
                fill="none"
                stroke="url(#edgeGradient)"
                strokeWidth={1.5}
                strokeDasharray={1}
                pathLength={1}
              />
            );
          })}
          <defs>
            <linearGradient id="edgeGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#60a5fa" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {NODES.map((n) => (
            // Outer <g> holds the static layout position; GSAP animates the
            // inner .arch-node group's opacity/scale/y in its own local
            // coordinate space, so the tween doesn't clobber this translate.
            <g key={n.id} transform={`translate(${n.x}, ${n.y})`}>
              <g className="arch-node">
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  rx={14}
                  fill="rgba(255,255,255,0.04)"
                  stroke="rgba(255,255,255,0.12)"
                />
                <text x={16} y={26} fill="white" fontSize={13} fontWeight={600}>
                  {n.label}
                </text>
                <text x={16} y={44} fill="#9ca3af" fontSize={10.5}>
                  {n.sub}
                </text>
              </g>
            </g>
          ))}
        </svg>
      </div>
    </section>
  );
}
