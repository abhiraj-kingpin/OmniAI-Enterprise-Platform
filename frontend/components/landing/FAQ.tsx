"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

import Reveal from "./Reveal";

const FAQS = [
  {
    q: "Do I need an API key to use this?",
    a: "Yes, for most of it. Set ANTHROPIC_API_KEY in backend/.env and 11 of the 16 modules work — chat, RAG answers, code generation, vision captioning, the research and browser agents. Four modules (Vision's local CLIP search, Speech, Recommendations, Forecasting) run entirely on local inference and need no key at all.",
  },
  {
    q: "Is this connected to a real database?",
    a: "No relational database. Module state is either stateless per request, held in local files under backend/data/ (uploads, model outputs, an MLflow SQLite database), or delegated to Redis for the task queue.",
  },
  {
    q: "What runs locally vs. calls an external API?",
    a: "Embeddings, OCR, speech-to-text, and CLIP-based vision search all run on ONNX Runtime, fully local. Chat, RAG answer synthesis, code generation, and the agent modules call Anthropic or OpenAI. Fine-tuning and image/video generation run PyTorch models locally, no external API.",
  },
  {
    q: "Can I run this without Docker?",
    a: "Yes — Docker Compose is one option, not a requirement. A local Python virtual environment plus npm install covers the full stack; see the Get Started section above.",
  },
  {
    q: "Is the authentication production-ready?",
    a: "The mechanism is real (JWT, OAuth2 password flow, bcrypt, RBAC) but the user store is in-memory with two seeded demo accounts. Replace app/core/users.py with a real identity provider before deploying this anywhere but locally.",
  },
];

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="relative py-28">
      <div className="mx-auto max-w-3xl px-6">
        <Reveal className="mb-12 text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Frequently asked
          </h2>
        </Reveal>

        <div className="space-y-3">
          {FAQS.map((item, i) => {
            const isOpen = open === i;
            return (
              <Reveal key={item.q} delay={i * 0.05}>
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? null : i)}
                    className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left"
                  >
                    <span className="text-sm font-medium text-white">{item.q}</span>
                    <motion.span
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.25 }}
                      className="shrink-0 text-neutral-400"
                    >
                      <ChevronDown size={16} />
                    </motion.span>
                  </button>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <p className="px-6 pb-5 text-sm leading-relaxed text-neutral-400">{item.a}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
