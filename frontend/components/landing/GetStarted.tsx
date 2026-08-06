"use client";

import { motion } from "framer-motion";
import { Check, Container, Laptop, Boxes } from "lucide-react";

import MagneticButton from "./MagneticButton";
import Reveal from "./Reveal";

const OPTIONS = [
  {
    icon: Laptop,
    title: "Local",
    description: "Run the backend and frontend directly on your machine.",
    steps: ["pip install -r requirements.txt", "npm install", "uvicorn + npm run dev"],
  },
  {
    icon: Container,
    title: "Docker Compose",
    description: "Backend, frontend, Redis, Kafka, and an MLflow UI in one command.",
    steps: ["docker compose up --build"],
    highlighted: true,
  },
  {
    icon: Boxes,
    title: "Kubernetes",
    description: "Deployment, Service, Ingress, and HPA manifests included.",
    steps: ["kubectl apply -f infra/k8s/"],
  },
];

export default function GetStarted() {
  return (
    <section id="get-started" className="relative py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Self-hosted. No pricing tiers.
          </h2>
          <p className="mt-4 text-balance text-lg text-neutral-400">
            This is source code you run yourself — pick the deployment shape that fits.
          </p>
        </Reveal>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {OPTIONS.map((opt, i) => (
            <Reveal key={opt.title} delay={i * 0.1}>
              <motion.div
                whileHover={{ y: -6 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={`relative h-full rounded-2xl border p-6 backdrop-blur-sm ${
                  opt.highlighted
                    ? "border-blue-500/40 bg-blue-500/[0.06] shadow-[0_0_60px_-15px_rgba(59,130,246,0.5)]"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-blue-300">
                  <opt.icon size={18} />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{opt.title}</h3>
                <p className="mt-2 text-sm text-neutral-400">{opt.description}</p>
                <ul className="mt-5 space-y-2">
                  {opt.steps.map((step) => (
                    <li key={step} className="flex items-start gap-2 text-xs text-neutral-500">
                      <Check size={13} className="mt-0.5 shrink-0 text-blue-400" />
                      <code className="font-mono">{step}</code>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.3} className="mt-10 text-center">
          <MagneticButton href="https://github.com/abhiraj-kingpin/OmniAI-Enterprise-Platform" variant="glass">
            View the source on GitHub
          </MagneticButton>
        </Reveal>
      </div>
    </section>
  );
}
