"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ChevronDown } from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect } from "react";

import AuroraBackground from "./AuroraBackground";
import MagneticButton from "./MagneticButton";

// The Three.js canvas is client-only and non-trivial to hydrate — load it
// after the rest of the hero paints instead of blocking first render.
const HeroScene = dynamic(() => import("./HeroScene"), { ssr: false });

const HEADLINE_WORDS = ["Sixteen", "AI", "modules.", "One", "real", "platform."];

export default function Hero() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 50, damping: 20 });
  const parallaxX = useTransform(springX, [-0.5, 0.5], [-18, 18]);
  const parallaxY = useTransform(springY, [-0.5, 0.5], [-18, 18]);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      mouseX.set(e.clientX / window.innerWidth - 0.5);
      mouseY.set(e.clientY / window.innerHeight - 0.5);
    }
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [mouseX, mouseY]);

  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
      <AuroraBackground />

      <motion.div style={{ x: parallaxX, y: parallaxY }} className="absolute inset-0 -z-0">
        <HeroScene />
      </motion.div>

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs text-neutral-300 backdrop-blur-md"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Chat · RAG · Vision · Speech · Fine-Tuning · and 11 more
        </motion.div>

        <h1 className="text-balance text-5xl font-bold leading-[1.05] tracking-tight text-white sm:text-6xl md:text-7xl">
          {HEADLINE_WORDS.map((word, i) => (
            <motion.span
              key={word + i}
              initial={{ opacity: 0, y: 24, filter: "blur(6px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.6, delay: 0.15 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="inline-block bg-gradient-to-b from-white to-neutral-400 bg-clip-text pr-[0.28em] text-transparent"
            >
              {word}
            </motion.span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mx-auto mt-6 max-w-2xl text-balance text-lg text-neutral-400"
        >
          A FastAPI backend and Next.js frontend covering LLM chat, retrieval-augmented generation,
          computer vision, speech, forecasting, fine-tuning, and MLOps — every module built, tested, and
          documented, not scaffolded.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.85 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <MagneticButton href="/dashboard" variant="primary">
            Launch the app
          </MagneticButton>
          <MagneticButton href="#features" variant="glass">
            Explore modules
          </MagneticButton>
        </motion.div>
      </div>

      <motion.a
        href="#built-with"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.3, duration: 0.6 }}
        className="absolute bottom-8 flex flex-col items-center gap-2 text-neutral-500"
        aria-label="Scroll down"
      >
        <motion.span animate={{ y: [0, 8, 0] }} transition={{ duration: 1.8, repeat: Infinity }}>
          <ChevronDown size={20} />
        </motion.span>
      </motion.a>
    </section>
  );
}
