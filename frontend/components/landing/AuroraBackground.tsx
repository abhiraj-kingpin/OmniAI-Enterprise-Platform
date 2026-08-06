"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

/** Layered ambient background: two slow-drifting blurred gradient blobs
 * ("aurora"), a subtle SVG noise texture (breaks up flat-color banding),
 * and a handful of softly pulsing particles. Pure CSS/SVG + a few Framer
 * Motion loops — no canvas, no WebGL — so it costs effectively nothing to
 * render behind heavier sections (like the 3D hero).
 */
export default function AuroraBackground() {
  const particles = useMemo(
    () =>
      Array.from({ length: 18 }, (_, i) => ({
        id: i,
        left: `${(i * 53) % 100}%`,
        top: `${(i * 31) % 100}%`,
        size: 2 + (i % 3),
        duration: 6 + (i % 5),
        delay: i * 0.3,
      })),
    [],
  );

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="absolute -left-1/4 top-[-10%] h-[60vh] w-[60vh] rounded-full bg-blue-600/25 blur-[120px]"
        animate={{ x: [0, 60, 0], y: [0, 40, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute right-[-15%] top-[20%] h-[50vh] w-[50vh] rounded-full bg-indigo-500/20 blur-[120px]"
        animate={{ x: [0, -50, 0], y: [0, 60, 0] }}
        transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-[-20%] left-1/3 h-[45vh] w-[45vh] rounded-full bg-sky-500/15 blur-[110px]"
        animate={{ x: [0, 40, 0], y: [0, -30, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />

      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute rounded-full bg-blue-300/60"
          style={{ left: p.left, top: p.top, width: p.size, height: p.size }}
          animate={{ opacity: [0.15, 0.8, 0.15], scale: [1, 1.4, 1] }}
          transition={{ duration: p.duration, repeat: Infinity, delay: p.delay, ease: "easeInOut" }}
        />
      ))}

      <svg className="absolute inset-0 h-full w-full opacity-[0.03]">
        <filter id="noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noise)" />
      </svg>
    </div>
  );
}
