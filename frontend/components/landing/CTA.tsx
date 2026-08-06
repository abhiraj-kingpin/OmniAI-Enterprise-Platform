"use client";

import AuroraBackground from "./AuroraBackground";
import MagneticButton from "./MagneticButton";
import Reveal from "./Reveal";

export default function CTA() {
  return (
    <section className="relative overflow-hidden py-32">
      <AuroraBackground />
      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <Reveal>
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Sixteen modules are waiting.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-balance text-lg text-neutral-400">
            Add an API key, run two commands, and you have a working AI platform — not a demo.
          </p>
        </Reveal>
        <Reveal delay={0.15} className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <MagneticButton href="/dashboard" variant="primary">
            Launch the app
          </MagneticButton>
          <MagneticButton href="https://github.com/abhiraj-kingpin/OmniAI-Enterprise-Platform" variant="glass">
            View on GitHub
          </MagneticButton>
        </Reveal>
      </div>
    </section>
  );
}
