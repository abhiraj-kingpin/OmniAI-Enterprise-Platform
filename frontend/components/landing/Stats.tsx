"use client";

import Counter from "./Counter";
import Reveal from "./Reveal";

const STATS = [
  { value: 16, suffix: "", label: "AI modules, one backend" },
  { value: 17, suffix: "", label: "Frontend routes" },
  { value: 21, suffix: "", label: "Automated backend tests" },
  { value: 2, suffix: "", label: "LLM providers (Anthropic, OpenAI)" },
];

export default function Stats() {
  return (
    <section id="stats" className="border-y border-white/5 bg-white/[0.02] py-24">
      <div className="mx-auto max-w-5xl px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {STATS.map((stat, i) => (
            <Reveal key={stat.label} delay={i * 0.1} className="text-center">
              <p className="bg-gradient-to-b from-white to-neutral-400 bg-clip-text text-5xl font-bold tabular-nums text-transparent">
                <Counter value={stat.value} suffix={stat.suffix} />
              </p>
              <p className="mt-2 text-sm text-neutral-500">{stat.label}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
